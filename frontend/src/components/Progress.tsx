// Disclosure ladder (how much the friend has shared, levels 0–4) and skill chips.
import type { SkillLabel } from '../api/models';
import { usePrefs } from '../i18n';
import { LABELS, LABEL_COLOR, isNegative } from '../lib/labels';

export function DisclosureLadder({ level }: { level: number }) {
  const { t, tl } = usePrefs();
  const names = tl('chat.levels');
  return (
    <ol className="space-y-1" aria-label={t('chat.ladder')}>
      {[4, 3, 2, 1, 0].map((n) => {
        const reached = level >= n;
        const current = level === n;
        return (
          <li
            key={n}
            aria-current={current ? 'step' : undefined}
            className={`flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-xs transition ${
              current ? 'bg-brand text-brand-ink font-semibold shadow-card' : reached ? 'bg-brand-soft text-ink' : 'text-muted'
            }`}
          >
            <span className={`mono-num grid h-5 w-5 shrink-0 place-items-center rounded-full text-[10px] font-bold ${current ? 'bg-white/25' : reached ? 'bg-brand/20' : 'border border-line'}`}>
              {n}
            </span>
            {names[n]}
          </li>
        );
      })}
    </ol>
  );
}

/** One chip per label; a chip lights up once the detector has seen that behaviour this conversation. */
export function SkillChips({ seen, latest }: { seen: Set<SkillLabel>; latest: Set<SkillLabel> }) {
  const { t } = usePrefs();
  return (
    <ul className="flex flex-wrap gap-1.5">
      {LABELS.map((label) => {
        const on = seen.has(label);
        const negative = isNegative(label);
        return (
          <li
            key={label}
            className={`chip transition ${latest.has(label) ? 'ring-2 ring-offset-1 ring-offset-surface' : ''} ${
              on ? (negative ? 'border-transparent bg-bad-soft text-bad' : 'border-transparent bg-good-soft text-good') : 'border-dashed border-line text-muted'
            }`}
            style={latest.has(label) ? ({ '--tw-ring-color': LABEL_COLOR[label] } as React.CSSProperties) : undefined}
          >
            <span className="h-1.5 w-1.5 rounded-full" style={{ background: on ? LABEL_COLOR[label] : 'rgb(var(--line))' }} aria-hidden="true" />
            {t(`labels.${label}`)}
            <span className="sr-only">{on ? '(used)' : '(not yet)'}</span>
          </li>
        );
      })}
    </ul>
  );
}
