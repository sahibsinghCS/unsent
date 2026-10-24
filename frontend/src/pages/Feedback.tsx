/**
 * Feedback report (POST /finish): 7-skill radar, summary, "This is where you lost them", missed
 * opportunities, and a card per helper message with word highlights, uncertain tags and a verified
 * rewrite. From any message you can rewind ("Try again from here") or open the What-if simulation.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { ApiError, api } from '../api/client';
import type { CriticReport, Node } from '../api/models';
import { HighlightedText } from '../components/HighlightedText';
import { Icon } from '../components/Icon';
import { CheckInModal } from '../components/Safety';
import { SkillRadar } from '../components/SkillRadar';
import { ErrorBox, Spinner } from '../components/Status';
import { TrustChart } from '../components/TrustChart';
import { usePrefs } from '../i18n';
import { trustPoints } from '../lib/conversation';
import { LABEL_COLOR, activeLabels, isNegative } from '../lib/labels';
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
  const turningNode = turning ? byId.get(turning.node_id) : undefined;
  const turningScore = turning ? report.per_message.find((m) => m.node_id === turning.node_id) : undefined;

  const actions = (nodeId: string) => (
    <div className="flex flex-wrap gap-2">
      <button type="button" className="btn-ghost px-4 py-2 text-xs" onClick={() => tryAgain(nodeId)} disabled={busy}>
        <Icon name="rewind" className="h-3.5 w-3.5" />
        {t('feedback.try_again')}
      </button>
      <Link to={`/whatif/${sessionId}?node=${encodeURIComponent(nodeId)}`} className="btn-ghost px-4 py-2 text-xs">
        <Icon name="sparkle" className="h-3.5 w-3.5 text-warm" />
        {t('feedback.what_if')}
      </Link>
    </div>
  );

  return (
    <div className="mx-auto max-w-5xl px-4 py-10 sm:px-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="eyebrow">{t('feedback.story_with', { name })}</p>
          <h1 className="mt-1 text-4xl font-semibold sm:text-5xl">{t('feedback.title')}</h1>
        </div>
        <div className="flex gap-2">
          <Link to={`/chat/${sessionId}`} className="btn-ghost">
            <Icon name="back" className="h-4 w-4" />
            {t('feedback.back_chat')}
          </Link>
          <Link to="/practice" className="btn-primary">
            {t('feedback.new_scenario')}
          </Link>
        </div>
      </div>

      {/* The critic's summary as an editorial pull quote */}
      <figure className="relative mt-8 overflow-hidden rounded-[1.75rem] bg-night p-6 text-night-ink sm:p-8">
        <span className="absolute -right-10 -top-16 h-56 w-56 rounded-full bg-[rgb(var(--brand)/0.35)] blur-3xl" aria-hidden="true" />
        <span className="absolute -bottom-20 left-10 h-48 w-48 rounded-full bg-[rgb(var(--glow)/0.25)] blur-3xl" aria-hidden="true" />
        <p className="relative font-sans text-[11px] font-bold uppercase tracking-[0.14em] text-night-muted">{t('feedback.summary_title')}</p>
        <blockquote className="relative mt-3 font-display text-2xl leading-snug sm:text-[1.9rem]" data-testid="summary">
          “{report.summary_text}”
        </blockquote>
      </figure>

      <div className="mt-6 grid gap-5 lg:grid-cols-[1fr_1.15fr]">
        {/* The story: every helper message on a timeline, with trust after it */}
        <section className="card p-5 sm:p-6" aria-labelledby="story-title">
          <h2 id="story-title" className="text-2xl font-semibold">{t('feedback.story_title')}</h2>
          <ol className="relative mt-5 space-y-4 before:absolute before:bottom-2 before:left-[0.95rem] before:top-2 before:w-px before:bg-line">
            {report.per_message.map((score, i) => {
              const node = byId.get(score.node_id);
              if (!node) return null;
              const delta = node.state_after.last_delta ?? 0;
              const lost = score.node_id === turning?.node_id;
              return (
                <li key={score.node_id} className="relative flex gap-3">
                  <span
                    className={`relative z-10 grid h-8 w-8 shrink-0 place-items-center rounded-full text-[11px] font-bold ring-4 ring-surface ${
                      lost ? 'bg-warm text-white dark:text-[rgb(40_10_6)]' : delta >= 0 ? 'bg-good-soft text-good' : 'bg-bad-soft text-bad'
                    }`}
                  >
                    {i + 1}
                  </span>
                  <div className="min-w-0 flex-1 pt-1">
                    <p className="line-clamp-2 text-[15px] leading-snug">{node.bubbles.join(' ')}</p>
                    <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted">
                      <span className={`mono-num font-semibold ${delta > 0 ? 'text-good' : delta < 0 ? 'text-bad' : ''}`}>{signed(delta)}</span>
                      <span>
                        {t('chat.trust')} {Math.round(node.state_after.trust)}
                      </span>
                      {lost && <span className="chip border-transparent bg-warm-soft px-2 py-0.5 font-semibold text-ink">{t('feedback.lost_here')}</span>}
                    </p>
                  </div>
                </li>
              );
            })}
          </ol>
        </section>

        {/* The moment you lost them, and what would have worked instead */}
        <section
          className={`relative overflow-hidden rounded-[1.5rem] border p-5 sm:p-6 ${turning ? 'border-warm/40 bg-warm-soft/50' : 'border-good/30 bg-good-soft/50'}`}
          data-testid="turning-point"
        >
          <h2 className="flex items-center gap-2 text-2xl font-semibold">
            <Icon name={turning ? 'flag' : 'check'} className={`h-5 w-5 shrink-0 ${turning ? 'text-warm' : 'text-good'}`} />
            {turning ? t('feedback.lost_title') : t('feedback.no_lost')}
          </h2>
          {turning && turningNode && (
            <div className="mt-5 space-y-4">
              <div>
                <p className="eyebrow mb-2">{t('feedback.you_said')}</p>
                <div className="inline-block max-w-full rounded-bubble rounded-br-md bg-surface px-4 py-2.5 text-[15px] shadow-card">
                  <HighlightedText text={turningNode.bubbles.join(' ')} highlights={turningScore?.highlights} />
                </div>
                <p className="mt-2 text-sm">
                  <span className="chip mono-num mr-2 border-transparent bg-bad-soft text-bad">
                    {t('chat.trust')} {signed(-turning.trust_drop)}
                  </span>
                  {turning.reason || t('feedback.lost_body', { drop: Math.round(turning.trust_drop) })}
                </p>
              </div>
              {turningScore?.rewrite && (
                <div>
                  <p className="eyebrow mb-2 text-good">{t('feedback.would_have_worked')}</p>
                  <div className="inline-block max-w-full rounded-bubble rounded-br-md bg-me px-4 py-2.5 text-[15px] text-white shadow-[0_10px_24px_-12px_rgb(var(--bubble-me))]">
                    {turningScore.rewrite}
                  </div>
                </div>
              )}
              {actions(turning.node_id)}
            </div>
          )}
        </section>
      </div>

      {/* The numbers, secondary */}
      <div className="mt-5 grid gap-5 md:grid-cols-2">
        <section className="card p-5">
          <h2 className="eyebrow">{t('feedback.skills_title')}</h2>
          <SkillRadar summary={report.skill_summary} />
        </section>
        <section className="card flex flex-col p-5">
          <h2 className="eyebrow">{t('chat.trust_graph')}</h2>
          {points.length > 1 && (
            <div className="mt-4 flex-1">
              <TrustChart points={points} height={250} />
            </div>
          )}
        </section>
      </div>

      {(report.missed_opportunities?.length ?? 0) > 0 && (
        <section className="card mt-5 p-5">
          <h2 className="text-2xl font-semibold">{t('feedback.missed_title')}</h2>
          <ul className="mt-3 space-y-2">
            {report.missed_opportunities!.map((m, i) => (
              <li key={i} className="flex gap-2.5 leading-relaxed">
                <Icon name="sparkle" className="mt-1 h-4 w-4 shrink-0 text-warm" />
                {m}
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="mt-12">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-3xl font-semibold">{t('feedback.messages_title')}</h2>
          <div className="flex gap-3 text-xs">
            <span className="chip border-transparent bg-good-soft text-good">{t('feedback.legend_good')}</span>
            <span className="chip border-transparent bg-bad-soft text-bad">{t('feedback.legend_bad')}</span>
            <span className="hidden text-muted sm:inline">{t('feedback.legend_strong')}</span>
          </div>
        </div>
        {report.per_message.length === 0 && <p className="mt-4 text-muted">{t('feedback.no_messages')}</p>}
        <ol className="mt-4 space-y-4">
          {report.per_message.map((score, i) => {
            const node = byId.get(score.node_id);
            if (!node) return null;
            const isTurning = score.node_id === turning?.node_id;
            const delta = node.state_after.last_delta ?? 0;
            return (
              <li key={score.node_id} className={`card p-5 ${isTurning ? 'ring-2 ring-warm/60' : ''}`} data-testid="message-card">
                <div className="mb-2 flex flex-wrap items-center gap-2 text-xs">
                  <span className="eyebrow">{t('feedback.message_n', { n: i + 1 })}</span>
                  <span className={`chip mono-num border-transparent ${delta > 0 ? 'bg-good-soft text-good' : delta < 0 ? 'bg-bad-soft text-bad' : 'bg-sunken text-muted'}`}>
                    {t('chat.trust')} {signed(delta)}
                  </span>
                  {activeLabels(score.probs).map((label) => (
                    <span key={label} className={`chip border-transparent ${isNegative(label) ? 'bg-bad-soft text-bad' : 'bg-good-soft text-good'}`}>
                      <span className="h-1.5 w-1.5 rounded-full" style={{ background: LABEL_COLOR[label] }} aria-hidden="true" />
                      {t(`labels.${label}`)} {Math.round((score.probs[label] ?? 0) * 100)}%
                    </span>
                  ))}
                  {(score.uncertain?.length ?? 0) > 0 && (
                    <span className="chip border-dashed border-muted/60 text-muted" title={t('feedback.uncertain_hint')} data-testid="uncertain">
                      ? {t('feedback.uncertain', { labels: score.uncertain!.map((l) => t(`labels.${l}`)).join(', ') })}
                    </span>
                  )}
                </div>
                <p className="text-[17px] leading-relaxed">
                  <HighlightedText text={node.bubbles.join(' ')} highlights={score.highlights} />
                </p>
                {score.rewrite && (
                  <div className="mt-4 rounded-xl border border-good/30 bg-good-soft/50 p-3.5" data-testid="rewrite">
                    <p className="flex flex-wrap items-center gap-2 text-xs font-semibold uppercase tracking-wide text-good">
                      <Icon name="sparkle" className="h-3.5 w-3.5" />
                      {t('feedback.try_instead')}
                      {score.rewrite_gain != null && (
                        // rewrite_gain = how much higher our detector scores the missing skill on this
                        // reply. The chip names the skill it adds; the exact number is in the tooltip.
                        <span
                          className="chip border-transparent bg-good text-white normal-case dark:text-[rgb(6_30_20)]"
                          title={t('feedback.gain_hint', { gain: Math.round(score.rewrite_gain * 100) })}
                          data-testid="rewrite-gain"
                        >
                          ✓ {score.rewrite_skill ? t('feedback.gain', { skill: t(`skills_verb.${score.rewrite_skill}`) }) : t('feedback.gain_generic')}
                        </span>
                      )}
                    </p>
                    <p className="mt-1.5 text-[15px] leading-relaxed">“{score.rewrite}”</p>
                    {score.rewrite_source && (
                      <p className="mt-1.5 text-xs text-muted" data-testid="rewrite-source">
                        {score.rewrite_source === 'llm' ? t('feedback.rewrite_llm') : t('feedback.rewrite_exemplar')}
                      </p>
                    )}
                  </div>
                )}
                <div className="mt-4">{actions(score.node_id)}</div>
              </li>
            );
          })}
        </ol>
      </section>
      <CheckInModal open={checkIn} onClose={closeCheckIn} />
    </div>
  );
}
