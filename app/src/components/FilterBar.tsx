import type { ChangeEvent } from 'react';
import type { SelectOption, StatusChip, ToggleButton } from '../lib/dashboard';

const labelStyle: React.CSSProperties = {
  fontSize: 10,
  letterSpacing: '.12em',
  textTransform: 'uppercase',
  color: '#7A8C9C',
  fontWeight: 700,
  marginBottom: 6,
};

const selectStyle: React.CSSProperties = {
  fontFamily: 'inherit',
  fontSize: 12.5,
  color: '#0F2238',
  backgroundColor: '#fff',
  border: '1px solid #D5DEE6',
  borderRadius: 8,
  padding: '8px 30px 8px 12px',
  cursor: 'pointer',
};

interface FilterBarProps {
  viewTabs: ToggleButton[];
  onView: (label: string) => void;
  typeBtns: ToggleButton[];
  onType: (v: string) => void;
  practice: string;
  practiceOpts: SelectOption[];
  onPractice: (v: string) => void;
  region: string;
  regionOpts: SelectOption[];
  onRegion: (v: string) => void;
  office: string;
  officeOpts: SelectOption[];
  onOffice: (v: string) => void;
  statusChips: StatusChip[];
  onToggleStatus: (v: string) => void;
  quarterChips: ToggleButton[];
  onToggleQuarter: (v: string) => void;
  onReset: () => void;
}

export function FilterBar({
  viewTabs,
  onView,
  typeBtns,
  onType,
  practice,
  practiceOpts,
  onPractice,
  region,
  regionOpts,
  onRegion,
  office,
  officeOpts,
  onOffice,
  statusChips,
  onToggleStatus,
  quarterChips,
  onToggleQuarter,
  onReset,
}: FilterBarProps) {
  return (
    <div
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 30,
        background: 'rgba(237,241,244,.93)',
        backdropFilter: 'blur(8px)',
        borderBottom: '1px solid #DCE3EA',
      }}
    >
      <div style={{ maxWidth: 1340, margin: '0 auto', padding: '12px 24px' }}>
        {/* View tabs */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
          {viewTabs.map((v) => (
            <button
              key={v.label}
              onClick={() => onView(v.label)}
              style={{
                fontFamily: 'inherit',
                cursor: 'pointer',
                fontSize: 13.5,
                fontWeight: 700,
                padding: '9px 20px',
                borderRadius: 9,
                border: `1px solid ${v.bd}`,
                background: v.bg,
                color: v.fg,
              }}
            >
              {v.label}
            </button>
          ))}
        </div>

        <div style={{ display: 'flex', gap: 18, flexWrap: 'wrap', alignItems: 'flex-end' }}>
          {/* Type segmented (prominent) */}
          <div>
            <div style={{ fontSize: 11, letterSpacing: '.12em', textTransform: 'uppercase', color: '#0B5A8A', fontWeight: 800, marginBottom: 7 }}>
              Request type
            </div>
            <div
              style={{
                display: 'inline-flex',
                background: '#fff',
                border: '2px solid #0B6FA4',
                borderRadius: 11,
                padding: 4,
                gap: 3,
                boxShadow: '0 2px 8px rgba(11,111,164,.14)',
              }}
            >
              {typeBtns.map((t) => (
                <button
                  key={t.label}
                  onClick={() => onType(t.label)}
                  style={{
                    border: 'none',
                    cursor: 'pointer',
                    fontFamily: 'inherit',
                    fontSize: 15,
                    fontWeight: 700,
                    padding: '10px 22px',
                    borderRadius: 8,
                    background: t.bg,
                    color: t.fg,
                  }}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* Practice select */}
          <div>
            <div style={labelStyle}>Practice / sector</div>
            <select
              value={practice}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => onPractice(e.target.value)}
              style={{ ...selectStyle, minWidth: 200 }}
            >
              <option value="All">All practices</option>
              {practiceOpts.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>

          {/* Region select */}
          <div>
            <div style={labelStyle}>Region</div>
            <select
              value={region}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => onRegion(e.target.value)}
              style={{ ...selectStyle, minWidth: 160 }}
            >
              <option value="All">All regions</option>
              {regionOpts.map((r) => (
                <option key={r.value} value={r.value}>
                  {r.label}
                </option>
              ))}
            </select>
          </div>

          {/* Country office select */}
          <div>
            <div style={labelStyle}>Country office</div>
            <select
              value={office}
              onChange={(e: ChangeEvent<HTMLSelectElement>) => onOffice(e.target.value)}
              style={{ ...selectStyle, minWidth: 180 }}
            >
              <option value="All">All countries</option>
              {officeOpts.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>

          <div style={{ flex: 1 }} />
          <button
            onClick={onReset}
            style={{
              border: '1px solid #D5DEE6',
              background: '#fff',
              cursor: 'pointer',
              fontFamily: 'inherit',
              fontSize: 12,
              fontWeight: 600,
              color: '#5B7186',
              padding: '8px 14px',
              borderRadius: 8,
              alignSelf: 'flex-end',
            }}
          >
            Reset filters
          </button>
        </div>

        {/* Status + Quarter chips */}
        <div style={{ display: 'flex', gap: 26, flexWrap: 'wrap', marginTop: 12 }}>
          <div>
            <div style={labelStyle}>Implementation status</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {statusChips.map((ch) => (
                <button
                  key={ch.label}
                  onClick={() => onToggleStatus(ch.label)}
                  style={{
                    fontFamily: 'inherit',
                    cursor: 'pointer',
                    padding: '5px 11px',
                    borderRadius: 999,
                    fontSize: 11.5,
                    fontWeight: 600,
                    border: `1px solid ${ch.bd}`,
                    background: ch.bg,
                    color: ch.fg,
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  <span style={{ width: 8, height: 8, borderRadius: 2, background: ch.dot, display: 'inline-block' }} />
                  {ch.label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <div style={labelStyle}>Expected completion quarter</div>
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {quarterChips.map((ch) => (
                <button
                  key={ch.label}
                  onClick={() => onToggleQuarter(ch.label)}
                  style={{
                    fontFamily: 'inherit',
                    cursor: 'pointer',
                    padding: '5px 11px',
                    borderRadius: 999,
                    fontSize: 11.5,
                    fontWeight: 600,
                    border: `1px solid ${ch.bd}`,
                    background: ch.bg,
                    color: ch.fg,
                  }}
                >
                  {ch.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
