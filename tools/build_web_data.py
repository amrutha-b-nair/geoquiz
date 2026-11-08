"""Generate the web app's data from the original Python assets.

Reads python/geoquiz/csv/selected_names.csv and the GeoJSON files in
python/geojson files/, and writes:
  web/data/countries.json   - quiz questions, ordered by increasing difficulty
  web/img/countries/*.svg   - country silhouettes

How the silhouettes are drawn:
  * Parts that sit on the far side of the 180th meridian (Russia's Chukotka,
    the Aleutians) are moved back next to the rest of the country.
  * Parts far from the main landmass (Alaska, Hawaii, French Guiana, Réunion,
    the Canaries, ...) are drawn in boxes beside it instead of where they are
    on the map. All parts use the same scale, so sizes stay comparable, but
    the empty distance between them is not shown.
  * Each part is projected around its own latitude so its size is accurate.

Run from the repository root:  python3 tools/build_web_data.py
Requires numpy.
"""

import csv
import json
import math
import re
import unicodedata
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC_CSV = ROOT / "python/geoquiz/csv/selected_names.csv"
GEOJSON = ROOT / "python/geojson files"
OUT_JSON = ROOT / "web/data/countries.json"
OUT_IMG = ROOT / "web/img/countries"

# Higher-detail boundaries used by the original app for small island countries.
SPECIAL_FILES = {
    "MHL": "Marshall Islands.geojson",
    "MUS": "Mauritius.geojson",
    "SYC": "Seychelles.geojson",
    "MDV": "maldives.geojson",
    "VAT": "vatican.json",
}
NAME_FALLBACK = {"Kosovo": "Kosovo"}  # no ISO code in the CSV

# Display names that read better than the dataset's official names.
DISPLAY_NAMES = {"People's Republic of China": "China"}

# Fragments left over from scraping that should never count as an answer.
JUNK = {
    "", "a", "an", "and", "or", "of", "the", "the of", "former", "new", "east",
    "west", "german", "mainland", "confederation", "()", "or the of the",
}

# --- Layout tuning -----------------------------------------------------------
KM_PER_DEG = 111.32
CLUSTER_GAP_FRACTION = 0.15   # parts closer than this * sqrt(main area) belong together
CLUSTER_GAP_MIN_KM = 250      # ... or closer than this, whichever is larger
ABSORB_GROWTH = 1.3           # keep a far part in place if it grows the frame <= 30%
ABSORB_GROWTH_TOTAL = 1.6
MAX_INSETS = 5
MIN_INSET_AREA = 2e-4         # drop specks smaller than this fraction of the main part
VIEW = 1000                   # SVG units on the longest side
SIMPLIFY = 0.6                # SVG units
FILL = "#0b7a3b"
BOX = "#7d8b83"


# --- Text helpers ------------------------------------------------------------
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


# --- Loading -----------------------------------------------------------------
def polygons_of(geometry) -> list[list[np.ndarray]]:
    """A geometry as a list of polygons, each a list of (lon, lat) rings."""
    coords = geometry["coordinates"]
    polys = [coords] if geometry["type"] == "Polygon" else coords
    return [[np.asarray(ring, dtype=float)[:, :2] for ring in poly] for poly in polys]


def load_world():
    world = json.loads((GEOJSON / "world.geo.json").read_text(encoding="utf-8"))
    by_code, by_name = {}, {}
    for f in world["features"]:
        p = f["properties"]
        for key in ("adm0_a3", "iso_a3", "sov_a3"):
            if p.get(key) and p[key] != "-99":
                by_code.setdefault(p[key], f["geometry"])
        by_name[p["name"]] = f["geometry"]
    return by_code, by_name


def geometry_for(row, by_code, by_name):
    code = row["Alpha-3 code"]
    if code in SPECIAL_FILES:
        data = json.loads((GEOJSON / SPECIAL_FILES[code]).read_text(encoding="utf-8"))
        features = data.get("features", [data])
        polys = []
        for f in features:
            polys += polygons_of(f["geometry"])
        return polys
    geom = by_code.get(code) or by_name.get(NAME_FALLBACK.get(row["Country"], row["Country"]))
    if geom is None:
        raise KeyError(f"No geometry for {row['Country']} ({code})")
    return polygons_of(geom)


# --- Geometry ----------------------------------------------------------------
def ring_area(xy: np.ndarray) -> float:
    x, y = xy[:, 0], xy[:, 1]
    return abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1))) / 2


def local_xy(ring: np.ndarray, lat0: float) -> np.ndarray:
    """Equirectangular projection in km, correct around latitude lat0. y points down."""
    return np.column_stack((ring[:, 0] * math.cos(math.radians(lat0)) * KM_PER_DEG,
                            -ring[:, 1] * KM_PER_DEG))


