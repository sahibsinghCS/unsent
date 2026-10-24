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

const custom = new Map<string, Promise<ScenarioSummary>>();

/**
 * Scenario info by id. Custom friends ("custom-…") aren't in /api/scenarios, so they're looked up
 * with GET /api/friends/{id} (404 once the server has deleted them).
 */
export async function scenarioById(id: string, lang = 'en'): Promise<ScenarioSummary | undefined> {
  if (id.startsWith('custom-')) {
    let found = custom.get(id);
    if (!found) {
      found = api.friend(id).catch((error) => {
        custom.delete(id);
        throw error;
      });
      custom.set(id, found);
    }
    return found;
  }
  return (await scenarioList(lang)).find((s) => s.id === id);
}

/** True when this friend can be practiced in `lang` (older APIs without `locales` mean English only). */
export const supportsLang = (scenario: ScenarioSummary, lang: string) => (scenario.locales ?? ['en']).includes(lang);
