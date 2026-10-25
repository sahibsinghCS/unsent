/**
 * The practice chat. The conversation is the server's root-to-head path (SessionView.nodes); every
 * turn appends the nodes from the TurnResponse. Friend bubbles are revealed one at a time behind a
 * typing indicator. X-ray mode shows the Guardian, skill probabilities and trust math per message.
 */
import { Fragment, useCallback, useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react';
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom';
import { ApiError, api } from '../api/client';
import type { Node, SessionView } from '../api/models';
import { Icon } from '../components/Icon';
import { Bubble, MessagesHeader, PhoneFrame, TypingDots } from '../components/Phone';
import { DisclosureLadder, SkillChips } from '../components/Progress';
import { BlockedCard, CrisisModal } from '../components/Safety';
import { ErrorBox, Spinner } from '../components/Status';
import { TreeDrawer } from '../components/TreeDrawer';
import { TrustChart } from '../components/TrustChart';
import { TrustMeter } from '../components/TrustMeter';
import { XrayFriend, XrayHelper } from '../components/Xray';
import { usePrefs } from '../i18n';
import { isEnded, labelsSeen, trustPoints } from '../lib/conversation';
import { scenarioById } from '../lib/scenarios';
import { load, save } from '../lib/storage';
import { prefersReducedMotion, typingDelay } from '../lib/typingDelay';

const MAX_CHARS = 500;
const SEEN_DELAY_MS = 900;
const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/** Which friend node is mid-reveal and how many of its bubbles are visible so far. */
type Reveal = { id: string; shown: number } | null;

export function Chat() {
  const { sessionId = '' } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { t, lang } = usePrefs();

  const [view, setView] = useState<SessionView | null>(null);
  const [loadError, setLoadError] = useState<ApiError | null>(null);
  const [name, setName] = useState('');
  const [reveal, setReveal] = useState<Reveal>(null);
  const [typing, setTyping] = useState(false);
  const [pendingText, setPendingText] = useState<string | null>(null);
  // What-if "Try this in the chat" hands over a suggested reply through router state.
  const [draft, setDraft] = useState<string>(() => (location.state as { draft?: string } | null)?.draft ?? '');
  const [sendError, setSendError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [xray, setXray] = useState(() => load('fr.xray') === '1');
  const [selected, setSelected] = useState<string | null>(null);
  const [treeOpen, setTreeOpen] = useState(false);

  const animation = useRef(0); // bumping this cancels an in-progress reveal
  const sending = useRef(false); // synchronous guard: a slow reply can never be sent twice
  const scroller = useRef<HTMLDivElement>(null);
  const input = useRef<HTMLTextAreaElement>(null);

  const loadSession = useCallback(() => {
    setLoadError(null);
    api.session(sessionId).then(
      (v) => {
        setView(v);
        scenarioById(v.scenario_id, lang).then((s) => setName(s?.persona_name ?? ''), () => undefined);
      },
      (e: ApiError) => setLoadError(e),
    );
  }, [sessionId]);
  useEffect(() => {
    loadSession();
  }, [loadSession]);
  useEffect(
    () => () => {
      animation.current++; // cancel any reveal still running when the page unmounts
    },
    [],
  );

  const nodes = useMemo(() => view?.nodes ?? [], [view]);
  const last = nodes[nodes.length - 1];
  const status = last?.state_after.status;
  const ended = isEnded(status);
  const crisisNode = status === 'paused_crisis' && last?.role === 'system' ? last : null;
  const points = useMemo(() => trustPoints(nodes), [nodes]);
  const { seen, latest } = useMemo(() => labelsSeen(nodes), [nodes]);
  const friendName = name || '…';

  // Keep the newest message in view.
  useEffect(() => {
    const el = scroller.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: prefersReducedMotion() ? 'auto' : 'smooth' });
  }, [nodes.length, reveal, typing, pendingText, xray, selected]);

  /** Reveal a friend reply bubble by bubble, each after its own typing delay. */
  async function animateFriend(node: Node) {
    const token = ++animation.current;
    const reduced = prefersReducedMotion();
    if (node.seen_no_reply || node.bubbles.length === 0) {
      setReveal({ id: node.id, shown: 0 });
      await sleep(reduced ? 0 : SEEN_DELAY_MS);
    } else {
      for (let i = 0; i < node.bubbles.length; i++) {
        if (token !== animation.current) return;
        setReveal({ id: node.id, shown: i });
        setTyping(true);
        await sleep(typingDelay(node.bubbles[i], reduced));
      }
    }
    if (token !== animation.current) return;
    setReveal(null);
    setTyping(false);
  }

  async function send() {
    const text = draft.trim();
    if (!text || busy || sending.current || ended || crisisNode) return;
    sending.current = true;
    setBusy(true);
    setSendError(null);
    setSelected(null);
    setPendingText(text);
    setDraft('');
    setTyping(true);
    try {
      const turn = await api.send(sessionId, text);
      const added = [turn.user_node, turn.friend_node, turn.system_node].filter((n): n is Node => !!n);
      if (turn.friend_node) setReveal({ id: turn.friend_node.id, shown: 0 });
      else setTyping(false);
      setView((v) => v && { ...v, head_id: added[added.length - 1].id, state: turn.state_after, nodes: [...v.nodes, ...added] });
      setPendingText(null);
      if (turn.friend_node) await animateFriend(turn.friend_node);
    } catch (e) {
      const error = e as ApiError;
      setTyping(false);
      setPendingText(null);
      setDraft(text);
      setSendError(`${t('chat.error_send')} ${error.message}`);
      if (error.status === 404) setLoadError(error);
    } finally {
      sending.current = false;
      setBusy(false);
      input.current?.focus();
    }
  }

  async function rewindTo(nodeId: string, prefill?: string) {
    animation.current++;
    setBusy(true);
    setSendError(null);
    try {
      const v = await api.rewind(sessionId, nodeId);
      setView(v);
      setReveal(null);
      setTyping(false);
      setSelected(null);
      setTreeOpen(false);
      if (prefill !== undefined) setDraft(prefill);
      setTimeout(() => input.current?.focus(), 0);
    } catch (e) {
      setSendError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      void send();
    }
  }

  function toggleXray() {
    setXray((on) => {
      save('fr.xray', on ? '0' : '1');
      return !on;
    });
  }

  if (loadError) {
    return loadError.status === 404 ? (
      <div className="mx-auto max-w-md px-4 py-16 text-center">
        <p className="text-lg font-semibold">{t('errors.session_gone')}</p>
        <Link to="/practice" className="btn-primary mt-6">
          {t('feedback.new_scenario')}
        </Link>
      </div>
    ) : (
      <ErrorBox message={loadError.message} onRetry={loadSession} />
    );
  }
  if (!view) return <Spinner />;

  const trustNow = points[points.length - 1]?.trust ?? 0;
  const lastDelta = points.length > 1 ? points[points.length - 1].delta : 0;

  // Only your most recent message gets a receipt ("Delivered", then "Read"), like a messaging app.
  const lastUserIdx = nodes.reduce((last, n, i) => (n.role === 'user' ? i : last), -1);
  const clock = (createdAt?: number) =>
    createdAt ? new Date(createdAt * 1000).toLocaleTimeString(lang === 'es' ? 'es-US' : 'en-US', { hour: 'numeric', minute: '2-digit' }) : '';

  /** Render one node of the path. */
  function renderNode(node: Node, idx: number) {
    const prev = nodes[idx - 1] ?? null;
    const next = nodes[idx + 1] ?? null;

    if (node.role === 'friend') {
      if (node.seen_no_reply) return null; // shown as "Read …" under the helper's message
      const shown = reveal?.id === node.id ? reveal.shown : node.bubbles.length;
      return (
        <div className="space-y-0.5">
          {node.bubbles.slice(0, shown).map((b, i) => (
            <Bubble key={i} tail={i === shown - 1}>
              {b}
            </Bubble>
          ))}
          {xray && idx > 0 && shown === node.bubbles.length && <XrayFriend node={node} />}
        </div>
      );
    }

    if (node.role === 'system') {
      if (prev?.guardian?.action === 'block_message') return <BlockedCard message={node.bubbles[0]} />;
      return (
        <p className="mx-auto w-fit rounded-full bg-warm-soft px-3 py-1 text-xs font-medium text-ink" role="note">
          {t('chat.crisis.title')}
        </p>
      );
    }

    // Helper (user) message
    const blocked = node.guardian?.action === 'block_message';
    const paused = node.guardian?.action === 'pause_roleplay';
    const concern = node.guardian?.action === 'show_resources';
    const showSeen = next?.seen_no_reply && reveal?.id !== next.id;
    const canRewind = !blocked && !paused && !!node.parent_id;
    // Receipt under your latest message: Delivered while they type, then Read (with a time if they
    // left you on read).
    let receipt: { text: string; seen: boolean } | null = null;
    if (idx === lastUserIdx && next?.role === 'friend') {
      if (next.seen_no_reply) receipt = showSeen ? { text: t('chat.read_at', { time: clock(next.created_at) }), seen: true } : { text: t('chat.delivered'), seen: false };
      else receipt = { text: reveal?.id === next.id ? t('chat.delivered') : t('chat.read'), seen: false };
    }
    return (
      <div className="space-y-1">
        <div className="flex justify-end pr-1.5">
          <button
            type="button"
            disabled={!canRewind || busy}
            onClick={() => setSelected(selected === node.id ? null : node.id)}
            aria-expanded={canRewind ? selected === node.id : undefined}
            aria-label={`${t('chat.you')}: ${node.bubbles[0]}`}
            className={`im im-bubble im-sent im-tail text-left animate-pop-in disabled:cursor-default ${
              blocked ? 'line-through decoration-white/70 opacity-60' : 'hover:brightness-110'
            } ${selected === node.id ? 'ring-2 ring-brand ring-offset-2 ring-offset-[rgb(var(--im-bg))]' : ''}`}
          >
            {node.bubbles[0]}
          </button>
        </div>
        {selected === node.id && (
          <div className="flex justify-end gap-2 animate-pop-in">
            <button type="button" className="btn-ghost px-3 py-1.5 text-xs" onClick={() => rewindTo(node.parent_id!, node.bubbles[0])} data-testid="rewind-here">
              <Icon name="rewind" className="h-3.5 w-3.5" />
              {busy ? t('chat.rewinding') : t('chat.rewind')}
            </button>
          </div>
        )}
        {receipt && (
          <p className="im-meta pr-2 text-right animate-pop-in" data-testid={receipt.seen ? 'seen' : 'receipt'}>
            {receipt.text}
          </p>
        )}
        {concern && <p className="ml-auto max-w-[80%] text-right text-xs text-muted">{t('chat.concern')}</p>}
        {xray && (node.guardian || node.events) && <XrayHelper node={node} before={prev?.state_after ?? null} />}
        {xray && showSeen && next && <div className="flex justify-start"><XrayFriend node={next} /></div>}
      </div>
    );
  }

  // X-ray banner: a solid strip under the contact bar (outside the scrolling messages, so nothing
  // ever slides underneath it).
  const xrayBanner = xray && (
    <div className="mt-2.5 flex items-center gap-2 overflow-hidden rounded-xl bg-night px-3 py-1.5 text-[11px] font-semibold text-night-ink" role="note" data-testid="xray-banner">
      <Icon name="eye" className="h-3.5 w-3.5 shrink-0 text-night-muted" />
      {t('chat.xray_banner')}
    </div>
  );

  const header = (
    <>
    <MessagesHeader
      name={friendName}
      left={
        <Link to="/practice" className="flex items-center rounded-full py-1 pr-2 text-[rgb(var(--im-sent))]" aria-label={t('chat.back')}>
          <Icon name="chevron" className="h-6 w-6" />
        </Link>
      }
      sub={
        typing ? (
          <span>{t('chat.typing', { name: friendName })}…</span>
        ) : (
          <span>
            {t('chat.trust')} <span className="mono-num font-semibold">{Math.round(trustNow)}</span>
          </span>
        )
      }
      right={
        <>
          <button type="button" onClick={() => setTreeOpen(true)} className="im-icon-btn" aria-label={t('chat.branches')} title={t('chat.branches')}>
            <Icon name="branch" className="h-4 w-4" />
          </button>
          <button
            type="button"
            role="switch"
            aria-checked={xray}
            onClick={toggleXray}
            title={xray ? t('chat.xray_off') : t('chat.xray_on')}
            className={`im-icon-btn ${xray ? '!bg-[rgb(var(--im-sent))] !text-white' : ''}`}
            data-testid="xray-toggle"
          >
            <Icon name="eye" className="h-4 w-4" />
            <span className="sr-only">{t('chat.xray')}</span>
          </button>
        </>
      }
    />
    {xrayBanner}
    </>
  );

  const composer = ended ? (
    <div className="border-t border-line/60 bg-[rgb(var(--im-bar))] p-3">
      <button type="button" className="btn-primary w-full" onClick={() => navigate(`/feedback/${sessionId}`)}>
        {t('chat.ended.see_feedback')}
      </button>
    </div>
  ) : (
    <form
      className="border-t border-line/60 bg-[rgb(var(--im-bar))] px-2.5 pb-1.5 pt-2"
      onSubmit={(e) => {
        e.preventDefault();
        void send();
      }}
    >
      {sendError && (
        <p role="alert" className="mb-2 rounded-lg bg-bad-soft px-3 py-1.5 text-xs text-bad">
          {sendError}
        </p>
      )}
      <div className="flex items-end gap-2">
        {/* The round "+" of a messaging app: decorative here (practice is text only). */}
        <span className="im-icon-btn mb-0.5 shrink-0 !text-[rgb(var(--im-meta))]" aria-hidden="true">
          <Icon name="plus" className="h-4 w-4" />
        </span>
        <div className="flex min-w-0 flex-1 items-end rounded-[1.3rem] border border-[rgb(var(--im-meta)/0.4)] bg-[rgb(var(--im-bg))] py-1 pl-3.5 pr-1 focus-within:ring-2 focus-within:ring-brand">
          <label htmlFor="composer" className="sr-only">
            {t('chat.placeholder', { name: friendName })}
          </label>
          <textarea
            id="composer"
            ref={input}
            rows={1}
            value={draft}
            maxLength={MAX_CHARS}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder={t('chat.placeholder', { name: friendName })}
            disabled={!!crisisNode}
            aria-describedby="composer-count"
            className="im max-h-32 min-h-[1.9rem] flex-1 resize-none bg-transparent py-1 leading-snug text-ink outline-none placeholder:text-[rgb(var(--im-meta))] focus-visible:ring-0 focus-visible:ring-offset-0"
            data-testid="composer"
          />
          <button
            type="submit"
            className="mb-px grid h-7 w-7 shrink-0 place-items-center rounded-full bg-[rgb(var(--im-sent))] text-white transition disabled:opacity-35"
            disabled={!draft.trim() || busy}
            aria-label={t('chat.send')}
          >
            <Icon name="up" className="h-4 w-4" />
          </button>
        </div>
      </div>
      <p id="composer-count" className={`mono-num mt-1 pr-2 text-right text-[10px] ${draft.length > MAX_CHARS - 50 ? 'text-bad' : 'im-meta'}`}>
        {t('chat.counter', { n: draft.length })}
      </p>
    </form>
  );

  return (
    <div className="mx-auto grid max-w-6xl gap-6 px-3 py-5 sm:px-6 lg:grid-cols-[minmax(0,26rem)_1fr] lg:items-start">
      <div className="lg:sticky lg:top-20">
        <div className="mb-3 flex items-center justify-between gap-2">
          <div className="flex min-w-0 flex-wrap items-center gap-2">
            <h1 className="text-lg font-bold">{t('chat.with', { name: friendName })}</h1>
            {/* The chat's language is the session's; the UI language never changes. */}
            {view.locale && view.locale !== lang && (
              <span className="chip border-line bg-sunken text-muted" data-testid="chat-locale">
                <Icon name="globe" className="h-3.5 w-3.5" />
                {t('chat.practice_in', { lang: t(`langs.${view.locale}`) })}
              </span>
            )}
          </div>
          <button type="button" className="btn-ghost px-4 py-2" onClick={() => navigate(`/feedback/${sessionId}`)} disabled={points.length < 2} data-testid="finish">
            <Icon name="flag" className="h-4 w-4" />
            {t('chat.finish')}
          </button>
        </div>
        <PhoneFrame header={header} footer={composer} bezelOnMobile={false} className="h-[calc(100svh-11rem)] min-h-[32rem] lg:h-[min(46rem,calc(100vh-9rem))]">
          <div ref={scroller} className="im-screen h-full space-y-2.5 overflow-y-auto overscroll-contain px-2.5 py-3" aria-live="polite" aria-relevant="additions" data-testid="messages">
            {nodes[0]?.created_at && (
              <p className="im-meta pb-1 text-center" data-testid="chat-timestamp">
                <b className="font-semibold">{t('chat.today')}</b> {clock(nodes[0].created_at)}
              </p>
            )}
            {nodes.map((node, idx) => (
              <Fragment key={node.id}>{renderNode(node, idx)}</Fragment>
            ))}
            {pendingText && (
              <div className="space-y-1" aria-busy="true">
                <Bubble me>{pendingText}</Bubble>
                <p className="im-meta pr-2 text-right">{t('chat.delivered')}</p>
              </div>
            )}
            {typing && <TypingDots label={t('chat.typing', { name: friendName })} />}
            {ended && !reveal && (
              <div
                className={`mt-4 rounded-2xl p-4 text-center animate-pop-in ${status === 'ended_success' ? 'bg-good-soft' : 'bg-sunken'}`}
                data-testid={status === 'ended_success' ? 'end-success' : 'end-fail'}
              >
                <p className="text-3xl" aria-hidden="true">
                  {status === 'ended_success' ? '💛' : '🌧️'}
                </p>
                <p className="mt-1 font-bold">{status === 'ended_success' ? t('chat.ended.success_title') : t('chat.ended.fail_title')}</p>
                <p className="mt-1 text-sm leading-relaxed text-muted">{status === 'ended_success' ? t('chat.ended.success_body') : t('chat.ended.fail_body')}</p>
                <p className="mt-2 text-xs text-muted">{t('chat.ended.rewind_hint')}</p>
              </div>
            )}
          </div>
        </PhoneFrame>
      </div>

      <aside className="space-y-4" aria-label={t('chat.panel_title')}>
        <section className="card p-4">
          <div className="mb-3 flex items-center justify-between gap-4">
            <div>
              <h2 className="text-lg">{t('chat.trust_graph')}</h2>
              <p className="mt-1 max-w-[12rem] text-sm text-muted">{t('chat.trust_hint')}</p>
            </div>
            <div data-testid="trust-now">
              <TrustMeter value={trustNow} delta={points.length > 1 ? lastDelta : undefined} label={t('chat.trust')} />
            </div>
          </div>
          <TrustChart points={points} />
        </section>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
          <section className="card p-4">
            <h2 className="mb-3 text-lg">{t('chat.ladder')}</h2>
            <DisclosureLadder level={last?.state_after.level ?? 0} />
          </section>
          <section className="card p-4">
            <h2 className="mb-1 text-lg">{t('chat.skills')}</h2>
            <p className="mb-3 text-xs text-muted">{t('chat.skills_hint')}</p>
            <SkillChips seen={seen} latest={latest} />
          </section>
        </div>
      </aside>

      <CrisisModal
        key={crisisNode?.id ?? 'none'}
        open={!!crisisNode}
        message={crisisNode?.bubbles[0]}
        onAcknowledge={() => {
          const userNode = nodes.find((n) => n.id === crisisNode?.parent_id);
          if (userNode?.parent_id) void rewindTo(userNode.parent_id);
        }}
      />
      <TreeDrawer sessionId={sessionId} open={treeOpen} onClose={() => setTreeOpen(false)} onJump={(id) => rewindTo(id)} />
    </div>
  );
}
