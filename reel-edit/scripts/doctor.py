"""Check everything /reel-edit needs is installed. Run it first on a new machine.

    python doctor.py
"""
import importlib.util, json, os, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
ok = True


def check(name, cond, fix, required=True):
    global ok
    print(("OK   " if cond else ("MISS " if required else "note ")) + name + ("" if cond else f"   -> {fix}"))
    if required:
        ok &= bool(cond)


check("ffmpeg", shutil.which("ffmpeg"), "Windows: winget install Gyan.FFmpeg   Mac: brew install ffmpeg")
check("ffprobe", shutil.which("ffprobe"), "comes with ffmpeg")
for mod, pkg in [("faster_whisper", "faster-whisper"), ("playwright", "playwright"), ("PIL", "pillow"), ("numpy", "numpy")]:
    check(f"python: {pkg}", importlib.util.find_spec(mod), f"pip install {pkg}")
check("python: truststore (only behind a network that re-signs HTTPS)", importlib.util.find_spec("truststore"),
      "pip install truststore", required=False)
check("python: yt-dlp (only to download reference reels from links)", importlib.util.find_spec("yt_dlp"),
      "pip install yt-dlp", required=False)

model = os.path.expanduser("~/.cache/faster-whisper-small/model.bin")
check("Whisper small model (~/.cache/faster-whisper-small)", os.path.exists(model),
      "download https://huggingface.co/Systran/faster-whisper-small (all files) into ~/.cache/faster-whisper-small")

brand_path = os.path.join(ROOT, "brand.json")
check("brand.json", os.path.exists(brand_path), "copy it from the repo, then put your colors, fonts and logo in it")
if os.path.exists(brand_path):
    from reel_edit.brand import BRAND, LOGO, BROWSER
    try:
        json.load(open(brand_path, encoding="utf-8"))
        check("brand.json is valid JSON", True, "")
    except ValueError as e:
        check("brand.json is valid JSON", False, str(e))
    local_path = os.path.join(ROOT, "local", "brand.json")
    if os.path.exists(local_path):
        try:
            json.load(open(local_path, encoding="utf-8"))
            check("local/brand.json (your values, laid on top) is valid JSON", True, "")
        except ValueError as e:
            check("local/brand.json is valid JSON", False, str(e))
    else:
        check("local/brand.json (your own brand, never committed)", False,
              "optional: put your colors, fonts, logo and follow line in local/brand.json", required=False)
    check(f"logo for covers ({BRAND.get('logo_config') or 'none set'})", LOGO, "put a PNG at the path in brand.json, or covers are made with no logo",
          required=False)
    paths = {"msedge": [r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"],
             "chrome": [r"C:\Program Files\Google\Chrome\Application\chrome.exe", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]}
    found = any(os.path.exists(p) for p in paths.get(BROWSER, [])) or shutil.which(BROWSER)
    check(f"browser for rendering graphics ({BROWSER})", found,
          'install Microsoft Edge or Google Chrome, and set "browser" in brand.json to "msedge" or "chrome"')

for name in ("pop", "whoosh"):
    found = any(os.path.exists(os.path.join(ROOT, d, "sfx", f"{name}{ext}")) for d in ("local", "assets") for ext in (".wav", ".mp3", ".m4a"))
    check(f"sound effect {name} (local/sfx or assets/sfx)", found, "optional, see assets/sfx/SOURCE.md", required=False)
print("\nready" if ok else "\nfix the MISS lines, then run this again")
