// Landing page: a big headline beside the live demo, the "1 in 5" band with sources, three steps
// that each show a real snippet of the app, the annotated conversation (a recorded real run, see
// lib/demoTranscript) that explains the product the way X-ray does: each message, plus a short
// note on what the app did with it. Then where to get real help.
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { LiveDemo } from '../components/LiveDemo';
import { Bubble } from '../components/Phone';
import { Call988 } from '../components/Safety';
import { usePrefs } from '../i18n';
import { demoRun, turnSummary, type DemoTurn } from '../lib/demoTranscript';

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
  const firstReply = run.turns.findIndex((x) => x.line_id);
  return (
    <ol className="im-screen divide-y divide-line overflow-hidden rounded-2xl border border-line" data-testid="annotated-example">
      <Row
        thread={run.opening.map((b, j) => (
          <Bubble key={j} tail={j === run.opening.length - 1}>
            {b}
          </Bubble>
        ))}
        label={t('landing.run.label_friend')}
        note={t('landing.run.opening', { trust: Math.round(run.turns[0]?.trust_before ?? 0) })}
      />
      {run.turns.map((turn, i) => (
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
          note={turnNote(turn, i > 0 ? run.turns[i - 1].level_after : null, i === firstReply, t)}
        />
      ))}
    </ol>
  );
}

function Row({ thread, label, note, testid }: { thread: ReactNode; label: string; note: string; testid?: string }) {
  return (
    <li className="grid gap-2 px-3 py-3 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] md:items-center md:gap-6 md:px-5" data-testid={testid}>
      <div className="space-y-1 py-1">{thread}</div>
      <p className="border-l-2 border-line pl-3 text-sm leading-relaxed text-[rgb(var(--im-meta))] md:border-l md:pl-4">
        <span className="font-semibold text-[rgb(var(--im-recv-ink))]">{label}</span> {note}
      </p>
    </li>
  );
}

/** Step 1 snippet: Maya's real opening text and your real first reply, as Messages bubbles. */
function ChatSnippet() {
  const { lang } = usePrefs();
  const run = demoRun(lang);
  return (
    <div className="im-screen space-y-1 overflow-hidden rounded-xl border border-line px-3 py-3" aria-hidden="true">
      <Bubble>{run.opening[run.opening.length - 1]}</Bubble>
      <Bubble me>{run.turns[0].you}</Bubble>
      <Bubble>{run.turns[0].friend[0]}</Bubble>
    </div>
  );
}

/** Step 2 snippet: what X-ray showed for the real "ask directly" turn (Guardian, skill, trust). */
function XraySnippet() {
  const { t, lang } = usePrefs();
  const run = demoRun(lang);
  const turn = run.turns.find((x) => x.skills.includes('asked_directly')) ?? run.turns[0];
  const sum = turnSummary(turn);
  return (
    <div className="night-panel space-y-2.5 p-4 text-[12px]" aria-hidden="true">
      <p className="flex justify-between gap-2">
        <span className="text-night-muted">{t('landing.snip.guardian')}</span>
        <span className="mono-num text-night-ink">
          {turn.guardian} · {Math.round(turn.guardian_ms)} ms
        </span>
      </p>
      <p className="flex justify-between gap-2">
        <span className="text-night-muted">{t('landing.snip.heard')}</span>
        <span className="font-semibold text-night-ink">{t(`labels.${sum.skill}`)}</span>
      </p>
      <div>
        <p className="flex justify-between gap-2">
          <span className="text-night-muted">{t('landing.snip.trust')}</span>
          <span className="mono-num text-night-ink">
            {sum.from} → {sum.to}
          </span>
        </p>
        <span className="relative mt-1.5 block h-1.5 overflow-hidden rounded-full bg-white/10">
          <span className="absolute inset-y-0 left-0 rounded-full bg-white/30" style={{ width: `${sum.to}%` }} />
          <span className="absolute inset-y-0 left-0 rounded-full bg-[#30D158]" style={{ width: `${sum.from}%` }} />
        </span>
      </div>
    </div>
  );
}

/** Step 3 snippet: the real reply that lost her (left on Read) next to the real reply that won her back. */
function LessonSnippet() {
  const { t, lang } = usePrefs();
  const run = demoRun(lang);
  const lost = run.turns.findIndex((x) => x.seen);
  const pair = [run.turns[lost], run.turns[lost + 1]].filter(Boolean);
  return (
    <div className="space-y-2" aria-hidden="true">
      {pair.map((turn, i) => {
        const sum = turnSummary(turn);
        return (
          <div key={i} className={`rounded-xl border p-3 ${i === 0 ? 'border-bad/40 bg-bad-soft/50' : 'border-good/40 bg-good-soft/50'}`}>
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

export function Landing() {
  const { t, tl } = usePrefs();
  const stepTitles = tl('landing.steps_title');
  const stepBodies = tl('landing.steps_body');
  const snippets = [<ChatSnippet key="c" />, <XraySnippet key="x" />, <LessonSnippet key="l" />];
  return (
    <div className="overflow-x-hidden">
      <section className="hero-vignette">
        <div className="mx-auto grid max-w-6xl items-center gap-14 px-4 pb-20 pt-12 sm:px-6 md:grid-cols-[1.15fr_1fr] md:pt-20">
          <div>
            <h1 className="text-[2.7rem] leading-[0.98] sm:text-6xl lg:text-[4.6rem]">{t('landing.title')}</h1>
            <p className="mt-7 max-w-xl text-lg leading-relaxed text-muted">{t('landing.sub')}</p>
            <div className="mt-9 flex flex-wrap items-center gap-3">
              <Link to="/practice" className="btn-primary px-7 py-3.5 text-base" data-testid="start-practicing">
                {t('landing.start')}
              </Link>
              <Link to="/how" className="btn-ghost px-6 py-3.5 text-base">
                {t('landing.how')}
              </Link>
            </div>
          </div>
          <LiveDemo />
        </div>
      </section>

      <section className="bg-night text-night-ink" data-testid="stat-band">
        <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-14 sm:px-6 md:flex-row md:items-center md:gap-14 md:py-16">
          <p className={`numeral shrink-0 leading-[0.95] ${t('landing.stat_big').length > 6 ? 'text-6xl md:max-w-[5.5ch] md:text-[5.5rem]' : 'whitespace-nowrap text-7xl md:text-[7.5rem]'}`}>
            {t('landing.stat_big')}
          </p>
          <div className="space-y-4">
            <p className="text-xl leading-snug sm:text-2xl">{t('landing.stat')}</p>
            <p className="font-mono text-xs leading-relaxed text-night-muted">{t('landing.stat_source')}</p>
            <p className="pt-1 text-xl leading-snug sm:text-2xl">{t('landing.stat_kicker')}</p>
            <p className="font-mono text-xs leading-relaxed text-night-muted">{t('landing.kicker_source')}</p>
          </div>
        </div>
      </section>

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
        <p className="mt-3 font-mono text-xs text-muted" data-testid="real-run-note">
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
