"""Composite the reel in one ffmpeg pass and export for Instagram.

    python build.py <workdir> [--out path] [--quality default|small|max] [--youtube]

Pipeline: normalize source to the 1440x2560 canvas -> punch-in zooms -> split-mode slide ->
visuals (graphics + b-roll) with eased motion -> captions -> 1080x1920 H.264 export.

--youtube builds the same edit ending at YOUTUBE_END (before the DM keyword ask, which only works on
Instagram), with a soft audio fade, to "<OUTPUT stem> - YouTube.mp4".
"""
import argparse, json, os, subprocess
from PIL import Image, ImageDraw
from reel_edit.project import load, kind_of
from reel_edit.components import W, H, SAFE_L, SAFE_R, SAFE_W, SAFE_T, SAFE_B, SPLIT_Y, SPLIT_H, PIP, BOTTOM_TOP, BOTTOM_CAP_Y

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

# ---- layout + motion (seconds). Nothing pops, everything eases.
# cards sit high, in the empty space above the head, so they never cover the eyes
OVERLAY_Y, CAP_Y, CAP_Y_SPLIT = 260, 1700, 1845
OV_IN, OV_OUT, OV_RISE = 0.45, 0.35, 50   # cards: fade + ease-out rise
FS_IN, FS_OUT = 0.35, 0.35                # full / split from and back to the face
XF = 0.3                                  # crossfade between back-to-back solid states
CAP_IN = 0.12                             # caption soft fade-in
SLIDE = 0.4                               # face slides up for split mode
FX, FY = p.face
SHIFT = max(0, FY - 575)                  # puts the face centre in the middle of the top area

vis = [[v, s, e, kind_of(p.visuals[v])] for v, s, e in p.timeline if e - s > 0.05]
STILL = (".png", ".jpg", ".jpeg", ".webp")
sounds = []                               # (input index, start, end, file, start in file) of b-roll clips whose sound plays
XA = 0.3                                  # the voice crossfades back in over this at a sound clip's end
SOLID = {"split", "full", "broll_full", "broll_split"}
CARD = {"overlay", "broll_pip", "broll_bottom"}
WINDOW = {"broll_pip", "broll_bottom"}   # rounded b-roll windows over the face video
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
f = [f"[0:v]setpts=PTS-STARTPTS,hqdn3d=1.5:1.5:6:6,scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30:start_time=0[src{0 if p.face_pip else str()}]"]
if p.face_pip:
    k = len(p.face_pip)
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

BORDER = 6  # white edge on the bottom window, so a dark clip does not melt into a dark shirt


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


def window_mask(size, name, circle=False):
    if circle:   # drawn 4x and scaled down, so the round edge is smooth
        big = Image.new("L", (size[0] * 4, size[1] * 4), 0)
        ImageDraw.Draw(big).ellipse([0, 0, size[0] * 4 - 1, size[1] * 4 - 1], fill=255)
        mask = big.resize(size, Image.LANCZOS)
    else:
        mask = Image.new("L", size, 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=36, fill=255)
    path = os.path.join(p.png, f"mask_{name}.png")
    mask.save(path)
    return path

