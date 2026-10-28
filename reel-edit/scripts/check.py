"""Pull frames from the exported reel and lay them out with the Instagram safe box drawn on.

    python check.py <workdir> [--times 1.0,3.5,...] [--video path]

Default times: every visual at 0.15s after it starts (catches mid-transition problems) and at
its midpoint. Writes check_*.jpg contact sheets into the work dir and prints their paths.
"""
import argparse, os, subprocess
from PIL import Image, ImageDraw
from reel_edit.project import load

ap = argparse.ArgumentParser()
ap.add_argument("workdir")
ap.add_argument("--times")
ap.add_argument("--video")
a = ap.parse_args()
p = load(a.workdir)
video = a.video or p.output
if a.times:
    ts = [float(t) for t in a.times.split(",")]
else:
    ts = sorted({round(s + 0.15, 2) for _, s, _ in p.timeline} | {round((s + e) / 2, 2) for _, s, e in p.timeline})

d = os.path.join(p.workdir, "check")
os.makedirs(d, exist_ok=True)
frames = []
for i, t in enumerate(ts):
    out = os.path.join(d, f"{i:03d}.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t}", "-i", video, "-frames:v", "1", out], check=True)
    im = Image.open(out).convert("RGB")
    k = im.width / 1440  # safe box is defined on the 1440 master
    dr = ImageDraw.Draw(im)
    dr.rectangle([90 * k, 360 * k, 1350 * k, 1920 * k], outline=(255, 0, 255), width=max(2, int(5 * k)))
    dr.rectangle([0, 0, 150 * k, 50 * k], fill=(0, 0, 0))
    dr.text((8 * k, 8 * k), f"{t:.2f}s", fill=(255, 0, 255))
    frames.append(im)

cell_w, cols, per = 300, 5, 20
cell_h = int(cell_w * 16 / 9)
for sheet_i in range(0, len(frames), per):
    chunk = frames[sheet_i:sheet_i + per]
    rows = (len(chunk) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w, rows * cell_h), (110, 110, 110))
    for j, im in enumerate(chunk):
        sheet.paste(im.resize((cell_w - 6, cell_h - 6)), ((j % cols) * cell_w + 3, (j // cols) * cell_h + 3))
    path = os.path.join(p.workdir, f"check_{sheet_i // per + 1}.jpg")
    sheet.save(path, quality=85)
    print(path)
# the very first frame: Instagram shows it before the reel plays, so it must be the real picture,
# not a dark or empty frame
first = os.path.join(d, "first.png")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", "select='eq(n,0)+eq(n,8)',tile=2x1", "-frames:v", "1", first], check=True)
pair = Image.open(first).convert("L")
half = pair.width // 2
mean = lambda im: sum(im.resize((64, 64)).getdata()) / 4096
m0, m8 = mean(pair.crop((0, 0, half, pair.height))), mean(pair.crop((half, 0, pair.width, pair.height)))
print(f"first frame: brightness {m0:.0f} against {m8:.0f} eight frames later  ({first})")
if abs(m0 - m8) > 8:
    print("WARNING: THE FIRST FRAME IS NOT THE SAME PICTURE AS THE REST. Open it, fix it, rebuild. Never deliver this.")
print(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration,size:stream=codec_name,width,height",
                      "-of", "compact", video], capture_output=True, text=True).stdout.strip())
