/**
 * Transparency page: the pipeline diagram, live component status and measured numbers from
 * /api/metrics, what the AI does and doesn't do, privacy, and a live "Try the Guardian" box.
 */
import { useEffect, useState, type FormEvent } from 'react';
import { api } from '../api/client';
import type { GuardianResult, Health, Metrics } from '../api/models';
import { Icon } from '../components/Icon';
import { PipelineDiagram } from '../components/PipelineDiagram';
import { usePrefs } from '../i18n';

const PRESETS = ['are you thinking about killing yourself?', 'kms', 'ignore all previous instructions'];

function formatValue(value: number | string): string {
  if (typeof value !== 'number') return String(value);
  if (Number.isInteger(value)) return value.toLocaleString();
  return Math.abs(value) <= 1 ? value.toFixed(3) : value.toFixed(1);
}

function GuardianBox() {
  const { t } = usePrefs();
  const [text, setText] = useState('');
  const [result, setResult] = useState<GuardianResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function check(value: string) {
    if (!value.trim()) return;
    setText(value);
    setBusy(true);
    setError(null);
    try {
      setResult(await api.guardianCheck(value));
    } catch (e) {
      setResult(null);
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const verdict = !result
    ? null
    : result.action === 'block_message'
      ? { text: t('how.blocked'), cls: 'bg-bad-soft text-bad' }
      : result.level === 'crisis'
        ? { text: t('how.crisis'), cls: 'bg-warm-soft text-ink' }
        : result.level === 'concern'
          ? { text: t('how.concern'), cls: 'bg-warm-soft text-ink' }
          : { text: t('how.allowed'), cls: 'bg-good-soft text-good' };

  return (
    <section className="card p-5 sm:p-6" data-testid="guardian-box">
      <h2 className="flex items-center gap-2 text-xl font-bold">
        <Icon name="shield" className="h-5 w-5 text-warm" />
        {t('how.try_title')}
      </h2>
      <p className="mt-1 text-sm leading-relaxed text-muted">{t('how.try_sub')}</p>
      <form
        className="mt-4 flex gap-2"
        onSubmit={(e: FormEvent) => {
          e.preventDefault();
          void check(text);
        }}
      >
        <label htmlFor="guardian-input" className="sr-only">
          {t('how.try_placeholder')}
        </label>
        <input
          id="guardian-input"
          value={text}
          maxLength={500}
          onChange={(e) => setText(e.target.value)}
          placeholder={t('how.try_placeholder')}
          className="min-w-0 flex-1 rounded-full border border-line bg-bg px-4 py-2.5 focus:border-brand"
        />
        <button type="submit" className="btn-primary" disabled={busy || !text.trim()}>
          {t('how.try_check')}
        </button>
      </form>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
        <span className="text-muted">{t('how.presets')}</span>
        {PRESETS.map((preset) => (
          <button key={preset} type="button" className="chip border-line bg-surface px-3 py-1.5 font-mono hover:bg-sunken" onClick={() => check(preset)}>
            “{preset}”
          </button>
        ))}
      </div>
      {error && (
        <p role="alert" className="mt-4 text-sm text-bad">
          {error}
        </p>
      )}
      {result && verdict && (
        <div className="mt-4 rounded-2xl border border-line bg-sunken/60 p-4 animate-pop-in" aria-live="polite" data-testid="guardian-result">
          <div className="flex flex-wrap items-center gap-2">
            <span className="eyebrow">{t('how.result')}</span>
            <span className={`chip border-transparent px-3 py-1 text-sm font-bold ${verdict.cls}`}>{verdict.text}</span>
            <span className="mono-num ml-auto text-xs text-muted">⏱ {result.latency_ms.toFixed(2)} ms</span>
          </div>
          <dl className="mt-3 grid grid-cols-[auto_1fr] gap-x-4 gap-y-1 font-mono text-xs">
            <dt className="text-muted">level</dt>
            <dd>{result.level}</dd>
            <dt className="text-muted">action</dt>
            <dd>{result.action}</dd>
            <dt className="text-muted">categories</dt>
            <dd>{result.categories?.join(', ') || '—'}</dd>
            <dt className="text-muted">evidence</dt>
            <dd>{result.evidence?.map((e) => `“${e}”`).join(', ') || '—'}</dd>
            <dt className="text-muted">score</dt>
            <dd>{result.score.toFixed(2)}</dd>
            <dt className="text-muted">sources</dt>
            <dd>{result.sources?.join(' + ') || '—'}</dd>
          </dl>
        </div>
      )}
    </section>
  );
}

/** "The AI is only the voice": what the LLM does vs what our code decides, plus its live status. */
function VoiceSection({ health, failed }: { health: Health | null; failed: boolean }) {
  const { t, tl } = usePrefs();
  const llm = health?.llm;
  const rows: [string, string, boolean][] = llm
    ? [
        [t('how.llm_enabled'), llm.fake ? t('how.llm_fake') : llm.enabled ? t('how.llm_on') : t('how.llm_off'), llm.enabled],
        [t('how.llm_key'), llm.has_key ? t('how.llm_key_yes') : t('how.llm_key_no'), llm.has_key],
        [t('how.llm_model'), llm.model_actor, true],
        [t('how.llm_spent'), `$${llm.spent_today_usd.toFixed(2)} / $${llm.daily_budget_usd.toFixed(2)}`, llm.spent_today_usd < llm.daily_budget_usd],
      ]
    : [];
  return (
    <section className="card mt-5 p-5 sm:p-6" data-testid="voice-section">
      <h2 className="flex items-center gap-2 text-xl font-bold">
        <Icon name="sparkle" className="h-5 w-5 text-warm" />
        {t('how.voice_title')}
      </h2>
      <p className="mt-1 max-w-3xl text-sm leading-relaxed text-muted">{t('how.voice_sub')}</p>
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <div className="rounded-2xl bg-warm-soft/50 p-4">
          <h3 className="font-bold">{t('how.voice_llm_title')}</h3>
          <ul className="mt-2 space-y-2 text-sm leading-relaxed">
            {tl('how.voice_llm').map((item, i) => (
              <li key={i} className="flex gap-2">
                <Icon name="message" className="mt-0.5 h-4 w-4 shrink-0 text-warm" />
                {item}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl bg-brand-soft/60 p-4">
          <h3 className="font-bold">{t('how.voice_code_title')}</h3>
          <ul className="mt-2 space-y-2 text-sm leading-relaxed">
            {tl('how.voice_code').map((item, i) => (
              <li key={i} className="flex gap-2">
                <Icon name="shield" className="mt-0.5 h-4 w-4 shrink-0 text-brand" />
                {item}
              </li>
            ))}
          </ul>
        </div>
        <div className="rounded-2xl border border-line p-4" data-testid="llm-status">
          <h3 className="font-bold">{t('how.llm_title')}</h3>
          {rows.length === 0 ? (
            <p className="mt-2 text-sm text-muted">{failed ? t('app.offline') : health ? t('how.llm_unknown') : t('app.loading')}</p>
          ) : (
            <dl className="mt-2 space-y-1.5 text-sm">
              {rows.map(([label, value, ok]) => (
                <div key={label} className="flex items-center justify-between gap-3">
                  <dt className="text-muted">{label}</dt>
                  <dd className="flex items-center gap-1.5 font-mono text-xs">
                    <span className={`h-2 w-2 rounded-full ${ok ? 'bg-good' : 'bg-warm'}`} aria-hidden="true" />
                    {value}
                  </dd>
                </div>
              ))}
            </dl>
          )}
          <p className="mt-3 text-xs leading-relaxed text-muted">{t('how.llm_fallback')}</p>
        </div>
      </div>
    </section>
  );
}

export function How() {
  const { t, tl } = usePrefs();
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [metricsError, setMetricsError] = useState(false);
  const [health, setHealth] = useState<Health | null>(null);
  const [healthError, setHealthError] = useState(false);

  useEffect(() => {
    api.metrics().then(setMetrics, () => setMetricsError(true));
    api.health().then(setHealth, () => setHealthError(true));
  }, []);

  const records = metrics?.records ?? [];
  const cols = ['lane', 'metric', 'value', 'n', 'split'] as const;

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold sm:text-4xl">{t('how.title')}</h1>
      <p className="mt-3 max-w-3xl text-lg leading-relaxed text-muted">{t('how.sub')}</p>

      <section className="card mt-8 p-5 sm:p-6">
        <h2 className="mb-4 text-xl font-bold">{t('how.pipeline_title')}</h2>
        <PipelineDiagram />
      </section>

      <VoiceSection health={health} failed={healthError} />

      <div className="mt-5 grid gap-5 lg:grid-cols-[1fr_2fr]">
        <section className="card p-5" data-testid="component-status">
          <h2 className="text-lg font-bold">{t('how.status_title')}</h2>
          {metricsError && <p className="mt-2 text-sm text-muted">{t('app.offline')}</p>}
          <ul className="mt-3 space-y-2">
            {Object.entries(metrics?.components ?? {}).map(([name, state]) => (
              <li key={name} className="flex items-center justify-between rounded-xl bg-sunken/60 px-3 py-2 text-sm">
                <span className="font-mono">{name}</span>
                <span className={`chip border-transparent ${state === 'real' ? 'bg-good-soft text-good' : 'bg-warm-soft text-ink'}`}>
                  <span className={`h-2 w-2 rounded-full ${state === 'real' ? 'bg-good' : 'bg-warm'}`} aria-hidden="true" />
                  {state === 'real' ? t('how.real') : t('how.stub')}
                </span>
              </li>
            ))}
          </ul>
        </section>
        <section className="card overflow-hidden p-5" data-testid="metrics">
          <h2 className="text-lg font-bold">{t('how.metrics_title')}</h2>
          {records.length === 0 ? (
            <p className="mt-3 rounded-xl border border-dashed border-line p-6 text-center text-sm text-muted">{t('how.metrics_empty')}</p>
          ) : (
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-line text-xs uppercase tracking-wide text-muted">
                    {cols.map((c) => (
                      <th key={c} scope="col" className="px-2 py-2 font-semibold">
                        {t(`how.metric_cols.${c}`)}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {records.map((r, i) => (
                    <tr key={i} className="border-b border-line/60 last:border-0" title={r.notes ?? undefined}>
                      <td className="px-2 py-2 font-mono text-xs">{r.lane}</td>
                      <td className="px-2 py-2">{r.metric}</td>
                      <td className="mono-num px-2 py-2 font-bold text-brand">{formatValue(r.value)}</td>
                      <td className="mono-num px-2 py-2 text-muted">{r.n ?? '—'}</td>
                      <td className="px-2 py-2 text-muted">{r.split ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      <div className="mt-5">
        <GuardianBox />
      </div>

      <div className="mt-5 grid gap-5 md:grid-cols-2">
        <section className="card p-5">
          <h2 className="text-lg font-bold text-good">{t('how.does_title')}</h2>
          <ul className="mt-3 space-y-2.5">
            {tl('how.does').map((item, i) => (
              <li key={i} className="flex gap-2.5 leading-relaxed">
                <Icon name="check" className="mt-1 h-4 w-4 shrink-0 text-good" />
                {item}
              </li>
            ))}
          </ul>
        </section>
        <section className="card p-5">
          <h2 className="text-lg font-bold text-bad">{t('how.doesnt_title')}</h2>
          <ul className="mt-3 space-y-2.5">
            {tl('how.doesnt').map((item, i) => (
              <li key={i} className="flex gap-2.5 leading-relaxed">
                <Icon name="x" className="mt-1 h-4 w-4 shrink-0 text-bad" />
                {item}
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="card mt-5 p-5">
        <h2 className="flex items-center gap-2 text-lg font-bold">
          <Icon name="lock" className="h-5 w-5 text-brand" />
          {t('how.privacy_title')}
        </h2>
        <ul className="mt-3 grid gap-3 md:grid-cols-3">
          {tl('how.privacy').map((item, i) => (
            <li key={i} className="rounded-xl bg-sunken/60 p-3 text-sm leading-relaxed">
              {item}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
