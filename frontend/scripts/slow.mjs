/**
 * Slow-backend check: the real AI voice can take 2–5 s per reply. This adds latency in the test
 * harness only (Playwright network routing; app code is untouched) and verifies:
 *   - the typing indicator shows for the whole request, and the Send button is disabled;
 *   - clicking Send / pressing Enter again during the wait never sends a second message;
 *   - a slow failure shows the error, restores the draft and re-enables the composer.
 * Usage: API on :8000 + `npm run preview`, then `node scripts/slow.mjs`.
 */
import { chromium } from 'playwright-core';

const BASE = process.env.FR_UI ?? 'http://localhost:4173';
const EXECUTABLE = process.env.CHROMIUM_PATH ?? '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const fail = (msg) => {
  throw new Error(msg);
};

const browser = await chromium.launch({ executablePath: EXECUTABLE });
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));

const view = await page.request.post(`${BASE}/api/sessions`, { data: { scenario_id: 'after-the-breakup', locale: 'en', country: 'US' } }).then((r) => r.json());
await page.goto(`${BASE}/chat/${view.session_id}`);
await page.getByTestId('composer').waitFor();

// 1. A 4.5 s reply
let posts = 0;
await page.route('**/api/sessions/*/messages', async (route) => {
  posts++;
  await new Promise((r) => setTimeout(r, 4500));
  await route.continue();
});
const send = page.getByRole('button', { name: 'Send' });
await page.fill('[data-testid="composer"]', 'hey are you ok? you seemed really off at lunch');
await send.click();
await page.waitForTimeout(1000);
if (!(await page.getByRole('status', { name: /typing/ }).isVisible())) fail('typing indicator not shown while waiting');
if (!(await send.isDisabled())) fail('Send should be disabled while a reply is in flight');
// Try hard to double-send: type again, press Enter, force-click the button.
await page.fill('[data-testid="composer"]', 'are you there?');
await page.keyboard.press('Enter');
await send.click({ force: true }).catch(() => {});
await page.waitForTimeout(500);
if (posts !== 1) fail(`expected 1 request during a slow reply, saw ${posts}`);
// The reply arrives and is revealed bubble by bubble.
await page.waitForFunction(() => !document.querySelector('[role="status"][aria-label*="typing"]'), null, { timeout: 30000 });
const friendBubbles = await page.locator('[data-testid="messages"] .bg-them').count();
if (friendBubbles < 3) fail('friend reply did not appear after the slow request');
if ((await page.inputValue('[data-testid="composer"]')) !== 'are you there?') fail('a draft typed during the wait was lost');
console.log('  slow reply: typing shown, Send disabled, 1 request, reply revealed, draft kept');
await page.unroute('**/api/sessions/*/messages');

// 2. A slow failure (3 s then 503)
await page.route('**/api/sessions/*/messages', async (route) => {
  await new Promise((r) => setTimeout(r, 3000));
  await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'The friend is taking too long to answer. Please try again.' }) });
});
await page.fill('[data-testid="composer"]', 'that sounds really hard');
await page.keyboard.press('Enter');
await page.getByRole('alert').filter({ hasText: 'Message not sent' }).waitFor({ timeout: 10000 });
if ((await page.inputValue('[data-testid="composer"]')) !== 'that sounds really hard') fail('draft not restored after an error');
if (await page.getByRole('status', { name: /typing/ }).count()) fail('typing indicator stuck after an error');
if (await send.isDisabled()) fail('Send still disabled after an error');
await page.screenshot({ path: new URL('../screenshots/30-chat-slow-error-mobile.png', import.meta.url).pathname });
console.log('  slow failure: error shown, draft restored, composer usable again');
await page.unroute('**/api/sessions/*/messages');

// 3. Retry works
await page.keyboard.press('Enter');
await page.waitForFunction(() => !document.querySelector('[role="status"][aria-label*="typing"]'), null, { timeout: 30000 });
if (await page.getByRole('alert').count()) fail('error did not clear after a successful retry');
console.log('  retry: sent, error cleared');

await browser.close();
if (errors.length) fail(`page errors:\n${errors.join('\n')}`);
console.log('slow backend OK');
