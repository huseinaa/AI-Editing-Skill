"""Study reels you like, so your own edits borrow their taste (never their content).

    python references.py <link or file> [<link or file> ...] [--out <folder>] [--no-transcribe]

Links are downloaded with yt-dlp (pip install yt-dlp). A link that will not download (a login wall,
a blocked network) is reported and skipped: download that reel yourself and pass the file instead.

For each reel, in <out>/<name>/ (default out: local/references at the skill root):
    video.<ext>    the reel
    sheet-N.jpg    one frame per second, 8 across, the time on each, the safe box drawn in magenta
    words.txt      the transcript with word times (language detected), unless --no-transcribe
    analysis.md    duration, size, cuts and shot lengths, speaking pace, pauses, loudness
and <out>/summary.md with every reel's numbers side by side.

The numbers are a starting point. The style is read from the contact sheets by eye: where the text
sits, how big, how long it stays, what is shown on screen and when.
"""
import argparse, json, os, re, shutil, subprocess, sys
try:
    import truststore; truststore.inject_into_ssl()  # for networks that re-sign HTTPS
except ImportError:
    pass
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MODEL = os.path.expanduser("~/.cache/faster-whisper-small")
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
SCENE = 0.2          # scene score that counts as a cut: a jump cut between takes of one framing scores ~0.22
PAUSE = 0.3          # a gap between words at least this long counts as a pause
COLS, ROWS, TW = 8, 6, 216   # contact sheet: 8 x 6 frames per sheet, each 216 px wide

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("inputs", nargs="+", help="reel links or video files")
ap.add_argument("--out", default=os.path.join(ROOT, "local", "references"))
ap.add_argument("--no-transcribe", action="store_true", help="skip the transcript (faster, no pace numbers)")
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def slug(text):
    s = re.sub(r"[^A-Za-z0-9_-]+", "-", text).strip("-")
    return s[-40:] or "reel"


def unique_dir(name):
    d, n = os.path.join(a.out, name), 2
    while os.path.exists(d) and os.listdir(d):
        d, n = os.path.join(a.out, f"{name}-{n}"), n + 1
    os.makedirs(d, exist_ok=True)
    return d


