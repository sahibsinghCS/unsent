// Landing page: a calm opening (night sky or dawn wash, a light that breathes behind the phone, the
// headline rising line by line, the phone with the recorded real run), the "1 in 5" band, three
// steps that each animate a real snippet of the app when they scroll into view, the annotated
// conversation (lib/demoTranscript), and where to get real help. Every motion plays once, is slow and
// eased, and is skipped entirely with reduced motion. Help UI never animates.
import { useId, useLayoutEffect, useRef, useState, type ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { LiveDemo } from '../components/LiveDemo';
import { Bubble } from '../components/Phone';
import { Call988 } from '../components/Safety';
import { StarField } from '../components/StarField';
import { useCountUp } from '../components/TrustMeter';
import { usePrefs } from '../i18n';
import { demoRun, turnSummary, type DemoTurn } from '../lib/demoTranscript';
import { useInView } from '../lib/useInView';

// Rows shown before "See the whole conversation": the opening plus check-in, the dismissive reply
// (left on Read) and the apology.
const FIRST_TURNS = 3;

/** The note beside one recorded turn, generated from the data: Guardian time, skills, trust, reply. */
function turnNote(turn: DemoTurn, prevLevel: number | null, first: boolean, t: (k: string, v?: Record<string, string | number>) => string) {
  const sum = turnSummary(turn);
  const asked = turn.skills.includes('asked_directly');
  const parts = [t('landing.run.safety', { ms: Math.round(turn.guardian_ms) })];
  if (asked) parts.push(t('landing.run.direct'));
  parts.push(
    turn.skills.length
      ? t('landing.run.heard', { labels: turn.skills.map((s) => `“${t(`labels.${s}`)}”`).join(', ') })
      : t('landing.run.heard_none'),
  );
  parts.push(t(sum.up ? 'landing.run.up' : 'landing.run.down', { from: sum.from, to: sum.to }));
  if (turn.seen) parts.push(t('landing.run.read'));
  else if (asked) parts.push(t('landing.run.not_ready'));
  else if (prevLevel !== null && turn.level_after > prevLevel) parts.push(t('landing.run.level_up', { level: turn.level_after }));
  if (first) parts.push(t('landing.run.bank'));
  return parts.join(' ');
}

function AnnotatedExample() {
  const { t, lang } = usePrefs();
  const run = demoRun(lang);
  const [open, setOpen] = useState(false);
  const restId = useId();
  const unsent = run.turns.findIndex((x) => x.line_id);
  const row = (turn: DemoTurn, i: number) => (
    <Row
      key={i}
      testid="example-turn"
      thread={
        <>
          <Bubble me>{turn.you}</Bubble>
          {turn.seen ? (
            <p className="im-meta pr-3 text-right">{t('chat.read_at', { time: '9:42 PM' })}</p>
          ) : (
            turn.friend.map((b, j) => (
              <Bubble key={j} tail={j === turn.friend.length - 1}>
                {b}
              </Bubble>
            ))
          )}
        </>
      }
      label={t('landing.run.label_you', { n: i + 1 })}
      note={turnNote(turn, i > 0 ? run.turns[i - 1].level_after : null, i === unsent, t)}
    />
  );
  return (
    <div>
      <ol id={restId} className="im-screen divide-y divide-line overflow-hidden rounded-2xl border border-line" data-testid="annotated-example">
        <Row
          thread={run.opening.map((b, j) => (
            <Bubble key={j} tail={j === run.opening.length - 1}>
              {b}
            </Bubble>
          ))}
          label={t('landing.run.label_friend')}
          note={t('landing.run.opening', { trust: Math.round(run.turns[0]?.trust_before ?? 0) })}
        />
        {run.turns.slice(0, FIRST_TURNS).map(row)}
        {open && run.turns.slice(FIRST_TURNS).map((turn, i) => row(turn, i + FIRST_TURNS))}
      </ol>
      {run.turns.length > FIRST_TURNS && (
        <button
          type="button"
          className="btn-ghost mt-4"
          aria-expanded={open}
          aria-controls={restId}
          onClick={() => setOpen((v) => !v)}
          data-testid="example-more"
        >
          {open ? t('landing.run.less') : t('landing.run.more', { n: run.turns.length - FIRST_TURNS })}
        </button>
      )}
      <span className="sr-only" aria-live="polite">
        {open ? t('landing.run.expanded') : ''}
      </span>
    </div>
  );
}

/** One annotated row; it fades in with an 8px rise the first time it scrolls into view. */
function Row({ thread, label, note, testid }: { thread: ReactNode; label: string; note: string; testid?: string }) {
  const [ref, seen] = useInView<HTMLLIElement>();
  return (
    <li ref={ref} className={`reveal grid gap-2 px-3 py-3 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] md:items-center md:gap-6 md:px-5 ${seen ? 'is-in' : ''}`} data-testid={testid}>
      <div className="space-y-1 py-1">{thread}</div>
      <p className="border-l-2 border-line pl-3 text-sm leading-relaxed text-[rgb(var(--im-meta))] md:border-l md:pl-4">
        <span className="font-semibold text-[rgb(var(--im-recv-ink))]">{label}</span> {note}
      </p>
    </li>
  );
}

/** Step 1 snippet: Maya's real opening text and your real first reply; the bubbles slide in on view. */
function ChatSnippet() {
  const { lang } = usePrefs();
  const run = demoRun(lang);
  const [ref, seen] = useInView<HTMLDivElement>();
  const bubbles = [
    <Bubble key="a">{run.opening[run.opening.length - 1]}</Bubble>,
    <Bubble key="b" me>
      {run.turns[0].you}
    </Bubble>,
    <Bubble key="c">{run.turns[0].friend[0]}</Bubble>,
  ];
  return (
    <div ref={ref} className="im-screen space-y-1 overflow-hidden rounded-xl border border-line px-3 py-3" aria-hidden="true">
      {bubbles.map((b, i) => (
        <div key={i} className={`reveal ${seen ? 'is-in' : ''}`} style={{ transitionDelay: `${i * 450}ms` }}>
          {b}
        </div>
      ))}
    </div>
  );
}

/** Step 2 snippet: X-ray for the real "ask directly" turn; on view the trust bar fills and the number ticks. */
function XraySnippet() {
  const { t, lang } = usePrefs();
  const run = demoRun(lang);
  const turn = run.turns.find((x) => x.skills.includes('asked_directly')) ?? run.turns[0];
  const sum = turnSummary(turn);
  const [ref, seen] = useInView<HTMLDivElement>();
  const trust = useCountUp(seen ? sum.to : sum.from, 1200);
  return (
    <div ref={ref} className="night-panel space-y-2.5 p-4 text-[12px]" aria-hidden="true">
      <p className="flex justify-between gap-2">
        <span className="text-night-muted">{t('landing.snip.guardian')}</span>
        <span className="mono-num text-night-ink">
          {turn.guardian} · {Math.round(turn.guardian_ms)} ms
        </span>
      </p>
      <p className="flex justify-between gap-2">
        <span className="text-night-muted">{t('landing.snip.heard')}</span>
        <span className={`font-semibold text-night-ink transition-opacity delay-300 duration-700 ${seen ? 'opacity-100' : 'opacity-0'}`}>{t(`labels.${sum.skill}`)}</span>
      </p>
      <div>
        <p className="flex justify-between gap-2">
          <span className="text-night-muted">{t('landing.snip.trust')}</span>
          <span className="mono-num text-night-ink">
            {sum.from} → {Math.round(trust)}
          </span>
        </p>
        <span className="relative mt-1.5 block h-1.5 overflow-hidden rounded-full bg-white/10">
          <span className="absolute inset-y-0 left-0 rounded-full bg-white/30 transition-[width] duration-[1200ms] ease-out" style={{ width: `${seen ? sum.to : 0}%` }} />
          <span className="absolute inset-y-0 left-0 rounded-full bg-[#30D158] transition-[width] duration-[1200ms] ease-out" style={{ width: `${seen ? sum.from : 0}%` }} />
        </span>
      </div>
    </div>
  );
}

/** Step 3 snippet: the real reply that lost her, then (fading in after it) the real reply that won her back. */
function LessonSnippet() {
  const { t, lang } = usePrefs();
  const run = demoRun(lang);
  const lost = run.turns.findIndex((x) => x.seen);
  const pair = [run.turns[lost], run.turns[lost + 1]].filter(Boolean);
  const [ref, seen] = useInView<HTMLDivElement>();
  return (
    <div ref={ref} className="space-y-2" aria-hidden="true">
      {pair.map((turn, i) => {
        const sum = turnSummary(turn);
        return (
          <div
            key={i}
            className={`reveal rounded-xl border p-3 ${i === 0 ? 'border-bad/40 bg-bad-soft/50' : 'border-good/40 bg-good-soft/50'} ${seen ? 'is-in' : ''}`}
            style={{ transitionDelay: `${i * 900}ms` }}
          >
            <p className="flex justify-between gap-2 text-xs font-semibold">
              <span className="text-ink">{t(i === 0 ? 'landing.snip.lost' : 'landing.snip.back')}</span>
              <span className={`mono-num ${i === 0 ? 'text-bad' : 'text-good'}`}>
                {sum.from} → {sum.to}
              </span>
            </p>
            <p className="mt-1 text-sm leading-snug">“{turn.you}”</p>
          </div>
        );
      })}
    </div>
  );
}

function Step({ n, title, body, children }: { n: number; title: string; body: string; children: ReactNode }) {
  return (
    <li className="card card-lift flex flex-col p-5 sm:p-6">
      <span className="meta-label">{String(n).padStart(2, '0')}</span>
      <h3 className="mt-3 text-xl">{title}</h3>
      <p className="mt-2 leading-relaxed text-muted">{body}</p>
      <div className="mt-5 flex flex-1 flex-col justify-end">{children}</div>
    </li>
  );
}

/**
 * The headline, rising line by line (700 ms each, 120 ms apart). Words are measured after layout so
 * the stagger follows the real line breaks at any width; no letter-by-letter typing.
 */
function RiseLines({ text, delay = 0 }: { text: string; delay?: number }) {
  const ref = useRef<HTMLSpanElement>(null);
  const [lines, setLines] = useState<number[]>([]);
  const words = text.split(' ');
  useLayoutEffect(() => {
    const spans = ref.current?.querySelectorAll<HTMLSpanElement>('[data-word]') ?? [];
    const tops: number[] = [];
    setLines(
      Array.from(spans, (el) => {
        const top = Math.round(el.offsetTop);
        if (!tops.includes(top)) tops.push(top);
        return tops.indexOf(top);
      }),
    );
  }, [text]);
  return (
    <span ref={ref}>
      {words.map((w, i) => (
        <span key={i}>
          <span data-word className="inline-block animate-rise-in" style={{ animationDelay: `${delay + (lines[i] ?? 0) * 120}ms` }}>
            {w}
          </span>{' '}
        </span>
      ))}
    </span>
  );
}

/** "1 in 5" with the digits set in Plex Sans (Syne's "1" reads like a dotless i). */
function StatNumeral({ text }: { text: string }) {
  return (
    <>
      {text.split(/(\d+)/).map((part, i) =>
        /\d/.test(part) ? (
          <span key={i} className="font-sans font-semibold">
            {part}
          </span>
        ) : (
          part
        ),
      )}
    </>
  );
}

/** Five figures; once the band is in view, one of them softly lights up in the accent over 1.2 s. */
function FiveFigures({ lit }: { lit: boolean }) {
  return (
    <div className="flex items-end gap-3" aria-hidden="true">
      {[0, 1, 2, 3, 4].map((i) => (
        <svg key={i} viewBox="0 0 24 40" className="h-10 w-6 md:h-12 md:w-7">
          <circle cx="12" cy="7" r="6" className={`transition-colors delay-500 duration-[1200ms] ease-in-out ${i === 2 && lit ? 'fill-[rgb(var(--brand))]' : 'fill-[rgb(var(--night-muted)/0.35)]'}`} />
          <path d="M2 40v-14a10 10 0 0 1 20 0v14z" className={`transition-colors delay-500 duration-[1200ms] ease-in-out ${i === 2 && lit ? 'fill-[rgb(var(--brand))]' : 'fill-[rgb(var(--night-muted)/0.35)]'}`} />
        </svg>
      ))}
    </div>
  );
}

function StatBand() {
  const { t } = usePrefs();
  const [ref, seen] = useInView<HTMLDivElement>();
  const big = t('landing.stat_big');
  return (
    <section className="bg-night text-night-ink" data-testid="stat-band">
      <div ref={ref} className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-16 sm:px-6 md:flex-row md:items-center md:gap-14 md:py-20">
        <div className={`reveal shrink-0 space-y-5 ${seen ? 'is-in' : ''}`}>
          <p className={`numeral leading-[0.95] ${big.length > 6 ? 'text-6xl md:max-w-[5.5ch] md:text-[5.5rem]' : 'whitespace-nowrap text-7xl md:text-[7.5rem]'}`}>
            <StatNumeral text={big} />
          </p>
          <FiveFigures lit={seen} />
        </div>
        <div className="space-y-4">
          <p className="text-xl leading-snug sm:text-2xl">{t('landing.stat')}</p>
          <p className="font-mono text-xs leading-relaxed text-night-muted">{t('landing.stat_source')}</p>
          <p className="pt-1 text-xl leading-snug sm:text-2xl">{t('landing.stat_kicker')}</p>
          <p className="font-mono text-xs leading-relaxed text-night-muted">{t('landing.kicker_source')}</p>
        </div>
      </div>
    </section>
  );
}

export function Landing() {
  const { t, tl, theme } = usePrefs();
  const stepTitles = tl('landing.steps_title');
  const stepBodies = tl('landing.steps_body');
  const snippets = [<ChatSnippet key="c" />, <XraySnippet key="x" />, <LessonSnippet key="l" />];
  return (
    <div className="overflow-x-hidden">
      <section className="hero-sky relative isolate">
        {theme === 'dark' && <StarField className="absolute inset-0 -z-10 h-full w-full" />}
        <div className="mx-auto grid max-w-6xl items-center gap-14 px-4 pb-20 pt-12 sm:px-6 md:grid-cols-[1.15fr_1fr] md:pt-20">
          <div>
            <h1 className="text-[2.75rem] leading-[1.0] sm:text-6xl lg:text-[5.2rem]">
              <RiseLines text={t('landing.title')} />
            </h1>
            <p className="mt-7 max-w-xl animate-rise-in text-lg leading-relaxed text-muted [animation-delay:420ms]">{t('landing.sub')}</p>
            <div className="mt-9 flex animate-fade-in flex-wrap items-center gap-3 [animation-delay:1300ms]">
              <Link to="/practice" className="btn-primary px-7 py-3.5 text-base" data-testid="start-practicing">
                {t('landing.start')}
              </Link>
              <Link to="/how" className="btn-ghost px-6 py-3.5 text-base">
                {t('landing.how')}
              </Link>
            </div>
          </div>
          <div className="relative">
            {/* The breathing light: one soft, slow radial light behind the phone (not a glow on UI). */}
            <div className="pointer-events-none absolute left-1/2 top-1/2 -z-10 h-[34rem] w-[34rem] -translate-x-1/2 -translate-y-1/2" aria-hidden="true">
              <div className="breathe-light h-full w-full animate-breathe rounded-full" />
            </div>
            <div className="animate-rise-phone [animation-delay:250ms]">
              <LiveDemo />
            </div>
          </div>
        </div>
      </section>

      <StatBand />

      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <h2 className="max-w-3xl text-4xl leading-[1.05] sm:text-5xl">{t('landing.features_title')}</h2>
        <ol className="mt-10 grid gap-5 md:grid-cols-3">
          {stepTitles.map((title, i) => (
            <Step key={i} n={i + 1} title={title} body={stepBodies[i]}>
              {snippets[i]}
            </Step>
          ))}
        </ol>
      </section>

      <section className="section-rule mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <h2 className="text-3xl sm:text-4xl">{t('landing.example_title')}</h2>
        <p className="mt-3 max-w-2xl text-muted">{t('landing.example_sub')}</p>
        <div className="mt-8">
          <AnnotatedExample />
        </div>
        <p className="mt-4 font-mono text-xs text-muted" data-testid="real-run-note">
          {t('landing.run.note')}
        </p>
        <div className="mt-8">
          <Link to="/practice" className="btn-primary">
            {t('landing.start')}
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-14 sm:px-6">
        <div className="card flex flex-col gap-5 p-6 sm:p-8 md:flex-row md:items-center md:justify-between">
          <div className="min-w-0 flex-1">
            <h2 className="text-2xl">{t('landing.safety_title')}</h2>
            <p className="mt-2 max-w-xl leading-relaxed text-muted">
              {t('landing.safety_body')}{' '}
              <Link to="/real" className="link">
                {t('landing.safety_link')}
              </Link>
            </p>
          </div>
          <div className="w-full shrink-0 md:w-72">
            <Call988 compact />
          </div>
        </div>
      </section>
    </div>
  );
}
