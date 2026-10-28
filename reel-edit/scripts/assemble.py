"""Join a reel folder's camera takes into one master video, ready for transcribe.py.

    python assemble.py <reel folder> <workdir> [--cuts cuts.txt]

A reel folder holds the camera takes (.mov from his phone) and, optionally, B-roll (any other video,
its file name says what it shows). Takes are ordered by when they were filmed. Writes
<workdir>/master.mp4 (1440x2560, 30 fps) and <workdir>/takes.json (each take's place in the master).

Run it once with no cuts, transcribe the master, then write cuts.txt and run it again:

    drop CGAK5759                      # a line he says again in a later take
    trim VVTY3909 from=0.35 to=11.20   # seconds inside that take; either side may be left out
    keep ORME2737 0.27-7.16 9.47-11.62 # one long take with pauses or a repeated line inside it: only these stretches stay
    order VVTY3909 EGHA4017 NUSC7920   # only when filming order is not the script's order
    tail 0.15                          # the end of the video keeps this much after the last word (default 0.3)
    clean UDKI8679 26.30-30.05         # a phone-mic take: adds the tone match from clean-eq.txt
    voice raw CGAK5759                 # skip the voice cleaning on one take (it still gets the -14 LUFS gain)

Every take's voice is cleaned and set to -14 LUFS (see VOICE below): highpass, RNNoise, a gentle
expander for the room echo, a fixed gain, a limiter.

Every end in cuts.txt is written 0.06s after the last word. The video's very last end is the one
exception: it is pushed out so END_TAIL is left after the word and it finishes, with a softer fade.
Names are the file names without the extension. Raw takes are never changed.
"""
import argparse, json, os, subprocess

TAKE_EXT = {".mov"}
VIDEO_EXT = {".mov", ".mp4", ".m4v", ".webm", ".mkv"}
W, H = 1440, 2560
CUT_TAIL = 0.06   # how far after the last word every end in cuts.txt is written
END_TAIL = 0.3    # what the video's very last word keeps instead, so it finishes

ap = argparse.ArgumentParser()
ap.add_argument("folder")
ap.add_argument("workdir")
ap.add_argument("--cuts")
a = ap.parse_args()
folder, workdir = os.path.abspath(a.folder), os.path.abspath(a.workdir)
parts = os.path.join(workdir, "takes")
os.makedirs(parts, exist_ok=True)


def probe(path, entries):
    return subprocess.run(["ffprobe", "-v", "error", "-show_entries", entries, "-of", "csv=p=0", path],
                          capture_output=True, text=True).stdout.strip()


def filmed_at(path):
    """The phone's own recording time; a copied file's modified time is only the fallback."""
    return probe(path, "format_tags=creation_time") or f"~{os.path.getmtime(path):020.3f}"


files = [f for f in sorted(os.listdir(folder))
         if os.path.splitext(f)[1].lower() in VIDEO_EXT and " - edited" not in f]
# takes: the .mov files (iPhone). A folder with no .mov (Android saves .mp4): every video is a take.
# Either way, a file whose name starts with "broll" is B-roll, never a take.
is_broll = lambda f: f.lower().startswith("broll")
movs = [f for f in files if os.path.splitext(f)[1].lower() in TAKE_EXT]
takes = sorted((f for f in (movs or files) if not is_broll(f)), key=lambda f: filmed_at(os.path.join(folder, f)))
brolls = [f for f in files if f not in takes]
if not takes:
    raise SystemExit(f"no camera takes (.mov) in {folder}")

stem = lambda f: os.path.splitext(f)[0]
by_stem = {stem(f): f for f in takes}
drop, trim, keep, clean, raw_voice = set(), {}, {}, {}, set()
SKILL_ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


