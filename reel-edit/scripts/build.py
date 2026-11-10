"""Composite the reel in one ffmpeg pass and export for Instagram.

    python build.py <workdir> [--out path] [--quality default|small|max] [--youtube]

Pipeline: normalize source to the 1440x2560 canvas -> punch-in zooms -> split-mode slide ->
visuals (graphics + b-roll) with eased motion -> the face square of light screens (it shrinks from full
screen into the square and grows back) -> captions -> sound effects -> 1080x1920 H.264 export.

--youtube builds the same edit ending at YOUTUBE_END (before the DM keyword ask, which only works on
Instagram), with a soft audio fade, to "<OUTPUT stem> - YouTube.mp4".
"""
import argparse, glob, json, os, subprocess
from PIL import Image, ImageDraw, ImageFilter
from reel_edit.project import load, kind_of
from reel_edit.components import (W, H, SAFE_L, SAFE_R, SAFE_W, SAFE_T, SAFE_B, SPLIT_Y, SPLIT_H, PIP, BOTTOM_TOP,
                                  BOTTOM_CAP_Y, PANEL_BOX, FACE_RADIUS, FACE_CAP_Y, PILL_TOP)

ap = argparse.ArgumentParser()
ap.add_argument("workdir")
ap.add_argument("--out")
ap.add_argument("--quality")
ap.add_argument("--youtube", action="store_true")
a = ap.parse_args()
p = load(a.workdir)
meta = json.load(open(os.path.join(p.png, "meta.json")))
OUT = a.out or p.output
END_FADE = 0.12   # the YouTube copy's last word fades out over this, like the Instagram ending
if a.youtube:
    # the same edit, ended before the keyword ask. Nothing new is said in the 0.3s end tail, so a caption or
    # card that starts in it (0.1s slack for one placed a few frames early) belongs to the ask and is gone
    if not p.youtube_end:
        raise SystemExit("--youtube needs YOUTUBE_END in edit.py (0.3s after the last word before the keyword ask)")
    p.dur = p.youtube_end
    cut = p.dur - 0.4
    p.captions = [(t, s, min(e, p.dur)) for t, s, e in p.captions if s < cut]
    if p.captions:   # the last caption left holds to the end, as it does on Instagram
        p.captions[-1] = (*p.captions[-1][:2], p.dur)
    p.timeline = [(v, s, min(e, p.dur)) for v, s, e in p.timeline if s < cut]
    OUT = a.out or f"{os.path.splitext(p.output)[0]} - YouTube.mp4"
CRF = {"small": 24, "default": 22, "max": 18}[a.quality or p.quality]

# ---- layout + motion (seconds). Text is stationary; footage/graphic motion is retained.
# cards sit high, in the empty space above the head, so they never cover the eyes
OVERLAY_Y, CAP_Y, CAP_Y_SPLIT = 260, 1700, 1845
OV_IN, OV_OUT, OV_RISE = 0.45, 0.35, 50   # cards: fade + ease-out rise
FS_IN, FS_OUT = 0.35, 0.35                # full / split from and back to the face
XF = 0.3                                  # crossfade between back-to-back solid states
QUICK = 0.15                              # quick fade between states of one card
SLIDE = 0.4                               # face slides up for split mode
FX, FY = p.face
SHIFT = max(0, FY - 575)                  # puts the face centre in the middle of the top area

vis = [[v, s, e, kind_of(p.visuals[v])] for v, s, e in p.timeline if e - s > 0.05]
STILL = (".png", ".jpg", ".jpeg", ".webp")
sounds = []                               # (input index, start, end, file, start in file) of b-roll clips whose sound plays
XA = 0.3                                  # the voice crossfades back in over this at a sound clip's end
SOLID = {"split", "full", "broll_full", "broll_split"}
CARD = {"overlay", "broll_pip", "broll_bottom", "broll_panel"}
WINDOW = {"broll_pip", "broll_bottom", "broll_panel"}   # rounded b-roll windows over the face video
GROW = 12                                 # frames (0.4 s) the face takes to shrink into the square and back
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPLITS = {"split", "broll_split"}


def adjacent(i, j):
    if not 0 <= j < len(vis):
        return False
    return abs((vis[j][1] - vis[i][2]) if j > i else (vis[i][1] - vis[j][2])) < 0.05


def solid(i):
    return vis[i][3] in SOLID


