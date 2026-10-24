/**
 * The trust readout: a big number that counts to its new value, a thin bar (0–100) in the action
 * color and the last change. Used in the chat side panel. Respects reduced motion.
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

export function TrustMeter({ value, delta, label }: { value: number; delta?: number; label: string; size?: 'sm' | 'md' }) {
  const shown = Math.max(0, Math.min(100, useCountUp(value)));
  return (
    <div className="w-40" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(value)} aria-label={label}>
      <div className="flex items-baseline justify-end gap-2">
        {delta !== undefined && delta !== 0 && (
          <span key={value} className={`text-sm font-semibold tabular-nums ${delta > 0 ? 'text-good' : 'text-bad'}`}>
            {signed(delta)}
          </span>
        )}
        <span className="numeral text-4xl">{Math.round(shown)}</span>
        <span className="text-sm text-muted">/100</span>
      </div>
      <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-sunken" aria-hidden="true">
        <div className="h-full rounded-full bg-brand" style={{ width: `${shown}%` }} />
      </div>
    </div>
  );
}
