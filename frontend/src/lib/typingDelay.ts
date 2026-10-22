/**
 * How long the friend "types" before a bubble appears: longer messages take longer, like a real
 * person, clamped so short texts don't feel instant and long ones don't drag.
 *   delay = clamp(400 + 35 × characters, 800, 3500) ms, and 0 when the user prefers reduced motion.
 */
export function typingDelay(text: string, reducedMotion = false): number {
  if (reducedMotion) return 0;
  const raw = 400 + 35 * [...text].length;
  return Math.min(3500, Math.max(800, raw));
}

/** True when the OS asks for reduced motion (safe to call during tests/SSR). */
export function prefersReducedMotion(): boolean {
  return typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
}
