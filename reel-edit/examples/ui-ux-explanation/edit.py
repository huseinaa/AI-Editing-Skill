# Worked example, style EXPLAINER (Authority). "UI UX Explanation.mp4", 61s, Sep 2026.
# Every caption and visual starts on a word timestamp from words.txt. Caption text is what he said.
from reel_edit.components import *

VIDEO = r"C:\path\to\UI UX Explanation.mp4"
CAPTION_LANG = "ar"
FACE = (720, 905)

CAPTIONS = [
    (0.00, "UI حلو مع UX سيّئة"), (1.80, "رح يخلّي العالم دغري"), (3.02, "تطلع من الـ software تبعك"),
    (4.12, "وحتى نحلّ، لازم نفهم قبل"), (6.12, "شو يعني UI و UX؟"), (7.70, "UI يعني user interface"),
    (9.62, "وهوّي شكل your software"), (11.02, "من ألوان، images، videos"), (13.42, "buttons، وحتى الـ layout"),
    (15.30, "وإذا كان UI حلو"), (17.06, "هيدا شي بيجذب العالم"), (18.40, "حتى يستعملوا الـ software تبعك"),
    (20.20, "وهلّق بدّي ياك تفكّر"), (21.40, "بشي مرّة على app"), (22.60, "أو website، وكبست كبسة"),
    (24.76, "وصار شي غير المتوقّع"), (26.26, "أو حتى ما صار شي أبداً"), (27.90, "وهيدا هوّي الـ bad UX"),
    (29.58, "which is user experience"), (31.42, "الـ software تبعك لازم يكون"), (32.84, "كتير واضح من دون ما"),
    (34.28, "يعوز الـ user كتير instructions"), (35.94, "حتى يستعملو"), (37.16, "وهيدي المشكلة بالـ AI"),
    (38.34, "بعدو لهلّق ما بيقدر"), (39.78, "يعمل good UI/UX للـ software"), (41.74, "بس بيقدر يعمل الـ basics"),
    (43.36, "وإيه، حتى مع استعمال"), (44.98, "كل الـ skills اللي الـ gurus"), (46.80, "بيقولولكن عنن"),
    (47.92, "فدايماً بينسى يحطّ"), (49.16, "proper loading state"), (50.26, "empty states"),
    (51.28, "وحتى الـ error pages"), (52.38, "متل 404 وغيرن"), (54.14, "فكتير مهم الـ software تبعك"),
    (55.88, "يكون عندو good UI/UX"), (57.56, "و follow for more tips"), (59.02, "on building software with AI"),
]

# ---- list that builds on the words he says (colors 11.50, images 12.06, videos 12.72, buttons 13.42, layout 14.92)
ICON = {
    "colors": "".join(f'<span style="width:26px;height:26px;border-radius:8px;background:{c};display:inline-block;margin-right:6px"></span>' for c in [BRIGHT, "#FFB020", "#fff"]),
    "images": '<span style="display:inline-block;width:70px;height:46px;border-radius:10px;background:linear-gradient(135deg,#8EC5FF,#0051BD)"></span>',
    "videos": '<span style="display:inline-flex;width:70px;height:46px;border-radius:10px;background:#1B2440;align-items:center;justify-content:center;color:#fff;font-size:24px">&#9654;</span>',
    "buttons": f'<span style="display:inline-block;width:92px;height:40px;border-radius:12px;background:{BRIGHT}"></span>',
    "layout": '<span style="display:inline-grid;grid-template-columns:1fr 1fr;gap:5px;width:60px;height:44px">' + '<span style="border:3px dashed #9AB8FF;border-radius:5px"></span>' * 4 + "</span>",
}
UI_ITEMS = ["colors", "images", "videos", "buttons", "layout"]
UI_AT = [11.50, 12.06, 12.72, 13.42, 14.92, 16.00]


