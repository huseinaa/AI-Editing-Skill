"""Make a reel's cover image: a frame of you (smiling, chosen by eye), your logo, a blue fade from the bottom, the title.

    python cover.py <workdir | video> --title "What is *UI/UX*?" [--frame 3.2] [--style default|sales]
                                      [--title-y 1300] [--out path.jpg]

The title is English. Put | where the line breaks, and *stars* around the line (or words) that go
yellow. With no | a long title is split into two balanced lines.

Writes "<video> - cover.jpg" (1080x1920) next to the video. In <workdir>/cover/ it leaves
candidates.jpg (every frame it considered, with its time) and cover-check.jpg, which shows the cover
as the reels tab (9:16) and as the posts grid (the centre 4:5). Look at both before reporting.
"""
import argparse, base64, io, os, re, subprocess, sys
import cv2
from PIL import Image, ImageDraw, ImageFilter, ImageStat
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from reel_edit.components import FONTS

W, H = 1080, 1920
BAND = (285, 1635)          # the centre 4:5 the posts grid shows
from reel_edit.brand import BLUE, YELLOW, INK, LOGO, LATIN, FONTS_URL as FONTS, BROWSER

LOGO_W, LOGO_Y = 150, 110   # top centre, above the 4:5 band: the reels tab shows it, the posts grid does not
TITLE_Y = 1330              # centre of the title block when no face is found
TITLE_PX = 84
MAX_CHARS = 22
N_CANDIDATES = 24

ap = argparse.ArgumentParser()
ap.add_argument("src")
ap.add_argument("--title", required=True)
ap.add_argument("--frame", type=float)
ap.add_argument("--style", choices=["default", "sales"], default="default")
ap.add_argument("--title-y", type=int, help="centre of the title block; default sits it just under the chin")
ap.add_argument("--out")
a = ap.parse_args()

if os.path.isdir(a.src):
    from reel_edit.project import load
    video, workdir = load(a.src).video, os.path.abspath(a.src)
else:
    video = os.path.abspath(a.src)
    workdir = os.path.join(os.path.dirname(video), ".reel-edit", os.path.splitext(os.path.basename(video))[0])
cdir = os.path.join(workdir, "cover")
os.makedirs(cdir, exist_ok=True)
out = a.out or os.path.join(os.path.dirname(video), os.path.splitext(os.path.basename(video))[0] + " - cover.jpg")

cc = lambda name: cv2.CascadeClassifier(cv2.data.haarcascades + name)
FACE, EYES = cc("haarcascade_frontalface_default.xml"), cc("haarcascade_eye_tree_eyeglasses.xml")


def grab(t):
    path = os.path.join(cdir, f"cand_{t:06.2f}.jpg")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(t), "-i", video, "-frames:v", "1",
                    "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}", "-q:v", "2", path], check=True)
    return path


def face_of(path):
    """(x, y, w, h) of the biggest face, or None."""
    g = cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2GRAY)
    faces = FACE.detectMultiScale(g, 1.1, 6, minSize=(250, 250))
    return (max(faces, key=lambda f: f[2] * f[3]), g) if len(faces) else (None, g)


def score(path):
    """Eyes open, then sharpness. A smile cannot be detected reliably (a talking mouth reads as one),
    so the smiling frame is chosen by eye from candidates.jpg and passed with --frame."""
    f, g = face_of(path)
    sharp = ImageStat.Stat(Image.open(path).convert("L").resize((270, 480)).filter(ImageFilter.FIND_EDGES)).var[0]
    if f is None:
        return (0, sharp), "no face"
    x, y, w, h = f
    eyes = len(EYES.detectMultiScale(g[y:y + h * 6 // 10, x:x + w], 1.1, 4)) >= 2
    return (int(eyes), sharp), "eyes open" if eyes else "eyes?"


if a.frame is not None:
    frame = grab(a.frame)
else:
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                               capture_output=True, text=True, check=True).stdout.strip())
    times = [round(0.4 + i * (dur - 0.8) / (N_CANDIDATES - 1), 2) for i in range(N_CANDIDATES)]
    cands = [(t, grab(t)) for t in times]
    scored = [(score(p), t, p) for t, p in cands]
    (_, _), best_t, frame = max(scored, key=lambda s: s[0][0])
    # contact sheet of every candidate with its time, so a better one can be picked by eye
    tw, th = 270, 480
    sheet = Image.new("RGB", (tw * 8, (th + 34) * ((len(cands) + 7) // 8)), INK)
    d = ImageDraw.Draw(sheet)
    for i, ((_, note), t, p) in enumerate(scored):
        cx, cy = (i % 8) * tw, (i // 8) * (th + 34)
        sheet.paste(Image.open(p).resize((tw, th)), (cx, cy + 34))
        d.text((cx + 8, cy + 10), f"{t}s  {note}" + ("   <- used" if p == frame else ""), fill="#FAFF00" if p == frame else "#fff")
    sheet.save(os.path.join(cdir, "candidates.jpg"), quality=88)
    print(f"frame: {best_t}s, picked for open eyes and sharpness only. Open {os.path.join(cdir, 'candidates.jpg')} and pass the smiling one with --frame <seconds>.")


def lines_of(title):
    if "|" in title:
        return [s.strip() for s in title.split("|")]
    if len(title.replace("*", "")) <= MAX_CHARS:
        return [title.strip()]
    words = title.split()
    best = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i]).replace("*", "")) - len(" ".join(words[i:]).replace("*", ""))))
    one, two = " ".join(words[:best]), " ".join(words[best:])
    if one.count("*") % 2:  # the break landed inside a starred run: close it on line one, reopen on line two
        one, two = one + "*", "*" + two
    return [one, two]


