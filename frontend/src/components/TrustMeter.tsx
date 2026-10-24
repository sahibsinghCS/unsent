/**
 * The trust meter: a semicircle gauge (0–100) in the accent color and a Syne number that counts to its
 * new value, with the last change under it. Used in the chat side panel. Respects reduced motion.
 */
import { useEffect, useRef, useState } from 'react';
import { prefersReducedMotion } from '../lib/typingDelay';
import { signed } from '../lib/trustMath';

/** Animate a number toward `target` (ease-out, ~600 ms); jumps straight there with reduced motion. */
export function useCountUp(target: number, duration = 600): number {
  const [value, setValue] = useState(target);
  const from = useRef(target);
  useEffect(() => {
    if (prefersReducedMotion() || typeof requestAnimationFrame === 'undefined') {
      from.current = target;
      setValue(target);
      return undefined;
    }
    const start = performance.now();
    const origin = from.current;
    let frame = 0;
    const tick = (now: number) => {
      const p = Math.min(1, (now - start) / duration);
      const next = origin + (target - origin) * (1 - Math.pow(1 - p, 3));
      from.current = next;
      setValue(next);
      if (p < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [target, duration]);
  return value;
}

export function TrustMeter({ value, delta, label, size = 'md' }: { value: number; delta?: number; label: string; size?: 'sm' | 'md' }) {
  const shown = Math.max(0, Math.min(100, useCountUp(value)));
  // Semicircle from 180° to 0°; arc length = π·r.
  const arc = Math.PI * 52;
  return (
    <div className={`relative ${size === 'sm' ? 'w-36' : 'w-44'}`} role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(value)} aria-label={label}>
      <svg viewBox="0 0 128 72" className="w-full" aria-hidden="true">
        <path d="M12 64 A52 52 0 0 1 116 64" fill="none" stroke="rgb(var(--sunken))" strokeWidth="9" strokeLinecap="round" />
        <path
          d="M12 64 A52 52 0 0 1 116 64"
          fill="none"
          stroke="rgb(var(--brand))"
          strokeWidth="9"
          strokeLinecap="round"
          strokeDasharray={arc}
          strokeDashoffset={arc * (1 - shown / 100)}
        />
      </svg>
      <div className="absolute inset-x-0 bottom-0 flex flex-col items-center leading-none">
        <span className={`numeral ${size === 'sm' ? 'text-3xl' : 'text-4xl'}`}>{Math.round(shown)}</span>
        {delta !== undefined && delta !== 0 && (
          <span key={value} className={`mono-num mt-1 animate-bump text-xs font-medium ${delta > 0 ? 'text-good' : 'text-bad'}`}>
            {signed(delta)}
          </span>
        )}
      </div>
    </div>
  );
}
