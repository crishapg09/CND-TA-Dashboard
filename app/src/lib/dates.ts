const MONTH_ABBR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

/** Convert an Excel serial day number to a UTC Date. */
function excelToDate(serial: number): Date {
  return new Date(Math.round((serial - 25569) * 86400000));
}

/** Quarter label for an Excel serial date, e.g. "2026 Q2". Empty string when null. */
export function quarter(serial: number | null | undefined): string {
  if (serial == null) return '';
  const d = excelToDate(serial);
  return d.getUTCFullYear() + ' Q' + (Math.floor(d.getUTCMonth() / 3) + 1);
}

/** Format an Excel serial date as "06 Jul 2026". Em dash when null. */
export function formatDate(serial: number | null | undefined): string {
  if (serial == null) return '—';
  const d = excelToDate(serial);
  return (
    d.getUTCDate().toString().padStart(2, '0') + ' ' + MONTH_ABBR[d.getUTCMonth()] + ' ' + d.getUTCFullYear()
  );
}

/** 0-based month index if the serial date falls in 2026, else -1. */
export function monthIndex2026(serial: number | null | undefined): number {
  if (serial == null) return -1;
  const d = excelToDate(serial);
  return d.getUTCFullYear() === 2026 ? d.getUTCMonth() : -1;
}

export const MONTHS = MONTH_ABBR;