args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-stats", "-i", p.video]
# light temporal denoise on the camera only: sensor grain is where the bits go, and Instagram's
# re-encode smears it anyway. Visually identical, ~6% smaller on this camera.
# setpts first: a master joined from takes starts its video a few ms after 0, and without this the
# very first frame of the reel is the dark background with no face on it.
f = [f"[0:v]setpts=PTS-STARTPTS,hqdn3d=1.5:1.5:6:6,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30:start_time=0[src{0 if p.face_pip or p.face_card else str()}]"]
if p.face_pip or p.face_card:
    k = len(p.face_pip) + len(p.face_card)
    f.append(f"[src0]split={k + 1}[src]" + "".join(f"[srcp{j}]" for j in range(k)))

# ---- eased zooms: "hook" eases in over the spoken hook and cuts back, "in" eases in
# and holds (a reflective moment), "out" eases back (the realization). perspective takes float corners, so
# the zoom moves smoothly instead of stepping a whole pixel at a time the way crop/zoompan do.
face = "src"
if p.zoom:
    T = "(in/30)"   # [src] is fps=30 from 0, so frame n is second n/30

    def ease(s, e):
        u = f"clip(({T}-{s})/{e - s:.3f}\\,0\\,1)"
        return f"{u}*{u}*(3-2*{u})"

    level = "0"   # ffmpeg's parser rejects "+-", so each term carries its own sign
    for s, e, k in p.zoom:
        level += {"hook": f"+{ease(s, e)}*lt({T}\\,{e})", "in": f"+{ease(s, e)}", "out": f"-{ease(s, e)}"}[k]
    Z = f"(1+{p.zoom_level - 1:.4f}*clip({level}\\,0\\,1))"
    x0, y0 = f"({FX}-{FX}/{Z})", f"({FY}-{FY}/{Z})"
    x1, y1 = f"({x0}+{W}/{Z})", f"({y0}+{H}/{Z})"
    # only run it where a zoom is on screen: from the first window's start to the end of the last held stretch
    on, level = [], 0
    for s, e, k in p.zoom:
        if level == 0:
            on.append([s, e])
        on[-1][1] = e
        level = {"hook": 0, "in": 1, "out": 0}[k]
    if level:
        on[-1][1] = p.dur + 1
    en = "+".join(f"between(t,{s},{e + 0.05:.2f})" for s, e in on)
    f.append(f"[src]perspective=x0='{x0}':y0='{y0}':x1='{x1}':y1='{y0}':x2='{x0}':y2='{y1}':x3='{x1}':y3='{y1}'"
             f":interpolation=cubic:eval=frame:enable='{en}'[zm]")
    face = "zm"

# ---- punch-in zooms (hard cut in and out, anchored on the face)
if p.punch:
    z = p.punch_zoom
    en = "+".join(f"between(t,{s},{e})" for s, e in p.punch)
    f.append(f"[{face}]split[s0][s1]")
    f.append(f"[s1]crop=w=iw/{z}:h=ih/{z}:x={FX}-{FX}/{z}:y={FY}-{FY}/{z},scale={W}:{H}[pz]")
    f.append(f"[s0][pz]overlay=0:0:enable='{en}'[face]")
    face = "face"

# ---- blur private details on screen (user emails, keys): BLUR = [(start, end, (x, y, w, h)), ...]
for i, (s, e, (bx_, by_, bw_, bh_)) in enumerate(p.blur):
    f.append(f"[{face}]split[bl{i}a][bl{i}b]")
    f.append(f"[bl{i}b]crop={bw_}:{bh_}:{bx_}:{by_},boxblur=28:3[bl{i}c]")
    f.append(f"[bl{i}a][bl{i}c]overlay=x={bx_}:y={by_}:enable='between(t,{s},{e})'[blur{i}]")
    face = f"blur{i}"

# ---- split mode: the face slides up (smoothstep) instead of crossfading two positions (ghosting)
windows = []
for i, (v, s, e, k) in enumerate(vis):
    if k not in SPLITS:
        continue
    if windows and abs(windows[-1]["e"] - s) < 0.05:
        windows[-1].update(e=e, last=i)
    else:
        windows.append({"s": s, "e": e, "first": i, "last": i})
terms = []
for win in windows:
    s, e = win["s"], win["e"]
    if adjacent(win["last"], win["last"] + 1) and vis[win["last"] + 1][3] in {"full", "broll_full"}:
        e += XF + SLIDE  # a full screen covers it first, slide back down unseen
    q = f"(clip((t-{s})/{SLIDE}\\,0\\,1)*clip(({e:.2f}-t)/{SLIDE}\\,0\\,1))"
    terms.append(f"{SHIFT}*{q}*{q}*(3-2*{q})")
