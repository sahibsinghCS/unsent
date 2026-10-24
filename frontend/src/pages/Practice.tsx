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
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <h1 className="text-4xl sm:text-5xl">{t('practice.title')}</h1>
      <p className="mt-3 max-w-2xl text-lg text-muted">{t('practice.sub')}</p>

      {expired && (
        <div role="alert" className="mt-6 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-line bg-surface p-4" data-testid="friend-expired">
          <p className="font-medium">{t('friends.expired')}</p>
          <Link to="/practice/new" className="btn-primary">
            {t('friends.create_again')}
          </Link>
        </div>
      )}
      {error && <ErrorBox message={`${t('practice.error')} ${error}`} onRetry={load} />}
      {!error && !scenarios && <Spinner />}
      {scenarios && (
        <ul className="card mt-8 divide-y divide-line/70 overflow-hidden" data-testid="scenarios">
          {[...(friend ? [friend] : []), ...scenarios].map((s) => (
            <li key={s.id}>
              <button type="button" onClick={() => setChosen(s)} className="flex w-full items-center gap-3 px-4 py-3.5 text-left transition-colors hover:bg-sunken/60">
                <Avatar name={s.persona_name} size="md" />
                <span className="min-w-0 flex-1">
                  <span className="flex flex-wrap items-baseline gap-x-2">
                    <span className="text-[17px] font-semibold">{s.persona_name}</span>
                    <span className="text-sm text-muted">
                      {t('practice.age', { age: s.persona_age })} · {isCustomId(s.id) ? t('friends.yours') : s.title}
                    </span>
                  </span>
                  <span className="mt-0.5 block truncate text-[15px] text-muted">{s.situation}</span>
                  <span className="mt-1.5 flex flex-wrap items-center gap-1.5">
                    <span className="chip border-line text-muted">{s.guardedness === 'guarded' ? t('practice.guarded') : t('practice.open')}</span>
                    <span className="chip border-line uppercase text-muted">{(s.locales ?? ['en']).join(' · ')}</span>
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
                </span>
                <span className="sr-only">{t('practice.start', { name: s.persona_name })}</span>
                <Icon name="chevron" className="h-5 w-5 shrink-0 rotate-180 text-muted" />
              </button>
            </li>
          ))}
          <li>
            <Link to="/practice/new" className="flex items-center gap-3 px-4 py-3.5 transition-colors hover:bg-sunken/60" data-testid="add-friend">
              <span className="grid h-11 w-11 shrink-0 place-items-center rounded-full border border-dashed border-line text-brand-deep" aria-hidden="true">
                <Icon name="plus" className="h-5 w-5" />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block text-[17px] font-semibold text-brand-deep">{t('friends.add_card')}</span>
                <span className="block text-[15px] text-muted">{t('friends.add_card_sub')}</span>
              </span>
              <Icon name="chevron" className="h-5 w-5 shrink-0 rotate-180 text-muted" />
            </Link>
          </li>
        </ul>
      )}
      <ContentWarningModal scenario={chosen} busy={starting} onCancel={() => setChosen(null)} onStart={start} />
    </div>
  );
}
