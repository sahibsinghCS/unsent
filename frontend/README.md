# FirstReply frontend

React + TypeScript + Tailwind, built with Vite. Full explanation: [`docs/how/frontend.md`](../docs/how/frontend.md).

```bash
make dev-stub          # (repo root) API on :8000 with every component stubbed
npm install
npm run dev            # http://localhost:5173 (proxies /api → :8000)
npm run test           # vitest
npm run build          # → dist/, served by FastAPI at /
npm run preview & npm run screenshots   # full journey in Chromium → screenshots/
npm run gen:api        # regenerate src/api/types.ts from the running API
```

## Customizing the look
- **Colors / dark mode:** every color is a CSS variable in `src/index.css` (`:root` = light, `.dark` = dark). Change them there; Tailwind classes like `bg-brand`, `text-muted`, `bg-me` follow automatically.
- **Words:** all UI text lives in `src/i18n/en.json` and `es.json` (same keys). Use `t('section.key')` in components.
- **Shared pieces:** buttons/cards are Tailwind component classes in `src/index.css` (`.btn-primary`, `.card`, `.chip`). Phone bubbles are in `src/components/Phone.tsx`. Skill colors are in `src/lib/labels.ts`.
