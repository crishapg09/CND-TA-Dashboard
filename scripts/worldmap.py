#!/usr/bin/env python3
"""Robinson-projection world map for the "Where support flows" section.

Renders an inline SVG: light country silhouettes (Natural Earth 110m), the
supported country offices highlighted and dotted, thin arcs from each TA-lead
duty station to the countries it supports, and duty-station bubbles sized by
requests led. Points and the base map share one projection so they register.

No runtime/network dependency: the base map is committed at
design/assets/ne_110m_admin_0_countries.geojson and projected at build time.
"""
import json, os, math, re

GEO = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   'design', 'assets', 'ne_110m_admin_0_countries.geojson')

# ---- Robinson projection ----------------------------------------------------
_ROB = [(0, 1.0000, 0.0000), (5, 0.9986, 0.0620), (10, 0.9954, 0.1240),
        (15, 0.9900, 0.1860), (20, 0.9822, 0.2480), (25, 0.9730, 0.3100),
        (30, 0.9600, 0.3720), (35, 0.9427, 0.4340), (40, 0.9216, 0.4958),
        (45, 0.8962, 0.5571), (50, 0.8679, 0.6176), (55, 0.8350, 0.6769),
        (60, 0.7986, 0.7346), (65, 0.7597, 0.7903), (70, 0.7186, 0.8435),
        (75, 0.6732, 0.8936), (80, 0.6213, 0.9394), (85, 0.5722, 0.9761),
        (90, 0.5322, 1.0000)]
_S, _CX, _PAD = 182.0, 500.0, 30.0
_MAXY = 1.3523
_CY = _PAD + _MAXY * _S
HEIGHT = 2 * _MAXY * _S + 2 * _PAD
WIDTH = 1000.0


def _interp(la):
    la = min(la, 90.0)
    for i in range(len(_ROB) - 1):
        a, b = _ROB[i], _ROB[i + 1]
        if a[0] <= la <= b[0]:
            t = (la - a[0]) / (b[0] - a[0])
            return a[1] + t * (b[1] - a[1]), a[2] + t * (b[2] - a[2])
    return _ROB[-1][1], _ROB[-1][2]


def project(lon, lat):
    X, Y = _interp(abs(lat))
    x = 0.8487 * X * math.radians(lon)
    y = 1.3523 * Y * (1 if lat >= 0 else -1)
    return _CX + x * _S, _CY - y * _S


