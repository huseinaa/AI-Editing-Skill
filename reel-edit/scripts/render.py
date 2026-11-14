"""Render every graphic visual and caption chunk of a reel to transparent PNGs.

    python render.py <workdir> [visual_id ...] [caps]

Uses Playwright with the installed Microsoft Edge (no browser download) and Google Fonts, so Arabic
shaping and mixed-direction text come out right.
"""
import json, os, re, sys
from playwright.sync_api import sync_playwright
from reel_edit.project import load, kind_of
from reel_edit.components import CSS, caption_css, SAFE_W, FACE_BOX
CARD_TEXT_W = FACE_BOX[2] - 60   # one-line captions inside the face square fit this width
from reel_edit.brand import BROWSER

OVERLAY_PAD = 110  # transparent room for the card shadow, or it clips into a square behind the corners

p = load(sys.argv[1])
from reel_edit import components as _K   # edit.py may change the layout (face_portrait()): read it after loading
CSS, FACE_BOX = _K.CSS, _K.FACE_BOX
CARD_TEXT_W = FACE_BOX[2] - 60
only = sys.argv[2:]
os.makedirs(p.png, exist_ok=True)


def wrap(text):
    """English runs in Inter, isolated so bidi keeps them in order; *word* = the keyword, in the accent color."""
    text = re.sub(r"\*([^*]+)\*", lambda m: "\x00" + m.group(1) + "\x01", text)
    if p.lang == "ar":
        # apostrophes belong inside the English run, or "you're" splits into "re ... 'you"
        # commas and $ € % stay inside the run, or "5,000" splits and an RTL line shows "000,5"
        text = re.sub(r"([A-Za-z0-9$€\x00][A-Za-z0-9/ .,%\-'’\x00\x01]*[A-Za-z0-9%\x01]|[A-Za-z0-9])", r'<bdi class="en" dir="ltr">\1</bdi>', text)
    text = text.replace("\x00", '<span class="kw">').replace("\x01", "</span>")
    return re.sub(r"\{([^}]+)\}", r'<span class="big">\1</span>', text)   # {word} = a big word (moving-caption style)


def page(body, extra=""):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}{extra}</style></head><body>{body}</body></html>"


meta_path = os.path.join(p.png, "meta.json")
meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
with sync_playwright() as pw:
    # REEL_EDIT_BROWSER_ARGS: extra browser flags, e.g. "--no-sandbox" when the headless browser
    # cannot reach the network (Google Fonts) on a machine
    b = pw.chromium.launch(channel=BROWSER, args=os.environ.get("REEL_EDIT_BROWSER_ARGS", "").split())
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
            # always one line (the user's call, 10 Nov 2026). Inside the face square of a light screen the
            # caption shrinks to fit the square's width instead of wrapping
            fc = next((c for c in p.face_card if c["window"][0] - 0.05 <= s < c["window"][1]), None)
            card = fc is not None and fc.get("cap", "in") == "in"   # a hard split or corner face keeps captions low
            cls = "cap in-card" if card else "cap"
            pg.set_content(page(f'<div id="c" class="{cls}"{style}>{wrap(text)}</div>', caption_css(p.lang)), wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            el = pg.locator("#c")
            fit = min(SAFE_W, fc["box"][2] - 60) if card else SAFE_W
            text_w = pg.evaluate("() => { const r = document.createRange(); r.selectNodeContents(document.getElementById('c')); return r.getBoundingClientRect().width; }")
            if text_w > fit:
                size = float(pg.evaluate("() => parseFloat(getComputedStyle(document.getElementById('c')).fontSize)"))
                new = size * fit / text_w
                pg.evaluate(f"() => document.getElementById('c').style.fontSize = '{new:.1f}px'")
                if new < size * 0.72:   # shrunk this far it reads small: the chunk has too many words
                    tall.append((i, text))
            el.screenshot(path=os.path.join(p.png, f"c_{i:03d}.png"), omit_background=True)
        if tall:
            print("WARNING captions too long for one line (split them, 3-4 words):", tall)
    b.close()
json.dump(meta, open(meta_path, "w"), indent=1)
print(f"rendered {n} visuals, {len(p.captions)} captions")
