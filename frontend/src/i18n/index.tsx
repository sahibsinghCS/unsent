/**
 * App-wide preferences: language (EN/ES), theme (light/dark) and country (for crisis lines).
 * `t('chat.typing', { name: 'Maya' })` looks a dotted key up in src/i18n/<lang>.json, fills in
 * {placeholders}, and falls back to English if a Spanish string is missing.
 */
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import en from './en.json';
import es from './es.json';
import { load, save } from '../lib/storage';

export type Lang = 'en' | 'es';
export type Theme = 'light' | 'dark';
type Dict = Record<string, unknown>;
const DICTS: Record<Lang, Dict> = { en, es };

function lookup(dict: Dict, key: string): unknown {
  return key.split('.').reduce<unknown>((node, part) => (node && typeof node === 'object' ? (node as Dict)[part] : undefined), dict);
}

/** Translate a key for a language. Exported for tests. */
export function translate(lang: Lang, key: string, vars?: Record<string, string | number>): string {
  const value = lookup(DICTS[lang], key) ?? lookup(DICTS.en, key);
  if (typeof value !== 'string') return key;
  return vars ? value.replace(/\{(\w+)\}/g, (_, name) => String(vars[name] ?? `{${name}}`)) : value;
}

/** A translated list (e.g. bullet points). */
export function translateList(lang: Lang, key: string): string[] {
  const value = lookup(DICTS[lang], key) ?? lookup(DICTS.en, key);
  return Array.isArray(value) ? (value as string[]) : [];
}

interface Prefs {
  lang: Lang;
  setLang: (lang: Lang) => void;
  theme: Theme;
  toggleTheme: () => void;
  country: string;
  setCountry: (country: string) => void;
  t: (key: string, vars?: Record<string, string | number>) => string;
  tl: (key: string) => string[];
}

const PrefsContext = createContext<Prefs | null>(null);

function initialLang(): Lang {
  const saved = load('fr.lang');
  if (saved === 'en' || saved === 'es') return saved;
  return typeof navigator !== 'undefined' && navigator.language?.startsWith('es') ? 'es' : 'en';
}

export function PrefsProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(initialLang);
  const [theme, setTheme] = useState<Theme>(() =>
    typeof document !== 'undefined' && document.documentElement.classList.contains('dark') ? 'dark' : 'light',
  );
  const [country, setCountryState] = useState<string>(() => load('fr.country') ?? 'US');

  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  const setLang = useCallback((next: Lang) => {
    save('fr.lang', next);
    setLangState(next);
  }, []);
  const toggleTheme = useCallback(() => {
    setTheme((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark';
      save('fr.theme', next);
      return next;
    });
  }, []);
  const setCountry = useCallback((next: string) => {
    save('fr.country', next);
    setCountryState(next);
  }, []);

  const value = useMemo<Prefs>(
    () => ({
      lang,
      setLang,
      theme,
      toggleTheme,
      country,
      setCountry,
      t: (key, vars) => translate(lang, key, vars),
      tl: (key) => translateList(lang, key),
    }),
    [lang, setLang, theme, toggleTheme, country, setCountry],
  );
  return <PrefsContext.Provider value={value}>{children}</PrefsContext.Provider>;
}

export function usePrefs(): Prefs {
  const prefs = useContext(PrefsContext);
  if (!prefs) throw new Error('usePrefs must be used inside <PrefsProvider>');
  return prefs;
}
