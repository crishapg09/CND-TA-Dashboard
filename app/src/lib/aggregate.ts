import type { TACase } from '../data/types';

export interface BarRow {
  label: string;
  n: number;
}

export interface ColoredBarRow extends BarRow {
  color: string;
  pct: number;
}

export function groupBy(cases: TACase[], key: keyof TACase): BarRow[] {
  const counts = new Map<string, number>();
  for (const c of cases) {
    const k = (c[key] as string) || '—';
    counts.set(k, (counts.get(k) || 0) + 1);
  }
  return [...counts.entries()]
    .map(([label, n]) => ({ label, n }))
    .sort((a, b) => b.n - a.n);
}

export function toBars(rows: BarRow[], color: string, limit: number): ColoredBarRow[] {
  const max = Math.max(1, ...rows.map((r) => r.n));
  return rows.slice(0, limit).map((r) => ({ ...r, color, pct: Math.round((r.n / max) * 100) }));
}

/** Distinct values of a field across cases, sorted by frequency desc then alphabetically, as [value, count] pairs. */
export function optionCounts(cases: TACase[], key: keyof TACase): [string, number][] {
  const counts = new Map<string, number>();
  for (const c of cases) {
    const v = c[key] as string;
    if (v) counts.set(v, (counts.get(v) || 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}