def bbox(points: np.ndarray):
    return (*points.min(axis=0), *points.max(axis=0))


def bbox_union(a, b):
    return (min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3]))


def bbox_area(b):
    return max(b[2] - b[0], 1e-9) * max(b[3] - b[1], 1e-9)


def bbox_gap(a, b):
    dx = max(0.0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0.0, max(a[1], b[1]) - min(a[3], b[3]))
    return math.hypot(dx, dy)


def fix_antimeridian(polys):
    """Shift parts by 360° so they sit next to the largest part."""
    def center_lon(poly):
        lon = poly[0][:, 0]
        return (lon.min() + lon.max()) / 2

    areas = [ring_area(p[0]) for p in polys]
    main_lon = center_lon(polys[int(np.argmax(areas))])
    fixed = []
    for poly in polys:
        shift = round((main_lon - center_lon(poly)) / 360) * 360
        fixed.append([ring + (shift, 0) for ring in poly] if shift else poly)
    return fixed


def cluster(polys, lat0):
    """Group parts that are close to each other (single linkage)."""
    outer = [local_xy(p[0], lat0) for p in polys]
    areas = np.array([ring_area(o) for o in outer])
    boxes = [bbox(o) for o in outer]
    samples = [o[:: max(1, len(o) // 80)] for o in outer]
    main = int(np.argmax(areas))
    gap = max(CLUSTER_GAP_FRACTION * math.sqrt(areas[main]), CLUSTER_GAP_MIN_KM)

    parent = list(range(len(polys)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(len(polys)):
        for j in range(i + 1, len(polys)):
            if find(i) == find(j) or bbox_gap(boxes[i], boxes[j]) > gap:
                continue
            d = np.sqrt(((samples[i][:, None, :] - samples[j][None, :, :]) ** 2).sum(-1)).min()
            if d <= gap:
                parent[find(i)] = find(j)

    groups = {}
    for i in range(len(polys)):
        groups.setdefault(find(i), []).append(i)
    clusters = []
    for members in groups.values():
        b = boxes[members[0]]
        for m in members[1:]:
            b = bbox_union(b, boxes[m])
        clusters.append({"members": members, "area": areas[members].sum(), "box": b})
    main_cluster = next(c for c in clusters if main in c["members"])
    return main_cluster, [c for c in clusters if c is not main_cluster]


def split_main_and_insets(polys):
    polys = fix_antimeridian(polys)
    all_lat = np.concatenate([p[0][:, 1] for p in polys])
    main_poly = max(polys, key=lambda p: ring_area(p[0]))
    lat0 = (main_poly[0][:, 1].min() + main_poly[0][:, 1].max()) / 2
    if len(polys) == 1:
        return [polys], 0
    main, others = cluster(polys, lat0)

    # Keep nearby or in-frame parts in place when they barely enlarge the frame.
    start = bbox_area(main["box"])
    others.sort(key=lambda c: bbox_gap(main["box"], c["box"]))
    insets = []
    for c in others:
        grown = bbox_union(main["box"], c["box"])
        if bbox_area(grown) <= ABSORB_GROWTH * bbox_area(main["box"]) and bbox_area(grown) <= ABSORB_GROWTH_TOTAL * start:
            main["members"] += c["members"]
            main["box"] = grown
            main["area"] += c["area"]
        else:
            insets.append(c)

    insets = [c for c in insets if c["area"] >= MIN_INSET_AREA * main["area"]]
    insets.sort(key=lambda c: -c["area"])
    insets = insets[:MAX_INSETS]
    parts = [[polys[i] for i in main["members"]]] + [[polys[i] for i in c["members"]] for c in insets]
    return parts, float(all_lat.mean())


def project_part(part):
    """Project a part around its own latitude; returns rings of xy in km."""
    lats = np.concatenate([p[0][:, 1] for p in part])
    lat0 = (lats.min() + lats.max()) / 2
    return [[local_xy(ring, lat0) for ring in poly] for poly in part]


def simplify(points: np.ndarray, tol: float) -> np.ndarray:
    """Radial-distance pass followed by Douglas-Peucker."""
    if len(points) <= 4:
        return points
    keep = [0]
    for i in range(1, len(points)):
        if np.hypot(*(points[i] - points[keep[-1]])) >= tol:
            keep.append(i)
    pts = points[keep]
    if len(pts) <= 4:
        return pts
    mask = np.zeros(len(pts), dtype=bool)
    mask[0] = mask[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        seg = pts[b] - pts[a]
        length = np.hypot(*seg)
        rel = pts[a + 1:b] - pts[a]
        if length == 0:
            dist = np.hypot(rel[:, 0], rel[:, 1])
        else:
            dist = np.abs(seg[0] * rel[:, 1] - seg[1] * rel[:, 0]) / length
        k = int(np.argmax(dist))
        if dist[k] > tol:
            idx = a + 1 + k
            mask[idx] = True
            stack += [(a, idx), (idx, b)]
    return pts[mask]


def layout(parts_xy):
    """Place the main part and inset boxes; returns placements and total size (km)."""
    boxes = [bbox(np.concatenate([poly[0] for poly in part])) for part in parts_xy]
    main_box = boxes[0]
    mw, mh = main_box[2] - main_box[0], main_box[3] - main_box[1]
    size = max(mw, mh)
    pad, gap, min_box = 0.05 * size, 0.06 * size, 0.1 * size
    placements = [(-main_box[0], -main_box[1], None)]
    if len(parts_xy) == 1:
        return placements, mw, mh

    below = mw >= mh
    limit = max(mw if below else mh, 1)
    cursor_main = 0.0                       # along the row / column
    cursor_cross = (mh if below else mw) + gap
    line_thickness = 0.0
    total_w, total_h = mw, mh
    for b in boxes[1:]:
        w, h = b[2] - b[0], b[3] - b[1]
        bw, bh = max(w + 2 * pad, min_box), max(h + 2 * pad, min_box)
        along, across = (bw, bh) if below else (bh, bw)
        if cursor_main > 0 and cursor_main + along > limit:
            cursor_cross += line_thickness + gap
            cursor_main, line_thickness = 0.0, 0.0
        bx, by = (cursor_main, cursor_cross) if below else (cursor_cross, cursor_main)
        # centre the part inside its box
        dx = bx + (bw - w) / 2 - b[0]
        dy = by + (bh - h) / 2 - b[1]
        placements.append((dx, dy, (bx, by, bw, bh)))
        cursor_main += along + gap
        line_thickness = max(line_thickness, across)
        total_w, total_h = max(total_w, bx + bw), max(total_h, by + bh)
    return placements, total_w, total_h


def fmt(v: float) -> str:
    s = f"{v:.1f}"
    return s[:-2] if s.endswith(".0") else s


def render_svg(polys) -> str:
    parts, _ = split_main_and_insets(polys)
    parts_xy = [project_part(p) for p in parts]
    placements, total_w, total_h = layout(parts_xy)
    margin = 0.02 * max(total_w, total_h)
    scale = VIEW / (max(total_w, total_h) + 2 * margin)
    width, height = (total_w + 2 * margin) * scale, (total_h + 2 * margin) * scale

    def to_svg(xy, dx, dy):
        return (xy + (dx + margin, dy + margin)) * scale

    path, rects = [], []
    for part, (dx, dy, box) in zip(parts_xy, placements):
        for poly in part:
            for ring in poly:
                pts = simplify(to_svg(ring, dx, dy), SIMPLIFY)
                if len(pts) < 3:
                    pts = to_svg(ring, dx, dy)
                path.append("M" + "L".join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + "Z")
        if box:
            bx, by, bw, bh = box
            x, y = (bx + margin) * scale, (by + margin) * scale
            rects.append(
                f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(bw * scale)}" height="{fmt(bh * scale)}" '
                f'rx="{fmt(0.02 * VIEW)}"/>'
            )
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(width)} {fmt(height)}" '
        f'width="{round(width)}" height="{round(height)}">',
        f'<path fill="{FILL}" fill-rule="evenodd" stroke="{FILL}" stroke-width="1.5" '
        f'stroke-linejoin="round" vector-effect="non-scaling-stroke" d="{"".join(path)}"/>',
    ]
    if rects:
        svg.append(f'<g fill="none" stroke="{BOX}" stroke-width="1.5" stroke-dasharray="6 4" '
                   f'vector-effect="non-scaling-stroke">{"".join(rects)}</g>')
    svg.append("</svg>")
    return "".join(svg)


# --- Main --------------------------------------------------------------------
def main() -> None:
    OUT_IMG.mkdir(parents=True, exist_ok=True)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    for old in OUT_IMG.iterdir():
        old.unlink()
    by_code, by_name = load_world()
    countries = []
    with SRC_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name = row["Country"]
            slug = slugify(name)
            svg = render_svg(geometry_for(row, by_code, by_name))
            (OUT_IMG / f"{slug}.svg").write_text(svg, encoding="utf-8")
            countries.append({
                "id": slug,
                "name": DISPLAY_NAMES.get(name, name),
                "aliases": clean_aliases(name, row["Other names"]),
                "image": f"img/countries/{slug}.svg",
            })
    OUT_JSON.write_text(json.dumps(countries, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {len(countries)} countries to {OUT_JSON.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