lines = lines_of(a.title)
longest = max(len(l.replace("*", "")) for l in lines)
if len(lines) > 2 or longest > MAX_CHARS + 4:
    print(f"WARNING: title is {len(lines)} lines, longest {longest} characters. Aim for 2 lines of {MAX_CHARS}.")
px = min(TITLE_PX, int(940 / (longest * 0.56)))
block_h = len(lines) * (px * 1.18 + 18)

# the title goes in the space under the chin, never on the face, and stays inside the 4:5 band
face, _ = face_of(frame)
chin = int(face[1] + face[3] * 1.12) if face is not None else None
if a.title_y is not None:
    title_y = a.title_y
elif chin is not None:
    title_y = int(chin + 40 + block_h / 2)
else:
    title_y = TITLE_Y
title_y = int(min(title_y, BAND[1] - 70 - block_h / 2))

sales = a.style == "sales"


def line_html(l):
    whole = re.fullmatch(r"\*([^*]+)\*", l)
    if whole:  # the whole line is the keyword line
        style = f"background:{YELLOW};color:{INK}" if sales else f"background:{BLUE};color:{YELLOW}"
        return f'<div class="l" style="{style}">{whole.group(1)}</div>'
    kw = YELLOW
    return f'<div class="l">{re.sub(r"\*([^*]+)\*", rf"<span style=\"color:{kw}\">\1</span>", l)}</div>'


def rgba(hexc, a):
    h = hexc.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


def uri(path):
    mime = "image/png" if path.endswith(".png") else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(open(path, "rb").read()).decode()


html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@import url('{FONTS}');
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ width:{W}px; height:{H}px; position:relative; overflow:hidden; font-family:'{LATIN}', sans-serif; }}
.bg {{ position:absolute; inset:0; width:{W}px; height:{H}px; object-fit:cover; }}
.fade {{ position:absolute; inset:0; background:linear-gradient(to top, {rgba(BLUE, .96)} 0%, {rgba(BLUE, .62)} 20%, {rgba(BLUE, .22)} 40%, {rgba(BLUE, 0)} 56%); }}
.logo {{ position:absolute; left:50%; top:{LOGO_Y}px; width:{LOGO_W}px; transform:translateX(-50%); }}
.title {{ position:absolute; left:0; right:0; top:{title_y}px; transform:translateY(-50%); display:flex; flex-direction:column; align-items:center; }}
.l {{ background:{BLUE}; color:#fff; font-weight:600; font-size:{px}px; line-height:1.18; padding:8px 26px 10px; white-space:nowrap; }}  /* 600, not heavier */
</style></head><body>
<img class="bg" src="{uri(frame)}"><div class="fade"></div>{f'<img class="logo" src="{uri(LOGO)}">' if LOGO else ""}
<div class="title">{''.join(line_html(l) for l in lines)}</div>
</body></html>"""

with sync_playwright() as pw:
    b = pw.chromium.launch(channel=BROWSER)
    pg = b.new_page(viewport={"width": W, "height": H})
    pg.set_content(html, wait_until="networkidle")
    pg.evaluate("document.fonts.ready")
    box = pg.locator(".title").bounding_box()
    shot = pg.screenshot(type="png")
    b.close()

cover = Image.open(io.BytesIO(shot)).convert("RGB")
cover.save(out, quality=93)

problems = []
if box["y"] < BAND[0] or box["y"] + box["height"] > BAND[1]:
    problems.append("the title leaves the 4:5 band")
if box["width"] > W:
    problems.append("the title is wider than the cover")
if chin is not None and box["y"] < chin - 10:
    problems.append(f"the title starts {int(chin - box['y'])}px above the chin (the face is low in this frame): try another --frame, or accept it")
if face is None:
    problems.append("no face found in the frame, title placed at the default height: check it by eye")

# the check sheet: reels tab on the left, posts grid crop on the right
grid = cover.crop((0, BAND[0], W, BAND[1]))
sh = 960
left = cover.resize((W * sh // H, sh))
right = grid.resize((W * sh // (BAND[1] - BAND[0]), sh))
sheet = Image.new("RGB", (left.width + right.width + 90, sh + 80), INK)
sheet.paste(left, (30, 60)); sheet.paste(right, (left.width + 60, 60))
d = ImageDraw.Draw(sheet)
d.text((30, 22), "REELS TAB (9:16)", fill="#fff"); d.text((left.width + 60, 22), "POSTS GRID (4:5)", fill="#fff")
check = os.path.join(cdir, "cover-check.jpg")
sheet.save(check, quality=90)

print(f"cover: {out}\ncheck: {check}\ntitle: {px}px, {len(lines)} line(s), centre y {title_y}")
for pr in problems:
    print("NOTE:", pr)