def ui_screen(cur):
    it = UI_ITEMS[cur] if cur >= 0 else None
    return full(title_block("UI = User Interface", "How your app looks")
                + f'<div style="position:absolute;left:{SAFE_L}px;top:640px;transform:scale(.8);transform-origin:top left">{demo_app(it, grid=(it == "layout"))}</div>'
                + f'<div style="position:absolute;left:{SAFE_L + 560}px;top:700px">{list_rows([(i.title(), ICON[i]) for i in UI_ITEMS], cur, SAFE_W - 560)}</div>')


def checkout(state):
    if state == "wrong":
        inner = f"""<div style="padding:36px 50px"><div style="font-size:28px;color:{MUTED};font-weight:600">You clicked "Pay now". You got:</div>
          <div style="font-size:76px;font-weight:900;margin-top:16px">Our Blog</div>
          {''.join(f'<div style="margin-top:22px;height:24px;width:{w}%;background:{PANEL};border-radius:12px"></div>' for w in (80, 65, 72))}</div>
          <div class="chip" style="position:absolute;right:40px;bottom:40px;background:{RED};color:#fff;font-size:40px">Not what you expected</div>"""
        title = "Something else happened"
    else:
        q = f'<div style="position:absolute;right:90px;top:60px;font-size:240px;font-weight:900;color:{RED}">?</div>' if state == "nothing" else ""
        inner = f"""<div style="padding:36px 50px"><div style="font-size:48px;font-weight:800">Checkout</div>
          <div style="font-size:30px;color:{MUTED};margin-top:10px">Total: 40$</div>
          <div style="margin-top:34px;width:380px;height:100px;border-radius:26px;background:{BRIGHT};color:#fff;font-size:44px;font-weight:800;display:flex;align-items:center;justify-content:center">Pay now</div></div>
          <div style="position:absolute;left:340px;top:215px">{CURSOR}</div>{q}"""
        title = "Nothing happened" if state == "nothing" else "You click a button..."
    return split(f"""<div style="text-align:center"><div class="t-white" style="font-size:64px;font-weight:900">{title}</div>
        <div style="margin:22px auto 0;width:900px">{browser(inner, "myapp.com/checkout")}</div></div>""")


def ai_panel(guru):
    reply = f"""<div style="border:2px solid #E4E7EC;border-radius:18px;padding:24px">
        <div style="height:24px;width:60%;background:{PANEL};border-radius:8px"></div>
        <div style="height:64px;margin-top:14px;background:{PANEL};border-radius:12px"></div>
        <div style="height:44px;width:40%;margin-top:14px;background:#D0D5DD;border-radius:12px"></div></div>
      <div class="chip" style="margin-top:22px;background:{PANEL if guru else YELLOW};color:{INK};font-size:38px">Just the basics</div>"""
    g = f"""<div style="position:absolute;right:0;top:170px;width:440px;padding:36px;border-radius:36px;background:#fff">
        <div style="font-size:38px;font-weight:700;color:{MUTED}">"UI/UX skills"</div>
        <div style="font-size:60px;font-weight:900;margin-top:10px;position:relative;width:fit-content">from gurus
          <div style="position:absolute;left:-10px;right:-10px;top:50%;height:10px;background:{RED};transform:rotate(-6deg)"></div></div>
        <div style="font-size:38px;font-weight:700;margin-top:22px">Still just the basics</div></div>""" if guru else ""
    # same container width in both states, so the prompt bubble doesn't jump during the crossfade
    return split(f'<div style="position:relative;height:560px;width:720px">{chat("Build me a dashboard", reply)}</div>{g}')


