/**
 * Delete a custom friend: a small button and a calm confirm. DELETE /api/friends/{id} also ends every
 * chat with that friend on the server; afterwards the friend is removed from React state and
 * `onDeleted` runs (e.g. go back to /practice from its chat). A 404 means it's already gone.
 */
import { useState } from 'react';
import { ApiError, api } from '../api/client';
import { usePrefs } from '../i18n';
import { useFriends } from '../lib/friends';
import { Icon } from './Icon';
import { Modal } from './Modal';

export function DeleteFriendButton({ id, name, onDeleted, className = '' }: { id: string; name: string; onDeleted?: () => void; className?: string }) {
  const { t } = usePrefs();
  const { friend, setFriend } = useFriends();
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function remove() {
    setBusy(true);
    setError(null);
    try {
      await api.deleteFriend(id);
    } catch (e) {
      if ((e as ApiError).status !== 404) {
        setError((e as ApiError).message);
        setBusy(false);
        return;
      }
    }
    if (friend?.id === id) setFriend(null);
    setBusy(false);
    setOpen(false);
    onDeleted?.();
  }

  return (
    <>
      <button type="button" className={`btn-ghost px-3 py-1.5 text-[13px] ${className}`} onClick={() => setOpen(true)} aria-label={t('friends.delete_label', { name })} data-testid="delete-friend">
        <Icon name="trash" className="h-3.5 w-3.5" />
        {t('friends.delete')}
      </button>
      <Modal open={open} title={t('friends.delete_title', { name })} onClose={() => setOpen(false)}>
        <p className="leading-relaxed text-muted">{t('friends.delete_body')}</p>
        {error && (
          <p role="alert" className="mt-3 text-sm text-bad">
            {error}
          </p>
        )}
        <div className="mt-5 flex flex-wrap justify-end gap-2">
          <button type="button" className="btn-ghost" onClick={() => setOpen(false)} disabled={busy}>
            {t('friends.delete_cancel')}
          </button>
          <button type="button" className="btn-primary" onClick={remove} disabled={busy} data-testid="delete-friend-confirm">
            {t('friends.delete_confirm', { name })}
          </button>
        </div>
      </Modal>
    </>
  );
}