# a big bottom window lifts the face (lift= px) so the clip can be large and the face stays clear
for v, s, e, k in vis:
    lift = p.visuals[v].get("lift", 0) if k == "broll_bottom" else 0
    if lift:
        rise = "1" if s < 0.05 else f"clip((t-{s})/{SLIDE}\\,0\\,1)"   # already up on frame one
        q = f"({rise}*clip(({e:.2f}-t)/{SLIDE}\\,0\\,1))"
        terms.append(f"{lift}*{q}*{q}*(3-2*{q})")
if any(p.visuals[v].get("lift") for v, s, e, k in vis if k == "broll_bottom"):
    # a lifted face uncovers the bottom of the frame: fill it with the same shot, blurred, not flat black
    f.append(f"[{face}]split[facef][faceb]")
    f.append("[faceb]boxblur=40:4,eq=brightness=-0.06[bg]")
    face = "facef"
else:
    f.append(f"color=c=0x080B14:s={W}x{H}:r=30:d={p.dur + 0.5}[bg]")
f.append(f"[bg][{face}]overlay=x=0:y='-({'+'.join(terms) or '0'})':eval=frame:shortest=1[b0]")
last, n = "b0", 1

BORDER = 0  # px of white edge around a bottom window; 0 = round corners only


def bottom_box(b):
    """Top edge and size of a 'bottom' window: the whole clip, not cropped, as tall as the room
    between its top edge and the safe box's bottom allows."""
    top = b.get("top") or BOTTOM_TOP
    if b["broll"].lower().endswith(STILL):
        cw, ch = Image.open(b["broll"]).size
    else:
        cw, ch = (int(x) for x in subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", b["broll"]],
            capture_output=True, text=True, check=True).stdout.strip().split("x")[:2])
    k = b["height"] / ch if b.get("height") else min((SAFE_B - top) / ch, SAFE_W / cw)   # height= makes it bigger on purpose
    return top, (int(cw * k) // 2 * 2, int(ch * k) // 2 * 2)


def rounded(size, radius, circle=False):
    """An L mask, drawn 4x and scaled down so the edge is smooth."""
    big = Image.new("L", (max(1, size[0] * 4), max(1, size[1] * 4)), 0)
    d = ImageDraw.Draw(big)
    if circle:
        d.ellipse([0, 0, size[0] * 4 - 1, size[1] * 4 - 1], fill=255)
    else:
        d.rounded_rectangle([0, 0, size[0] * 4 - 1, size[1] * 4 - 1], radius=radius * 4, fill=255)
    return big.resize(size, Image.LANCZOS)


def window_mask(size, name, circle=False, radius=36):
    path = os.path.join(p.png, f"mask_{name}.png")
    rounded(size, radius, circle).save(path)
    return path


SHADOW_PAD, SHADOW_Y = 70, 18


def shadow_img(size, alpha=0.20):
    """A soft, slightly blue drop shadow for a rounded window, SHADOW_PAD bigger on every side."""
    w, h = size[0] + 2 * SHADOW_PAD, size[1] + 2 * SHADOW_PAD
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([SHADOW_PAD, SHADOW_PAD, w - SHADOW_PAD, h - SHADOW_PAD], radius=44, fill=int(255 * alpha))
    m = m.filter(ImageFilter.GaussianBlur(28))
    im = Image.new("RGBA", (w, h), (0, 40, 110, 0))
    im.putalpha(m)
    return im


def panel_box(b):
    """A screen recording on a light screen: fitted into PANEL_BOX, centered."""
    px, py, pw, ph = PANEL_BOX
    if b["broll"].lower().endswith(STILL):
        cw, ch = Image.open(b["broll"]).size
    else:
        cw, ch = (int(x) for x in subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", b["broll"]],
            capture_output=True, text=True, check=True).stdout.strip().split("x")[:2])
    k = min(pw / cw, ph / ch)
    bw, bh = int(cw * k) // 2 * 2, int(ch * k) // 2 * 2
    return py + (ph - bh) // 2, (bw, bh)

