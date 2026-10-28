"""Brand components for /reel-edit. Every visual is HTML rendered to a transparent PNG.

Canvas is the 1440x2560 master (exported at 1080x1920). Instagram safe box: x 90..1350, y 360..1920 (centered on the frame).
Brand palette and fonts: brand.json at the skill root (see reel_edit/brand.py).

An edit.py builds VISUALS from these. Each value is one of:
    overlay(html)   small card over the face, top of the safe box
    split(inner)    face video on top, dark graphic panel below SPLIT_Y
    full(inner)     full-screen graphic, voice carries on
    broll(path, mode="full"|"split"|"pip", start=0)   a real video clip, muted
"""

from .brand import INK, PANEL, MUTED, BLUE, BRIGHT, YELLOW, RED, LATIN, ARABIC, FONTS_URL
W, H = 1440, 2560
SAFE_L, SAFE_R, SAFE_T, SAFE_B = 90, 1350, 360, 1920   # symmetric left/right: everything centers on the frame (x = 720)
SAFE_W = SAFE_R - SAFE_L
SPLIT_Y = 1150          # split mode: face video above, panel below
SPLIT_H = H - SPLIT_Y
PIP = (1000, 700)       # b-roll picture-in-picture window size (top of safe box)
BOTTOM_TOP = 1100       # b-roll "bottom" window: from just under the mouth down to the safe box's bottom edge
BOTTOM_CAP_Y = 1835     # captions sit across that window's bottom edge while it is up, clear of the face

FONTS = FONTS_URL

CSS = f"""
@import url('{FONTS}');
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ background: transparent; font-family: '{LATIN}', '{ARABIC}', sans-serif; color: {INK}; }}
.card {{ background: #fff; border: 1px solid #E4E7EC; border-radius: 36px; box-shadow: 0 24px 60px rgba(8,11,20,.35); }}
.chip {{ display: inline-flex; align-items: center; gap: 14px; padding: 14px 30px; border-radius: 999px; font-weight: 800; font-size: 46px; }}
.hl {{ background: {YELLOW}; color: {INK}; padding: 0 16px; border-radius: 14px; }}
.full {{ width: {W}px; height: {H}px; background: {INK}; position: relative; overflow: hidden; }}
.split {{ width: {W}px; height: {SPLIT_H}px; background: {INK}; position: relative; overflow: hidden; }}
.grid-bg::before {{ content: ''; position: absolute; inset: 0; background-image: radial-gradient(rgba(255,255,255,.07) 2px, transparent 2px); background-size: 48px 48px; }}
.safe {{ position: absolute; left: {SAFE_L}px; width: {SAFE_W}px; top: {SAFE_T}px; }}
.pan {{ position: absolute; left: {SAFE_L}px; width: {SAFE_W}px; top: 44px; }}
.t-white {{ color: #fff; }}
.kicker {{ font-weight: 700; font-size: 44px; color: #9AA3B2; letter-spacing: 4px; text-transform: uppercase; }}
.phone {{ width: 620px; height: 1180px; background: #fff; border-radius: 72px; border: 14px solid #1B1F2A; position: relative; overflow: hidden; box-shadow: 0 40px 90px rgba(0,0,0,.5); }}
.phone.sm {{ width: 400px; height: 780px; border-radius: 52px; border-width: 10px; }}
.notch {{ width: 180px; height: 36px; background: #1B1F2A; border-radius: 0 0 22px 22px; margin: 0 auto; }}
.sm .notch {{ width: 120px; height: 24px; }}
.row {{ display: flex; align-items: center; }}
.icon {{ display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; font-weight: 900; color: #fff; flex: none; }}
.ring {{ outline: 9px solid {YELLOW}; outline-offset: 6px; }}
"""


def hl(text):
    """The one yellow 'look here' word. Max one per visual."""
    return f"<span class='hl'>{text}</span>"


# ---------------- layout wrappers ----------------
def overlay(html, top=None):
    """top= moves this one card (its top edge, master px). Default: high, above the eyes."""
    return (html, "overlay", {"top": top})


def full(inner, grid=True):
    return (f'<div class="full{" grid-bg" if grid else ""}">{inner}</div>', "full")


