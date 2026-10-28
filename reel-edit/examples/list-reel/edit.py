# 16 signs your website is vibe coded (14 said on camera). List reel, Sales, 45s, Oct 2026.
# Layout: the title and every point on top, each written on the word it is said, the face
# bottom-left, and an illustration of the current point bottom-right. Then the face, captions and the keyword card.
# One 73s take cut down by assemble.py (cuts.txt). Times are from words.txt of the cut master.
from reel_edit.components import *

FOLDER = r"C:\path\to\Reels\16 signs your website is vibe coded"
VIDEO = r"C:\path\to\workdir\master.mp4"
OUTPUT = FOLDER + r"\16 signs your website is vibe coded - edited.mp4"
CAPTION_LANG = "ar"
FACE = (735, 880)

LIST_END = 34.95
ZONE_Y, ZONE_H = 1050, 840                       # the row under the list: face window left, illustration right
FACE_PIP = {"crop": (285, 200, 930, 1420), "box": (SAFE_L, ZONE_Y, 550, ZONE_H), "window": (0, LIST_END)}

# (label, the second he starts saying it, one plain line under the illustration)
SIGNS = [
    ("vercel.app link", 0.00, "Not your own domain"),
    ("no 404 page", 2.60, "A wrong link shows a raw error"),
    ("the purple gradient", 4.32, "Every AI site picks it"),
    ("dead footer links", 6.98, "They go nowhere"),
    ("no meta description", 9.24, "Google has nothing to show"),
    ("no share preview image", 10.62, "A blank card when you share it"),
    ("no sitemap", 12.72, "Search engines can't map the site"),
    ("looks bad on mobile", 14.12, "Never checked on a phone"),
    ("3.5 MB of JavaScript", 15.76, "To show a single page"),
    ("API key in the source", 18.86, "Anyone can copy it"),
    ("no limit on AI buttons", 21.46, "One user, 1,000 clicks, your bill"),
    ("no privacy policy", 23.92, "Users can't see what you collect"),
    ("no terms of service", 25.55, "No rules between you and users"),
    ("you can't explain the code", 27.07, "You can't fix what you can't read"),
]
MONO = "font-family:Consolas,'Courier New',monospace"
CARD_W = SAFE_W - 550 - 40                       # illustration card width
IN_W = CARD_W - 72


def url_pill(html, size=40):
    return f"""<div class="row" style="gap:14px;height:92px;padding:0 26px;border-radius:46px;background:{PANEL};border:2px solid #E4E7EC;font-size:{size}px;font-weight:700;white-space:nowrap">
      <span style="width:22px;height:22px;border-radius:50%;border:5px solid {MUTED};flex:none"></span>{html}</div>"""


def mini_browser(url, inner, h=380):
    return f"""<div style="width:{IN_W}px;height:{h}px;border-radius:24px;border:2px solid #E4E7EC;overflow:hidden;background:#fff">
      <div class="row" style="height:60px;background:{PANEL};gap:10px;padding:0 20px;border-bottom:2px solid #E4E7EC">
        {''.join(f'<div style="width:16px;height:16px;border-radius:50%;background:{c}"></div>' for c in ['#FF5F57', '#FEBC2E', '#28C840'])}
        <div style="margin-left:10px;font-size:24px;font-weight:600;color:{MUTED}">{url}</div></div>
      <div style="position:relative;height:{h - 62}px">{inner}</div></div>"""


def chip(text, color=RED):
    return f'<div style="display:inline-block;padding:10px 24px;border-radius:999px;background:{color};color:#fff;font-size:32px;font-weight:800;white-space:nowrap">{text}</div>'


def doc(title):
    lines = "".join(f'<div style="height:16px;width:{w}%;background:#E4E7EC;border-radius:8px;margin-top:18px"></div>' for w in (90, 76, 84, 60))
    return f"""<div style="position:relative;width:330px;margin:0 auto;padding:36px 34px 44px;border-radius:24px;background:{PANEL};border:2px solid #E4E7EC">
      <div style="font-size:34px;font-weight:800">{title}</div>{lines}
      <div class="icon" style="position:absolute;right:-34px;top:-34px;width:110px;height:110px;background:{RED};font-size:64px">&#10005;</div></div>
      <div style="text-align:center;margin-top:34px">{chip('Page not found')}</div>"""