def fetch(src):
    """Returns (folder, video path), or None with the reason printed."""
    if os.path.isfile(src):
        if os.path.splitext(src)[1].lower() not in VIDEO_EXT:
            print(f"skip {src}: not a video file")
            return None
        d = unique_dir(slug(os.path.splitext(os.path.basename(src))[0]))
        dst = os.path.join(d, "video" + os.path.splitext(src)[1].lower())
        shutil.copy2(src, dst)
        return d, dst
    if not re.match(r"https?://", src):
        print(f"skip {src}: not a file on disk and not a link")
        return None
    try:
        import yt_dlp
    except ImportError:
        print(f"skip {src}: downloading links needs yt-dlp (pip install yt-dlp), or download the reel and pass the file")
        return None
    d = unique_dir(slug(src.rstrip("/").split("?")[0].split("/")[-1]))
    opts = {"outtmpl": os.path.join(d, "video.%(ext)s"), "format": "bv*[height<=1920]+ba/b",
            "merge_output_format": "mp4", "quiet": True, "no_warnings": True, "noplaylist": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(src, download=True)
        json.dump({"url": src, "title": info.get("title"), "uploader": info.get("uploader"),
                   "views": info.get("view_count"), "likes": info.get("like_count")},
                  open(os.path.join(d, "source.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    except Exception as e:  # yt-dlp raises many kinds; any of them means "get the file another way"
        print(f"skip {src}: download failed ({str(e).splitlines()[0][:160]}). Download it yourself and pass the file.")
        shutil.rmtree(d, ignore_errors=True)
        return None
    vids = [f for f in os.listdir(d) if os.path.splitext(f)[1].lower() in VIDEO_EXT]
    if not vids:
        print(f"skip {src}: nothing was downloaded")
        return None
    return d, os.path.join(d, vids[0])


def probe(video):
    out = run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height:format=duration",
               "-of", "json", video]).stdout
    j = json.loads(out or "{}")
    st = (j.get("streams") or [{}])[0]
    return float(j.get("format", {}).get("duration", 0)), st.get("width", 0), st.get("height", 0)


def cuts(video):
    err = run(["ffmpeg", "-hide_banner", "-i", video, "-vf", f"scale=270:-2,select='gt(scene,{SCENE})',showinfo",
               "-an", "-f", "null", "-"]).stderr
    out = []
    for t in (round(float(x), 2) for x in re.findall(r"pts_time:([\d.]+)", err)):
        if not out or t - out[-1] > 0.2:   # one cut can score on two frames in a row
            out.append(t)
    return out


def loudness(video):
    err = run(["ffmpeg", "-hide_banner", "-i", video, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    tail = err.rsplit("Summary:", 1)[-1]
    i = re.search(r"I:\s+(-?[\d.]+) LUFS", tail)
    p = re.search(r"Peak:\s+(-?[\d.]+) dBFS", tail)
    return (float(i.group(1)) if i else None), (float(p.group(1)) if p else None)


def sheets(video, d, dur, w, h):
    frames = os.path.join(d, "frames")
    os.makedirs(frames, exist_ok=True)
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-vf", f"fps=1,scale={TW}:-2", os.path.join(frames, "%04d.jpg")])
    files = sorted(os.listdir(frames))
    if not files:
        return []
    th = Image.open(os.path.join(frames, files[0])).height
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    out, per = [], COLS * ROWS
    for n in range(0, len(files), per):
        chunk = files[n:n + per]
        rows = (len(chunk) + COLS - 1) // COLS
        sheet = Image.new("RGB", (COLS * TW, rows * th), (20, 20, 20))
        dr = ImageDraw.Draw(sheet)
        for i, f in enumerate(chunk):
            x, y = (i % COLS) * TW, (i // COLS) * th
            sheet.paste(Image.open(os.path.join(frames, f)), (x, y))
            if h and w and h / w > 1.6:   # vertical video: draw the safe box (x 90-1350, y 360-1920 of 1440x2560)
                dr.rectangle([x + TW * 90 / 1440, y + th * 360 / 2560, x + TW * 1350 / 1440, y + th * 1920 / 2560],
                             outline=(255, 0, 255), width=1)
            dr.rectangle([x, y, x + 46, y + 20], fill=(0, 0, 0))
            dr.text((x + 4, y + 2), f"{n + i}s", fill=(255, 255, 255), font=font)
        path = os.path.join(d, f"sheet-{n // per + 1}.jpg")
        sheet.save(path, quality=85)
        out.append(os.path.basename(path))
    shutil.rmtree(frames, ignore_errors=True)
    return out


_model = None


def transcribe(video, d):
    global _model
    from faster_whisper import WhisperModel
    if _model is None:
        _model = WhisperModel(MODEL, device="cpu", compute_type="int8")
    wav = os.path.join(d, "audio.wav")
    run(["ffmpeg", "-v", "error", "-y", "-i", video, "-ac", "1", "-ar", "16000", wav])
    segs, info = _model.transcribe(wav, word_timestamps=True)
    words = [(round(x.start, 2), round(x.end, 2), x.word.strip()) for s in segs for x in s.words]
    os.remove(wav)
    with open(os.path.join(d, "words.txt"), "w", encoding="utf-8") as fh:
        for s, e, t in words:
            fh.write(f"{s:.2f} {e:.2f} {t}\n")
    return words, info.language


rows = []
for src in a.inputs:
    got = fetch(src)
    if not got:
        continue
    d, video = got
    name = os.path.basename(d)
    print(f"{name}: analysing")
    dur, w, h = probe(video)
    cut_t = cuts(video)
    bounds = [0.0] + cut_t + [dur]
    shots = [b - a_ for a_, b in zip(bounds, bounds[1:]) if b - a_ > 0.05]
    lufs, peak = loudness(video)
    sheet_files = sheets(video, d, dur, w, h)
    r = {"name": name, "dur": dur, "size": f"{w}x{h}", "cuts": len(cut_t),
         "avg_shot": sum(shots) / len(shots) if shots else dur, "longest_shot": max(shots) if shots else dur,
         "lufs": lufs, "peak": peak}
    lines = [f"# {name}", "", f"Source: {src}", ""]
    if os.path.exists(os.path.join(d, "source.json")):
        s = json.load(open(os.path.join(d, "source.json"), encoding="utf-8"))
        lines += [f"Uploader: {s.get('uploader')} · views: {s.get('views')} · likes: {s.get('likes')}", ""]
    lines += ["| Measure | Value |", "|---|---|",
              f"| Duration | {dur:.1f} s |", f"| Size | {w}x{h} |",
              f"| Cuts (scene changes over {SCENE}) | {len(cut_t)} |",
              f"| Average shot | {r['avg_shot']:.1f} s |", f"| Longest shot | {r['longest_shot']:.1f} s |",
              f"| Loudness | {lufs if lufs is not None else '?'} LUFS, peak {peak if peak is not None else '?'} dBFS |"]
    if not a.no_transcribe:
        try:
            words, lang = transcribe(video, d)
        except Exception as e:
            words, lang = [], None
            print(f"{name}: no transcript ({str(e).splitlines()[0][:120]})")
        if words:
            gaps = [(words[i][1], words[i + 1][0]) for i in range(len(words) - 1) if words[i + 1][0] - words[i][1] >= PAUSE]
            talk = words[-1][1] - words[0][0]
            r.update({"wpm": len(words) / talk * 60 if talk > 0 else 0, "first_word": words[0][0], "pauses": len(gaps), "lang": lang})
            lines += [f"| Language heard | {lang} |", f"| First word at | {words[0][0]:.2f} s |",
                      f"| Words | {len(words)} |", f"| Pace | {r['wpm']:.0f} words a minute |",
                      f"| Pauses of {PAUSE} s or more | {len(gaps)}"
                      + (f", longest {max(e - s for s, e in gaps):.2f} s |" if gaps else " |")]
        elif not a.no_transcribe:
            lines += ["| Speech | none heard (music or text only) |"]
    lines += ["", "## Cut times (s)", "", ", ".join(f"{t:.2f}" for t in cut_t) or "none", "",
              "## Contact sheets", "", *[f"- {f}" for f in sheet_files], "",
              "## Read from the sheets by eye", "",
              "- Text: where it sits, size, words per line, how long it stays, how it appears",
              "- Captions: position, words per chunk, style",
              "- What is shown on screen and on which words (B-roll, screenshots, full screens, the face)",
              "- Pacing: what happens at each cut, zooms, how the hook and the ending look",
              "", "Take inspiration, never copy: write down how it is edited, never its lines, graphics, music or branding.", ""]
    open(os.path.join(d, "analysis.md"), "w", encoding="utf-8").write("\n".join(lines))
    rows.append(r)
    print(f"{name}: {dur:.1f}s, {len(cut_t)} cuts, avg shot {r['avg_shot']:.1f}s, {len(sheet_files)} sheet(s)")

if not rows:
    sys.exit("nothing analysed")
fmt = lambda v, f="{:.1f}": "?" if v is None else f.format(v)
summary = ["# Reference reels", "", "| Reel | Duration | Cuts | Avg shot | Pace (wpm) | First word | Pauses | LUFS |",
           "|---|---|---|---|---|---|---|---|"]
for r in rows:
    summary.append(f"| {r['name']} | {r['dur']:.1f} s | {r['cuts']} | {r['avg_shot']:.1f} s | {fmt(r.get('wpm'), '{:.0f}')} | "
                   f"{fmt(r.get('first_word'), '{:.2f}')} s | {r.get('pauses', '?')} | {fmt(r['lufs'])} |")
summary += ["", "Next: look at every contact sheet, then write the patterns seen in at least 2 reels into local/style.md.", ""]
open(os.path.join(a.out, "summary.md"), "w", encoding="utf-8").write("\n".join(summary))
print(f"\nwrote {os.path.join(a.out, 'summary.md')}")
