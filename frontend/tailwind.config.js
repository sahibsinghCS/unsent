/** @type {import('tailwindcss').Config} */
// Design tokens live as CSS variables in src/index.css (light + dark). Tailwind just maps names
// to them, so restyling the whole app means editing one block of variables.
const token = (name) => `rgb(var(--${name}) / <alpha-value>)`;

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        bg: token('bg'),
        surface: token('surface'),
        sunken: token('sunken'),
        ink: token('ink'),
        muted: token('muted'),
        line: token('line'),
        brand: { DEFAULT: token('brand'), soft: token('brand-soft'), ink: token('brand-ink') },
        warm: { DEFAULT: token('warm'), soft: token('warm-soft') },
        good: { DEFAULT: token('good'), soft: token('good-soft') },
        bad: { DEFAULT: token('bad'), soft: token('bad-soft') },
        me: token('bubble-me'),
        them: token('bubble-them'),
      },
      fontFamily: {
        sans: ['ui-sans-serif', 'system-ui', '-apple-system', '"Segoe UI"', 'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
      borderRadius: { bubble: '1.25rem' },
      boxShadow: {
        card: '0 1px 2px rgb(0 0 0 / 0.04), 0 4px 16px rgb(0 0 0 / 0.06)',
        phone: '0 30px 60px -20px rgb(0 0 0 / 0.35), 0 0 0 1px rgb(0 0 0 / 0.06)',
      },
      keyframes: {
        'pop-in': { '0%': { opacity: 0, transform: 'translateY(6px) scale(0.98)' }, '100%': { opacity: 1, transform: 'none' } },
        blink: { '0%, 80%, 100%': { opacity: 0.25 }, '40%': { opacity: 1 } },
      },
      animation: { 'pop-in': 'pop-in 220ms ease-out both', blink: 'blink 1.2s infinite ease-in-out' },
    },
  },
  plugins: [],
};
