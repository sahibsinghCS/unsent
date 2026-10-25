// The landing page's example conversation: a real run of the app recorded by the repo's
// scripts/demo_transcript.py (`make demo-transcript`, FR_LLM=0, so Maya only uses reviewed lines) and
// copied into src/content by scripts/sync-content.mjs. Nothing here is hand-picked: the bubbles,
// skills, trust and Guardian times are what the engine produced.
import recorded from '../content/demo_transcript.json';
import type { Lang } from '../i18n';

export interface DemoTurn {
  you: string;
  friend: string[];
  seen: boolean;
  line_id: string | null;
  skills: string[];
  guardian: string;
  guardian_ms: number;
  trust_before: number;
  trust_after: number;
  level_after: number;
}

export interface DemoRun {
  scenario: string;
  opening: string[];
  turns: DemoTurn[];
}

export function demoRun(lang: Lang): DemoRun {
  return (lang === 'es' ? recorded.es : recorded.en) as DemoRun;
}

/** One-line annotation for a turn: the first skill heard, and how trust moved (rounded). */
export function turnSummary(turn: DemoTurn) {
  return { skill: turn.skills[0] ?? null, from: Math.round(turn.trust_before), to: Math.round(turn.trust_after), up: turn.trust_after >= turn.trust_before };
}
