// Scenario lists cached per language for the whole visit (chat and feedback need the friend's name).
import { api } from '../api/client';
import type { ScenarioSummary } from '../api/models';

const cache = new Map<string, Promise<ScenarioSummary[]>>();

/** Scenarios with title, situation and content warning in `lang` (the API falls back to English). */
export function scenarioList(lang = 'en'): Promise<ScenarioSummary[]> {
  let list = cache.get(lang);
  if (!list) {
    list = api.scenarios(lang).catch((error) => {
      cache.delete(lang); // retry next time
      throw error;
    });
    cache.set(lang, list);
  }
  return list;
}

export async function scenarioById(id: string, lang = 'en'): Promise<ScenarioSummary | undefined> {
  return (await scenarioList(lang)).find((s) => s.id === id);
}

/** True when this friend can be practiced in `lang` (older APIs without `locales` mean English only). */
export const supportsLang = (scenario: ScenarioSummary, lang: string) => (scenario.locales ?? ['en']).includes(lang);
