"""Render every graphic visual and caption chunk of a reel to transparent PNGs.

    python render.py <workdir> [visual_id ...] [caps]

Uses Playwright with the installed Microsoft Edge (no browser download) and Google Fonts, so Arabic
shaping and mixed-direction text come out right.
"""
import json, os, re, sys
from playwright.sync_api import sync_playwright
from reel_edit.project import load, kind_of
from reel_edit.components import CSS, caption_css
from reel_edit.brand import BROWSER

OVERLAY_PAD = 110  # transparent room for the card shadow, or it clips into a square behind the corners

p = load(sys.argv[1])
only = sys.argv[2:]
os.makedirs(p.png, exist_ok=True)


def wrap(text):
    """English runs in Inter, isolated so bidi keeps them in order; *word* = yellow keyword."""
    text = re.sub(r"\*([^*]+)\*", lambda m: "\x00" + m.group(1) + "\x01", text)
    if p.lang == "ar":
        # apostrophes belong inside the English run, or "you're" splits into "re ... 'you"
        text = re.sub(r"([A-Za-z0-9\x00][A-Za-z0-9/ .\-'’\x00\x01]*[A-Za-z0-9\x01]|[A-Za-z0-9])", r'<bdi class="en">\1</bdi>', text)
    text = text.replace("\x00", '<span class="kw">').replace("\x01", "</span>")
    return re.sub(r"\{([^}]+)\}", r'<span class="big">\1</span>', text)   # {word} = a big word (moving-caption style)


def page(body, extra=""):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}{extra}</style></head><body>{body}</body></html>"


meta_path = os.path.join(p.png, "meta.json")
meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
with sync_playwright() as pw:
    b = pw.chromium.launch(channel=BROWSER)
    pg = b.new_page(viewport={"width": 1440, "height": 2560})
    n = 0
    for vid, value in p.visuals.items():
        if only and vid not in only:
            continue
        kind = kind_of(value)
        if kind.startswith("broll"):
            meta[vid] = {"kind": kind}
            continue
        html = value[0]
        pad = OVERLAY_PAD if kind == "overlay" else 0
        pg.set_content(page(f'<div id="v" style="display:inline-block;padding:{pad}px">{html}</div>'), wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        el = pg.locator("#v")
        el.screenshot(path=os.path.join(p.png, f"v_{vid}.png"), omit_background=True)
        bb = el.bounding_box()
        meta[vid] = {"kind": kind, "w": round(bb["width"]), "h": round(bb["height"]), "pad": pad}
        n += 1
    if not only or "caps" in only:
        for f in os.listdir(p.png):
            if f.startswith("c_"):
                os.remove(os.path.join(p.png, f))
        tall = []
        for i, (text, s, e) in enumerate(p.captions):
            sc = p.caption_style.get(i, {}).get("scale", 1)
            style = f' style="font-size:{78 * sc if p.lang == "ar" else 74 * sc:.0f}px"' if sc != 1 else ""
            pg.set_content(page(f'<div id="c" class="cap"{style}>{wrap(text)}</div>', caption_css(p.lang)), wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            el = pg.locator("#c")
            el.screenshot(path=os.path.join(p.png, f"c_{i:03d}.png"), omit_background=True)
            if el.bounding_box()["height"] > 260 * max(sc, 1) * (1.6 if "class=\"big\"" in wrap(text) else 1):
                tall.append((i, text))
        if tall:
            print("WARNING two-line captions (split them):", tall)
    b.close()
json.dump(meta, open(meta_path, "w"), indent=1)
print(f"rendered {n} visuals, {len(p.captions)} captions")
