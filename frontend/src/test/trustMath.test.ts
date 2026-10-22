import { clampNote, formatTrustMath, signed, trustTerms } from '../lib/trustMath';

describe('signed', () => {
  it('uses a plus sign, a real minus sign and plain zero', () => {
    expect(signed(12)).toBe('+12');
    expect(signed(-2)).toBe('−2');
    expect(signed(0)).toBe('0');
    expect(signed(0.4, 1)).toBe('+0.4');
    expect(signed(-0.04, 1)).toBe('0');
  });
});

describe('trust math (engine breakdown, State.last_breakdown)', () => {
  it('formats the engine breakdown in its own order', () => {
    const terms = trustTerms({ validated: 12, asked_directly: 15, decay: -2 });
    expect(formatTrustMath(terms, 25)).toBe('+12 validated · +15 asked directly · −2 decay = +25');
  });

  it('shows negative and engine terms (diminishing, secrecy broken)', () => {
    const terms = trustTerms({ dismissed: -20, secrecy_broken: -10, decay: -2 });
    expect(formatTrustMath(terms, -32)).toBe('−20 dismissed · −10 secrecy broken · −2 decay = −32');
  });

  it('keeps one decimal for fractional terms (e.g. the guarded multiplier)', () => {
    const terms = trustTerms({ validated: 8.4, diminishing: -1.5, decay: -2 });
    expect(formatTrustMath(terms, 4.9)).toBe('+8.4 validated · −1.5 diminishing · −2 decay = +4.9');
  });

  it('skips zero terms', () => {
    expect(trustTerms({ validated: 12, decay: 0 })).toEqual([{ key: 'validated', value: 12 }]);
  });

  it('shows just the total when the breakdown is empty or missing (never guesses a split)', () => {
    expect(trustTerms({})).toEqual([]);
    expect(trustTerms(undefined)).toEqual([]);
    expect(formatTrustMath([], 10)).toBe('+10');
    expect(formatTrustMath([], -22)).toBe('−22');
    expect(formatTrustMath([], 0)).toBe('0');
  });

  it('uses translated names when given', () => {
    const terms = trustTerms({ validated: 12, decay: -2 });
    expect(formatTrustMath(terms, 10, (k) => ({ validated: 'validó', decay: 'desgaste' })[k] ?? k)).toBe('+12 validó · −2 desgaste = +10');
  });
});

describe('engine breakdown example and clamping', () => {
  it('renders the engine example with one decimal', () => {
    const terms = trustTerms({ validated: 8.4, diminishing: -4.2, decay: -2 });
    expect(formatTrustMath(terms, 2.2, (k) => ({ diminishing: 'repeated', decay: 'time' })[k] ?? k)).toBe('+8.4 validated · −4.2 repeated · −2 time = +2.2');
  });

  it('flags when trust was clamped at 0 (fixture: 5 → 0 with a raw change of −22)', () => {
    const fixture = { before: 5, after: 0, breakdown: { dismissed: -20, decay: -2 }, last_delta: -22 };
    expect(formatTrustMath(trustTerms(fixture.breakdown), fixture.last_delta)).toBe('−20 dismissed · −2 decay = −22');
    expect(clampNote(fixture.before, fixture.after, fixture.last_delta)).toEqual({ bound: 0, actual: -5 });
  });

  it('flags clamping at 100 and stays quiet when nothing was clamped', () => {
    expect(clampNote(95, 100, 23)).toEqual({ bound: 100, actual: 5 });
    expect(clampNote(37, 60, 23)).toBeNull();
    expect(clampNote(30, 32.2, 2.2)).toBeNull();
  });
});
