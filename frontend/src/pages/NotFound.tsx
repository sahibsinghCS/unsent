import { Link } from 'react-router-dom';
import { usePrefs } from '../i18n';

export function NotFound() {
  const { t } = usePrefs();
  return (
    <div className="mx-auto max-w-md px-4 py-20 text-center">
      <p className="numeral text-8xl italic text-brand">404</p>
      <h1 className="mt-4 text-3xl font-semibold">{t('notfound.title')}</h1>
      <p className="mt-2 text-muted">{t('notfound.body')}</p>
      <div className="mt-8 flex justify-center gap-3">
        <Link to="/" className="btn-primary">
          {t('notfound.home')}
        </Link>
        <Link to="/practice" className="btn-ghost">
          {t('app.nav.practice')}
        </Link>
      </div>
    </div>
  );
}
