#!/usr/bin/env python3
"""Stitch the per-practice dashboard bundles behind a top-level Global Practice
filter (Nutrition / Climate).

gen_prototype.py renders ONE practice at a time; run with GP=n it emits the
Child Nutrition & Development view, with GP=c the Climate Resilience for
Children view, and alongside each it writes design/_gp_<GP>.bundle.json holding
that practice's page body, its shared JS functions and its country-profile data.

This script runs the generator once per practice, then assembles a single page:
a persistent "Global Practice" toggle at the very top, both practice bodies held
inert inside <template> elements, and one shared <script>. Selecting a practice
mounts that body into #gpmount and re-inits it, so only one practice is ever
live in the DOM — no duplicate ids, no cross-practice bleed, and the existing
per-practice JS runs unchanged.

Outputs (in design/):
  nutrition-ta-dashboard.html            full standalone page
  nutrition-ta-dashboard.artifact.html   style + body only (for Claude Artifacts)
"""
import json, os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'design')
GEN = os.path.join(HERE, 'gen_prototype.py')

# Order controls the toggle order and which practice mounts first.
PRACTICES = ['n', 'c']


def run(gp):
    env = dict(os.environ, GP=gp)
    subprocess.run([sys.executable, GEN], check=True, env=env)
    with open(f'{OUT}/_gp_{gp}.bundle.json', encoding='utf-8') as f:
        return json.load(f)


def build():
    bundles = {gp: run(gp) for gp in PRACTICES}
    first = PRACTICES[0]
    style = bundles[first]['style']                 # identical across practices
    js_funcs = bundles[first]['js_funcs']           # identical across practices

    country_all = json.dumps({gp: bundles[gp]['country'] for gp in PRACTICES},
                             ensure_ascii=False)
    templates = '\n'.join(
        f'<template id="tpl-{gp}">{bundles[gp]["wrap"]}</template>'
        for gp in PRACTICES)
    buttons = '\n      '.join(
        f'<button class="gpbtn{" on" if gp == first else ""}" data-gp="{gp}" '
        f'onclick="setGP(\'{gp}\')">{bundles[gp]["label"]}</button>'
        for gp in PRACTICES)

    gp_css = '''
  .gpouter { max-width:1340px; margin:0 auto; padding:22px 24px 0; }
  .gpbar { display:flex; align-items:center; gap:14px; flex-wrap:wrap;
           background:#0F2238; border-radius:14px; padding:14px 18px;
           box-shadow:0 2px 10px rgba(15,34,56,.14); }
  .gpbar .gplbl { font-size:11px; letter-spacing:.16em; text-transform:uppercase;
                  color:#8FB9D6; font-weight:700; }
  .gpbtn { appearance:none; border:1px solid rgba(255,255,255,.22);
           background:transparent; color:#CFE0EC; font:inherit; font-weight:600;
           font-size:14px; padding:8px 20px; border-radius:9px; cursor:pointer;
           transition:background .12s,color .12s,border-color .12s; }
  .gpbtn:hover { border-color:rgba(255,255,255,.5); color:#fff; }
  .gpbtn.on { background:#1CABE2; border-color:#1CABE2; color:#fff; }
  @media (max-width:560px){ .gpbar{ gap:10px; } .gpbtn{ padding:8px 14px; } }
'''

    script = f'''<script>
{js_funcs}
var COUNTRY_ALL={country_all};
var COUNTRY_DATA=COUNTRY_ALL['{first}'];
var CURRENT_GP=null;
function setGP(gp){{
  CURRENT_GP=gp;
  document.getElementById('gpmount').innerHTML=document.getElementById('tpl-'+gp).innerHTML;
  COUNTRY_DATA=COUNTRY_ALL[gp];
  var bs=document.querySelectorAll('.gpbtn');
  for(var i=0;i<bs.length;i++){{ bs[i].classList.toggle('on', bs[i].getAttribute('data-gp')===gp); }}
  __initGP();
  window.scrollTo(0,0);
}}
setGP('{first}');
</script>'''

    body = (f'<div class="gpouter"><div class="gpbar">'
            f'<span class="gplbl">Global Practice</span>\n      {buttons}\n'
            f'</div></div>\n{templates}\n<div id="gpmount"></div>')

    # style already ends with </style>; splice the GP css in just before the close.
    style_full = style.replace('</style>', gp_css + '</style>', 1)

    page = (
        '<!-- @dsCard group="Dashboards" -->\n<!doctype html>\n'
        '<html lang="en"><head><meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>TA Management Dashboard</title>\n'
        f'{style_full}\n</head><body>\n{body}\n{script}\n</body></html>')

    with open(f'{OUT}/nutrition-ta-dashboard.html', 'w', encoding='utf-8') as f:
        f.write(page)
    print('wrote', f'{OUT}/nutrition-ta-dashboard.html', f'({len(page):,} bytes)')

    # Artifact partial: Artifacts inject their own doctype/head/body wrappers.
    artifact = style_full + '\n' + body + '\n' + script
    with open(f'{OUT}/nutrition-ta-dashboard.artifact.html', 'w', encoding='utf-8') as f:
        f.write(artifact)
    print('wrote', f'{OUT}/nutrition-ta-dashboard.artifact.html', f'({len(artifact):,} bytes)')


if __name__ == '__main__':
    build()