# ---- visuals
for i, (v, s, e, k) in enumerate(vis):
    xf_in = adjacent(i, i - 1) and solid(i) and solid(i - 1)
    xf_out = adjacent(i, i + 1) and solid(i) and solid(i + 1)
    end = e + XF if xf_out else e  # hold under the next state while it crossfades in
    # Card motion: ease (fade in + out), cut (neither), in / out (one side only), quick (a 0.15s fade in,
    # for the next state of the same card), quick-out (quick in, normal out: the last state).
    # in and quick hold QUICK past their end so the next state fades in on top of them, no dip between.
    val = p.visuals[v]
    motion = (val[2].get("motion", "ease") if isinstance(val, tuple) and len(val) > 2
              else val.get("motion", "ease") if isinstance(val, dict) else "ease")
    if k in CARD and motion in ("in", "quick"):
        end = max(end, e + QUICK)
    if k.startswith("broll"):
        b = p.visuals[v]
        win_top = OVERLAY_Y
        if k == "broll_bottom":
            win_top, (bw, bh) = bottom_box(b)
        elif k == "broll_panel":
            win_top, (bw, bh) = panel_box(b)
        else:
            bw, bh = {"broll_full": (W, H), "broll_split": (W, SPLIT_H), "broll_pip": PIP}[k]
        if b["broll"].lower().endswith(STILL):
            args += ["-loop", "1", "-framerate", "30", "-t", f"{end - s + 0.3:.2f}", "-itsoffset", f"{s}", "-i", b["broll"]]
        else:
            args += ["-ss", str(b["start"]), "-t", f"{end - s + 0.3:.2f}", "-itsoffset", f"{s}", "-i", b["broll"]]
            if b.get("audio"):
                sounds.append((n, s, e, b["broll"], b["start"]))
        fit = ((f"scale={bw - 2 * BORDER}:{bh - 2 * BORDER},pad={bw}:{bh}:{BORDER}:{BORDER}:white" if BORDER else f"scale={bw}:{bh}")
               if k in ("broll_bottom", "broll_panel")
               else f"scale={bw}:{bh}:force_original_aspect_ratio=increase,crop={bw}:{bh}")
        prep = f"{fit},setsar=1,fps=30,tpad=stop_mode=clone:stop_duration=30,format=rgba"
        f.append(f"[{n}:v]{prep}[bx{n}]")
        src_label, n_used = f"bx{n}", 1
        if k in WINDOW:
            args += ["-loop", "1", "-framerate", "30", "-t", f"{end - s + 0.3:.2f}", "-itsoffset", f"{s}", "-i", window_mask((bw, bh), v)]
            f.append(f"[{n + 1}:v]format=gray[bm{n}]")
            f.append(f"[bx{n}][bm{n}]alphamerge[ba{n}]")
            src_label, n_used = f"ba{n}", 2
    else:
        args += ["-loop", "1", "-framerate", "30", "-t", f"{end - s + 0.1:.2f}", "-itsoffset", f"{s}", "-i", os.path.join(p.png, f"v_{v}.png")]
        src_label, n_used = f"{n}:v", 1

    chain = "format=rgba"
    if k in CARD:
        options = p.visuals[v][2] if k == "overlay" and len(p.visuals[v]) > 2 else {}
        # motion is read above the loop branch (ease / cut / in / out / quick / quick-out)
        stationary = motion != "ease"
        if motion in ("ease", "in") and s >= 0.05:  # a visual that starts the reel is there on frame one, it does not fade in
            chain += f",fade=t=in:st={s}:d={OV_IN}:alpha=1"
        if motion in ("quick", "quick-out") and s >= 0.05:
            chain += f",fade=t=in:st={s}:d={QUICK}:alpha=1"
        if motion in ("ease", "out", "quick-out") and e < p.dur - 0.1:
            chain += f",fade=t=out:st={e - OV_OUT:.2f}:d={OV_OUT}:alpha=1"
        w = bw if k in WINDOW else meta[v]["w"]
        card_top = options.get("top")
        if card_top is None:
            card_top = OVERLAY_Y
        top = win_top if k in WINDOW else card_top - meta[v]["pad"]
        x = f"{SAFE_L + (SAFE_W - w) // 2}"
        if k in WINDOW and b.get("x") is not None:
            x = str(b["x"])
        y = str(top) if motion not in ("ease", "in") or s < 0.05 else f"'{top}+{OV_RISE}*pow(max(0\\,1-(t-{s})/{OV_IN})\\,3)'"
    else:
        # From the face to a full screen and back is a hard cut on the word, like a cut between clips
        # (a fade shows the face through the graphic). motion="ease" brings
        # the old fade and slide back. Two states of one graphic still crossfade into each other.
        opts = p.visuals[v][2] if isinstance(p.visuals[v], tuple) and len(p.visuals[v]) > 2 else {}
        eased = opts.get("motion") == "ease"
        if s >= 0.05 and (xf_in or eased):
            chain += f",fade=t=in:st={s}:d={XF if xf_in else FS_IN}:alpha=1"
        if eased and not xf_out and e < p.dur - 0.1:
            chain += f",fade=t=out:st={e - FS_OUT:.2f}:d={FS_OUT}:alpha=1"
        x, y = "0", "0"
        if k in SPLITS:
            y = str(SPLIT_Y) if (xf_in or not eased) else f"'{SPLIT_Y}+{OV_RISE * 2}*pow(max(0\\,1-(t-{s})/{SLIDE})\\,3)'"
    f.append(f"[{src_label}]{chain}[v{n}]")
    enabled = f"gte(t,{s})*lt(t,{end:.2f})" if k == "overlay" and stationary else f"between(t,{s},{end:.2f})"
    if k == "broll_panel":   # a soft shadow under the recording, so it sits on the light screen like a card
        sh = os.path.join(p.png, f"shadow_{v}.png")
        shadow_img((bw, bh)).save(sh)
        args += ["-loop", "1", "-framerate", "30", "-t", f"{end - s + 0.3:.2f}", "-itsoffset", f"{s}", "-i", sh]
        sx = SAFE_L + (SAFE_W - bw) // 2 - SHADOW_PAD
        f.append(f"[{last}][{n + n_used}:v]overlay=x={sx}:y={win_top - SHADOW_PAD + SHADOW_Y}:eof_action=pass:enable='{enabled}'[sh{n}]")
        last, n_used = f"sh{n}", n_used + 1
    f.append(f"[{last}][v{n}]overlay=x={x}:y={y}:eof_action=pass:enable='{enabled}'[o{n}]")

    last, n = f"o{n}", n + n_used


