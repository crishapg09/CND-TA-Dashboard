import type { KPI } from '../lib/dashboard';

export function KpiStrip({ kpis }: { kpis: KPI[] }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(150px, 100%), 1fr))', gap: 12, marginTop: 8 }}>
      {kpis.map((k) => (
        <div
          key={k.label}
          style={{
            background: '#fff',
            border: '1px solid #E3E9EF',
            borderTop: `3px solid ${k.accent}`,
            borderRadius: 10,
            padding: '15px 16px',
          }}
        >
          <div style={{ fontSize: 10.5, letterSpacing: '.1em', textTransform: 'uppercase', color: '#7A8C9C', fontWeight: 700, minHeight: 26 }}>
            {k.label}
          </div>
          <div
            style={{
              fontSize: 30,
              fontWeight: 700,
              letterSpacing: '-.02em',
              color: k.color,
              fontVariantNumeric: 'tabular-nums',
              lineHeight: 1.1,
              marginTop: 4,
            }}
          >
            {k.value}
          </div>
          <div style={{ fontSize: 11.5, color: '#7A8C9C', marginTop: 3 }}>{k.sub}</div>
        </div>
      ))}
    </div>
  );
}
