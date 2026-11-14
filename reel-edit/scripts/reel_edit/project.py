"""Loads a reel's edit.py (the per-video edit decision list) and fills in defaults.

edit.py contract (Claude writes one per video, in the video's work dir):
    VIDEO        absolute path to the raw vertical video
    CAPTIONS     [(start_seconds, "caption text"), ...]  each holds until the next starts
                 Plain 3-4 word phrases by default. Explicit legacy *word* highlighting remains supported. Optional third item, a style dict (the moving-caption style, 27 Oct 2026):
                 {"y": centre y, "x": centre x, "scale": size multiplier}; {word} inside the text = a big word
    VISUALS      {"id": overlay(...) | split(...) | full(...) | broll(...)}
                 A broll window dict may set "x" (left edge on the master canvas) for side-by-side recordings.
    TIMELINE     [("id", start, end), ...]  later entries draw on top of earlier ones
  optional:
    CAPTION_LANG "ar" (Arabic letters, English terms kept Latin) or "en"
    FACE         (x, y) face centre on the 1440x2560 canvas, default (720, 900)
    PUNCH        [(start, end), ...] punch-in zoom windows
    PUNCH_ZOOM   default 1.12
    ZOOM         [(start, end, kind), ...] eased zooms, anchored on FACE:
                   "hook" eases in over the spoken hook, then a hard cut back to normal at end
                   "in"   eases in over the window and holds (a reflective moment)
                   "out"  eases back to normal over the window (the realization after it)
                 PUNCH stays the hard zoom on an emphasis line, and works on top of these
    ZOOM_LEVEL   how far an eased zoom goes, default 1.15
    SFX          [(time, "pop" | "click" | "whoosh" | "ding" | path, gain_db=None), ...] extra sound effects.
                 Sounds are local/sfx/<name>.wav, else assets/sfx/<name>.wav, peak-normalized to -1 dBFS
    AUTO_SFX     default True: a soft pop when a top pill or card first appears (not at 0, not on its
                 quick states) and a soft whoosh as the face shrinks into a light screen. False: only SFX
    FACE_CARD    the face in a box: the rounded rectangle of a light screen, the bottom part of a hard split, the
                 top-left box of a corner screen. Worked out from the light() / hard() / corner() visuals in the
                 TIMELINE (adjacent ones with the same box merge; different boxes link and the face moves
                 between them). Set it only to override: [(start, end), ...] or dicts
                 {"window": (s, e), "box": .., "crop": .., "grow": True, "radius": 44, "shadow": True, "cap": "in"}
    OUTPUT       default "<video stem> - edited.mp4" next to the video
    YOUTUBE_END  seconds: where the YouTube copy ends, 0.3s after the last word before a DM keyword ask
                 (his automation only answers comments on Instagram). None when there is no keyword ask
    QUALITY      "default" (CRF 22, ~27 MB/min) | "small" (CRF 24, ~21) | "max" (CRF 18, ~40)
    FACE_PIP     {"crop": (x, y, w, h), "box": (x, y, w, h), "window": (start, end)}  the face, cropped from the
                 master and shown in a rounded window on top of full-screen graphics (list reels).
                 A list of these gives several windows; "shape": "circle" makes one round (use a square box
                 and crop), for the face in a small circle over a full screen
    BLUR         [(start, end, (x, y, w, h)), ...] blur a box of his footage (user emails, keys on a screen)
"""
import importlib.util, json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def probe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def load(workdir):
    workdir = os.path.abspath(workdir)
    sys.path.insert(0, os.path.dirname(HERE))  # so edit.py can `from reel_edit.components import *`
    spec = importlib.util.spec_from_file_location("edit", os.path.join(workdir, "edit.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)

    p = type("Project", (), {})()
    p.workdir = workdir
    p.png = os.path.join(workdir, "png")
    p.video = m.VIDEO
    p.dur = probe_duration(m.VIDEO)
    from .brand import CAPTION_LANG
    p.lang = getattr(m, "CAPTION_LANG", CAPTION_LANG)
    p.face = getattr(m, "FACE", (720, 900))
    p.punch = getattr(m, "PUNCH", [])
    p.punch_zoom = getattr(m, "PUNCH_ZOOM", 1.12)
    p.zoom = sorted(getattr(m, "ZOOM", []))
    bad = [z for z in p.zoom if len(z) != 3 or z[2] not in ("hook", "in", "out") or z[1] <= z[0]]
    if bad:
        raise SystemExit(f'ZOOM entries must be (start, end, "hook" | "in" | "out") with end > start: {bad}')
    p.zoom_level = getattr(m, "ZOOM_LEVEL", 1.15)
    p.sfx = [tuple(x) for x in getattr(m, "SFX", [])]
    p.auto_sfx = getattr(m, "AUTO_SFX", True)
    p.quality = getattr(m, "QUALITY", "default")
    fp = getattr(m, "FACE_PIP", None)
    p.face_pip = [fp] if isinstance(fp, dict) else list(fp or [])
    p.blur = getattr(m, "BLUR", [])
    p.youtube_end = getattr(m, "YOUTUBE_END", None)
    stem = os.path.splitext(os.path.basename(m.VIDEO))[0]
    p.output = getattr(m, "OUTPUT", None) or os.path.join(os.path.dirname(m.VIDEO), f"{stem} - edited.mp4")
    ch = m.CAPTIONS
    p.captions = [(c[1], c[0], ch[i + 1][0] if i + 1 < len(ch) else p.dur) for i, c in enumerate(ch)]
    p.caption_style = {i: c[2] for i, c in enumerate(ch) if len(c) > 2 and c[2]}
    p.visuals = m.VISUALS
    p.timeline = [(v, s, min(e, p.dur)) for v, s, e in m.TIMELINE]
    missing = [v for v, _, _ in p.timeline if v not in p.visuals]
    if missing:
        raise SystemExit(f"TIMELINE uses visuals not defined in VISUALS: {missing}")
    p.face_card = face_cards(p, getattr(m, "FACE_CARD", None))
    return p


def face_crop(face, box, head=.48):
    """A crop of the full frame around the head with the face square's shape: head and shoulders, the
    head in the upper half so the captions inside the square sit on the chest."""
    from .components import W, H
    fx, fy = face
    bw, bh = box[2], box[3]
    cw = 1300
    ch = round(cw * bh / bw)
    x = min(max(fx - cw // 2, 0), W - cw)
    y = min(max(round(fy - head * ch), 0), H - ch)   # air above the hair
    return (x, y, cw, ch)


def options_of(value):
    """The options dict of a visual: the third item of a tuple, or the broll dict itself."""
    if isinstance(value, dict):
        return value
    return value[2] if isinstance(value, tuple) and len(value) > 2 else {}


def face_layout(value):
    """light | blur | hard | corner for a visual that puts the face in a box, else None."""
    o = options_of(value)
    return o.get("layout", "light") if o.get("face") else None


def card_style(layout):
    """Where the face goes for each layout: box, corner radius, shadow, and whether captions sit inside the box
    ("in"), at the normal height ("normal") or low, under a recording ("low")."""
    from . import components as K
    if layout == "hard":
        # the head high in the bottom part, so the face sits clear of the platform's bottom bar and captions go under it
        return {"box": (0, K.HARD_Y, K.W, K.H - K.HARD_Y), "radius": 0, "shadow": False, "cap": "low", "head": .28}
    if layout == "corner":
        return {"box": K.CORNER_BOX, "radius": 36, "shadow": True, "cap": "low"}
    return {"box": K.FACE_BOX, "radius": K.FACE_RADIUS, "shadow": True, "cap": "in"}   # light, blur


def face_cards(p, explicit):
    """Windows where the face sits in a box (a light screen and the other layouts). Back-to-back spans with the same
    box merge into one window. Back-to-back spans with different boxes stay two windows, linked: the face moves
    from one box to the other instead of growing back to full screen in between."""
    wins = []
    if explicit is not None:
        for w in explicit:
            w = {"window": tuple(w)} if not isinstance(w, dict) else dict(w)
            wins.append(w)
    else:
        spans = sorted((s, e, face_layout(p.visuals[v])) for v, s, e in p.timeline if face_layout(p.visuals[v]))
        for s, e, layout in spans:
            st = card_style(layout)
            if wins and s - wins[-1]["window"][1] < 0.05 and wins[-1]["style"] == st:
                wins[-1]["window"] = (wins[-1]["window"][0], max(e, wins[-1]["window"][1]))
            elif wins and wins[-1]["window"][0] <= s < wins[-1]["window"][1] - 0.05:
                continue   # a second visual inside an open window (a recording over its panel)
            else:
                wins.append({"window": (s, e), "style": st, **st})
    for w in wins:
        w.setdefault("box", card_style("light")["box"])
        for k, v in card_style("light").items():
            w.setdefault(k, v)
        w.setdefault("crop", face_crop(p.face, w["box"], w.pop("head", .48)))
        w.setdefault("grow", True)
        w.pop("style", None)
    for a, b in zip(wins, wins[1:]):   # linked windows: the face moves from a's box into b's
        if abs(b["window"][0] - a["window"][1]) < 0.05:
            a["to_next"] = True
            b["from_prev"] = {k: a[k] for k in ("box", "crop", "radius", "shadow")}
    return wins


def kind_of(value):
    """overlay | split | full | broll_full | broll_split | broll_pip | broll_bottom"""
    if isinstance(value, dict):
        return "broll_" + value["mode"]
    return value[1]


def read_meta(p):
    path = os.path.join(p.png, "meta.json")
    return json.load(open(path)) if os.path.exists(path) else {}