def split(inner):
    """inner is laid out inside the panel's safe column. Keep it under ~560px tall:
    the caption sits at y 1845, inside the panel."""
    return (f'<div class="split grid-bg"><div class="pan">{inner}</div></div>', "split")


def broll(path, mode="full", start=0.0, top=None, audio=False, height=None, lift=0):
    """A real clip (screen recording, footage). Muted, frozen on its last frame if short.
    full / split / pip cover-crop the clip to their shape. bottom shows it whole, not cropped, in a
    rounded window under the face (a clip he reacts to while talking); top= moves that window's top edge.
    A still image (.png/.jpg/.webp) works too, held for the whole span: posters that pop in one by one.
    audio=True plays the clip's own sound at full and mutes his camera over the same span, crossfading
    back to the voice at the end (a clip he reacts to).
    bottom only: height= makes the window that tall (it may run past the safe line for a clip he
    reacts to: "way bigger, it should be clear"), lift= slides the face up that many px while it is up."""
    return {"broll": path, "mode": mode, "start": start, "top": top, "audio": audio, "height": height, "lift": lift}


# ---------------- icons ----------------
CHECK = f'<span class="icon" style="width:64px;height:64px;background:{BRIGHT};font-size:40px">&#10003;</span>'
CROSS = f'<span class="icon" style="width:64px;height:64px;background:{RED};font-size:40px">&#10005;</span>'
PLAY = '<svg width="70" height="70" viewBox="0 0 24 24"><circle cx="12" cy="12" r="12" fill="rgba(255,255,255,.95)"/><path d="M10 7.5v9l7-4.5z" fill="#080B14"/></svg>'
CURSOR = '<svg width="80" height="100" viewBox="0 0 24 30" style="position:absolute"><path d="M2 2 L2 24 L8 18 L12 28 L16 26 L12 17 L20 17 Z" fill="#fff" stroke="#080B14" stroke-width="1.6" stroke-linejoin="round"/></svg>'
PHOTO = f"""<svg width="100%" height="100%" viewBox="0 0 300 150" preserveAspectRatio="xMidYMid slice"><defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8EC5FF"/><stop offset="1" stop-color="#DCEBFF"/></linearGradient></defs>
  <rect width="300" height="150" fill="url(#sky)"/><circle cx="230" cy="45" r="18" fill="#FFD166"/>
  <path d="M0 150 L80 60 L140 120 L190 80 L300 150Z" fill="{BLUE}"/><path d="M0 150 L60 110 L120 150Z" fill="{BRIGHT}"/></svg>"""


# ---------------- overlay cards ----------------
def hook_card(html, size=106):
    """Frame-one text hook. Use hl() on one word. Keep it 7 words or fewer, 2 lines max."""
    return overlay(f"""<div class="card" style="width:1150px;padding:54px 60px;text-align:center">
      <div style="font-weight:900;font-size:{size}px;line-height:1.12;letter-spacing:-2px">{html}</div></div>""")


def pill(label, kind="good"):
    """Cause pill: good = blue + check, bad = red + cross, plain = ink, no mark."""
    if kind == "plain":
        return f'<div class="row" style="padding:12px 30px;border-radius:999px;background:{INK};color:#fff;font-size:46px;font-weight:800">{label}</div>'
    bg, mark = (BRIGHT, "&#10003;") if kind == "good" else (RED, "&#10005;")
    return f"""<div class="row" style="gap:14px;padding:12px 30px 12px 14px;border-radius:999px;background:{bg};color:#fff;font-size:46px;font-weight:800">
      <span class="icon" style="width:52px;height:52px;background:#fff;color:{bg};font-size:32px">{mark}</span>{label}</div>"""


def takeaway(pills, headline, sub="", color=INK):
    """THE takeaway card: centered, cause pills on top, one big result line, optional muted sub-line.
    pills: [("Good UI", "good"), ("Bad UX", "bad")]. Never left-aligned stacks, never dangling arrows."""
    top = f'<div class="row" style="justify-content:center;gap:18px;margin-bottom:26px">{"".join(pill(l, k) for l, k in pills)}</div>' if pills else ""
    return overlay(f"""<div class="card" style="width:fit-content;min-width:760px;max-width:1150px;padding:40px 56px 44px;text-align:center">
      {top}<div style="font-size:68px;font-weight:900;line-height:1.1;color:{color};white-space:nowrap">{headline}</div>
      {f'<div style="font-size:44px;font-weight:700;color:{MUTED};margin-top:12px">{sub}</div>' if sub else ''}</div>""")


