/**
 * The landing page's live demo: the recorded real run (lib/demoTranscript) replayed in a phone. "You"
 * type each message, it sends with a small note (the skill the detector heard and how trust moved),
 * then Maya types her real reply or leaves you on Read. Older messages scroll off the top. Pure React
 * state + CSS; reduced motion shows the whole thread at once.
 */
import { useEffect, useMemo, useState } from 'react';
import { usePrefs } from '../i18n';
import { demoRun, turnSummary, type DemoTurn } from '../lib/demoTranscript';
import { prefersReducedMotion } from '../lib/typingDelay';
import { Icon } from './Icon';
import { Bubble, MessagesHeader, PhoneFrame, TypingDots } from './Phone';

type Step = { kind: 'type' | 'sent' | 'typing' | 'read' | 'friend'; turn: number; ms: number };

/** The replay timeline: per turn, type → sent → (typing → friend) or read. */
function timeline(turns: DemoTurn[]): Step[] {
  return turns.flatMap((t, i) => {
    const steps: Step[] = [
      { kind: 'type', turn: i, ms: Math.min(2600, 38 * t.text.length) + 400 },
      { kind: 'sent', turn: i, ms: 1100 },
    ];
    if (t.friend?.seen) steps.push({ kind: 'read', turn: i, ms: 2400 });
    else if (t.friend) steps.push({ kind: 'typing', turn: i, ms: 1300 }, { kind: 'friend', turn: i, ms: 1500 + 450 * t.friend.bubbles.length });
    return steps;
  });
}

export function LiveDemo() {
  const { t, lang } = usePrefs();
  const run = demoRun(lang);
  const steps = useMemo(() => timeline(run.turns), [run]);
  const [step, setStep] = useState(-1);
  const [typed, setTyped] = useState(0);

  useEffect(() => {
    if (prefersReducedMotion()) {
      setStep(steps.length - 1);
      return undefined;
    }
    let timers: ReturnType<typeof setTimeout>[] = [];
    const play = () => {
      timers.forEach(clearTimeout);
      timers = [];
      setStep(-1);
      let at = 1200;
      steps.forEach((s, i) => {
        timers.push(setTimeout(() => setStep(i), at));
        if (s.kind === 'type') {
          const text = run.turns[s.turn].text;
          const span = s.ms - 400;
          for (let c = 0; c <= text.length; c++) timers.push(setTimeout(() => setTyped(c), at + (span * c) / text.length));
        }
        at += s.ms;
      });
      timers.push(setTimeout(play, at + 6000));
    };
    play();
    return () => timers.forEach(clearTimeout);
  }, [steps, run]);

  const current = steps[step];
  const shown = steps.slice(0, step + 1);
  return (
    <div className="relative mx-auto w-full max-w-[20rem]" aria-hidden="true">
      <PhoneFrame
        header={<MessagesHeader name="Maya" sub={current?.kind === 'typing' ? t('chat.typing', { name: 'Maya' }) : undefined} left={<Icon name="chevron" className="h-6 w-6 text-[rgb(var(--im-sent))]" />} />}
        className="h-[31rem]"
      >
        {/* Top-aligned while the thread is short; once it overflows, the newest stays in view (justify-end). */}
        <div className="im-screen flex h-full flex-col justify-end overflow-hidden px-2.5 pb-16 pt-3">
          <div className="flex shrink-0 grow flex-col gap-1">
          <p className="im-meta shrink-0 pb-1 text-center">
            <b className="font-semibold">{t('chat.today')}</b> 9:41 PM
          </p>
          {run.opening.map((b, j) => (
            <Bubble key={`o${j}`} tail={j === run.opening.length - 1}>
              {b}
            </Bubble>
          ))}
          {shown.map((s, i) => {
            const turn = run.turns[s.turn];
            if (s.kind === 'sent') {
              const sum = turnSummary(turn);
              return (
                <div key={i} className="shrink-0 space-y-1">
                  <Bubble me>{turn.text}</Bubble>
                  <p className={`animate-pop-in pr-2 text-right text-xs font-medium ${sum.up ? 'text-good' : 'text-bad'}`}>
                    {sum.skill ? `${t(`labels.${sum.skill}`)} · ` : ''}
                    {t('landing.run.trust_short', { from: sum.from, to: sum.to })}
                  </p>
                </div>
              );
            }
            if (s.kind === 'read') {
              return (
                <p key={i} className="im-meta shrink-0 pr-2 text-right">
                  {t('chat.read_at', { time: '9:42 PM' })}
                </p>
              );
            }
            if (s.kind === 'typing') return i === step ? <TypingDots key={i} label="" /> : null;
            if (s.kind === 'friend' && turn.friend) {
              return turn.friend.bubbles.map((b, j) => (
                <Bubble key={`${i}-${j}`} tail={j === turn.friend!.bubbles.length - 1}>
                  {b}
                </Bubble>
              ));
            }
            return null;
          })}
          </div>
        </div>
      </PhoneFrame>
      {/* The composer, with "you" typing the next recorded message */}
      <div className="absolute inset-x-5 bottom-3 flex items-center gap-2">
        <span className="im-icon-btn shrink-0 !text-[rgb(var(--im-meta))]">
          <Icon name="plus" className="h-4 w-4" />
        </span>
        <span className="im flex min-w-0 flex-1 items-center gap-2 rounded-full border border-[rgb(var(--im-meta)/0.4)] bg-[rgb(var(--im-bg))] py-1 pl-3 pr-1 !text-[14px]">
          <span className="min-w-0 flex-1 truncate text-ink">
            {current?.kind === 'type' ? run.turns[current.turn].text.slice(0, typed) : <span className="text-[rgb(var(--im-meta))]">{t('chat.placeholder', { name: 'Maya' })}</span>}
            {current?.kind === 'type' && <span className="ml-px inline-block h-4 w-px translate-y-0.5 animate-caret bg-[rgb(var(--im-sent))]" />}
          </span>
          <span className={`grid h-6 w-6 shrink-0 place-items-center rounded-full ${current?.kind === 'type' ? 'bg-[rgb(var(--im-sent))] text-white' : 'bg-[rgb(var(--im-recv))] text-[rgb(var(--im-meta))]'}`}>
            <Icon name="up" className="h-3.5 w-3.5" />
          </span>
        </span>
      </div>
    </div>
  );
}
