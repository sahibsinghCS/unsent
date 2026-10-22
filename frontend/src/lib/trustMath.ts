/**
 * "The trust math" shown in X-ray mode, e.g. "+12 validated · −2 decay = +10".
 *
 * The API gives us the real total change (state_after.last_delta) and the detected labels, but not
 * the engine's per-label breakdown. We show each detected label's nominal weight (the published
 * engine weights in backend/app/engine/config.yaml) and put whatever is left over (decay per turn,
 * the guarded-persona multiplier, the 0–100 cap...) into one "other" term, so the shown equation
 * always adds up to the engine's actual number.
 */
import type { SkillLabel, SkillProbs } from '../api/models';
import { activeLabels } from './labels';

export const LABEL_WEIGHTS: Record<SkillLabel, number> = {
  checked_in: 8,
  validated: 12,
  asked_directly: 15,
  encouraged_help: 6,
  referred_adult: 8,
  referred_988: 6,
  follow_up: 5,
  dismissed: -20,
  advice_dump: -10,
  promised_secrecy: -15,
};
export const DECAY_PER_TURN = 2;

export interface TrustTerm {
  /** A label id, or "decay" / "other" for the remainder. */
  key: string;
  value: number;
}

/** Signed number with a real minus sign: +12, −2, 0. */
export function signed(value: number, digits = 0): string {
  const rounded = Number(value.toFixed(digits));
  if (rounded === 0) return '0';
  const body = Math.abs(rounded).toFixed(digits);
  return rounded > 0 ? `+${body}` : `−${body}`;
}

/** Split a trust change into per-label terms plus a remainder that makes the sum exact. */
export function trustTerms(events: SkillProbs | null | undefined, delta: number): TrustTerm[] {
  const terms: TrustTerm[] = activeLabels(events).map((label) => ({ key: label, value: LABEL_WEIGHTS[label] }));
  const remainder = Math.round((delta - terms.reduce((sum, t) => sum + t.value, 0)) * 10) / 10;
  if (remainder !== 0) terms.push({ key: remainder === -DECAY_PER_TURN ? 'decay' : 'other', value: remainder });
  return terms;
}

/**
 * Format the equation. `name` turns a term key into words (translated label names).
 *   formatTrustMath([{validated, 12}, {decay, -2}], 10) → "+12 validated · −2 decay = +10"
 */
export function formatTrustMath(terms: TrustTerm[], delta: number, name: (key: string) => string = (k) => k.replace(/_/g, ' ')): string {
  const total = signed(delta, Number.isInteger(delta) ? 0 : 1);
  if (terms.length === 0) return `${total}`;
  const parts = terms.map((t) => `${signed(t.value, Number.isInteger(t.value) ? 0 : 1)} ${name(t.key)}`);
  return `${parts.join(' · ')} = ${total}`;
}
