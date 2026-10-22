// Scenario list cached for the whole visit (chat and feedback need the friend's name).
import { api } from '../api/client';
import type { ScenarioSummary } from '../api/models';

let cache: Promise<ScenarioSummary[]> | null = null;

export function scenarioList(): Promise<ScenarioSummary[]> {
  cache ??= api.scenarios().catch((error) => {
    cache = null; // retry next time
    throw error;
  });
  return cache;
}

export async function scenarioById(id: string): Promise<ScenarioSummary | undefined> {
  return (await scenarioList()).find((s) => s.id === id);
}