# ---- the voice, every take.
# Target -14 LUFS integrated, true peak under -1 dBTP: the common convention for Reels, Shorts and TikTok
# (Instagram publishes no number; louder gains nothing because platforms turn it down). Tuned on Stuck on
# Idea's takes: RNNoise takes the room down ~12 dB, the expander a further ~9 dB in pauses and makes the
# sound die 1 to 2 dB faster after each word (his slight room echo), the speech itself is unchanged.
VOICE = {
    "lufs": -14.0,
    "limit": 0.84,                 # -1.5 dBFS sample peak, so true peak stays under -1 dBTP after AAC
    "highpass": 80,
    "rnnoise_mix": 0.85,           # a little of the room left so it never sounds underwater
    "gate_below_speech": 14,       # expander threshold: this many dB under the take's speech level
    "gate_range": 0.35,            # the most it lowers the room: -9 dB (0.25 sounded dead-silent in pauses)
    "gate_release": 120,
    # No compressor, on purpose: with one in the chain Whisper heard Arabic speech as English and wrote the
    # whole transcript translated (tested 27 Oct 2026). Each take is already even (loudness range 1 to 2
    # LU) and every take is set to the same level, so it was not needed.
}
voice_cache = {}


def speech_level(src, t0, d, chain):
    """dB of the loud 10% of 50 ms windows: his speaking level, ignoring pauses."""
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{d:.3f}", "-i", src, "-vn", "-af", chain,
                          "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True, cwd=SKILL_ASSETS).stdout
    a = np.frombuffer(raw, np.float32)
    w = 2400
    db = [20 * np.log10(np.sqrt(np.mean(a[i:i + w] ** 2)) + 1e-9) for i in range(0, len(a) - w, w)]
    return float(np.percentile(db, 90)) if db else -20.0


def voice_chain(name, src, spans, phone):
    """The chain for one take, measured once over everything kept from it, so every stretch of a take gets
    the same treatment: highpass, RNNoise, a gentle expander for the room tail, the phone-mic tone match (only on a `clean` take, from <workdir>/clean-eq.txt), then a fixed gain to
    VOICE["lufs"] and a limiter. Fixed gain, never loudnorm: loudnorm pads the audio and the take drifts
    out of sync. `voice raw <take>` in cuts.txt skips the cleaning (gain and limiter still apply)."""
    if name in voice_cache:
        return voice_cache[name]
    t0, d = min(s for s, _ in spans), max(e for _, e in spans) - min(s for s, _ in spans)
    eq = os.path.join(workdir, "clean-eq.txt")
    eq = (open(eq).read().strip() + ",") if phone and os.path.exists(eq) else ""
    if name in raw_voice:
        chain = eq
    else:
        base = f"highpass=f={VOICE['highpass']},arnndn=m=rnnoise-sh.rnnn:mix={VOICE['rnnoise_mix']}"
        thr = 10 ** ((speech_level(src, t0, d, base) - VOICE["gate_below_speech"]) / 20)
        chain = (f"{base},agate=threshold={thr:.4f}:ratio=2:range={VOICE['gate_range']}:attack=5:"
                 f"release={VOICE['gate_release']}:knee=4:detection=rms,{eq}")
    meter = subprocess.run(["ffmpeg", "-hide_banner", "-ss", f"{t0:.3f}", "-t", f"{d:.3f}", "-i", src, "-vn",
                            "-af", chain + "ebur128", "-f", "null", "-"], capture_output=True, text=True, cwd=SKILL_ASSETS).stderr
    lufs = float(meter.rsplit("I:", 1)[1].split("LUFS")[0])
    voice_cache[name] = f"{chain}volume={VOICE['lufs'] - lufs:.2f}dB,alimiter=limit={VOICE['limit']}:level=false,"
    print(f"voice {name}: {lufs:.1f} LUFS after cleaning, {VOICE['lufs'] - lufs:+.1f} dB to {VOICE['lufs']:.0f}" + (" (raw)" if name in raw_voice else ""))
    return voice_cache[name]
