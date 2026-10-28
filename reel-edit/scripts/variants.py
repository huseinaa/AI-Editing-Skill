"""Make version B or C of a reel from finished version A: same body, a different opening.

    python variants.py <A workdir> <B|C> <opening take> [--from 0.30] [--to 3.80]

Every reel is tested as three trial reels that differ only in the opening.
Version A is edited in full first. This then:
  1. copies A's work dir to <A workdir without -A>-<version>
  2. writes cuts.txt: A's cuts with A's opening dropped and this opening put first (trimmed
     with --from/--to, the same 0.04s-before / 0.06s-after rule as every cut)
  3. runs assemble.py, so the body takes come out exactly as in A
  4. moves every body time in edit.py (captions, cards, zooms, punches, blur, YOUTUBE_END) by the
     difference in opening length. Times inside A's opening are left as they are and listed: that
     is the part to rewrite (the opening's captions and hook card). The hook zoom's end lands on the
     new opening's end by itself.
  5. names the export "<title> - Trial <version>.mp4" and transcribes the new master.
A's opening is the first take in A's takes.json and must be one stretch of one take.
"""
import argparse, io, json, os, re, shutil, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.stdout.reconfigure(encoding="utf-8")   # Arabic words on a Windows console
ap = argparse.ArgumentParser()
ap.add_argument("a_workdir")
ap.add_argument("version", choices=["B", "C"])
ap.add_argument("opening")
ap.add_argument("--from", dest="t_from", type=float)
ap.add_argument("--to", dest="t_to", type=float)
a = ap.parse_args()

src = os.path.abspath(a.a_workdir)
base = src[:-2] if src.endswith("-A") else src
dst = f"{base}-{a.version}"
A = json.load(open(os.path.join(src, "takes.json"), encoding="utf-8"))
a_takes = [t for t in A["takes"] if not t.get("dropped")]
a_open = a_takes[0]
stem = lambda name: name.split(" #")[0]
a_open_stem = stem(a_open["take"])
if a_open["take"] != a_open_stem:
    raise SystemExit(f"A's opening ({a_open['take']}) is one stretch of a longer take. Film each opening as its own take.")
if a.opening == a_open_stem:
    raise SystemExit("that is A's opening")

# ---- 1. copy the work dir, without A's video, transcript and checks
if os.path.exists(dst):
    raise SystemExit(f"{dst} already exists. Delete it to make version {a.version} again.")
skip = shutil.ignore_patterns("takes", "master.mp4", "audio.wav", "words.*", "frames", "check*", "filter.txt",
                              "build.log", "*.mp4", "cover*", "__pycache__")
shutil.copytree(src, dst, ignore=skip)

# ---- 2. cuts.txt: A's, minus every line about either opening, plus this opening first
lines = []
if os.path.exists(os.path.join(src, "cuts.txt")):
    for raw in io.open(os.path.join(src, "cuts.txt"), encoding="utf-8"):
        words = raw.split("#")[0].split()
        if words and (words[0] == "order" or a_open_stem in words[1:] or a.opening in words[1:]):
            continue
        lines.append(raw.rstrip("\n"))
trim = " ".join(x for x in [f"from={a.t_from:.2f}" if a.t_from is not None else "",
                            f"to={a.t_to:.2f}" if a.t_to is not None else ""] if x)
body_order = []
for t in a_takes[1:]:
    if stem(t["take"]) not in body_order:
        body_order.append(stem(t["take"]))
lines += [f"# version {a.version}: opening {a.opening} in place of A's {a_open_stem}",
          f"drop {a_open_stem}"] + ([f"trim {a.opening} {trim}"] if trim else []) + [f"order {a.opening} {' '.join(body_order)}"]
io.open(os.path.join(dst, "cuts.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

# ---- 3. assemble
subprocess.run([sys.executable, os.path.join(HERE, "assemble.py"), A["folder"], dst, "--cuts", os.path.join(dst, "cuts.txt")], check=True)
B = json.load(open(os.path.join(dst, "takes.json"), encoding="utf-8"))
b_takes = {t["take"]: t for t in B["takes"] if not t.get("dropped")}
b_open = b_takes[a.opening]
body = [t for t in a_takes[1:]]
missing = [t["take"] for t in body if t["take"] not in b_takes]
if missing:
    raise SystemExit(f"these body takes did not come out of assemble.py: {missing}")
shift = b_open["end"] - a_open["end"]

# ---- 4. move the body times
LEVELS = re.compile(r"^\s*(PUNCH_ZOOM|ZOOM_LEVEL|RISER_GAIN_DB)\s*=")
TIME = re.compile(r"(?<!start=)(?<![\w.])(\d{1,2}\.\d{2})(?!\d)")
in_opening = []


JOIN = 0.035   # one frame: a time written a frame before a join belongs to the take after it


def move(t, line_no):
    if t < a_open["end"] - JOIN:
        in_opening.append(line_no)
        return t
    for r in body:  # half-open, so a time on a join belongs to the take that starts there
        if r["start"] - JOIN <= t < r["end"] - JOIN:
            n = b_takes[r["take"]]
            return n["start"] + (r["from"] + (t - r["start"]) - n["from"])
    last = body[-1]
    if abs(t - last["end"]) <= JOIN:
        return b_takes[last["take"]]["end"]
    return t  # past the end (99) and the like


p = os.path.join(dst, "edit.py")
# A's work dir as written in edit.py, whatever the drive letter's case or the slashes
SRC_PATH = re.compile(r"[\\/]".join(re.escape(part) for part in re.split(r"[\\/]", src)) + r"(?![\w-])", re.IGNORECASE)
out = []
for i, line in enumerate(io.open(p, encoding="utf-8").read().splitlines(keepends=True), 1):
    if not LEVELS.match(line):
        line = TIME.sub(lambda m: f"{move(float(m.group(1)), i):.2f}", line)
    if line.lstrip().startswith("OUTPUT"):
        line = (line.replace("- Trial A.mp4", f"- Trial {a.version}.mp4") if "- Trial A.mp4" in line
                else line.replace('.mp4"', f' - Trial {a.version}.mp4"'))
    out.append(SRC_PATH.sub(lambda m: dst, line))
in_opening = sorted({n + 2 for n in in_opening})   # the two header lines below push every line down by 2
head = (f"# VERSION {a.version}: opening {a.opening} (0.00 to {b_open['end']:.2f}) in place of A's {a_open_stem}. Body moved "
        f"{shift:+.2f}s by variants.py.\n# Rewrite the opening from words.txt: its captions, the hook card, the hook text. "
        f"Lines {in_opening} still carry A's opening times.\n")
io.open(p, "w", encoding="utf-8").write(head + "".join(out))

# ---- 5. transcript
subprocess.run([sys.executable, os.path.join(HERE, "transcribe.py"), os.path.join(dst, "master.mp4"), dst], check=True)
words = json.load(open(os.path.join(dst, "words.json"), encoding="utf-8"))
print(f"\nversion {a.version}: {dst}")
print(f"opening {a.opening}: 0.00 - {b_open['end']:.2f}s (A's was {a_open['end']:.2f}s), body moved {shift:+.2f}s")
print("opening words:", " ".join(f"{w['s']:.2f} {w['w']}" for w in words if w["s"] < b_open["end"]))
print(f"edit.py lines still on A's opening: {in_opening}")
