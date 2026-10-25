/**
 * "Practice for a real friend": start the custom-friend form from screenshots of a real chat.
 *   1. explain + consent  2. pick 1-3 images  3. cover names and numbers (required)
 *   4. flatten, downscale and re-encode in the browser (lib/redact)  5. POST /friends/analyze
 *   6. "What we noticed": real help FIRST when urgency is tell_an_adult_now, then warning-sign chips
 *   7. pre-fill the normal form (name left empty) and continue with the usual flow.
 * Privacy: images, data URLs and the draft live only in React state; they're dropped as soon as the
 * analysis returns or the user leaves. Errors always offer "Fill it in myself".
 */
import { useEffect, useId, useRef, useState, type RefObject } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ApiError, api, type AnalyzeResult } from '../api/client';
import { Icon } from '../components/Icon';
import { RedactEditor } from '../components/RedactEditor';
import { Call988 } from '../components/Safety';
import { usePrefs } from '../i18n';
import { EMPTY_DRAFT, LIMITS, useFriends } from '../lib/friends';
import { offlineRealMode } from '../lib/realmode';
import { loadImage, prepareScreenshot, type Box } from '../lib/redact';

const MAX_IMAGES = 3;
type Step = 'explain' | 'pick' | 'redact' | 'analyzing' | 'noticed';