# ---- name matching ----------------------------------------------------------
def _norm(s):
    s = (s or '').lower()
    s = re.sub(r'\(.*?\)', ' ', s)
    s = re.sub(r"[.,'\-]", ' ', s)
    s = re.sub(r'\b(the|of|and|rep|republic|dem|democratic|state|united|people s|peoples|island|islands|s)\b', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

_ALIAS = {
    'DRC': 'Dem. Rep. Congo', "Lao People's Dem Rep.": 'Laos', 'United Rep. of Tanzania': 'Tanzania',
    'Syrian Arab Republic': 'Syria', 'State of Palestine': 'Palestine', 'Republic of Moldova': 'Moldova',
    'Viet Nam': 'Vietnam', 'Iran (Islamic Republic of)': 'Iran', 'Bolivia (Plurinational State of)': 'Bolivia',
    'Venezuela (Bolivarian Republic of)': 'Venezuela', 'Turkiye': 'Turkey', 'Cabo Verde': 'Cape Verde',
    'North Macedonia': 'Macedonia', "Cote d'Ivoire": 'Ivory Coast', "Cote D'Ivoire": 'Ivory Coast',
    "Democratic People's Republic of Korea": 'North Korea', 'Republic of Korea': 'South Korea',
    'Solomon, Republic of Marshall Islands': 'Solomon Is.', 'Pacific': 'Fiji',
}
# small nations the 110m base map omits — placed by hand so they still get a dot
_MANUAL = {'Barbados': (-59.5, 13.1), 'Comoros': (43.3, -11.6), 'Eswatini': (31.5, -26.5)}

_FEATMAP = None   # norm name -> centroid (lon, lat)
_PATHS = None     # list of (norm_names_set, svg_path_d)


def _largest_ring(geom):
    rings = []
    if geom['type'] == 'Polygon':
        rings = geom['coordinates']
    elif geom['type'] == 'MultiPolygon':
        for poly in geom['coordinates']:
            rings.extend(poly)
    return max(rings, key=len) if rings else []


def _load():
    global _FEATMAP, _PATHS
    if _FEATMAP is not None:
        return
    gj = json.load(open(GEO, encoding='utf-8'))
    _FEATMAP, _PATHS = {}, []
    for f in gj['features']:
        p = f['properties']
        if (p.get('NAME') or '') == 'Antarctica':
            continue
        names = set()
        for key in ('NAME', 'ADMIN', 'NAME_LONG', 'SOVEREIGNT', 'BRK_NAME', 'FORMAL_EN', 'NAME_SORT'):
            v = p.get(key)
            if v:
                names.add(_norm(v))
        ring = _largest_ring(f['geometry'])
        if ring:
            clon = sum(pt[0] for pt in ring) / len(ring)
            clat = sum(pt[1] for pt in ring) / len(ring)
            for nm in names:
                _FEATMAP.setdefault(nm, (clon, clat))
        # build projected path (all rings)
        segs = []
        geom = f['geometry']
        if geom['type'] == 'Polygon':
            rings = geom['coordinates']
        else:
            rings = [r for poly in geom['coordinates'] for r in poly]
        for r in rings:
            pts = [project(lon, lat) for lon, lat in r]
            if len(pts) < 2:
                continue
            segs.append('M' + ' L'.join(f'{x:.1f} {y:.1f}' for x, y in pts) + ' Z')
        if segs:
            _PATHS.append((names, ' '.join(segs)))


def resolve(office):
    """office display name -> (lon, lat) centroid, or None."""
    _load()
    if office in _MANUAL:
        return _MANUAL[office]
    key = _norm(_ALIAS.get(office, office))
    if key in _FEATMAP:
        return _FEATMAP[key]
    for nk, c in _FEATMAP.items():
        if key and len(key) > 3 and (key in nk or nk in key):
            return c
    return None


def build_world_map(stations, office_counts, links, office_totals=None, suffix='', floating_tip=True):
    """
    stations: list of {name, lon, lat, count, color, anchor, key, tip}
    office_counts: {office_display_name: n}  (destination dots + highlight)
    links: {(station_name, office_display_name): weight}
    office_totals: {office: total requests received} for the dot tooltips
                   (falls back to office_counts when omitted)
    suffix: appended to per-station tooltip element ids so several maps (e.g. one
            per filter state) can coexist without id collisions.
    floating_tip: emit the shared position:fixed #maptip element (only one is
            needed on the page — pass False for extra copies of the map).
    """
    totals = office_totals or office_counts
    _load()
    highlight = set()
    for off in office_counts:
        c = resolve(off)
        if not c:
            continue
        key = _norm(_ALIAS.get(off, off))
        highlight.add(key)

    # base countries
    base = []
    for names, d in _PATHS:
        hit = any(n in highlight for n in names)
        fill = '#C6D8E8' if hit else '#E6EAF0'
        base.append(f'<path d="{d}" fill="{fill}" stroke="#FFFFFF" stroke-width="0.4"/>')

    # arcs (tagged by hub so a click can highlight them)
    arcs = []
    stn = {s['name']: s for s in stations}
    office_hubs = {}   # office -> set of hub keys that serve it
    for (sname, off), w in sorted(links.items(), key=lambda kv: -kv[1]):
        s = stn.get(sname)
        c = resolve(off)
        if not s or not c:
            continue
        key = s.get('key', '')
        office_hubs.setdefault(off, set()).add(key)
        x0, y0 = project(s['lon'], s['lat'])
        x1, y1 = project(c[0], c[1])
        dist = math.hypot(x1 - x0, y1 - y0)
        cxp, cyp = (x0 + x1) / 2, min(y0, y1) - dist * 0.22 - 8
        wdt = 0.5 + min(w, 12) * 0.16
        arcs.append(f'<path class="wmarc" data-hub="{key}" data-op="0.28" data-w="{wdt:.2f}" '
                    f'd="M{x0:.1f} {y0:.1f} Q{cxp:.1f} {cyp:.1f} {x1:.1f} {y1:.1f}" '
                    f'stroke="{s["color"]}" stroke-width="{wdt:.2f}" fill="none" opacity="0.28"/>')

    # destination dots (tagged with the hubs that serve them) + hover hit-areas
    dots, dothits = [], []
    for off in office_counts:
        c = resolve(off)
        if not c:
            continue
        x, y = project(c[0], c[1])
        hubs = ' '.join(sorted(office_hubs.get(off, ())))
        dots.append(f'<circle class="wmdot" data-hubs="{hubs}" cx="{x:.1f}" cy="{y:.1f}" r="2.3" fill="#6C7B8C" opacity="0.9"/>')
        dothits.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="6" fill="#000" opacity="0" '
                       f'style="pointer-events:all" data-name="{_attr(off)}" data-n="{totals.get(off, 0)}" '
                       f'onmouseenter="dotTip(evt,this)" onmousemove="mapTipMove(evt)" onmouseleave="mapTipHide()"/>')

    # duty-station bubbles (hover + click live on the visible bubble itself) + labels
    bubbles, labels, tips = [], [], []
    for s in sorted(stations, key=lambda s: -s['count']):
        x, y = project(s['lon'], s['lat'])
        r = 6 + math.sqrt(s['count']) * 2.15
        col = s['color']
        key = s.get('key', '')
        handlers = (f' style="cursor:pointer" onmouseenter="mapTip(evt,\'{key}{suffix}\')" onmousemove="mapTipMove(evt)" '
                    f'onmouseleave="mapTipHide()" onclick="selectHub(evt,\'{key}\')"') if key else ''
        bubbles.append(f'<g class="wmbub" data-hub="{key}"{handlers}>'
                       f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r+7:.1f}" fill="{col}" opacity="0.13"/>'
                       f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{col}" opacity="0.88" stroke="#fff" stroke-width="2"/>'
                       f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.4" fill="#fff"/></g>')
        anchor = s.get('anchor', 'top')
        if anchor == 'right':
            lx, ly, ta = x + r + 8, y + 4, 'start'
        elif anchor == 'left':
            lx, ly, ta = x - r - 8, y + 4, 'end'
        else:
            lx, ly, ta = x, y - r - 8, 'middle'
        labels.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{ta}" class="wmlabel" '
                      f'style="pointer-events:none">{_esc(s["name"])} <tspan class="wmcount">{s["count"]}</tspan></text>')
        if key and s.get('tip'):
            tips.append(f'<div id="tip-{key}{suffix}" class="tiptpl" style="display:none">{s["tip"]}</div>')

    # Layer order (bottom -> top): map, arcs, visible dots, dot hover-targets,
    # interactive bubbles (topmost so a click on the disc always selects the
    # station), then labels (non-interactive, drawn last so text stays legible).
    svg = (f'<div class="wmwrap"><svg viewBox="0 0 {WIDTH:.0f} {HEIGHT:.0f}" class="wmsvg" '
           f'preserveAspectRatio="xMidYMid meet" onclick="clearHub()">'
           + ''.join(base) + ''.join(arcs) + ''.join(dots) + ''.join(dothits) + ''.join(bubbles) + ''.join(labels)
           + '</svg></div>')
    return svg + ''.join(tips) + ('<div id="maptip" class="maptip"></div>' if floating_tip else '')


def _esc(x):
    return (str(x).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def _attr(x):
    return _esc(x).replace('"', '&quot;')
