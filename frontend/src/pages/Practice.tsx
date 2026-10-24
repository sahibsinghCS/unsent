// Scenario picker: cards from /api/scenarios. Choosing one opens the content warning first.
import { useCallback, useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ApiError, api } from '../api/client';
import { isCustomId, useFriends } from '../lib/friends';
import { scenarioList, supportsLang } from '../lib/scenarios';
import type { ScenarioSummary } from '../api/models';
import { Avatar } from '../components/Avatar';
import { Icon } from '../components/Icon';
import { ContentWarningModal } from '../components/Safety';
import { ErrorBox, Spinner } from '../components/Status';
import { usePrefs } from '../i18n';
import { apiCountry } from '../lib/realmode';

export function Practice() {
  const { t, lang, country } = usePrefs();
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState<ScenarioSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [chosen, setChosen] = useState<ScenarioSummary | null>(null);
  const [starting, setStarting] = useState(false);
  const [expired, setExpired] = useState(false);
  const { friend, setFriend } = useFriends();

  // Localized title/situation/warning come from the API in the UI language.
  const load = useCallback(() => {
    setError(null);
    scenarioList(lang).then(setScenarios, (e) => setError(e.message));
  }, [lang]);
  useEffect(() => {
    load();
  }, [load]);

  async function start() {
    if (!chosen) return;
    setStarting(true);
    try {
      // Custom friends are practiced only in the language they were written in (locales[0]).
      const locale = isCustomId(chosen.id) ? (chosen.locales?.[0] ?? lang) : lang;
      const session = await api.startSession(chosen.id, locale, apiCountry(country));
      navigate(`/chat/${session.session_id}`);
    } catch (e) {
      // A custom friend the server already deleted (60 min): offer to create it again.
      if ((e as ApiError).status === 404 && isCustomId(chosen.id)) {
        setFriend(null);
        setExpired(true);
      } else setError((e as Error).message);
      setChosen(null);
    } finally {
      setStarting(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <p className="eyebrow">{t('app.nav.practice')}</p>
      <h1 className="mt-2 text-4xl font-semibold sm:text-5xl">{t('practice.title')}</h1>
      <p className="mt-3 max-w-2xl text-lg text-muted">{t('practice.sub')}</p>

      {expired && (
        <div role="alert" className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-warm-soft p-4" data-testid="friend-expired">
          <p className="font-medium">{t('friends.expired')}</p>
          <Link to="/practice/new" className="btn-primary">
            {t('friends.create_again')}
          </Link>
        </div>
      )}
      {error && <ErrorBox message={`${t('practice.error')} ${error}`} onRetry={load} />}
      {!error && !scenarios && <Spinner />}
      {scenarios && (
        <ul className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3" data-testid="scenarios">
          {[...(friend ? [friend] : []), ...scenarios].map((s, i) => (
            <li key={s.id} className="animate-rise" style={{ animationDelay: `${i * 70}ms` }}>
              <button
                type="button"
                onClick={() => setChosen(s)}
                className="card group flex h-full w-full flex-col p-5 text-left transition duration-300 hover:-translate-y-1 hover:border-brand/40 hover:shadow-lift"
              >
                <div className="flex items-center gap-4">
                  <Avatar name={s.persona_name} size="lg" ring />
                  <div className="min-w-0 flex-1">
                    {isCustomId(s.id) && <p className="eyebrow text-brand">{t('friends.yours')}</p>}
                    <p className="font-display text-2xl font-semibold italic leading-tight">{s.persona_name}</p>
                    <p className="truncate text-sm text-muted">
                      {t('practice.age', { age: s.persona_age })} · {s.title}
                    </p>
                  </div>
                </div>
                <p className="mt-4 line-clamp-3 flex-1 text-[15px] leading-relaxed">{s.situation}</p>
                <div className="mt-4 flex flex-wrap items-center gap-1.5">
                  <span className={`chip ${s.guardedness === 'guarded' ? 'border-warm/40 bg-warm-soft text-ink' : 'border-good/30 bg-good-soft text-ink'}`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${s.guardedness === 'guarded' ? 'bg-warm' : 'bg-good'}`} aria-hidden="true" />
                    {s.guardedness === 'guarded' ? t('practice.guarded') : t('practice.open')}
                  </span>
                  <span className="chip border-line bg-surface font-semibold uppercase tracking-wide text-muted">
                    <Icon name="globe" className="h-3 w-3" />
                    {(s.locales ?? ['en']).join(' · ')}
                  </span>
                  {isCustomId(s.id) && (
                    <span className="chip border-brand/30 bg-brand-soft text-ink" data-testid="custom-chip">
                      {t('friends.custom_chip')}
                    </span>
                  )}
                  {!isCustomId(s.id) && !supportsLang(s, lang) && (
                    <span className="chip w-fit border-line bg-sunken text-muted" data-testid="lang-only">
                      {t('practice.only_lang', { lang: t('langs.en') })}
                    </span>
                  )}
                </div>
                <span className="mt-5 inline-flex w-fit items-center gap-2 rounded-full bg-brand-soft px-4 py-2 text-sm font-semibold text-ink transition group-hover:bg-brand group-hover:text-brand-ink">
                  <Icon name="message" className="h-4 w-4" />
                  {t('practice.start', { name: s.persona_name })}
                  <Icon name="arrow" className="h-4 w-4 transition group-hover:translate-x-0.5" />
                </span>
              </button>
            </li>
          ))}
          <li className="animate-rise">
            <Link
              to="/practice/new"
              className="group flex h-full min-h-[16rem] flex-col items-center justify-center gap-3 rounded-[1.5rem] border-2 border-dashed border-brand/40 bg-brand-soft/30 p-6 text-center transition hover:-translate-y-1 hover:border-brand hover:bg-brand-soft/60"
              data-testid="add-friend"
            >
              <span className="grid h-14 w-14 place-items-center rounded-full bg-brand text-brand-ink shadow-glow transition group-hover:scale-105">
                <Icon name="plus" className="h-6 w-6" />
              </span>
              <span className="font-display text-2xl font-semibold italic">{t('friends.add_card')}</span>
              <span className="max-w-[16rem] text-sm text-muted">{t('friends.add_card_sub')}</span>
            </Link>
          </li>
        </ul>
      )}
      <ContentWarningModal scenario={chosen} busy={starting} onCancel={() => setChosen(null)} onStart={start} />
    </div>
  );
}
