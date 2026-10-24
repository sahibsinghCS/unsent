// Landing page: a plain headline beside the live conversation, the key fact with its source, and an
// annotated conversation (a recorded real run, see lib/demoTranscript) that explains the product the way X-ray does: each message, plus a short
// note on what the app did with it. Then where to get real help.
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { LiveDemo } from '../components/LiveDemo';
import { Bubble } from '../components/Phone';
import { Call988 } from '../components/Safety';
import { usePrefs } from '../i18n';
import { DEMO_RECORDED_AT, demoRun, turnSummary, type DemoTurn } from '../lib/demoTranscript';

/** The note beside one recorded turn: Guardian time, skills heard, trust change, and how Maya replied. */
function turnNote(turn: DemoTurn, first: boolean, t: (k: string, v?: Record<string, string | number>) => string) {
  const sum = turnSummary(turn);
  const parts = [t('landing.run.safety', { ms: Math.round(turn.guardian.ms) })];
  parts.push(
    turn.skills.length
      ? t('landing.run.heard', { labels: turn.skills.map((s) => `“${t(`labels.${s}`)}”`).join(', ') })
      : t('landing.run.heard_none'),
  );
  if (turn.skills.includes('asked_directly')) parts.push(t('landing.run.direct'));
  parts.push(t(sum.up ? 'landing.run.up' : 'landing.run.down', { from: sum.from, to: sum.to }));
  if (turn.friend?.seen) parts.push(t('landing.run.read'));
  else if (turn.status === 'ended_success') parts.push(t('landing.run.success'));
  else if (turn.level_after > turn.level_before) parts.push(t('landing.run.level_up', { level: turn.level_after }));
  else if (turn.skills.includes('asked_directly')) parts.push(t('landing.run.level_same', { level: turn.level_after }));
  if (first && turn.friend?.voice === 'bank') parts.push(t('landing.run.bank'));
  return parts.join(' ');
}

function AnnotatedExample() {
  const { t, lang } = usePrefs();
  const run = demoRun(lang);
  const firstReply = run.turns.findIndex((x) => x.friend?.voice === 'bank');
  return (
    <ol className="im-screen divide-y divide-line/70 overflow-hidden rounded-xl border border-line/70" data-testid="annotated-example">
      <Row
        thread={run.opening.map((b, j) => (
          <Bubble key={j} tail={j === run.opening.length - 1}>
            {b}
          </Bubble>
        ))}
        label={t('landing.run.label_friend')}
        note={t('landing.run.opening', { trust: Math.round(run.trust_start) })}
      />
      {run.turns.map((turn, i) => (
        <Row
          key={i}
          testid="example-turn"
          thread={
            <>
              <Bubble me>{turn.text}</Bubble>
              {turn.friend?.seen ? (
                <p className="im-meta pr-3 text-right">{t('chat.read_at', { time: '9:42 PM' })}</p>
              ) : (
                turn.friend?.bubbles.map((b, j) => (
                  <Bubble key={j} tail={j === turn.friend!.bubbles.length - 1}>
                    {b}
                  </Bubble>
                ))
              )}
            </>
          }
          label={t('landing.run.label_you', { n: i + 1 })}
          note={turnNote(turn, i === firstReply, t)}
        />
      ))}
    </ol>
  );
}

function Row({ thread, label, note, testid }: { thread: ReactNode; label: string; note: string; testid?: string }) {
  return (
    <li className="grid gap-2 px-3 py-3 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] md:items-center md:gap-6 md:px-5" data-testid={testid}>
      <div className="space-y-1 py-1">{thread}</div>
      <p className="border-l-2 border-line pl-3 text-sm leading-relaxed text-muted md:border-l md:pl-4">
        <span className="font-semibold text-ink">{label}</span> {note}
      </p>
    </li>
  );
}

export function Landing() {
  const { t } = usePrefs();
  return (
    <div className="overflow-x-hidden">
      <section className="mx-auto grid max-w-6xl items-center gap-12 px-4 pb-14 pt-10 sm:px-6 md:grid-cols-[1.1fr_1fr] md:pt-14">
        <div>
          <h1 className="text-[2.4rem] leading-[1.08] sm:text-5xl lg:text-[3.4rem]">{t('landing.title')}</h1>
          <p className="mt-5 max-w-xl text-lg leading-relaxed text-muted">{t('landing.sub')}</p>
          <div className="mt-8 flex flex-wrap items-center gap-x-6 gap-y-3">
            <Link to="/practice" className="btn-primary px-6 py-3 text-base" data-testid="start-practicing">
              {t('landing.start')}
            </Link>
            <Link to="/how" className="link">
              {t('landing.how')}
            </Link>
          </div>
          <div className="mt-10 max-w-xl space-y-3 border-t border-line/70 pt-6 text-[15px] leading-relaxed">
            <p>
              {t('landing.stat')} <span className="text-sm text-muted">({t('landing.stat_source')})</span>
            </p>
            <p>
              {t('landing.stat_kicker')} <span className="text-sm text-muted">({t('landing.kicker_source')})</span>
            </p>
          </div>
        </div>
        <LiveDemo />
      </section>

      <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6">
        <h2 className="text-3xl sm:text-4xl">{t('landing.example_title')}</h2>
        <p className="mt-2 max-w-2xl text-muted">{t('landing.example_sub')}</p>
        <div className="mt-6">
          <AnnotatedExample />
        </div>
        <p className="mt-3 text-sm text-muted" data-testid="real-run-note">
          {t('landing.run.note', { date: DEMO_RECORDED_AT })}
        </p>
        <div className="mt-6">
          <Link to="/practice" className="btn-primary">
            {t('landing.start')}
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-10 sm:px-6">
        <div className="card flex flex-col gap-4 p-5 sm:p-6 md:flex-row md:items-center md:justify-between">
          <div>
            <h2 className="text-xl">{t('landing.safety_title')}</h2>
            <p className="mt-1 max-w-xl leading-relaxed text-muted">
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
