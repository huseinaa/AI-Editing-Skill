"""Make the tone-match EQ for a line recorded on the phone mic, so it sits closer to his mic takes.

    python clean_eq.py <workdir> --phone "<take>:26.40-29.90" --mic "<take>:0.40-7.20" --mic "<take>:0.50-7.20"

Compares the two average spectra in 1/3-octave bands, keeps only the tilt (loudness is set later),
smooths it, applies half of it (a natural move toward the mic, not a copy) and writes
<workdir>/clean-eq.txt, which assemble.py's `clean` line picks up.
"""
import argparse, os, subprocess
import numpy as np

SR = 48000
BANDS = [63, 80, 100, 125, 160, 200, 250, 315, 400, 500, 630, 800, 1000, 1250, 1600, 2000, 2500, 3150, 4000,
         5000, 6300, 8000, 10000, 12500]


def load(spec):
    path, span = spec.rsplit(":", 1)
    s, e = (float(x) for x in span.split("-"))
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(s), "-t", str(e - s), "-i", path, "-ac", "1", "-ar", str(SR),
                          "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def bands(x, n=4096):
    win = np.hanning(n)
    p = np.mean([np.abs(np.fft.rfft(x[i:i + n] * win)) ** 2 for i in range(0, len(x) - n, n // 2)], axis=0)
    f = np.fft.rfftfreq(n, 1 / SR)
    return np.array([10 * np.log10(p[(f >= c / 2 ** (1 / 6)) & (f < c * 2 ** (1 / 6))].mean() + 1e-20) for c in BANDS])


ap = argparse.ArgumentParser()
ap.add_argument("workdir")
ap.add_argument("--phone", required=True)
ap.add_argument("--mic", action="append", required=True)
a = ap.parse_args()

lp, lm = bands(load(a.phone)), bands(np.concatenate([load(m) for m in a.mic]))
g = (lm - lm.mean()) - (lp - lp.mean())
g = np.convolve(np.pad(g, 1, mode="edge"), [0.25, 0.5, 0.25], mode="valid")
g = np.clip(g * 0.5, -5, 5)
entries = ";".join(f"entry({b},{v:.1f})" for b, v in zip(BANDS, g))
open(os.path.join(a.workdir, "clean-eq.txt"), "w").write(f"firequalizer=gain_entry='{entries}'")
print(" ".join(f"{b}:{v:+.1f}" for b, v in zip(BANDS, g)))
