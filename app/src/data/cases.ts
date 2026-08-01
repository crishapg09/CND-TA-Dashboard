import rawCases from './cases.json';
import rawToday from './today.json';
import rawStaff from './staff.json';
import type { TACase, Staff } from './types';
import { quarter } from '../lib/dates';
import { mapOffice } from '../lib/regionMap';

/**
 * The CND staff roster, keyed by name for the case join.
 * Source: CND_staff export (see scripts/extract_staff.py).
 */
export const STAFF = rawStaff as unknown as Staff[];
const STAFF_BY_NAME = new Map(STAFF.map((s) => [s.name, s]));

/**
 * Source: UNICEF TA case export, Jan–Jul 2026 (354 rows, as of 31 Jul 2026).
 * Dates are Excel serial day numbers (matches the source export).
 * Each record's office and region are corrected via the Regions & Countries
 * reference (see lib/regionMap), and annotated with its expected-completion
 * quarter (`q`). The TA lead ("Assigned to") is joined to the staff roster on
 * lead = staff name, attaching the lead's title, thematic area and location.
 * Offices the reference doesn't cover fall into region "Unmapped".
 */
export const RAW_CASES = (rawCases as unknown as TACase[]).map((c) => {
  const { office, region } = mapOffice(c.office);
  const staff = c.lead ? STAFF_BY_NAME.get(c.lead) : undefined;
  return {
    ...c,
    office,
    region,
    q: quarter(c.xc),
    leadTitle: staff?.title || '',
    leadArea: staff?.area || '',
    leadLocation: staff?.location || '',
  };
});

/**
 * The reporting universe for the Performance view: excludes HQ offices,
 * Discontinued requests, and "Unmapped" offices (regional/HQ divisions and
 * blank offices the reference doesn't cover). The Data Quality view uses
 * RAW_CASES (the full export), so nothing is hidden there.
 */
export const CASES = RAW_CASES.filter(
  (c) => c.region !== 'HQ' && c.region !== 'Unmapped' && c.status !== 'Discontinued',
);

/** Selectable expected-completion quarters (2026, ascending). */
export const QUARTERS = [...new Set(CASES.map((c) => c.q).filter(Boolean))]
  .filter((q): q is string => !!q && q.startsWith('2026'))
  .sort();

/** "As of" date for the dataset, as an Excel serial day number. */
export const TODAY = rawToday as unknown as number;
