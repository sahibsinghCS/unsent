/**
 * The trust meter: a semicircle gauge (0–100) with a dusk gradient and a number that counts to its
 * new value. Used in the chat side panel and the landing demo. Respects reduced motion.
 */
import { useEffect, useId, useRef, useState } from 'react';
import { prefersReducedMotion } from '../lib/typingDelay';
import { signed } from '../lib/trustMath';

/** Animate a number toward `target` (ease-out, ~700 ms); jumps straight there with reduced motion. */
export function useCountUp(target: number, duration = 700): number {
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
      const eased = 1 - Math.pow(1 - p, 3);
      const next = origin + (target - origin) * eased;
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
  const id = useId().replace(/:/g, '');
  const shown = useCountUp(value);
  const clamped = Math.max(0, Math.min(100, shown));
  // Semicircle from 180° to 0°; arc length = π·r.
  const r = 52;
  const arc = Math.PI * r;
  const width = size === 'sm' ? 'w-36' : 'w-48';
  return (
    <div className={`relative ${width}`} role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(value)} aria-label={label}>
      <svg viewBox="0 0 128 72" className="w-full" aria-hidden="true">
        <defs>
          <linearGradient id={`g${id}`} x1="0" x2="1">
            <stop offset="0" stopColor="rgb(var(--warm))" />
            <stop offset="0.5" stopColor="rgb(var(--brand-deep))" />
            <stop offset="1" stopColor="rgb(var(--brand))" />
          </linearGradient>
        </defs>
        <path d="M12 64 A52 52 0 0 1 116 64" fill="none" stroke="rgb(var(--line))" strokeWidth="10" strokeLinecap="round" />
        <path
          d="M12 64 A52 52 0 0 1 116 64"
          fill="none"
          stroke={`url(#g${id})`}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={arc}
          strokeDashoffset={arc * (1 - clamped / 100)}
        />
      </svg>
      <div className="absolute inset-x-0 bottom-0 flex flex-col items-center leading-none">
        <span className={`numeral ${size === 'sm' ? 'text-3xl' : 'text-4xl'}`}>{Math.round(clamped)}</span>
        {delta !== undefined && delta !== 0 && (
          <span key={value} className={`mt-1 animate-bump rounded-full px-2 py-0.5 text-xs font-bold ${delta > 0 ? 'bg-good-soft text-good' : 'bg-bad-soft text-bad'}`}>
            {signed(delta)}
          </span>
        )}
      </div>
    </div>
  );
}
