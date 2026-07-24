import { useState } from 'react';
import type { Dashboard, StackedRow } from '../lib/dashboard';
import { Card } from './Card';
import { SectionHeading } from './SectionHeading';
import { KpiStrip } from './KpiStrip';
import { BarList } from './BarList';

const SUBTABS = [
  { id: 'demand', label: 'Demand & delivery' },
  { id: 'cycle', label: 'Cycle time' },
  { id: 'overdue', label: 'Overdue requests' },
  { id: 'workload', label: 'Workload' },
] as const;
type SubTab = (typeof SUBTABS)[number]['id'];

const cardTitle: React.CSSProperties = { fontSize: 13, fontWeight: 700, marginBottom: 14 };
const bigCardTitle: React.CSSProperties = { fontSize: 13.5, fontWeight: 700 };
const whatSays: React.CSSProperties = {
  fontSize: 12, color: '#8A98A6', lineHeight: 1.55, marginTop: 16, borderTop: '1px solid #F1F4F7', paddingTop: 12,
};
const scrollBox: React.CSSProperties = { maxHeight: 150, overflowY: 'auto', paddingRight: 6 };

function Hero({ bg, border, labelColor, value, valueColor, label, body, bodyColor }: {
  bg: string; border: string; labelColor: string; value: number | string; valueColor: string; label: string; body: string; bodyColor: string;
}) {
  return (
    <div style={{ background: bg, border: `1px solid ${border}`, borderRadius: 10, padding: '20px 22px', height: 216, boxSizing: 'border-box', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
      <div style={{ fontSize: 12, letterSpacing: '.06em', textTransform: 'uppercase', color: labelColor, fontWeight: 700 }}>{label}</div>
      <div style={{ fontSize: 52, fontWeight: 700, letterSpacing: '-.03em', color: valueColor, lineHeight: 1, margin: '10px 0 6px', fontVariantNumeric: 'tabular-nums' }}>{value}</div>
      <div style={{ fontSize: 12.5, color: bodyColor, lineHeight: 1.5 }}>{body}</div>
    </div>
  );
}

const tableCols = '100px 110px 1.5fr 124px 96px 64px 74px 120px 80px';

function RequestTable({ title, rows, metricLabel, daysColor, footer }: {
  title: string; rows: Dashboard['newTable']; metricLabel: string; daysColor: string; footer?: string;
}) {
  return (
    <div style={{ background: '#fff', border: '1px solid #E3E9EF', borderRadius: 10, padding: '6px 0 4px', marginTop: 16, overflow: 'hidden' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, padding: '14px 22px 10px', flexWrap: 'wrap' }}>
        <div style={{ fontSize: 13, fontWeight: 700 }}>{title}</div>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <div style={{ minWidth: 900 }}>
          <div style={{ display: 'grid', gridTemplateColumns: tableCols, gap: 10, padding: '8px 22px', background: '#F6F8FA', borderTop: '1px solid #EDF1F4', borderBottom: '1px solid #EDF1F4', fontSize: 10.5, letterSpacing: '.06em', textTransform: 'uppercase', color: '#7A8C9C', fontWeight: 700 }}>
            <div>Case</div><div>Country</div><div>Description</div><div>Practice</div><div>Exp. completion</div><div>Status</div><div>State</div><div>TA lead</div><div style={{ textAlign: 'right' }}>{metricLabel}</div>
          </div>
          <div style={{ maxHeight: 420, overflowY: 'auto' }}>
            {rows.map((r) => (
              <div key={r.id} style={{ display: 'grid', gridTemplateColumns: tableCols, gap: 10, padding: '11px 22px', borderBottom: '1px solid #F1F4F7', alignItems: 'center', fontSize: 12.5 }}>
                <div style={{ fontWeight: 600, color: '#0B5A8A', fontVariantNumeric: 'tabular-nums' }}>{r.id}</div>
                <div style={{ color: '#43586B', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.country}</div>
                <div title={r.full} style={{ color: '#5B7186', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', cursor: 'help' }}>{r.full}</div>
                <div style={{ color: '#43586B', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.practice}</div>
                <div style={{ color: '#43586B', fontVariantNumeric: 'tabular-nums', whiteSpace: 'nowrap' }}>{r.expDate}</div>
                <div><span style={{ fontSize: 11.5, fontWeight: 700, padding: '2px 8px', borderRadius: 5, background: r.stBg, color: r.stFg }}>{r.status}</span></div>
                <div><span style={{ fontSize: 11.5, fontWeight: 700, padding: '2px 9px', borderRadius: 5, background: r.stateBg, color: r.stateFg }}>{r.state}</span></div>
                <div style={{ color: r.leadColor, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.lead}</div>
                <div style={{ textAlign: 'right', fontWeight: 700, color: daysColor, fontVariantNumeric: 'tabular-nums' }}>{r.days}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
      {footer && (
        <div style={{ padding: '12px 22px 14px', fontSize: 11.5, color: '#8A98A6', lineHeight: 1.55, borderTop: '1px solid #F1F4F7' }}>{footer}</div>
      )}
    </div>
  );
}

function StackTrack({ row, height, track = '#EEF2F6' }: { row: StackedRow; height: number; track?: string }) {
  return (
    <div style={{ height, background: track, borderRadius: height / 2, overflow: 'hidden' }}>
      <div style={{ height: '100%', width: `${row.barPct}%`, display: 'flex', borderRadius: height / 2, overflow: 'hidden' }}>
        {row.segs.map((s, i) => (
          <div key={i} style={{ width: `${s.w}%`, background: s.color }} />
        ))}
      </div>
    </div>
  );
}

function SolidWorkloadCard({ title, rows, labelW }: { title: string; rows: StackedRow[]; labelW: number }) {
  const scroll = labelW >= 150;
  const body = (
    <>
      <div style={{ display: 'grid', gridTemplateColumns: `${labelW}px 1fr 38px 74px`, gap: 10, marginBottom: 9, fontSize: 10, letterSpacing: '.05em', textTransform: 'uppercase', color: '#9AA7B2', fontWeight: 700 }}>
        <div /><div /><div style={{ textAlign: 'right' }}>TAs</div><div style={{ textAlign: 'right' }}>Leads</div>
      </div>
      <div style={scroll ? scrollBox : undefined}>
        {rows.map((row) => (
          <div key={row.label} style={{ display: 'grid', gridTemplateColumns: `${labelW}px 1fr 38px 74px`, alignItems: 'center', gap: 10, marginBottom: 10 }}>
            <div style={{ fontSize: 12, color: '#43586B', fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{row.label}</div>
            <div style={{ height: 10, background: '#EEF2F6', borderRadius: 5 }}><div style={{ height: '100%', width: `${row.barPct}%`, background: '#0B6FA4', borderRadius: 5 }} /></div>
            <div style={{ fontSize: 12.5, fontWeight: 700, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{row.n}</div>
            <div style={{ fontSize: 12, textAlign: 'right', fontVariantNumeric: 'tabular-nums', color: '#0B6FA4', fontWeight: 700 }}>{row.leads}</div>
          </div>
        ))}
      </div>
    </>
  );
  return (
    <div style={{ background: '#fff', border: '1px solid #E3E9EF', borderRadius: 10, padding: '20px 22px', height: 238, boxSizing: 'border-box' }}>
      <div style={{ ...bigCardTitle, marginBottom: 16 }}>{title}</div>
      {body}
    </div>
  );
}

function SeverityLegend({ items }: { items: { label: string; color: string }[] }) {
  return (
    <div style={{ display: 'flex', gap: 16 }}>
      {items.map((b) => (
        <div key={b.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 11, height: 11, borderRadius: 3, background: b.color }} />
          <span style={{ fontSize: 11.5, color: '#43586B' }}>{b.label}</span>
        </div>
      ))}
    </div>
  );
}

function StalledCard({ title, rows, legend, labelW }: { title: string; rows: StackedRow[]; legend: { label: string; color: string }[]; labelW: number }) {
  const scroll = labelW >= 150;
  const list = (
    <>
      {rows.map((row) => (
        <div key={row.label} style={{ display: 'grid', gridTemplateColumns: `${labelW}px 1fr 44px`, alignItems: 'center', gap: 10, marginBottom: 11 }}>
          <div style={{ fontSize: 12, color: '#43586B', fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{row.label}</div>
          <StackTrack row={row} height={11} track="#F5EEDF" />
          <div style={{ fontSize: 12.5, fontWeight: 700, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{row.n}</div>
        </div>
      ))}
    </>
  );
  return (
    <div style={{ background: '#fff', border: '1px solid #E3E9EF', borderRadius: 10, padding: '20px 22px', height: 252, boxSizing: 'border-box' }}>
      <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
        <div style={bigCardTitle}>{title}</div>
        <SeverityLegend items={legend} />
      </div>
      {scroll ? <div style={{ maxHeight: 160, overflowY: 'auto', paddingRight: 6 }}>{list}</div> : list}
    </div>
  );
}

export function PerformanceView({ d }: { d: Dashboard }) {
  const [tab, setTab] = useState<SubTab>('demand');
  return (
    <>
      <KpiStrip kpis={d.kpis} />

      {/* Sub-tab bar */}
      <div style={{ display: 'flex', gap: 4, borderBottom: '1px solid #DCE3EA', margin: '26px 0 6px', flexWrap: 'wrap' }}>
        {SUBTABS.map((t) => {
          const on = tab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              style={{
                border: 'none',
                background: 'transparent',
                cursor: 'pointer',
                fontFamily: 'inherit',
                fontSize: 16.5,
                fontWeight: 700,
                padding: '12px 20px',
                color: on ? '#0B5A8A' : '#5B7186',
                borderBottom: on ? '3px solid #0B5A8A' : '3px solid transparent',
                marginBottom: -1,
              }}
            >
              {t.label}
            </button>
          );
        })}
      </div>

      {tab === 'demand' && (
      <>
      {/* ===== SECTION 1: DEMAND & STATUS ===== */}
      <SectionHeading n={1} title="Demand, delivery & status" />

      {/* opened vs completed vs closed by month */}
      <Card>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 18 }}>
          <div style={bigCardTitle}>Requests opened vs. completed, by month (2026)</div>
          <div style={{ display: 'flex', gap: 16 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span style={{ width: 11, height: 11, borderRadius: 3, background: '#0B6FA4' }} /><span style={{ fontSize: 11.5, color: '#43586B' }}>Opened</span></div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}><span style={{ width: 11, height: 11, borderRadius: 3, background: '#2E7D5B' }} /><span style={{ fontSize: 11.5, color: '#43586B' }}>Completed</span></div>
          </div>
        </div>
        <div style={{ overflowX: 'auto' }}>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 14, padding: '0 6px', minWidth: 320 }}>
          {d.ioMonths.map((m) => (
            <div key={m.label} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 7 }}>
              <div style={{ display: 'flex', alignItems: 'flex-end', gap: 5 }}>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
                  {m.hasNote && (
                    <div style={{ fontSize: 10, fontWeight: 700, color: '#0B6FA4', background: '#EAF2F8', border: '1px solid #CFE0EE', borderRadius: 5, padding: '2px 7px', marginBottom: 2, whiteSpace: 'nowrap' }}>import into REACH</div>
                  )}
                  <div style={{ fontSize: 10.5, fontWeight: 700, color: '#0B6FA4', fontVariantNumeric: 'tabular-nums' }}>{m.in}</div>
                  <div style={{ width: 26, height: m.inH, minHeight: 2, background: '#0B6FA4', borderRadius: '4px 4px 0 0' }} />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3 }}>
                  <div style={{ fontSize: 10.5, fontWeight: 700, color: '#2E7D5B', fontVariantNumeric: 'tabular-nums' }}>{m.done}</div>
                  <div style={{ width: 26, height: m.doneH, minHeight: 2, background: '#2E7D5B', borderRadius: '4px 4px 0 0' }} />
                </div>
              </div>
              <div style={{ fontSize: 11.5, color: '#5B7186', fontWeight: 600 }}>{m.label}</div>
            </div>
          ))}
        </div>
        </div>
        <div style={whatSays}>
          <strong style={{ color: '#5B7186' }}>What this says:</strong> every month the blue bar (new demand) towers over the green bar (completed work), the active backlog grows. In the current filter, <strong style={{ color: '#0B6FA4' }}>{d.ioOpenedTotal}</strong> requests were opened since April and <strong style={{ color: '#2E7D5B' }}>{d.ioCompletedTotal}</strong> reached 100%.
        </div>
      </Card>

      {/* received last 30 days */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(230px, 100%), 1fr))', gap: 16, marginTop: 16, alignItems: 'start' }}>
        <Hero bg="#EAF2F8" border="#CFE0EE" labelColor="#0B6FA4" value={d.recent} valueColor="#0B6FA4" label="Received in last 30 days" body="new TA requests opened between 22 Jun and 22 Jul 2026." bodyColor="#3E6178" />
        <div style={{ background: '#fff', border: '1px solid #E3E9EF', borderRadius: 10, padding: '20px 22px', height: 216, boxSizing: 'border-box' }}>
          <div style={cardTitle}>New by region</div>
          <BarList rows={d.recentByRegion} labelWidth={64} trackBg="#E9F0F6" />
        </div>
        <div style={{ background: '#fff', border: '1px solid #E3E9EF', borderRadius: 10, padding: '20px 22px', height: 216, boxSizing: 'border-box' }}>
          <div style={cardTitle}>New by practice</div>
          <div style={scrollBox}><BarList rows={d.recentByPractice} labelWidth={150} trackBg="#E9F0F6" /></div>
        </div>
      </div>

      {/* active on track */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(230px, 100%), 1fr))', gap: 16, marginTop: 16, alignItems: 'start' }}>
        <Hero bg="#EAF2F8" border="#CFE0EE" labelColor="#3E9CD6" value={d.onTrack} valueColor="#3E9CD6" label="Active & on track" body="requests in progress whose expected completion date has not yet passed." bodyColor="#3E6178" />
        <div style={{ background: '#fff', border: '1px solid #E3E9EF', borderRadius: 10, padding: '20px 22px', height: 216, boxSizing: 'border-box' }}>
          <div style={cardTitle}>On track by region</div>
          <BarList rows={d.onTrackByRegion} labelWidth={64} trackBg="#E4EFF6" />
        </div>
        <div style={{ background: '#fff', border: '1px solid #E3E9EF', borderRadius: 10, padding: '20px 22px', height: 216, boxSizing: 'border-box' }}>
          <div style={cardTitle}>On track by practice</div>
          <div style={scrollBox}><BarList rows={d.onTrackByPractice} labelWidth={150} trackBg="#E4EFF6" /></div>
        </div>
      </div>

      {/* newest requests table */}
      <RequestTable title="Newest requests (last 30 days)" rows={d.newTable} metricLabel="Age (days)" daysColor="#0B6FA4" />

      </>
      )}

      {tab === 'cycle' && (
      <>
      {/* ===== SECTION 2: CYCLE TIME ===== */}
      <SectionHeading n={2} title="Cycle time: opening, response time and closure" />
      <KpiStrip kpis={d.mgmtKpis} />

      <Card style={{ marginTop: 16 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 16 }}>
          <div style={bigCardTitle}>Average response time after assignment, by practice</div>
          <div style={{ fontSize: 11.5, color: '#9AA7B2' }}>coming soon</div>
        </div>
        <div style={{ fontSize: 12.5, color: '#9AA7B2' }}>This measure requires an assignment date, which is not yet captured at source. Space reserved here for when that data becomes available.</div>
      </Card>

      </>
      )}

      {tab === 'overdue' && (
      <>
      {/* ===== SECTION 3: OVERDUE REQUESTS ===== */}
      <SectionHeading n={3} title="Overdue requests" />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(230px, 100%), 1fr))', gap: 16, alignItems: 'start' }}>
        <Hero bg="#FBF0EF" border="#F0D2CF" labelColor="#B0453F" value={d.overdue} valueColor="#C0453F" label="Should be closed by now" body="active requests are past their expected completion date but not yet at 100%." bodyColor="#8A5450" />
        <div style={{ background: '#fff', border: '1px solid #E3E9EF', borderRadius: 10, padding: '20px 22px', height: 216, boxSizing: 'border-box' }}>
          <div style={cardTitle}>Overdue by region</div>
          <BarList rows={d.overdueByRegion} labelWidth={64} trackBg="#F2EAE9" />
        </div>
        <div style={{ background: '#fff', border: '1px solid #E3E9EF', borderRadius: 10, padding: '20px 22px', height: 216, boxSizing: 'border-box' }}>
          <div style={cardTitle}>Overdue by practice</div>
          <div style={scrollBox}><BarList rows={d.overdueByPractice} labelWidth={150} trackBg="#F2EAE9" /></div>
        </div>
      </div>

      {/* overdue severity stacked bar */}
      <Card style={{ marginTop: 16 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 16 }}>
          <div style={bigCardTitle}>Overdue severity — how far past the target date</div>
          <SeverityLegend items={d.overdueBuckets} />
        </div>
        <div style={{ display: 'flex', height: 30, borderRadius: 6, overflow: 'hidden', border: '1px solid #E3E9EF' }}>
          {d.overdueBuckets.map((b) => (
            <div key={b.label} title={b.label} style={{ width: `${b.pct}%`, background: b.color }} />
          ))}
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-start', gap: 24, marginTop: 10, fontSize: 12.5 }}>
          {d.overdueBuckets.map((b) => (
            <span key={b.label} style={{ color: b.color, fontWeight: 700 }}>{b.n} · {b.label}</span>
          ))}
        </div>
        <div style={whatSays}>
          <strong style={{ color: '#5B7186' }}>What this says:</strong> most overdue requests are less than 30 days late. Action needed for the <strong style={{ color: '#C0453F' }}>&gt;60 days</strong> group is to review expected completion dates as targets are no longer credible and need re-planning or closure.
        </div>
      </Card>

      {/* stalled by region + practice */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(300px, 100%), 1fr))', gap: 16, alignItems: 'start', marginTop: 16 }}>
        <StalledCard title="Stalled at 0% for 30+ days, by region" rows={d.stalledByRegionSev} legend={d.stalledSeverity} labelW={64} />
        <StalledCard title="Stalled at 0% for 30+ days, by practice" rows={d.stalledByPracticeSev} legend={d.stalledSeverity} labelW={150} />
      </div>

      <div style={{ background: 'rgba(224,162,30,0.12)', border: '1px solid rgba(224,162,30,0.35)', borderRadius: 10, padding: '16px 20px', marginTop: 16 }}>
        <div style={{ fontSize: 12.5, color: '#7A5B10', lineHeight: 1.55 }}>
          <strong style={{ color: '#5B7186' }}>What this says:</strong> these <strong style={{ color: '#B0453F' }}>{d.stalledCount}</strong> requests were assigned 30 or more days ago and have shown no progress at all.
        </div>
      </div>

      {/* most overdue table */}
      <RequestTable
        title="Most overdue active requests"
        rows={d.overdueTableFinal}
        metricLabel="Days over"
        daysColor="#C0453F"
        footer="Days over = today (22 Jul 2026) − the request’s Expected Completion Date, counting only active requests (implementation status below 100%) whose target date has already passed."
      />

      </>
      )}

      {tab === 'workload' && (
      <>
      {/* ===== SECTION 4: WORKLOAD ===== */}
      <SectionHeading n={4} title="Workload: practices, regions & staff" bg="#16385C" />
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(300px, 100%), 1fr))', gap: 16, alignItems: 'start' }}>
        <SolidWorkloadCard title="Requests by region" rows={d.byRegion} labelW={80} />
        <SolidWorkloadCard title="Requests by practice" rows={d.byPractice} labelW={150} />
      </div>

      {/* workload spread */}
      <Card style={{ marginTop: 16 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 6, flexWrap: 'wrap', gap: 8 }}>
          <div style={bigCardTitle}>Requests per TA lead — workload spread</div>
        </div>
        <div style={{ fontSize: 13, color: '#5B7186', marginBottom: 2 }}><span style={{ fontWeight: 700, color: '#0B6FA4', fontSize: 15 }}>{d.loadN}</span> TA lead staff assigned in current filter</div>
        <div style={{ display: 'flex', gap: 12, margin: '16px 0 22px' }}>
          <div style={{ flex: 1, background: '#F6F8FA', border: '1px solid #EDF1F4', borderRadius: 9, padding: '13px 16px' }}>
            <div style={{ fontSize: 10.5, letterSpacing: '.08em', textTransform: 'uppercase', color: '#7A8C9C', fontWeight: 700 }}>Minimum</div>
            <div style={{ fontSize: 26, fontWeight: 700, color: '#2E7D5B', fontVariantNumeric: 'tabular-nums', lineHeight: 1.15, marginTop: 3 }}>{d.loadMin}</div>
            <div style={{ fontSize: 11, color: '#9AA7B2' }}>held by {d.loadMinCountLabel}</div>
          </div>
          <div style={{ flex: 1, background: '#EEF6FB', border: '1px solid #CFE6F2', borderRadius: 9, padding: '13px 16px' }}>
            <div style={{ fontSize: 10.5, letterSpacing: '.08em', textTransform: 'uppercase', color: '#2C5A75', fontWeight: 700 }}>Average</div>
            <div style={{ fontSize: 26, fontWeight: 700, color: '#0B6FA4', fontVariantNumeric: 'tabular-nums', lineHeight: 1.15, marginTop: 3 }}>{d.loadAvg}</div>
            <div style={{ fontSize: 11, color: '#7FA6BE' }}>requests per lead</div>
          </div>
          <div style={{ flex: 1, background: '#FBF0EF', border: '1px solid #F0D2CF', borderRadius: 9, padding: '13px 16px' }}>
            <div style={{ fontSize: 10.5, letterSpacing: '.08em', textTransform: 'uppercase', color: '#B0453F', fontWeight: 700 }}>Maximum</div>
            <div style={{ fontSize: 26, fontWeight: 700, color: '#C0453F', fontVariantNumeric: 'tabular-nums', lineHeight: 1.15, marginTop: 3 }}>{d.loadMax}</div>
            <div style={{ fontSize: 11, color: '#C79490', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{d.loadMaxLead}</div>
          </div>
        </div>
        <div style={{ position: 'relative', height: 10, borderRadius: 5, margin: '6px 4px 0', background: 'linear-gradient(90deg,#4CA576,#5BA3D0,#C0453F)' }}>
          <div style={{ position: 'absolute', top: -5, left: `${d.avgPos}%`, transform: 'translateX(-50%)', width: 3, height: 20, background: '#0F2238', borderRadius: 2 }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', margin: '9px 4px 0', fontSize: 11, color: '#7A8C9C' }}>
          <span>Min {d.loadMin}</span>
          <span style={{ color: '#0F2238', fontWeight: 700 }}>Avg {d.loadAvg}</span>
          <span>Max {d.loadMax}</span>
        </div>
      </Card>

      {/* busiest TA lead staff */}
      <Card style={{ marginTop: 16 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
          <div style={bigCardTitle}>Busiest TA lead staff <span style={{ fontWeight: 400, color: '#9AA7B2', fontSize: 12 }}>— bar coloured by implementation status</span></div>
          <div style={{ fontSize: 12, color: '#7A8C9C' }}>{d.distinctStaff} distinct leads · <span style={{ color: '#C0453F', fontWeight: 700 }}>{d.unassigned}</span> requests unassigned</div>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px 16px', marginBottom: 16 }}>
          {d.staffLegend.map((s) => (
            <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ width: 11, height: 11, borderRadius: 3, background: s.color, display: 'inline-block' }} />
              <span style={{ fontSize: 11.5, color: '#43586B' }}>{s.label}</span>
            </div>
          ))}
        </div>
        <div style={{ columnCount: 2, columnGap: 40, maxHeight: 340, overflowY: 'auto', paddingRight: 6 }}>
          {d.staffBars.map((row) => (
            <div key={row.label} style={{ display: 'grid', gridTemplateColumns: '185px 1fr 34px', alignItems: 'center', gap: 10, breakInside: 'avoid', marginBottom: 11 }}>
              <div style={{ fontSize: 12, color: '#43586B', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{row.label}</div>
              <StackTrack row={row} height={11} />
              <div style={{ fontSize: 12, fontWeight: 700, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{row.n}</div>
            </div>
          ))}
        </div>
      </Card>
      </>
      )}
    </>
  );
}