def follow_card(line):
    """Growth CTA. line e.g. f"Build {hl('proper')} software with AI"."""
    return overlay(f"""<div class="card" style="width:1000px;padding:40px 50px;text-align:center">
      <div style="margin:0 auto;width:fit-content;padding:22px 80px;border-radius:24px;background:{BRIGHT};color:#fff;font-size:64px;font-weight:900">Follow</div>
      <div style="font-size:54px;font-weight:800;margin-top:26px;line-height:1.2">{line}</div></div>""")


def send_card(line):
    """Growth CTA built for sends: 'Send this to the friend whose project broke'."""
    return overlay(f"""<div class="card" style="width:1000px;padding:40px 50px;text-align:center">
      <div style="margin:0 auto;width:fit-content;padding:22px 70px;border-radius:24px;background:{BRIGHT};color:#fff;font-size:60px;font-weight:900">&#10148; Send this</div>
      <div style="font-size:52px;font-weight:800;margin-top:26px;line-height:1.2">{line}</div></div>""")


def keyword_card(keyword, line, verb="Comment"):
    """Authority / Sales CTA. keyword MUST be a ready row in Freebies/registry.md. Never invent one."""
    return overlay(f"""<div class="card" style="width:1000px;padding:40px 50px;text-align:center">
      <div style="font-size:50px;font-weight:800;color:{MUTED}">{verb}</div>
      <div style="margin:10px auto 0;width:fit-content;padding:14px 60px;border-radius:24px;background:{YELLOW};color:{INK};font-size:110px;font-weight:900;letter-spacing:4px">{keyword}</div>
      <div style="font-size:50px;font-weight:800;margin-top:26px;line-height:1.2">{line}</div></div>""")


# ---------------- full-screen building blocks (put inside full(...)) ----------------
def title_block(kicker, title, size=112):
    return f"""<div class="safe" style="text-align:center"><div class="kicker">{kicker}</div>
      <div class="t-white" style="font-weight:900;font-size:{size}px;line-height:1.05;margin-top:14px">{title}</div></div>"""


def statement(big, line, tag="", sub="", tag_color=RED, top=470):
    """One huge word + one line. For definitions and reveals: 'UX = User Experience'."""
    t = f'<div class="chip" style="background:{tag_color};color:#fff;font-size:60px;padding:18px 44px">{tag}</div>' if tag else ""
    s = f'<div style="font-size:52px;color:#9AA3B2;font-weight:600">{sub}</div>' if sub else ""
    return f"""<div class="safe" style="top:{top}px;display:flex;flex-direction:column;align-items:center;gap:36px">
      {t}<div class="t-white" style="font-size:380px;font-weight:900;line-height:1;letter-spacing:-10px">{big}</div>
      <div class="t-white" style="font-size:100px;font-weight:800;text-align:center">{line}</div>{s}</div>"""


def big_number(number, label, sub=""):
    """A single stat. Only real numbers with a source; proof before promise."""
    s = f'<div style="font-size:52px;color:#9AA3B2;font-weight:600;margin-top:20px">{sub}</div>' if sub else ""
    return f"""<div class="safe" style="top:560px;text-align:center">
      <div style="font-size:340px;font-weight:900;line-height:1;color:{BRIGHT};letter-spacing:-8px">{number}</div>
      <div class="t-white" style="font-size:96px;font-weight:900;margin-top:20px">{label}</div>{s}</div>"""


def list_rows(items, current, width=None):
    """A list that builds in sync with the voice. items: [(label, icon_html_or_""), ...].
    Rows up to `current` are shown, `current` is highlighted, later rows reserve their space."""
    rows = ""
    for i, (label, icon) in enumerate(items):
        if i > current:
            rows += '<div style="height:140px"></div>'
            continue
        on = i == current
        ic = f'<span style="width:96px;display:inline-flex;justify-content:center">{icon}</span>' if icon else ""
        rows += f"""<div class="row" style="height:124px;margin-bottom:16px;gap:22px;padding:0 28px;border-radius:28px;
            background:{BRIGHT if on else 'rgba(255,255,255,.06)'};color:{'#fff' if on else '#C9CFDA'};font-size:60px;font-weight:800">{ic}{label}</div>"""
    return f'<div style="width:{width or SAFE_W}px">{rows}</div>'


