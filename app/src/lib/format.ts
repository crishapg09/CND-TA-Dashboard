export function mean(values: number[]): number | null {
  return values.length ? values.reduce((x, y) => x + y, 0) / values.length : null;
}

export function median(values: number[]): number | null {
  if (!values.length) return null;
  const sorted = [...values].sort((x, y) => x - y);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

export function p90(values: number[]): number | null {
  if (!values.length) return null;
  const sorted = [...values].sort((x, y) => x - y);
  return sorted[Math.floor(0.9 * (sorted.length - 1))];
}

export function fmtDays(n: number | null): string {
  return n == null ? '—' : Math.round(n) + 'd';
}

export function fmtNum(n: number | null): string {
  return n == null ? '—' : Number(n).toLocaleString('en-US');
}

export function pct(n: number, d: number): number {
  return d ? Math.round((n / d) * 100) : 0;
}
