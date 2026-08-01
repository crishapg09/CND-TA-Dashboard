import type { TACase } from '../data/types';
import { STATUS_ORDER, STATUS_COLORS, statusChipStyle } from './status';
import { mean, fmtNum, pct } from './format';
import { groupBy, toBars, optionCounts, type ColoredBarRow } from './aggregate';
import { formatDate, monthIndex2026, MONTHS } from './dates';

export type ViewId = 'overview' | 'quality';

export interface FilterState {
  view: ViewId;
  type: string;
  regions: string[];
  practice: string;
  office: string;
  statuses: string[];
  quarters: string[];
  lead: string;
}

export const INITIAL_FILTERS: FilterState = {
  view: 'overview',
  type: 'All',
  regions: [],
  practice: 'All',
  office: 'All',
  statuses: [],
  quarters: [],
  lead: 'All',
};

export function matchesFilters(c: TACase, s: FilterState): boolean {
  if (s.type !== 'All' && c.type !== s.type) return false;
  if (s.regions.length && !s.regions.includes(c.region)) return false;
  if (s.practice !== 'All' && c.practice !== s.practice) return false;
  if (s.office !== 'All' && c.office !== s.office) return false;
  if (s.statuses.length && !s.statuses.includes(c.status)) return false;
  if (s.quarters.length && !s.quarters.includes(c.q || '')) return false;
  if (s.lead !== 'All' && c.lead !== s.lead) return false;
  return true;
}

export interface SelectOption { value: string; label: string; }
export interface KPI { label: string; value: string; sub: string; accent: string; color: string; }
export interface StatusChip { label: string; dot: string; on: boolean; bg: string; fg: string; bd: string; }
export interface ToggleButton { label: string; on: boolean; bg: string; fg: string; bd?: string; }
export interface StackSeg { w: number; color: string; }
export interface StackedRow { label: string; n: number; barPct: number; segs: StackSeg[]; leads?: number; sub?: string; }
export interface MonthBar { label: string; in: number; done: number; inH: number; doneH: number; hasNote: boolean; }
export interface BucketRow { label: string; n: number; color: string; pct: number; }
export interface LegendItem { label: string; color: string; }
export interface OverdueTableRow {
  id: string; country: string; full: string; practice: string; expDate: string; status: string;
  lead: string; leadColor: string; state: string; stateBg: string; stateFg: string; days: string; stBg: string; stFg: string;
}
export interface NoLeadTableRow { id: string; desc: string; practice: string; region: string; status: string; stBg: string; stFg: string; }
export interface CheckItem { n: string; label: string; sub: string; color: string; }
export interface CompletenessRow { label: string; pct: number; pctLabel: string; color: string; }
export interface QualityRegionRow { label: string; pct: number; pctLabel: string; color: string; }
export interface ObjPracticeRow { label: string; n: number; pct: number; pctLabel: string; color: string; }

export interface Dashboard {
  isOverview: boolean;
  isQuality: boolean;
  viewTabs: ToggleButton[];

  metaTotal: string;
  coFrom: string;
  coUnassigned: string;
  filterTitle: string;
  total: string;
  pctOfAll: string;

  typeBtns: ToggleButton[];
  statusChips: StatusChip[];
  quarterChips: ToggleButton[];
  regionOpts: SelectOption[];
  practiceOpts: SelectOption[];
  officeOpts: SelectOption[];

  // Performance
  kpis: KPI[];
  ioMonths: MonthBar[];
  ioOpenedTotal: string;
  ioCompletedTotal: string;
  recent: number;
  recentByRegion: ColoredBarRow[];
  recentByPractice: ColoredBarRow[];
  onTrack: number;
  onTrackByRegion: ColoredBarRow[];
  onTrackByPractice: ColoredBarRow[];
  newTable: OverdueTableRow[];

  mgmtKpis: KPI[];

  overdue: number;
  overdueByRegion: ColoredBarRow[];
  overdueByPractice: ColoredBarRow[];
  overdueBuckets: BucketRow[];
  stalledSeverity: LegendItem[];
  stalledByRegionSev: StackedRow[];
  stalledByPracticeSev: StackedRow[];
  stalledCount: string;
  overdueTableFinal: OverdueTableRow[];

  byPractice: StackedRow[];
  byRegion: StackedRow[];
  staffBars: StackedRow[];
  staffLegend: LegendItem[];
  loadN: number;
  loadMin: number;
  loadMax: number;
  loadMaxLead: string;
  loadMinCountLabel: string;
  loadAvg: string;
  avgPos: number;
  distinctStaff: number;
  unassigned: number;

