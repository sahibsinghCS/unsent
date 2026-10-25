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

/** Two annotation colors only: green for behaviours that help, red for ones that hurt (iOS-like). */
const HELPED = '#248A3D';
const HURT = '#D70015';
export const LABEL_COLOR: Record<SkillLabel, string> = {
  checked_in: HELPED,
  validated: HELPED,
  asked_directly: HELPED,
  encouraged_help: HELPED,
  referred_adult: HELPED,
  referred_988: HELPED,
  follow_up: HELPED,
  dismissed: HURT,
  advice_dump: HURT,
  promised_secrecy: HURT,
};
export const NEUTRAL_COLOR = '#8E8E93';

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
