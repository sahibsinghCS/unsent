// Loading and error states used by every page.
import { usePrefs } from '../i18n';

export function Spinner({ label }: { label?: string }) {
  const { t } = usePrefs();
  return (
    <div role="status" className="flex items-center justify-center gap-3 py-16 text-muted">
      <span className="h-5 w-5 animate-spin rounded-full border-2 border-brand border-t-transparent" aria-hidden="true" />
      <span>{label ?? t('app.loading')}</span>
    </div>
  );
}

export function ErrorBox({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const { t } = usePrefs();
  return (
    <div role="alert" className="card mx-auto my-10 max-w-md p-6 text-center">
      <p className="font-medium">{message}</p>
      {onRetry && (
        <button type="button" className="btn-ghost mt-4" onClick={onRetry}>
          {t('app.retry')}
        </button>
      )}
    </div>
  );
}
