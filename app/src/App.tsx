import { useMemo, useState } from 'react';
import { CASES, RAW_CASES, QUARTERS, TODAY } from './data/cases';
import { computeDashboard, INITIAL_FILTERS, type FilterState, type ViewId } from './lib/dashboard';
import { Header } from './components/Header';
import { FilterBar } from './components/FilterBar';
import { PerformanceView } from './components/PerformanceView';
import { DataQualityView } from './components/DataQualityView';

const VIEW_BY_LABEL: Record<string, ViewId> = {
  Performance: 'overview',
  'Data Quality Review': 'quality',
};

function App() {
  const [filters, setFilters] = useState<FilterState>(INITIAL_FILTERS);
  const d = useMemo(() => computeDashboard(CASES, RAW_CASES, QUARTERS, TODAY, filters), [filters]);

  const onView = (label: string) => setFilters((f) => ({ ...f, view: VIEW_BY_LABEL[label] ?? 'overview' }));
  const setType = (v: string) => setFilters((f) => ({ ...f, type: v }));
  const onRegion = (v: string) =>
    setFilters((f) => ({ ...f, regions: v === 'All' ? [] : [v], office: 'All' }));
  const onPractice = (v: string) => setFilters((f) => ({ ...f, practice: v }));
  const onOffice = (v: string) => setFilters((f) => ({ ...f, office: v }));
  const onToggleStatus = (v: string) =>
    setFilters((f) => ({ ...f, statuses: f.statuses.includes(v) ? f.statuses.filter((x) => x !== v) : [...f.statuses, v] }));
  const onToggleQuarter = (v: string) =>
    setFilters((f) => ({ ...f, quarters: f.quarters.includes(v) ? f.quarters.filter((x) => x !== v) : [...f.quarters, v] }));
  const onReset = () => setFilters((f) => ({ ...INITIAL_FILTERS, view: f.view }));

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#EDF1F4',
        fontFamily: "'Helvetica Neue',Helvetica,Arial,sans-serif",
        color: '#0F2238',
        WebkitFontSmoothing: 'antialiased',
        paddingBottom: 60,
      }}
    >
      <Header metaTotal={d.metaTotal} isQuality={d.isQuality} coFrom={d.coFrom} coUnassigned={d.coUnassigned} />

      <FilterBar
        viewTabs={d.viewTabs}
        onView={onView}
        typeBtns={d.typeBtns}
        onType={setType}
        practice={filters.practice}
        practiceOpts={d.practiceOpts}
        onPractice={onPractice}
        region={filters.regions[0] || 'All'}
        regionOpts={d.regionOpts}
        onRegion={onRegion}
        office={filters.office}
        officeOpts={d.officeOpts}
        onOffice={onOffice}
        statusChips={d.statusChips}
        onToggleStatus={onToggleStatus}
        quarterChips={d.quarterChips}
        onToggleQuarter={onToggleQuarter}
        onReset={onReset}
      />

      <div style={{ maxWidth: 1340, margin: '0 auto', padding: '0 24px' }}>
        {/* Active filter summary */}
        <div style={{ padding: '20px 2px 4px' }}>
          <div style={{ fontSize: 19, fontWeight: 700, letterSpacing: '-.01em', color: '#0F2238' }}>{d.filterTitle}</div>
          <div style={{ fontSize: 13, color: '#5B7186', marginTop: 5 }}>
            Showing <span style={{ fontWeight: 700, color: '#0F2238' }}>{d.total}</span> requests{' '}
            <span style={{ color: '#9AA7B2' }}>({d.pctOfAll} of all)</span>
          </div>
        </div>

        {d.isOverview && <PerformanceView d={d} />}
        {d.isQuality && <DataQualityView d={d} />}
      </div>
    </div>
  );
}

export default App;