ART = [
    # 1 vercel.app link
    f"""<div style="margin-top:90px">{url_pill(f'my-app<span class="hl" style="padding:0 8px">.vercel.app</span>', 44)}</div>
        <div style="text-align:center;margin-top:44px">{chip('A free test address')}</div>""",
    # 2 no 404 page
    mini_browser("myapp.com/pricng", f"""<div style="padding:22px 24px;{MONO};font-size:26px;color:{INK}">404: NOT_FOUND<br><span style="color:{MUTED}">Code: NOT_FOUND<br>ID: cdg1::x7k2p</span></div>"""),
    # 3 the purple gradient
    f"""<div style="width:{IN_W}px;height:380px;border-radius:24px;background:linear-gradient(135deg,#7C3AED,#6366F1 55%,#A855F7);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px">
        <div style="font-size:44px;font-weight:900;color:#fff;text-align:center;line-height:1.1">Build faster<br>with AI</div>
        <div style="padding:14px 40px;border-radius:999px;background:#fff;color:#6D28D9;font-size:30px;font-weight:800">Get started</div></div>""",
    # 4 dead footer links
    f"""<div style="width:{IN_W}px;padding:34px 30px;border-radius:24px;background:{INK}">""" + "".join(
        f"""<div class="row" style="justify-content:space-between;margin:14px 0"><span style="font-size:36px;font-weight:700;color:#fff;text-decoration:underline">{l}</span>
            <span style="{MONO};font-size:28px;font-weight:700;color:#fff;background:{RED};padding:6px 16px;border-radius:10px">href="#"</span></div>""" for l in ("About", "Pricing", "Contact")) + "</div>",
    # 5 no meta description
    f"""<div style="width:{IN_W}px;padding:30px;border-radius:24px;border:2px solid #E4E7EC;margin-top:30px">
        <div style="font-size:26px;color:{MUTED};font-weight:600">myapp.com</div>
        <div style="font-size:42px;font-weight:800;color:#1A0DAB;margin-top:6px">My App</div>
        <div style="margin-top:18px;height:120px;border:4px dashed {RED};border-radius:16px;display:flex;align-items:center;justify-content:center;font-size:30px;font-weight:800;color:{RED}">no description</div></div>""",
    # 6 no share preview image
    f"""<div style="width:{IN_W - 40}px;margin-left:40px;padding:14px;border-radius:28px 28px 8px 28px;background:#DCF8C6">
        <div style="height:210px;border-radius:18px;background:#C9CFDA;display:flex;align-items:center;justify-content:center">
          <svg width="110" height="90" viewBox="0 0 110 90"><rect x="4" y="4" width="102" height="82" rx="10" fill="none" stroke="#8A93A3" stroke-width="7"/><path d="M14 74 L44 40 L64 60 L78 48 L98 74Z" fill="#8A93A3"/><path d="M8 8 L102 82" stroke="{RED}" stroke-width="9" stroke-linecap="round"/></svg></div>
        <div style="font-size:32px;font-weight:800;margin:14px 8px 0">myapp.com</div>
        <div style="font-size:26px;color:{MUTED};font-weight:600;margin:4px 8px 6px">https://myapp.com</div></div>""",
    # 7 no sitemap
    f"""<div style="margin-top:50px">{url_pill('myapp.com/<b>sitemap.xml</b>', 34)}</div>
        <div style="text-align:center;font-size:150px;font-weight:900;color:{RED};line-height:1;margin-top:40px;letter-spacing:-4px">404</div>""",
    # 8 looks bad on mobile
    f"""<div style="width:270px;height:430px;margin:0 auto;border-radius:44px;border:10px solid #1B1F2A;background:#fff;overflow:hidden;position:relative">
        <div style="width:520px;padding:26px 22px"><div style="font-size:46px;font-weight:900;white-space:nowrap">Welcome to my awesome app</div>
          <div style="margin-top:20px;width:470px;height:130px;border-radius:16px;background:linear-gradient(135deg,{BRIGHT},{BLUE})"></div>
          <div class="row" style="gap:14px;margin-top:20px">{''.join(f'<div style="width:150px;height:70px;border-radius:14px;background:{PANEL};border:2px solid #E4E7EC;flex:none"></div>' for _ in range(3))}</div></div>
        <div style="position:absolute;right:0;top:0;bottom:0;width:10px;background:{RED}"></div></div>""",
    # 9 3.5 MB of JavaScript
    f"""<div style="text-align:center;margin-top:30px"><div style="font-size:150px;font-weight:900;color:{RED};line-height:1;letter-spacing:-5px">3.5 MB</div>
        <div style="{MONO};font-size:34px;font-weight:700;margin-top:20px">main.js</div>
        <div style="margin:30px auto 0;width:{IN_W - 40}px;height:34px;border-radius:17px;background:#E4E7EC;overflow:hidden"><div style="width:22%;height:100%;background:{RED}"></div></div>
        <div style="font-size:28px;font-weight:700;color:{MUTED};margin-top:14px">loading...</div></div>""",
    # 10 API key in the source
    f"""<div style="width:{IN_W}px;padding:30px 26px;border-radius:24px;background:{INK};{MONO};font-size:27px;line-height:1.75;color:#C9CFDA;white-space:nowrap;overflow:hidden">
        <span style="color:#7AA2FF">const</span> ai = <span style="color:#7AA2FF">new</span> OpenAI({{<br>
        <span style="display:inline-block;background:{RED};color:#fff;padding:0 10px;border-radius:8px">&nbsp;apiKey: "sk-proj-9xQ4..."</span><br>}})</div>
        <div style="text-align:center;margin-top:34px">{chip('Visible in the browser')}</div>""",
    # 11 no limit on AI buttons
    f"""<div style="position:relative;width:360px;margin:50px auto 0"><div style="height:120px;border-radius:30px;background:{BRIGHT};color:#fff;font-size:46px;font-weight:900;display:flex;align-items:center;justify-content:center">Generate</div>
        <div style="position:absolute;left:230px;top:70px">{CURSOR}</div>
        <div style="position:absolute;right:-70px;top:-46px;padding:8px 22px;border-radius:999px;background:{INK};color:#fff;font-size:40px;font-weight:900">x1,000</div></div>
        <div style="text-align:center;margin-top:110px">{chip('Every click costs you')}</div>""",
    # 12, 13 the legal pages
    doc("Privacy Policy"),
    doc("Terms of Service"),
    # 14 you can't explain the code
    f"""<div style="position:relative;width:{IN_W}px;padding:30px 26px;border-radius:24px;background:{INK}">""" + "".join(
        f'<div style="height:20px;width:{w}%;margin:{20 if i else 0}px 0 0 {ind}px;border-radius:10px;background:{c}"></div>'
        for i, (w, ind, c) in enumerate([(55, 0, "#7AA2FF"), (70, 36, "#5F6571"), (48, 36, "#5F6571"), (62, 72, "#9AA3B2"), (40, 36, "#5F6571"), (30, 0, "#7AA2FF"), (66, 0, "#5F6571")]))
    + f"""<div style="position:absolute;right:34px;top:50%;transform:translateY(-50%);width:170px;height:170px;border-radius:50%;background:{YELLOW};color:{INK};font-size:130px;font-weight:900;display:flex;align-items:center;justify-content:center">?</div></div>""",
]


