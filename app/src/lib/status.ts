export const STATUS_ORDER = ['0%', '25%', '50%', '75%', '100%', 'Unassigned'] as const;

export const STATUS_COLORS: Record<string, string> = {
  '0%': '#D6E0E8',
  '25%': '#9CC6E0',
  '50%': '#5BA3D0',
  '75%': '#2C7DB5',
  '100%': '#0B5A8A',
  Discontinued: '#9AA7B2',
  Unassigned: '#E0A21E',
};

const DARK_STATUSES = new Set(['50%', '75%', '100%', 'Discontinued']);

export function statusChipStyle(status: string): { bg: string; fg: string } {
  return { bg: STATUS_COLORS[status], fg: DARK_STATUSES.has(status) ? '#fff' : '#1F3346' };
}
