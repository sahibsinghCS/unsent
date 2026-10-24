// Landing page: an editorial hero with a live chat demo, the CDC stat, "how it works" in three
// steps, and a calm safety strip. Short on purpose: the demo shows the product in 3 seconds.
import { Link } from 'react-router-dom';
import { Icon, type IconName } from '../components/Icon';
import { LiveDemo } from '../components/LiveDemo';
import { Call988 } from '../components/Safety';
import { usePrefs } from '../i18n';

function Step({ n, icon, title, body }: { n: number; icon: IconName; title: string; body: string }) {
  return (
    <li className="card group relative overflow-hidden p-6 transition hover:-translate-y-1 hover:shadow-lift">
      <span className="numeral pointer-events-none absolute -right-2 -top-6 text-[7rem] leading-none text-brand/10" aria-hidden="true">
        {n}
      </span>
      <span className="grid h-11 w-11 place-items-center rounded-2xl bg-brand text-brand-ink shadow-glow">
        <Icon name={icon} className="h-5 w-5" />
      </span>
      <h3 className="mt-5 text-lg font-bold">{title}</h3>
      <p className="mt-2 leading-relaxed text-muted">{body}</p>
    </li>
  );
}

export function Landing() {
  const { t, tl } = usePrefs();
  const steps = tl('landing.steps_body');
  const stepTitles = tl('landing.steps_title');
  const icons: IconName[] = ['message', 'eye', 'sparkle'];
  return (
    <div className="overflow-x-hidden">
      <section className="mx-auto grid max-w-6xl items-center gap-14 px-4 pb-20 pt-10 sm:px-6 md:grid-cols-[1.1fr_1fr] md:pt-16">
        <div className="animate-rise">
          <p className="chip mb-6 border-brand/25 bg-brand-soft/70 text-ink">
            <span className="h-2 w-2 animate-pulse rounded-full bg-warm" aria-hidden="true" />
            {t('landing.eyebrow')}
          </p>
          <h1 className="text-[2.6rem] font-semibold leading-[1.02] sm:text-6xl lg:text-7xl">
            {t('landing.title_a')} <em className="ink-gradient pr-1 font-semibold">{t('landing.title_em')}</em>
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted">{t('landing.sub')}</p>
          <div className="mt-9 flex flex-wrap items-center gap-3">
            <Link to="/practice" className="btn-primary px-7 py-3.5 text-base" data-testid="start-practicing">
              {t('landing.start')}
              <Icon name="arrow" className="h-4 w-4" />
            </Link>
            <Link to="/how" className="btn-ghost px-6 py-3.5 text-base">
              {t('landing.how')}
            </Link>
          </div>
        </div>
        <LiveDemo />
      </section>

      <section className="relative overflow-hidden bg-night text-night-ink">
        <div className="absolute inset-0 bg-[radial-gradient(40rem_20rem_at_80%_0%,rgb(var(--brand)/0.35),transparent_70%)]" aria-hidden="true" />
        <div className="relative mx-auto flex max-w-6xl flex-col gap-5 px-4 py-14 sm:px-6 md:flex-row md:items-center md:gap-12">
          <p className="numeral shrink-0 text-7xl italic md:text-8xl">
            1&nbsp;<span className="text-[rgb(var(--glow))]">in</span>&nbsp;5
          </p>
          <div>
            <p className="font-display text-2xl leading-snug sm:text-3xl">{t('landing.stat')}</p>
            <p className="mt-2 text-xl leading-snug text-night-ink sm:text-2xl">{t('landing.stat_kicker')}</p>
            <p className="mt-4 text-sm text-night-muted">{t('landing.stat_source')}</p>
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <p className="eyebrow">{t('landing.steps_eyebrow')}</p>
        <h2 className="mt-2 max-w-2xl text-4xl font-semibold sm:text-5xl">{t('landing.features_title')}</h2>
        <ol className="mt-10 grid gap-5 md:grid-cols-3">
          {stepTitles.map((title, i) => (
            <Step key={i} n={i + 1} icon={icons[i]} title={title} body={steps[i]} />
          ))}
        </ol>
        <div className="mt-10 flex flex-wrap items-center gap-4">
          <Link to="/practice" className="btn-primary">
            {t('landing.start')}
          </Link>
          <Link to="/how" className="font-semibold text-brand underline-offset-4 hover:underline">
            {t('landing.how')} →
          </Link>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-4 pb-8 sm:px-6">
        <div className="card flex flex-col gap-5 border-warm/30 p-6 sm:p-8 md:flex-row md:items-center md:justify-between">
          <div className="flex gap-4">
            <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-warm-soft text-warm">
              <Icon name="shield" className="h-6 w-6" />
            </span>
            <div>
              <h2 className="text-2xl font-semibold">{t('landing.safety_title')}</h2>
              <p className="mt-1 max-w-xl leading-relaxed text-muted">{t('landing.safety_body')}</p>
            </div>
          </div>
          <div className="w-full shrink-0 md:w-72">
            <Call988 compact />
          </div>
        </div>
      </section>
    </div>
  );
}
