/**
 * Before/after screenshots for a restyle: landing, practice, chat, chat + X-ray, feedback, what-if
 * and the friend form, on mobile and desktop, in light and dark. Drives a real session through the
 * API (the recorded demo messages), so every screen shows real data.
 *
 *   FR_UI=http://localhost:4173 node scripts/brand-shots.mjs after    → screenshots/brand/after-*.png
 */
import { chromium } from 'playwright-core';
import { mkdirSync } from 'node:fs';

const BASE = process.env.FR_UI ?? 'http://localhost:4173';
const API = process.env.FR_API ?? 'http://localhost:8000/api';
const PREFIX = process.argv[2] ?? 'after';
const ONLY = process.env.ONLY?.split(',');
const OUT = new URL('../screenshots/brand/', import.meta.url).pathname;
const EXECUTABLE = process.env.CHROMIUM_PATH ?? '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
mkdirSync(OUT, { recursive: true });

const DEVICES = {
  mobile: { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
  desktop: { viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 },
};
const MESSAGES = ["hey, you've seemed off lately. you ok?", "lol you'll be fine", 'sorry, that was a dumb thing to say. that sounds really hard'];

async function post(path, body) {
  const res = await fetch(API + path, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(`${path}: ${res.status}`);
  return res.json();
}

async function session() {
  const view = await post('/sessions', { scenario_id: 'after-the-breakup', locale: 'en', country: 'US' });
  let lost = null;
  for (const text of MESSAGES) {
    const turn = await post(`/sessions/${view.session_id}/messages`, { text });
    if (turn.friend_node?.seen_no_reply) lost = turn.user_node.id;
  }
  return { id: view.session_id, lost };
}

const browser = await chromium.launch({ executablePath: EXECUTABLE });
for (const theme of ['dark', 'light']) {
  for (const device of ['desktop', 'mobile']) {
    const { id, lost } = await session();
    const context = await browser.newContext({ ...DEVICES[device], colorScheme: theme, reducedMotion: 'reduce' });
    await context.addInitScript(() => sessionStorage.setItem('fr.checkin.' + location.pathname.split('/').pop(), '1'));
    const page = await context.newPage();
    const shot = async (name, full = true) => {
      if (ONLY && !ONLY.includes(name)) return;
      await page.waitForTimeout(500);
      await page.screenshot({ path: `${OUT}${PREFIX}-${name}-${device}-${theme}.png`, fullPage: full });
    };
    await page.goto(`${BASE}/`);
    await page.getByTestId('start-practicing').waitFor();
    await shot('landing');
    await page.goto(`${BASE}/practice`);
    await page.getByTestId('add-friend').waitFor();
    await shot('practice');
    await page.goto(`${BASE}/chat/${id}`);
    await page.getByTestId('messages').waitFor();
    await page.waitForTimeout(800);
    await shot('chat', false);
    await page.getByTestId('xray-toggle').click();
    await page.locator('[data-testid="xray-helper"]').first().waitFor();
    await shot('chat-xray', false);
    await page.goto(`${BASE}/feedback/${id}`);
    await page.getByTestId('summary').waitFor({ timeout: 30000 });
    await shot('feedback');
    await page.goto(`${BASE}/whatif/${id}${lost ? `?node=${lost}` : ''}`);
    await page.locator('[data-testid="whatif-path"], [data-testid="whatif-empty"]').first().waitFor({ timeout: 60000 });
    await shot('whatif');
    await page.goto(`${BASE}/practice/new`);
    await page.locator('form').first().waitFor();
    await shot('friend-form');
    await context.close();
    console.log(`  ${PREFIX} ${device} ${theme} OK`);
  }
}
await browser.close();
