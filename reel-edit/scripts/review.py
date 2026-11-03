"""Reel cut review: original-take handles, the finished look, and source-time feedback.

    python review.py WORK --prepare
    python review.py WORK [--no-browser] [--port N]

The review package lives beside the finished reel in _edit. It snapshots the rendered
edit and its take map. Existing working timelines are never reset by --prepare.
"""
import argparse
import copy
import hashlib
import json
import math
import os
import re
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

import numpy as np

from reel_edit.project import load

SKILL = Path(__file__).resolve().parents[1]
FPS = 30
NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, path)


def run(args):
    return subprocess.run(args, check=True, capture_output=True, creationflags=NO_WINDOW)


def probe(path):
    return json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]).stdout)


def nframes(path):
    s = next(s for s in probe(path)["streams"] if s["codec_type"] == "video")
    return int(s.get("nb_frames") or round(float(s["duration"]) * FPS))


def encode_parts(parts, output, width=1080, crf=20):
    """Frame-counted concatenation; video and audio share the same zero-based clock."""
    args = ["ffmpeg", "-y", "-v", "error", "-filter_complex_threads", "1"]
    filters, labels = [], []
    for i, (source, start, frames) in enumerate(parts):
        duration = frames / FPS
        args += ["-ss", f"{start:.7f}", "-i", str(source)]
        filters += [
            f"[{i}:v]fps=30:start_time=0,scale={width}:{width * 16 // 9}:force_original_aspect_ratio=increase,"
            f"crop={width}:{width * 16 // 9},setsar=1,tpad=stop_mode=clone:stop_duration=1,"
            f"trim=end_frame={frames},setpts=N/(30*TB),format=yuv420p[v{i}]",
            f"[{i}:a]aresample=48000,apad,atrim=duration={duration:.7f},asetpts=PTS-STARTPTS[a{i}]",
        ]
        labels.append(f"[v{i}][a{i}]")
    filters.append("".join(labels) + f"concat=n={len(parts)}:v=1:a=1[v][a]")
    output = Path(output)
    tmp = output.with_name(output.stem + ".part.mp4")
    upright = output.with_name(output.stem + ".upright.mp4")
    try:
        run(args + ["-filter_complex", ";".join(filters), "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", str(crf), "-g", "15", "-bf", "0",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-ac", "2",
                    "-video_track_timescale", "30000", "-movflags", "+faststart", str(tmp)])
        if abs(nframes(tmp) - sum(p[2] for p in parts)) > 1:
            raise ValueError("Rendered frame count does not match the timeline")
        # A camera input's display matrix can survive a complex concat even after its
        # pixels were autorotated. Clear that container tag without re-encoding pixels.
        stream = next(s for s in probe(tmp)["streams"] if s["codec_type"] == "video")
        if any(s.get("rotation", 0) for s in stream.get("side_data_list", [])):
            run(["ffmpeg", "-y", "-v", "error", "-display_rotation:v:0", "0", "-i", str(tmp),
                 "-map", "0", "-c", "copy", "-map_metadata", "-1", str(upright)])
            os.replace(upright, tmp)
        os.replace(tmp, output)
    finally:
        tmp.unlink(missing_ok=True)
        upright.unlink(missing_ok=True)


def parts_for(clip, source, frames, snapshot):
    """Finished composition inside the AI keep; raw footage outside it for restored handles."""
    end = source + frames / FPS
    cuts = sorted({source, end} | {p for r in clip["keeps"] for p in (r["src"], r["src"] + r["frames"] / FPS)
                                 if source < p < end})
    parts = []
    consumed = 0
    for j, (a, b) in enumerate(zip(cuts, cuts[1:])):
        nf = frames - consumed if j == len(cuts) - 2 else round((b - source) * FPS) - consumed
        consumed += nf
        if nf <= 0:
            continue
        keep = next((r for r in clip["keeps"] if r["src"] - 1e-6 <= (a + b) / 2 < r["src"] + r["frames"] / FPS), None)
        parts.append((snapshot if keep else clip["path"], keep["master"] / FPS + a - keep["src"] if keep else raw_time(clip, a), nf))
    return parts