# ---- the face in a rounded window over full-screen graphics (a list reel: the list, the face, the illustration)
for j, fp in enumerate(p.face_pip):
    (cx, cy, cw, ch), (bx, by, bw, bh) = fp["crop"], fp["box"]
    ps, pe = fp["window"]
    circle = fp.get("shape") == "circle"
    args += ["-loop", "1", "-framerate", "30", "-t", f"{p.dur + 0.5:.2f}", "-i", window_mask((bw, bh), f"facepip{j}", circle)]
    # cuts in and out with the full screen under it; "motion": "ease" fades it
    eased = fp.get("motion") == "ease"
    fades = (f",fade=t=in:st={ps}:d={FS_IN}:alpha=1" if eased and ps >= 0.05 else "") + (f",fade=t=out:st={pe - FS_OUT:.2f}:d={FS_OUT}:alpha=1" if eased and pe < p.dur - 0.1 else "")
    f.append(f"[srcp{j}]crop={cw}:{ch}:{cx}:{cy},scale={bw}:{bh},format=rgba[fp0_{j}]")
    f.append(f"[{n}:v]format=gray[fpm{j}]")
    f.append(f"[fp0_{j}][fpm{j}]alphamerge{fades}[fp{j}]")
    if circle and fp.get("ring"):   # optional white ring: "ring": True in the window
        ring = os.path.join(p.png, f"ring_{j}.png")
        im = Image.new("RGBA", (bw * 4, bh * 4), (0, 0, 0, 0))
        ImageDraw.Draw(im).ellipse([6, 6, bw * 4 - 7, bh * 4 - 7], outline=(255, 255, 255, 255), width=40)
        im.resize((bw, bh), Image.LANCZOS).save(ring)
        args += ["-loop", "1", "-framerate", "30", "-t", f"{p.dur + 0.5:.2f}", "-i", ring]
        f.append(f"[{n + 1}:v]format=rgba{fades}[rg{j}]")
        f.append(f"[fp{j}][rg{j}]overlay=0:0[fpr{j}]")
        f.append(f"[{last}][fpr{j}]overlay=x={bx}:y={by}:eof_action=pass:enable='between(t,{ps},{pe})'[o{n}]")
        last, n = f"o{n}", n + 2
    else:
        f.append(f"[{last}][fp{j}]overlay=x={bx}:y={by}:eof_action=pass:enable='between(t,{ps},{pe})'[o{n}]")
        last, n = f"o{n}", n + 1


# ---- the face square of light screens: the face shrinks from full screen into a rounded square under the
# graphic (GROW frames, drawn here frame by frame from the master), holds there, and grows back at the end.
def ease(u):
    return 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2


