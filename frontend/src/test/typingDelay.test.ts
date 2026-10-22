import { typingDelay } from '../lib/typingDelay';

describe('typingDelay = clamp(400 + 35 × chars, 800, 3500)', () => {
  it('uses the formula in the middle of the range', () => {
    expect(typingDelay('a'.repeat(20))).toBe(400 + 35 * 20); // 1100
  });
  it('never goes below 800 ms for short texts', () => {
    expect(typingDelay('')).toBe(800);
    expect(typingDelay('ok')).toBe(800);
  });
  it('never goes above 3500 ms for long texts', () => {
    expect(typingDelay('a'.repeat(300))).toBe(3500);
  });
  it('hits the boundaries exactly', () => {
    expect(typingDelay('a'.repeat(12))).toBe(820);
    expect(typingDelay('a'.repeat(88))).toBe(3480);
  });
  it('counts emoji as one character', () => {
    expect(typingDelay('😭'.repeat(20))).toBe(1100);
  });
  it('is 0 when the user prefers reduced motion', () => {
    expect(typingDelay('a'.repeat(50), true)).toBe(0);
  });
});
