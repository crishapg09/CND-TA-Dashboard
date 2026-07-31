#!/usr/bin/env python3
"""Generate a self-contained HTML prototype of the nutrition TA dashboard for
iterating the look in Claude Design.

Faithful to the live React dashboard (app/src/lib/dashboard.ts) — same KPIs,
Performance sections and three-stage Data Quality Review — but rescoped to one
team: thematic area (from the staff-roster join) replaces practice AND region,
regions are dropped entirely, and a new "Where support flows" section links
each request's TA-lead duty station to the supported country office.

Everything is rendered as visible stacked sections (no hidden tabs) so the
whole dashboard can be reviewed and edited at once. Data-driven from the
committed cases.json + staff.json."""
import json, os, re, math, html, datetime
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(os.path.dirname(HERE), 'app', 'src', 'data')
OUT = os.path.join(os.path.dirname(HERE), 'design')
os.makedirs(OUT, exist_ok=True)

cases = json.load(open(f'{ROOT}/cases.json'))
staff = json.load(open(f'{ROOT}/staff.json'))
TODAY = json.load(open(f'{ROOT}/today.json'))
by_name = {s['name']: s for s in staff}
EPOCH = datetime.datetime(1899, 12, 30)

# "as of" date and the 30-day window, derived from the data
TODAY_STR = (EPOCH + datetime.timedelta(days=TODAY)).strftime('%-d %b %Y')      # e.g. 29 Jul 2026
WIN_STR = (EPOCH + datetime.timedelta(days=TODAY - 30)).strftime('%-d %b %Y')   # e.g. 29 Jun 2026
WIN_SHORT = (EPOCH + datetime.timedelta(days=TODAY - 30)).strftime('%-d %b')    # e.g. 29 Jun
RECV_BODY = f'new TA requests opened between {WIN_SHORT} and {TODAY_STR}.'
OVERDUE_FOOTER = (f'Days over = today ({TODAY_STR}) − the request’s Expected Completion Date, '
                  'counting only active requests (below 100%) whose target date has already passed.')

STATUS_ORDER = ['0%', '25%', '50%', '75%', '100%', 'Unassigned']
SC = {'0%': '#D6E0E8', '25%': '#9CC6E0', '50%': '#5BA3D0', '75%': '#2C7DB5',
      '100%': '#0B5A8A', 'Discontinued': '#9AA7B2', 'Unassigned': '#E0A21E'}
DARK = {'50%', '75%', '100%', 'Discontinued'}

for c in cases:
    s = by_name.get(c['lead'])
    c['area'] = (s['area'] if s and s['area'] else '') or '(unassigned lead)'
    c['loc'] = (s['location'].strip() if s and s['location'] else '') if s else ''

def esc(x): return html.escape(str(x))
def month(serial):
    if serial is None: return -1
    d = EPOCH + datetime.timedelta(days=serial)
    return d.month - 1 if d.year == 2026 else -1
def fmtdate(serial):
    if serial is None: return '—'
    d = EPOCH + datetime.timedelta(days=serial)
    return d.strftime('%d %b %Y')
def pct(a, b): return round(100 * a / b) if b else 0
def chip(status):
    return SC[status], ('#fff' if status in DARK else '#1F3346')

# ---- universes (regions dropped; CO = has a real country office) ----
CO = [c for c in cases if c['region'] not in ('HQ', '')]           # country-office requests
PERF = [c for c in CO if c['status'] != 'Discontinued']            # performance universe
active = [c for c in PERF if c['status'] not in ('100%', 'Discontinued', 'Unassigned')]
overdue = sorted([c for c in active if c['xc'] is not None and c['xc'] < TODAY],
                 key=lambda c: -(TODAY - c['xc']))
ontrackSet = [c for c in active if not (c['xc'] is not None and c['xc'] < TODAY)]
onTrack = len(active) - len(overdue)
recent = [c for c in PERF if (c['cr'] or c['op']) and (c['cr'] or c['op']) >= TODAY - 30]
due = [c for c in PERF if c['xc'] is not None and c['xc'] <= TODAY]
doneDue = [c for c in due if c['status'] == '100%']
closed30 = [c for c in PERF if c['cl'] is not None and TODAY - 30 <= c['cl'] <= TODAY]
stalled = [c for c in active if c['status'] == '0%' and c['op'] is not None and TODAY - c['op'] > 30]
disc = [c for c in CO if c['status'] == 'Discontinued']

# ======================================================================
# small rendering helpers
# ======================================================================
def groupby_area(rows):
    g = defaultdict(list)
    for c in rows: g[c['area']].append(c)
    return sorted(g.items(), key=lambda kv: -len(kv[1]))

def stacked_segs(rows):
    n = len(rows); out = []
    for s in STATUS_ORDER:
        w = sum(1 for c in rows if c['status'] == s)
        if w: out.append((SC[s], 100 * w / n))
    return out

def seg_bar(segs, width_pct, h=12, track='#EEF2F6'):
    inner = ''.join(f'<span style="width:{w:.2f}%;background:{col}"></span>' for col, w in segs)
    return (f'<div class="track" style="height:{h}px;background:{track};border-radius:{h/2}px">'
            f'<div class="bar" style="height:100%;width:{width_pct:.1f}%;border-radius:{h/2}px">{inner}</div></div>')

def barlist(items, color, track='#E9F0F6', label_w=64, empty='None in the current filter.',
            right=False, pct=False, denom=None):
    """pct=True adds a % column. By default it's each row's share of the chart
    total; pass `denom` (a {label: total} map) to show each row as a share of
    that category's own portfolio instead."""
    if not items: return f'<div class="muted">{empty}</div>'
    mx = max(n for _, n in items) or 1
    tot = sum(n for _, n in items) or 1
    lblcls = 'bllabel right' if right else 'bllabel'
    cols = f'{label_w}px 1fr 34px' + (' 44px' if pct else '')
    rows = ''
    for label, n in items:
        d = (denom.get(label, n) if denom else tot) or 1
        pcttd = f'<div class="blpct">{round(100 * n / d)}%</div>' if pct else ''
        rows += (f'<div class="blrow" style="grid-template-columns:{cols}">'
                 f'<div class="{lblcls}">{esc(label)}</div>'
                 f'<div class="track" style="height:9px;background:{track};border-radius:5px"><div style="height:100%;width:{100*n/mx:.1f}%;background:{color};border-radius:5px"></div></div>'
                 f'<div class="bln">{n}</div>{pcttd}</div>')
    return rows

def bucket_bars(buckets, label_w=92):
    mx = max((b[1] for b in buckets), default=1) or 1
    rows = ''
    for label, n, color in buckets:
        rows += (f'<div class="blrow" style="grid-template-columns:{label_w}px 1fr 44px">'
                 f'<div class="bllabel">{esc(label)}</div>'
                 f'<div class="track" style="height:12px;background:#EEF2F6;border-radius:6px"><div style="height:100%;width:{100*n/mx:.1f}%;background:{color};border-radius:6px"></div></div>'
                 f'<div class="bln" style="color:{color}">{n}</div></div>')
    return rows

def area_status_rows(rows_by_area, label_w=210):
    mx = max((len(v) for _, v in rows_by_area), default=1) or 1
    out = ''
    for name, rows in rows_by_area:
        leads = len({c['lead'] for c in rows if c['lead']})
        out += (f'<div class="arearow" style="grid-template-columns:{label_w}px 1fr 44px 52px">'
                f'<div class="arealabel">{esc(name)}</div>'
                f'{seg_bar(stacked_segs(rows), 100*len(rows)/mx, 13)}'
                f'<div class="an">{len(rows)}</div><div class="al">{leads}</div></div>')
    return out

def legend():
    return ''.join(f'<div class="lg"><span class="lgdot" style="background:{SC[s]}"></span>{s}</div>' for s in STATUS_ORDER)

def kpi_strip(tiles):
    out = ''
    for label, val, sub, accent, color in tiles:
        out += (f'<div class="kpi" style="border-top:3px solid {accent}">'
                f'<div class="kpilabel">{label}</div><div class="kpival" style="color:{color}">{val}</div>'
                f'<div class="kpisub">{sub}</div></div>')
    return f'<div class="kpistrip">{out}</div>'

def hero(bg, border, labelc, value, valuec, label, body, bodyc):
    return (f'<div class="hero" style="background:{bg};border:1px solid {border}">'
            f'<div class="herolabel" style="color:{labelc}">{label}</div>'
            f'<div class="heroval" style="color:{valuec}">{value}</div>'
            f'<div class="herobody" style="color:{bodyc}">{body}</div></div>')

def req_table(title, rows, metric_label, days_color, footer='', cols=None):
    cols = cols or ['Case', 'Country', 'Description', 'Thematic area', 'Exp. completion', 'Status', 'State', 'TA lead', metric_label]
    head = ''.join(f'<div class="{"r" if h==cols[-1] else ""}">{esc(h)}</div>' for h in cols)
    body = ''
    for r in rows:
        cbg, cfg = chip(r['status'])
        state = 'Closed' if r['cl'] else 'Open'
        sbg, sfg = ('#E7EEF3', '#0B5A8A') if r['cl'] else ('#E6F0EA', '#2E7D5B')
        lead = r['lead'] or '— none —'
        leadc = '#43586B' if r['lead'] else '#C0453F'
        body += (f'<div class="trow">'
                 f'<div class="tid">{esc(r["id"])}</div>'
                 f'<div class="tclip">{esc(r["office"] or "—")}</div>'
                 f'<div class="tclip muted" title="{esc(r.get("full") or r.get("desc") or "")}">{esc(r.get("full") or r.get("desc") or "—")}</div>'
                 f'<div class="tclip">{esc(r["area"])}</div>'
                 f'<div class="tnum">{fmtdate(r["xc"])}</div>'
                 f'<div><span class="pill" style="background:{cbg};color:{cfg}">{esc(r["status"])}</span></div>'
                 f'<div><span class="pill" style="background:{sbg};color:{sfg}">{state}</span></div>'
                 f'<div class="tclip" style="color:{leadc}">{esc(lead)}</div>'
                 f'<div class="tmetric" style="color:{days_color}">{esc(r["_m"])}</div></div>')
    foot = f'<div class="tfoot">{footer}</div>' if footer else ''
    return (f'<div class="table"><div class="ttitle">{esc(title)}</div>'
            f'<div class="tscroll"><div class="tmin">'
            f'<div class="thead">{head}</div><div class="tbody">{body}</div></div></div>{foot}</div>')


# --- "TA Requests · Detailed" table (country-profiles style) with a New/Overdue toggle ---
def fmt_my(serial):
    if serial is None:
        return '—'
    return (EPOCH + datetime.timedelta(days=serial)).strftime('%b %y')

DET_STPCT = {'0%': 6, '25%': 25, '50%': 50, '75%': 75, '100%': 100, 'Unassigned': 4, 'Discontinued': 100}

