// Horizontal probability bars for the 10 labels (X-ray mode). Detected labels are bold and colored.
import type { SkillProbs } from '../api/models';
import { usePrefs } from '../i18n';
import { EVENT_THRESHOLD, LABELS, LABEL_COLOR } from '../lib/labels';

export function ProbBars({ probs, compact = false }: { probs: SkillProbs; compact?: boolean }) {
  const { t } = usePrefs();
  const rows = LABELS.filter((label) => probs[label] !== undefined)
    .map((label) => ({ label, p: probs[label] ?? 0 }))
    .sort((a, b) => b.p - a.p)
    .slice(0, compact ? 4 : 10);
  return (
    <ul className="space-y-1">
      {rows.map(({ label, p }) => {
        const on = p >= EVENT_THRESHOLD;
        return (
          <li key={label} className="grid grid-cols-[7.5rem_1fr_2.5rem] items-center gap-2 text-[11px]">
            <span className={`truncate ${on ? 'font-semibold text-ink' : 'text-muted'}`}>{t(`labels.${label}`)}</span>
            <span className="relative h-1.5 overflow-hidden rounded-full bg-line/70" aria-hidden="true">
              <span
                className="absolute inset-y-0 left-0 rounded-full transition-[width] duration-700"
                style={{ width: `${Math.round(p * 100)}%`, background: on ? LABEL_COLOR[label] : 'rgb(var(--muted) / 0.45)' }}
              />
              <span className="absolute inset-y-0 w-px bg-ink/30" style={{ left: `${EVENT_THRESHOLD * 100}%` }} />
            </span>
            <span className={`mono-num text-right ${on ? 'text-ink' : 'text-muted'}`}>{p.toFixed(2)}</span>
          </li>
        );
      })}
    </ul>
  );
}
