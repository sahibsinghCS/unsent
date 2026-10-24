/** @type {import('tailwindcss').Config} */
// Design tokens live as CSS variables in src/index.css (light + dark). Tailwind maps names to them,
// so restyling the whole app means editing one block of variables there.
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
        brand: { DEFAULT: token('brand'), soft: token('brand-soft'), ink: token('brand-ink'), deep: token('brand-deep') },
        warm: { DEFAULT: token('warm'), soft: token('warm-soft') },
        glow: token('glow'),
        good: { DEFAULT: token('good'), soft: token('good-soft') },
        bad: { DEFAULT: token('bad'), soft: token('bad-soft') },
        me: token('bubble-me'),
        them: token('bubble-them'),
        night: { DEFAULT: token('night'), ink: token('night-ink'), muted: token('night-muted'), line: token('night-line') },
      },
      fontFamily: {
        // Self-hosted (@fontsource-variable): the production CSP only allows fonts from our own origin.
        display: ['"Fraunces Variable"', 'ui-serif', 'Georgia', 'serif'],
        sans: ['"Plus Jakarta Sans Variable"', 'ui-sans-serif', 'system-ui', '-apple-system', '"Segoe UI"', 'Roboto', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
      borderRadius: { bubble: '1.35rem', xl2: '1.75rem' },
      boxShadow: {
        card: '0 1px 0 rgb(255 255 255 / 0.6) inset, 0 1px 2px rgb(30 15 50 / 0.05), 0 8px 24px -12px rgb(30 15 50 / 0.18)',
        lift: '0 2px 4px rgb(30 15 50 / 0.06), 0 22px 44px -18px rgb(60 30 120 / 0.35)',
        phone: '0 40px 80px -30px rgb(40 20 90 / 0.45), 0 0 0 1px rgb(0 0 0 / 0.06)',
        glow: '0 0 0 1px rgb(var(--brand) / 0.35), 0 10px 40px -10px rgb(var(--brand) / 0.55)',
      },
      keyframes: {
        'pop-in': { '0%': { opacity: 0, transform: 'translateY(8px) scale(0.97)' }, '100%': { opacity: 1, transform: 'none' } },
        rise: { '0%': { opacity: 0, transform: 'translateY(14px)' }, '100%': { opacity: 1, transform: 'none' } },
        blink: { '0%, 80%, 100%': { opacity: 0.25, transform: 'translateY(0)' }, '40%': { opacity: 1, transform: 'translateY(-2px)' } },
        float: { '0%, 100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-8px)' } },
        scan: { '0%': { transform: 'translateY(-100%)' }, '100%': { transform: 'translateY(100%)' } },
        caret: { '0%, 49%': { opacity: 1 }, '50%, 100%': { opacity: 0 } },
        'bump': { '0%': { transform: 'scale(1)' }, '40%': { transform: 'scale(1.12)' }, '100%': { transform: 'scale(1)' } },
      },
      animation: {
        'pop-in': 'pop-in 260ms cubic-bezier(.2,.8,.2,1) both',
        rise: 'rise 600ms cubic-bezier(.2,.8,.2,1) both',
        blink: 'blink 1.2s infinite ease-in-out',
        float: 'float 6s ease-in-out infinite',
        scan: 'scan 2.8s linear infinite',
        caret: 'caret 1s steps(1) infinite',
        bump: 'bump 420ms ease-out',
      },
    },
  },
  plugins: [],
};