def frames_at(n0, count, out_dir, tag):
    """count frames of the master from frame n0, exactly as [src] has them (30 fps from 0)."""
    for old in glob.glob(os.path.join(out_dir, f"{tag}_src_*.png")):
        os.remove(old)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p.video, "-vf",
                    f"setpts=PTS-STARTPTS,fps=30:start_time=0,select='between(n,{n0},{n0 + count - 1})',"
                    f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1",
                    "-fps_mode", "passthrough", os.path.join(out_dir, f"{tag}_src_%03d.png")], check=True)
    return sorted(glob.glob(os.path.join(out_dir, f"{tag}_src_*.png")))


def grow_frame(img, u, crop, box):
    """The face at shrink progress u (0 = full screen, 1 = in the square), on a transparent canvas."""
    cx, cy, cw, ch = crop
    bx, by, bw, bh = box
    lerp = lambda a, b: a + (b - a) * u
    k = lerp(1, bw / cw)
    dx, dy, dw, dh = lerp(0, bx), lerp(0, by), lerp(W, bw), lerp(H, bh)
    sw, sh = min(dw / k, W), min(dh / k, H)
    mx, my = lerp(W / 2, cx + cw / 2), lerp(H / 2, cy + ch / 2)
    sx, sy = min(max(mx - sw / 2, 0), W - sw), min(max(my - sh / 2, 0), H - sh)
    size = (max(2, round(dw)), max(2, round(dh)))
    piece = img.crop((round(sx), round(sy), round(sx + sw), round(sy + sh))).resize(size, Image.LANCZOS).convert("RGBA")
    piece.putalpha(rounded(size, max(1, round(FACE_RADIUS * u))))
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if u > 0.02:
        shadow = shadow_img(size, 0.22 * u)
        canvas.alpha_composite(shadow, (round(dx) - SHADOW_PAD, round(dy) - SHADOW_PAD + SHADOW_Y))
    canvas.alpha_composite(piece, (round(dx), round(dy)))
    return canvas


face_grows = []   # (start of the shrink) for the auto whoosh
for j, fc in enumerate(p.face_card):
    srcp = f"srcp{len(p.face_pip) + j}"
    s, e = fc["window"]
    n0, m0 = round(s * 30), round(e * 30)
    (cx, cy, cw, ch), (bx, by, bw, bh) = fc["crop"], fc["box"]
    grow_in = fc.get("grow", True) and s >= 0.05 and m0 - n0 >= 2 * GROW + 6
    grow_out = fc.get("grow", True) and e < p.dur - 0.05 and m0 - n0 >= 2 * GROW + 6
    h0, h1 = (n0 + GROW if grow_in else n0) / 30, (m0 - GROW if grow_out else m0) / 30
    # held: a static shadow, then the face cropped and scaled into the rounded square
    sh = os.path.join(p.png, f"faceshadow_{j}.png")
    shadow_img((bw, bh), 0.22).save(sh)
    args += ["-loop", "1", "-framerate", "30", "-t", f"{p.dur + 0.5:.2f}", "-i", sh,
             "-loop", "1", "-framerate", "30", "-t", f"{p.dur + 0.5:.2f}", "-i", window_mask((bw, bh), f"facecard{j}", radius=FACE_RADIUS)]
    f.append(f"[{srcp}]crop={cw}:{ch}:{cx}:{cy},scale={bw}:{bh},format=rgba[fc0_{j}]")
    f.append(f"[{n + 1}:v]format=gray[fcm{j}]")
    f.append(f"[fc0_{j}][fcm{j}]alphamerge[fc{j}]")
    hold = f"gte(t,{h0:.4f})*lt(t,{h1:.4f})"
    f.append(f"[{last}][{n}:v]overlay=x={bx - SHADOW_PAD}:y={by - SHADOW_PAD + SHADOW_Y}:eof_action=pass:enable='{hold}'[fs{j}]")
    f.append(f"[fs{j}][fc{j}]overlay=x={bx}:y={by}:eof_action=pass:enable='{hold}'[o{n}]")
    last, n = f"o{n}", n + 2
    # the shrink and the grow back, frame by frame
    for side, on in (("in", grow_in), ("out", grow_out)):
        if not on:
            continue
        start = n0 if side == "in" else m0 - GROW
        tag = f"grow{j}{side}"
        srcs = frames_at(start, GROW, p.png, tag)
        if len(srcs) < GROW:
            raise SystemExit(f"face square {j}: only {len(srcs)} frames at {start / 30:.2f}s for the {side} move")
        for i, path in enumerate(srcs):
            u = i / GROW if side == "in" else 1 - (i + 1) / GROW
            grow_frame(Image.open(path).convert("RGB"), ease(u), fc["crop"], fc["box"]).save(os.path.join(p.png, f"{tag}_{i:03d}.png"))
            os.remove(path)
        args += ["-framerate", "30", "-itsoffset", f"{start / 30:.4f}", "-i", os.path.join(p.png, f"{tag}_%03d.png")]
        f.append(f"[{n}:v]format=rgba[g{n}]")
        f.append(f"[{last}][g{n}]overlay=0:0:eof_action=pass:enable='gte(t,{start / 30:.4f})*lt(t,{(start + GROW) / 30:.4f})'[o{n}]")
        last, n = f"o{n}", n + 1
        if side == "in":
            face_grows.append(start / 30)