def raw_time(clip, t):
    """Map the proxy's frame grid back to the take's recorded, fractional cut times."""
    keep = min(clip["keeps"], key=lambda r: max(r["src"] - t, t - r["src"] - r["frames"] / FPS, 0))
    a, b = keep["src"], keep["src"] + keep["frames"] / FPS
    if t < a:
        value = keep["raw_from"] + t - a
    elif t > b:
        value = keep["raw_to"] + t - b
    else:
        value = keep["raw_from"] + (t - a) / (b - a) * (keep["raw_to"] - keep["raw_from"])
    return max(0, min(value, clip["duration"]))


def package(work):
    p = load(str(work))
    return Path(p.output).parent / "_edit", p


def prepare(work):
    import shutil
    work = Path(work).resolve()
    folder, p = package(work)
    rv = folder / "review"
    rv.mkdir(parents=True, exist_ok=True)
    if (rv / "project.json").exists():
        print("Existing review package kept, including your timeline:", folder)
        return folder
    output = Path(p.output)
    if not output.exists():
        raise ValueError("Build and check the reel before preparing its cut review")
    take_map = read(work / "takes.json")
    source_root = Path(take_map["folder"])
    if not source_root.exists():
        source_root = output.parent / "assets"
    sources = {f.stem: f for f in source_root.iterdir() if f.suffix.lower() in (".mov", ".mp4", ".mkv")}
    snapshot = rv / "baseline.mp4"
    shutil.copy2(output, snapshot)
    rows = [r for r in take_map["takes"] if not r.get("dropped")]
    clips, lane = {}, []
    total = nframes(snapshot)
    for n, row in enumerate(rows):
        cid = row["take"].split(" #")[0]
        start = round(row["start"] * FPS)
        stop = round(rows[n + 1]["start"] * FPS) if n + 1 < len(rows) else total
        if cid not in sources:
            raise ValueError(f"Missing raw take: {cid}")
        if cid not in clips:
            info = probe(sources[cid])
            duration = float(info["format"]["duration"])
            clips[cid] = {"id": cid, "take": len(clips) + 1, "path": str(sources[cid]),
                          "duration": duration, "screen_offset": 0, "keeps": []}
        source_start = round(row["from"] * FPS) / FPS
        keep = {"src": source_start, "frames": stop - start, "master": start,
                "raw_from": row["from"], "raw_to": row["to"]}
        clips[cid]["keeps"].append(keep)
        lane.append({"clip": cid, "src": source_start, "len": stop - start, "at": start})
    peaks = {}
    for cid, c in clips.items():
        path = rv / f"{cid}.mp4"
        frames = math.floor(c["duration"] * FPS)
        # Anchor the proxy exactly at the fractional source start used by the timeline.
        parts = parts_for(c, 0, frames, snapshot)
        encode_parts(parts, path, width=540, crf=25)
        raw = run(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"]).stdout
        samples = np.frombuffer(raw, np.float32)
        hop = 320
        a = np.abs(samples[:len(samples) // hop * hop]).reshape(-1, hop).max(axis=1)
        top = max(float(np.percentile(a, 99.5)), 1e-6)
        peaks[cid] = np.clip(a / top * 255, 0, 255).astype(int).tolist()
        print("Review take ready:", cid, flush=True)
    tl = {"fps": FPS, "lanes": {"voice": lane, "screen": copy.deepcopy(lane)}}
    phrases = []
    for text, s, e in p.captions:
        for item in lane:
            a, b = max(s, item["at"] / FPS), min(e, (item["at"] + item["len"]) / FPS)
            if b > a:
                phrases.append({"id": str(len(phrases)), "clip": item["clip"], "s": item["src"] + a - item["at"] / FPS,
                                "e": item["src"] + b - item["at"] / FPS, "text": text})
    data = {"name": output.stem, "work": str(work), "output": str(output), "snapshot": str(snapshot),
            "clips": list(clips.values()), "phrases": phrases,
            "baseline_sha256": hashlib.sha256(snapshot.read_bytes()).hexdigest()}
    write(rv / "timeline.ai.json", tl)
    write(rv / "timeline.json", tl)
    write(rv / "peaks.json", {"per_second": 50, "clips": peaks})
    write(rv / "project.json", data)
    pyw = Path(sys.executable).with_name("pythonw.exe")
    exe = pyw if pyw.exists() else Path(sys.executable)
    launch = output.parent / "Edit cuts.cmd"
    launch.write_text(f'@echo off\nstart "" "{exe}" "{Path(__file__).resolve()}" "{folder}"\n', encoding="utf-8")
    print("Open:", launch, flush=True)
    return folder


def validate(tl, data):
    if tl.get("fps") != FPS or set(tl.get("lanes", {})) != {"screen", "voice"}:
        raise ValueError("A reel timeline needs linked picture and voice at 30 fps")
    if tl["lanes"]["screen"] != tl["lanes"]["voice"]:
        raise ValueError("Picture and voice must stay linked for reel cut review")
    clips = {c["id"]: c for c in data["clips"]}
    lane = sorted(tl["lanes"]["voice"], key=lambda i: i["at"])
    if not lane or len(lane) > 1000:
        raise ValueError("Keep at least one clip (maximum 1000)")
    previous = 0
    for i in lane:
        if i.get("clip") not in clips:
            raise ValueError("Unknown take")
        if any(not isinstance(i.get(k), (int, float)) or not math.isfinite(i[k]) for k in ("at", "src", "len")):
            raise ValueError("Invalid clip timing")
        if i["at"] != round(i["at"]) or i["len"] != round(i["len"]) or i["len"] <= 0:
            raise ValueError("Cuts must land on whole frames")
        if i["at"] != previous:
            raise ValueError("Reel cuts must stay contiguous. Keep Snap on to close holes")
        if i["src"] < 0 or i["src"] + i["len"] / FPS > clips[i["clip"]]["duration"] + 1 / FPS:
            raise ValueError("Clip extends outside its raw take")
        previous = i["at"] + i["len"]
    return tl


def ranges(lane):
    result = {}
    for i in lane:
        result.setdefault(i["clip"], []).append([i["src"], i["src"] + i["len"] / FPS])
    for cid, spans in result.items():
        merged = []
        for a, b in sorted(spans):
            if merged and a <= merged[-1][1] + 1e-6:
                merged[-1][1] = max(b, merged[-1][1])
            else:
                merged.append([a, b])
        result[cid] = merged
    return result


def subtract(a, b):
    out = []
    for s, e in a:
        for x, y in sorted(b):
            if y <= s or x >= e:
                continue
            if x > s:
                out.append([s, min(x, e)])
            s = max(s, y)
        if e - s > 0.5 / FPS:
            out.append([s, e])
    return out


def feedback(folder, tl, exported=None):
    rv = folder / "review"
    data, ai = read(rv / "project.json"), read(rv / "timeline.ai.json")
    clips = {c["id"]: c for c in data["clips"]}
    a, h = ranges(ai["lanes"]["voice"]), ranges(tl["lanes"]["voice"])
    def describe(cid, span):
        s, e = span
        words = [p["text"] for p in data["phrases"] if p["clip"] == cid and min(e, p["e"]) - max(s, p["s"]) > 0.02]
        boundaries = [("head", x) for x, y in a.get(cid, [])] + [("tail", y) for x, y in a.get(cid, [])]
        edge = next((side for side, t in boundaries if min(abs(s - t), abs(e - t)) < 0.5 / FPS), None)
        return {"take": cid, "source_from": round(raw_time(clips[cid], s), 6), "source_to": round(raw_time(clips[cid], e), 6),
                "review_from": round(s, 6), "review_to": round(e, 6),
                "seconds": round(e - s, 6), "edge": edge, "caption_context": words}
    removed = [describe(cid, r) for cid in a for r in subtract(a[cid], h.get(cid, []))]
    restored = [describe(cid, r) for cid in h for r in subtract(h[cid], a.get(cid, []))]
    result = {"name": data["name"], "date": datetime.now(timezone.utc).isoformat(), "learned": False,
              "state": "exported" if exported else "draft", "project": str(folder),
              "output": str(exported) if exported else None, "baseline_sha256": data["baseline_sha256"],
              "ai_timeline": ai, "reviewed_timeline": tl, "he_cut": removed, "he_restored": restored,
              "changed": tl != ai}
    write(rv / "feedback.json", result)
    lines = [f"# Cut feedback: {data['name']}", f"State: {result['state']}",
             "Source times refer to the original take. Context is caption text, not verified word alignment."]
    for kind, changes in (("REMOVED", removed), ("RESTORED", restored)):
        for c in changes:
            lines.append(f"{kind} {c['take']} {c['source_from']:.6f}–{c['source_to']:.6f}s "
                         f"({c['edge'] or 'internal'}): {' / '.join(c['caption_context'])}")
    if not result["changed"]:
        lines.append("The AI cut was accepted unchanged.")
    (rv / "review-diff.txt").write_text("\n".join(lines), encoding="utf-8")
    if exported:
        key = re.sub(r"[^\w-]+", "-", data["name"]).strip("-").lower()
        key += "-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        write(SKILL / "history" / f"{key}.json", result)
    return result


def export_cut(folder, tl):
    rv = folder / "review"
    data = read(rv / "project.json")
    validate(tl, data)
    clips = {c["id"]: c for c in data["clips"]}
    parts = []
    for i in sorted(tl["lanes"]["voice"], key=lambda i: i["at"]):
        parts += parts_for(clips[i["clip"]], i["src"], i["len"], data["snapshot"])
    original = Path(data["output"])
    output = original.with_name(original.stem + " - reviewed.mp4")
    if output.exists():
        output = output.with_name(output.stem + " - " + datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".mp4")
    encode_parts(parts, output)
    feedback(folder, tl, output)
    return output


class State:
    folder = None
    last_seen = time.time()
    lock = threading.Lock()
    export = {"state": "idle", "log": [], "output": None}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    def log_message(self, *args):
        pass

    def json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def file(self, path, kind):
        if not path.exists():
            return self.json({"error": "File not found"}, 404)
        size = path.stat().st_size
        start, end, partial = 0, size - 1, False
        m = re.fullmatch(r"bytes=(\d+)-(\d*)", self.headers.get("Range", ""))
        if m:
            start, end, partial = int(m[1]), min(int(m[2]), size - 1) if m[2] else size - 1, True
        if start > end:
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{size}")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        self.send_response(206 if partial else 200)
        if partial:
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(end - start + 1))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        try:
            with path.open("rb") as f:
                f.seek(start)
                left = end - start + 1
                while left > 0:
                    chunk = f.read(min(left, 262144))
                    if not chunk:
                        break
                    self.wfile.write(chunk)
                    left -= len(chunk)
        except (ConnectionError, OSError):
            pass

    def do_GET(self):
        State.last_seen = time.time()
        rv = State.folder / "review"
        path = unquote(self.path.split("?")[0])
        if path == "/":
            return self.file(SKILL / "review" / "index.html", "text/html; charset=utf-8")
        if path == "/api/ping":
            return self.json({"project": str(State.folder)})
        if path == "/api/export":
            return self.json(State.export)
        if path == "/api/project":
            data = read(rv / "project.json")
            return self.json({**data, "fps": FPS, "ai": read(rv / "timeline.ai.json"), "timeline": read(rv / "timeline.json"),
                              "peaks": read(rv / "peaks.json"), "slides": {}, "bubble": {"size": 0, "left": 0, "bottom": 0},
                              "out": {"width": 1080, "height": 1920}, "final": data["output"]})
        m = re.fullmatch(r"/media/([\w -]+)\.(screen|voice)\.mp4", path)
        if m:
            return self.file(rv / f"{m[1]}.mp4", "video/mp4")
        return self.json({"error": "Not found"}, 404)

    def do_POST(self):
        # Same-origin local requests only; media GETs remain normal browser range requests.
        origin = self.headers.get("Origin")
        if origin and origin != f"http://{self.headers.get('Host')}":
            return self.json({"error": "Origin mismatch"}, 403)
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length < 0 or length > 2_000_000:
                raise ValueError("Timeline too large")
            data = json.loads(self.rfile.read(length) or b"{}")
            rv = State.folder / "review"
            if self.path == "/api/save":
                with State.lock:
                    if State.export["state"] == "running":
                        return self.json({"error": "Wait for export to finish"}, 409)
                    validate(data, read(rv / "project.json"))
                    write(rv / "timeline.prev.json", read(rv / "timeline.json"))
                    write(rv / "timeline.json", data)
                    feedback(State.folder, data)
                return self.json({"ok": True})
            if self.path == "/api/export":
                with State.lock:
                    if State.export["state"] == "running":
                        return self.json({"error": "Export already running"}, 409)
                    tl = read(rv / "timeline.json")
                    validate(tl, read(rv / "project.json"))
                    State.export = {"state": "running", "log": ["Rendering your reviewed cut…"], "output": None}
                def render():
                    try:
                        output = export_cut(State.folder, tl)
                        State.export = {"state": "done", "log": ["Exported. Your source-time cut feedback was saved."], "output": str(output)}
                    except Exception as e:
                        message = (e.stderr.decode(errors="replace")[-3000:] if isinstance(e, subprocess.CalledProcessError) else str(e))
                        State.export = {"state": "failed", "log": [message], "output": None}
                threading.Thread(target=render, daemon=True).start()
                return self.json({"ok": True})
            return self.json({"error": "Not found"}, 404)
        except (ValueError, KeyError, TypeError) as e:
            return self.json({"error": str(e)}, 400)


def serve(folder, port=0, browser=True):
    rv = folder / "review"
    state_file = rv / "server.json"
    if state_file.exists():
        try:
            running = read(state_file)["port"]
            with urllib.request.urlopen(f"http://127.0.0.1:{running}/api/ping", timeout=1) as r:
                if json.loads(r.read())["project"] == str(folder):
                    if browser:
                        webbrowser.open(f"http://127.0.0.1:{running}/")
                    print(f"Cut editor: http://127.0.0.1:{running}/", flush=True)
                    return
        except (OSError, ValueError, KeyError):
            pass
    State.folder = folder
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    srv.daemon_threads = True
    port = srv.server_address[1]
    write(state_file, {"port": port})
    url = f"http://127.0.0.1:{port}/"
    print("Cut editor:", url, flush=True)
    if browser:
        webbrowser.open(url)
    def idle():
        while True:
            time.sleep(10)
            if time.time() - State.last_seen > 600 and State.export["state"] != "running":
                srv.shutdown()
                break
    threading.Thread(target=idle, daemon=True).start()
    try:
        srv.serve_forever()
    finally:
        state_file.unlink(missing_ok=True)
        srv.server_close()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("project")
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--port", type=int, default=0)
    args = ap.parse_args()
    path = Path(args.project).resolve()
    if args.prepare:
        prepare(path)
    else:
        folder = path if (path / "review" / "project.json").exists() else package(path)[0]
        if not (folder / "review" / "project.json").exists():
            folder = prepare(path)
        serve(folder, args.port, not args.no_browser)


if __name__ == "__main__":
    main()