# ---- visuals
for i, (v, s, e, k) in enumerate(vis):
    xf_in = adjacent(i, i - 1) and solid(i) and solid(i - 1)
    xf_out = adjacent(i, i + 1) and solid(i) and solid(i + 1)
    end = e + XF if xf_out else e  # hold under the next state while it crossfades in
    if k.startswith("broll"):
        b = p.visuals[v]
        win_top = OVERLAY_Y
        if k == "broll_bottom":
            win_top, (bw, bh) = bottom_box(b)
        else:
            bw, bh = {"broll_full": (W, H), "broll_split": (W, SPLIT_H), "broll_pip": PIP}[k]
        if b["broll"].lower().endswith(STILL):
            args += ["-loop", "1", "-framerate", "30", "-t", f"{end - s + 0.3:.2f}", "-itsoffset", f"{s}", "-i", b["broll"]]
        else:
            args += ["-ss", str(b["start"]), "-t", f"{end - s + 0.3:.2f}", "-itsoffset", f"{s}", "-i", b["broll"]]
            if b.get("audio"):
                sounds.append((n, s, e, b["broll"], b["start"]))
        fit = (f"scale={bw - 2 * BORDER}:{bh - 2 * BORDER},pad={bw}:{bh}:{BORDER}:{BORDER}:white" if k == "broll_bottom"
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
        if s >= 0.05:  # a visual that starts the reel is there on frame one, it does not fade in
            chain += f",fade=t=in:st={s}:d={OV_IN}:alpha=1"
        if e < p.dur - 0.1:
            chain += f",fade=t=out:st={e - OV_OUT:.2f}:d={OV_OUT}:alpha=1"
        w = bw if k in WINDOW else meta[v]["w"]
        card_top = (p.visuals[v][2].get("top") if k == "overlay" and len(p.visuals[v]) > 2 else None) or OVERLAY_Y
        top = win_top if k in WINDOW else card_top - meta[v]["pad"]
        x = f"{SAFE_L + (SAFE_W - w) // 2}"
        y = f"'{top}+{OV_RISE}*pow(max(0\\,1-(t-{s})/{OV_IN})\\,3)'"
    else:
        if s >= 0.05:
            chain += f",fade=t=in:st={s}:d={XF if xf_in else FS_IN}:alpha=1"
        if not xf_out and e < p.dur - 0.1:
            chain += f",fade=t=out:st={e - FS_OUT:.2f}:d={FS_OUT}:alpha=1"
        x, y = "0", "0"
        if k in SPLITS:
            y = str(SPLIT_Y) if xf_in else f"'{SPLIT_Y}+{OV_RISE * 2}*pow(max(0\\,1-(t-{s})/{SLIDE})\\,3)'"
    f.append(f"[{src_label}]{chain}[v{n}]")
    f.append(f"[{last}][v{n}]overlay=x={x}:y={y}:eof_action=pass:enable='between(t,{s},{end:.2f})'[o{n}]")
    last, n = f"o{n}", n + n_used


# ---- the face in a rounded window over full-screen graphics (a list reel: the list, the face, the illustration)
for j, fp in enumerate(p.face_pip):
    (cx, cy, cw, ch), (bx, by, bw, bh) = fp["crop"], fp["box"]
    ps, pe = fp["window"]
    circle = fp.get("shape") == "circle"
    args += ["-loop", "1", "-framerate", "30", "-t", f"{p.dur + 0.5:.2f}", "-i", window_mask((bw, bh), f"facepip{j}", circle)]
    fades = (f",fade=t=in:st={ps}:d={FS_IN}:alpha=1" if ps >= 0.05 else "") + (f",fade=t=out:st={pe - FS_OUT:.2f}:d={FS_OUT}:alpha=1" if pe < p.dur - 0.1 else "")
    f.append(f"[srcp{j}]crop={cw}:{ch}:{cx}:{cy},scale={bw}:{bh},format=rgba[fp0_{j}]")
    f.append(f"[{n}:v]format=gray[fpm{j}]")
    f.append(f"[fp0_{j}][fpm{j}]alphamerge{fades}[fp{j}]")
    if circle:   # a thin white ring so the circle reads on any background
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


def caption_y(t):
    """Normal height, inside the panel in split mode, across the bottom edge of a bottom b-roll window."""
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
    cy = st.get("y") or caption_y((s + e) / 2)
    cx = st.get("x", SAFE_L + SAFE_W // 2)
    x0 = min(max(cx - w // 2, SAFE_L - 50), SAFE_R + 50 - w)   # the PNG carries 50px of transparent side padding
    args += ["-loop", "1", "-framerate", "30", "-t", f"{e - s + 0.05:.2f}", "-itsoffset", f"{s}", "-i", path]
    f.append(f"[{n}:v]format=rgba" + (f",fade=t=in:st={s}:d={CAP_IN}:alpha=1" if s >= 0.05 else "") + f"[c{n}]")  # a caption at 0 is on frame one
    f.append(f"[{last}][c{n}]overlay=x={x0}:y={cy - h // 2}:eof_action=pass:enable='gte(t,{s})*lt(t,{e})'[o{n}]")
    last, n = f"o{n}", n + 1

# ---- export: Instagram-native 1080x1920, one encode from the full-res composite
f.append(f"[{last}]scale=1080:1920:flags=lanczos,format=yuv420p[out]")
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


# the rising sound under the spoken-hook zoom: it ends, at its peak, as the hook zoom ends
RISER_WAV = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "sfx", "riser-hook.wav")
riser = None
hooks = [(s, e) for s, e, k in p.zoom if k == "hook"]
if p.riser and hooks and not os.path.exists(RISER_WAV):
    print(f"no riser sound at {RISER_WAV} (see assets/sfx/SOURCE.md), the hook zoom plays without it")
elif p.riser and hooks:
    rlen = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", RISER_WAV],
                                capture_output=True, text=True, check=True).stdout.strip())
    he = hooks[0][1]
    skip = max(0.0, rlen - he)            # a hook shorter than the riser plays only its last part
    args += ["-i", RISER_WAV]
    riser = (n, he - (rlen - skip), skip, rlen - skip)   # input, start in the reel, start in the file, length
    n += 1
if sounds or riser:
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
    if riser:
        k, at, skip, length = riser
        chain.append(f"[{k}:a]atrim={skip:.3f}:{skip + length:.3f},asetpts=PTS-STARTPTS,aresample=48000,"
                     f"volume={p.riser_gain_db}dB,afade=t=out:st={max(0, length - 0.08):.3f}:d=0.08,"
                     f"adelay={int(at * 1000)}:all=1[rz]")
        mix.append("rz")
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