def _det_row(i, c):
    title = c['desc'] or '—'
    full = c['full'] if c.get('full') and c['full'] != c['desc'] else ''
    chips = ''
    if c['area'] and c['area'] != '(unassigned lead)':
        chips += f'<span class="dchip area">{esc(c["area"])}</span>'
    if c.get('modality'):
        chips += f'<span class="dchip mod">{esc(c["modality"])}</span>'
    reqfor = esc(c['reqFor']) if c['reqFor'] else '—'
    assigned = (f'<span class="dval">{esc(c["lead"])}</span>' if c['lead']
                else '<span class="dwarn">&#9888; unassigned</span>')
    typ = c['type'] or '—'
    typlabel = 'Big Ticket Item' if typ == 'Big Ticket' else typ
    typcls = 'big' if typ == 'Big Ticket' else 'routine'
    st = c['status']
    stcol = SC.get(st, '#9AA7B2')
    stlabel = st
    stpct = DET_STPCT.get(st, 0)
    return (
        f'<div class="drow">'
        f'<div class="dnum">{i:02d}</div>'
        f'<div class="ddesc"><div class="dtitle">{esc(title)}</div>'
        + (f'<div class="dfull">{esc(full)}</div>' if full else '')
        + (f'<div class="dchips">{chips}</div>' if chips else '')
        + '</div>'
        f'<div class="dreq"><div class="dlabel">Requested for</div><div class="dval">{reqfor}</div>'
        f'<div class="dlabel" style="margin-top:9px">Assigned to</div>{assigned}</div>'
        f'<div class="dtype"><span class="dpill {typcls}">{esc(typlabel)}</span>'
        f'<div class="ddate">{fmt_my(c["xs"])} &rarr; {fmt_my(c["xc"])}</div></div>'
        f'<div class="dstatus"><span class="dstpill"><span class="dstdot" style="background:{stcol}"></span>{esc(stlabel)}</span>'
        f'<div class="dstbar"><div style="width:{stpct}%;background:{stcol}"></div></div></div>'
        f'</div>'
    )

def detailed_table(sets):
    """sets = list of (key, toggle-label, rows). Country-profiles styling."""
    tabs, boxes = '', ''
    for j, (key, label, rows) in enumerate(sets):
        tabs += (f'<button class="dtoggle{" on" if j == 0 else ""}" data-tbl="{key}" '
                 f'onclick="showTbl(\'{key}\')">{label} <b>{len(rows)}</b></button>')
        body = ''.join(_det_row(i + 1, c) for i, c in enumerate(rows))
        boxes += (f'<div class="dtblbox" data-tbl="{key}" style="display:{"block" if j == 0 else "none"}">'
                  f'<div class="dhead"><div>#</div><div>Description</div><div>Requested for</div>'
                  f'<div>Type</div><div>Implementation status</div></div>'
                  f'<div class="dbody">{body}</div></div>')
    return (f'<div class="dtable"><div class="dtophead">'
            f'<div class="dttitle">TA Requests <span>&middot; Detailed</span></div>'
            f'<div class="dtoggles">{tabs}</div></div>'
            f'<div class="dscroll">{boxes}</div></div>')

# ======================================================================
# PERFORMANCE
# ======================================================================
perf_kpis = kpi_strip([
    ('Total requests', str(len(PERF)), 'nutrition TA requests (country offices)', '#0B6FA4', '#0F2238'),
    ('Received last 30 days', str(len(recent)), f'new since {WIN_STR}', '#1CABE2', '#0F2238'),
    ('Active &amp; on track', str(onTrack), 'in progress, not overdue', '#3E9CD6', '#3E9CD6'),
    ('Completed vs. target', f'{pct(len(doneDue), len(due))}%', f'of {len(due)} due by today, {len(doneDue)} at 100%', '#2E7D5B', '#2E7D5B'),
    ('Active on target', f'{pct(onTrack, len(active))}%', f'{len(overdue)} overdue — update date or close', '#3E9CD6', '#0F2238'),
    ('Overdue', str(len(overdue)), 'past their expected completion date', '#C0453F', '#C0453F'),
])

# opened vs completed by month (Apr-Jul = idx 3..6)
io = []
for i in range(3, 7):
    opened = sum(1 for c in PERF if month(c['op']) == i)
    comp = sum(1 for c in PERF if c['status'] == '100%' and month(c['cl'] if c['cl'] is not None else c['rs']) == i)
    io.append((['Jan','Feb','Mar','Apr','May','Jun','Jul'][i], opened, comp))
io_max = max((max(o, d) for _, o, d in io), default=1) or 1
io_html = ''
for label, o, d in io:
    io_html += (f'<div class="mcol">'
                f'<div class="mpair">'
                f'<div class="mbarwrap"><div class="mval" style="color:#0B6FA4">{o}</div><div class="mbar" style="height:{round(140*o/io_max)}px;background:#0B6FA4"></div></div>'
                f'<div class="mbarwrap"><div class="mval" style="color:#2E7D5B">{d}</div><div class="mbar" style="height:{round(140*d/io_max)}px;background:#2E7D5B"></div></div>'
                f'</div><div class="mlabel">{label}</div></div>')
io_opened = sum(o for _, o, _ in io); io_done = sum(d for _, _, d in io)

# received last 30 / on track / overdue / completed — by thematic area & by programme offer
def by_offer(rows):
    return Counter(c['offer'] or '(no offer)' for c in rows).most_common()

# each category's whole portfolio (all statuses), used as the % denominator
area_total = Counter(c['area'] for c in PERF)
offer_total = Counter(c['offer'] or '(no offer)' for c in PERF)

recent_area = [(k, len(v)) for k, v in groupby_area(recent)]
ontrack_area = [(k, len(v)) for k, v in groupby_area(ontrackSet)]
overdue_area = [(k, len(v)) for k, v in groupby_area(overdue)]
completed_perf = [c for c in PERF if c['status'] == '100%']
completed_area = [(k, len(v)) for k, v in groupby_area(completed_perf)]

# ---- "flow of work" — bubbles sized by share of all requests, click -> by-area/offer bars ----
flow_total = len(PERF)
FLOW = [   # key, label, sub, count, colour, by-area data, by-offer data, show-% -of-total
    ('received',  'Received',  'new · last 30 days',   len(recent),         '#0B6FA4', recent_area,    by_offer(recent),         False),
    ('ontrack',   'On track',  'in progress, on time', onTrack,             '#3E9CD6', ontrack_area,   by_offer(ontrackSet),     True),
    ('overdue',   'Overdue',   'past target date',     len(overdue),        '#C0453F', overdue_area,   by_offer(overdue),        True),
    ('completed', 'Completed', 'reached 100%',         len(completed_perf), '#2E7D5B', completed_area, by_offer(completed_perf), True),
]
FLOW_DEFAULT = 'ontrack'
_flow_track = {'#0B6FA4': '#E9F0F6', '#3E9CD6': '#E4EFF6', '#C0453F': '#F2EAE9', '#2E7D5B': '#E6F1EB'}
_cmax = max(d[3] for d in FLOW) or 1
_k = 70.0 / math.sqrt(_cmax)                 # radius so the biggest bubble ~70px
_radii = {d[0]: max(15, round(math.sqrt(d[3]) * _k)) for d in FLOW}
_maxR = max(_radii.values())

flow_band = ''
for i, (key, label, sub, count, col, area, offer, showpct) in enumerate(FLOW):
    r = _radii[key]; dia = 2 * r
    fs = max(13, min(34, round(r * 0.85)))
    on = ' on' if key == FLOW_DEFAULT else ''
    pcttxt = f'{round(100 * count / flow_total)}% of all TA' if showpct else 'inflow · 30d'
    flow_band += (f'<div class="flownode{on}" data-flow="{key}" onclick="showFlow(\'{key}\')">'
                  f'<div class="flowcircwrap" style="height:{2 * _maxR}px;animation-delay:{i * 0.1:.2f}s">'
                  f'<div class="flowcirc" style="--c:{col};width:{dia}px;height:{dia}px">'
                  f'<span class="flownum" data-val="{count}" style="color:{col};font-size:{fs}px">{count}</span></div></div>'
                  f'<div class="flowlabel">{label}</div><div class="flowsub">{sub}</div>'
                  f'<div class="flowpct" style="color:{col}">{pcttxt}</div></div>')
    if i < len(FLOW) - 1:
        flow_band += f'<div class="flowarrow" style="height:{2 * _maxR}px">&rarr;</div>'

flow_bars = ''
for key, label, sub, count, col, area, offer, showpct in FLOW:
    disp = 'block' if key == FLOW_DEFAULT else 'none'
    trk = _flow_track.get(col, "#E9F0F6")
    flow_bars += (f'<div class="flowbarbox" data-flow="{key}" style="display:{disp}">'
                  f'<div class="cardtitle">{label} — by thematic area</div>'
                  f'{barlist(area, col, trk, label_w=300, right=True, pct=True, denom=area_total)}'
                  f'<div class="divider"></div>'
                  f'<div class="cardtitle">{label} — by programme offer</div>'
                  f'{barlist(offer, col, trk, label_w=300, right=True, pct=True, denom=offer_total)}'
                  f'<div class="barnote">% is the share of each thematic area’s (or programme offer’s) '
                  f'own portfolio that is {label.lower()}.</div></div>')

_onpct = round(100 * onTrack / flow_total)
_ovpct = round(100 * len(overdue) / flow_total)
_dopct = round(100 * len(completed_perf) / flow_total)
flow_card = (
    '<div class="card">'
    f'<div class="cardtitle" style="margin-bottom:2px">Where the {flow_total} nutrition TA requests stand today</div>'
    f'<div style="font-size:12.5px;color:#5B7186;margin-bottom:8px">Each circle is sized by its share of the portfolio — '
    f'<b style="color:#3E9CD6">{_onpct}% on track</b>, <b style="color:#2E7D5B">{_dopct}% completed</b>, and '
    f'<b style="color:#C0453F">{_ovpct}% overdue</b>. Click a circle to break that group down by thematic area.</div>'
    f'<div class="flowband">{flow_band}</div>'
    '<div class="flownote"><b>On track</b>, <b>Overdue</b> and <b>Completed</b> cover the whole portfolio. '
    '<b>Received</b> is the 30-day inflow and already counted within the other three by their status.</div>'
    '<div class="divider"></div>'
    f'<div class="flowbars">{flow_bars}</div>'
    '</div>'
)

# newest + overdue tables
for c in cases: c['_m'] = ''
newest = sorted(recent, key=lambda c: -((c['cr'] or c['op']) or 0))
for c in newest: c['_m'] = str(round(TODAY - (c['cr'] or c['op'])))
for c in overdue: c['_m'] = '+' + str(round(TODAY - c['xc']))