  // Data Quality — stage-aware (see DataQuality)
  dq: DataQuality;
}

const notOther = (key: keyof TACase, c: TACase) => !(key === 'practice' && c.practice === 'Other');

export function computeDashboard(
  cases: TACase[],
  rawCases: TACase[],
  quarters: string[],
  today: number,
  state: FilterState,
): Dashboard {
  const TODAY = today;
  const F = cases.filter((c) => matchesFilters(c, state));
  const total = F.length;
  const ALL = cases.length;

  const activeSet = F.filter((c) => !['100%', 'Discontinued', 'Unassigned'].includes(c.status));
  // Completion against target: of the requests whose expected completion date
  // has arrived (due by today), how many are actually at 100%.
  const dueByToday = F.filter((c) => c.xc != null && (c.xc as number) <= TODAY);
  const doneByTarget = dueByToday.filter((c) => c.status === '100%').length;
  const overdueSet = activeSet
    .filter((c) => c.xc != null && c.xc < TODAY)
    .sort((a, b) => TODAY - (b.xc as number) - (TODAY - (a.xc as number)));
  const onTrack = activeSet.length - overdueSet.length;
  const onTrackSet = activeSet.filter((c) => !(c.xc != null && c.xc < TODAY));
  const recentSet = F.filter((c) => {
    const t = c.cr ?? c.op;
    return t != null && t >= TODAY - 30 && t <= TODAY;
  });

  // ---- table rows ----
  const rowFrom = (c: TACase, metric: string): OverdueTableRow => {
    const chip = statusChipStyle(c.status);
    return {
      id: c.id,
      country: c.office || '—',
      full: c.full || c.desc || '—',
      practice: c.practice || '—',
      expDate: formatDate(c.xc),
      status: c.status,
      lead: c.lead || '— none —',
      leadColor: c.lead ? '#43586B' : '#C0453F',
      state: c.cl ? 'Closed' : 'Open',
      stateBg: c.cl ? '#E7EEF3' : '#E6F0EA',
      stateFg: c.cl ? '#0B5A8A' : '#2E7D5B',
      days: metric,
      stBg: chip.bg,
      stFg: chip.fg,
    };
  };
  const newSet = [...recentSet].sort((a, b) => (b.cr ?? b.op)! - (a.cr ?? a.op)!);
  const newTable = newSet.map((c) => rowFrom(c, String(Math.round(TODAY - (c.cr ?? c.op)!))));
  const overdueTableFinal = overdueSet.map((c) => rowFrom(c, '+' + Math.round(TODAY - (c.xc as number))));

  // chips + toggles
  const statusChips: StatusChip[] = STATUS_ORDER.map((v) => {
    const on = state.statuses.includes(v);
    return { label: v, dot: STATUS_COLORS[v], on, bg: on ? '#16385C' : '#fff', fg: on ? '#fff' : '#43586B', bd: on ? '#16385C' : '#D5DEE6' };
  });
  const quarterChips: ToggleButton[] = quarters.map((v) => {
    const on = state.quarters.includes(v);
    return { label: v, on, bg: on ? '#0B6FA4' : '#fff', fg: on ? '#fff' : '#43586B', bd: on ? '#0B6FA4' : '#D5DEE6' };
  });
  const typeBtns: ToggleButton[] = ['All', 'Big Ticket', 'Routine'].map((v) => {
    const on = state.type === v;
    return { label: v, on, bg: on ? '#0B6FA4' : 'transparent', fg: on ? '#fff' : '#5B7186' };
  });

  // filter title
  const anyFilter =
    state.type !== 'All' || state.regions.length > 0 || state.practice !== 'All' || state.office !== 'All' ||
    state.statuses.length > 0 || state.quarters.length > 0 || state.lead !== 'All';
  let filterTitle: string;
  if (!anyFilter) {
    filterTitle = 'All TA requests — every region, practice & status';
  } else {
    const parts: string[] = [];
    parts.push(state.type === 'All' ? 'All requests' : state.type + ' requests');
    parts.push(state.regions.length ? state.regions[0] : 'all regions');
    if (state.practice !== 'All') parts.push(state.practice);
    if (state.office !== 'All') parts.push(state.office);
    if (state.statuses.length) parts.push(state.statuses.join(', ') + (state.statuses.length > 1 ? ' status' : ' implemented'));
    if (state.quarters.length) parts.push('due ' + state.quarters.join(', '));
    if (state.lead !== 'All') parts.push('led by ' + state.lead);
    filterTitle = parts.join('  ·  ');
  }

  // staff bars (stacked by status)
  const staffGrp = groupBy(F.filter((c) => c.lead), 'lead');
  const staffMax = Math.max(1, ...staffGrp.map((r) => r.n));
  const staffBars: StackedRow[] = staffGrp.map((r) => {
    const rowCases = F.filter((c) => c.lead === r.label);
    const segs = STATUS_ORDER.map((s) => ({ w: r.n ? (rowCases.filter((c) => c.status === s).length / r.n) * 100 : 0, color: STATUS_COLORS[s] })).filter((seg) => seg.w > 0);
    // thematic area from the staff roster join (see data/cases.ts), shown under the name
    const sub = rowCases[0]?.leadArea || '';
    return { label: r.label, n: r.n, barPct: Math.round((r.n / staffMax) * 100), segs, sub };
  });
  const staffLegend: LegendItem[] = STATUS_ORDER.map((s) => ({ label: s, color: STATUS_COLORS[s] }));

  // requests-by (stacked; rendered as solid bar + TAs/Leads), excluding practice "Other"
  const stackByStatus = (key: keyof TACase, limit: number): StackedRow[] => {
    const groups = groupBy(F.filter((c) => notOther(key, c)), key);
    const max = Math.max(1, ...groups.map((r) => r.n));
    return groups.slice(0, limit).map((r) => {
      const rowCases = F.filter((c) => (((c[key] as string) || '—') === r.label));
      const segs = STATUS_ORDER.map((s) => ({ w: r.n ? (rowCases.filter((c) => c.status === s).length / r.n) * 100 : 0, color: STATUS_COLORS[s] })).filter((seg) => seg.w > 0);
      const leads = new Set(rowCases.filter((c) => c.lead).map((c) => c.lead)).size;
      return { label: r.label, n: r.n, barPct: Math.round((r.n / max) * 100), segs, leads };
    });
  };

  // per-lead load spread
  const allLeads = groupBy(F.filter((c) => c.lead), 'lead');
  const counts = allLeads.map((r) => r.n);
  const loadN = counts.length;
  const loadMin = loadN ? Math.min(...counts) : 0;
  const loadMax = loadN ? Math.max(...counts) : 0;
  const loadAvgNum = loadN ? (mean(counts) as number) : 0;
  const loadMaxLead = loadN ? allLeads[0].label : '';
  const loadMinCount = counts.filter((n) => n === loadMin).length;
  const span = Math.max(1, loadMax - loadMin);
  const avgPos = ((loadAvgNum - loadMin) / span) * 100;

  // opened vs completed by month (Apr–Jul)
  const io: { label: string; opened: number; completedN: number }[] = [];
  for (let i = 3; i <= 6; i++) {
    io.push({
      label: MONTHS[i],
      opened: F.filter((c) => monthIndex2026(c.op) === i).length,
      completedN: F.filter((c) => c.status === '100%' && monthIndex2026(c.cl != null ? c.cl : c.rs) === i).length,
    });
  }
  const ioMax = Math.max(1, ...io.map((m) => Math.max(m.opened, m.completedN)));
  const ioMonths: MonthBar[] = io.map((m) => ({
    label: m.label, in: m.opened, done: m.completedN, hasNote: m.label === 'Apr',
    inH: Math.round((m.opened / ioMax) * 140), doneH: Math.round((m.completedN / ioMax) * 140),
  }));
  const ioOpenedTotal = fmtNum(io.reduce((s, m) => s + m.opened, 0));
  const ioCompletedTotal = fmtNum(io.reduce((s, m) => s + m.completedN, 0));

  // overdue severity buckets
  const over1_30 = overdueSet.filter((c) => TODAY - (c.xc as number) <= 30).length;
  const over31_60 = overdueSet.filter((c) => { const d = TODAY - (c.xc as number); return d > 30 && d <= 60; }).length;
  const over60 = overdueSet.filter((c) => TODAY - (c.xc as number) > 60).length;
  const obMax = Math.max(1, over1_30, over31_60, over60);
  const overdueBuckets: BucketRow[] = [
    { label: '1–30 days', n: over1_30, color: '#E0A21E' },
    { label: '31–60 days', n: over31_60, color: '#CD6A2E' },
    { label: '>60 days', n: over60, color: '#C0453F' },
  ].map((b) => ({ ...b, pct: Math.round((b.n / obMax) * 100) }));

  // stalled at 0% > 30 days
  const stalled = activeSet.filter((c) => c.status === '0%' && c.op != null && TODAY - (c.op as number) > 30);
  const stalledByRegion = toBars(groupBy(stalled, 'region'), '#E0A21E', 7);
  const stalledByPractice = toBars(groupBy(stalled.filter((c) => c.practice !== 'Other'), 'practice'), '#E0A21E', 15);
  const stalledBucket = (c: TACase) => (TODAY - (c.op as number) <= 60 ? '31–60 days' : '>60 days');
  const stalledSevColors: Record<string, string> = { '31–60 days': '#CD6A2E', '>60 days': '#C0453F' };
  const stalledSeverity: LegendItem[] = ['31–60 days', '>60 days'].map((label) => ({ label, color: stalledSevColors[label] }));
  const stalledStack = (rows: ColoredBarRow[]): StackedRow[] =>
    rows.map((row) => {
      const cs = stalled.filter((c) => c.region === row.label || c.practice === row.label);
      const segs = ['31–60 days', '>60 days'].map((label) => {
        const n = cs.filter((c) => stalledBucket(c) === label).length;
        return { color: stalledSevColors[label], w: row.n ? Math.round((n / row.n) * 100) : 0 };
      });
      return { label: row.label, n: row.n, barPct: row.pct, segs };
    });
  const stalledByRegionSev = stalledStack(stalledByRegion);
  const stalledByPracticeSev = stalledStack(stalledByPractice);

  const closed30 = F.filter((c) => c.cl != null && (c.cl as number) >= TODAY - 30 && (c.cl as number) <= TODAY).length;

  // full-export match for discontinued + data quality
  // Full export in the current filter — used only to source the discontinued
  // rate and the "no country office assigned" (blank) count.
  const FQ = rawCases.filter((c) => matchesFilters(c, state));
  const REAL_REGIONS = new Set(['ESAR', 'APR', 'WCAR', 'LACR', 'ECAR', 'MENAR']);
  // All Country Office requests (any status) — basis for the discontinued rate.
  const FCO = FQ.filter((c) => REAL_REGIONS.has(c.region));
  const disc = FCO.filter((c) => c.status === 'Discontinued').length;
  const discRate = FCO.length ? (disc / FCO.length) * 100 : 0;

  // Data Quality corner note: active CO requests (= the Performance universe)
  // vs. requests with no country office assigned (blank).
  const coFromN = F.length;
  const coUnassignedN = FQ.filter((c) => !c.office).length;

  const mgmtKpis: KPI[] = [
    { label: 'Open → assignment', value: 'N/A', sub: 'measure coming soon', accent: '#9AA7B2', color: '#9AA7B2' },
    { label: 'Assignment → first response', value: 'N/A', sub: 'measure coming soon', accent: '#9AA7B2', color: '#9AA7B2' },
    { label: 'Opened last 30 days', value: fmtNum(recentSet.length), sub: 'new requests received', accent: '#0B6FA4', color: '#0F2238' },
    { label: 'Closed last 30 days', value: fmtNum(closed30), sub: 'vs ' + fmtNum(recentSet.length) + ' received — throughput', accent: '#2E7D5B', color: '#0F2238' },
    { label: 'Stalled at 0%', value: fmtNum(stalled.length), sub: 'open >30 days, no progress', accent: '#E0A21E', color: '#E0A21E' },
    { label: 'Discontinued', value: fmtNum(disc), sub: discRate.toFixed(1) + '% requests dropped', accent: '#9AA7B2', color: '#5B7186' },
  ];

  const viewTabs: ToggleButton[] = ([['overview', 'Performance'], ['quality', 'Data Quality Review']] as [ViewId, string][]).map(([v, label]) => ({
    label, on: state.view === v, bg: state.view === v ? '#16385C' : '#fff', fg: state.view === v ? '#fff' : '#43586B', bd: state.view === v ? '#16385C' : '#D5DEE6',
  }));

  const kpis: KPI[] = [
    { label: 'Total requests', value: fmtNum(total), sub: 'in current filter', accent: '#0B6FA4', color: '#0F2238' },
    { label: 'Received last 30 days', value: fmtNum(recentSet.length), sub: 'new since 1 Jul 2026', accent: '#1CABE2', color: '#0F2238' },
    { label: 'Active & on track', value: fmtNum(onTrack), sub: 'in progress, not overdue', accent: '#3E9CD6', color: '#3E9CD6' },
    { label: 'Completed vs. target', value: dueByToday.length ? pct(doneByTarget, dueByToday.length) + '%' : '—', sub: 'of ' + fmtNum(dueByToday.length) + ' due by today, ' + fmtNum(doneByTarget) + ' at 100%', accent: '#2E7D5B', color: '#2E7D5B' },
    { label: 'Active on target', value: activeSet.length ? pct(onTrack, activeSet.length) + '%' : '—', sub: fmtNum(overdueSet.length) + ' overdue — update date or close', accent: '#3E9CD6', color: '#0F2238' },
    { label: 'Overdue', value: fmtNum(overdueSet.length), sub: 'past their expected completion date', accent: '#C0453F', color: '#C0453F' },
  ];

  return {
    isOverview: state.view === 'overview',
    isQuality: state.view === 'quality',
    viewTabs,
    metaTotal: fmtNum(ALL),
    coFrom: fmtNum(coFromN),
    coUnassigned: fmtNum(coUnassignedN),
    filterTitle,
    total: fmtNum(total),
    pctOfAll: pct(total, ALL) + '%',
    typeBtns,
    statusChips,
    quarterChips,
    regionOpts: optionCounts(cases, 'region').map(([v, n]) => ({ value: v, label: `${v} (${n})` })),
    practiceOpts: optionCounts(cases, 'practice').map(([v, n]) => ({ value: v, label: `${v} (${n})` })),
    // Country options are scoped to the selected region so the list only shows
    // countries within that region.
    officeOpts: optionCounts(
      state.regions.length ? cases.filter((c) => state.regions.includes(c.region)) : cases,
      'office',
    ).map(([v, n]) => ({ value: v, label: `${v} (${n})` })),

    kpis,
    ioMonths,
    ioOpenedTotal,
    ioCompletedTotal,
    recent: recentSet.length,
    recentByRegion: toBars(groupBy(recentSet, 'region'), '#0B6FA4', 7),
    recentByPractice: toBars(groupBy(recentSet.filter((c) => c.practice !== 'Other'), 'practice'), '#0B6FA4', 15),
    onTrack,
    onTrackByRegion: toBars(groupBy(onTrackSet, 'region'), '#3E9CD6', 7),
    onTrackByPractice: toBars(groupBy(onTrackSet.filter((c) => c.practice !== 'Other'), 'practice'), '#3E9CD6', 15),
    newTable,

    mgmtKpis,

    overdue: overdueSet.length,
    overdueByRegion: toBars(groupBy(overdueSet, 'region'), '#C0453F', 7),
    overdueByPractice: toBars(groupBy(overdueSet.filter((c) => c.practice !== 'Other'), 'practice'), '#C0453F', 15),
    overdueBuckets,
    stalledSeverity,
    stalledByRegionSev,
    stalledByPracticeSev,
    stalledCount: fmtNum(stalled.length),
    overdueTableFinal,

    byPractice: stackByStatus('practice', 15),
    byRegion: stackByStatus('region', 9),
    staffBars,
    staffLegend,
    loadN,
    loadMin,
    loadMax,
    loadMaxLead,
    loadMinCountLabel: loadMinCount + (loadMinCount === 1 ? ' staff member' : ' staff members'),
    loadAvg: loadAvgNum ? loadAvgNum.toFixed(1) : '0',
    avgPos,
    distinctStaff: new Set(F.filter((c) => c.lead).map((c) => c.lead)).size,
    unassigned: F.filter((c) => !c.lead).length,

    dq: computeDataQuality(FCO, TODAY),
  };
}

