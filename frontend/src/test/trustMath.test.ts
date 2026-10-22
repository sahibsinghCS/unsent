import { formatTrustMath, signed, trustTerms } from '../lib/trustMath';

describe('signed', () => {
  it('uses a plus sign, a real minus sign and plain zero', () => {
    expect(signed(12)).toBe('+12');
    expect(signed(-2)).toBe('−2');
    expect(signed(0)).toBe('0');
    expect(signed(0.4, 1)).toBe('+0.4');
    expect(signed(-0.04, 1)).toBe('0');
  });
});

describe('trust math', () => {
  it('formats the README example: +12 validated · −2 decay = +10', () => {
    const terms = trustTerms({ validated: 0.9, dismissed: 0.05 }, 10);
    expect(terms).toEqual([
      { key: 'validated', value: 12 },
      { key: 'decay', value: -2 },
    ]);
    expect(formatTrustMath(terms, 10)).toBe('+12 validated · −2 decay = +10');
  });

  it('lists several labels strongest first', () => {
    const terms = trustTerms({ validated: 0.8, referred_adult: 0.9, follow_up: 0.7 }, 23);
    expect(terms.map((t) => t.key)).toEqual(['referred_adult', 'validated', 'follow_up', 'decay']);
    expect(formatTrustMath(terms, 23)).toBe('+8 referred adult · +12 validated · +5 follow up · −2 decay = +23');
  });

  it('puts any unexplained difference into "other" so the equation always adds up', () => {
    // e.g. a guarded persona's multiplier or the 0–100 cap changed the real delta
    const terms = trustTerms({ asked_directly: 0.95 }, 8.5);
    expect(terms).toEqual([
      { key: 'asked_directly', value: 15 },
      { key: 'other', value: -6.5 },
    ]);
    const sum = terms.reduce((s, t) => s + t.value, 0);
    expect(sum).toBeCloseTo(8.5);
  });

  it('shows negative labels as negative terms', () => {
    const terms = trustTerms({ dismissed: 0.9 }, -22);
    expect(formatTrustMath(terms, -22)).toBe('−20 dismissed · −2 decay = −22');
  });

  it('handles messages with no events and no change', () => {
    expect(trustTerms(null, 0)).toEqual([]);
    expect(formatTrustMath([], 0)).toBe('0');
  });

  it('uses translated names when given', () => {
    const terms = trustTerms({ validated: 0.9 }, 10);
    expect(formatTrustMath(terms, 10, (k) => ({ validated: 'validó', decay: 'desgaste' })[k] ?? k)).toBe('+12 validó · −2 desgaste = +10');
  });
});
