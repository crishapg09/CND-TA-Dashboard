#!/usr/bin/env python3
"""Build the pre-projected geometry the Power BI "Where support flows" measure needs.

Outputs three files the report imports as tables:
  powerbi/Stations.csv  — 6 duty stations, projected to pixel space (PxX,PxY)
  powerbi/Geo.csv       — every supported country office -> pixel centroid
  powerbi/MapBase.csv   — one row: the static world silhouette as inline SVG <path>s

All three share ONE projection (worldmap.project, Robinson) and the same viewBox
(0 0 WIDTH HEIGHT), so the DAX measure can place bubbles/arcs/dots by simple
arithmetic on these pixel coordinates — no projection maths at query time.
"""
import csv, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import worldmap as wm

DATA = os.path.join(os.path.dirname(HERE), 'app', 'src', 'data')
cases = json.load(open(f'{DATA}/cases.json'))

# same hubs/colours as the web dashboard
HUB_META = {
    'Nairobi':  (36.82, -1.29, 'top',   '#0B6FA4'),
    'Bangkok':  (100.50, 13.75, 'right', '#2E7D5B'),
    'Amman':    (35.93, 31.95, 'top',   '#7A4FB0'),
    'Brussels': (4.35, 50.85, 'top',    '#1CABE2'),
    'Panama':   (-79.52, 8.98, 'left',  '#C87A2E'),
    'New York': (-74.01, 40.71, 'left', '#43586B'),
}

def slug(x):
    import re
    return re.sub(r'[^a-z0-9]+', '', x.lower()) or 'x'

# ---- Stations.csv ----
with open(f'{HERE}/Stations.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Name', 'Key', 'PxX', 'PxY', 'Color', 'Anchor'])
    for name, (lon, lat, anchor, col) in HUB_META.items():
        x, y = wm.project(lon, lat)
        w.writerow([name, slug(name), round(x, 1), round(y, 1), col, anchor])

# ---- Geo.csv (offices present in the data -> pixel centroid) ----
offices = sorted({c['office'] for c in cases if c['status'] != 'Discontinued' and c['office']})
rows, unresolved = [], []
for off in offices:
    c = wm.resolve(off)
    if not c:
        unresolved.append(off)
        continue
    x, y = wm.project(c[0], c[1])
    rows.append([off, round(x, 1), round(y, 1)])
with open(f'{HERE}/Geo.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Office', 'PxX', 'PxY'])
    w.writerows(rows)

# ---- MapBase.csv (static world silhouette, simplified) ----
# Re-project the Natural Earth geometry to integer pixels and drop redundant
# points / tiny islands so the string stays small enough to embed in a measure.
wm._load()
gj = json.load(open(wm.GEO, encoding='utf-8'))

def ring_to_pts(ring):
    pts = []
    for lon, lat in ring:
        x, y = wm.project(lon, lat)
        p = (int(round(x)), int(round(y)))
        if not pts or pts[-1] != p:      # drop consecutive duplicates after rounding
            pts.append(p)
    return pts

segs = []
for feat in gj['features']:
    if (feat['properties'].get('NAME') or '') == 'Antarctica':
        continue
    geom = feat['geometry']
    rings = geom['coordinates'] if geom['type'] == 'Polygon' else \
        [r for poly in geom['coordinates'] for r in poly] if geom['type'] == 'MultiPolygon' else []
    for ring in rings:
        pts = ring_to_pts(ring)
        if len(pts) > 40:               # decimate large rings
            pts = pts[::2]
        if len(pts) < 4:
            continue
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        if (max(xs) - min(xs)) * (max(ys) - min(ys)) < 8:   # drop specks
            continue
        segs.append('M' + ' '.join(f'{x} {y}' for x, y in pts) + 'Z')

base_path = f'<path d="{"".join(segs)}" fill="#E6EAF0" stroke="#FFFFFF" stroke-width="0.4"/>'
with open(f'{HERE}/MapBase.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['Id', 'SVG'])
    w.writerow([1, base_path])

print(f'WIDTH={wm.WIDTH:.0f}  HEIGHT={wm.HEIGHT:.0f}')
print(f'Stations: {len(HUB_META)}  Geo: {len(rows)} (unresolved: {unresolved})')
print(f'MapBase: {len(base_path):,} chars, {len(segs)} rings')
