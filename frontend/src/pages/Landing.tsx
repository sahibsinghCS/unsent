// Landing page: hero with a phone mockup, three feature cards, the CDC stat, and a link to /how.
import { Link } from 'react-router-dom';
import { Icon, type IconName } from '../components/Icon';
import { Bubble, ContactHeader, PhoneFrame } from '../components/Phone';
import { usePrefs } from '../i18n';
import { LABEL_COLOR } from '../lib/labels';

/** A tiny static trust sparkline for the hero (no chart library needed on the landing page). */
function HeroSparkline() {
  const pts = [30, 36, 24, 46, 61, 78];
  const path = pts.map((v, i) => `${i === 0 ? 'M' : 'L'}${i * 36 + 6},${86 - v * 0.8}`).join(' ');
  return (
    <svg viewBox="0 0 196 92" className="h-16 w-full" aria-hidden="true">
      <defs>
        <linearGradient id="spark" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor="rgb(var(--brand))" stopOpacity="0.35" />
          <stop offset="1" stopColor="rgb(var(--brand))" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`${path} L186,90 L6,90 Z`} fill="url(#spark)" />
      <path d={path} fill="none" stroke="rgb(var(--brand))" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      {pts.map((v, i) => (
        <circle key={i} cx={i * 36 + 6} cy={86 - v * 0.8} r="4.5" fill={i === 2 ? LABEL_COLOR.dismissed : i >= 3 ? LABEL_COLOR.asked_directly : 'rgb(var(--muted))'} stroke="rgb(var(--surface))" strokeWidth="2" />
      ))}
    </svg>
  );
}

function HeroPhone() {
  const { t } = usePrefs();
  return (
    <div className="relative mx-auto w-full max-w-[19rem]">
      <div className="absolute -inset-8 -z-10 rounded-full bg-gradient-to-tr from-brand/25 via-warm/15 to-transparent blur-3xl" aria-hidden="true" />
      <PhoneFrame header={<ContactHeader name="Maya" sub="16" />} className="h-[34rem]">
        <div className="space-y-2 bg-surface p-3 pt-4" aria-hidden="true">
          <Bubble>{t('landing.demo.friend1')}</Bubble>
          <Bubble me>{t('landing.demo.you1')}</Bubble>
          <div className="flex justify-end">
            <span className="chip border-transparent bg-good-soft text-good">
              <span className="h-1.5 w-1.5 rounded-full" style={{ background: LABEL_COLOR.asked_directly }} />
              {t('labels.asked_directly')} +15
            </span>
          </div>
          <Bubble>{t('landing.demo.friend2')}</Bubble>
          <Bubble me>{t('landing.demo.you2')}</Bubble>
        </div>
      </PhoneFrame>
      <div className="card absolute -bottom-8 -left-3 w-44 p-3 sm:-left-16" aria-hidden="true">
        <p className="eyebrow">{t('landing.demo.trust')}</p>
        <p className="mono-num text-2xl font-bold">
          30 <span className="text-muted">→</span> <span className="text-brand">78</span>
        </p>
        <HeroSparkline />
      </div>
    </div>
  );
}

function Feature({ icon, title, body, tint }: { icon: IconName; title: string; body: string; tint: string }) {
  return (
    <div className="card p-6">
      <div className={`mb-4 grid h-11 w-11 place-items-center rounded-2xl ${tint}`}>
        <Icon name={icon} className="h-5 w-5" />
      </div>
      <h3 className="text-lg font-bold">{title}</h3>
      <p className="mt-2 leading-relaxed text-muted">{body}</p>
    </div>
  );
}

export function Landing() {
  const { t } = usePrefs();
  return (
    <div className="overflow-x-hidden">
      <section className="mx-auto grid max-w-6xl items-center gap-14 px-4 pb-20 pt-10 sm:px-6 md:grid-cols-[1.15fr_1fr] md:pt-16">
        <div>
          <p className="chip mb-5 border-brand/30 bg-brand-soft/60 text-ink">
            <Icon name="heart" className="h-3.5 w-3.5 text-warm" />
            {t('landing.eyebrow')}
          </p>
          <h1 className="text-4xl font-extrabold leading-[1.08] sm:text-5xl lg:text-6xl">{t('landing.title')}</h1>
          <p className="mt-5 max-w-xl text-lg leading-relaxed text-muted">{t('landing.sub')}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/practice" className="btn-primary px-7 py-3.5 text-base" data-testid="start-practicing">
              {t('landing.start')}
              <Icon name="arrow" className="h-4 w-4" />
            </Link>
            <Link to="/how" className="btn-ghost px-6 py-3.5 text-base">
              {t('landing.how')}
            </Link>
          </div>
        </div>
        <HeroPhone />
      </section>

      <section className="bg-brand text-brand-ink">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-12 sm:px-6 md:flex-row md:items-center md:gap-10">
          <p className="shrink-0 text-6xl font-extrabold tracking-tight md:text-7xl">1&nbsp;in&nbsp;5</p>
          <div>
            <p className="text-xl font-semibold leading-snug sm:text-2xl">{t('landing.stat')}</p>
            <p className="mt-1 text-xl leading-snug sm:text-2xl">{t('landing.stat_kicker')}</p>
            <p className="mt-3 text-sm">{t('landing.stat_source')}</p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <h2 className="mb-10 max-w-2xl text-3xl font-bold sm:text-4xl">{t('landing.features_title')}</h2>
        <div className="grid gap-5 md:grid-cols-3">
          <Feature icon="message" title={t('landing.features.practice.title')} body={t('landing.features.practice.body')} tint="bg-brand-soft text-brand" />
          <Feature icon="chart" title={t('landing.features.feedback.title')} body={t('landing.features.feedback.body')} tint="bg-warm-soft text-warm" />
          <Feature icon="shield" title={t('landing.features.safety.title')} body={t('landing.features.safety.body')} tint="bg-good-soft text-good" />
        </div>
        <div className="mt-10 flex flex-wrap items-center gap-4">
          <Link to="/practice" className="btn-primary">
            {t('landing.start')}
          </Link>
          <Link to="/how" className="font-semibold text-brand underline-offset-4 hover:underline">
            {t('landing.how')} →
          </Link>
        </div>
      </section>
    </div>
  );
}
