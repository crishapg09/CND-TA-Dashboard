#!/usr/bin/env python3
"""
Extract the CND staff roster into the app's data file.

Usage:
    python scripts/extract_staff.py path/to/CND_staff.xlsx

What it does:
  1. Reads the "CND_staff" export (first sheet).
  2. Writes app/src/data/staff.json — one record per staff member (minified).

The roster links to the TA cases on staff Name = case "Assigned to" (the case
`lead`). Names, titles, thematic areas and locations are trimmed of the stray
trailing whitespace the source export carries so the join is exact.

Requires: openpyxl  (pip install openpyxl)
"""
import sys
import os
import json

# ---- source layout -------------------------------------------------------
# Header row followed by one row per staff member.
EXPECTED_HEADER = ('Name', 'Title', 'Thematic Area', 'Location')

C_NAME, C_TITLE, C_AREA, C_LOCATION = 0, 1, 2, 3


def s(v):
    """Trimmed string; None -> ''. Collapses the export's stray trailing spaces."""
    return '' if v is None else str(v).strip()


def load_rows(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb[wb.sheetnames[0]]
    ws.reset_dimensions()
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    header = tuple(s(v) for v in rows[0][:len(EXPECTED_HEADER)])
    if header != EXPECTED_HEADER:
        raise SystemExit(
            'ERROR: unexpected staff layout.\n'
            f'  expected {EXPECTED_HEADER}\n'
            f'  got      {header}\n'
            'The column mapping in this script would need updating.'
        )
    return rows[1:]


def build(r):
    """One roster row -> one Staff record (see app/src/data/types.ts)."""
    return {
        'name': s(r[C_NAME]),
        'title': s(r[C_TITLE]) if len(r) > C_TITLE else '',
        'area': s(r[C_AREA]) if len(r) > C_AREA else '',
        'location': s(r[C_LOCATION]) if len(r) > C_LOCATION else '',
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/extract_staff.py <CND_staff.xlsx>')
    src = sys.argv[1]
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(repo_root, 'app', 'src', 'data')

    rows = load_rows(src)
    records = [build(r) for r in rows if r and s(r[C_NAME])]
    # De-duplicate on name, keeping the first occurrence.
    seen = set()
    unique = []
    for rec in records:
        if rec['name'] in seen:
            continue
        seen.add(rec['name'])
        unique.append(rec)

    with open(os.path.join(data_dir, 'staff.json'), 'w', encoding='utf-8') as f:
        json.dump(unique, f, ensure_ascii=False, separators=(',', ':'))

    from collections import Counter
    areas = dict(Counter(r['area'] for r in unique))
    print(f'Wrote {len(unique):,} staff records')
    print(f'Thematic areas: {areas}')


if __name__ == '__main__':
    main()
