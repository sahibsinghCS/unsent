/**
 * X-ray mode: the "under the hood" view shown beneath each message.
 * Helper messages: Guardian decision (level, action, latency, evidence), the skill detector's label
 * probabilities, and the trust math. Friend messages: the reaction and which bank line was used.
 */
import type { GuardianResult, Node, State } from '../api/models';
import { usePrefs } from '../i18n';
import { LABEL_COLOR } from '../lib/labels';
import { clampNote, formatTrustMath, signedAuto, trustTerms } from '../lib/trustMath';
import { Icon } from './Icon';
import { ProbBars } from './ProbBars';

function GuardianRow({ g }: { g: GuardianResult }) {
  const { t } = usePrefs();
  const clear = g.level === 'none' && g.action === 'continue';
  // Fixed light tints: these sit on the night X-ray panel in both themes.
  const tone = clear ? 'text-[#86efac] bg-[#86efac]/15' : g.level === 'crisis' ? 'text-[#fca5a5] bg-[#fca5a5]/15' : 'text-[#fdba74] bg-[#fdba74]/15';
  return (
    <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
      <span className={`chip border-transparent ${tone}`}>
        <Icon name="shield" className="h-3 w-3" />
        {t('xray.guardian')}
      </span>
      {clear ? (
        <span className="text-[#86efac]">{t('xray.no_flags')}</span>
      ) : (
        <span className="font-mono">
          {t('xray.level')}=<b>{g.level}</b> · {t('xray.action')}=<b>{g.action}</b>
        </span>
      )}
      <span className="mono-num ml-auto rounded bg-white/10 px-1.5 py-0.5 text-night-muted" title="Guardian latency">
        ⏱ {t('xray.latency', { ms: (g.latency_ms ?? 0).toFixed(g.latency_ms < 10 ? 2 : 1) })}
      </span>
      {(g.evidence?.length ?? 0) > 0 && (
        <span className="w-full text-night-muted">
          {t('xray.evidence')}: {g.evidence!.map((e) => `“${e}”`).join(', ')}
          {g.sources?.length ? ` · ${t('xray.sources')} ${g.sources.join(' + ')}` : ''}
        </span>
      )}
    </div>
  );
}

/** The trust equation, colored per term, e.g. "+12 validated · −2 decay = +10". */
export function TrustMath({ node, before }: { node: Node; before: State | null }) {
  const { t } = usePrefs();
  const after = node.state_after;
  const delta = after.last_delta ?? 0;
  const terms = trustTerms(after.last_breakdown);
  const clamped = before ? clampNote(before.trust, after.trust, delta) : null;
  // Label ids and known engine terms are translated; any new engine term falls back to its own name.
  const name = (key: string) => {
    const label = t(`labels.${key}`);
    return label === `labels.${key}` ? key.replace(/_/g, ' ') : label;
  };
  return (
    <div className="flex flex-wrap items-baseline gap-x-1.5 gap-y-1 font-mono" aria-label={`${t('xray.trust_math')}: ${formatTrustMath(terms, delta, name)}`}>
      <span className="mr-1 font-sans font-semibold text-night-ink">{t('xray.trust_math')}</span>
      {terms.length === 0 && <b className={delta > 0 ? 'text-[#86efac]' : delta < 0 ? 'text-[#fca5a5]' : 'text-night-muted'}>{signedAuto(delta)}</b>}
      {terms.map((term, i) => (
        <span key={term.key + i} className="whitespace-nowrap">
          {i > 0 && <span className="mr-1.5 text-night-muted">·</span>}
          {/* Label color as a dot; the number itself stays high-contrast text (WCAG AA at 11px). */}
          <span
            className="mr-1 inline-block h-1.5 w-1.5 rounded-full align-middle"
            style={{ background: (LABEL_COLOR as Record<string, string>)[term.key] ?? 'rgb(var(--night-muted))' }}
            aria-hidden="true"
          />
          <b className="text-night-ink">{signedAuto(term.value)}</b>{' '}
          <span className="text-night-muted">{name(term.key)}</span>
        </span>
      ))}
      {terms.length > 0 && (
        <span className="whitespace-nowrap">
          <span className="text-night-muted">=</span>{' '}
          <b className={delta > 0 ? 'text-[#86efac]' : delta < 0 ? 'text-[#fca5a5]' : 'text-night-muted'}>{signedAuto(delta)}</b>
        </span>
      )}
      {clamped && (
        <span className="w-full font-sans text-night-muted" data-testid="clamp-note">
          {t(clamped.bound === 0 ? 'xray.clamp_low' : 'xray.clamp_high', { change: signedAuto(clamped.actual) })}
        </span>
      )}
      {before && (
        <span className="ml-auto whitespace-nowrap text-night-muted">
          {Math.round(before.trust)} → <b className="text-night-ink">{Math.round(after.trust)}</b>
        </span>
      )}
    </div>
  );
}

export function XrayHelper({ node, before }: { node: Node; before: State | null }) {
  const { t } = usePrefs();
  return (
    <div className="night-panel ml-auto mt-1.5 w-full max-w-[22rem] space-y-2.5 p-3 text-[11px] leading-relaxed animate-pop-in" data-testid="xray-helper">
      {node.guardian && <GuardianRow g={node.guardian} />}
      {node.events && (
        <div>
          <p className="mb-1.5 font-semibold text-night-muted">{t('xray.skills')}</p>
          <ProbBars probs={node.events} compact />
        </div>
      )}
      {node.events && <TrustMath node={node} before={before} />}
    </div>
  );
}

// Night pills, like the rest of X-ray. The AI voice gets a blue edge so it stands out honestly.
const VOICE_STYLE: Record<string, string> = {
  llm: 'border-[rgb(var(--brand))] bg-night text-night-ink',
  bank: 'border-night-line bg-night text-[#86efac]',
  fallback: 'border-night-line bg-night text-night-muted',
};

/** Who wrote the friend's words (contracts 1.1): the AI (always verified), a reviewed bank line, or a fallback. */
export function VoiceChip({ voice }: { voice?: string | null }) {
  const { t } = usePrefs();
  if (!voice) return null;
  return (
    <span className={`chip font-semibold ${VOICE_STYLE[voice] ?? VOICE_STYLE.fallback}`} data-testid="voice-chip" title={t('xray.voice.label')}>
      <Icon name={voice === 'llm' ? 'message' : 'check'} className="h-3 w-3" />
      {t(`xray.voice.${voice}`)}
    </span>
  );
}

export function XrayFriend({ node }: { node: Node }) {
  const { t } = usePrefs();
  return (
    <div className="mt-1 flex max-w-[22rem] flex-wrap items-center gap-1.5 text-[11px] text-muted animate-pop-in" data-testid="xray-friend">
      <VoiceChip voice={node.voice} />
      {node.reaction && (
        <span className="chip border-night-line bg-night font-mono text-night-muted">
          {t('xray.reaction')}: <b className="text-night-ink">{node.reaction}</b>
        </span>
      )}
      <span className="chip border-night-line bg-night font-mono text-night-muted">
        {t('xray.line')}: <b className="text-night-ink">{node.line_id ?? t('xray.fallback')}</b>
      </span>
      <span className="chip border-night-line bg-night text-night-muted">{t('xray.level_label', { n: node.state_after.level })}</span>
      {node.seen_no_reply && <span className="chip border-night-line bg-night text-[#fca5a5]">{t('xray.seen')}</span>}
    </div>
  );
}
