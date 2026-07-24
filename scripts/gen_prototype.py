#!/usr/bin/env python3
"""Generate a self-contained HTML prototype of the nutrition TA dashboard
(thematic areas, no regions, staff-location -> supported-country flow) for
iterating the look in Claude Design. Data-driven from the committed JSON."""
import json, os, math, html
from collections import Counter, defaultdict

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app', 'src', 'data')
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'design')
os.makedirs(OUT, exist_ok=True)

cases = json.load(open(f'{ROOT}/cases.json'))
staff = json.load(open(f'{ROOT}/staff.json'))
TODAY = json.load(open(f'{ROOT}/today.json'))
by_name = {s['name']: s for s in staff}

STATUS_ORDER = ['0%', '25%', '50%', '75%', '100%', 'Unassigned']
STATUS_COLORS = {'0%': '#D6E0E8', '25%': '#9CC6E0', '50%': '#5BA3D0',
                 '75%': '#2C7DB5', '100%': '#0B5A8A', 'Discontinued': '#9AA7B2',
                 'Unassigned': '#E0A21E'}

# ---- enrich cases with lead thematic area + location ----
for c in cases:
    s = by_name.get(c['lead'])
    c['area'] = s['area'] if s and s['area'] else ''
    c['loc'] = (s['location'].strip() if s and s['location'] else '') if s else ''

live = [c for c in cases if c['status'] != 'Discontinued']       # reporting universe
active = [c for c in live if c['status'] not in ('100%', 'Unassigned')]
overdue = [c for c in active if c['xc'] is not None and c['xc'] < TODAY]
ontrack = [c for c in active if not (c['xc'] is not None and c['xc'] < TODAY)]
recent = [c for c in live if (c['cr'] or c['op']) and (c['cr'] or c['op']) >= TODAY - 30]
due = [c for c in live if c['xc'] is not None and c['xc'] <= TODAY]
done_due = [c for c in due if c['status'] == '100%']
completed = [c for c in live if c['status'] == '100%']

def pct(a, b): return round(100 * a / b) if b else 0

# ---------- helpers ----------
def esc(x): return html.escape(str(x))

def stacked_segs(rows):
    """rows: list of case dicts -> list of (color, width%) by status order."""
    n = len(rows)
    segs = []
    for s in STATUS_ORDER:
        w = sum(1 for c in rows if c['status'] == s)
        if w:
            segs.append((STATUS_COLORS[s], 100 * w / n))
    return segs

def seg_html(segs, pct_of_max, h=11, track='#EEF2F6'):
    inner = ''.join(f'<span style="width:{w:.2f}%;background:{col}"></span>' for col, w in segs)
    return (f'<div class="track" style="height:{h}px;background:{track};border-radius:{h/2}px">'
            f'<div class="bar" style="height:100%;width:{pct_of_max:.1f}%;border-radius:{h/2}px">{inner}</div></div>')

# ============ SECTION: thematic areas ============
area_groups = defaultdict(list)
for c in live:
    area_groups[c['area'] or '(unassigned lead)'].append(c)
area_rows = sorted(area_groups.items(), key=lambda kv: -len(kv[1]))
area_max = max(len(v) for _, v in area_rows)

area_html = ''
for name, rows in area_rows:
    leads = len({c['lead'] for c in rows if c['lead']})
    area_html += f'''
      <div class="arearow">
        <div class="arealabel">{esc(name)}</div>
        {seg_html(stacked_segs(rows), 100*len(rows)/area_max, h=13)}
        <div class="an">{len(rows)}</div>
        <div class="al">{leads}</div>
      </div>'''

# ============ SECTION: where support flows ============
HUB_ORDER = ['Nairobi', 'Bangkok', 'Brussels', 'Panama', 'Canada']
hub_cases = defaultdict(list)
for c in live:
    hub = c['loc'] if c['loc'] else 'Not recorded'
    hub_cases[hub].append(c)

