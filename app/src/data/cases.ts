import rawCases from './cases.json';
import rawToday from './today.json';
import type { TACase } from './types';
import { quarter } from '../lib/dates';
import { mapOffice } from '../lib/regionMap';

/**
 * Source: UNICEF TA case export, Jan–Jul 2026 (4,369 rows, as of 22 Jul 2026).
 * Dates are Excel serial day numbers (matches the source export).
 * Each record's office and region are corrected via the Regions & Countries
 * reference (see lib/regionMap), and annotated with its expected-completion
 * quarter (`q`). Offices the reference doesn't cover fall into region "Unmapped".
 */
export const RAW_CASES = (rawCases as unknown as TACase[]).map((c) => {
  const { office, region } = mapOffice(c.office);
  return { ...c, office, region, q: quarter(c.xc) };
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
