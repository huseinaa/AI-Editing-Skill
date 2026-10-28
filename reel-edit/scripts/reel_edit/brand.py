"""Your brand, read from brand.json at the skill's root. Every graphic, caption and cover uses it.

Missing keys fall back to the defaults below, so a half-filled brand.json still works.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULTS = {
    "name": "", "follow_line": "follow for more",
    "colors": {"ink": "#080B14", "panel": "#F7F8FA", "muted": "#5F6571", "primary": "#0051BD",
               "bright": "#2F6BFF", "highlight": "#FAFF00", "error": "#D92D20"},
    "fonts": {"latin": "Inter", "arabic": "Tajawal",
              "google_fonts_url": "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900"
                                  "&family=Tajawal:wght@500;700;800;900&display=block"},
    "logo": "assets/logo.png", "caption_language": "en", "browser": "msedge",
}


def load():
    path = os.path.join(ROOT, "brand.json")
    data = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {}
    out = {**DEFAULTS, **{k: v for k, v in data.items() if not k.startswith("_")}}
    for k in ("colors", "fonts"):
        out[k] = {**DEFAULTS[k], **data.get(k, {})}
    logo = out["logo_config"] = out.get("logo")
    out["logo"] = os.path.join(ROOT, logo) if logo and not os.path.isabs(logo) else logo
    if out["logo"] and not os.path.exists(out["logo"]):
        out["logo"] = None   # no logo file: covers are made without one
    return out


BRAND = load()
C, F = BRAND["colors"], BRAND["fonts"]
INK, PANEL, MUTED, BLUE, BRIGHT, YELLOW, RED = C["ink"], C["panel"], C["muted"], C["primary"], C["bright"], C["highlight"], C["error"]
LATIN, ARABIC, FONTS_URL = F["latin"], F["arabic"], F["google_fonts_url"]
LOGO, BROWSER, CAPTION_LANG, FOLLOW_LINE = BRAND["logo"], BRAND["browser"], BRAND["caption_language"], BRAND["follow_line"]