# overdue severity
ob = [('1–30 days', sum(1 for c in overdue if TODAY - c['xc'] <= 30), '#E0A21E'),
      ('31–60 days', sum(1 for c in overdue if 30 < TODAY - c['xc'] <= 60), '#CD6A2E'),
      ('>60 days', sum(1 for c in overdue if TODAY - c['xc'] > 60), '#C0453F')]
ob_max = max((n for _, n, _ in ob), default=1) or 1

# stalled at 0% by thematic area (severity stacked)
def stalled_area_rows():
    g = groupby_area(stalled)
    if not g: return ''
    mx = max((len(v) for _, v in g), default=1) or 1
    out = ''
    for name, rows in g:
        n31 = sum(1 for c in rows if TODAY - c['op'] <= 60)
        n60 = sum(1 for c in rows if TODAY - c['op'] > 60)
        segs = []
        if n31: segs.append(('#CD6A2E', 100*n31/len(rows)))
        if n60: segs.append(('#C0453F', 100*n60/len(rows)))
        out += (f'<div class="arearow" style="grid-template-columns:210px 1fr 44px">'
                f'<div class="arealabel">{esc(name)}</div>{seg_bar(segs, 100*len(rows)/mx, 11, "#F5EEDF")}'
                f'<div class="an">{len(rows)}</div></div>')
    return out

# workload
lead_map = defaultdict(list)
for c in PERF:
    if c['lead']: lead_map[c['lead']].append(c)
lead_groups = sorted(lead_map.items(), key=lambda kv: -len(kv[1]))
counts = [len(v) for _, v in lead_groups]
load_min, load_max, load_avg = min(counts), max(counts), sum(counts)/len(counts)
lmax = max(counts) or 1
lead_html = ''
for name, rows in lead_groups:
    lead_html += (f'<div class="leadrow"><div class="leadlabel"><div class="leadname">{esc(name)}</div>'
                  f'<div class="leadarea">{esc(rows[0]["area"])}</div></div>'
                  f'{seg_bar(stacked_segs(rows), 100*len(rows)/lmax, 11)}<div class="ln">{len(rows)}</div></div>')

mgmt_kpis = kpi_strip([
    ('Open → assignment', 'N/A', 'measure coming soon', '#9AA7B2', '#9AA7B2'),
    ('Assignment → first response', 'N/A', 'measure coming soon', '#9AA7B2', '#9AA7B2'),
    ('Opened last 30 days', str(len(recent)), 'new requests received', '#0B6FA4', '#0F2238'),
    ('Closed last 30 days', str(len(closed30)), f'vs {len(recent)} received — throughput', '#2E7D5B', '#0F2238'),
    ('Stalled at 0%', str(len(stalled)), 'open >30 days, no progress', '#E0A21E', '#E0A21E'),
    ('Discontinued', str(len(disc)), f'{pct(len(disc), len(CO))}% requests dropped', '#9AA7B2', '#5B7186'),
])

# ======================================================================
# WHERE SUPPORT FLOWS — geographic map (origin duty station -> destination)
# Universe: all non-discontinued requests (matches the map's "349").
# ======================================================================
import worldmap

flowcases = [c for c in cases if c['status'] != 'Discontinued']
# duty station of each request = its TA lead's location (from the enriched roster)
HUB_META = {  # name: (lon, lat, label-anchor, colour)
    'Nairobi':  (36.82, -1.29, 'top',   '#0B6FA4'),
    'Bangkok':  (100.50, 13.75, 'right', '#2E7D5B'),
    'Amman':    (35.93, 31.95, 'top',   '#7A4FB0'),
    'Brussels': (4.35, 50.85, 'top',    '#1CABE2'),
    'Panama':   (-79.52, 8.98, 'left',  '#C87A2E'),
    'New York': (-74.01, 40.71, 'left', '#43586B'),
}

def hub_of(c):
    loc = c['loc']
    return loc if loc in HUB_META else ('(blank)' if c['lead'] else '(unassigned)')

def slug(x):
    return re.sub(r'[^a-z0-9]+', '', x.lower()) or 'x'

hub_total = Counter(hub_of(c) for c in flowcases)
hub_leads = defaultdict(Counter)   # hub -> {lead: n}
for c in flowcases:
    if c['lead']:
        hub_leads[hub_of(c)][c['lead']] += 1

# headline figures
ordered_hubs = sorted([n for n in HUB_META if hub_total.get(n, 0)], key=lambda n: -hub_total[n])
n_hubs = len(ordered_hubs)
n_countries = len({c['office'] for c in flowcases if c['office']})
n_resolved = sum(hub_total[h] for h in ordered_hubs)
n_blank = hub_total.get('(blank)', 0)
n_unassigned = hub_total.get('(unassigned)', 0)

LOC_ORDER = ordered_hubs + ['Blank']            # Nairobi … New York, then Blank
LOC_COLOR = {**{n: HUB_META[n][3] for n in HUB_META}, 'Blank': '#9AA7B2'}

def loc_key(c):
    return c['loc'] if c['loc'] in HUB_META else 'Blank'

loc_total = Counter(loc_key(c) for c in flowcases)
loc_leadcount = {L: len({c['lead'] for c in flowcases if loc_key(c) == L and c['lead']}) for L in LOC_ORDER}
# location -> thematic area -> staff -> Counter(implementation status)
loc_area = {L: defaultdict(lambda: defaultdict(Counter)) for L in LOC_ORDER}
# location -> thematic area -> set of supported country offices
loc_area_countries = {L: defaultdict(set) for L in LOC_ORDER}
for c in flowcases:
    L = loc_key(c)
    loc_area[L][c['area']][c['lead'] or '(unassigned lead)'][c['status']] += 1
    if c['office']:
        loc_area_countries[L][c['area']].add(c['office'])

# per-hub tooltip content for the map (thematic areas + staff-per-area, countries supported)
station_tips = {}
for L in HUB_META:
    hc = [c for c in flowcases if hub_of(c) == L]
    if not hc:
        continue
    countries = len({c['office'] for c in hc if c['office']})
    area_staff = defaultdict(set)
    for c in hc:
        if c['lead']:
            area_staff[c['area']].add(c['lead'])
    nstaff = len({c['lead'] for c in hc if c['lead']})
    rows = ''.join(
        f'<div><span>{esc("No lead" if a == "(unassigned lead)" else a)}</span><b>{len(s)} staff</b></div>'
        for a, s in sorted(area_staff.items(), key=lambda kv: -len(kv[1])))
    station_tips[L] = (
        f'<div class="maptip-title"><span class="mtdot" style="background:{HUB_META[L][3]}"></span>{esc(L)}</div>'
        f'<div class="maptip-sub">{len(hc)} requests · {countries} countries supported · {nstaff} staff</div>'
        f'<div class="maptip-areas">{rows}</div>')

# map inputs
office_counts = Counter(c['office'] for c in flowcases if c['loc'] in HUB_META and c['office'])
office_totals = Counter(c['office'] for c in flowcases if c['office'])   # all requests per country
links = Counter((c['loc'], c['office']) for c in flowcases if c['loc'] in HUB_META and c['office'])
stations = [{'name': n, 'key': slug(n), 'lon': lo, 'lat': la, 'anchor': an, 'color': co,
             'count': hub_total.get(n, 0), 'tip': station_tips.get(n, '')}
            for n, (lo, la, an, co) in HUB_META.items() if hub_total.get(n, 0)]
flow_map = worldmap.build_world_map(stations, office_counts, links, office_totals)

loc_tabs = ''
for L in LOC_ORDER:
    on = ' on' if L == LOC_ORDER[0] else ''
    loc_tabs += (f'<button class="loctab{on}" data-loc="{slug(L)}" onclick="showLoc(\'{slug(L)}\')">'
                 f'<span class="ltdot" style="background:{LOC_COLOR[L]}"></span>{esc(L)} <b>{loc_total.get(L, 0)}</b></button>')

def status_waffle(counter, cls='', label=None):
    """A unit chart: one little square per TA request, coloured by implementation
    status. `label` (the total) renders right after the last square."""
    sq = ''
    for s in STATUS_ORDER:
        n = counter.get(s, 0)
        if n:
            sq += f'<span class="sq" style="background:{SC[s]}"></span>' * n
    tail = f'<span class="stn">{label}</span>' if label is not None else ''
    return f'<div class="waffle {cls}">{sq}{tail}</div>'

def build_loc_bars(L, areas):
    """Collapsible thematic areas; each shows a square per TA (coloured by status).
    Expand for staff. All closed. `areas` = list of (area, {staff: Counter(status)})."""
    col = LOC_COLOR[L]
    out = ''
    for area, staff_map in areas:
        area_status = Counter()
        staff_tot = {}
        for st, sc in staff_map.items():
            staff_tot[st] = sum(sc.values())
            area_status.update(sc)
        atot = sum(area_status.values())
        aname = 'No lead assigned' if area == '(unassigned lead)' else area
        staff_rows = ''
        for st, tot in sorted(staff_tot.items(), key=lambda kv: -kv[1]):
            stname = '— unassigned —' if st == '(unassigned lead)' else st
            staff_rows += (f'<div class="strow"><div class="stname">{esc(stname)}</div>'
                           f'{status_waffle(staff_map[st], "sub", tot)}</div>')
        nstaff = len(staff_map)
        ncountries = len(loc_area_countries[L].get(area, ()))
        out += (f'<details class="areadet"><summary class="asum"><div class="arow">'
                f'<span class="chev">&#9656;</span>'
                f'<div class="aname">{esc(aname)}</div>'
                f'<div class="astats">'
                f'<span class="astat"><b style="color:{col}">{atot}</b> requests</span>'
                f'<span class="astat"><b>{nstaff}</b> staff</span>'
                f'<span class="astat"><b>{ncountries}</b> countries</span>'
                f'</div></div></summary>'
                f'<div class="staffwrap">{staff_rows}</div></details>')
    return out

loc_panels = ''
def _area_total(kv):
    return sum(sum(sc.values()) for sc in kv[1].values())

for L in LOC_ORDER:
    areas = sorted(loc_area[L].items(), key=lambda kv: -_area_total(kv))
    n_areas = len([a for a, _ in areas if a != '(unassigned lead)'])
    disp = 'block' if L == LOC_ORDER[0] else 'none'
    nlead = loc_leadcount.get(L, 0)
    summary = (f'{nlead} TA lead{"s" if nlead != 1 else ""} · {n_areas} thematic area'
               f'{"s" if n_areas != 1 else ""} · {loc_total.get(L, 0)} requests led')
    loc_panels += (f'<div class="locpanel" data-loc="{slug(L)}" style="display:{disp}">'
                   f'<div class="locsummary">{summary}</div>'
                   f'{build_loc_bars(L, areas)}</div>')

