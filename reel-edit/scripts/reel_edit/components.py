"""Brand components for /reel-edit. Every visual is HTML rendered to a transparent PNG.

Canvas is the 1440x2560 master (exported at 1080x1920). Instagram safe box: x 90..1350, y 360..1920 (centered on the frame).
Brand palette and fonts: brand.json at the skill root (see reel_edit/brand.py).

An edit.py builds VISUALS from these. Each value is one of:
    overlay(html)   graphic overlay over the face (top_pill, hook_card, float_card and the CTAs are overlays)
    light(inner)    THE DEFAULT SCREEN: a light background, the graphic in the top part (panel()), and
                    the face shrinking from full screen into a tall rounded rectangle under it.
                    layout="blur" puts it on the speaker's own footage, blurred
    hard(inner)     the hard split: the graphic edge to edge on top, the face edge to edge below
    corner(src)     screen first: a recording or graphic full screen, the face small at the top left
    cutout(inner)   the speaker cut out of their background, standing in front of the graphic
    split(inner)    face video on top, dark graphic panel below SPLIT_Y (the older look)
    full(inner)     full-screen graphic, voice carries on (a full takeover)
    broll(path, mode="full"|"split"|"pip"|"bottom"|"panel"|"top", start=0)   a real video clip, muted

The default look (light mode, user's call 10 Nov 2026): the face with white pills at the top for names,
labels and numbers; a split with the face in a vertical rectangle for anything worth seeing, varied with the
other layouts by the size of the visual (14 Nov 2026, SKILL.md "The layouts, and which one when");
captions with one *keyword* in the accent color.
"""

from .brand import INK, PANEL, MUTED, BLUE, BRIGHT, YELLOW, RED, SURFACE, TINT, ACCENT, LATIN, ARABIC, FONTS_URL
W, H = 1440, 2560
SAFE_L, SAFE_R, SAFE_T, SAFE_B = 90, 1350, 360, 1920   # symmetric left/right: everything centers on the frame (x = 720)
SAFE_W = SAFE_R - SAFE_L
SPLIT_Y = 1150          # split mode: face video above, panel below
SPLIT_H = H - SPLIT_Y
PIP = (1000, 700)       # b-roll picture-in-picture window size (top of safe box)
BOTTOM_TOP = 1100       # b-roll "bottom" window: from just under the mouth down to the safe box's bottom edge
BOTTOM_CAP_Y = 1835     # captions sit across that window's bottom edge while it is up, clear of the face
# light screens: the graphic sits in PANEL_BOX, the face in FACE_BOX, a tall rounded rectangle with its bottom on
# the safe line (the default since 14 Nov 2026: a wide square crops a talking face badly). face_square() = the old box.
FACE_BOX = (420, 1140, 600, 780)        # x, y, w, h
PANEL_BOX = (120, 380, 1200, FACE_BOX[1] - 45 - 380)   # x, y, w, h: ends 45 px above the face box
FACE_RADIUS = 44
FACE_CAP_Y = FACE_BOX[1] + FACE_BOX[3] - 90    # captions sit inside the bottom of the face box
HARD_Y = 1280                            # hard split: the visual edge to edge above, the face edge to edge below
CORNER_BOX = (130, 400, 400, 520)        # screen first: the face top left, inside the safe edges, not in the corner
PILL_TOP = SAFE_T + 12                   # white pills and the hook, at the top of the safe box
ICONS = "https://cdn.jsdelivr.net/npm/lucide-static@0.460.0/icons"        # lucide.dev names: globe, database, lock...
LOGOS = "https://cdn.jsdelivr.net/npm/simple-icons@13.21.0/icons"          # simpleicons.org slugs: supabase, github...
SHADOW = "0 22px 56px rgba(0,81,189,.14), 0 3px 10px rgba(8,11,20,.07)"   # soft, a little blue, like the brand's cards

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
/* Text over footage, scoped so demo UI and cover styling retain their own design. */
.text-overlay {{ width:1150px; padding:8px 12px; text-align:center; color:#fff;
  font-weight:800; line-height:1.18; direction:rtl; unicode-bidi:plaintext;
  -webkit-text-stroke:3px rgba(0,0,0,.9); paint-order:stroke fill;
  text-shadow:0 3px 8px rgba(0,0,0,.6); }}
