/**
 * What-if (POST /whatif): stronger replies from the chosen message, simulated forward through the
 * real trust engine and line bank. Paths sit side by side (stacked on phones), each with its own mini
 * chat and trust curve, plus an overlay of every path against what you actually said.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { ApiError, api } from '../api/client';
import type { Node, WhatIfPath, WhatIfResult } from '../api/models';
import { Icon } from '../components/Icon';
import { OverlayChart, type Series } from '../components/OverlayChart';
import { BranchMap, type Branch } from '../components/BranchMap';
import { Bubble } from '../components/Phone';
import { ErrorBox, Spinner } from '../components/Status';
import { TrustChart } from '../components/TrustChart';
import { tokenColor } from '../lib/chart';
import { usePrefs } from '../i18n';
import { isScoredUserNode } from '../lib/conversation';
import { strongestLabel } from '../lib/labels';

const PATH_COLORS = ['#8b5cf6', '#0ea5e9', '#f59e0b', '#db2777'];

/** Trust points for a simulated path: its starting trust, then after each simulated helper message. */
function pathPoints(path: WhatIfPath) {
  const start = path.trust_series[0] ?? 0;
  return [
    { trust: start, delta: 0, label: null },
    ...path.nodes.filter(isScoredUserNode).map((n) => ({ trust: n.state_after.trust, delta: n.state_after.last_delta ?? 0, label: strongestLabel(n.events) })),
  ];
}

/** What actually happened from the same message: trust before it, then after each later helper message. */
function actualSeries(nodes: Node[], fromId: string): number[] {
  const index = nodes.findIndex((n) => n.id === fromId);
  if (index < 1) return [];
  return [nodes[index - 1].state_after.trust, ...nodes.slice(index).filter(isScoredUserNode).map((n) => n.state_after.trust)];
}

