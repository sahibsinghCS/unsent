// App shell: top bar (logo, nav, language, theme, the always-visible "I need help now" button),
// page content, and the safety footer. Shown on every screen.
import { Link, NavLink, Outlet } from 'react-router-dom';
import { usePrefs, type Lang } from '../i18n';
import { Icon } from './Icon';

export function Logo({ className = '' }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 font-extrabold tracking-tight ${className}`}>
      <img src="/favicon.svg" alt="" className="h-7 w-7" />
      FirstReply
    </span>
  );
}

function LangToggle() {
  const { lang, setLang, t } = usePrefs();
  return (
    <div role="group" aria-label={t('app.language')} className="flex rounded-full border border-line bg-surface p-0.5 text-xs font-semibold">
      {(['en', 'es'] as Lang[]).map((code) => (
        <button
          key={code}
          type="button"
          onClick={() => setLang(code)}
          aria-pressed={lang === code}
          className={`rounded-full px-2.5 py-1 uppercase transition ${lang === code ? 'bg-brand text-brand-ink' : 'text-muted hover:text-ink'}`}
        >
          {code}
        </button>
      ))}
    </div>
  );
}

function ThemeToggle() {
  const { theme, toggleTheme, t } = usePrefs();
  const label = theme === 'dark' ? t('app.theme_light') : t('app.theme_dark');
  return (
    <button type="button" onClick={toggleTheme} className="rounded-full border border-line bg-surface p-2 text-muted hover:text-ink" aria-label={label} title={label}>
      <Icon name={theme === 'dark' ? 'sun' : 'moon'} className="h-4 w-4" />
    </button>
  );
}

const navClass = ({ isActive }: { isActive: boolean }) =>
  `rounded-full px-3 py-1.5 text-sm font-medium transition ${isActive ? 'bg-brand-soft text-ink' : 'text-muted hover:text-ink'}`;

export function Layout() {
  const { t } = usePrefs();
  return (
    <div className="flex min-h-screen flex-col">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[60] focus:rounded-lg focus:bg-surface focus:px-4 focus:py-2">
        {t('app.skip')}
      </a>
      <header className="sticky top-0 z-40 border-b border-line/70 bg-bg/85 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center gap-2 px-3 sm:px-5">
          <Link to="/" className="mr-1 rounded-lg text-lg" aria-label="FirstReply home">
            <Logo />
          </Link>
          <nav className="hidden items-center gap-1 md:flex" aria-label="Main">
            <NavLink to="/practice" className={navClass}>
              {t('app.nav.practice')}
            </NavLink>
            <NavLink to="/how" className={navClass}>
              {t('app.nav.how')}
            </NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-1.5 sm:gap-2">
            <div className="hidden items-center gap-2 sm:flex">
              <LangToggle />
              <ThemeToggle />
            </div>
            <Link to="/real" className="btn-warm px-3 py-2 text-xs sm:px-4 sm:text-sm" data-testid="help-now">
              <Icon name="heart" className="h-4 w-4" />
              {t('app.help_now')}
            </Link>
          </div>
        </div>
        {/* Small screens: language + theme live in a slim second row so nothing is hidden. */}
        <div className="flex items-center justify-end gap-2 border-t border-line/50 px-3 py-1.5 sm:hidden">
          <NavLink to="/practice" className={navClass}>
            {t('app.nav.practice')}
          </NavLink>
          <NavLink to="/how" className={`${navClass({ isActive: false })} mr-auto`}>
            {t('app.nav.how')}
          </NavLink>
          <LangToggle />
          <ThemeToggle />
        </div>
      </header>

      <main id="main" className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-line bg-sunken/60">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 px-4 py-6 text-sm text-muted sm:flex-row sm:items-center sm:justify-between">
          <p className="max-w-2xl">
            <Icon name="shield" className="mr-1.5 inline h-4 w-4 align-[-3px] text-brand" />
            {t('app.footer')}
          </p>
          <nav className="flex gap-4" aria-label="Footer">
            <Link className="hover:text-ink underline-offset-4 hover:underline" to="/real">{t('app.footer_links.real')}</Link>
            <Link className="hover:text-ink underline-offset-4 hover:underline" to="/how">{t('app.footer_links.how')}</Link>
            <Link className="hover:text-ink underline-offset-4 hover:underline" to="/privacy">{t('app.footer_links.privacy')}</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
}