def in_face_card(t):
    return any(fc["window"][0] - 0.05 <= t < fc["window"][1] for fc in p.face_card)


def caption_y(t):
    """Normal height, inside the panel in split mode, across the bottom edge of a bottom b-roll window,
    inside the bottom of the face square on a light screen."""
    if in_face_card(t):
        return FACE_CAP_Y
    for v, s, e, k in vis:
        if s <= t < e and k in SPLITS:
            return CAP_Y_SPLIT
        if s <= t < e and k == "broll_bottom":
            return BOTTOM_CAP_Y
    return CAP_Y


# ---- captions on top of everything
for i, (_, s, e) in enumerate(p.captions):
    if e - s < 0.05:
        continue
    path = os.path.join(p.png, f"c_{i:03d}.png")
    w, h = Image.open(path).size
    st = p.caption_style.get(i, {})
    cy = st.get("y") or caption_y(s if in_face_card(s) else (s + e) / 2)
    cx = st.get("x", SAFE_L + SAFE_W // 2)
    x0 = min(max(cx - w // 2, SAFE_L - 50), SAFE_R + 50 - w)   # the PNG carries 50px of transparent side padding
    args += ["-loop", "1", "-framerate", "30", "-t", f"{e - s + 0.05:.2f}", "-itsoffset", f"{s}", "-i", path]
    f.append(f"[{n}:v]format=rgba[c{n}]")  # a caption at 0 is on frame one
    f.append(f"[{last}][c{n}]overlay=x={x0}:y={cy - h // 2}:eof_action=pass:enable='gte(t,{s})*lt(t,{e})'[o{n}]")
    last, n = f"o{n}", n + 1

# ---- export: Instagram-native 1080x1920, one encode from the full-res composite
f.append(f"[{last}]fps=30,scale=1080:1920:flags=lanczos,format=yuv420p[out]")   # fps: frame sequences can repeat a timestamp at the end
script = os.path.join(p.workdir, "filter.txt")
open(script, "w").write(";\n".join(f))
acodec = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=codec_name", "-of", "csv=p=0", p.video],
                        capture_output=True, text=True).stdout.strip()
audio = ["-c:a", "copy"] if acodec == "aac" else ["-c:a", "aac", "-b:a", "192k"]
amap = "0:a?"
VOICE_LUFS = -14.0   # the voice is set to this in assemble.py (VOICE); clips are matched to it


def lufs_of(path, start, length):
    """Integrated loudness of the stretch of a clip that plays."""
    err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-ss", f"{start}", "-t", f"{max(length, 0.5):.3f}", "-i", path,
                          "-vn", "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    v = float(err.rsplit("I:", 1)[1].split("LUFS")[0])
    return v if v > -70 else VOICE_LUFS   # a silent clip: leave it alone


# ---- sound effects: soft and sparse, well under the voice. Files are peak-normalized to -1 dBFS.
SFX_GAIN = {"pop": -15, "click": -13, "whoosh": -17, "ding": -15}


def sfx_file(name):
    if os.path.isfile(name):
        return name
    for d in (os.path.join(SKILL, "local", "sfx"), os.path.join(SKILL, "assets", "sfx")):
        for ext in (".wav", ".mp3", ".m4a"):
            if os.path.exists(os.path.join(d, name + ext)):
                return os.path.join(d, name + ext)
    return None


hits = [(float(x[0]), x[1], x[2] if len(x) > 2 else None) for x in p.sfx]
if p.auto_sfx:
    for v, s, e, k in vis:   # a pill or card arriving at the top (not frame one, not a quick state change)
        val = p.visuals[v]
        if k == "overlay" and s >= 0.05 and val[2].get("top") == PILL_TOP and val[2].get("motion") not in ("quick", "quick-out", "out"):
            hits.append((s, "pop", None))
    hits += [(max(0.0, t - 0.08), "whoosh", None) for t in face_grows]   # the face shrinking into a light screen
hits.sort()
kept_hits = []
for t, name, g in hits:   # never two effects on top of each other
    if t < p.dur - 0.1 and not any(abs(t - t2) < 0.25 for t2, _, _ in kept_hits):
        kept_hits.append((t, name, g))
sfx_inputs, missing_sfx = [], set()
for t, name, g in kept_hits:
    path = sfx_file(name)
    if not path:
        missing_sfx.add(name)
        continue
    args += ["-i", path]
    sfx_inputs.append((n, t, SFX_GAIN.get(name, -15) if g is None else g, name))
    n += 1
if missing_sfx:
    print(f"no sound file for {sorted(missing_sfx)} in local/sfx or assets/sfx, those effects are skipped")
if sounds or sfx_inputs:
    chain, mix = [], ["a0"]
    if sounds:
        # the voice off while a clip he reacts to plays its own sound, then back in over XA at the clip's end
        mute = "+".join(f"clip((t-{s})/0.08,0,1)*clip(({e}-t)/{XA},0,1)" for _, s, e, _, _ in sounds)  # commas are safe inside the quotes
        chain.append(f"[0:a]asetpts=PTS-STARTPTS,volume='max(0,1-({mute}))':eval=frame[a0]")
    else:
        chain.append("[0:a]asetpts=PTS-STARTPTS[a0]")
    for i, (k, s, e, clip_file, clip_start) in enumerate(sounds):
        # an outside clip plays at the voice's level, so the reel sounds like one piece
        gain = VOICE_LUFS - lufs_of(clip_file, clip_start, e - s)
        chain.append(f"[{k}:a]asetpts=PTS-STARTPTS,atrim=0:{e - s:.3f},volume={gain:.2f}dB,afade=t=out:st={max(0, e - s - XA):.3f}:d={XA},"
                     f"adelay={int(s * 1000)}:all=1[ca{i}]")
        mix.append(f"ca{i}")
    for i, (k, at, gain, name) in enumerate(sfx_inputs):
        chain.append(f"[{k}:a]asetpts=PTS-STARTPTS,aresample=48000,aformat=channel_layouts=stereo,volume={gain}dB,"
                     f"adelay={int(at * 1000)}:all=1[fx{i}]")
        mix.append(f"fx{i}")
    chain.append("".join(f"[{x}]" for x in mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first,alimiter=limit=0.84:level=false"
                 + (f",afade=t=out:st={p.dur - END_FADE:.3f}:d={END_FADE}" if a.youtube else "") + "[aout]")
    open(script, "a").write(";\n" + ";\n".join(chain))
    amap, audio = "[aout]", ["-c:a", "aac", "-b:a", "192k"]
elif a.youtube:
    open(script, "a").write(f";\n[0:a]asetpts=PTS-STARTPTS,afade=t=out:st={p.dur - END_FADE:.3f}:d={END_FADE}[aout]")
    amap, audio = "[aout]", ["-c:a", "aac", "-b:a", "192k"]
args += ["-filter_complex_script", script, "-map", "[out]", "-map", amap,
         "-c:v", "libx264", "-preset", "slow", "-crf", str(CRF), "-maxrate", "8M", "-bufsize", "16M",
         "-profile:v", "high", "-x264-params", "aq-mode=3", "-r", "30", *audio, "-movflags", "+faststart", "-t", f"{p.dur}", OUT]
subprocess.run(args, check=True)
print(f"wrote {OUT} ({os.path.getsize(OUT) / 1e6:.1f} MB)")
# the loudness check for the report: -14 LUFS (+-1) and true peak at or under -1 dBTP
err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", OUT, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                     capture_output=True, text=True).stderr.rsplit("Summary:", 1)[-1]
I, TP = float(err.split("I:")[1].split()[0]), float(err.split("Peak:")[1].split()[0])
flag = "" if -15 <= I <= -13 and TP <= -1.0 else "   << OUTSIDE -14 LUFS +-1 / -1 dBTP, say so in the report"
print(f"loudness {I:.1f} LUFS, true peak {TP:.1f} dBTP{flag}")
if sfx_inputs:
    print("sound effects: " + ", ".join(f"{name} {at:.2f}s" for _, at, _, name in sfx_inputs))
