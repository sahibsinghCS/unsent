/**
 * Feedback report (POST /finish), told as a story: the critic's summary as pull text, a timeline of
 * every message with trust after it, "This is where you lost them" (what you said and what would have
 * worked), the trust chart and missed chances, then your full conversation annotated like a teacher's
 * notes (green/red underlines, a margin note per message, the verified rewrite under it).
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
        <div className={lost ? '-mx-1 rounded-xl border border-bad/40 bg-bad-soft/40 p-3 sm:-mx-2' : ''} data-lost={lost || undefined}>
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

  const turningNode = turning ? byId.get(turning.node_id) : undefined;
  const turningScore = turning ? scores.get(turning.node_id) : undefined;

  let n = 0;
  return (
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-5xl sm:text-6xl">{t('feedback.title')}</h1>
          <p className="mt-2 text-muted">{t('feedback.story_with', { name })}</p>
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

      {/* The critic's summary as large pull text (Plex Sans, not italic) */}
      <figure className="card mt-8 p-6 sm:p-8">
        <figcaption className="meta-label">{t('feedback.summary_title')}</figcaption>
        <blockquote className="mt-3 text-[1.35rem] font-medium leading-snug sm:text-[1.65rem]" data-testid="summary">
          {report.summary_text}
        </blockquote>
      </figure>

      <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_1.15fr]">
        {/* The story: every helper message on a timeline, with trust after it */}
        <section className="card p-5 sm:p-6" aria-labelledby="story-title">
          <h2 id="story-title" className="text-2xl">
            {t('feedback.story_title')}
          </h2>
          <ol className="relative mt-5 space-y-4 before:absolute before:bottom-2 before:left-[0.95rem] before:top-2 before:w-px before:bg-line">
            {report.per_message.map((score, i) => {
              const node = byId.get(score.node_id);
              if (!node) return null;
              const delta = node.state_after.last_delta ?? 0;
              const lost = score.node_id === turning?.node_id;
              return (
                <li key={score.node_id} className="relative flex gap-3">
                  <span
                    className={`relative z-10 grid h-8 w-8 shrink-0 place-items-center rounded-full border font-mono text-[11px] font-medium ring-4 ring-surface ${
                      lost ? 'border-bad bg-bad text-white dark:text-black' : delta >= 0 ? 'border-good/40 bg-good-soft text-good' : 'border-bad/40 bg-bad-soft text-bad'
                    }`}
                  >
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <div className="min-w-0 flex-1 pt-1">
                    <p className="line-clamp-2 text-[15px] leading-snug">{node.bubbles.join(' ')}</p>
                    <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted">
                      <span className={`mono-num font-semibold ${delta > 0 ? 'text-good' : delta < 0 ? 'text-bad' : ''}`}>{signed(delta)}</span>
                      <span>
                        {t('chat.trust')} <span className="mono-num">{Math.round(node.state_after.trust)}</span>
                      </span>
                      {lost && <span className="chip border-bad/40 font-semibold text-bad">{t('feedback.lost_here')}</span>}
                    </p>
                  </div>
                </li>
              );
            })}
          </ol>
        </section>

        {/* The moment you lost them, and what would have worked instead */}
        <section className={`rounded-2xl border p-5 sm:p-6 ${turning ? 'border-bad/40 bg-bad-soft/40' : 'border-good/40 bg-good-soft/40'}`} data-testid="turning-point">
          <h2 className="flex items-center gap-2 text-2xl">
            <Icon name={turning ? 'flag' : 'check'} className={`h-5 w-5 shrink-0 ${turning ? 'text-bad' : 'text-good'}`} />
            {turning ? t('feedback.lost_title') : t('feedback.no_lost')}
          </h2>
          {turning && turningNode && (
            <div className="mt-5 space-y-5">
              <div>
                <p className="small-label mb-2">{t('feedback.you_said')}</p>
                <p className="im inline-block max-w-full rounded-[18px] border border-line bg-surface px-3.5 py-2 text-ink">
                  <HighlightedText text={turningNode.bubbles.join(' ')} highlights={turningScore?.highlights} />
                </p>
                <p className="mt-2 text-sm leading-relaxed">
                  <span className="mono-num mr-2 font-semibold text-bad">
                    {t('chat.trust')} {signed(-turning.trust_drop)}
                  </span>
                  {turning.reason || t('feedback.lost_body', { drop: Math.round(turning.trust_drop) })}
                </p>
              </div>
              {turningScore?.rewrite && (
                <div>
                  <p className="small-label mb-2 !text-good">{t('feedback.would_have_worked')}</p>
                  <p className="im im-bubble im-sent inline-block !max-w-full">{turningScore.rewrite}</p>
                </div>
              )}
              {actions(turning.node_id)}
            </div>
          )}
        </section>
      </div>

      {points.length > 1 && (
        <section className="card mt-5 p-5 sm:p-6">
          <h2 className="text-xl">{t('chat.trust_graph')}</h2>
          <div className="mt-4">
            <TrustChart points={points} height={220} />
          </div>
        </section>
      )}

      {(report.missed_opportunities?.length ?? 0) > 0 && (
        <section className="card mt-5 p-5 sm:p-6">
          <h2 className="text-xl">{t('feedback.missed_title')}</h2>
          <ul className="mt-2 list-disc space-y-1.5 pl-5 leading-relaxed">
            {report.missed_opportunities!.map((m, i) => (
              <li key={i}>{m}</li>
            ))}
          </ul>
        </section>
      )}
      <section className="mt-14" aria-labelledby="transcript-title">
        <div className="flex flex-wrap items-baseline justify-between gap-3">
          <h2 id="transcript-title" className="text-3xl">
            {t('feedback.transcript_title')}
          </h2>
          <p className="text-[13px] text-muted">
            <span className="font-semibold text-good underline decoration-2 underline-offset-4">{t('feedback.legend_good')}</span> ·{' '}
            <span className="font-semibold text-bad underline decoration-2 underline-offset-4">{t('feedback.legend_bad')}</span> · {t('feedback.legend_strong')}
          </p>
        </div>
        {report.per_message.length === 0 && <p className="mt-4 text-muted">{t('feedback.no_messages')}</p>}
        <ol className="im-screen mt-4 divide-y divide-line overflow-hidden rounded-2xl border border-line px-3 sm:px-4">
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

      <CheckInModal open={checkIn} onClose={closeCheckIn} />
    </div>
  );
}
