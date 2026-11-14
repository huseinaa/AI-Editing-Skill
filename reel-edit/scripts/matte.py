"""Cut the speaker out of their background for cutout() spans: a matte per frame from RobustVideoMatting
(MobileNetV3, ONNX, runs on the CPU with onnxruntime).

    python matte.py <video> <first frame> <end frame> <out.mkv>

build.py calls make_matte() by itself for every cutout() visual, and reuses a matte already made. The model
(rvm_mobilenetv3_fp32.onnx, ~14 MB, GPL-3.0, github.com/PeterL1n/RobustVideoMatting) is downloaded once to
~/.cache/reel-edit/. The matte is made at half size and scaled back up in build.py.
"""
import os, subprocess, sys, urllib.request

MODEL_URL = "https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx"
MODEL = os.path.join(os.path.expanduser("~"), ".cache", "reel-edit", "rvm_mobilenetv3_fp32.onnx")
W, H = 1440, 2560     # the master canvas
MW, MH = 720, 1280    # matted at half size
WARM = 20             # frames read before the span so the model's memory has settled on the first frame


def session():
    if not os.path.exists(MODEL):
        os.makedirs(os.path.dirname(MODEL), exist_ok=True)
        print("downloading the matting model (~14 MB, once)")
        try:
            urllib.request.urlretrieve(MODEL_URL, MODEL + ".part")
            os.replace(MODEL + ".part", MODEL)
        except Exception as ex:
            raise SystemExit(f"cutout() needs the matting model and it could not be downloaded ({ex}).\n"
                             f"Download {MODEL_URL} to {MODEL}, or use another layout for that beat.")
    import onnxruntime as ort
    return ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])


def make_matte(video, n0, m0, out):
    """Frames n0 to m0 - 1 of the master (30 fps from 0, as build.py's [src] has them) -> a gray matte video."""
    if os.path.exists(out):
        return out
    import numpy as np
    a = max(0, n0 - WARM)
    vf = (f"setpts=PTS-STARTPTS,fps=30:start_time=0,select='between(n,{a},{m0 - 1})',"
          f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},scale={MW}:{MH}")
    reader = subprocess.Popen(["ffmpeg", "-v", "error", "-i", video, "-vf", vf, "-fps_mode", "passthrough",
                               "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    tmp = out + ".part.mkv"
    writer = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{MW}x{MH}",
                               "-r", "30", "-i", "-", "-c:v", "ffv1", "-pix_fmt", "gray", tmp], stdin=subprocess.PIPE)
    sess = session()
    rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
    ratio = np.array([0.4], np.float32)   # the model looks at the frame at 40% of 720x1280 for the coarse pass
    size, i, written = MW * MH * 3, a, 0
    while True:
        buf = reader.stdout.read(size)
        if len(buf) < size:
            break
        src = np.frombuffer(buf, np.uint8).reshape(MH, MW, 3).transpose(2, 0, 1)[None].astype(np.float32) / 255
        _, pha, *rec = sess.run(None, {"src": src, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3],
                                       "downsample_ratio": ratio})
        if i >= n0:
            writer.stdin.write((pha[0, 0] * 255).clip(0, 255).astype(np.uint8).tobytes())
            written += 1
        i += 1
    reader.wait()
    writer.stdin.close()
    writer.wait()
    if written < m0 - n0:
        raise SystemExit(f"matte: only {written} of {m0 - n0} frames from {n0 / 30:.2f}s")
    os.replace(tmp, out)
    print(f"matte: {written} frames from {n0 / 30:.2f}s")
    return out


if __name__ == "__main__":
    make_matte(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