# ======================================================================
# DATA QUALITY (co = CO, all statuses)
# ======================================================================
co = CO
setupSet = [c for c in co if c['status'] in ('Unassigned', '0%', '25%')]
started = [c for c in co if c['status'] in ('50%', '75%')]
completedC = [c for c in co if c['status'] == '100%']
delivery = started + completedC
activeCO = [c for c in co if c['status'] not in ('100%', 'Discontinued')]

def stall_days(c):
    if c['status'] == 'Unassigned': return round(TODAY - (c['cr'] if c['cr'] is not None else c['op']))
    return round(TODAY - (c['up'] if c['up'] is not None else (c['cr'] if c['cr'] is not None else c['op'])))
def is_stalled(c):
    return stall_days(c) > (14 if c['status'] == 'Unassigned' else 30)
stalledSetup = [c for c in setupSet if is_stalled(c)]

# stage 1
stage_color = {'Unassigned': '#E0A21E', '0%': '#9CC6E0', '25%': '#5BA3D0'}
setup_funnel = [(s, sum(1 for c in setupSet if c['status'] == s), stage_color[s]) for s in ('Unassigned', '0%', '25%')]
aging = [('0–14 days', sum(1 for c in setupSet if stall_days(c) <= 14), '#3E9CD6'),
         ('15–30 days', sum(1 for c in setupSet if 14 < stall_days(c) <= 30), '#E0A21E'),
         ('30+ days', sum(1 for c in setupSet if stall_days(c) > 30), '#C0453F')]
stalled_by_area = [(k, len(v)) for k, v in groupby_area(stalledSetup)]
unassigned_by_area = [(k, len(v)) for k, v in groupby_area([c for c in setupSet if c['status'] == 'Unassigned'])]
zero_by_area = [(k, len(v)) for k, v in groupby_area([c for c in setupSet if c['status'] == '0%'])]
stalled_table_rows = sorted(stalledSetup, key=lambda c: -stall_days(c))[:12]
for c in stalled_table_rows: c['_m'] = str(stall_days(c)) + 'd'
at25 = [c for c in setupSet if c['status'] == '25%']
ready = [c for c in at25 if c['ho'] and c['lead'] and c['xc'] is not None]
no_lead = [c for c in setupSet if c['status'] in ('0%', '25%') and not c['lead']]

# stage 2
delN = len(delivery)
cfields = [('Objectives', lambda c: bool(c['ho'])), ('TA lead', lambda c: bool(c['lead'])),
           ('Expected completion', lambda c: c['xc'] is not None), ('Description', lambda c: bool(c['hd'])),
           ('Modality', lambda c: bool(c['modality'])), ('Programme offer', lambda c: bool(c['offer']))]
def qcolor(p): return '#2E7D5B' if p >= 95 else '#3E9CD6' if p >= 80 else '#E0A21E'
completeness = [(label, pct(sum(1 for c in delivery if fn(c)), delN)) for label, fn in cfields]
def passes(c):
    ok = bool(c['ho'] and c['lead'] and c['xc'] is not None and c['hd'] and c['modality'] and c['offer'])
    bad = c['xc'] is not None and c['xs'] is not None and c['xc'] < c['xs']
    return ok and not bad
passN = sum(1 for c in delivery if passes(c))
score = pct(passN, delN)
def qcol2(p): return '#2E7D5B' if p >= 80 else '#3E9CD6' if p >= 60 else '#E0A21E'
quality_by_area = sorted([(k, pct(sum(1 for c in v if passes(c)), len(v))) for k, v in groupby_area(delivery)], key=lambda kv: kv[1])
delivery_flags = [
    (sum(1 for c in delivery if not c['ho']), 'Missing objectives', 'work has started but objectives were never captured', '#C0453F'),
    (sum(1 for c in delivery if not c['lead']), 'No TA lead', 'in delivery yet unassigned', '#C0453F'),
    (sum(1 for c in delivery if c['xc'] is None), 'No expected completion date', 'timeliness can never be measured', '#C0453F'),
    (sum(1 for c in delivery if c['xc'] is not None and c['xs'] is not None and c['xc'] < c['xs']), 'Completion target before start', 'expected completion earlier than expected start', '#E0A21E'),
]
def reason(c):
    if not c['ho']: return 'no objectives'
    if not c['lead']: return 'no TA lead'
    if c['xc'] is None: return 'no target date'
    if not c['hd']: return 'no description'
    if not c['modality']: return 'no modality'
    if not c['offer']: return 'no offer'
    if c['xs'] is not None and c['xc'] < c['xs']: return 'target before start'
    return 'ok'
flagRecords = [c for c in delivery if not passes(c)]
for c in flagRecords: c['_m'] = reason(c)
seen = set(); dup = 0
for c in co:
    if not c['reqFor'] or not c['desc']: continue
    k = (c['reqFor'] + '|' + c['desc']).lower()
    if k in seen: dup += 1
    else: seen.add(k)

# stage 3
dq_overdue = sorted([c for c in activeCO if c['xc'] is not None and c['xc'] < TODAY], key=lambda c: -(TODAY - c['xc']))
for c in dq_overdue: c['_m'] = '+' + str(round(TODAY - c['xc'])) + 'd'
dq_ob = [('1–30 days', sum(1 for c in dq_overdue if TODAY - c['xc'] <= 30), '#E0A21E'),
         ('31–60 days', sum(1 for c in dq_overdue if 30 < TODAY - c['xc'] <= 60), '#CD6A2E'),
         ('>60 days', sum(1 for c in dq_overdue if TODAY - c['xc'] > 60), '#C0453F')]
at_risk = [c for c in activeCO if c['xc'] is not None and TODAY <= c['xc'] <= TODAY + 30]
dq_overdue_area = [(k, len(v)) for k, v in groupby_area(dq_overdue)]
not_closed = [c for c in co if c['status'] in ('100%', 'Discontinued') and not c['cl']]
for c in not_closed: c['_m'] = 'completed' if c['status'] == '100%' else 'discontinued'

dq_kpis = kpi_strip([
    ('Awaiting assignment', str(sum(1 for c in setupSet if c['status'] == 'Unassigned')), 'unassigned CO requests', '#E0A21E', '#0F2238'),
    ('In setup (0–25%)', str(sum(1 for c in setupSet if c['status'] != 'Unassigned')), 'being scoped with the CO', '#5BA3D0', '#0F2238'),
    ('Stalled in setup', str(len(stalledSetup)), 'stuck past the threshold', '#C0453F', '#C0453F'),
    ('In delivery (50%+)', str(len(started)), 'work has started', '#0B6FA4', '#0F2238'),
    ('Needing cleanup', str(len(flagRecords)), '50%+ with a data flag', '#C0453F', '#C0453F'),
    ('Overdue', str(len(dq_overdue)), 'active past target date', '#C0453F', '#C0453F'),
])

def completeness_rows():
    out = ''
    for label, p in completeness:
        out += (f'<div class="crow"><div class="clabel">{esc(label)}</div>'
                f'<div class="track" style="height:10px;background:#EEF2F6;border-radius:5px"><div style="height:100%;width:{p}%;background:{qcolor(p)};border-radius:5px"></div></div>'
                f'<div class="cpct" style="color:{qcolor(p)}">{p}%</div></div>')
    return out
def quality_rows(items, label_w=210):
    out = ''
    for label, p in items:
        out += (f'<div class="blrow" style="grid-template-columns:{label_w}px 1fr 44px">'
                f'<div class="bllabel">{esc(label)}</div>'
                f'<div class="track" style="height:10px;background:#EEF2F6;border-radius:5px"><div style="height:100%;width:{p}%;background:{qcol2(p)};border-radius:5px"></div></div>'
                f'<div class="bln" style="color:{qcol2(p)}">{p}%</div></div>')
    return out
def checkitems(items):
    out = ''
    for n, label, sub, color in items:
        out += (f'<div class="check"><div class="checkn" style="color:{color}">{n}</div>'
                f'<div><div class="checklabel">{esc(label)}</div><div class="checksub">{esc(sub)}</div></div></div>')
    return out

# ======================================================================
# ASSEMBLE
# ======================================================================
def panelhead(title, sub=''):
    s = f'<div class="ps">{sub}</div>' if sub else ''
    return f'<div class="panelhead"><div class="pt">{esc(title)}</div>{s}</div>'

