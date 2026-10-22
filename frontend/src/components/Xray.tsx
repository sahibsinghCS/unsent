/**
 * X-ray mode: the "under the hood" view shown beneath each message.
 * Helper messages: Guardian decision (level, action, latency, evidence), the skill detector's label
 * probabilities, and the trust math. Friend messages: the reaction and which bank line was used.
 */
import type { GuardianResult, Node, State } from '../api/models';
import { usePrefs } from '../i18n';
import { LABEL_COLOR } from '../lib/labels';
import { formatTrustMath, signed, trustTerms } from '../lib/trustMath';
import { Icon } from './Icon';
import { ProbBars } from './ProbBars';

function GuardianRow({ g }: { g: GuardianResult }) {
  const { t } = usePrefs();
  const clear = g.level === 'none' && g.action === 'continue';
  const tone = clear ? 'text-good bg-good-soft' : g.level === 'crisis' ? 'text-bad bg-bad-soft' : 'text-warm bg-warm-soft';
  return (
    <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
      <span className={`chip border-transparent ${tone}`}>
        <Icon name="shield" className="h-3 w-3" />
        {t('xray.guardian')}
      </span>
      {clear ? (
        <span className="text-good">{t('xray.no_flags')}</span>
      ) : (
        <span className="font-mono">
          {t('xray.level')}=<b>{g.level}</b> · {t('xray.action')}=<b>{g.action}</b>
        </span>
      )}
      <span className="mono-num ml-auto rounded bg-sunken px-1.5 py-0.5 text-muted" title="Guardian latency">
        ⏱ {t('xray.latency', { ms: (g.latency_ms ?? 0).toFixed(g.latency_ms < 10 ? 2 : 1) })}
      </span>
      {(g.evidence?.length ?? 0) > 0 && (
        <span className="w-full text-muted">
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
  const terms = trustTerms(node.events, delta);
  const name = (key: string) => t(`labels.${key}`);
  return (
    <div className="flex flex-wrap items-baseline gap-x-1.5 gap-y-1 font-mono" aria-label={`${t('xray.trust_math')}: ${formatTrustMath(terms, delta, name)}`}>
      <span className="mr-1 font-sans font-semibold text-ink">{t('xray.trust_math')}</span>
      {terms.length === 0 && <span className="text-muted">{signed(delta)}</span>}
      {terms.map((term, i) => (
        <span key={term.key + i} className="whitespace-nowrap">
          {i > 0 && <span className="mr-1.5 text-muted">·</span>}
          <b style={{ color: (LABEL_COLOR as Record<string, string>)[term.key] }} className={term.key in LABEL_COLOR ? '' : 'text-muted'}>
            {signed(term.value, Number.isInteger(term.value) ? 0 : 1)}
          </b>{' '}
          <span className="text-muted">{name(term.key)}</span>
        </span>
      ))}
      {terms.length > 0 && (
        <span className="whitespace-nowrap">
          <span className="text-muted">=</span>{' '}
          <b className={delta > 0 ? 'text-good' : delta < 0 ? 'text-bad' : 'text-muted'}>{signed(delta, Number.isInteger(delta) ? 0 : 1)}</b>
        </span>
      )}
      {before && (
        <span className="ml-auto whitespace-nowrap text-muted">
          {Math.round(before.trust)} → <b className="text-ink">{Math.round(after.trust)}</b>
        </span>
      )}
    </div>
  );
}

export function XrayHelper({ node, before }: { node: Node; before: State | null }) {
  const { t } = usePrefs();
  return (
    <div className="ml-auto mt-1.5 w-full max-w-[22rem] space-y-2.5 rounded-xl border border-brand/25 bg-brand-soft/40 p-3 text-[11px] leading-relaxed animate-pop-in" data-testid="xray-helper">
      {node.guardian && <GuardianRow g={node.guardian} />}
      {node.events && (
        <div>
          <p className="mb-1 font-semibold">{t('xray.skills')}</p>
          <ProbBars probs={node.events} compact />
        </div>
      )}
      {node.events && <TrustMath node={node} before={before} />}
    </div>
  );
}

const VOICE_STYLE: Record<string, string> = {
  llm: 'border-transparent bg-brand-soft text-ink',
  bank: 'border-transparent bg-good-soft text-good',
  fallback: 'border-line bg-sunken text-muted',
};

/** Who wrote the friend's words (contracts 1.1): the AI (always verified), a reviewed bank line, or a fallback. */
export function VoiceChip({ voice }: { voice?: string | null }) {
  const { t } = usePrefs();
  if (!voice) return null;
  return (
    <span className={`chip font-semibold ${VOICE_STYLE[voice] ?? VOICE_STYLE.fallback}`} data-testid="voice-chip" title={t('xray.voice.label')}>
      <Icon name={voice === 'llm' ? 'sparkle' : 'check'} className="h-3 w-3" />
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
        <span className="chip border-line bg-surface font-mono">
          {t('xray.reaction')}: <b className="text-ink">{node.reaction}</b>
        </span>
      )}
      <span className="chip border-line bg-surface font-mono">
        {t('xray.line')}: <b className="text-ink">{node.line_id ?? t('xray.fallback')}</b>
      </span>
      <span className="chip border-line bg-surface">{t('xray.level_label', { n: node.state_after.level })}</span>
      {node.seen_no_reply && <span className="chip border-transparent bg-bad-soft text-bad">{t('xray.seen')}</span>}
    </div>
  );
}
