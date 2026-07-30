# Nutrition TA Management Dashboard — Power BI

Rebuild of the Nutrition TA dashboard in Power BI. **Phase 1** (this pack) covers
everything that maps to *native* Power BI visuals — KPIs, thematic-area
breakdowns, the month trend, workload and tables. **Phase 2** (the custom
"Where support flows" arc map) is scaffolded here but built later once we're
connected to Power BI directly.

The reference web dashboard lives in the sibling repo (`cnd-ta-dashboard`,
`design/nutrition-ta-dashboard.html`) — use it as the visual target.

---

## 1. Data model

Two tables, one relationship. This join is the whole foundation.

| Table | Grain | Source |
|-------|-------|--------|
| **Cases** | one row per TA request | ServiceNow *Case Report* export (`sn_customerservice_case.xlsx`) |
| **Staff** | one row per person | CND staff roster (`CND_staff.xlsx`) — Name, Title, Thematic Area, Duty Station |
| **Calendar** | one row per day | a standard date table (Phase-1 optional, needed for the month trend) |

**Relationships**
- `Cases[Assigned to]` → `Staff[Name]` (many-to-one, single direction)
- `Calendar[Date]` → `Cases[Opened]` (active)
- `Calendar[Date]` → `Cases[Closed]` (inactive — used by the "Completed by close month" measure)

**Calculated columns on Cases** (add before the measures):
```DAX
Thematic Area = RELATED ( Staff[Thematic Area] )
Duty Station  = RELATED ( Staff[Duty Station] )
Include =
    NOT ( Cases[Resolution code] IN
          { "Voided/Canceled", "Duplicate Issue",
            "Discontinued — did not need to proceed" } )
```
`Include = TRUE` reproduces the web dashboard's row filtering (drops voided /
duplicate / dropped-before-work requests). Every measure already applies it.

> **Roster note.** The staff roster carries the enriched **Duty Station** for
> each person (Nairobi, Bangkok, Amman, Brussels, Panama, New York). Keep that
> column — the thematic-area grouping and the flow-map origins both depend on it.

---

## 2. Measures

Import `measures.dax`. It defines: `As Of Date`, `Total requests`, `Completed`,
`Active (in progress)`, `On track`, `Overdue`, `Received last 30 days`,
`Completed vs target %`, `Active on target %`, `Opened`,
`Completed (by close month)`, `Distinct TA leads`, `Avg requests per lead`,
`Countries supported`, `Origins resolved`, and `Overdue in band`.

`As Of Date` matches the web dashboard: the latest activity date in the data
(max of Created / Opened / Updated). Swap it for `TODAY()` if you'd rather the
report track the calendar.

---

## 3. Build guide — native visuals (Management page)

| Dashboard element | Power BI visual | Fields / measures |
|---|---|---|
| KPI strip | **Card** ×6 | `Total requests`, `Received last 30 days`, `On track`, `Completed vs target %`, `Active on target %`, `Overdue` |
| Opened vs completed by month | **Clustered column** | Axis `Calendar[Month]`; values `Opened`, `Completed (by close month)` |
| New / On track / Completed **by thematic area** | **Clustered bar** ×3 | Axis `Staff[Thematic Area]`; value `Received last 30 days` / `On track` / `Completed`. Sort descending. |
| Completed card (green) | **Card** | `Completed` — set the data colour to `#2E7D5B` |
| Requests by thematic area & status | **Stacked bar** | Axis `Staff[Thematic Area]`; legend `Cases[Implementation Status]`; value `Total requests` |
| Thematic area → staff (the collapsible squares) | **Matrix** | Rows `Staff[Thematic Area]` then `Staff[Name]`; value `Total requests`; turn on **row drill / expand**. Optional: conditional-format the value cell by status. |
| Workload spread | **Card**s + **bar** | `Distinct TA leads`, `Avg requests per lead`; bar: axis `Staff[Name]`, value `Total requests` |
| Newest / Overdue / Cleanup tables | **Table** | `Case`, `Office/Division`, `Short description`, `Thematic Area`, `Expected Completion Date`, `Implementation Status`, `Assigned to` + the relevant measure |
| Overdue severity | **Clustered bar** | Add the `Severity` disconnected table (see `measures.dax` §6); axis `Severity[Band]`, value `Overdue in band` |

**Interactivity comes for free:** drop a **slicer** on `Staff[Duty Station]` (or
`Staff[Thematic Area]`). Clicking it cross-filters every visual — this replaces
the web dashboard's custom click-to-highlight, and it's more powerful because it
filters the whole page at once.

### Data Quality page
Reuse the same model: cards for `Unassigned`, in-setup and delivery counts;
completeness = `DIVIDE(COUNTROWS(non-blank field), Total)` per field; tables for
the flag lists. (Ask and I'll add the DAX for these once the Management page is up.)

---

## 4. Refresh (the real win)

Instead of exporting XLSX and re-running scripts:
- **Cases** → connect Power BI directly to **ServiceNow** (REST/OData connector),
  filtered to `Global Practice = "Child Nutrition and Development"`.
- **Staff** → point at the roster's home (SharePoint / Excel / a table).
- Schedule a refresh in the Power BI Service. The dates auto-track because
  `As Of Date` is derived from the data.

Until the live connectors are set up, just *Get Data → Excel* on the two files.

---

## 5. Phase 2 — the custom "Where support flows" map

The arc map needs a custom build (native maps don't draw weighted origin→
destination arcs the way the web version does). The plan: render it from a
**DAX measure that returns inline SVG**, shown with the **HTML Content** custom
visual. To keep it robust (many HTML visuals strip `<script>`), the geometry is
**pre-projected to pixel coordinates** so the measure only concatenates SVG —
no projection maths, no JS.

This pack already ships the pre-projected geometry:

| File | Import as | Contents |
|------|-----------|----------|
| `Stations.csv` | table **Stations** | 6 duty stations → `PxX,PxY`, colour, label anchor |
| `Geo.csv` | table **Geo** | every supported country office → `PxX,PxY` centroid |
| `MapBase.csv` | 1-row table **MapBase** | the static world silhouette as one inline `<path>` (viewBox `0 0 1000 552`) |

`build_powerbi_assets.py` regenerates all three from the committed data (shares
one Robinson projection with the web map, so everything registers). The DAX
measure that assembles the SVG comes next — we'll write it together against your
live model so the table/column names match exactly.

---

## Files
```
powerbi/
  README.md                 this file
  measures.dax              phase-1 measures (native visuals)
  Stations.csv              pre-projected duty stations   (phase-2 map)
  Geo.csv                   pre-projected country offices (phase-2 map)
  MapBase.csv               static world silhouette SVG   (phase-2 map)
  build_powerbi_assets.py   regenerates the three CSVs from the data
```
