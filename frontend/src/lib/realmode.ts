/**
 * Real mode must work even when the server is down, so the fixed crisis content is bundled into the
 * app (copied from content/ by scripts/sync-content.mjs at build time). This mirrors the backend's
 * crisis_lines_for() so the offline result has exactly the same shape as GET /api/realmode.
 */
import type { CrisisLine, RealMode } from '../api/models';
import { api } from '../api/client';
import crisisLines from '../content/crisis_lines.json';
import realmodeEn from '../content/realmode.en.json';
import realmodeEs from '../content/realmode.es.json';

export const COUNTRIES = ['US', 'CA', 'GB', 'AU', 'other'] as const;
export type Country = (typeof COUNTRIES)[number];

/** The country code the backend understands ("other" means the international fallback "*"). */
export const apiCountry = (country: string) => (country === 'other' ? '*' : country);

type CrisisFile = { lines: CrisisLine[]; emergency: Record<string, string>; verified_on: string | null };

/** Build the Real mode payload from the bundled copies, with no network. */
export function offlineRealMode(lang: string, country: string): RealMode {
  const base = (lang === 'es' ? realmodeEs : realmodeEn) as unknown as Omit<RealMode, 'crisis'>;
  const data = crisisLines as unknown as CrisisFile;
  const code = apiCountry(country);
  return {
    ...base,
    crisis: {
      country: code,
      lines: data.lines.filter((line) => line.country === code || line.country === '*'),
      emergency: data.emergency[code] ?? data.emergency['*'] ?? '',
      verified_on: data.verified_on,
    },
  };
}

/** Ask the API first; if it fails for any reason, fall back to the bundled copy. */
export async function loadRealMode(lang: string, country: string): Promise<{ data: RealMode; offline: boolean }> {
  try {
    const data = await api.realmode(lang, apiCountry(country));
    if (!data?.steps?.length) throw new Error('empty');
    return { data, offline: false };
  } catch {
    return { data: offlineRealMode(lang, country), offline: true };
  }
}
