// Renders a helper message with the critic's word highlights: green = helped, red = hurt.
import type { Highlight } from '../api/models';
import { usePrefs } from '../i18n';
import { toSegments } from '../lib/highlight';
import { signed } from '../lib/trustMath';

export function HighlightedText({ text, highlights }: { text: string; highlights?: Highlight[] | null }) {
  const { t } = usePrefs();
  return (
    <span data-testid="highlighted">
      {toSegments(text, highlights).map((seg, i) =>
        seg.highlight ? (
          <mark
            key={i}
            data-tone={seg.tone}
            title={`${t(`labels.${seg.highlight.label}`)} ${signed(seg.highlight.delta, 2)}`}
            className={`rounded px-0.5 font-semibold ${
              seg.tone === 'bad' ? 'bg-bad-soft text-bad decoration-bad' : 'bg-good-soft text-good decoration-good'
            } underline decoration-2 underline-offset-4`}
          >
            {seg.text}
            <span className="sr-only"> ({t(`labels.${seg.highlight.label}`)})</span>
          </mark>
        ) : (
          <span key={i}>{seg.text}</span>
        ),
      )}
    </span>
  );
}
