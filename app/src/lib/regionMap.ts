import source from '../data/regionSource.json';

/**
 * Canonical country → region correction.
 * Source: "Regions & Countries 2026" reference sheet (127 offices) plus six
 * country offices the sheet omits (Uganda, Eswatini, Saudi Arabia, Oman,
 * Panama, Cabo Verde) and the DRC abbreviation. Offices the reference does not
 * cover — regional/HQ divisions and blank offices — fall through to "Unmapped".
 *
 * Note: the reference folds South Asia into APR, so the export's former SAR and
 * EAPR regions both become APR.
 */

/** Normalize an office name for tolerant matching (drops parentheticals, punctuation, and filler words). */
function norm(s: string | null | undefined): string {
  return (s || '')
    .toString()
    .toLowerCase()
    .replace(/\(.*?\)/g, ' ')
    .replace(/[.,''\-]/g, ' ')
    .replace(/\b(the|of|and|rep|republic|dem|state|united|people s|peoples|island s?)\b/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

export interface OfficeMapping {
  office: string;
  region: string;
}

const LOOKUP = new Map<string, OfficeMapping>();
for (const [country, region] of source as [string, string][]) {
  LOOKUP.set(norm(country), { office: country.trim(), region: region.trim() });
}

// Aliases: a differently-spelled office in the export → a canonical country already in the reference.
const ALIASES: [string, string, string][] = [
  ['DRC', 'Democratic Republic of Congo', 'WCAR'],
  ['Pacific', 'Fiji (Pacific Islands)', 'APR'],
  ['Solomon, Republic of Marshall Islands', 'Fiji (Pacific Islands)', 'APR'],
];
for (const [alias, country, region] of ALIASES) {
  LOOKUP.set(norm(alias), { office: country, region });
}

/** Return the corrected office name and region for a raw office value. */
export function mapOffice(raw: string | null | undefined): OfficeMapping {
  return LOOKUP.get(norm(raw)) || { office: (raw || '').trim(), region: 'Unmapped' };
}
