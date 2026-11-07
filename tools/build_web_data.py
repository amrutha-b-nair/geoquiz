"""Generate the web app's data from the original Python assets.

Reads python/geoquiz/csv/selected_names.csv and python/geoquiz/images_noaxis/*.png
and writes:
  web/data/countries.json   - quiz questions, ordered by increasing difficulty
  web/img/countries/*.webp  - small transparent silhouettes

Run from the repository root:  python3 tools/build_web_data.py
Requires Pillow.
"""

import csv
import json
import re
import unicodedata
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC_CSV = ROOT / "python/geoquiz/csv/selected_names.csv"
SRC_IMG = ROOT / "python/geoquiz/images_noaxis"
OUT_JSON = ROOT / "web/data/countries.json"
OUT_IMG = ROOT / "web/img/countries"
MAX_SIZE = 640

# Display names that read better than the dataset's official names.
DISPLAY_NAMES = {"People's Republic of China": "China"}

# Fragments left over from scraping that should never count as an answer.
JUNK = {
    "", "a", "an", "and", "or", "of", "the", "the of", "former", "new", "east",
    "west", "german", "mainland", "confederation", "()", "or the of the",
}


def slugify(name: str) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")


def clean_aliases(country: str, raw: str) -> list[str]:
    seen, out = set(), []
    for alias in [country, DISPLAY_NAMES.get(country, country), *raw.split(",")]:
        alias = re.sub(r"[()]", "", alias).strip()
        alias = re.sub(r"\s+(or|and|former)$", "", alias)
        key = alias.lower()
        if key in JUNK or len(key) < 2 or key in seen:
            continue
        seen.add(key)
        out.append(alias)
    return out


def convert_image(src: Path, dest: Path) -> None:
    img = Image.open(src).convert("RGBA")
    # The originals are green shapes on white: turn white into transparency.
    r, g, b, a = img.split()
    lightness = Image.merge("RGB", (r, g, b)).convert("L")
    alpha = lightness.point(lambda v: 0 if v > 245 else 255)
    img.putalpha(alpha)
    bbox = img.getbbox()
    if bbox:
        img = img.crop(bbox)
    img.thumbnail((MAX_SIZE, MAX_SIZE), Image.LANCZOS)
    img.save(dest, "WEBP", quality=85, method=6)


def main() -> None:
    OUT_IMG.mkdir(parents=True, exist_ok=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    countries = []
    with SRC_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["Country"]
            slug = slugify(name)
            convert_image(SRC_IMG / row["Image_path"], OUT_IMG / f"{slug}.webp")
            countries.append({
                "id": slug,
                "name": DISPLAY_NAMES.get(name, name),
                "aliases": clean_aliases(name, row["Other names"]),
                "image": f"img/countries/{slug}.webp",
            })
    OUT_JSON.write_text(json.dumps(countries, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {len(countries)} countries to {OUT_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
