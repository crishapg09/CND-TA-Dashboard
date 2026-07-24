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
  /** TA lead's title, from the staff roster join on lead = staff name (derived at load) */
  leadTitle?: string;
  /** TA lead's thematic area, from the staff roster join (derived at load) */
  leadArea?: string;
  /** TA lead's duty-station location, from the staff roster join (derived at load) */
  leadLocation?: string;
}

/** One member of the CND staff roster (see scripts/extract_staff.py). */
export interface Staff {
  name: string;
  title: string;
  /** thematic area / sub-team, e.g. "Food Systems for Children" */
  area: string;
  /** duty station, e.g. "Nairobi" (blank when not recorded) */
  location: string;
}
