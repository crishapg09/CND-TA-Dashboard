import type { ColoredBarRow } from '../lib/aggregate';

interface BarListProps {
  rows: ColoredBarRow[];
  labelWidth: number;
  trackBg: string;
  /** overrides row.color when set */
  barColor?: string;
  labelWeight?: number;
}

/** Simple label · track · count rows (used for the region/practice breakdown cards). */
export function BarList({ rows, labelWidth, trackBg, barColor, labelWeight = 600 }: BarListProps) {
  return (
    <>
      {rows.map((row) => (
        <div
          key={row.label}
          style={{ display: 'grid', gridTemplateColumns: `${labelWidth}px 1fr 34px`, alignItems: 'center', gap: 10, marginBottom: 9 }}
        >
          <div
            style={{
              fontSize: 12,
              color: '#43586B',
              fontWeight: labelWeight,
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            {row.label}
          </div>
          <div style={{ height: 9, background: trackBg, borderRadius: 5 }}>
            <div style={{ height: '100%', width: `${row.pct}%`, background: barColor || row.color, borderRadius: 5 }} />
          </div>
          <div style={{ fontSize: 12.5, fontWeight: 700, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{row.n}</div>
        </div>
      ))}
    </>
  );
}