def screen(cur):
    cols = ""
    for c in range(2):
        rows = ""
        for i in range(c * 7, c * 7 + 7):
            label = SIGNS[i][0]
            on, shown = i == cur, i <= cur
            rows += f"""<div class="row" style="height:58px;margin-bottom:4px;padding:0 18px;border-radius:16px;gap:14px;font-size:38px;font-weight:{800 if on else 700};white-space:nowrap;
                background:{BRIGHT if on else 'transparent'};color:{'#fff' if shown else '#4B5262'}">
                <span style="width:52px;text-align:right;flex:none">{i + 1}.</span><span>{label if shown else ''}</span></div>"""
        cols += f'<div style="width:{SAFE_W // 2 - 5}px">{rows}</div>'
    label, _, line = SIGNS[cur]
    return full(f"""<div class="safe" style="text-align:center">
        <div class="t-white" style="font-size:66px;font-weight:900;line-height:1.15">{len(SIGNS)} signs your website is<br><span class="hl">vibe coded</span></div>
        <div class="row" style="margin-top:36px;gap:10px;align-items:flex-start;text-align:left">{cols}</div></div>
      <div class="card" style="position:absolute;left:{SAFE_L + 550 + 40}px;top:{ZONE_Y}px;width:{CARD_W}px;height:{ZONE_H}px;padding:34px 36px;box-shadow:none;border:none">
        <div class="row" style="gap:16px;height:120px;align-items:flex-start"><span class="icon" style="width:64px;height:64px;background:{BRIGHT};font-size:34px">{cur + 1}</span>
          <span style="font-size:42px;font-weight:900;line-height:1.12;padding-top:6px">{label}</span></div>
        <div style="height:520px;display:flex;flex-direction:column;justify-content:center">{ART[cur]}</div>
        <div style="position:absolute;left:36px;right:36px;bottom:34px;font-size:32px;font-weight:700;color:{MUTED};text-align:center;line-height:1.2">{line}</div></div>""")


CAPTIONS = [
    (35.14, "وهيدا باختصار الـ vibe coding"), (37.15, "ومنّو شي غلط"), (38.57, "بس you have to do it"),
    (39.47, "in a proper way"), (40.68, "فإذا you're interested"), (41.39, "تبني professional software"),
    (43.10, "comment AIC"), (44.28, "وأنا بتواصل معك"),
]

VISUALS = {
    **{f"s{i + 1}": screen(i) for i in range(len(SIGNS))},
    "aic": keyword_card("AIC", "and I'll message you"),
}

STARTS = [t for _, t, _ in SIGNS] + [LIST_END]
TIMELINE = [
    *[(f"s{i + 1}", STARTS[i], STARTS[i + 1]) for i in range(len(SIGNS))],
    ("aic", 43.10, 99),         # "comment AIC"
]

PUNCH = [(40.58, 43.10)]        # the ask
