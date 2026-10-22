/**
 * "The trust math" shown in X-ray mode, e.g. "+12 validated · +15 asked directly · −2 decay = +25".
 *
 * The engine sends its own breakdown of every trust change (State.last_breakdown): one term per
 * detected label plus engine terms like "decay", "diminishing" or "secrecy_broken", summing to
 * last_delta. We show exactly those numbers. If a breakdown is missing (older or stub engines), we
 * show only the total change rather than guessing how it splits.
 */

export interface TrustTerm {
  /** A label id or an engine term ("decay", "diminishing", "secrecy_broken", ...). */
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

/** Signed with one decimal only when needed (+12, −2.5). */
export const signedAuto = (value: number) => signed(value, Number.isInteger(Number(value.toFixed(1))) ? 0 : 1);

/** The engine's breakdown as display terms, in the engine's order, skipping zero terms. */
export function trustTerms(breakdown: Record<string, number> | null | undefined): TrustTerm[] {
  return Object.entries(breakdown ?? {})
    .filter(([, value]) => typeof value === 'number' && Math.abs(value) >= 0.05)
    .map(([key, value]) => ({ key, value }));
}

/**
 * Format the equation. `name` turns a term key into words (translated label names).
 *   formatTrustMath([{validated, 12}, {decay, -2}], 10) → "+12 validated · −2 decay = +10"
 */
export function formatTrustMath(terms: TrustTerm[], delta: number, name: (key: string) => string = (k) => k.replace(/_/g, ' ')): string {
  const total = signedAuto(delta);
  if (terms.length === 0) return total;
  return `${terms.map((t) => `${signedAuto(t.value)} ${name(t.key)}`).join(' · ')} = ${total}`;
}
