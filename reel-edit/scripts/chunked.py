"""Build a reel in time chunks and join them, for reels too long for one ffmpeg graph.

    python chunked.py <workdir> <cut1> [<cut2> ...] [--youtube]

Each cut must sit where the face is full screen (no light screen, card or pill spanning it); a take
join is best. For each chunk: a sub work dir <workdir>/_chunks/<i>/ with the master segment and an
edit.py that loads the reel's own edit.py and keeps only what falls in the chunk, shifted to 0. Then
render.py + build.py there, and an ffmpeg concat into the reel's OUTPUT (or its YouTube name).
"""
import importlib.util, json, os, subprocess, sys
from pathlib import Path

S = Path(__file__).resolve().parent
work = Path(sys.argv[1]).resolve()
youtube = "--youtube" in sys.argv
cuts = [float(x) for x in sys.argv[2:] if not x.startswith("--")]

sys.path.insert(0, str(S))
from reel_edit.project import options_of
spec = importlib.util.spec_from_file_location("reel_edit_src", work / "edit.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", m.VIDEO],
                           capture_output=True, text=True).stdout)
end = min(dur, m.YOUTUBE_END) if youtube and getattr(m, "YOUTUBE_END", None) else dur
bounds = [0.0] + [c for c in cuts if c < end] + [end]
for name, items in (("TIMELINE", m.TIMELINE),):
    for v, s, e in items:
        for c in cuts:
            if s < c - 0.01 and e > c + 0.01:
                sys.exit(f"{v} ({s}-{e}) spans the cut at {c}: move the cut")
            o = options_of(m.VISUALS[v])
            light = o.get("face") or o.get("cutout")   # every face-box layout, and a cut-out
            # a light screen ending at (or just before) a cut, or starting right on it, would lose the face's
            # grow back / shrink, so the face jumps between square and full screen at the join (14 Nov 2026)
            if light and (c - 0.1 < e <= c + 0.01 or c - 0.01 <= s < c + 0.1):
                sys.exit(f"{v} ({s}-{e}) is a light screen next to the cut at {c}: cut in the middle of a full-face stretch")
parts = []
env = dict(os.environ, REEL_EDIT_BROWSER_ARGS=os.environ.get("REEL_EDIT_BROWSER_ARGS", "--no-sandbox"))
for i, (a, b) in enumerate(zip(bounds, bounds[1:])):
    d = work / "_chunks" / str(i)
    d.mkdir(parents=True, exist_ok=True)
    seg = d / "master.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-i", m.VIDEO, "-t", f"{b - a:.3f}",
                    "-c:v", "libx264", "-crf", "12", "-preset", "fast", "-c:a", "aac", "-b:a", "320k", str(seg)], check=True)
    last = i == len(bounds) - 2
    out = d / "part.mp4"
    (d / "edit.py").write_text(f'''# chunk {i} of {work.name}: {a:.3f}s to {b:.3f}s, made by chunked.py
import importlib.util, sys
_spec = importlib.util.spec_from_file_location("_src", r"{work / 'edit.py'}")
_m = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_m)
globals().update({{k: v for k, v in vars(_m).items() if not k.startswith("__")}})
A, B = {a}, {b}
VIDEO = r"{seg}"
OUTPUT = r"{out}"
TIMELINE = [(v, s - A, min(e, B) - A) for v, s, e in _m.TIMELINE if s < B - 0.01 and e > A + 0.01]
CAPTIONS = [(c[0] - A,) + tuple(c[1:]) for c in _m.CAPTIONS if A - 0.01 <= c[0] < B - 0.01]
_before = [c for c in _m.CAPTIONS if c[0] < A - 0.01]          # the caption still on screen at the cut carries over
if _before and (not CAPTIONS or CAPTIONS[0][0] > 0.05):
    CAPTIONS.insert(0, (0.0,) + tuple(_before[-1][1:]))
ZOOM = [(max(s, A) - A, min(e, B) - A, k) for s, e, k in getattr(_m, "ZOOM", []) if s < B and e > A]
PUNCH = [(max(s, A) - A, min(e, B) - A) for s, e in getattr(_m, "PUNCH", []) if s < B and e > A]
SFX = [(t - A, n) for t, n in getattr(_m, "SFX", []) if A <= t < B]
YOUTUBE_END = None
''', encoding="utf-8")
    subprocess.run([sys.executable, str(S / "render.py"), str(d)], check=True, env=env)
    r = subprocess.run([sys.executable, str(S / "build.py"), str(d)], env=env, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"chunk {i} failed:\n" + r.stderr[-1500:])
    print(f"chunk {i}: {a:.2f}-{b:.2f} ok")
    parts.append(out)
final = Path(m.OUTPUT)
if youtube:
    final = final.with_name(final.stem + " - YouTube.mp4")
lst = work / "_chunks" / "list.txt"
lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in parts), encoding="utf-8")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(final)], check=True)
err = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(final), "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"],
                     capture_output=True, text=True).stderr.rsplit("Summary:", 1)[-1]
I, TP = float(err.split("I:")[1].split()[0]), float(err.split("Peak:")[1].split()[0])
print(f"wrote {final} ({os.path.getsize(final) / 1e6:.1f} MB)\nloudness {I} LUFS, true peak {TP} dBTP")
