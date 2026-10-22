// Scenario picker: cards from /api/scenarios. Choosing one opens the content warning first.
import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import type { ScenarioSummary } from '../api/models';
import { Icon } from '../components/Icon';
import { ContentWarningModal } from '../components/Safety';
import { ErrorBox, Spinner } from '../components/Status';
import { usePrefs } from '../i18n';
import { apiCountry } from '../lib/realmode';

const GRADIENTS = ['from-[#f4a18f] to-[#0f766e]', 'from-[#8b5cf6] to-[#0ea5e9]', 'from-[#f59e0b] to-[#d65c48]', 'from-[#14b8a6] to-[#6366f1]', 'from-[#db2777] to-[#f59e0b]'];

export function Practice() {
  const { t, lang, country } = usePrefs();
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState<ScenarioSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [chosen, setChosen] = useState<ScenarioSummary | null>(null);
  const [starting, setStarting] = useState(false);

  const load = useCallback(() => {
    setError(null);
    api.scenarios().then(setScenarios, (e) => setError(e.message));
  }, []);
  useEffect(load, [load]);

  async function start() {
    if (!chosen) return;
    setStarting(true);
    try {
      const session = await api.startSession(chosen.id, lang, apiCountry(country));
      navigate(`/chat/${session.session_id}`);
    } catch (e) {
      setError((e as Error).message);
      setChosen(null);
    } finally {
      setStarting(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <h1 className="text-3xl font-bold sm:text-4xl">{t('practice.title')}</h1>
      <p className="mt-2 max-w-2xl text-muted">{t('practice.sub')}</p>

      {error && <ErrorBox message={`${t('practice.error')} ${error}`} onRetry={load} />}
      {!error && !scenarios && <Spinner />}
      {scenarios && (
        <ul className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3" data-testid="scenarios">
          {scenarios.map((s, i) => (
            <li key={s.id}>
              <button
                type="button"
                onClick={() => setChosen(s)}
                className="card group flex h-full w-full flex-col p-5 text-left transition hover:-translate-y-0.5 hover:border-brand/50 hover:shadow-phone"
              >
                <div className="flex items-center gap-3">
                  <div className={`grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br ${GRADIENTS[i % GRADIENTS.length]} text-lg font-bold text-white`} aria-hidden="true">
                    {s.persona_name.slice(0, 1)}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-lg font-bold leading-tight">{s.persona_name}</p>
                    <p className="text-sm text-muted">{t('practice.age', { age: s.persona_age })}</p>
                  </div>
                  <span className={`chip ${s.guardedness === 'guarded' ? 'border-warm/40 bg-warm-soft text-ink' : 'border-good/30 bg-good-soft text-ink'}`}>
                    {s.guardedness === 'guarded' ? t('practice.guarded') : t('practice.open')}
                  </span>
                </div>
                <p className="mt-4 font-semibold">{s.title}</p>
                <p className="mt-1.5 flex-1 text-sm leading-relaxed text-muted">{s.situation}</p>
                <span className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-brand">
                  {t('practice.start', { name: s.persona_name })}
                  <Icon name="arrow" className="h-4 w-4 transition group-hover:translate-x-0.5" />
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      <ContentWarningModal scenario={chosen} busy={starting} onCancel={() => setChosen(null)} onStart={start} />
    </div>
  );
}