hub_color = {'Nairobi': '#0B6FA4', 'Bangkok': '#2E7D5B', 'Brussels': '#7A4FB0',
             'Panama': '#C87A2E', 'Canada': '#0B5A8A', 'Not recorded': '#9AA7B2'}
ordered_hubs = [h for h in HUB_ORDER if h in hub_cases] + \
               [h for h in hub_cases if h not in HUB_ORDER and h != 'Not recorded'] + \
               (['Not recorded'] if 'Not recorded' in hub_cases else [])

n_hubs = len([h for h in ordered_hubs if h != 'Not recorded'])
n_countries = len({c['office'] for c in live if c['office']})

flow_html = ''
for hub in ordered_hubs:
    rows = hub_cases[hub]
    dest = Counter(c['office'] or '— global / HQ —' for c in rows)
    ndest = len({c['office'] for c in rows if c['office']})
    col = hub_color.get(hub, '#5B7186')
    chips = ''
    for country, cnt in dest.most_common(6):
        chips += f'<span class="destchip">{esc(country)} <b>{cnt}</b></span>'
    more = len(dest) - 6
    if more > 0:
        chips += f'<span class="destchip muted">+{more} more</span>'
    note = f'{ndest} countries supported' if hub != 'Not recorded' else 'lead duty station not in roster'
    flow_html += f'''
      <div class="hubcard">
        <div class="hubhead">
          <span class="hubdot" style="background:{col}"></span>
          <span class="hubname">{esc(hub)}</span>
          <span class="hubcount" style="color:{col}">{len(rows)}</span>
        </div>
        <div class="hubsub">{note}</div>
        <div class="destwrap">{chips}</div>
      </div>'''

# ============ SECTION: workload by lead ============
lead_groups = defaultdict(list)
for c in live:
    if c['lead']:
        lead_groups[c['lead']].append(c)
lead_rows = sorted(lead_groups.items(), key=lambda kv: -len(kv[1]))
lead_max = max(len(v) for _, v in lead_rows)
counts = [len(v) for _, v in lead_rows]
load_min, load_max = min(counts), max(counts)
load_avg = sum(counts) / len(counts)

lead_html = ''
for name, rows in lead_rows:
    area = rows[0]['area']
    lead_html += f'''
      <div class="leadrow">
        <div class="leadlabel"><div class="leadname">{esc(name)}</div><div class="leadarea">{esc(area)}</div></div>
        {seg_html(stacked_segs(rows), 100*len(rows)/lead_max, h=11)}
        <div class="ln">{len(rows)}</div>
      </div>'''

# ============ status legend ============
legend_html = ''.join(
    f'<div class="lg"><span class="lgdot" style="background:{STATUS_COLORS[s]}"></span>{s}</div>'
    for s in STATUS_ORDER)

# ============ KPI strip ============
kpis = [
    ('Total requests', str(len(live)), 'active nutrition TA requests', '#0B6FA4', '#0F2238'),
    ('Received last 30 days', str(len(recent)), 'new since 24 Jun 2026', '#1CABE2', '#0F2238'),
    ('Active &amp; on track', str(len(ontrack)), 'in progress, not overdue', '#3E9CD6', '#3E9CD6'),
    ('Completed vs. target', f'{pct(len(done_due), len(due))}%', f'of {len(due)} due by today at 100%', '#2E7D5B', '#2E7D5B'),
    ('Overdue', str(len(overdue)), 'past expected completion', '#C0453F', '#C0453F'),
]
kpi_html = ''
for label, val, sub, accent, color in kpis:
    kpi_html += f'''
      <div class="kpi" style="border-top:3px solid {accent}">
        <div class="kpilabel">{label}</div>
        <div class="kpival" style="color:{color}">{val}</div>
        <div class="kpisub">{sub}</div>
      </div>'''

