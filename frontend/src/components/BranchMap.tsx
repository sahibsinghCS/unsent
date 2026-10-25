/**
 * "Branching futures" for the What-if page: the message you sent on the left, a curve to each
 * simulated future on the right, ending at the trust it reached. The best one is marked with the word
 * "Best"; what really happened is the dashed red branch. HTML for the text (readable on phones) + one stretched SVG for curves.
 */
import { usePrefs } from '../i18n';
import { signed } from '../lib/trustMath';

export interface Branch {
  label: string;
  from: number;
  to: number;
  color: string;
  /** e.g. "in 3 messages" (what the Best ranking also weighs). */
  detail?: string;
  best?: boolean;
  actual?: boolean;
}

export function BranchMap({ origin, branches }: { origin: string; branches: Branch[] }) {
  const { t } = usePrefs();
  const n = branches.length;
  return (
    <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:gap-0" data-testid="branch-map">
      <div className="flex w-full shrink-0 items-center sm:w-56">
        <div className="w-full rounded-2xl border border-line bg-surface p-4">
          <p className="small-label mb-1.5">{t('whatif.you_said')}</p>
          <p className="text-sm leading-snug">{origin}</p>
        </div>
      </div>
      <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="hidden w-24 shrink-0 sm:block" aria-hidden="true">
        {branches.map((b, i) => {
          const y = ((i + 0.5) / n) * 100;
          return (
            <path
              key={i}
              d={`M0 50 C 55 50, 45 ${y}, 100 ${y}`}
              fill="none"
              stroke={b.color}
              strokeWidth={b.best ? 4 : 2}
              strokeDasharray={b.actual ? '5 5' : undefined}
              vectorEffect="non-scaling-stroke"
              opacity={b.actual ? 0.7 : 1}
            />
          );
        })}
      </svg>
      {/* Below sm: a vertical rail from "what you said" instead of the fork curves. */}
      <ol className="ml-4 flex min-w-0 flex-1 flex-col justify-around gap-2.5 border-l-2 border-line pl-4 sm:ml-0 sm:border-0 sm:pl-0">
        {branches.map((b, i) => (
          <li
            key={i}
            className={`flex items-center gap-3 rounded-2xl border px-3.5 py-3 ${
              b.best ? 'border-2 border-brand bg-surface' : b.actual ? 'border-dashed border-line bg-sunken/60' : 'border-line bg-surface'
            }`}
          >
            <span className="h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: b.color }} aria-hidden="true" />
            <span className="min-w-0 flex-1">
              <span className="block text-sm font-semibold leading-snug">
                {b.label}
                {b.best && <span className="chip ml-2 border-brand bg-brand align-middle font-semibold text-brand-ink">{t('whatif.best')}</span>}
              </span>
              <span className="mono-num block text-xs text-muted">
                <span className="whitespace-nowrap">{t('whatif.trust_end', { from: Math.round(b.from), to: Math.round(b.to) })}</span>
                {b.detail && <span className="whitespace-nowrap"> · {b.detail}</span>}
              </span>
            </span>
            <span className="text-right">
              <span className="numeral block text-2xl leading-none">{Math.round(b.to)}</span>
              <span className={`mono-num text-[11px] font-semibold ${b.to - b.from >= 0 ? 'text-good' : 'text-bad'}`}>{signed(Math.round(b.to - b.from))}</span>
            </span>
          </li>
        ))}
      </ol>
    </div>
  );
}