def mini_state(kind):
    btn = lambda t: f'<div style="margin:34px auto 0;width:240px;height:76px;border-radius:20px;background:{BRIGHT};color:#fff;font-size:30px;font-weight:800;display:flex;align-items:center;justify-content:center">{t}</div>'
    body, name = {
        "loading": (f"""<div style="padding:34px">{''.join(f'<div style="height:{h}px;margin-top:22px;border-radius:14px;background:#EEF0F3"></div>' for h in [40, 150, 40, 40, 150])}
          <div style="margin:40px auto 0;width:90px;height:90px;border-radius:50%;border:12px solid #E4E7EC;border-top-color:{BRIGHT}"></div></div>""", "Loading state"),
        "empty": (f"""<div style="padding:34px;text-align:center"><div style="margin:120px auto 0;width:170px;height:170px;border-radius:40px;background:{PANEL};display:flex;align-items:center;justify-content:center;font-size:90px">&#128194;</div>
          <div style="font-size:38px;font-weight:800;margin-top:30px">No projects yet</div><div style="font-size:26px;color:{MUTED};margin-top:10px">Create your first one</div>{btn('+ New')}</div>""", "Empty state"),
        "404": (f"""<div style="padding:34px;text-align:center"><div style="font-size:150px;font-weight:900;margin-top:120px;letter-spacing:-4px">404</div>
          <div style="font-size:36px;font-weight:800">Page not found</div>{btn('Go home')}</div>""", "Error page"),
    }[kind]
    return f"""<div style="display:flex;flex-direction:column;align-items:center;gap:26px">{phone(body, small=True)}
      <div class="t-white" style="font-size:44px;font-weight:800">{name}</div></div>"""


def states(n):
    cols = "".join(mini_state(k) if i < n else '<div style="width:400px"></div>' for i, k in enumerate(["loading", "empty", "404"]))
    return full(title_block("What AI forgets", f"The {hl('missing')} screens", 104)
                + f'<div class="row" style="position:absolute;left:{SAFE_L}px;top:680px;gap:30px;transform:scale(.93);transform-origin:top left">{cols}</div>')


VISUALS = {
    "hook": hook_card(f"Why users {hl('quit')}<br>your AI-built app"),
    "leave": takeaway([("Pretty UI", "good"), ("Bad UX", "bad")], "Users leave", color=RED),
    "uiux": split(vs("UI", "User Interface", "UX", "User Experience")),
    "ui": ui_screen(-1),
    **{f"ui_{it}": ui_screen(i) for i, it in enumerate(UI_ITEMS)},
    "attract": takeaway([("Good UI", "good")], f"People {hl('want')} to use it"),
    "click": checkout("click"), "click_wrong": checkout("wrong"), "click_nothing": checkout("nothing"),
    "badux": full(statement("UX", f"= User {hl('Experience')}", tag="BAD UX", sub="How it feels to use your app")),
    "clear": takeaway([("Good UX", "good")], f"Clear on its {hl('own')}", "No instructions needed"),
    "ai_basic": ai_panel(False), "ai_guru": ai_panel(True),
    **{f"states{n}": states(n) for n in range(4)},
    "good": takeaway([("Good UI", "good"), ("Good UX", "good")], f"Software people {hl('keep')} using"),
    "follow": follow_card(f"Build {hl('proper')} software with AI"),
}

TIMELINE = [
    ("hook", 0.00, 2.70),
    ("leave", 2.70, 4.12),            # "تطلع من الـ software تبعك"
    ("uiux", 4.12, 7.70),             # "شو يعني UI و UX"
    ("ui", 7.70, UI_AT[0]),
    *[(f"ui_{it}", UI_AT[i], UI_AT[i + 1]) for i, it in enumerate(UI_ITEMS)],
    ("attract", 16.00, 20.20),        # "بيجذب العالم"
    ("click", 23.18, 24.76),          # "وكبست كبسة"
    ("click_wrong", 24.76, 26.26),    # "صار شي غير المتوقّع"
    ("click_nothing", 26.26, 27.90),  # "ما صار شي أبداً"
    ("badux", 27.90, 31.42),          # "bad UX which is user experience"
    ("clear", 31.42, 37.16),          # "لازم يكون كتير واضح"
    ("ai_basic", 37.16, 43.36),       # "المشكلة بالـ AI"
    ("ai_guru", 43.36, 47.92),        # "skills اللي الـ gurus"
    ("states0", 47.92, 49.56), ("states1", 49.56, 50.26), ("states2", 50.26, 51.68), ("states3", 51.68, 54.14),
    ("good", 54.14, 57.56),           # "good UI/UX"
    ("follow", 57.56, 99),            # "follow for more tips"
]