# overall status funnel
funnel_max = max(sum(1 for c in live if c['status'] == s) for s in STATUS_ORDER)
funnel_html = ''
for s in STATUS_ORDER:
    n = sum(1 for c in live if c['status'] == s)
    funnel_html += f'''
      <div class="funrow">
        <div class="funlabel">{s}</div>
        <div class="track" style="height:14px;background:#EEF2F6;border-radius:7px"><div style="height:100%;width:{100*n/funnel_max:.1f}%;background:{STATUS_COLORS[s]};border-radius:7px"></div></div>
        <div class="funn">{n}</div>
      </div>'''

PAGE = f'''<!-- @dsCard group="Dashboards" -->
<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nutrition TA Performance Dashboard</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:#EDF1F4; color:#0F2238;
         font-family:'Helvetica Neue',Helvetica,Arial,sans-serif; -webkit-font-smoothing:antialiased; }}
  .wrap {{ max-width:1340px; margin:0 auto; padding:0 24px 70px; }}
  .track {{ overflow:hidden; }}
  .bar {{ display:flex; overflow:hidden; }}
  .bar span {{ display:block; }}

  /* header */
  header.hd {{ padding:30px 0 18px; display:flex; justify-content:space-between; align-items:flex-end; gap:24px; flex-wrap:wrap; }}
  .eyebrow {{ font-size:11px; letter-spacing:.16em; text-transform:uppercase; color:#1CABE2; font-weight:700; }}
  .h1 {{ font-size:27px; font-weight:700; letter-spacing:-.01em; margin-top:6px; }}
  .meta {{ text-align:right; font-size:12px; color:#5B7186; line-height:1.6; }}
  .meta b {{ color:#0F2238; }}

  /* kpi */
  .kpistrip {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:14px; margin-top:6px; }}
  .kpi {{ background:#fff; border:1px solid #E3E9EF; border-radius:10px; padding:16px 18px; }}
  .kpilabel {{ font-size:12px; color:#5B7186; font-weight:600; }}
  .kpival {{ font-size:34px; font-weight:700; letter-spacing:-.02em; line-height:1.1; margin:6px 0 4px; font-variant-numeric:tabular-nums; }}
  .kpisub {{ font-size:11.5px; color:#9AA7B2; }}

  /* section heading */
  .sec {{ display:flex; align-items:center; gap:12px; margin:34px 0 14px; }}
  .secn {{ width:26px; height:26px; border-radius:7px; background:#0B6FA4; color:#fff; font-size:13px; font-weight:700;
          display:flex; align-items:center; justify-content:center; }}
  .sectitle {{ font-size:18px; font-weight:700; letter-spacing:-.01em; }}
  .secsub {{ font-size:13px; color:#5B7186; margin-left:auto; }}

  .card {{ background:#fff; border:1px solid #E3E9EF; border-radius:10px; padding:20px 22px; }}
  .cardtitle {{ font-size:13.5px; font-weight:700; margin-bottom:4px; }}
  .cardnote {{ font-size:12px; color:#8A98A6; line-height:1.55; margin-top:16px; border-top:1px solid #F1F4F7; padding-top:12px; }}

  /* legend */
  .legend {{ display:flex; flex-wrap:wrap; gap:10px 16px; margin:12px 0 18px; }}
  .lg {{ display:flex; align-items:center; gap:6px; font-size:11.5px; color:#43586B; }}
  .lgdot {{ width:11px; height:11px; border-radius:3px; display:inline-block; }}

  /* thematic area rows */
  .areahead, .arearow {{ display:grid; grid-template-columns:230px 1fr 44px 52px; gap:12px; align-items:center; }}
  .areahead {{ font-size:10px; letter-spacing:.05em; text-transform:uppercase; color:#9AA7B2; font-weight:700; margin-bottom:10px; }}
  .areahead .r {{ text-align:right; }}
  .arearow {{ margin-bottom:12px; }}
  .arealabel {{ font-size:12.5px; color:#43586B; font-weight:600; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .an {{ text-align:right; font-weight:700; font-size:13px; font-variant-numeric:tabular-nums; }}
  .al {{ text-align:right; font-size:12.5px; font-weight:700; color:#0B6FA4; font-variant-numeric:tabular-nums; }}

  /* flow */
  .flowintro {{ font-size:13px; color:#5B7186; margin-bottom:16px; }}
  .flowintro b {{ color:#0B6FA4; font-size:15px; }}
  .hubgrid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:14px; }}
  .hubcard {{ background:#fff; border:1px solid #E3E9EF; border-radius:10px; padding:16px 18px; }}
  .hubhead {{ display:flex; align-items:center; gap:9px; }}
  .hubdot {{ width:12px; height:12px; border-radius:4px; }}
  .hubname {{ font-size:14.5px; font-weight:700; }}
  .hubcount {{ margin-left:auto; font-size:20px; font-weight:700; font-variant-numeric:tabular-nums; }}
  .hubsub {{ font-size:11.5px; color:#9AA7B2; margin:3px 0 12px 21px; }}
  .destwrap {{ display:flex; flex-wrap:wrap; gap:6px; }}
  .destchip {{ font-size:11.5px; color:#43586B; background:#F1F5F9; border:1px solid #E3E9EF; border-radius:999px; padding:4px 10px; }}
  .destchip b {{ color:#0B6FA4; }}
  .destchip.muted {{ color:#9AA7B2; background:transparent; }}

  /* workload */
  .leadgrid {{ column-count:2; column-gap:40px; }}
  @media (max-width:820px) {{ .leadgrid {{ column-count:1; }} }}
  .leadrow {{ display:grid; grid-template-columns:190px 1fr 34px; gap:10px; align-items:center; break-inside:avoid; margin-bottom:11px; }}
  .leadlabel {{ white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .leadname {{ font-size:12px; color:#43586B; overflow:hidden; text-overflow:ellipsis; }}
  .leadarea {{ font-size:10.5px; color:#9AA7B2; overflow:hidden; text-overflow:ellipsis; }}
  .ln {{ text-align:right; font-weight:700; font-size:12px; font-variant-numeric:tabular-nums; }}
  .loadstat {{ display:flex; gap:12px; margin:4px 0 4px; }}
  .loadbox {{ flex:1; border-radius:9px; padding:13px 16px; }}
  .loadlabel {{ font-size:10.5px; letter-spacing:.08em; text-transform:uppercase; font-weight:700; }}
  .loadval {{ font-size:26px; font-weight:700; font-variant-numeric:tabular-nums; line-height:1.15; margin-top:3px; }}
  .loadsub {{ font-size:11px; }}

  /* funnel */
  .funrow {{ display:grid; grid-template-columns:90px 1fr 40px; gap:12px; align-items:center; margin-bottom:9px; }}
  .funlabel {{ font-size:12px; color:#43586B; font-weight:600; }}
  .funn {{ text-align:right; font-weight:700; font-size:12.5px; font-variant-numeric:tabular-nums; }}

  .grid2 {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(min(340px,100%),1fr)); gap:16px; align-items:start; }}
</style></head>
<body>
<div class="wrap">

  <header class="hd">
    <div>
      <div class="eyebrow">Child Nutrition &amp; Development &middot; Technical Assistance</div>
      <div class="h1">Nutrition TA Performance Dashboard</div>
    </div>
    <div class="meta">
      <div><b>{len(live)}</b> nutrition TA requests &middot; <b>{len(staff)}</b> team members</div>
      <div>Created Jan&ndash;Jul 2026 &middot; as of 24 Jul 2026</div>
    </div>
  </header>

  <div class="kpistrip">{kpi_html}
  </div>

  <!-- SECTION 1: thematic areas -->
  <div class="sec"><div class="secn">1</div><div class="sectitle">Requests by thematic area</div>
    <div class="secsub">{len(area_rows)} thematic areas &middot; bar coloured by implementation status</div></div>
  <div class="card">
    <div class="legend">{legend_html}</div>
    <div class="areahead"><div>Thematic area</div><div></div><div class="r">TAs</div><div class="r">Leads</div></div>
    {area_html}
    <div class="cardnote"><b style="color:#5B7186">What this says:</b> with the whole dashboard now scoped to one team, thematic area &mdash; not practice or region &mdash; is the meaningful way to see where nutrition TA demand concentrates. <b>Food Systems for Children</b> and <b>Maternal Nutrition</b> carry the largest share.</div>
  </div>

  <!-- SECTION 2: where support flows -->
  <div class="sec"><div class="secn">2</div><div class="sectitle">Where support flows</div>
    <div class="secsub">from staff duty station &rarr; supported country</div></div>
  <div class="card">
    <div class="flowintro"><b>{n_hubs}</b> support hubs providing technical assistance to <b>{n_countries}</b> countries. Origin is each request's TA lead duty station; destination is the country office being supported.</div>
    <div class="hubgrid">{flow_html}
    </div>
    <div class="cardnote"><b style="color:#5B7186">What this says:</b> most nutrition TA is delivered remotely across regions &mdash; a lead in Nairobi or Bangkok supporting country offices worldwide. The <b>Not recorded</b> group is requests whose lead has no duty station in the staff roster; capturing that would complete the origin picture.</div>
  </div>

  <!-- SECTION 3: workload -->
  <div class="sec"><div class="secn">3</div><div class="sectitle">Team workload</div>
    <div class="secsub">{len(lead_rows)} TA leads &middot; requests per lead</div></div>
  <div class="grid2">
    <div class="card">
      <div class="cardtitle">Workload spread</div>
      <div class="loadstat">
        <div class="loadbox" style="background:#F6F8FA;border:1px solid #EDF1F4">
          <div class="loadlabel" style="color:#7A8C9C">Minimum</div>
          <div class="loadval" style="color:#2E7D5B">{load_min}</div>
          <div class="loadsub" style="color:#9AA7B2">lightest lead</div></div>
        <div class="loadbox" style="background:#EEF6FB;border:1px solid #CFE6F2">
          <div class="loadlabel" style="color:#2C5A75">Average</div>
          <div class="loadval" style="color:#0B6FA4">{load_avg:.1f}</div>
          <div class="loadsub" style="color:#7FA6BE">requests per lead</div></div>
        <div class="loadbox" style="background:#FBF0EF;border:1px solid #F0D2CF">
          <div class="loadlabel" style="color:#B0453F">Maximum</div>
          <div class="loadval" style="color:#C0453F">{load_max}</div>
          <div class="loadsub" style="color:#C79490">{esc(lead_rows[0][0])}</div></div>
      </div>
      <div class="cardnote" style="margin-top:8px"><b style="color:#5B7186">What this says:</b> workload ranges from {load_min} to {load_max} requests per lead, averaging {load_avg:.1f}. Bars at right are coloured by implementation status.</div>
    </div>
    <div class="card">
      <div class="cardtitle">Overall implementation status</div>
      <div style="margin-top:14px">{funnel_html}
      </div>
    </div>
  </div>

  <div class="card" style="margin-top:16px">
    <div class="cardtitle" style="margin-bottom:16px">Requests per TA lead &mdash; coloured by status</div>
    <div class="legend">{legend_html}</div>
    <div class="leadgrid">{lead_html}
    </div>
  </div>

</div>
</body></html>'''

with open(f'{OUT}/nutrition-ta-dashboard.html', 'w', encoding='utf-8') as f:
    f.write(PAGE)
print('wrote', f'{OUT}/nutrition-ta-dashboard.html', f'({len(PAGE)} bytes)')
print('thematic areas:', len(area_rows), '| hubs:', ordered_hubs, '| leads:', len(lead_rows))
print('KPIs: total', len(live), 'recent', len(recent), 'ontrack', len(ontrack),
      'overdue', len(overdue), 'completed-vs-target', f'{pct(len(done_due),len(due))}%')
