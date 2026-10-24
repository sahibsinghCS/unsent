import { usePrefs } from '../i18n';
import { Icon } from '../components/Icon';

export function Privacy() {
  const { t, tl } = usePrefs();
  return (
    <div className="mx-auto max-w-2xl px-4 py-12 sm:px-6">
      <h1 className="text-4xl font-semibold sm:text-5xl">{t('privacy.title')}</h1>
      <p className="mt-3 text-lg text-muted">{t('privacy.intro')}</p>
      <ul className="mt-8 space-y-3">
        {tl('privacy.points').map((point, i) => (
          <li key={i} className="card flex gap-3 p-4 leading-relaxed">
            <Icon name="lock" className="mt-0.5 h-5 w-5 shrink-0 text-brand" />
            {point}
          </li>
        ))}
      </ul>
    </div>
  );
}
