// Scenario picker: story cards from /api/scenarios. Choosing one opens the content warning first.
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
    <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 md:py-16">
      <h1 className="text-5xl sm:text-6xl">{t('practice.title')}</h1>
      <p className="mt-4 max-w-2xl text-lg text-muted">{t('practice.sub')}</p>

      {expired && (
        <div role="alert" className="card mt-6 flex flex-wrap items-center justify-between gap-3 p-4" data-testid="friend-expired">
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
          {[...(friend ? [friend] : []), ...scenarios].map((s) => (
            <li key={s.id}>
              <button type="button" onClick={() => setChosen(s)} className="card card-lift group flex h-full w-full flex-col p-6 text-left">
                <span className="flex items-center gap-4">
                  <Avatar name={s.persona_name} size="lg" tone />
                  <span className="min-w-0 flex-1">
                    {isCustomId(s.id) && <span className="meta-label block">{t('friends.yours')}</span>}
                    <span className="block font-display text-[1.7rem] font-bold leading-tight tracking-tight">{s.persona_name}</span>
                    <span className="block truncate text-sm text-muted">
                      {t('practice.age', { age: s.persona_age })} · {s.title}
                    </span>
                  </span>
                </span>
                <span className="mt-4 line-clamp-3 flex-1 text-[15px] leading-relaxed">{s.situation}</span>
                <span className="mt-5 flex flex-wrap items-center gap-1.5">
                  <span className="chip border-line text-muted">{s.guardedness === 'guarded' ? t('practice.guarded') : t('practice.open')}</span>
                  <span className="chip border-line font-mono uppercase text-muted">{(s.locales ?? ['en']).join(' · ')}</span>
                  {isCustomId(s.id) && (
                    <span className="chip border-line text-muted" data-testid="custom-chip">
                      {t('friends.custom_chip')}
                    </span>
                  )}
                  {!isCustomId(s.id) && !supportsLang(s, lang) && (
                    <span className="chip border-line text-muted" data-testid="lang-only">
                      {t('practice.only_lang', { lang: t('langs.en') })}
                    </span>
                  )}
                </span>
                <span className="mt-6 inline-flex w-fit items-center gap-2 rounded-full border border-line-strong px-4 py-2 text-sm font-semibold transition group-hover:border-brand group-hover:bg-brand group-hover:text-brand-ink">
                  {t('practice.start', { name: s.persona_name })}
                </span>
              </button>
            </li>
          ))}
          <li>
            <Link
              to="/practice/new"
              className="card-lift flex h-full min-h-[16rem] flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-line-strong p-6 text-center hover:border-brand"
              data-testid="add-friend"
            >
              <span className="grid h-14 w-14 place-items-center rounded-full border border-line-strong text-brand-deep" aria-hidden="true">
                <Icon name="plus" className="h-6 w-6" />
              </span>
              <span className="font-display text-2xl font-bold tracking-tight">{t('friends.add_card')}</span>
              <span className="max-w-[16rem] text-sm text-muted">{t('friends.add_card_sub')}</span>
            </Link>
          </li>
        </ul>
      )}
      <ContentWarningModal scenario={chosen} busy={starting} onCancel={() => setChosen(null)} onStart={start} />
    </div>
  );
}