def steps(kicker, title, items, current):
    """Full-screen numbered list that builds item by item. Wrap in full(...)."""
    numbered = [(f"{i + 1}. {label}", "") for i, label in enumerate(items)]
    return title_block(kicker, title) + f'<div style="position:absolute;left:{SAFE_L}px;top:720px">{list_rows(numbered, current)}</div>'


def phone(inner, small=False):
    return f'<div class="phone{" sm" if small else ""}"><div class="notch"></div>{inner}</div>'


def browser(inner, url="myapp.com", w=900, h=430):
    return f"""<div style="width:{w}px;height:{h}px;border-radius:32px;background:#fff;overflow:hidden;box-shadow:0 30px 80px rgba(0,0,0,.5)">
      <div class="row" style="height:72px;background:{PANEL};gap:14px;padding:0 28px;border-bottom:1px solid #E4E7EC">
        {''.join(f'<div style="width:22px;height:22px;border-radius:50%;background:{c}"></div>' for c in ['#FF5F57', '#FEBC2E', '#28C840'])}
        <div style="margin-left:20px;flex:1;height:42px;border-radius:21px;background:#fff;border:1px solid #E4E7EC;font-size:24px;color:{MUTED};display:flex;align-items:center;padding-left:22px">{url}</div></div>
      <div style="position:relative;height:{h - 72}px">{inner}</div></div>"""


def vs(a_big, a_small, b_big, b_small, kicker="what's the difference?"):
    """Two boxes side by side. Fits a split panel."""
    def box(big, small, bg, fg):
        return f"""<div style="width:470px;height:470px;border-radius:44px;background:{bg};display:flex;flex-direction:column;align-items:center;justify-content:center;gap:20px">
          <div style="font-size:180px;font-weight:900;color:{fg};line-height:1">{big}</div>
          <div style="font-size:44px;font-weight:700;color:{fg};opacity:.8">{small}</div></div>"""
    return f"""<div style="text-align:center"><div class="kicker">{kicker}</div>
      <div class="row" style="margin-top:30px;justify-content:center;gap:40px">
        {box(a_big, a_small, BRIGHT, '#fff')}<div style="font-size:80px;font-weight:900;color:#fff">vs</div>{box(b_big, b_small, '#fff', INK)}</div></div>"""


def wrong_right(wrong, right, show_right=True):
    """Mistake vs fix, stacked. Fits a split panel. Build it in two states: right hidden, then shown."""
    r = f"""<div class="row" style="gap:24px;margin-top:24px;padding:30px 36px;border-radius:32px;background:#fff;font-size:54px;font-weight:800">{CHECK}{right}</div>""" if show_right else '<div style="height:150px"></div>'
    return f"""<div class="row" style="gap:24px;padding:30px 36px;border-radius:32px;background:rgba(255,255,255,.08);color:#C9CFDA;font-size:54px;font-weight:800">{CROSS}<span style="text-decoration:line-through;text-decoration-color:{RED};text-decoration-thickness:6px">{wrong}</span></div>{r}"""


def chat(prompt, reply_html, reply_label="&#10022; AI"):
    """A prompt bubble and an AI reply card. Fits a split panel."""
    return f"""<div style="width:fit-content;margin-left:auto;padding:26px 36px;border-radius:32px 32px 8px 32px;background:{BRIGHT};color:#fff;font-size:42px;font-weight:700">{prompt}</div>
      <div style="margin-top:20px;width:720px;padding:28px 34px;border-radius:32px 32px 32px 8px;background:#fff">
        <div class="row" style="gap:14px;font-size:34px;font-weight:800">{reply_label}</div><div style="margin-top:16px">{reply_html}</div></div>"""


