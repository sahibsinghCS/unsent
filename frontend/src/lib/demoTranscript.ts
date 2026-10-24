// The landing page's example conversation, recorded from a real run of the app by
// scripts/demo-transcript.mjs (FR_LLM=0, so every reply of Maya is a reviewed line). Nothing here is
// hand-picked: the bubbles, skills, trust and Guardian times are what the engine produced.
import recorded from '../content/demo-transcript.json';
import type { Lang } from '../i18n';

export interface DemoTurn {
  text: string;
  guardian: { level?: string; action?: string; ms: number };
  skills: string[];
  trust_before: number;
  trust_after: number;
  level_before: number;
  level_after: number;
  status: string;
  friend: { bubbles: string[]; line_id: string | null; voice: string | null; seen: boolean } | null;
}

export interface DemoRun {
  opening: string[];
  trust_start: number;
  turns: DemoTurn[];
}

export const DEMO_RECORDED_AT: string = recorded.recorded_at;

export function demoRun(lang: Lang): DemoRun {
  return (lang === 'es' ? recorded.es : recorded.en) as DemoRun;
}

/** One-line annotation for a helper turn: the strongest skill heard, and how trust moved (rounded). */
export function turnSummary(turn: DemoTurn) {
  const from = Math.round(turn.trust_before);
  const to = Math.round(turn.trust_after);
  return { skill: turn.skills[0] ?? null, from, to, up: turn.trust_after >= turn.trust_before };
}
