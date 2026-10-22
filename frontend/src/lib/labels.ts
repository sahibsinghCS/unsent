// Display metadata for the 10 skill labels and 7 rubric skills (mirrors backend/app/contracts.py).
import type { SkillLabel, SkillProbs } from '../api/models';

export const LABELS: SkillLabel[] = [
  'checked_in',
  'validated',
  'asked_directly',
  'encouraged_help',
  'referred_adult',
  'referred_988',
  'follow_up',
  'dismissed',
  'advice_dump',
  'promised_secrecy',
];
export const NEGATIVE: ReadonlySet<SkillLabel> = new Set(['dismissed', 'advice_dump', 'promised_secrecy']);
export const isNegative = (label: string) => NEGATIVE.has(label as SkillLabel);

/** The 7 rubric skills (docs/RUBRIC.md), in order. */
export const RUBRIC_SKILLS = ['check_in', 'listen', 'ask_directly', 'no_secrecy', 'persuade', 'refer', 'follow_up'] as const;

/** Same threshold the engine uses (engine/config.yaml `event_threshold`). */
export const EVENT_THRESHOLD = 0.5;

/** One color per label: cool/green hues help, warm/red hues hurt. Used for chips and chart markers. */
export const LABEL_COLOR: Record<SkillLabel, string> = {
  checked_in: '#0ea5e9',
  validated: '#10b981',
  asked_directly: '#8b5cf6',
  encouraged_help: '#14b8a6',
  referred_adult: '#f59e0b',
  referred_988: '#eab308',
  follow_up: '#6366f1',
  dismissed: '#ef4444',
  advice_dump: '#f97316',
  promised_secrecy: '#db2777',
};
export const NEUTRAL_COLOR = '#94a3b8';

/** Labels whose probability reaches the threshold, strongest first. */
export function activeLabels(probs: SkillProbs | null | undefined, threshold = EVENT_THRESHOLD): SkillLabel[] {
  if (!probs) return [];
  return (Object.entries(probs) as [SkillLabel, number][])
    .filter(([, p]) => p >= threshold)
    .sort((a, b) => b[1] - a[1])
    .map(([label]) => label);
}

/** The single strongest detected label, or null if nothing was detected. */
export function strongestLabel(probs: SkillProbs | null | undefined): SkillLabel | null {
  return activeLabels(probs)[0] ?? null;
}
