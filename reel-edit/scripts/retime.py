"""Move every master-time number in edit.py (captions, cards, punches, blur) to match a re-cut master.

    python retime.py <workdir> <old takes.json>

Each number is placed in the take it fell in, and keeps its distance from the take's source start.
start= values (a time inside a B-roll clip) are left alone, and so are lines that set a level, not a time
(PUNCH_ZOOM, ZOOM_LEVEL, RISER_GAIN_DB).
"""
import io, json, re, sys

wd, old_path = sys.argv[1], sys.argv[2]
old = [r for r in json.load(open(old_path, encoding="utf-8"))["takes"] if not r.get("dropped")]
new = [r for r in json.load(open(f"{wd}/takes.json", encoding="utf-8"))["takes"] if not r.get("dropped")]
base = lambda name: name.split(" #")[0]   # a take kept in pieces is "WVKU5828 #1", "#2"...


def move(t):
    for r in old:
        if r["start"] - 0.005 <= t <= r["end"] + 0.005:
            src = r["from"] + (t - r["start"])                 # the moment in the raw take
            pieces = [n for n in new if base(n["take"]) == base(r["take"])]
            # the piece of the new cut that holds that moment, else the nearest one
            n = min(pieces, key=lambda n: 0 if n["from"] - 0.005 <= src <= n["to"] + 0.005 else min(abs(src - n["from"]), abs(src - n["to"])))
            return min(max(n["start"] + (src - n["from"]), n["start"]), n["end"])
    return t                                                   # past the end (99) and the like


p = f"{wd}/edit.py"
s = io.open(p, encoding="utf-8").read()
LEVELS = re.compile(r"^\s*(PUNCH_ZOOM|ZOOM_LEVEL|RISER_GAIN_DB)\s*=")
TIME = re.compile(r"(?<!start=)(?<![\w.])(\d{1,2}\.\d{2})(?!\d)")
out = "".join(line if LEVELS.match(line) else TIME.sub(lambda m: f"{move(float(m.group(1))):.2f}", line)
              for line in s.splitlines(keepends=True))
io.open(p, "w", encoding="utf-8").write(out)
print("retimed", p)