export function RealFriend() {
  const { t, lang } = usePrefs();
  const navigate = useNavigate();
  const { setDraft, setFromRealFriend, setRemovedIdentifying } = useFriends();
  const [step, setStep] = useState<Step>('explain');
  const [consent, setConsent] = useState(false);
  const [images, setImages] = useState<HTMLImageElement[]>([]);
  const [boxes, setBoxes] = useState<Box[][]>([]);
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checkedAll, setCheckedAll] = useState(false);
  const consentId = useId();
  const checkedId = useId();
  const heading = useRef<HTMLHeadingElement>(null);

  // Move focus to each step's heading so keyboard and screen-reader users land in the right place.
  useEffect(() => {
    heading.current?.focus();
  }, [step]);

  // Drop the images from memory when leaving the page.
  const imagesRef = useRef(images);
  imagesRef.current = images;
  useEffect(() => {
    return () => {
      imagesRef.current.forEach((img) => img.removeAttribute('src'));
    };
  }, []);

  function forget() {
    images.forEach((img) => img.removeAttribute('src'));
    setImages([]);
    setBoxes([]);
  }

  async function pick(files: FileList | null) {
    setError(null);
    const list = Array.from(files ?? []);
    if (!list.length) return;
    if (list.length > MAX_IMAGES) {
      setError(t('real_friend.too_many'));
      return;
    }
    try {
      const loaded = await Promise.all(list.map(loadImage));
      setImages(loaded);
      setBoxes(loaded.map(() => []));
      setCheckedAll(false);
      setStep('redact');
    } catch {
      setError(t('real_friend.bad_file'));
    }
  }

  async function analyze() {
    setError(null);
    let prepared: string[] = [];
    try {
      prepared = images.map((img, i) => prepareScreenshot(img, boxes[i]));
    } catch {
      setError(t('real_friend.bad_file'));
      return;
    }
    setStep('analyzing');
    try {
      const r = await api.analyzeFriend(prepared, lang);
      forget();
      setResult(r);
      setStep('noticed');
    } catch (e) {
      setError((e as ApiError).message);
      setStep('redact');
    } finally {
      prepared = [];
    }
  }

  function toForm(fromScreens: boolean) {
    if (fromScreens && result) {
      const d = result.draft;
      setDraft({
        ...EMPTY_DRAFT,
        name: '',
        guardedness: d.guardedness,
        personality: d.personality.slice(0, LIMITS.personality),
        situation: d.situation.slice(0, LIMITS.situation[1]),
        sample_texts: d.sample_texts.length ? d.sample_texts.slice(0, LIMITS.sampleCount).map((s) => s.slice(0, LIMITS.sampleText)) : [''],
      });
    }
    setFromRealFriend(fromScreens);
    setRemovedIdentifying(fromScreens && !!result?.removed_identifying);
    forget();
    setResult(null);
    navigate('/practice/new');
  }

  const manual = (
    <button type="button" className="link text-sm" onClick={() => toForm(false)} data-testid="fill-myself">
      {t('real_friend.fill_myself')}
    </button>
  );
  const allCovered = boxes.length > 0 && boxes.every((b) => b.length > 0);
  // The final check: the user confirms every screenshot is covered before anything is uploaded.
  const ready = allCovered && checkedAll;

  return (
    <div className="mx-auto max-w-3xl px-4 py-12 sm:px-6">
      <Link to="/practice/new" className="inline-flex items-center gap-1.5 text-sm font-semibold text-brand-deep">
        <Icon name="back" className="h-4 w-4" />
        {t('real_friend.back')}
      </Link>
      <h1 className="mt-5 text-4xl sm:text-5xl">{t('real_friend.title')}</h1>

      {step === 'explain' && (
        <section className="card mt-8 p-6 sm:p-8" aria-labelledby="rf-step">
          <h2 id="rf-step" ref={heading} tabIndex={-1} className="text-2xl outline-none">
            {t('real_friend.explain_title')}
          </h2>
          <p className="mt-3 leading-relaxed text-muted" data-testid="real-friend-explain">
            {t('real_friend.explain')}
          </p>
          <label htmlFor={consentId} className="mt-6 flex cursor-pointer items-start gap-3 rounded-xl border border-line p-4">
            <input id={consentId} type="checkbox" className="mt-1 h-4 w-4 accent-[rgb(var(--brand))]" checked={consent} onChange={(e) => setConsent(e.target.checked)} data-testid="consent" />
            <span className="leading-relaxed">{t('real_friend.consent')}</span>
          </label>
          <div className="mt-6 flex flex-wrap items-center gap-4">
            <button type="button" className="btn-primary" disabled={!consent} onClick={() => setStep('pick')} data-testid="consent-continue">
              {t('real_friend.continue')}
            </button>
            {manual}
          </div>
        </section>
      )}

      {step === 'pick' && (
        <section className="card mt-8 p-6 sm:p-8" aria-labelledby="rf-step">
          <h2 id="rf-step" ref={heading} tabIndex={-1} className="text-2xl outline-none">
            {t('real_friend.pick_title')}
          </h2>
          <p className="mt-3 leading-relaxed text-muted">{t('real_friend.pick_body')}</p>
          <label className="mt-6 flex cursor-pointer flex-col items-center gap-3 rounded-2xl border border-dashed border-line-strong p-8 text-center hover:border-brand">
            <Icon name="image" className="h-8 w-8 text-muted" />
            <span className="font-semibold">{t('real_friend.pick_button')}</span>
            <span className="text-sm text-muted">{t('real_friend.pick_hint')}</span>
            <input type="file" accept="image/png,image/jpeg,image/webp" multiple className="sr-only" onChange={(e) => pick(e.target.files)} data-testid="pick-images" />
          </label>
          {error && (
            <p role="alert" className="mt-4 text-sm font-medium text-bad">
              {error}
            </p>
          )}
          <div className="mt-6">{manual}</div>
        </section>
      )}

      {step === 'redact' && (
        <section className="mt-8" aria-labelledby="rf-step">
          <h2 id="rf-step" ref={heading} tabIndex={-1} className="text-2xl outline-none">
            {t('real_friend.redact_title')}
          </h2>
          <p className="mt-2 leading-relaxed text-muted">{t('real_friend.redact_body')}</p>
          <div className="mt-6 space-y-5">
            {images.map((img, i) => (
              <RedactEditor key={i} index={i} image={img} boxes={boxes[i] ?? []} onChange={(next) => setBoxes(boxes.map((b, j) => (j === i ? next : b)))} />
            ))}
          </div>
          <label htmlFor={checkedId} className="card mt-5 flex cursor-pointer items-start gap-3 p-4">
            <input
              id={checkedId}
              type="checkbox"
              className="mt-1 h-4 w-4 accent-[rgb(var(--brand))]"
              checked={checkedAll}
              onChange={(e) => setCheckedAll(e.target.checked)}
              data-testid="checked-all"
            />
            <span className="leading-relaxed">{t('real_friend.checked_all')}</span>
          </label>
          {error && (
            <div role="alert" className="card mt-5 border-bad/40 p-4" data-testid="analyze-error">
              <p className="font-medium">{error}</p>
              <div className="mt-3 flex flex-wrap gap-3">
                <button type="button" className="btn-ghost px-4 py-2 text-sm" onClick={analyze} disabled={!ready}>
                  {t('real_friend.try_again')}
                </button>
                <button type="button" className="btn-primary px-4 py-2 text-sm" onClick={() => toForm(false)}>
                  {t('real_friend.fill_myself')}
                </button>
              </div>
            </div>
          )}
          <div className="mt-6 flex flex-wrap items-center gap-4">
            <button type="button" className="btn-primary" disabled={!ready} onClick={analyze} data-testid="analyze">
              {t('real_friend.analyze')}
            </button>
            {!allCovered ? (
              <span className="text-sm text-muted">{t('real_friend.cover_each')}</span>
            ) : (
              !checkedAll && <span className="text-sm text-muted">{t('real_friend.tick_check')}</span>
            )}
            {manual}
          </div>
        </section>
      )}

      {step === 'analyzing' && (
        <section className="card mt-8 p-8 text-center" aria-labelledby="rf-step" aria-busy="true">
          <h2 id="rf-step" ref={heading} tabIndex={-1} className="text-2xl outline-none" role="status">
            {t('real_friend.analyzing')}
          </h2>
          <p className="mt-2 text-muted">{t('real_friend.analyzing_body')}</p>
          <div className="mx-auto mt-6 h-1 w-48 overflow-hidden rounded-full bg-sunken" aria-hidden="true">
            <div className="h-full w-1/3 animate-[slide_1.6s_ease-in-out_infinite] rounded-full bg-brand" />
          </div>
        </section>
      )}

      {step === 'noticed' && result && <Noticed result={result} headingRef={heading} onContinue={() => toForm(true)} />}
    </div>
  );
}

