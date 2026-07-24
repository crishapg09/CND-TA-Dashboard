export type Status = '0%' | '25%' | '50%' | '75%' | '100%' | 'Discontinued' | 'Unassigned';

export interface TACase {
  id: string;
  type: string;
  region: string;
  office: string;
  practice: string;
  offer: string;
  modality: string;
  status: Status;
  lead: string;
  reqFor: string;
  desc: string;
  /** full (long) description, used for row tooltips */
  full?: string;
  /** expected start (Excel serial date) */
  xs: number | null;
  /** expected completion (Excel serial date) */
  xc: number | null;
  /** created (Excel serial date) */
  cr: number | null;
  /** opened (Excel serial date) */
  op: number | null;
  /** updated (Excel serial date) */
  up: number | null;
  /** resolved (Excel serial date) */
  rs: number | null;
  /** closed (Excel serial date) */
  cl: number | null;
  /** has description */
  hd: 0 | 1;
  /** has objectives */
  ho: 0 | 1;
  /** expected-completion quarter label, e.g. "2026 Q2" (derived at load) */
  q?: string;
}
