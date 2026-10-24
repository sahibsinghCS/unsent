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
        raised: token('raised'),
        ink: token('ink'),
        muted: token('muted'),
        line: { DEFAULT: token('line'), strong: token('line-strong') },
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
        // Sahib's type system (sahibs.dev): Syne display, IBM Plex Sans UI, IBM Plex Mono for data.
        sans: ['"IBM Plex Sans"', 'system-ui', '-apple-system', '"Segoe UI"', 'Roboto', 'sans-serif'],
        display: ['Syne', '"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      borderRadius: { bubble: '1.35rem', xl2: '1.75rem' },
      boxShadow: {
        card: 'none',
        phone: '0 0 0 1px rgb(0 0 0 / 0.08)',
      },
      keyframes: {
        'pop-in': { '0%': { opacity: 0, transform: 'translateY(8px) scale(0.97)' }, '100%': { opacity: 1, transform: 'none' } },
        rise: { '0%': { opacity: 0, transform: 'translateY(14px)' }, '100%': { opacity: 1, transform: 'none' } },
        blink: { '0%, 80%, 100%': { opacity: 0.25, transform: 'translateY(0)' }, '40%': { opacity: 1, transform: 'translateY(-2px)' } },
        float: { '0%, 100%': { transform: 'translateY(0)' }, '50%': { transform: 'translateY(-8px)' } },
        scan: { '0%': { transform: 'translateY(-100%)' }, '100%': { transform: 'translateY(100%)' } },
        caret: { '0%, 49%': { opacity: 1 }, '50%, 100%': { opacity: 0 } },
        'bump': { '0%': { transform: 'scale(1)' }, '40%': { transform: 'scale(1.12)' }, '100%': { transform: 'scale(1)' } },
        // Calm intro motion: slow, eased, no bounce.
        'rise-in': { '0%': { opacity: 0, transform: 'translateY(12px)' }, '100%': { opacity: 1, transform: 'none' } },
        'rise-phone': { '0%': { opacity: 0, transform: 'translateY(24px)' }, '100%': { opacity: 1, transform: 'none' } },
        'fade-in': { '0%': { opacity: 0 }, '100%': { opacity: 1 } },
        breathe: { '0%, 100%': { transform: 'scale(0.84)', opacity: 'calc(var(--breathe-max) * 0.55)' }, '50%': { transform: 'scale(1.06)', opacity: 'var(--breathe-max)' } },
      },
      animation: {
        'pop-in': 'pop-in 260ms cubic-bezier(.2,.8,.2,1) both',
        rise: 'rise 600ms cubic-bezier(.2,.8,.2,1) both',
        blink: 'blink 1.2s infinite ease-in-out',
        float: 'float 6s ease-in-out infinite',
        scan: 'scan 2.8s linear infinite',
        caret: 'caret 1s steps(1) infinite',
        bump: 'bump 420ms ease-out',
        'rise-in': 'rise-in 700ms cubic-bezier(.25,.1,.25,1) both',
        'rise-phone': 'rise-phone 800ms cubic-bezier(.25,.1,.25,1) both',
        'fade-in': 'fade-in 700ms ease-out both',
        breathe: 'breathe 5.5s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};