/**
 * "What we noticed": real help comes FIRST, steady and in help red: the imminent card (call the
 * country's emergency number or 988 now) above the urgent card (tell a trusted adult today), then the
 * signs. Copy is the safety lane's reviewed wording (wt-notes/safety.md).
 */
export function Noticed({ result, onContinue, headingRef }: { result: AnalyzeResult; onContinue: () => void; headingRef?: RefObject<HTMLHeadingElement> }) {
  const { t, lang, country } = usePrefs();
  const heading = headingRef;
  const toForm = () => onContinue();
  // The country's emergency number from the bundled crisis_lines (same source as /api/realmode; works offline).
  const emergency = offlineRealMode(lang, country).crisis.emergency || '911';
  const dialable = /^\d+$/.test(emergency);
  const urgent = result.urgency === 'tell_an_adult_now';
  return (
        <div className="mt-8 space-y-5">
          {result.imminent && (
            <section className="rounded-2xl border-2 border-warm bg-warm-soft p-6 sm:p-7" aria-labelledby="rf-imminent" data-testid="imminent-help">
              <h2 id="rf-imminent" ref={heading} tabIndex={-1} className="flex items-center gap-2 text-2xl outline-none">
                <Icon name="phone" className="h-6 w-6 shrink-0 text-warm" />
                {t('real_friend.imminent_title')}
              </h2>
              <p className="mt-3 text-[17px] font-medium leading-relaxed">{t('real_friend.imminent_body', { emergency })}</p>
              <div className="mt-5 grid max-w-md gap-2 sm:grid-cols-2">
                {dialable && (
                  <a href={`tel:${emergency}`} className="btn-warm py-3" data-testid="call-emergency">
                    <Icon name="phone" className="h-4 w-4" />
                    {t('real_friend.call_number', { number: emergency })}
                  </a>
                )}
                <a href="tel:988" className={dialable ? 'btn-ghost border-warm/50 py-3' : 'btn-warm py-3'}>
                  <Icon name="phone" className="h-4 w-4" />
                  {t('chat.crisis.call')}
                </a>
              </div>
            </section>
          )}
          {urgent && (
            <section className="rounded-2xl border-2 border-warm bg-warm-soft/40 p-6 sm:p-7" aria-labelledby="rf-urgent" data-testid="urgent-help">
              <h2 id="rf-urgent" ref={result.imminent ? undefined : heading} tabIndex={-1} className="flex items-center gap-2 text-2xl outline-none">
                <Icon name="heart" className="h-6 w-6 shrink-0 text-warm" />
                {t('real_friend.urgent_title')}
              </h2>
              <p className="mt-3 leading-relaxed">{t('real_friend.urgent_body')}</p>
              <div className="mt-5 max-w-md">
                <Call988 />
              </div>
              <Link to="/real" className="link mt-4 inline-block">
                {t('real_friend.urgent_link')}
              </Link>
            </section>
          )}
          <section className="card p-6 sm:p-7" aria-labelledby="rf-step" data-testid="noticed">
            <h2 id="rf-step" ref={urgent || result.imminent ? undefined : heading} tabIndex={-1} className="text-2xl outline-none">
              {t('real_friend.noticed_title')}
            </h2>
            {result.signs.length > 0 ? (
              <>
                <ul className="mt-4 flex flex-wrap gap-2" data-testid="signs">
                  {result.signs.map((s) => (
                    <li key={s} className="chip border-line-strong px-3 py-1 text-sm text-ink">
                      {t(`real_friend.signs.${s}`).startsWith('real_friend.') ? s.replace(/_/g, ' ') : t(`real_friend.signs.${s}`)}
                    </li>
                  ))}
                </ul>
                <p className="mt-3 text-sm text-muted">{t('real_friend.not_diagnosis')}</p>
              </>
            ) : (
              <p className="mt-3 text-muted">{t('real_friend.no_signs')}</p>
            )}
            {result.urgency === 'check_in_soon' && (
              <p className="mt-4 rounded-xl border border-line-strong p-4 leading-relaxed" data-testid="check-in-soon">
                {t('real_friend.check_in_soon')}
              </p>
            )}
            <p className="mt-5 text-sm leading-relaxed text-muted">{t('real_friend.review_next')}</p>
            <div className="mt-5">
              <button
                type="button"
                className={urgent || result.imminent ? 'btn-ghost' : 'btn-primary'}
                onClick={toForm}
                data-testid="to-form"
              >
                {t('real_friend.to_form')}
              </button>
            </div>
          </section>
        </div>
        );
}