if a.cuts:
    for raw in open(a.cuts, encoding="utf-8"):
        line = raw.split("#")[0].split()
        if not line:
            continue
        cmd, names = line[0], line[1:]
        if cmd == "tail":
            END_TAIL = float(names[0])
            continue
        if cmd == "voice":   # voice raw <take>: no denoise/expander/compressor on that take
            if names[:1] != ["raw"]:
                raise SystemExit(f"cuts.txt: unknown line '{raw.strip()}' (only 'voice raw <take>')")
            names = names[1:]
        if cmd in ("keep", "clean"):
            names, spans = names[:1], [tuple(float(x) for x in r.split("-")) for r in names[1:]]
        unknown = [n for n in names if "=" not in n and n not in by_stem]
        if unknown:
            raise SystemExit(f"cuts.txt names takes that are not in the folder: {unknown}")
        if cmd == "drop":
            drop.update(names)
        elif cmd == "trim":
            trim[names[0]] = {k: float(v) for k, v in (x.split("=") for x in names[1:])}
        elif cmd == "keep":
            keep[names[0]] = spans
        elif cmd == "clean":
            clean.setdefault(names[0], []).extend(spans)
        elif cmd == "voice":
            raw_voice.update(names)
        elif cmd == "order":
            takes = [by_stem[n] for n in names] + [f for f in takes if stem(f) not in names]
        else:
            raise SystemExit(f"cuts.txt: unknown line '{raw.strip()}'")

kept = [stem(f) for f in takes if stem(f) not in drop]
last_take = kept[-1] if kept else None
end_note = None
listing, table, at = [], [], 0.0
for f in takes:
    name, src = stem(f), os.path.join(folder, f)
    if name in drop:
        table.append({"take": name, "dropped": True})
        continue
    full = float(probe(src, "format=duration"))
    spans = keep.get(name) or [(trim.get(name, {}).get("from", 0.0), trim.get(name, {}).get("to", full))]
    fix = voice_chain(name, src, [(s0, min(s1, full)) for s0, s1 in spans], phone=name in clean)
    for i, (t0, t1) in enumerate(spans):
        t1 = min(t1, full)
        out = os.path.join(parts, f"{name}.mp4" if len(spans) == 1 else f"{name}_{i + 1:02d}.mp4")
        dirty = any(abs(c0 - t0) < 0.05 and abs(c1 - t1) < 0.05 for c0, c1 in clean.get(name, []))
        # the video's last word keeps END_TAIL instead of CUT_TAIL so it finishes; between takes the cuts stay tight
        is_end = name == last_take and i == len(spans) - 1 and (name in keep or "to" in trim.get(name, {}))
        fade = 0.03
        if is_end:
            t1 = min(t1 + max(0.0, END_TAIL - CUT_TAIL), full)
            fade = 0.12   # a soft fade on the last word, every other cut is a quick de-click
            end_note = f"end tail: {END_TAIL:.2f}s after the last word, on {name}" + ("  (the take ran out first)" if t1 >= full else "")
        d = t1 - t0
        # seeking before -i is still exact to the frame when re-encoding. ffmpeg applies the phone's rotation itself.
        # cwd is the skill's assets folder so arnndn finds its model by a plain name (no drive-letter colon in the filter)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t0:.3f}", "-t", f"{d:.3f}", "-i", src,
                        "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps=30,format=yuv420p",
                        "-af", f"{fix}afade=t=in:d=0.02,afade=t=out:st={max(0, d - fade):.3f}:d={fade}",
                        "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                        "-video_track_timescale", "30000", out], check=True, cwd=SKILL_ASSETS)
        if dirty:
            print(f"phone-mic tone match on {name} {t0:.2f}-{t1:.2f}")
        real = float(probe(out, "format=duration"))
        table.append({"take": name if len(spans) == 1 else f"{name} #{i + 1}", "start": round(at, 2), "end": round(at + real, 2), "from": round(t0, 2), "to": round(t1, 2)})
        listing.append(f"file '{out.replace(os.sep, '/')}'")
        at += real

lst = os.path.join(workdir, "takes.txt")
open(lst, "w", encoding="utf-8").write("\n".join(listing))
master = os.path.join(workdir, "master.mp4")
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", master], check=True)
json.dump({"folder": folder, "takes": table, "broll": brolls}, open(os.path.join(workdir, "takes.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)

for t in table:
    print(f"{t['take']:<14}", "dropped" if t.get("dropped") else f"{t['start']:6.2f} - {t['end']:6.2f}   (take {t['from']:.2f} to {t['to']:.2f})")
print(f"master: {master} ({at:.2f}s)")
if end_note:
    print(end_note)
for b in brolls:
    print(f"b-roll: {b}")
