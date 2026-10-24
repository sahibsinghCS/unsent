/**
 * Feedback report (POST /finish), led by YOUR TRANSCRIPT, annotated like a teacher's notes: green/red
 * underlines on the words that helped or hurt, a margin note per message (trust change, what the skill
 * detector heard, "uncertain" tags), the "this is where you lost them" marker, and the verified rewrite
 * right under the message it improves. Then a plain summary, one trust line chart and missed chances.
 * From any message you can rewind ("Try a different reply") or open the What-if simulation.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ApiError, api } from '../api/client';
import type { CriticReport, Node } from '../api/models';
import { HighlightedText } from '../components/HighlightedText';
import { Bubble } from '../components/Phone';
import { Icon } from '../components/Icon';
import { CheckInModal } from '../components/Safety';
import { ErrorBox, Spinner } from '../components/Status';
import { TrustChart } from '../components/TrustChart';
import { usePrefs } from '../i18n';
import { trustPoints } from '../lib/conversation';
import { activeLabels, isNegative } from '../lib/labels';
import { scenarioById } from '../lib/scenarios';
import { signed } from '../lib/trustMath';

function checkInKey(id: string) {
  return `fr.checkin.${id}`;
}

export function Feedback() {
  const { sessionId = '' } = useParams();
  const navigate = useNavigate();
  const { t } = usePrefs();
  const [report, setReport] = useState<CriticReport | null>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [name, setName] = useState('');
  const [error, setError] = useState<ApiError | null>(null);
  const [checkIn, setCheckIn] = useState(false);
  const [busy, setBusy] = useState(false);

  const load = useCallback(() => {
    setError(null);
    Promise.all([api.session(sessionId), api.finish(sessionId)]).then(
      ([view, critic]) => {
        setNodes(view.nodes);
        setReport(critic);
        scenarioById(view.scenario_id).then((s) => setName(s?.persona_name ?? ''), () => undefined);
        try {
          if (!sessionStorage.getItem(checkInKey(sessionId))) setCheckIn(true);
        } catch {
          setCheckIn(true);
        }
      },
      (e: ApiError) => setError(e),
    );
  }, [sessionId]);
  useEffect(() => {
    load();
  }, [load]);

  const byId = useMemo(() => new Map(nodes.map((n) => [n.id, n])), [nodes]);
  const points = useMemo(() => trustPoints(nodes), [nodes]);

  function closeCheckIn() {
    setCheckIn(false);
    try {
      sessionStorage.setItem(checkInKey(sessionId), '1');
    } catch {
      /* ignore */
    }
  }

  /** Rewind to just before a helper message, then go back to the chat to try again. */
  async function tryAgain(nodeId: string) {
    const node = byId.get(nodeId);
    if (!node?.parent_id) return;
    setBusy(true);
    try {
      await api.rewind(sessionId, node.parent_id);
      navigate(`/chat/${sessionId}`);
    } catch (e) {
      setError(e as ApiError);
    } finally {
      setBusy(false);
    }
  }

  if (error) {
    return error.status === 404 ? <ErrorBox message={t('errors.session_gone')} /> : <ErrorBox message={`${t('feedback.error')} ${error.message}`} onRetry={load} />;
  }
  if (!report) return <Spinner label={t('feedback.loading')} />;

  const turning = report.turning_point ?? null;

  const scores = new Map(report.per_message.map((m) => [m.node_id, m]));

  const actions = (nodeId: string) => (
    <div className="flex flex-wrap gap-2">
      <button type="button" className="btn-ghost px-3.5 py-1.5 text-[13px]" onClick={() => tryAgain(nodeId)} disabled={busy}>
        <Icon name="rewind" className="h-3.5 w-3.5" />
        {t('feedback.try_again')}
      </button>
      <Link to={`/whatif/${sessionId}?node=${encodeURIComponent(nodeId)}`} className="btn-ghost px-3.5 py-1.5 text-[13px]">
        <Icon name="branch" className="h-3.5 w-3.5" />
        {t('feedback.what_if')}
      </Link>
    </div>
  );

  /** One helper message: your words (annotated), the note beside it, the rewrite under it. */
  function HelperMessage({ node, n }: { node: Node; n: number }) {
    const score = scores.get(node.id);
    const delta = node.state_after.last_delta ?? 0;
    const lost = node.id === turning?.node_id;
    const labels = score ? activeLabels(score.probs) : [];
    return (
      <li className="py-3" data-testid="message-card">
        <div className={lost ? '-mx-1 rounded-xl border border-bad/40 bg-bad-soft/40 p-3 sm:-mx-2' : ''} data-testid={lost ? 'turning-point' : undefined}>
        {lost && turning && (
          <p className="mb-2 text-sm font-semibold text-bad">
            {t('feedback.lost_title')} · {t('chat.trust')} {signed(-turning.trust_drop)}
            <span className="font-normal text-muted"> · {turning.reason || t('feedback.lost_body', { drop: Math.round(turning.trust_drop) })}</span>
          </p>
        )}
        <div className="grid gap-2 sm:grid-cols-[minmax(0,1fr)_14rem] sm:gap-5">
          <div className="flex justify-end">
            <p className="im max-w-[85%] rounded-[18px] rounded-br-md border border-brand/25 bg-brand-soft px-3.5 py-2 text-ink">
              <HighlightedText text={node.bubbles.join(' ')} highlights={score?.highlights} />
            </p>
          </div>
          <div className="border-l border-line pl-3 text-[13px] leading-relaxed text-muted">
            <p>
              <span className="font-semibold text-ink">{t('feedback.message_n', { n })}</span> ·{' '}
              <span className={`font-semibold tabular-nums ${delta > 0 ? 'text-good' : delta < 0 ? 'text-bad' : ''}`}>
                {t('chat.trust')} {signed(delta)}
              </span>
            </p>
            {labels.length > 0 && (
              <p>
                {labels.map((label, i) => (
                  <span key={label} className={isNegative(label) ? 'text-bad' : 'text-good'}>
                    {i > 0 && <span className="text-muted">, </span>}
                    {t(`labels.${label}`)} {Math.round((score!.probs[label] ?? 0) * 100)}%
                  </span>
                ))}
              </p>
            )}
            {(score?.uncertain?.length ?? 0) > 0 && (
              <p title={t('feedback.uncertain_hint')} data-testid="uncertain">
                {t('feedback.uncertain', { labels: score!.uncertain!.map((l) => t(`labels.${l}`)).join(', ') })}
              </p>
            )}
          </div>
        </div>
        {score?.rewrite && (
          <div className="mt-3 sm:mr-[15.25rem]" data-testid="rewrite">
            <p className="flex flex-wrap items-center justify-end gap-2 text-[13px] font-semibold text-good">
              {t('feedback.try_instead')}
              {score.rewrite_gain != null && (
                <span className="font-medium" title={t('feedback.gain_hint', { gain: Math.round(score.rewrite_gain * 100) })} data-testid="rewrite-gain">
                  ({score.rewrite_skill ? t('feedback.gain', { skill: t(`skills_verb.${score.rewrite_skill}`) }) : t('feedback.gain_generic')})
                </span>
              )}
            </p>
            <div className="mt-1 flex justify-end pr-1.5">
              <p className="im im-bubble im-sent">{score.rewrite}</p>
            </div>
            {score.rewrite_source && (
              <p className="mt-1 text-right text-xs text-muted" data-testid="rewrite-source">
                {score.rewrite_source === 'llm' ? t('feedback.rewrite_llm') : t('feedback.rewrite_exemplar')}
              </p>
            )}
          </div>
        )}
        <div className="mt-3 flex justify-end sm:mr-[15.25rem]">{actions(node.id)}</div>
        </div>
      </li>
    );
  }

  let n = 0;
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-4xl sm:text-5xl">{t('feedback.title')}</h1>
          <p className="mt-1 text-muted">{t('feedback.story_with', { name })}</p>
        </div>
        <div className="flex gap-2">
          <Link to={`/chat/${sessionId}`} className="btn-ghost">
            {t('feedback.back_chat')}
          </Link>
          <Link to="/practice" className="btn-primary">
            {t('feedback.new_scenario')}
          </Link>
        </div>
      </div>

      <p className="mt-6 max-w-3xl text-lg leading-relaxed" data-testid="summary">
        {report.summary_text}
      </p>

      {!turning && (
        <p className="mt-4 rounded-xl border border-good/30 bg-good-soft px-4 py-3 font-semibold text-good" data-testid="turning-point">
          {t('feedback.no_lost')}
        </p>
      )}

      <section className="mt-8" aria-labelledby="transcript-title">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <h2 id="transcript-title" className="text-2xl">
            {t('feedback.transcript_title')}
          </h2>
          <p className="text-[13px] text-muted">
            <span className="font-semibold text-good underline decoration-2 underline-offset-4">{t('feedback.legend_good')}</span> ·{' '}
            <span className="font-semibold text-bad underline decoration-2 underline-offset-4">{t('feedback.legend_bad')}</span> · {t('feedback.legend_strong')}
          </p>
        </div>
        {report.per_message.length === 0 && <p className="mt-4 text-muted">{t('feedback.no_messages')}</p>}
        <ol className="card im-screen mt-4 divide-y divide-line/60 overflow-hidden px-3 sm:px-4">
          {nodes.map((node) => {
            if (node.role === 'friend') {
              if (node.seen_no_reply)
                return (
                  <li key={node.id} className="im-meta py-2 text-right">
                    {t('chat.read')}
                  </li>
                );
              return (
                <li key={node.id} className="space-y-0.5 py-3">
                  {node.bubbles.map((b, i) => (
                    <Bubble key={i} tail={i === node.bubbles.length - 1}>
                      {b}
                    </Bubble>
                  ))}
                </li>
              );
            }
            if (node.role === 'user' && scores.has(node.id)) return <HelperMessage key={node.id} node={node} n={++n} />;
            return null;
          })}
        </ol>
      </section>

      {points.length > 1 && (
        <section className="card mt-8 p-5">
          <h2 className="text-lg">{t('chat.trust_graph')}</h2>
          <div className="mt-4">
            <TrustChart points={points} height={220} />
          </div>
        </section>
      )}

      {(report.missed_opportunities?.length ?? 0) > 0 && (
        <section className="card mt-5 p-5">
          <h2 className="text-lg">{t('feedback.missed_title')}</h2>
          <ul className="mt-2 list-disc space-y-1.5 pl-5 leading-relaxed">
            {report.missed_opportunities!.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        </section>
      )}
      <CheckInModal open={checkIn} onClose={closeCheckIn} />
    </div>
  );
}