// ===================== Stage-aware Data Quality =====================

export interface DqTableRow {
  id: string;
  office: string;
  full: string;
  region: string;
  practice: string;
  status: string;
  lead: string;
  leadColor: string;
  metric: string;
  metricColor: string;
  stBg: string;
  stFg: string;
}
export interface TransitionCard {
  label: string;
  sub: string;
}

export interface DataQuality {
  kpis: KPI[];
  // ① Received & in review (Unassigned · 0% · 25%)
  setupTotal: string;
  setupFunnel: BucketRow[];
  setupAging: BucketRow[];
  stalledCount: string;
  stalledByRegion: ColoredBarRow[];
  stalledByPractice: ColoredBarRow[];
  unassignedByPractice: ColoredBarRow[];
  zeroByPractice: ColoredBarRow[];
  stalledTable: DqTableRow[];
  readyCount: string;
  readyOf: string;
  setupContradictions: CheckItem[];
  transitionCards: TransitionCard[];
  stallNote: string;
  // ② Started & in delivery (50%+)
  deliveryTotal: string;
  completeness: CompletenessRow[];
  deliveryScore: string;
  deliveryScoreColor: string;
  deliveryScoreSub: string;
  qualityByRegion: QualityRegionRow[];
  qualityByPractice: QualityRegionRow[];
  deliveryFlags: CheckItem[];
  flagCount: string;
  flagTable: DqTableRow[];
  dupCount: string;
  // ③ Overdue, at-risk & closure
  overdueCount: string;
  overdueBuckets: BucketRow[];
  atRiskCount: string;
  overdueByRegion: ColoredBarRow[];
  overdueByPractice: ColoredBarRow[];
  overdueTable: DqTableRow[];
  notClosedCount: string;
  notClosedTable: DqTableRow[];
  overdueNote: string;
}

