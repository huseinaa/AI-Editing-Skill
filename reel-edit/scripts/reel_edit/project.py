"""Loads a reel's edit.py (the per-video edit decision list) and fills in defaults.

edit.py contract (Claude writes one per video, in the video's work dir):
    VIDEO        absolute path to the raw vertical video
    CAPTIONS     [(start_seconds, "caption text"), ...]  each holds until the next starts
                 *word* = yellow. Optional third item, a style dict (the moving-caption style, 27 Oct 2026):
                 {"y": centre y, "x": centre x, "scale": size multiplier}; {word} inside the text = a big word
    VISUALS      {"id": overlay(...) | split(...) | full(...) | broll(...)}
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
    RISER        play assets/sfx/riser-hook.wav under the "hook" zoom, ending as it ends. Default True
                 when a "hook" zoom exists
    RISER_GAIN_DB riser level, default -6: its peak sits about 10 dB under the voice at -14 LUFS
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
    p.riser = getattr(m, "RISER", any(k == "hook" for _, _, k in p.zoom))
    p.riser_gain_db = getattr(m, "RISER_GAIN_DB", -6)
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
    return p


def kind_of(value):
    """overlay | split | full | broll_full | broll_split | broll_pip | broll_bottom"""
    if isinstance(value, dict):
        return "broll_" + value["mode"]
    return value[1]


def read_meta(p):
    path = os.path.join(p.png, "meta.json")
    return json.load(open(path)) if os.path.exists(path) else {}
