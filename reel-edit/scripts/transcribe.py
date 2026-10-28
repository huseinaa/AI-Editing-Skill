"""Transcribe a reel with word timestamps and grab reference frames.

    python transcribe.py <video> <workdir> [--lang ar|en] [--prompt "UI UX Claude Code ..."]

Writes words.txt (start end word, one per line), words.json, and frames/f*.jpg at 1s, mid, end
so the face position can be read for FACE in edit.py. Captions are written from THIS, never from
the script: he changes wording while recording.
"""
import argparse, json, os, subprocess
try:
    import truststore; truststore.inject_into_ssl()  # this network re-signs TLS
except ImportError:
    pass
from faster_whisper import WhisperModel
from reel_edit.brand import CAPTION_LANG

MODEL = os.path.expanduser("~/.cache/faster-whisper-small")

ap = argparse.ArgumentParser()
ap.add_argument("video")
ap.add_argument("workdir")
ap.add_argument("--lang", default=CAPTION_LANG)
ap.add_argument("--prompt", default="UI UX user interface user experience app software AI Claude Code website skills")
a = ap.parse_args()
os.makedirs(os.path.join(a.workdir, "frames"), exist_ok=True)

wav = os.path.join(a.workdir, "audio.wav")
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-ac", "1", "-ar", "16000", wav], check=True)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", a.video],
                           capture_output=True, text=True).stdout)
for name, t in (("start", 1.0), ("mid", dur / 2), ("end", max(0, dur - 2))):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", a.video, "-frames:v", "1",
                    "-vf", "scale=360:-1", os.path.join(a.workdir, "frames", f"f_{name}.jpg")], check=True)

model = WhisperModel(MODEL, device="cpu", compute_type="int8")
segs, _ = model.transcribe(wav, language=a.lang, word_timestamps=True, initial_prompt=a.prompt)
words = [{"s": round(w.start, 2), "e": round(w.end, 2), "w": w.word.strip()} for seg in segs for w in seg.words]
json.dump(words, open(os.path.join(a.workdir, "words.json"), "w", encoding="utf-8"), ensure_ascii=False)
with open(os.path.join(a.workdir, "words.txt"), "w", encoding="utf-8") as fh:
    for w in words:
        fh.write(f"{w['s']:6.2f} {w['e']:6.2f} {w['w']}\n")
print(f"{len(words)} words, {dur:.2f}s -> {a.workdir}")
# Whisper can slip into writing Arabic speech as an English translation (seen 27 Oct 2026 when a compressor
# was in the voice chain). Captions must come from what he said, so say so loudly.
text = " ".join(w["w"] for w in words)
letters = sum(c.isalpha() for c in text)
arabic = sum("؀" <= c <= "ۿ" for c in text)
if a.lang == "ar" and letters and arabic / letters < 0.4:
    print(f"WARNING: only {arabic / letters:.0%} of the transcript is in Arabic letters. Whisper probably translated "
          "it to English. Check words.txt before captioning; if so, transcribe the raw takes instead.")