/**
 * Data quality read through the implementation-status lifecycle:
 *   Setup / in review  = Unassigned · 0% · 25%  → concern is stalling
 *   Delivery / started = 50% · 75% · 100%        → concern is completeness & consistency
 * `co` is every Country Office request in the current filter (any status).
 */
function computeDataQuality(co: TACase[], today: number): DataQuality {
  const row = (c: TACase, metric: string, metricColor: string): DqTableRow => {
    const st = statusChipStyle(c.status);
    return {
      id: c.id,
      office: c.office || '—',
      full: c.full || c.desc || '—',
      region: c.region || '—',
      practice: c.practice || '—',
      status: c.status,
      lead: c.lead || '— none —',
      leadColor: c.lead ? '#43586B' : '#C0453F',
      metric,
      metricColor,
      stBg: st.bg,
      stFg: st.fg,
    };
  };

  // stage populations
  const setupSet = co.filter((c) => ['Unassigned', '0%', '25%'].includes(c.status));
  const started = co.filter((c) => c.status === '50%' || c.status === '75%');
  const completed = co.filter((c) => c.status === '100%');
  const delivery = [...started, ...completed]; // 50%+ — completeness & flags apply here
  const activeCO = co.filter((c) => c.status !== '100%' && c.status !== 'Discontinued');

  // ---- ① setup / in review ----
  const stallDays = (c: TACase) =>
    c.status === 'Unassigned' ? Math.round(today - (c.cr ?? c.op)!) : Math.round(today - (c.up ?? c.cr ?? c.op)!);
  const isStalled = (c: TACase) => (c.status === 'Unassigned' ? stallDays(c) > 14 : stallDays(c) > 30);
  const stalledSetup = setupSet.filter(isStalled);

  const stageColor: Record<string, string> = { Unassigned: '#E0A21E', '0%': '#9CC6E0', '25%': '#5BA3D0' };
  const funMax = Math.max(1, ...['Unassigned', '0%', '25%'].map((s) => setupSet.filter((c) => c.status === s).length));
  const setupFunnel: BucketRow[] = ['Unassigned', '0%', '25%'].map((s) => {
    const n = setupSet.filter((c) => c.status === s).length;
    return { label: s, n, color: stageColor[s], pct: Math.round((n / funMax) * 100) };
  });

  const agingDefs: [string, (d: number) => boolean, string][] = [
    ['0–14 days', (d) => d <= 14, '#3E9CD6'],
    ['15–30 days', (d) => d > 14 && d <= 30, '#E0A21E'],
    ['30+ days', (d) => d > 30, '#C0453F'],
  ];
  const agMax = Math.max(1, ...agingDefs.map(([, t]) => setupSet.filter((c) => t(stallDays(c))).length));
  const setupAging: BucketRow[] = agingDefs.map(([label, t, color]) => {
    const n = setupSet.filter((c) => t(stallDays(c))).length;
    return { label, n, color, pct: Math.round((n / agMax) * 100) };
  });

  const stalledByRegion = toBars(groupBy(stalledSetup, 'region'), '#E0A21E', 7);
  const stalledByPractice = toBars(groupBy(stalledSetup.filter((c) => c.practice !== 'Other'), 'practice'), '#E0A21E', 15);

  // team performance: unassigned and 0% (awaiting the setup steps), by practice
  const unassignedByPractice = toBars(groupBy(setupSet.filter((c) => c.status === 'Unassigned' && c.practice !== 'Other'), 'practice'), '#E0A21E', 15);
  const zeroByPractice = toBars(groupBy(setupSet.filter((c) => c.status === '0%' && c.practice !== 'Other'), 'practice'), '#5BA3D0', 15);
  const stalledTable = [...stalledSetup]
    .sort((a, b) => stallDays(b) - stallDays(a))
    .slice(0, 12)
    .map((c) => row(c, stallDays(c) + 'd', '#C0453F'));

  const at25 = setupSet.filter((c) => c.status === '25%');
  const ready = at25.filter((c) => c.ho && c.lead && c.xc != null);

  const noLeadAssigned = setupSet.filter((c) => (c.status === '0%' || c.status === '25%') && !c.lead);
  const setupContradictions: CheckItem[] = [
    { n: fmtNum(noLeadAssigned.length), label: 'Past assignment, but no TA lead', sub: '0% or 25% means a lead should already be assigned', color: '#C0453F' },
  ];

  const transitionCards: TransitionCard[] = [
    { label: 'Unassigned → 0%', sub: 'days to assign a TA lead' },
    { label: '0% → 25%', sub: 'days to agree scope with the CO' },
    { label: '25% → 50%', sub: 'days to formally start delivery' },
  ];

  const stallNote =
    'Days stalled = today (' + formatDate(today) + ') − last Updated date (for Unassigned, − the date received). ' +
    'Stage-transition dates are not captured yet, so this is a proxy for time in the current stage.';

  // ---- ② started & in delivery (50%+) ----
  const delN = delivery.length;
  const cFields: [string, (c: TACase) => boolean][] = [
    ['Objectives', (c) => !!c.ho],
    ['TA lead', (c) => !!c.lead],
    ['Expected completion', (c) => c.xc != null],
    ['Description', (c) => !!c.hd],
    ['Modality', (c) => !!c.modality],
    ['Programme offer', (c) => !!c.offer],
  ];
  const completeness: CompletenessRow[] = cFields.map(([label, fn]) => {
    const p = delN ? Math.round((delivery.filter(fn).length / delN) * 100) : 0;
    const color = p >= 95 ? '#2E7D5B' : p >= 80 ? '#3E9CD6' : '#E0A21E';
    return { label, pct: p, pctLabel: p + '%', color };
  });

  const passes = (c: TACase) =>
    !!(c.ho && c.lead && c.xc != null && c.hd && c.modality && c.offer) &&
    !(c.xc != null && c.xs != null && (c.xc as number) < (c.xs as number));
  const passN = delivery.filter(passes).length;
  const score = delN ? Math.round((passN / delN) * 100) : 0;

  const qColor = (p: number) => (p >= 80 ? '#2E7D5B' : p >= 60 ? '#3E9CD6' : '#E0A21E');
  const qualityByRegion: QualityRegionRow[] = groupBy(delivery, 'region')
    .map((r) => {
      const cs = delivery.filter((c) => c.region === r.label);
      const p = Math.round((cs.filter(passes).length / cs.length) * 100);
      return { label: r.label, pct: p, pctLabel: p + '%', color: qColor(p) };
    })
    .sort((a, b) => a.pct - b.pct);
  const qualityByPractice: QualityRegionRow[] = groupBy(delivery.filter((c) => c.practice !== 'Other'), 'practice')
    .slice(0, 15)
    .map((r) => {
      const cs = delivery.filter((c) => c.practice === r.label);
      const p = Math.round((cs.filter(passes).length / cs.length) * 100);
      return { label: r.label, pct: p, pctLabel: p + '%', color: qColor(p) };
    })
    .sort((a, b) => a.pct - b.pct);

  const deliveryFlags: CheckItem[] = [
    { n: fmtNum(delivery.filter((c) => !c.ho).length), label: 'Missing objectives', sub: 'work has started but objectives were never captured', color: '#C0453F' },
    { n: fmtNum(delivery.filter((c) => !c.lead).length), label: 'No TA lead', sub: 'in delivery yet unassigned', color: '#C0453F' },
    { n: fmtNum(delivery.filter((c) => c.xc == null).length), label: 'No expected completion date', sub: 'timeliness can never be measured', color: '#C0453F' },
    { n: fmtNum(delivery.filter((c) => c.xc != null && c.xs != null && (c.xc as number) < (c.xs as number)).length), label: 'Completion target before start', sub: 'expected completion earlier than expected start', color: '#E0A21E' },
  ];

  const reason = (c: TACase): string =>
    !c.ho ? 'no objectives'
      : !c.lead ? 'no TA lead'
      : c.xc == null ? 'no target date'
      : !c.hd ? 'no description'
      : !c.modality ? 'no modality'
      : !c.offer ? 'no offer'
      : c.xs != null && (c.xc as number) < (c.xs as number) ? 'target before start'
      : 'ok';
  const flagRecords = delivery.filter((c) => !passes(c));
  const flagTable = flagRecords.slice(0, 12).map((c) => row(c, reason(c), '#C0453F'));

  let dupCount = 0;
  {
    const seen: Record<string, 1> = {};
    for (const c of co) {
      if (!c.reqFor || !c.desc) continue;
      const k = (c.reqFor + '|' + c.desc).toLowerCase();
      if (seen[k]) dupCount++;
      else seen[k] = 1;
    }
  }

  // ---- ③ overdue, at-risk & closure ----
  const overdueSet = activeCO
    .filter((c) => c.xc != null && (c.xc as number) < today)
    .sort((a, b) => today - (b.xc as number) - (today - (a.xc as number)));
  const o1 = overdueSet.filter((c) => today - (c.xc as number) <= 30).length;
  const o2 = overdueSet.filter((c) => { const d = today - (c.xc as number); return d > 30 && d <= 60; }).length;
  const o3 = overdueSet.filter((c) => today - (c.xc as number) > 60).length;
  const obMax = Math.max(1, o1, o2, o3);
  const overdueBuckets: BucketRow[] = [
    { label: '1–30 days', n: o1, color: '#E0A21E' },
    { label: '31–60 days', n: o2, color: '#CD6A2E' },
    { label: '>60 days', n: o3, color: '#C0453F' },
  ].map((b) => ({ ...b, pct: Math.round((b.n / obMax) * 100) }));
  const atRisk = activeCO.filter((c) => c.xc != null && (c.xc as number) >= today && (c.xc as number) <= today + 30);
  const overdueByRegion = toBars(groupBy(overdueSet, 'region'), '#C0453F', 7);
  const overdueByPractice = toBars(groupBy(overdueSet.filter((c) => c.practice !== 'Other'), 'practice'), '#C0453F', 15);
  const overdueTable = overdueSet.slice(0, 12).map((c) => row(c, '+' + Math.round(today - (c.xc as number)) + 'd', '#C0453F'));

  const notClosed = co.filter((c) => (c.status === '100%' || c.status === 'Discontinued') && !c.cl);
  const notClosedTable = notClosed.slice(0, 12).map((c) => row(c, c.status === '100%' ? 'completed' : 'discontinued', '#E0A21E'));

  const overdueNote =
    'Days overdue = today (' + formatDate(today) + ') − Expected Completion Date. ' +
    'If this looks too high, the TA lead should update the Expected Completion Date on the request.';

  // ---- KPIs (stage-aware) ----
  const unassignedN = setupSet.filter((c) => c.status === 'Unassigned').length;
  const inSetupN = setupSet.filter((c) => c.status !== 'Unassigned').length;
  const kpis: KPI[] = [
    { label: 'Awaiting assignment', value: fmtNum(unassignedN), sub: 'unassigned CO requests', accent: '#E0A21E', color: '#0F2238' },
    { label: 'In setup (0–25%)', value: fmtNum(inSetupN), sub: 'being scoped with the CO', accent: '#5BA3D0', color: '#0F2238' },
    { label: 'Stalled in setup', value: fmtNum(stalledSetup.length), sub: 'stuck past the threshold', accent: '#C0453F', color: '#C0453F' },
    { label: 'In delivery (50%+)', value: fmtNum(started.length), sub: 'work has started', accent: '#0B6FA4', color: '#0F2238' },
    { label: 'Needing cleanup', value: fmtNum(flagRecords.length), sub: '50%+ with a data flag', accent: '#C0453F', color: '#C0453F' },
    { label: 'Overdue', value: fmtNum(overdueSet.length), sub: 'active past target date', accent: '#C0453F', color: '#C0453F' },
  ];

  return {
    kpis,
    setupTotal: fmtNum(setupSet.length),
    setupFunnel,
    setupAging,
    stalledCount: fmtNum(stalledSetup.length),
    stalledByRegion,
    stalledByPractice,
    unassignedByPractice,
    zeroByPractice,
    stalledTable,
    readyCount: fmtNum(ready.length),
    readyOf: fmtNum(at25.length),
    setupContradictions,
    transitionCards,
    stallNote,
    deliveryTotal: fmtNum(delN),
    completeness,
    deliveryScore: score + '%',
    deliveryScoreColor: score >= 80 ? '#2E7D5B' : score >= 60 ? '#E0A21E' : '#C0453F',
    deliveryScoreSub: fmtNum(passN) + ' of ' + fmtNum(delN) + ' pass every check',
    qualityByRegion,
    qualityByPractice,
    deliveryFlags,
    flagCount: fmtNum(flagRecords.length),
    flagTable,
    dupCount: fmtNum(dupCount),
    overdueCount: fmtNum(overdueSet.length),
    overdueBuckets,
    atRiskCount: fmtNum(atRisk.length),
    overdueByRegion,
    overdueByPractice,
    overdueTable,
    notClosedCount: fmtNum(notClosed.length),
    notClosedTable,
    overdueNote,
  };
}