PAGE = f'''<!-- @dsCard group="Dashboards" -->
<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nutrition TA Management Dashboard</title>
<style>
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:#EDF1F4; color:#0F2238; font-family:'Helvetica Neue',Helvetica,Arial,sans-serif; -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:1340px; margin:0 auto; padding:0 24px 70px; }}
  .track {{ overflow:hidden; }} .bar {{ display:flex; overflow:hidden; }} .bar span {{ display:block; }}
  .muted {{ color:#9AA7B2; font-size:12.5px; }}

  header.hd {{ padding:30px 0 18px; display:flex; justify-content:space-between; align-items:flex-end; gap:24px; flex-wrap:wrap; }}
  .eyebrow {{ font-size:11px; letter-spacing:.16em; text-transform:uppercase; color:#1CABE2; font-weight:700; }}
  .h1 {{ font-size:27px; font-weight:700; letter-spacing:-.01em; margin-top:6px; }}
  .meta {{ text-align:right; font-size:12px; color:#5B7186; line-height:1.6; }} .meta b {{ color:#0F2238; }}

  /* top tabs */
  .tabs {{ display:flex; gap:8px; margin:6px 0 20px; flex-wrap:wrap; position:sticky; top:0; z-index:20; background:#EDF1F4; padding:10px 0; }}
  .tab {{ cursor:pointer; font-family:inherit; font-size:13.5px; font-weight:700; padding:10px 22px; border-radius:9px; border:1px solid #D5DEE6; background:#fff; color:#43586B; }}
  .tab.on {{ background:#16385C; color:#fff; border-color:#16385C; }}

  /* sub tabs */
  .subtabs {{ display:flex; gap:4px; border-bottom:1px solid #DCE3EA; margin:24px 0 10px; flex-wrap:wrap; }}
  .subtab {{ cursor:pointer; font-family:inherit; border:none; background:transparent; font-size:16px; font-weight:700; padding:11px 18px; color:#5B7186; border-bottom:3px solid transparent; margin-bottom:-1px; }}
  .subtab.on {{ color:#0B5A8A; border-bottom-color:#0B5A8A; }}

  .panelhead {{ margin:16px 0 14px; }}
  .panelhead .pt {{ font-size:18px; font-weight:700; letter-spacing:-.01em; }}
  .panelhead .ps {{ font-size:13px; color:#5B7186; margin-top:3px; }}

  .kpistrip {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:14px; }}
  .kpi {{ background:#fff; border:1px solid #E3E9EF; border-radius:10px; padding:16px 18px; }}
  .kpilabel {{ font-size:12px; color:#5B7186; font-weight:600; }}
  .kpival {{ font-size:32px; font-weight:700; letter-spacing:-.02em; line-height:1.1; margin:6px 0 4px; font-variant-numeric:tabular-nums; }}
  .kpisub {{ font-size:11.5px; color:#9AA7B2; }}

  .card {{ background:#fff; border:1px solid #E3E9EF; border-radius:10px; padding:20px 22px; }}
  .cardtitle {{ font-size:13.5px; font-weight:700; margin-bottom:14px; }}
  .cardnote {{ font-size:12px; color:#8A98A6; line-height:1.55; margin-top:16px; border-top:1px solid #F1F4F7; padding-top:12px; }}
  .cardnote b, .cardnote strong {{ color:#5B7186; }}
  .grid2 {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(320px,100%),1fr)); gap:16px; align-items:stretch; }}
  .grid3 {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(230px,100%),1fr)); gap:16px; align-items:stretch; }}
  .grid13 {{ display:grid; grid-template-columns:1fr 2fr; gap:16px; align-items:stretch; }}
  @media (max-width:720px) {{ .grid13 {{ grid-template-columns:1fr; }} }}
  .grid2 > *, .grid3 > *, .grid13 > * {{ height:100%; }}
  .mt16 {{ margin-top:16px; }}

  .legend {{ display:flex; flex-wrap:wrap; gap:10px 16px; margin:0 0 16px; }}
  .lg {{ display:flex; align-items:center; gap:6px; font-size:11.5px; color:#43586B; }}
  .lgdot {{ width:11px; height:11px; border-radius:3px; }}

  .blrow {{ display:grid; align-items:center; gap:10px; margin-bottom:9px; }}
  .bllabel {{ font-size:12px; color:#43586B; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .bllabel.right {{ font-size:13px; text-align:right; white-space:normal; overflow:visible; text-overflow:clip; line-height:1.3; }}
  .bln {{ text-align:right; font-weight:700; font-size:12.5px; font-variant-numeric:tabular-nums; }}
  .blpct {{ text-align:right; font-size:11.5px; color:#9AA7B2; font-weight:600; font-variant-numeric:tabular-nums; }}
  .barnote {{ font-size:11.5px; color:#9AA7B2; margin-top:16px; border-top:1px solid #F1F4F7; padding-top:12px; }}

  .arearow {{ display:grid; align-items:center; gap:12px; margin-bottom:11px; }}
  .arealabel {{ font-size:12.5px; color:#43586B; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .an {{ text-align:right; font-weight:700; font-size:13px; font-variant-numeric:tabular-nums; }}
  .al {{ text-align:right; font-size:12.5px; font-weight:700; color:#0B6FA4; font-variant-numeric:tabular-nums; }}
  .areahead {{ display:grid; grid-template-columns:210px 1fr 44px 52px; gap:12px; font-size:10px; letter-spacing:.05em; text-transform:uppercase; color:#9AA7B2; font-weight:700; margin-bottom:10px; }}
  .areahead .r {{ text-align:right; }}

  .hero {{ border-radius:10px; padding:20px 22px; min-height:216px; height:100%; display:flex; flex-direction:column; justify-content:center; }}
  .herolabel {{ font-size:12px; letter-spacing:.06em; text-transform:uppercase; font-weight:700; }}
  .heroval {{ font-size:52px; font-weight:700; letter-spacing:-.03em; line-height:1; margin:10px 0 6px; font-variant-numeric:tabular-nums; }}
  .herobody {{ font-size:12.5px; line-height:1.5; }}
  .minicard {{ background:#fff; border:1px solid #E3E9EF; border-radius:10px; padding:20px 22px; height:100%; }}

  .mchart {{ display:flex; align-items:flex-end; gap:14px; padding:0 6px; min-width:320px; }}
  .mcol {{ flex:1; display:flex; flex-direction:column; align-items:center; gap:7px; }}
  .mpair {{ display:flex; align-items:flex-end; gap:5px; }}
  .mbarwrap {{ display:flex; flex-direction:column; align-items:center; gap:3px; }}
  .mval {{ font-size:10.5px; font-weight:700; font-variant-numeric:tabular-nums; }}
  .mbar {{ width:26px; min-height:2px; border-radius:4px 4px 0 0; }}
  .mlabel {{ font-size:11.5px; color:#5B7186; font-weight:600; }}

  .table {{ background:#fff; border:1px solid #E3E9EF; border-radius:10px; margin-top:16px; overflow:hidden; }}
  .ttitle {{ font-size:13px; font-weight:700; padding:14px 22px 10px; }}
  .tscroll {{ overflow-x:auto; }} .tmin {{ min-width:960px; }}
  .thead, .trow {{ display:grid; grid-template-columns:100px 110px 1.5fr 150px 108px 64px 70px 130px 88px; gap:10px; padding:9px 22px; align-items:center; }}
  .thead {{ background:#F6F8FA; border-top:1px solid #EDF1F4; border-bottom:1px solid #EDF1F4; font-size:10.5px; letter-spacing:.06em; text-transform:uppercase; color:#7A8C9C; font-weight:700; }}
  .thead .r {{ text-align:right; }}
  .tbody {{ max-height:440px; overflow-y:auto; }}
  .trow {{ border-bottom:1px solid #F1F4F7; font-size:12.5px; }}
  .tid {{ font-weight:600; color:#0B5A8A; font-variant-numeric:tabular-nums; }}
  .tclip {{ color:#43586B; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .tclip.muted {{ color:#5B7186; }}
  .tnum {{ color:#43586B; font-variant-numeric:tabular-nums; white-space:nowrap; }}
  .tmetric {{ text-align:right; font-weight:700; font-variant-numeric:tabular-nums; }}
  .pill {{ font-size:11.5px; font-weight:700; padding:2px 8px; border-radius:5px; }}
  .tfoot {{ padding:12px 22px 14px; font-size:11.5px; color:#8A98A6; line-height:1.55; border-top:1px solid #F1F4F7; }}

  /* dense "TA Requests · Detailed" table (blue theme, New/Overdue toggle) */
  .dtable {{ background:#fff; border:1px solid #E3E9EF; border-radius:10px; margin-top:16px; overflow:hidden; }}
  .dtophead {{ display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; padding:15px 22px 12px; border-bottom:1px solid #EDF1F4; }}
  .dttitle {{ font-size:16px; font-weight:700; color:#0F2238; letter-spacing:-.01em; }}
  .dttitle span {{ color:#9AA7B2; font-weight:400; }}
  .dtoggles {{ display:flex; gap:6px; }}
  .dtoggle {{ cursor:pointer; font-family:inherit; font-size:12.5px; font-weight:700; padding:7px 13px; border-radius:8px; border:1px solid #D5DEE6; background:#fff; color:#5B7186; display:inline-flex; align-items:center; gap:6px; }}
  .dtoggle b {{ color:#0F2238; font-variant-numeric:tabular-nums; }}
  .dtoggle.on {{ background:#16385C; color:#fff; border-color:#16385C; }}
  .dtoggle.on b {{ color:#fff; }}
  .dscroll {{ max-height:580px; overflow:auto; }}
  .dhead, .drow {{ display:grid; grid-template-columns:40px minmax(230px,2.4fr) 1.3fr 1fr 1.05fr; gap:18px; min-width:900px; }}
  .dhead {{ position:sticky; top:0; z-index:1; background:#F6F8FA; padding:10px 22px; font-size:10px; letter-spacing:.07em; text-transform:uppercase; color:#7A8C9C; font-weight:700; border-bottom:1px solid #EDF1F4; }}
  .drow {{ padding:14px 22px; border-bottom:1px solid #F1F4F7; align-items:start; }}
  .dnum {{ font-size:12px; color:#9AA7B2; font-weight:600; font-variant-numeric:tabular-nums; padding-top:2px; }}
  .dtitle {{ font-size:13.5px; font-weight:700; color:#0F2238; line-height:1.35; }}
  .dfull {{ font-size:12px; color:#7A8794; margin-top:3px; line-height:1.45; }}
  .dchips {{ display:flex; flex-wrap:wrap; gap:6px; margin-top:9px; }}
  .dchip {{ font-size:11px; padding:3px 9px; border-radius:6px; white-space:nowrap; }}
  .dchip.area {{ background:#EAF2F8; color:#0B5A8A; }}
  .dchip.mod {{ background:#EEF2F6; color:#5B7186; }}
  .dlabel {{ font-size:9.5px; letter-spacing:.07em; text-transform:uppercase; color:#9AA7B2; font-weight:700; }}
  .dval {{ font-size:13px; color:#43586B; margin-top:2px; }}
  .dwarn {{ font-size:12.5px; color:#C0453F; font-weight:600; margin-top:2px; display:inline-block; }}
  .dpill {{ display:inline-block; font-size:11.5px; font-weight:700; padding:3px 10px; border-radius:6px; }}
  .dpill.routine {{ background:#E4EEF6; color:#0B5A8A; }}
  .dpill.big {{ background:#F5E6D6; color:#B0602C; }}
  .ddate {{ font-size:12px; color:#8A98A6; margin-top:8px; font-variant-numeric:tabular-nums; white-space:nowrap; }}
  .dstpill {{ display:inline-flex; align-items:center; gap:7px; font-size:12.5px; font-weight:700; color:#0F2238; background:#EEF2F6; padding:4px 11px; border-radius:999px; }}
  .dstdot {{ width:8px; height:8px; border-radius:50%; }}
  .dstbar {{ height:3px; background:#EAEEF2; border-radius:2px; margin-top:9px; max-width:150px; }}
  .dstbar > div {{ height:100%; border-radius:2px; }}

  /* flow map */
  .wmwrap {{ overflow-x:auto; background:#F7FAFC; border-radius:10px; padding:4px; }}
  .wmsvg {{ width:100%; min-width:720px; height:auto; display:block; }}
  .wmarc {{ transition:opacity .18s ease, stroke-width .18s ease; }}
  .wmdot, .wmbub {{ transition:opacity .18s ease; }}
  .wmbub {{ cursor:pointer; }}
  .wmhint {{ font-size:11.5px; color:#0B6FA4; margin-top:12px; }}
  .wmlabel {{ font:600 13px 'Helvetica Neue',Arial,sans-serif; fill:#0F2238; paint-order:stroke; stroke:#fff; stroke-width:3px; stroke-linejoin:round; }}
  .wmcount {{ font-weight:700; }}
  .wmlegend {{ display:flex; flex-wrap:wrap; gap:10px 20px; margin-top:14px; }}
  .lgswatch {{ width:16px; height:11px; border-radius:2px; background:#C6D8E8; display:inline-block; }}
  .flowintro {{ font-size:13px; color:#5B7186; margin-bottom:16px; }} .flowintro b {{ color:#0B6FA4; font-size:15px; }}

  /* by-location graphic */
  .loctabs {{ display:flex; gap:8px; flex-wrap:wrap; margin:2px 0 20px; }}
  .loctab {{ cursor:pointer; font-family:inherit; font-size:13px; font-weight:700; padding:9px 14px; border-radius:9px; border:1px solid #D5DEE6; background:#fff; color:#5B7186; display:inline-flex; align-items:center; gap:7px; }}
  .loctab b {{ color:#0F2238; font-variant-numeric:tabular-nums; }}
  .loctab.on {{ background:#16385C; color:#fff; border-color:#16385C; }}
  .loctab.on b {{ color:#fff; }}
  .ltdot {{ width:9px; height:9px; border-radius:3px; }}
  .locsummary {{ font-size:12.5px; color:#5B7186; margin-bottom:8px; }}
  .clicknote {{ font-size:11.5px; color:#0B6FA4; background:#EFF5FA; border:1px solid #DBE8F2; border-radius:7px; padding:7px 11px; display:inline-block; }}
  .areadet {{ border-top:1px solid #F1F4F7; }}
  .areadet:last-child {{ border-bottom:1px solid #F1F4F7; }}
  .asum {{ list-style:none; cursor:pointer; padding:12px 4px; }}
  .asum::-webkit-details-marker {{ display:none; }}
  .asum:hover .aname {{ color:#0B5A8A; }}
  .arow {{ display:grid; grid-template-columns:16px 1fr auto; gap:16px; align-items:center; }}
  .chev {{ color:#9AA7B2; font-size:13px; transition:transform .15s ease; }}
  details[open] .chev {{ transform:rotate(90deg); }}
  .aname {{ font-size:13.5px; font-weight:700; color:#0F2238; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .astats {{ display:flex; gap:20px; }}
  .astat {{ font-size:12px; color:#8593A1; white-space:nowrap; }}
  .astat b {{ color:#0F2238; font-size:14.5px; font-weight:700; font-variant-numeric:tabular-nums; margin-right:2px; }}
  @media (max-width:620px) {{ .astat {{ font-size:11px; }} .astats {{ gap:12px; }} }}
  .staffwrap {{ margin:0 0 14px 30px; padding:6px 0 6px 14px; border-left:2px solid #EDF1F4; }}
  .strow {{ display:grid; grid-template-columns:minmax(140px,200px) 1fr; gap:14px; align-items:center; margin-bottom:8px; }}
  .stname {{ font-size:12px; color:#43586B; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .stn {{ font-size:12px; font-weight:700; color:#43586B; font-variant-numeric:tabular-nums; margin-left:5px; }}
  .waffle {{ display:flex; flex-wrap:wrap; gap:3px; align-items:center; }}
  .sq {{ width:10px; height:10px; border-radius:2px; }}
  .waffle.sub .sq {{ width:9px; height:9px; }}
  .lochdr {{ display:flex; flex-wrap:wrap; align-items:center; justify-content:space-between; gap:10px 16px; margin-bottom:16px; }}
  .statuslegend {{ display:flex; flex-wrap:wrap; align-items:center; gap:8px 14px; }}
  .sllabel {{ font-size:11.5px; color:#5B7186; font-weight:600; }}

  /* map hover tooltip */
  .maptip {{ position:fixed; z-index:100; pointer-events:none; display:none; background:#0F2238; color:#fff; border-radius:9px; padding:11px 13px; font-size:12px; max-width:300px; box-shadow:0 8px 26px rgba(15,34,56,.32); }}
  .maptip-title {{ font-weight:700; font-size:13.5px; display:flex; align-items:center; gap:7px; }}
  .mtdot {{ width:10px; height:10px; border-radius:3px; display:inline-block; }}
  .maptip-sub {{ color:#AEBDCB; font-size:11px; margin:3px 0 9px; }}
  .maptip-areas > div {{ display:flex; justify-content:space-between; gap:18px; padding:2px 0; font-size:11.5px; color:#DCE6EF; }}
  .maptip-areas b {{ color:#fff; font-weight:700; white-space:nowrap; }}

  .hubgrid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:14px; }}
  .hubcard {{ border:1px solid #E3E9EF; border-radius:10px; padding:16px 18px; background:#FBFCFD; }}
  .hubhead {{ display:flex; align-items:center; gap:9px; }}
  .hubdot {{ width:12px; height:12px; border-radius:4px; }}
  .hubname {{ font-size:14.5px; font-weight:700; }}
  .hubcount {{ margin-left:auto; font-size:20px; font-weight:700; font-variant-numeric:tabular-nums; }}
  .hubsub {{ font-size:11.5px; color:#9AA7B2; margin:3px 0 12px 21px; }}
  .destwrap {{ display:flex; flex-wrap:wrap; gap:6px; }}
  .destchip {{ font-size:11.5px; color:#43586B; background:#F1F5F9; border:1px solid #E3E9EF; border-radius:999px; padding:4px 10px; }}
  .destchip b {{ color:#0B6FA4; }} .destchip.muted {{ color:#9AA7B2; background:transparent; }}

  /* workload */
  .leadgrid {{ column-count:2; column-gap:40px; }} @media (max-width:820px) {{ .leadgrid {{ column-count:1; }} }}
  .leadrow {{ display:grid; grid-template-columns:190px 1fr 34px; gap:10px; align-items:center; break-inside:avoid; margin-bottom:11px; }}
  .leadlabel {{ white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .leadname {{ font-size:12px; color:#43586B; overflow:hidden; text-overflow:ellipsis; }}
  .leadarea {{ font-size:10.5px; color:#9AA7B2; overflow:hidden; text-overflow:ellipsis; }}
  .ln {{ text-align:right; font-weight:700; font-size:12px; font-variant-numeric:tabular-nums; }}
  .loadstat {{ display:flex; gap:12px; margin:16px 0 22px; flex-wrap:wrap; }}
  .loadbox {{ flex:1; min-width:120px; border-radius:9px; padding:13px 16px; }}
  .loadlabel {{ font-size:10.5px; letter-spacing:.08em; text-transform:uppercase; font-weight:700; }}
  .loadval {{ font-size:26px; font-weight:700; font-variant-numeric:tabular-nums; line-height:1.15; margin-top:3px; }}
  .loadsub {{ font-size:11px; }}
  .divider {{ height:1px; background:#EDF1F4; margin:22px 0; }}

  /* flow-of-work bubbles */
  .flowband {{ display:flex; align-items:flex-start; justify-content:center; gap:6px; flex-wrap:wrap; margin:8px 0 2px; }}
  .flownode {{ cursor:pointer; text-align:center; padding:10px 12px; border-radius:14px; transition:background .15s; }}
  .flowcircwrap {{ display:flex; align-items:center; justify-content:center; animation:flowgrow .6s cubic-bezier(.34,1.56,.64,1) both; }}
  .flowcirc {{ border-radius:50%; border:2px solid color-mix(in srgb, var(--c) 48%, transparent); display:flex; align-items:center; justify-content:center;
    background:linear-gradient(180deg, color-mix(in srgb, var(--c) 6%, #fff) 0%, color-mix(in srgb, var(--c) 15%, #fff) 100%);
    box-shadow:0 8px 22px rgba(15,34,56,.10), 0 2px 5px rgba(15,34,56,.05);
    transition:transform .2s ease, box-shadow .2s ease, border-color .2s ease; }}
  .flownode:hover .flowcirc {{ transform:translateY(-3px) scale(1.02); box-shadow:0 14px 30px rgba(15,34,56,.14), 0 3px 7px rgba(15,34,56,.06); }}
  .flownode.on .flowcirc {{ transform:translateY(-2px) scale(1.02); border-color:var(--c); box-shadow:0 0 0 5px color-mix(in srgb, var(--c) 12%, transparent), 0 12px 28px rgba(15,34,56,.14); }}
  .flownum {{ font-weight:600; font-variant-numeric:tabular-nums; line-height:1; letter-spacing:-.01em; }}
  @keyframes flowgrow {{ from {{ transform:scale(.3); opacity:0; }} to {{ transform:scale(1); opacity:1; }} }}
  @media (prefers-reduced-motion: reduce) {{ .flowcircwrap {{ animation:none; }} }}
  .flowlabel {{ font-size:13.5px; font-weight:700; color:#0F2238; margin-top:12px; }}
  .flowsub {{ font-size:11px; color:#8A98A6; margin-top:1px; }}
  .flowpct {{ font-size:11.5px; font-weight:700; margin-top:4px; }}
  .flowarrow {{ color:#C4CDD6; font-size:22px; display:flex; align-items:center; }}
  .flownote {{ font-size:11.5px; color:#8A98A6; text-align:center; margin-top:6px; line-height:1.5; }}
  .flowbars {{ margin-top:2px; }}

  .sevlegend {{ display:flex; gap:16px; flex-wrap:wrap; }}
  .sevbar {{ display:flex; height:30px; border-radius:6px; overflow:hidden; border:1px solid #E3E9EF; }}
  .sevtags {{ display:flex; gap:24px; margin-top:10px; font-size:12.5px; flex-wrap:wrap; }}

  .crow {{ display:grid; grid-template-columns:170px 1fr 44px; gap:12px; align-items:center; margin-bottom:10px; }}
  .clabel {{ font-size:12.5px; color:#43586B; font-weight:600; }}
  .cpct {{ text-align:right; font-weight:700; font-size:12.5px; }}
  .score {{ font-size:46px; font-weight:700; letter-spacing:-.02em; line-height:1; }}
  .check {{ display:flex; gap:12px; align-items:flex-start; padding:10px 0; border-bottom:1px solid #F1F4F7; }}
  .checkn {{ font-size:22px; font-weight:700; min-width:44px; font-variant-numeric:tabular-nums; }}
  .checklabel {{ font-size:13px; font-weight:700; color:#0F2238; }}
  .checksub {{ font-size:11.5px; color:#8A98A6; }}
  .banner {{ border-radius:10px; padding:16px 20px; margin-top:16px; font-size:12.5px; line-height:1.55; }}
  .tcards {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:12px; }}
  .tcard {{ background:#F6F8FA; border:1px solid #EDF1F4; border-radius:9px; padding:14px 16px; }}
  .tcardlabel {{ font-size:13px; font-weight:700; color:#0F2238; }}
  .tcardsub {{ font-size:11.5px; color:#8A98A6; margin-top:3px; }}
</style></head>
<body>
<div class="wrap">

  <header class="hd">
    <div>
      <div class="eyebrow">Child Nutrition &amp; Development &middot; Technical Assistance</div>
      <div class="h1">Nutrition TA Management Dashboard</div>
    </div>
    <div class="meta">
      <div><b>{len(PERF)}</b> CO requests &middot; <b>{len(staff)}</b> team members</div>
      <div>Created Jan&ndash;Jul 2026 &middot; as of {TODAY_STR}</div>
    </div>
  </header>

  <div class="tabs">
    <button class="tab on" data-top="perf" onclick="showTop('perf')">Management</button>
    <button class="tab" data-top="dq" onclick="showTop('dq')">Data Quality</button>
  </div>

  <!-- ============ PERFORMANCE ============ -->
  <div class="toppanel" id="perf" style="display:block">
    {perf_kpis}

    <div class="subtabs">
      <button class="subtab subtab-perf on" data-sub="demand" onclick="showSub('perf','demand')">Status of TA</button>
      <button class="subtab subtab-perf" data-sub="flows" onclick="showSub('perf','flows')">Where support flows</button>
      <button class="subtab subtab-perf" data-sub="work" onclick="showSub('perf','work')">Workload</button>
    </div>

    <!-- demand -->
    <div class="subpanel-perf" id="demand" style="display:block">
      {panelhead('Status of TA', 'The full lifecycle of nutrition TA requests — received, in progress, completed and overdue.')}
      {flow_card}
      <div class="card mt16">
        <div style="display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:18px">
          <div class="cardtitle" style="margin:0">Requests opened vs. completed, by month (2026)</div>
          <div class="sevlegend"><div class="lg"><span class="lgdot" style="background:#0B6FA4"></span>Opened</div><div class="lg"><span class="lgdot" style="background:#2E7D5B"></span>Completed</div></div>
        </div>
        <div style="overflow-x:auto"><div class="mchart">{io_html}</div></div>
        <div class="cardnote"><strong>What this says:</strong> every month new demand (blue) outpaces completed work (green), so the active backlog grows. Since April, <b style="color:#0B6FA4">{io_opened}</b> requests were opened and <b style="color:#2E7D5B">{io_done}</b> reached 100%.</div>
      </div>
      <div class="grid2 mt16">
        <div class="card">
          <div style="display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:16px"><div class="cardtitle" style="margin:0">Overdue severity — how far past the target date</div>
            <div class="sevlegend">{''.join(f'<div class="lg"><span class="lgdot" style="background:{c}"></span>{l}</div>' for l,n,c in ob)}</div></div>
          <div class="sevbar">{''.join(f'<div style="width:{100*n/ob_max:.1f}%;background:{c}" title="{l}"></div>' for l,n,c in ob)}</div>
          <div class="sevtags">{''.join(f'<span style="color:{c};font-weight:700">{n} · {l}</span>' for l,n,c in ob)}</div>
        </div>
        <div class="card">
          <div style="display:flex;align-items:baseline;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:16px"><div class="cardtitle" style="margin:0">Stalled at 0% for 30+ days, by thematic area</div>
            <div class="sevlegend"><div class="lg"><span class="lgdot" style="background:#CD6A2E"></span>31–60 days</div><div class="lg"><span class="lgdot" style="background:#C0453F"></span>&gt;60 days</div></div></div>
          {stalled_area_rows() or '<div class="muted">None in the current filter.</div>'}
        </div>
      </div>
      <div class="banner" style="background:rgba(224,162,30,0.12);border:1px solid rgba(224,162,30,0.35);color:#7A5B10"><strong style="color:#5B7186">What this says:</strong> these <b style="color:#B0453F">{len(stalled)}</b> requests were assigned 30 or more days ago and have shown no progress at all.</div>
      {detailed_table([('new', 'New requests', newest), ('overdue', 'Overdue requests', overdue)])}
    </div>

    <!-- flows -->
    <div class="subpanel-perf" id="flows" style="display:none">
      {panelhead('Where support flows', 'From each request’s TA-lead duty station (origin) to the supported country office (destination).')}
      <div class="card">
        <div class="flowintro"><b>{n_hubs}</b> duty stations delivering technical assistance to <b>{n_countries}</b> countries. Origin is each request’s TA-lead duty station, joined to the CND staff roster ({len(staff)} staff); destination is the country office being supported.</div>
        {flow_map}
        <div class="wmlegend">
          <div class="lg"><span class="lgdot" style="background:#0B6FA4"></span>Duty station, sized by requests led</div>
          <div class="lg"><span class="lgdot" style="background:#6C7B8C;border-radius:50%"></span>Supported country office</div>
          <div class="lg"><span class="lgswatch"></span>Country named in the request export</div>
        </div>
        <div id="wmhint" class="wmhint" data-idle="Tip: click a duty station to trace the countries it supports · hover for details.">Tip: click a duty station to trace the countries it supports · hover for details.</div>
      </div>
      <div class="card mt16">
        <div class="cardtitle">By Centre-of-Excellence location — thematic areas &amp; staff assigned</div>
        <div class="loctabs">{loc_tabs}</div>
        <div class="lochdr">
          <div class="clicknote">Click a thematic area to see the staff assigned</div>
          <div class="statuslegend"><span class="sllabel">Each square = 1 request, by status</span>{legend()}</div>
        </div>
        {loc_panels}
        <div class="cardnote"><strong>What this says:</strong> select a CoE location to see how its TA load splits across thematic areas and staff assigned. <b>Nairobi</b> leads half of all nutrition TA ({hub_total.get('Nairobi', 0)})</div>
      </div>
    </div>

    <!-- workload -->
    <div class="subpanel-perf" id="work" style="display:none">
      {panelhead('Workload: thematic areas & staff', 'How requests distribute across thematic areas and individual TA leads.')}
      <div class="card">
        <div class="cardtitle">Requests by thematic area — coloured by implementation status</div>
        <div class="legend">{legend()}</div>
        <div class="areahead"><div>Thematic area</div><div></div><div class="r">TAs</div><div class="r">Leads</div></div>
        {area_status_rows(groupby_area(PERF))}
      </div>
      <div class="card mt16">
        <div class="cardtitle">Requests per TA lead — workload spread</div>
        <div style="font-size:13px;color:#5B7186;margin-bottom:2px"><b style="color:#0B6FA4;font-size:15px">{len(lead_groups)}</b> TA leads assigned</div>
        <div class="loadstat">
          <div class="loadbox" style="background:#F6F8FA;border:1px solid #EDF1F4"><div class="loadlabel" style="color:#7A8C9C">Minimum</div><div class="loadval" style="color:#2E7D5B">{load_min}</div><div class="loadsub" style="color:#9AA7B2">lightest lead</div></div>
          <div class="loadbox" style="background:#EEF6FB;border:1px solid #CFE6F2"><div class="loadlabel" style="color:#2C5A75">Average</div><div class="loadval" style="color:#0B6FA4">{load_avg:.1f}</div><div class="loadsub" style="color:#7FA6BE">requests per lead</div></div>
          <div class="loadbox" style="background:#FBF0EF;border:1px solid #F0D2CF"><div class="loadlabel" style="color:#B0453F">Maximum</div><div class="loadval" style="color:#C0453F">{load_max}</div><div class="loadsub" style="color:#C79490">{esc(lead_groups[0][0])}</div></div>
        </div>
        <div style="position:relative;height:10px;border-radius:5px;margin:6px 4px 0;background:linear-gradient(90deg,#4CA576,#5BA3D0,#C0453F)"><div style="position:absolute;top:-5px;left:{pct(round(load_avg)-load_min, max(1,load_max-load_min))}%;transform:translateX(-50%);width:3px;height:20px;background:#0F2238;border-radius:2px"></div></div>
        <div style="display:flex;justify-content:space-between;margin:9px 4px 0;font-size:11px;color:#7A8C9C"><span>Min {load_min}</span><span style="color:#0F2238;font-weight:700">Avg {load_avg:.1f}</span><span>Max {load_max}</span></div>
        <div class="divider"></div>
        <div class="cardtitle">Busiest TA lead staff — coloured by status</div>
        <div class="legend">{legend()}</div>
        <div class="leadgrid">{lead_html}</div>
      </div>
    </div>
  </div>

  <!-- ============ DATA QUALITY REVIEW ============ -->
  <div class="toppanel" id="dq" style="display:none">
    <div style="font-size:13px;color:#5B7186;margin:6px 0 14px;max-width:900px;line-height:1.5">Data quality read through the implementation-status lifecycle: <b>setup / in review</b> (Unassigned · 0% · 25%) where the concern is stalling, and <b>delivery / started</b> (50%+) where the concern is completeness &amp; consistency.</div>
    {dq_kpis}

    <div class="subtabs">
      <button class="subtab subtab-dq on" data-sub="recv" onclick="showSub('dq','recv')">Received &amp; in review</button>
      <button class="subtab subtab-dq" data-sub="deliv" onclick="showSub('dq','deliv')">Started &amp; in delivery</button>
      <button class="subtab subtab-dq" data-sub="close" onclick="showSub('dq','close')">Overdue &amp; closure</button>
    </div>

    <!-- received -->
    <div class="subpanel-dq" id="recv" style="display:block">
      {panelhead('Received & in review', 'Unassigned · 0% · 25% — the concern here is stalling before delivery starts.')}
      <div class="grid2">
        <div class="card"><div class="cardtitle">Setup funnel</div>{bucket_bars(setup_funnel, label_w=110)}</div>
        <div class="card"><div class="cardtitle">Time in stage (aging)</div>{bucket_bars(aging, label_w=110)}</div>
      </div>
      <div class="grid3 mt16">
        <div class="card"><div class="cardtitle">Stalled in setup, by thematic area</div>{barlist(stalled_by_area, '#E0A21E', '#F5EEDF', label_w=150)}</div>
        <div class="card"><div class="cardtitle">Unassigned, by thematic area</div>{barlist(unassigned_by_area, '#E0A21E', '#F5EEDF', label_w=150)}</div>
        <div class="card"><div class="cardtitle">At 0%, by thematic area</div>{barlist(zero_by_area, '#5BA3D0', label_w=150)}</div>
      </div>
      <div class="grid2 mt16">
        <div class="card"><div class="cardtitle">Ready to advance</div><div style="display:flex;align-items:baseline;gap:10px"><div class="score" style="color:#2E7D5B">{len(ready)}</div><div class="muted">of {len(at25)} requests at 25% have objectives, a lead and a target date</div></div></div>
        <div class="card"><div class="cardtitle">Setup contradictions</div>{checkitems([(len(no_lead), 'Past assignment, but no TA lead', '0% or 25% means a lead should already be assigned', '#C0453F')])}</div>
      </div>
      <div class="card mt16"><div class="cardtitle">Stage transitions (days) — coming soon</div>
        <div class="tcards">{''.join(f'<div class="tcard"><div class="tcardlabel">{l}</div><div class="tcardsub">{s}</div></div>' for l,s in [('Unassigned → 0%','days to assign a TA lead'),('0% → 25%','days to agree scope with the CO'),('25% → 50%','days to formally start delivery')])}</div>
      </div>
      {req_table('Most stalled setup requests', stalled_table_rows, 'Days stalled', '#C0453F', cols=['Case','Country','Description','Thematic area','Exp. completion','Status','State','TA lead','Days stalled'])}
    </div>

    <!-- delivery -->
    <div class="subpanel-dq" id="deliv" style="display:none">
      {panelhead('Started & in delivery', '50%+ — the concern here is completeness and internal consistency of the record.')}
      <div class="grid2">
        <div class="card"><div class="cardtitle">Field completeness ({delN} in delivery)</div>{completeness_rows()}</div>
        <div class="card"><div class="cardtitle">Delivery quality score</div>
          <div style="display:flex;align-items:baseline;gap:12px;margin:6px 0 4px"><div class="score" style="color:{'#2E7D5B' if score>=80 else '#E0A21E' if score>=60 else '#C0453F'}">{score}%</div><div class="muted">{passN} of {delN} pass every check</div></div>
          <div class="cardnote" style="margin-top:14px"><strong>What this says:</strong> a request passes when it has objectives, a lead, a target date, a description, a modality and a programme offer — and its completion target is not before its start.</div>
        </div>
      </div>
      <div class="card mt16"><div class="cardtitle">Delivery quality by thematic area — % passing every check</div>{quality_rows(quality_by_area)}</div>
      <div class="grid2 mt16">
        <div class="card"><div class="cardtitle">Delivery flags</div>{checkitems(delivery_flags)}</div>
        <div class="card"><div class="cardtitle">Possible duplicates</div><div style="display:flex;align-items:baseline;gap:10px"><div class="score" style="color:#E0A21E">{dup}</div><div class="muted">requests share a "requested-for + short description" with an earlier request</div></div></div>
      </div>
      {req_table('Requests needing cleanup', flagRecords[:14], 'Flag', '#C0453F', cols=['Case','Country','Description','Thematic area','Exp. completion','Status','State','TA lead','Flag'])}
    </div>

    <!-- closure -->
    <div class="subpanel-dq" id="close" style="display:none">
      {panelhead('Overdue, at-risk & closure', 'Active requests past or near their target date, and completed work not yet closed out.')}
      <div class="grid3">
        {hero('#FBF0EF', '#F0D2CF', '#B0453F', len(dq_overdue), '#C0453F', 'Overdue', 'active requests past their expected completion date.', '#8A5450')}
        <div class="minicard"><div class="cardtitle">Overdue severity</div><div style="margin-top:6px">{bucket_bars(dq_ob, label_w=92)}</div></div>
        <div class="minicard"><div class="cardtitle">At risk (next 30 days)</div><div style="display:flex;align-items:baseline;gap:10px;margin-top:6px"><div class="score" style="color:#E0A21E">{len(at_risk)}</div><div class="muted">due within 30 days and not yet complete</div></div></div>
      </div>
      <div class="card mt16"><div class="cardtitle">Overdue by thematic area</div>{barlist(dq_overdue_area, '#C0453F', '#F2EAE9', label_w=150)}</div>
      {req_table('Most overdue requests', dq_overdue[:14], 'Days over', '#C0453F', cols=['Case','Country','Description','Thematic area','Exp. completion','Status','State','TA lead','Days over'])}
      {req_table('Completed / discontinued but not closed', not_closed[:14], 'Outcome', '#E0A21E', cols=['Case','Country','Description','Thematic area','Exp. completion','Status','State','TA lead','Outcome'])}
    </div>
  </div>

</div>
<script>
function showTop(id){{
  var ps=document.querySelectorAll('.toppanel');
  for(var i=0;i<ps.length;i++){{ ps[i].style.display = ps[i].id===id ? 'block' : 'none'; }}
  var ts=document.querySelectorAll('.tab');
  for(var j=0;j<ts.length;j++){{ ts[j].className = 'tab' + (ts[j].getAttribute('data-top')===id ? ' on' : ''); }}
  window.scrollTo(0,0);
}}
function showSub(g,id){{
  var ps=document.querySelectorAll('.subpanel-'+g);
  for(var i=0;i<ps.length;i++){{ ps[i].style.display = ps[i].id===id ? 'block' : 'none'; }}
  var ts=document.querySelectorAll('.subtab-'+g);
  for(var j=0;j<ts.length;j++){{ ts[j].className = 'subtab subtab-'+g + (ts[j].getAttribute('data-sub')===id ? ' on' : ''); }}
}}
function showLoc(id){{
  var ps=document.querySelectorAll('.locpanel');
  for(var i=0;i<ps.length;i++){{ ps[i].style.display = ps[i].getAttribute('data-loc')===id ? 'block' : 'none'; }}
  var ts=document.querySelectorAll('.loctab');
  for(var j=0;j<ts.length;j++){{ if(ts[j].getAttribute('data-loc')===id){{ ts[j].classList.add('on'); }} else {{ ts[j].classList.remove('on'); }} }}
}}
function mapTip(e,id){{
  var t=document.getElementById('maptip'), s=document.getElementById('tip-'+id);
  if(!t||!s) return;
  t.innerHTML=s.innerHTML; t.style.display='block'; mapTipMove(e);
}}
function mapTipMove(e){{
  var t=document.getElementById('maptip'); if(t.style.display==='none') return;
  var x=e.clientX+16, y=e.clientY+16;
  if(x+t.offsetWidth>window.innerWidth-8) x=e.clientX-t.offsetWidth-16;
  if(y+t.offsetHeight>window.innerHeight-8) y=window.innerHeight-t.offsetHeight-8;
  t.style.left=x+'px'; t.style.top=Math.max(8,y)+'px';
}}
function mapTipHide(){{ document.getElementById('maptip').style.display='none'; }}
function showTbl(id){{
  var bs=document.querySelectorAll('.dtblbox');
  for(var i=0;i<bs.length;i++){{ bs[i].style.display = bs[i].getAttribute('data-tbl')===id ? 'block' : 'none'; }}
  var ts=document.querySelectorAll('.dtoggle');
  for(var j=0;j<ts.length;j++){{ if(ts[j].getAttribute('data-tbl')===id){{ ts[j].classList.add('on'); }} else {{ ts[j].classList.remove('on'); }} }}
}}
function showFlow(key){{
  var bs=document.querySelectorAll('.flowbarbox');
  for(var i=0;i<bs.length;i++){{ bs[i].style.display = bs[i].getAttribute('data-flow')===key ? 'block' : 'none'; }}
  var ns=document.querySelectorAll('.flownode');
  for(var j=0;j<ns.length;j++){{ if(ns[j].getAttribute('data-flow')===key){{ ns[j].classList.add('on'); }} else {{ ns[j].classList.remove('on'); }} }}
}}
function dotTip(e,el){{
  var t=document.getElementById('maptip'); if(!t) return;
  var n=el.getAttribute('data-n');
  t.innerHTML='<div class="maptip-title" style="margin-bottom:0"><span class="mtdot" style="background:#6C7B8C;border-radius:50%"></span><span id="dtname"></span></div>'
    +'<div class="maptip-sub" style="margin:4px 0 0">'+n+' request'+(n==='1'?'':'s')+' received</div>';
  document.getElementById('dtname').textContent=el.getAttribute('data-name');
  t.style.display='block'; mapTipMove(e);
}}
var selHub=null;
function selectHub(e,key){{ e.stopPropagation(); selHub=(selHub===key)?null:key; applyHub(); }}
function clearHub(){{ if(selHub!==null){{ selHub=null; applyHub(); }} }}
function applyHub(){{
  var arcs=document.querySelectorAll('.wmarc');
  for(var i=0;i<arcs.length;i++){{ var a=arcs[i];
    if(selHub===null){{ a.style.opacity=a.getAttribute('data-op'); a.style.strokeWidth=a.getAttribute('data-w'); }}
    else if(a.getAttribute('data-hub')===selHub){{ a.style.opacity='0.95'; a.style.strokeWidth=(parseFloat(a.getAttribute('data-w'))+0.7).toFixed(2); }}
    else {{ a.style.opacity='0.04'; }}
  }}
  var dots=document.querySelectorAll('.wmdot');
  for(var j=0;j<dots.length;j++){{ var d=dots[j];
    if(selHub===null){{ d.style.opacity='0.9'; d.setAttribute('r','2.3'); }}
    else if((' '+d.getAttribute('data-hubs')+' ').indexOf(' '+selHub+' ')>=0){{ d.style.opacity='1'; d.setAttribute('r','3.2'); }}
    else {{ d.style.opacity='0.12'; d.setAttribute('r','2.3'); }}
  }}
  var bubs=document.querySelectorAll('.wmbub');
  for(var k=0;k<bubs.length;k++){{ bubs[k].style.opacity=(selHub===null||bubs[k].getAttribute('data-hub')===selHub)?'':'0.28'; }}
  // drive the "By CoE location" graph below: selected hub, or Nairobi by default
  showLoc(selHub || 'nairobi');
  var hint=document.getElementById('wmhint');
  if(hint) hint.textContent = selHub===null ? hint.getAttribute('data-idle')
    : 'Highlighting the countries this duty station supports — click it again, or the map, to reset.';
}}
(function(){{
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var nums = document.querySelectorAll('.flownum');
  for(var i=0;i<nums.length;i++){{ (function(el,idx){{
    var target = parseInt(el.getAttribute('data-val'),10) || 0;
    if(reduce){{ el.textContent = target; return; }}
    el.textContent = '0';
    var dur = 750, delay = idx*100, t0 = null;
    function step(ts){{
      if(t0===null) t0 = ts;
      var p = Math.min(1,(ts-t0)/dur);
      var e = 1 - Math.pow(1-p,3);
      el.textContent = Math.round(e*target);
      if(p<1) requestAnimationFrame(step); else el.textContent = target;
    }}
    setTimeout(function(){{ requestAnimationFrame(step); }}, delay);
  }})(nums[i],i); }}
}})();
</script>
</body></html>'''

with open(f'{OUT}/nutrition-ta-dashboard.html', 'w', encoding='utf-8') as f:
    f.write(PAGE)
print('wrote', f'{OUT}/nutrition-ta-dashboard.html', f'({len(PAGE)} bytes)')

# Artifact-friendly partial: Artifacts inject their own <!doctype>/<head>/<body>,
# so emit just the <style> block plus the page content (no document wrappers).
style = PAGE[PAGE.index('<style>'):PAGE.index('</style>') + len('</style>')]
inner = PAGE[PAGE.index('<div class="wrap">'):PAGE.index('</body>')]
with open(f'{OUT}/nutrition-ta-dashboard.artifact.html', 'w', encoding='utf-8') as f:
    f.write(style + '\n' + inner)
print('wrote', f'{OUT}/nutrition-ta-dashboard.artifact.html')

print('PERF universe:', len(PERF), '| active:', len(active), '| overdue:', len(overdue),
      '| onTrack:', onTrack, '| recent:', len(recent))
print('DQ: setup', len(setupSet), 'delivery', delN, 'score', f'{score}%',
      'flags', len(flagRecords), 'dq_overdue', len(dq_overdue), 'not_closed', len(not_closed))