export function WhatIf() {
  const { sessionId = '' } = useParams();
  const [params] = useSearchParams();
  const nodeId = params.get('node');
  const navigate = useNavigate();
  const { t } = usePrefs();
  const [result, setResult] = useState<WhatIfResult | null>(null);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [error, setError] = useState<ApiError | null>(null);

  const load = useCallback(() => {
    setError(null);
    setResult(null);
    Promise.all([api.whatif(sessionId, nodeId), api.session(sessionId)]).then(
      ([r, view]) => {
        setResult(r);
        setNodes(view.nodes);
      },
      (e: ApiError) => setError(e),
    );
  }, [sessionId, nodeId]);
  useEffect(() => {
    load();
  }, [load]);

  // Exemplar strategies (check_in, validate, ask_directly, refer, follow_up, combo) in the UI language.
  const strategyName = useCallback((s: string) => {
    const name = t(`whatif.strategies.${s}`);
    return name.startsWith('whatif.') ? s.replace(/_/g, ' ') : name;
  }, [t]);

  const series = useMemo<Series[]>(() => {
    if (!result) return [];
    const simulated = result.paths.map((p, i) => ({
      label: `${i + 1}. ${strategyName(p.strategy)}`,
      values: p.trust_series,
      color: i === result.best_index ? tokenColor('brand') : PATH_COLORS[i % PATH_COLORS.length],
      emphasis: (i === result.best_index ? 'best' : 'normal') as Series['emphasis'],
    }));
    const actual = actualSeries(nodes, result.from_node_id);
    return actual.length > 1 ? [...simulated, { label: t('whatif.you_said'), values: actual, color: tokenColor('muted'), emphasis: 'actual' }] : simulated;
  }, [result, nodes, t, strategyName]);

  // The same data as the overlay chart, as branching futures (best first, what really happened last).
  const branches = useMemo<Branch[]>(() => {
    if (!result) return [];
    const sims = result.paths.map((p, i) => ({
      label: strategyName(p.strategy),
      from: p.trust_series[0] ?? 0,
      to: p.trust_series[p.trust_series.length - 1] ?? 0,
      color: i === result.best_index ? tokenColor('brand') : PATH_COLORS[i % PATH_COLORS.length],
      best: i === result.best_index,
    }));
    sims.sort((a, b) => Number(!!b.best) - Number(!!a.best));
    const actual = actualSeries(nodes, result.from_node_id);
    return actual.length > 1
      ? [...sims, { label: t('whatif.you_said'), from: actual[0], to: actual[actual.length - 1], color: tokenColor('muted'), actual: true }]
      : sims;
  }, [result, nodes, t, strategyName]);

  async function tryInChat(text: string) {
    if (!result) return;
    const from = nodes.find((n) => n.id === result.from_node_id);
    if (!from?.parent_id) return;
    try {
      await api.rewind(sessionId, from.parent_id);
      navigate(`/chat/${sessionId}`, { state: { draft: text } });
    } catch (e) {
      setError(e as ApiError);
    }
  }

  if (error) return <ErrorBox message={`${t('whatif.error')} ${error.message}`} onRetry={error.status === 409 ? undefined : load} />;
  if (!result) return <Spinner />;

  const original = nodes.find((n) => n.id === result.from_node_id);

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <Link to={`/feedback/${sessionId}`} className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand">
        <Icon name="back" className="h-4 w-4" />
        {t('whatif.back')}
      </Link>
      <div className="mt-4 flex flex-wrap items-start justify-between gap-3">
        <div className="max-w-2xl">
          <h1 className="text-4xl font-semibold sm:text-5xl">{t('whatif.title')}</h1>
          <p className="mt-2 text-muted">{t('whatif.sub')}</p>
        </div>
        {result.simulated && (
          <span className="chip border-warm/50 bg-warm-soft px-3 py-1.5 text-sm font-bold uppercase tracking-wider text-ink" title={t('whatif.simulated_hint')} data-testid="simulated">
            <Icon name="sparkle" className="h-4 w-4 text-warm" />
            {t('whatif.simulated')}
          </span>
        )}
      </div>

      {original && result.paths.length > 0 && (
        <section className="card mt-6 p-4 sm:p-6">
          <h2 className="mb-4 text-2xl font-semibold">{t('whatif.futures')}</h2>
          <BranchMap origin={original.bubbles.join(' ')} branches={branches} />
        </section>
      )}

      {result.paths.length === 0 && (
        <div className="card mt-6 p-8 text-center" role="status" data-testid="whatif-empty">
          <Icon name="sparkle" className="mx-auto h-8 w-8 text-warm" />
          <p className="mx-auto mt-3 max-w-md text-lg font-semibold">{t('whatif.empty')}</p>
          <Link to={`/feedback/${sessionId}`} className="btn-ghost mt-5">
            {t('whatif.back')}
          </Link>
        </div>
      )}

      {result.paths.length > 0 && (
        <section className="card mt-6 p-5">
          <h2 className="eyebrow mb-3">{t('whatif.overlay')}</h2>
          <OverlayChart series={series} />
          <p className="mt-2 text-xs text-muted">{t('whatif.simulated_hint')}</p>
        </section>
      )}

      <ol className="mt-6 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {result.paths.map((path, i) => {
          const best = i === result.best_index;
          const series = path.trust_series;
          return (
            <li key={i} className={`card flex flex-col p-4 ${best ? 'ring-2 ring-brand' : ''}`} data-testid="whatif-path">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <span className="grid h-7 w-7 place-items-center rounded-full border-2 bg-surface text-xs font-bold text-ink" style={{ borderColor: best ? tokenColor('brand') : PATH_COLORS[i % PATH_COLORS.length] }}>
                  {i + 1}
                </span>
                <span className="chip border-line">{strategyName(path.strategy)}</span>
                {best && <span className="chip border-transparent bg-brand text-brand-ink">★ {t('whatif.best')}</span>}
                {/* critic_score = our detector's score (0–1) for the skill this reply teaches */}
                <span className="mono-num ml-auto text-xs text-muted" title={t('whatif.score_hint')}>
                  {t('whatif.score', { score: Math.round(path.critic_score * 100) })}
                </span>
              </div>
              <p className="text-[15px] font-semibold leading-snug">“{path.candidate_text}”</p>
              <div className="im-screen my-3 space-y-1 rounded-2xl border border-line/70 px-2 py-3">
                {path.nodes.map((n) =>
                  n.role === 'system' ? null : n.seen_no_reply ? (
                    <p key={n.id} className="im-meta pr-2 text-right">
                      {t('chat.read')}
                    </p>
                  ) : (
                    n.bubbles.map((b, j) => (
                      <Bubble key={n.id + j} me={n.role === 'user'} tail={j === n.bubbles.length - 1} className="!text-[14px]">
                        {b}
                      </Bubble>
                    ))
                  ),
                )}
              </div>
              <div className="mt-auto">
                <p className="mono-num mb-1 text-xs text-muted">
                  {t('whatif.trust_end', { from: Math.round(series[0] ?? 0), to: Math.round(series[series.length - 1] ?? 0) })}
                </p>
                <TrustChart points={pathPoints(path)} height={110} />
                <button type="button" className="btn-ghost mt-3 w-full text-xs" onClick={() => tryInChat(path.candidate_text)}>
                  {t('whatif.try_this')}
                </button>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
