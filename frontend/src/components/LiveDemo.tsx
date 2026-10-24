/**
 * The landing page's live demo: a scripted, looping mini-conversation in a phone. A friend's text
 * arrives, "you" type a reply, it sends, the skill detector's chip pops up and the trust meter ticks
 * up, then the friend opens up. Pure React state + CSS; reduced motion shows the final frame.
 */
import { useEffect, useState } from 'react';
import { usePrefs } from '../i18n';
import { LABEL_COLOR } from '../lib/labels';
import { prefersReducedMotion } from '../lib/typingDelay';
import { Bubble, ContactHeader, PhoneFrame, TypingDots } from './Phone';
import { TrustMeter } from './TrustMeter';

// Timeline in ms. Phase n is active from STEPS[n] until STEPS[n+1].
const STEPS = [0, 1300, 2300, 4900, 5600, 7200, 11500];
// 0 friend typing · 1 friend text · 2 you type · 3 sent + chip + trust up · 4 friend typing · 5 friend opens up · 6 loop

export function LiveDemo() {
  const { t } = usePrefs();
  const reply = t('landing.demo.you1');
  const [phase, setPhase] = useState(5);
  const [typed, setTyped] = useState(reply.length);

  useEffect(() => {
    if (prefersReducedMotion()) {
      setPhase(5);
      setTyped(reply.length);
      return undefined;
    }
    let timers: ReturnType<typeof setTimeout>[] = [];
    const run = () => {
      timers.forEach(clearTimeout);
      timers = [];
      setTyped(0);
      STEPS.forEach((at, i) => timers.push(setTimeout(() => (i === STEPS.length - 1 ? run() : setPhase(i)), at)));
      // Type the reply one character at a time during phase 2.
      const span = STEPS[3] - STEPS[2] - 300;
      for (let c = 1; c <= reply.length; c++) timers.push(setTimeout(() => setTyped(c), STEPS[2] + (span * c) / reply.length));
    };
    run();
    return () => timers.forEach(clearTimeout);
  }, [reply]);

  const sent = phase >= 3;
  const trust = sent ? 54 : 30;
  return (
    <div className="relative mx-auto w-full max-w-[20rem]" aria-hidden="true">
      <div className="absolute -inset-10 -z-10 rounded-full bg-gradient-to-tr from-brand/30 via-glow/25 to-transparent blur-3xl" />
      <PhoneFrame header={<ContactHeader name="Maya" sub={phase === 0 || phase === 4 ? t('chat.typing', { name: 'Maya' }) : '16'} />} className="h-[31rem]">
        <div className="flex h-full flex-col justify-end gap-2 bg-surface p-3 pb-16">
          {phase === 0 && <TypingDots label="" />}
          {phase >= 1 && <Bubble>{t('landing.demo.friend1')}</Bubble>}
          {sent && <Bubble me>{reply}</Bubble>}
          {sent && (
            <div className="flex justify-end animate-pop-in">
              <span className="chip border-transparent bg-good-soft text-good">
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: LABEL_COLOR.asked_directly }} />
                {t('labels.asked_directly')} +15
              </span>
            </div>
          )}
          {phase === 4 && <TypingDots label="" />}
          {phase >= 5 && <Bubble>{t('landing.demo.friend2')}</Bubble>}
        </div>
      </PhoneFrame>
      {/* The composer, with "you" typing */}
      <div className="absolute inset-x-6 bottom-3 flex items-center gap-2 rounded-full border border-line bg-bg/95 px-3 py-2 text-[13px] shadow-card">
        <span className="min-w-0 flex-1 truncate text-ink">
          {phase === 2 ? reply.slice(0, typed) : <span className="text-muted">{t('chat.placeholder', { name: 'Maya' })}</span>}
          {phase === 2 && <span className="ml-px inline-block h-4 w-px translate-y-0.5 animate-caret bg-brand" />}
        </span>
        <span className={`grid h-7 w-7 place-items-center rounded-full ${phase === 2 ? 'bg-brand text-brand-ink' : 'bg-line text-muted'}`}>↑</span>
      </div>
      <div className="card absolute -left-4 top-24 hidden p-3 pb-2 sm:-left-20 sm:block">
        <p className="eyebrow text-center">{t('landing.demo.trust')}</p>
        <TrustMeter value={trust} delta={sent ? 24 : undefined} label={t('landing.demo.trust')} size="sm" />
      </div>
    </div>
  );
}
