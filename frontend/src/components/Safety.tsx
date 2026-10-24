/**
 * Safety UX. These follow docs/SAFE_MESSAGING.md: resources are always one tap away, the crisis
 * pause cannot be skipped without acknowledging them, and nothing here ever mentions methods.
 */
import { useState } from 'react';
import { Link } from 'react-router-dom';
import type { ScenarioSummary } from '../api/models';
import { usePrefs } from '../i18n';
import { Icon } from './Icon';
import { Modal } from './Modal';

/** Big call/text 988 buttons (US). Used in the crisis card, check-in and Real mode. */
export function Call988({ compact = false }: { compact?: boolean }) {
  const { t } = usePrefs();
  const size = compact ? 'py-2.5 text-sm' : 'py-3.5 text-base';
  return (
    <div className="grid grid-cols-2 gap-2">
      <a href="tel:988" className={`btn-warm ${size}`}>
        <Icon name="phone" className="h-4 w-4" />
        {t('chat.crisis.call')}
      </a>
      <a href="sms:988" className={`btn-ghost ${size} border-warm/50`}>
        <Icon name="message" className="h-4 w-4" />
        {t('chat.crisis.text')}
      </a>
    </div>
  );
}

/** Crisis pause: shown when the Guardian thinks the helper themself may be at risk. */
export function CrisisModal({ open, message, onAcknowledge }: { open: boolean; message?: string; onAcknowledge: () => void }) {
  const { t } = usePrefs();
  const [seen, setSeen] = useState(false);
  return (
    <Modal open={open} title={t('chat.crisis.title')} dismissible={false} tone="warm" icon={<Icon name="heart" className="mt-1 h-6 w-6 shrink-0 text-warm" />}>
      <div className="space-y-4" data-testid="crisis-card">
        <p className="text-[15px] leading-relaxed">{t('chat.crisis.body')}</p>
        {message && <p className="rounded-xl bg-sunken p-3 text-sm leading-relaxed text-muted">{message}</p>}
        <Call988 />
        <ul className="space-y-2 text-sm">
          <li className="flex gap-2">
            <Icon name="heart" className="mt-0.5 h-4 w-4 shrink-0 text-brand-deep" />
            {t('chat.crisis.adult')}
          </li>
          <li className="flex gap-2">
            <Icon name="phone" className="mt-0.5 h-4 w-4 shrink-0 text-bad" />
            {t('chat.crisis.emergency')}
          </li>
        </ul>
        <label className="flex cursor-pointer items-center gap-3 rounded-xl border border-line p-3 text-sm font-medium">
          <input type="checkbox" className="h-5 w-5 accent-[rgb(var(--brand))]" checked={seen} onChange={(e) => setSeen(e.target.checked)} />
          {t('chat.crisis.ack')}
        </label>
        <div className="flex flex-col-reverse gap-2 sm:flex-row sm:justify-between">
          <Link to="/real" className="btn-ghost">
            {t('chat.crisis.real')}
          </Link>
          <button type="button" className="btn-primary" disabled={!seen} onClick={onAcknowledge}>
            {t('chat.crisis.continue')}
          </button>
        </div>
      </div>
    </Modal>
  );
}

/** Teaching card shown in the chat when a harmful message was blocked. */
export function BlockedCard({ message }: { message?: string }) {
  const { t } = usePrefs();
  return (
    <div role="note" className="mx-auto my-1 max-w-[92%] rounded-xl border border-line bg-surface p-3.5 text-sm animate-pop-in" data-testid="blocked-card">
      <p className="flex items-center gap-2 font-semibold">
        <Icon name="shield" className="h-4 w-4 text-muted" />
        {t('chat.blocked.title')}
      </p>
      <p className="mt-1.5 leading-relaxed">{message || t('chat.blocked.teach')}</p>
      {message && <p className="mt-1.5 leading-relaxed text-muted">{t('chat.blocked.teach')}</p>}
    </div>
  );
}

/** Content warning before a scenario starts. */
export function ContentWarningModal({
  scenario,
  busy,
  onCancel,
  onStart,
}: {
  scenario: ScenarioSummary | null;
  busy: boolean;
  onCancel: () => void;
  onStart: () => void;
}) {
  const { t, tl } = usePrefs();
  return (
    <Modal open={!!scenario} title={t('cw.title')} onClose={onCancel} icon={<Icon name="shield" className="mt-1 h-6 w-6 shrink-0 text-brand-deep" />}>
      {scenario && (
        <div className="space-y-4" data-testid="content-warning">
          <div className="rounded-xl bg-sunken p-3.5">
            <p className="small-label mb-1">{t('cw.covers')}</p>
            <p className="font-medium">{scenario.content_warning}</p>
          </div>
          <ul className="space-y-2.5 text-sm leading-relaxed">
            {tl('cw.points').map((point, i) => (
              <li key={i} className="flex gap-2.5">
                <Icon name="check" className="mt-0.5 h-4 w-4 shrink-0 text-brand-deep" />
                {point}
              </li>
            ))}
          </ul>
          <Call988 compact />
          <div className="flex flex-col-reverse gap-2 pt-1 sm:flex-row sm:justify-end">
            <button type="button" className="btn-ghost" onClick={onCancel}>
              {t('cw.cancel')}
            </button>
            <button type="button" className="btn-primary" onClick={onStart} disabled={busy}>
              {busy ? t('cw.starting') : t('cw.begin')}
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}

/** "How are you feeling after that?" asked after every session. 😔 shows resources. */
export function CheckInModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { t } = usePrefs();
  const [mood, setMood] = useState<'good' | 'okay' | 'low' | null>(null);
  const moods = [
    { id: 'good', emoji: '😊' },
    { id: 'okay', emoji: '😐' },
    { id: 'low', emoji: '😔' },
  ] as const;
  return (
    <Modal open={open} title={t('checkin.title')} onClose={onClose}>
      <div className="space-y-4" data-testid="checkin">
        <p className="text-sm text-muted">{t('checkin.sub')}</p>
        <div role="radiogroup" aria-label={t('checkin.title')} className="grid grid-cols-3 gap-2">
          {moods.map((m) => (
            <button
              key={m.id}
              type="button"
              role="radio"
              aria-checked={mood === m.id}
              onClick={() => setMood(m.id)}
              className={`flex flex-col items-center gap-1 rounded-2xl border p-3 text-sm font-medium transition ${
                mood === m.id ? 'border-brand bg-brand-soft' : 'border-line hover:bg-sunken'
              }`}
            >
              <span className="text-3xl" aria-hidden="true">
                {m.emoji}
              </span>
              {t(`checkin.${m.id}`)}
            </button>
          ))}
        </div>
        {mood === 'low' && (
          <div className="space-y-3 rounded-2xl border border-warm/40 bg-warm-soft/50 p-4 animate-pop-in" data-testid="checkin-resources">
            <p className="text-sm leading-relaxed">{t('checkin.low_body')}</p>
            <Call988 compact />
            <Link to="/real" className="block text-center text-sm font-semibold text-brand-deep underline underline-offset-4">
              {t('chat.crisis.real')}
            </Link>
          </div>
        )}
        {mood && mood !== 'low' && <p className="text-sm text-muted animate-pop-in">{t('checkin.thanks')}</p>}
        <div className="flex justify-end">
          <button type="button" className="btn-primary" onClick={onClose}>
            {t('checkin.done')}
          </button>
        </div>
      </div>
    </Modal>
  );
}
