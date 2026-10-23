// Renders a helper message with the critic's word highlights: green = helped, red = hurt.
import type { Highlight } from '../api/models';
import { usePrefs } from '../i18n';
import { toSegments } from '../lib/highlight';

export function HighlightedText({ text, highlights }: { text: string; highlights?: Highlight[] | null }) {
  const { t } = usePrefs();
  return (
    <span data-testid="highlighted">
      {toSegments(text, highlights).map((seg, i) =>
        seg.highlight ? (
          <mark
            key={i}
            data-tone={seg.tone}
            data-strength={seg.strength}
            title={`${t(`labels.${seg.highlight.label}`)} · ${t(`feedback.strength_${seg.strength}`)}`}
            className={`rounded px-0.5 font-semibold underline underline-offset-4 ${
              seg.tone === 'bad' ? 'bg-bad-soft text-bad decoration-bad' : 'bg-good-soft text-good decoration-good'
            } ${seg.strength === 'strong' ? 'decoration-[3px]' : 'decoration-1 decoration-dotted'}`}
          >
            {seg.text}
            <span className="sr-only">
              {' '}
              ({t(`labels.${seg.highlight.label}`)}, {t(`feedback.strength_${seg.strength}`)})
            </span>
          </mark>
        ) : (
          <span key={i}>{seg.text}</span>
        ),
      )}
    </span>
  );
}