def demo_app(ring=None, grid=False):
    """A clean good-UI app screen. ring: colors|images|videos|buttons highlights that part in yellow;
    grid=True draws the layout boxes."""
    r = lambda k: "ring" if ring == k else ""
    layout = ""
    if grid:
        boxes = [(40, 120, None), (190, 270, None), (490, 300, "l"), (490, 300, "r"), (None, 120, None)]
        layout = '<div style="position:absolute;inset:36px 0 0 0">' + "".join(
            f'<div style="position:absolute;{"left:32px;right:32px" if s is None else ("left:32px;width:262px" if s == "l" else "right:32px;width:262px")};'
            f'{"bottom:60px" if t is None else f"top:{t}px"};height:{h}px;border:5px dashed {BRIGHT};border-radius:16px"></div>'
            for t, h, s in boxes) + "</div>"
    swatch = ""
    if ring == "colors":
        swatch = '<div class="row" style="position:absolute;left:44px;right:44px;top:56px;justify-content:center;gap:14px;z-index:3">' + "".join(
            f'<div style="width:78px;height:78px;border-radius:22px;background:{c};border:5px solid #fff;box-shadow:0 6px 16px rgba(0,0,0,.25)"></div>'
            for c in [BLUE, BRIGHT, "#FFB020", PANEL, INK]) + "</div>"
    return f"""<div class="phone"><div class="notch"></div>{swatch}
      <div style="padding:40px 44px 0">
        <div class="row" style="justify-content:space-between;height:120px">
          <div><div style="font-size:30px;color:{MUTED};font-weight:600">Good morning</div>
          <div style="font-size:52px;font-weight:800">Explore</div></div>
          <div style="width:88px;height:88px;border-radius:50%;background:linear-gradient(135deg,{BRIGHT},{BLUE})"></div></div>
        <div class="{r('images')}" style="margin-top:30px;height:270px;border-radius:32px;overflow:hidden;position:relative">{PHOTO}
          <div style="position:absolute;left:28px;bottom:22px;color:#fff;font-size:40px;font-weight:800;text-shadow:0 2px 8px rgba(0,0,0,.4)">Weekend trips</div></div>
        <div class="row" style="gap:28px;margin-top:30px">
          <div class="{r('videos')}" style="flex:1;height:300px;border-radius:28px;background:linear-gradient(160deg,#1B2440,{BLUE});display:flex;align-items:center;justify-content:center;position:relative">{PLAY}
            <div style="position:absolute;left:24px;bottom:20px;color:#fff;font-size:28px;font-weight:700">0:42</div></div>
          <div style="flex:1;height:300px;border-radius:28px;background:{PANEL};padding:30px"><div style="width:64px;height:64px;border-radius:18px;background:#FFB020"></div>
            <div style="font-size:36px;font-weight:800;margin-top:30px">Saved</div><div style="font-size:28px;color:{MUTED};margin-top:8px">12 places</div></div>
        </div>
        <div class="{r('buttons')}" style="position:absolute;left:44px;right:44px;bottom:70px;height:120px;border-radius:30px;background:{BRIGHT};color:#fff;font-size:44px;font-weight:800;display:flex;align-items:center;justify-content:center">Book now</div>
      </div>{layout}</div>"""


# ---------------- captions ----------------
def caption_css(lang="ar"):
    """Plain white, weight 800, soft shadow. 78px Arabic / 70px English keeps a 4-5 word chunk on one line."""
    d = "rtl" if lang == "ar" else "ltr"
    return f"""
.cap {{ display:inline-block; max-width:1290px; text-align:center; direction:{d}; unicode-bidi:plaintext;
  font-family: {f"'{LATIN}', '{ARABIC}'" if lang == 'ar' else f"'{LATIN}'"}, sans-serif; font-weight:800; font-size:{78 if lang == 'ar' else 74}px; line-height:1.3; color:#fff; padding:44px 50px;
  text-shadow: 0 0 3px rgba(0,0,0,.9), 0 3px 6px rgba(0,0,0,.8), 0 8px 26px rgba(0,0,0,.55); }}
.cap .en {{ font-family: '{LATIN}', sans-serif; font-weight:800; font-size:{'.9em' if lang == 'ar' else '1em'}; }}
.cap .kw {{ color: {YELLOW}; }}
.cap .big {{ font-size: 1.6em; line-height: 1; }}
.cap .big .en, .cap .en .big {{ font-size: inherit; }}
"""
