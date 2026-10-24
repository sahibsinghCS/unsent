/**
 * "If this is real right now": fixed, reviewed steps and crisis lines. No AI. Works offline: if the
 * API can't be reached, it shows the copy bundled into the app at build time.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import type { CrisisLine, RealMode as RealModeData } from '../api/models';
import { Icon } from '../components/Icon';
import { usePrefs } from '../i18n';
import { COUNTRIES, loadRealMode, offlineRealMode } from '../lib/realmode';

const telHref = (n: string) => `tel:${n.replace(/[^\d+]/g, '')}`;
const smsHref = (n: string) => `sms:${n.replace(/[^\d+]/g, '')}`;

function LineCard({ line, primary }: { line: CrisisLine; primary: boolean }) {
  const { t } = usePrefs();
  return (
    <li className={`card p-4 ${primary ? 'border-warm/50' : ''}`}>
      <p className="font-bold">{line.name}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {line.call && (
          <a href={telHref(line.call)} className={primary ? 'btn-warm py-3 text-base' : 'btn-ghost'}>
            <Icon name="phone" className="h-4 w-4" />
            {t('real.call', { number: line.call })}
          </a>
        )}
        {line.text && (
          <a href={smsHref(line.text)} className={primary ? 'btn-ghost border-warm/50 py-3 text-base' : 'btn-ghost'}>
            <Icon name="message" className="h-4 w-4" />
            {t('real.text', { number: line.text })}
          </a>
        )}
        {line.url && (
          <a href={line.url} target="_blank" rel="noopener noreferrer" className="btn-ghost">
            <Icon name="globe" className="h-4 w-4" />
            {t('real.visit')}
          </a>
        )}
      </div>
    </li>
  );
}

export function RealMode() {
  const { t, lang, country, setCountry } = usePrefs();
  // Start from the bundled copy so something useful shows instantly, then upgrade from the API.
  const [data, setData] = useState<RealModeData>(() => offlineRealMode(lang, country));
  const [offline, setOffline] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let live = true;
    setLoading(true);
    setData(offlineRealMode(lang, country));
    loadRealMode(lang, country).then((r) => {
      if (!live) return;
      setData(r.data);
      setOffline(r.offline);
      setLoading(false);
    });
    return () => {
      live = false;
    };
  }, [lang, country]);

  const lines = data.crisis.lines;
  const primary = lines.find((l) => l.call) ?? null;

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6" data-testid="realmode">
      <h1 className="text-4xl font-semibold sm:text-5xl">{data.title}</h1>
      <p className="mt-3 text-lg leading-relaxed text-muted">{data.intro}</p>

      <fieldset className="mt-6">
        <legend className="small-label mb-2">{t('real.country')}</legend>
        <div className="flex flex-wrap gap-2">
          {COUNTRIES.map((code) => (
            <button
              key={code}
              type="button"
              aria-pressed={country === code}
              onClick={() => setCountry(code)}
              className={`chip px-3 py-1.5 text-sm ${country === code ? 'border-brand bg-brand text-brand-ink' : 'border-line bg-surface hover:bg-sunken'}`}
            >
              {t(`real.countries.${code}`)}
            </button>
          ))}
        </div>
      </fieldset>

      {primary && (
        <div className="mt-6 grid gap-3 sm:grid-cols-2" data-testid="primary-line">
          {primary.call && (
            <a href={telHref(primary.call)} className="btn-warm rounded-2xl py-5 text-lg">
              <Icon name="phone" className="h-5 w-5" />
              {t('real.call', { number: primary.call })}
            </a>
          )}
          {primary.text && (
            <a href={smsHref(primary.text)} className="btn-ghost rounded-2xl border-2 border-warm/50 py-5 text-lg">
              <Icon name="message" className="h-5 w-5" />
              {t('real.text', { number: primary.text })}
            </a>
          )}
        </div>
      )}
      {data.crisis.emergency && (
        <a
          href={/^\d+$/.test(data.crisis.emergency) ? telHref(data.crisis.emergency) : undefined}
          className="mt-3 flex items-center justify-center gap-2 rounded-2xl bg-bad-soft p-4 text-center font-bold text-bad"
          data-testid="emergency"
        >
          <Icon name="phone" className="h-5 w-5" />
          {t('real.emergency', { number: data.crisis.emergency })}
        </a>
      )}

      {offline && !loading && (
        <p role="status" className="mt-4 rounded-xl bg-sunken p-3 text-sm text-muted" data-testid="offline-note">
          {t('real.offline')}
        </p>
      )}

      <ol className="mt-10 space-y-3">
        {data.steps.map((step, i) => (
          <li key={step.id} className="card flex gap-4 p-4">
            <span className="mono-num grid h-9 w-9 shrink-0 place-items-center rounded-full bg-brand text-sm font-bold text-brand-ink">{i + 1}</span>
            <div>
              <p className="font-bold">{step.title}</p>
              <p className="mt-1 leading-relaxed text-muted">{step.body}</p>
            </div>
          </li>
        ))}
      </ol>

      {lines.length > 0 && (
        <ul className="mt-8 space-y-3">
          {lines.map((line) => (
            <LineCard key={line.name} line={line} primary={line === primary} />
          ))}
        </ul>
      )}

      <div className="mt-8 rounded-2xl bg-brand-soft/60 p-5">
        <p className="small-label">{t('real.for_you')}</p>
        <p className="mt-1 leading-relaxed">{data.for_you}</p>
      </div>
      <p className="mt-6 flex items-start gap-2 text-sm text-muted">
        <Icon name="lock" className="mt-0.5 h-4 w-4 shrink-0" />
        {t('real.no_ai')} {data.disclaimer}
      </p>
      {data.needs_native_review && <p className="mt-2 text-xs text-muted">{t('real.review_note')}</p>}
      <Link to="/practice" className="btn-ghost mt-8">
        {t('real.back')}
      </Link>
    </div>
  );
}
