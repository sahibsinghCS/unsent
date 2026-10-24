/**
 * "Add your own friend": the user describes a friend (name, age, open/guarded, personality,
 * situation, sample texts) and practices with them. POST /api/friends creates it; our engine still
 * decides what the friend reveals and the Guardian still checks every message. Values live in React
 * state only (useFriends); nothing is written to browser storage.
 */
import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ApiError, api } from '../api/client';
import { Icon } from '../components/Icon';
import { Modal } from '../components/Modal';
import { Bubble, MessagesHeader, PhoneFrame } from '../components/Phone';
import { Call988, ContentWarningModal } from '../components/Safety';
import { usePrefs } from '../i18n';
import { LIMITS, draftProblems, useFriends, type CustomFriend, type FriendDraft } from '../lib/friends';
import { apiCountry } from '../lib/realmode';

type FieldErrors = Partial<Record<string, string>>;

function Counter({ n, max, id }: { n: number; max: number; id: string }) {
  return (
    <span id={id} className={`mono-num text-[11px] ${n > max - 20 ? 'text-warm' : 'text-muted'}`}>
      {n}/{max}
    </span>
  );
}

function FieldError({ id, message }: { id: string; message?: string }) {
  if (!message) return null;
  return (
    <p id={id} role="alert" className="mt-1.5 flex items-center gap-1.5 text-sm font-medium text-bad">
      <Icon name="x" className="h-3.5 w-3.5" />
      {message}
    </p>
  );
}

const inputCls =
  'w-full rounded-2xl border border-line bg-surface px-4 py-2.5 text-[15px] placeholder:text-muted focus:border-brand aria-[invalid=true]:border-bad';