.text-overlay .hl {{ background:transparent; color:inherit; padding:0; border-radius:0; }}
.text-overlay .context {{ font-size:42px; font-weight:700; margin-bottom:12px; }}
.text-overlay .support {{ font-size:44px; font-weight:700; margin-top:12px; }}

.ring {{ outline: 9px solid {YELLOW}; outline-offset: 6px; }}

/* light mode */
.light {{ width: {W}px; height: {H}px; position: relative; overflow: hidden; background:
  radial-gradient(1200px 900px at 50% 0%, rgba(47,107,255,.10), transparent 70%), {SURFACE}; }}
.panel {{ position: absolute; left: {PANEL_BOX[0]}px; top: {PANEL_BOX[1]}px; width: {PANEL_BOX[2]}px; height: {PANEL_BOX[3]}px;
  background: #fff; border-radius: 44px; box-shadow: {SHADOW}; overflow: hidden;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 36px; }}
.panel.dots {{ background-image: radial-gradient(rgba(8,11,20,.09) 2px, transparent 2px); background-size: 34px 34px; }}
.panel.bare {{ background: transparent; box-shadow: none; }}
.pill {{ display: inline-flex; align-items: center; gap: 28px; background: #fff; color: {INK}; border-radius: 40px;
  padding: 22px 44px 22px 22px; box-shadow: {SHADOW}; font-weight: 800; line-height: 1.1; white-space: nowrap;
  max-width: {SAFE_W}px; unicode-bidi: plaintext; }}
.pill.text {{ display: block; white-space: normal; text-align: center; padding: 30px 52px; line-height: 1.16; direction: rtl; }}
.pill .sub {{ font-weight: 700; color: {MUTED}; }}
.tile {{ display: inline-flex; align-items: center; justify-content: center; flex: none; }}
.tag {{ display: inline-flex; align-items: center; gap: 12px; border-radius: 999px; font-weight: 700; padding: 8px 24px; }}
.box {{ background: #fff; border-radius: 32px; box-shadow: {SHADOW}; display: flex; flex-direction: column;
  align-items: center; justify-content: center; gap: 18px; font-weight: 800; color: {INK}; }}
.box > span {{ text-align: center; line-height: 1.15; padding: 0 22px; }}
.light.clear {{ background: transparent; }}
.hard {{ width: {W}px; height: {H}px; position: relative; overflow: hidden; background: {INK}; }}
.hard-top {{ position: absolute; left: 0; top: 0; width: {W}px; height: {HARD_Y}px; overflow: hidden;
  background: linear-gradient(160deg, {BLUE}, {BRIGHT}); display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 36px; padding: {SAFE_T}px {SAFE_L}px 40px; }}
.hard-top.bleed {{ padding: 0; }}
.hard-top.bleed > img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
.float {{ display: inline-flex; flex-direction: column; align-items: center; gap: 16px; background: #fff; border-radius: 36px;
  box-shadow: {SHADOW}; padding: 18px; overflow: hidden; font-weight: 800; color: {INK}; }}
.float img {{ display: block; border-radius: 22px; }}
"""


def _face_box(w, h, cap_off):
    global PANEL_BOX, FACE_BOX, FACE_CAP_Y, CSS
    FACE_BOX = ((W - w) // 2, SAFE_B - h, w, h)
    PANEL_BOX = (120, 380, 1200, FACE_BOX[1] - 45 - 380)
    FACE_CAP_Y = FACE_BOX[1] + FACE_BOX[3] - cap_off
    CSS = CSS.split("/* layout */")[0] + f"""/* layout */
.panel {{ top: {PANEL_BOX[1]}px; height: {PANEL_BOX[3]}px; }}
"""


def face_portrait(w=600, h=780):
    """The face box on light screens is this tall rounded rectangle by default (14 Nov 2026). Call it at the top
    of an edit.py only to change its size; build.py and render.py read the layout after loading edit.py."""
    _face_box(w, h, 90)


def face_square():
    """The old wide face box (786x685), only when the user asks for the square."""
    _face_box(786, 685, 100)


def hl(text):
    """The one yellow 'look here' word. Max one per visual."""
    return f"<span class='hl'>{text}</span>"


# ---------------- layout wrappers ----------------
def overlay(html, top=None, motion="ease"):
    """top= visible top edge in master px. motion: ease (graphics) or cut (stationary text)."""
    # a card that changes in place: first state "in", middle states "quick", last state "quick-out"
    if motion not in ("ease", "cut", "in", "out", "quick", "quick-out"):
        raise ValueError("overlay motion must be one of ease, cut, in, out, quick, quick-out")
    return (html, "overlay", {"top": top, "motion": motion})


def full(inner, grid=True, motion="cut"):
    """Enters and leaves on a hard cut, like a cut between clips. Start it on the word it shows.
    motion="ease" brings back the fade."""
    return (f'<div class="full{" grid-bg" if grid else ""}">{inner}</div>', "full", {"motion": motion})


def split(inner, motion="cut"):
    """inner is laid out inside the panel's safe column. Keep it under ~560px tall:
    the caption sits at y 1845, inside the panel."""
    return (f'<div class="split grid-bg"><div class="pan">{inner}</div></div>', "split", {"motion": motion})


def broll(path, mode="full", start=0.0, top=None, audio=False, height=None, lift=0, motion="ease"):
    """A real clip (screen recording, footage). Muted, frozen on its last frame if short.
    full / split / pip cover-crop the clip to their shape. bottom shows it whole, not cropped, in a
    rounded window under the face (a clip he reacts to while talking); top= moves that window's top edge.
    A still image (.png/.jpg/.webp) works too, held for the whole span: posters that pop in one by one.
    audio=True plays the clip's own sound at full and mutes the camera sound over the same span, crossfading
    back to the voice at the end (a clip he reacts to).
    bottom only: height= makes the window that tall (it may run past the safe line for a clip he
    reacts to: "way bigger, it should be clear"), lift= slides the face up that many px while it is up."""
    return {"broll": path, "mode": mode, "start": start, "top": top, "audio": audio, "height": height, "lift": lift, "motion": motion}


# ---------------- icons ----------------
CHECK = f'<span class="icon" style="width:64px;height:64px;background:{BRIGHT};font-size:40px">&#10003;</span>'
CROSS = f'<span class="icon" style="width:64px;height:64px;background:{RED};font-size:40px">&#10005;</span>'
PLAY = '<svg width="70" height="70" viewBox="0 0 24 24"><circle cx="12" cy="12" r="12" fill="rgba(255,255,255,.95)"/><path d="M10 7.5v9l7-4.5z" fill="#080B14"/></svg>'
CURSOR = '<svg width="80" height="100" viewBox="0 0 24 30" style="position:absolute"><path d="M2 2 L2 24 L8 18 L12 28 L16 26 L12 17 L20 17 Z" fill="#fff" stroke="#080B14" stroke-width="1.6" stroke-linejoin="round"/></svg>'
PHOTO = f"""<svg width="100%" height="100%" viewBox="0 0 300 150" preserveAspectRatio="xMidYMid slice"><defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#8EC5FF"/><stop offset="1" stop-color="#DCEBFF"/></linearGradient></defs>
  <rect width="300" height="150" fill="url(#sky)"/><circle cx="230" cy="45" r="18" fill="#FFD166"/>
  <path d="M0 150 L80 60 L140 120 L190 80 L300 150Z" fill="{BLUE}"/><path d="M0 150 L60 110 L120 150Z" fill="{BRIGHT}"/></svg>"""


# ---------------- overlay cards ----------------
def hook_card(html, size=74, style="pill"):
    """The text hook (and any title above the head): a white pill at the top, on frame one.
    Seven words or fewer, at most two lines. style="outline" is the old plain outlined text."""
    if style == "outline":
        return overlay(f'<div class="text-overlay" style="font-size:{size * 1.4:.0f}px">{html}</div>', top=PILL_TOP, motion="cut")
    return overlay(f'<div class="pill text" style="font-size:{size}px;max-width:1180px">{html}</div>', top=PILL_TOP, motion="cut")

def pill(label, kind="good"):
    """Cause pill: good = blue + check, bad = red + cross, plain = ink, no mark."""
    if kind == "plain":
        return f'<div class="row" style="padding:12px 30px;border-radius:999px;background:{INK};color:#fff;font-size:46px;font-weight:800">{label}</div>'
    bg, mark = (BRIGHT, "&#10003;") if kind == "good" else (RED, "&#10005;")
    return f"""<div class="row" style="gap:14px;padding:12px 30px 12px 14px;border-radius:999px;background:{bg};color:#fff;font-size:46px;font-weight:800">
      <span class="icon" style="width:52px;height:52px;background:#fff;color:{bg};font-size:32px">{mark}</span>{label}</div>"""


def takeaway(pills, headline, sub="", color=INK):
    """Plain takeaway. Legacy pills/color arguments remain accepted, without badges or color fills."""
    context = " · ".join(label for label, kind in (pills or []))
    return overlay(f"""<div class="pill text" style="font-size:66px;max-width:1180px">
      {f'<div class="sub" style="font-size:40px;margin-bottom:10px">{context}</div>' if context else ''}
      <div>{headline}</div>
      {f'<div class="sub" style="font-size:42px;margin-top:10px">{sub}</div>' if sub else ''}</div>""",
      top=PILL_TOP, motion="ease")


def _cta(icon_name, head, line):
    return overlay(f"""<div class="pill" style="flex-direction:column;gap:14px;padding:30px 52px;white-space:normal;text-align:center">
      <div class="row" style="gap:26px;font-size:76px;justify-content:center">{tile(icon(icon_name, 54, "#fff"), 104) if icon_name else ""}<span>{head}</span></div>
      <div class="sub" style="font-size:42px;max-width:1080px">{line}</div></div>""", top=PILL_TOP, motion="ease")


def follow_card(line):
    """Growth CTA: a white pill, the follow icon, "Follow" and the line under it."""
    return _cta("user-plus", "Follow", line)


def send_card(line):
    """Send CTA as a white pill."""
    return _cta("send", "Send this", line)


def keyword_card(keyword, line, verb="Comment", icon_name=None):
    """Keyword CTA as a white pill, centered: "Comment KEYWORD" with the keyword in the brand color, the line
    under it. No icon by default (his call, 14 Nov 2026); icon_name="message-circle" brings the tile back."""
    return _cta(icon_name, f'{verb} <span style="color:{BRIGHT}">{keyword}</span>', line)

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


# ---------------- light mode (the default look) ----------------
def icon(name, size=56, color=None):
    """A lucide.dev line icon in any color (globe, smartphone, database, lock, link, check, arrow-right,
    cpu, mail, users, repeat, message-circle, search, code, server, zap...). Loaded from the CDN at render."""
    url = f"{ICONS}/{name}.svg"
    return (f'<span style="display:inline-block;width:{size}px;height:{size}px;flex:none;background:{color or BRIGHT};'
            f'-webkit-mask:url({url}) center/contain no-repeat;mask:url({url}) center/contain no-repeat"></span>')


def brand_logo(slug, size=56, color=None):
    """A real app or brand logo from simpleicons.org, in its brand color (pass color='#3ECF8E' for Supabase).
    Never draw a fake logo: if the brand is not on simple-icons, use its own SVG from the reel folder."""
    url = f"{LOGOS}/{slug}.svg"
    return (f'<span style="display:inline-block;width:{size}px;height:{size}px;flex:none;background:{color or INK};'
            f'-webkit-mask:url({url}) center/contain no-repeat;mask:url({url}) center/contain no-repeat"></span>')


def tile(inner, size=96, bg=None, radius=None):
    """A rounded icon tile: the brand blue with a white icon by default, or bg=TINT with a blue icon."""
    return (f'<span class="tile" style="width:{size}px;height:{size}px;border-radius:{radius or round(size * .28)}px;'
            f'background:{bg or BRIGHT}">{inner}</span>')


def tag(text, color=None, bg=None, dot=True, size=40):
    """A small rounded tag beside a label: "1+ year", "Open Source", "Free"."""
    c = color or BRIGHT
    d = f'<span style="width:{size // 3}px;height:{size // 3}px;border-radius:50%;background:{c}"></span>' if dot else ""
    return f'<span class="tag" style="font-size:{size}px;color:{c};background:{bg or TINT}">{d}{text}</span>'


def pill_html(label, icon_html=None, sub=None, size=80, after=""):
    """The white pill itself, as HTML (to place inside a panel, or to build states of)."""
    ic = tile(icon_html, round(size * 1.3)) if icon_html else ""
    s = f'<span class="sub" style="font-size:{round(size * .55)}px">{sub}</span>' if sub else ""
    pad = "" if ic else "padding-left:44px;"
    return f'<div class="pill" style="font-size:{size}px;{pad}">{ic}<span>{label}</span>{s}{after}</div>'


def top_pill(label, icon_html=None, sub=None, size=80, after="", motion="ease"):
    """A white pill at the top, over the face: the name, label or number being said ("Supabase", "20+
    automations", "Responsive"). States of one pill: motion "in", then "quick", last "quick-out".
    icon_html: icon("globe", 64, "#fff") or brand_logo("supabase", 64, "#fff"); it sits on a blue tile.
    after: anything appended inside the pill (a tag(), an arrow and a second icon, a check)."""
    return overlay(pill_html(label, icon_html, sub, size, after), top=PILL_TOP, motion=motion)


LAYOUTS = ("light", "blur", "hard", "corner")


def light(inner, face=True, motion="cut", layout="light"):
    """THE DEFAULT SCREEN for anything worth seeing: a light background with `inner` (usually a panel())
    in the top part, and the face shrinking from full screen into the rounded rectangle FACE_BOX under it
    (and growing back at the end). Captions move inside the face box by themselves.
    layout="blur": the same, on the speaker's own footage blurred and dimmed instead of the light ground.
    layout="hard" / "corner": see hard() and corner().
    face=False: the light screen alone, no face (rare)."""
    if layout not in LAYOUTS:
        raise ValueError(f"layout must be one of {LAYOUTS}")
    if layout == "hard":
        return hard(inner, motion=motion)
    if layout == "corner":
        return corner(inner, motion=motion)
    cls = "light clear" if layout == "blur" else "light"
    return (f'<div class="{cls}">{inner}</div>', "full", {"motion": motion, "face": face, "layout": layout})


def hard(inner="", bleed=False, motion="cut"):
    """The hard split: the visual edge to edge over the top part (to HARD_Y), the face edge to edge under it,
    a straight seam, no light ground and no rounded box. inner is centered inside the safe part of the top
    (y SAFE_T to HARD_Y) on the brand gradient; bleed=True lets it fill the whole top (an image(..)).
    A screen recording there: put top_screen(clip) in the TIMELINE over hard() with the same span."""
    cls = "hard-top bleed" if bleed else "hard-top"
    return (f'<div class="hard"><div class="{cls}">{inner}</div></div>', "full",
            {"motion": motion, "face": True, "layout": "hard"})


def top_screen(path, start=0.0, audio=False):
    """A screen recording (or a still) filling the top part of a hard split, cover-cropped."""
    return broll(path, mode="top", start=start, audio=audio, motion="cut")


MEDIA = (".mp4", ".mov", ".webm", ".mkv", ".m4v", ".png", ".jpg", ".jpeg", ".webp")


def corner(src, start=0.0, audio=False, motion="cut"):
    """Screen first: the recording (a file path) or a graphic (HTML) full screen, and the face shrinking into a
    small rounded rectangle at the top left (CORNER_BOX, inside the safe edges, never in the far corner).
    A tall clip (a phone recording) fills the frame; a landscape one sits whole in a rounded window under the
    face. Captions sit low, under it. For a demo where the screen matters more than the face."""
    if isinstance(src, str) and src.lower().endswith(MEDIA):
        d = broll(src, mode="corner", start=start, audio=audio, motion=motion)
        d.update(face=True, layout="corner")
        return d
    return (f'<div class="light">{src}</div>', "full", {"motion": motion, "face": True, "layout": "corner"})


def cutout(inner, scale=0.82, motion="cut"):
    """The speaker cut out of their background (a matte per frame from scripts/matte.py, made by build.py on its
    own) standing in front of the graphic, scaled by `scale` and anchored to the bottom edge. inner is a
    full-screen graphic: put what matters in the top part (y 380 to ~1000), above the head. For a
    screenshot, article or post being explained or reacted to."""
    return (f'<div class="light">{inner}</div>', "full", {"motion": motion, "cutout": True, "scale": scale})


def image(path, w=None, h=None, fit="contain", radius=22):
    """A local image inlined into the HTML (the renderer cannot read file paths), sized in master px."""
    import base64, mimetypes
    mime = mimetypes.guess_type(path)[0] or "image/png"
    encoded = base64.b64encode(open(path, "rb").read()).decode()
    size = (f"width:{w}px;" if w else "") + (f"height:{h}px;" if h else "")
    return f'<img src="data:{mime};base64,{encoded}" style="{size}object-fit:{fit};border-radius:{radius}px;display:block">'


def float_card(inner, label=None, motion="ease", top=None):
    """A small visual floating over the full-screen face, above the head: a logo, a screenshot, a number, a
    post, a price. inner is usually image(path, w=..) or a big number. Keep it under ~380 px tall so it clears
    the eyes (build.py warns when a card reaches down to them). Small things only: something to read goes
    on a split."""
    lab = f'<div style="font-size:46px">{label}</div>' if label else ""
    return overlay(f'<div class="float">{inner}{lab}</div>', top=PILL_TOP if top is None else top, motion=motion)


def panel(inner, dots=False, bare=False, h=None, style=""):
    """The white card in the top part of a light screen (PANEL_BOX). Content is centered.
    dots=True adds a faint dot grid (diagrams); bare=True drops the card (content straight on the light
    background, or under a screen() recording). The face square starts 45 px under it."""
    cls = "panel" + (" dots" if dots else "") + (" bare" if bare else "")
    hh = f"height:{h}px;" if h else ""
    return f'<div class="{cls}" style="{hh}{style}">{inner}</div>'


def heading(text, icon_html=None, size=60):
    """A title inside a panel: an icon and bold text ("Supabase", "Cron Jobs")."""
    return f'<div class="row" style="gap:20px;font-size:{size}px;font-weight:800;color:{INK}">{icon_html or ""}<span>{text}</span></div>'


def box(label, icon_html=None, w=420, h=260, size=46, dim=False):
    """A small white box with an icon tile on top and a label: one item of a set (Authentication, Database).
    dim=True keeps its slot but shows it faded (an item not said yet, so the layout never jumps)."""
    ic = tile(icon_html, 92, TINT) if icon_html else ""
    return (f'<div class="box" style="width:{w}px;height:{h}px;font-size:{size}px;opacity:{.25 if dim else 1}">'
            f'{ic}<span>{label}</span></div>')


def screen(path, start=0.0, audio=False):
    """A screen recording (or a still) on a light screen: fitted into the top part, rounded, with a soft
    shadow. Put it in the TIMELINE on top of a light(panel("", bare=True)) visual with the same span."""
    return broll(path, mode="panel", start=start, audio=audio, motion="cut")


# ---------------- captions ----------------
def caption_css(lang="ar"):
    """Stationary white captions, weight 700, thin outline. Write natural 3-4 word chunks.
    *word* colors the one key term of a caption in the accent color (the tool, product or concept named)."""
    d = "rtl" if lang == "ar" else "ltr"
    return f"""
.cap {{ display:inline-block; white-space:nowrap; text-align:center; direction:{d}; unicode-bidi:plaintext;
  font-family: {f"'{ARABIC}', '{LATIN}'" if lang == 'ar' else f"'{LATIN}'"}, sans-serif; font-weight:700; font-size:{78 if lang == 'ar' else 74}px; line-height:1.3; color:#fff; padding:44px 50px;
  -webkit-text-stroke:3px rgba(0,0,0,.9); paint-order:stroke fill;
  text-shadow:0 3px 8px rgba(0,0,0,.6); }}
.cap .en {{ font-family: '{LATIN}', sans-serif; font-weight:700; font-size:{'.9em' if lang == 'ar' else '1em'}; }}
.cap .kw {{ color: {ACCENT}; }}
.cap.in-card {{ padding: 30px 24px; }}
.cap .big {{ font-size: 1.6em; line-height: 1; }}
.cap .big .en, .cap .en .big {{ font-size: inherit; }}
"""
