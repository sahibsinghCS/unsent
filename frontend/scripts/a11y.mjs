/**
 * Accessibility check: runs axe-core (WCAG 2.0/2.1 A + AA rules) on the main pages in light and dark
 * mode, then drives the chat with the keyboard only. Fails on any serious or critical violation.
 * Usage: API on :8000 + `npm run preview`, then `node scripts/a11y.mjs`.
 */
import { chromium } from 'playwright-core';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const AXE = require.resolve('axe-core/axe.min.js');
const BASE = process.env.FR_UI ?? 'http://localhost:4173';
const EXECUTABLE = process.env.CHROMIUM_PATH ?? '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';

const browser = await chromium.launch({ executablePath: EXECUTABLE });
const api = await browser.newContext();
const post = (path, data) => api.request.post(`${BASE}/api${path}`, { data }).then((r) => r.json());

// A real conversation to audit chat (X-ray on), feedback and what-if.
const view = await post('/sessions', { scenario_id: 'after-the-breakup', locale: 'en', country: 'US' });
const sid = view.session_id;
for (const text of ['hey are you ok? you seemed really off at lunch', "lol you'll be fine", 'sorry, that sounds really hard', 'are you thinking about killing yourself?']) {
  await post(`/sessions/${sid}/messages`, { text });
}

const pages = [
  ['landing', '/', 'start-practicing'],
  ['practice', '/practice', 'scenarios'],
  ['chat', `/chat/${sid}`, 'composer'],
  ['feedback', `/feedback/${sid}`, 'turning-point'],
  ['whatif', `/whatif/${sid}`, 'simulated'],
  ['real', '/real', 'primary-line'],
  ['how', '/how', 'guardian-box'],
  ['privacy', '/privacy', null],
  ['404', '/nope', null],
];

const summary = [];
let blocking = 0;
for (const theme of ['light', 'dark']) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, colorScheme: theme, reducedMotion: 'reduce' });
  await context.addInitScript(() => sessionStorage.setItem('fr.checkin.' + location.pathname.split('/').pop(), '1'));
  const page = await context.newPage();
  for (const [name, path, testid] of pages) {
    await page.goto(BASE + path);
    if (testid) await page.getByTestId(testid).first().waitFor({ timeout: 30000 });
    if (name === 'chat') await page.getByTestId('xray-toggle').click();
    await page.waitForTimeout(600);
    await page.addScriptTag({ path: AXE });
    const result = await page.evaluate(() =>
      // eslint-disable-next-line no-undef
      axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] } }),
    );
    const bad = result.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical');
    blocking += bad.length;
    summary.push({ theme, page: name, violations: result.violations.length, serious_or_critical: bad.length, passes: result.passes.length });
    for (const v of result.violations) {
      console.log(`  [${theme}] ${name}: ${v.impact} ${v.id} (${v.nodes.length}) ${v.help}`);
      for (const n of v.nodes.slice(0, 3)) console.log(`      ${n.target.join(' ')} ${n.failureSummary?.split('\n')[1] ?? ''}`);
    }
  }
  await context.close();
}
console.table(summary);

// Keyboard-only chat: Tab to the composer, send with Enter, reach a sent bubble and rewind, toggle X-ray.
const kb = await browser.newContext({ viewport: { width: 390, height: 844 }, reducedMotion: 'reduce' });
const page = await kb.newPage();
const fresh = await post('/sessions', { scenario_id: 'after-the-breakup', locale: 'en', country: 'US' });
await page.goto(`${BASE}/chat/${fresh.session_id}`);
await page.getByTestId('composer').waitFor();
const focusedTestId = () => page.evaluate(() => document.activeElement?.getAttribute('data-testid'));
let found = false;
for (let i = 0; i < 40 && !found; i++) {
  await page.keyboard.press('Tab');
  found = (await focusedTestId()) === 'composer';
}
if (!found) throw new Error('keyboard: could not Tab to the message box');
await page.keyboard.type('hey are you ok? you seemed off today');
await page.keyboard.press('Enter');
await page.waitForFunction(() => document.querySelectorAll('[data-testid="messages"] .im-recv').length >= 3, null, { timeout: 30000 });
if ((await focusedTestId()) !== 'composer') throw new Error('keyboard: focus should return to the message box after sending');
// Your message becomes interactive (rewindable) once the friend's reply has finished arriving.
await page.locator('button[aria-label^="You:"]:enabled').first().waitFor({ timeout: 30000 });
// Shift+Tab back to the sent bubble, open it, rewind with Enter
let onBubble = false;
for (let i = 0; i < 10 && !onBubble; i++) {
  await page.keyboard.press('Shift+Tab');
  onBubble = await page.evaluate(() => (document.activeElement?.getAttribute('aria-label') ?? '').startsWith('You:'));
}
if (!onBubble) throw new Error('keyboard: could not reach the sent message');
await page.keyboard.press('Enter');
await page.getByTestId('rewind-here').waitFor();
await page.keyboard.press('Tab');
if ((await focusedTestId()) !== 'rewind-here') throw new Error('keyboard: Rewind button not next in tab order');
await page.keyboard.press('Enter');
await page.waitForFunction(() => document.querySelector('[data-testid="composer"]')?.value.startsWith('hey are you ok'), null, { timeout: 10000 });
// X-ray switch toggles with Space
await page.getByTestId('xray-toggle').focus();
await page.keyboard.press('Space');
if ((await page.getByTestId('xray-toggle').getAttribute('aria-checked')) !== 'true') throw new Error('keyboard: X-ray switch did not toggle');
console.log('  keyboard-only chat: Tab to box, Enter sends, focus returns, Shift+Tab to bubble, Enter → Rewind, Space toggles X-ray');

await browser.close();
if (blocking) throw new Error(`${blocking} serious/critical accessibility violations`);
console.log('a11y OK');