export function NewFriend() {
  const { t, lang, country } = usePrefs();
  const navigate = useNavigate();
  const { draft, setDraft, setFriend } = useFriends();
  const [errors, setErrors] = useState<FieldErrors>({});
  const [banner, setBanner] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState<CustomFriend | null>(null);
  const [showRealHelp, setShowRealHelp] = useState(false);
  const [starting, setStarting] = useState(false);

  const update = (patch: Partial<FriendDraft>) => setDraft({ ...draft, ...patch });
  const problems = draftProblems(draft);
  const texts = draft.sample_texts;
  const previewTexts = texts.map((s) => s.trim()).filter(Boolean);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (Object.keys(problems).length) return;
    setBusy(true);
    setErrors({});
    setBanner(null);
    try {
      const { friend, notice } = await api.createFriend({
        name: draft.name.trim(),
        age: draft.age,
        guardedness: draft.guardedness,
        personality: draft.personality.trim(),
        situation: draft.situation.trim(),
        sample_texts: previewTexts,
        locale: lang,
      });
      setFriend(friend);
      setCreated(friend);
      setShowRealHelp(notice === 'real_help');
    } catch (e) {
      const error = e as ApiError;
      const detail = error.detail as { field?: string; message?: string } | undefined;
      if (error.status === 422 && detail?.field) setErrors({ [detail.field]: detail.message || error.message });
      else setBanner(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function start() {
    if (!created) return;
    setStarting(true);
    try {
      // A custom friend is practiced only in the language it was written in (friend.locales).
      const session = await api.startSession(created.id, created.locales?.[0] ?? lang, apiCountry(country));
      navigate(`/chat/${session.session_id}`);
    } catch (e) {
      const error = e as ApiError;
      setCreated(null);
      setBanner(error.status === 404 ? t('friends.expired') : error.message);
    } finally {
      setStarting(false);
    }
  }

  const describedBy = (field: string, extra: string) => [extra, errors[field] ? `err-${field}` : ''].filter(Boolean).join(' ');

  return (
    <div className="mx-auto grid max-w-6xl gap-8 px-4 py-10 sm:px-6 lg:grid-cols-[1.15fr_0.85fr] lg:items-start">
      <div>
        <Link to="/practice" className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand">
          <Icon name="back" className="h-4 w-4" />
          {t('friends.back')}
        </Link>
        <p className="eyebrow mt-5">{t('friends.eyebrow')}</p>
        <h1 className="mt-2 text-4xl font-semibold sm:text-5xl">{t('friends.title')}</h1>
        <p className="mt-3 max-w-xl text-lg text-muted">{t('friends.sub')}</p>

        <div className="mt-6 space-y-3">
          <p className="flex gap-3 rounded-2xl border border-brand/20 bg-brand-soft/60 p-4 text-sm leading-relaxed" data-testid="friend-privacy">
            <Icon name="lock" className="mt-0.5 h-5 w-5 shrink-0 text-brand" />
            {t('friends.privacy')}
          </p>
          <p className="flex flex-wrap items-start gap-3 rounded-2xl border border-warm/30 bg-warm-soft/60 p-4 text-sm leading-relaxed" data-testid="friend-safety">
            <Icon name="heart" className="mt-0.5 h-5 w-5 shrink-0 text-warm" />
            <span className="min-w-0 flex-1">
              {t('friends.safety')}{' '}
              <Link to="/real" className="font-semibold text-ink underline underline-offset-4">
                {t('app.footer_links.real')} →
              </Link>
            </span>
          </p>
        </div>

        {banner && (
          <div role="alert" className="mt-5 rounded-2xl bg-bad-soft p-4 text-sm font-medium text-bad" data-testid="friend-banner">
            {banner}
            {banner === t('friends.expired') && (
              <button type="button" className="btn-ghost mt-3 w-full sm:w-auto" onClick={() => setBanner(null)}>
                {t('friends.create_again')}
              </button>
            )}
          </div>
        )}

        <form className="card mt-6 space-y-6 p-5 sm:p-6" onSubmit={submit} noValidate data-testid="friend-form">
          <div className="grid gap-5 sm:grid-cols-[1fr_8rem]">
            <div>
              <div className="flex items-baseline justify-between">
                <label htmlFor="f-name" className="font-semibold">
                  {t('friends.name')}
                </label>
                <Counter id="c-name" n={draft.name.length} max={LIMITS.name[1]} />
              </div>
              <input
                id="f-name"
                className={`${inputCls} mt-1.5`}
                value={draft.name}
                maxLength={LIMITS.name[1]}
                onChange={(e) => update({ name: e.target.value })}
                placeholder={t('friends.name_ph')}
                aria-invalid={!!errors.name}
                aria-describedby={describedBy('name', 'c-name')}
                autoComplete="off"
                required
              />
              <FieldError id="err-name" message={errors.name} />
            </div>
            <div>
              <label htmlFor="f-age" className="font-semibold">
                {t('friends.age')}
              </label>
              <select id="f-age" className={`${inputCls} mt-1.5`} value={draft.age} onChange={(e) => update({ age: Number(e.target.value) })}>
                {Array.from({ length: LIMITS.age[1] - LIMITS.age[0] + 1 }, (_, i) => LIMITS.age[0] + i).map((age) => (
                  <option key={age} value={age}>
                    {age}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <fieldset>
            <legend className="font-semibold">{t('friends.style')}</legend>
            <div className="mt-2 grid grid-cols-2 gap-2">
              {(['open', 'guarded'] as const).map((g) => (
                <label
                  key={g}
                  className={`flex cursor-pointer items-center gap-2.5 rounded-2xl border p-3 transition focus-within:ring-2 focus-within:ring-brand ${
                    draft.guardedness === g ? 'border-brand bg-brand-soft' : 'border-line bg-surface hover:border-ink/25'
                  }`}
                >
                  <input type="radio" name="guardedness" value={g} checked={draft.guardedness === g} onChange={() => update({ guardedness: g })} className="sr-only" />
                  <span className={`h-2.5 w-2.5 rounded-full ${g === 'guarded' ? 'bg-warm' : 'bg-good'}`} aria-hidden="true" />
                  <span>
                    <span className="block text-sm font-semibold">{t(`practice.${g}`)}</span>
                    <span className="block text-xs text-muted">{t(`friends.${g}_hint`)}</span>
                  </span>
                </label>
              ))}
            </div>
          </fieldset>

          <div>
            <div className="flex items-baseline justify-between">
              <label htmlFor="f-personality" className="font-semibold">
                {t('friends.personality')}
              </label>
              <Counter id="c-personality" n={draft.personality.length} max={LIMITS.personality} />
            </div>
            <textarea
              id="f-personality"
              rows={2}
              className={`${inputCls} mt-1.5 resize-y`}
              value={draft.personality}
              maxLength={LIMITS.personality}
              onChange={(e) => update({ personality: e.target.value })}
              placeholder={t('friends.personality_ph')}
              aria-invalid={!!errors.personality}
              aria-describedby={describedBy('personality', 'c-personality')}
            />
            <FieldError id="err-personality" message={errors.personality} />
          </div>

          <div>
            <div className="flex items-baseline justify-between">
              <label htmlFor="f-situation" className="font-semibold">
                {t('friends.situation')} <span className="text-warm">*</span>
              </label>
              <Counter id="c-situation" n={draft.situation.length} max={LIMITS.situation[1]} />
            </div>
            <textarea
              id="f-situation"
              rows={3}
              className={`${inputCls} mt-1.5 resize-y`}
              value={draft.situation}
              maxLength={LIMITS.situation[1]}
              onChange={(e) => update({ situation: e.target.value })}
              placeholder={t('friends.situation_ph')}
              aria-invalid={!!errors.situation}
              aria-describedby={describedBy('situation', 'c-situation h-situation')}
              required
            />
            <p id="h-situation" className="mt-1 text-xs text-muted">
              {t('friends.situation_hint')}
            </p>
            <FieldError id="err-situation" message={errors.situation} />
          </div>

          <fieldset>
            <legend className="font-semibold">{t('friends.texts')}</legend>
            <p className="text-xs text-muted">{t('friends.texts_hint')}</p>
            <ol className="mt-2 space-y-2">
              {texts.map((text, i) => (
                <li key={i}>
                  <div className="flex items-center gap-2">
                    <label htmlFor={`f-text-${i}`} className="sr-only">
                      {t('friends.text_n', { n: i + 1 })}
                    </label>
                    <input
                      id={`f-text-${i}`}
                      className={inputCls}
                      value={text}
                      maxLength={LIMITS.sampleText}
                      onChange={(e) => update({ sample_texts: texts.map((v, j) => (j === i ? e.target.value : v)) })}
                      placeholder={t('friends.text_ph')}
                      aria-invalid={!!errors[`sample_texts.${i}`]}
                      aria-describedby={describedBy(`sample_texts.${i}`, `c-text-${i}`)}
                      data-testid="friend-text"
                    />
                    <Counter id={`c-text-${i}`} n={text.length} max={LIMITS.sampleText} />
                    {texts.length > 1 && (
                      <button
                        type="button"
                        className="grid h-8 w-8 shrink-0 place-items-center rounded-full text-muted hover:bg-sunken hover:text-ink"
                        onClick={() => update({ sample_texts: texts.filter((_, j) => j !== i) })}
                        aria-label={t('friends.remove_text', { n: i + 1 })}
                      >
                        <Icon name="x" className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                  <FieldError id={`err-sample_texts.${i}`} message={errors[`sample_texts.${i}`]} />
                </li>
              ))}
            </ol>
            {texts.length < LIMITS.sampleCount && (
              <button type="button" className="btn-ghost mt-2 px-4 py-2 text-xs" onClick={() => update({ sample_texts: [...texts, ''] })}>
                <Icon name="plus" className="h-3.5 w-3.5" />
                {t('friends.add_text')}
              </button>
            )}
          </fieldset>

          <button type="submit" className="btn-primary w-full py-3 text-base sm:w-auto" disabled={busy || Object.keys(problems).length > 0} data-testid="friend-create">
            {busy ? t('friends.creating') : t('friends.create')}
            <Icon name="arrow" className="h-4 w-4" />
          </button>
        </form>
      </div>

      {/* Live preview of their voice */}
      <aside className="lg:sticky lg:top-20" aria-label={t('friends.preview')}>
        <p className="eyebrow mb-3">{t('friends.preview')}</p>
        <PhoneFrame header={<MessagesHeader name={draft.name.trim() || '?'} sub={t('practice.age', { age: draft.age })} />} className="mx-auto h-[28rem] max-w-[22rem]">
          <div className="im-screen flex h-full flex-col justify-end gap-0.5 px-2.5 py-3" data-testid="friend-preview">
            {previewTexts.length === 0 ? (
              <p className="im-meta m-auto max-w-[14rem] text-center">{t('friends.preview_empty')}</p>
            ) : (
              previewTexts.map((text, i) => (
                <Bubble key={i} tail={i === previewTexts.length - 1}>
                  {text}
                </Bubble>
              ))
            )}
          </div>
        </PhoneFrame>
      </aside>

      {/* A real friend may be in trouble: real help comes first, practice can wait */}
      <Modal open={!!created && showRealHelp} title={t('friends.real_title')} dismissible={false} tone="warm" icon={<Icon name="heart" className="mt-1 h-6 w-6 shrink-0 text-warm" />}>
        <div className="space-y-4" data-testid="friend-real-help">
          <p className="leading-relaxed">{t('friends.real_body')}</p>
          <Call988 />
          <div className="flex flex-col gap-2 sm:flex-row sm:justify-between">
            <Link to="/real" className="btn-warm">
              {t('friends.real_open')}
            </Link>
            <button type="button" className="btn-ghost" onClick={() => setShowRealHelp(false)}>
              {t('friends.real_continue')}
            </button>
          </div>
        </div>
      </Modal>
      <ContentWarningModal scenario={created && !showRealHelp ? created : null} busy={starting} onCancel={() => setCreated(null)} onStart={start} />
    </div>
  );
}
