/**
 * E2E for "Practice for a real friend" (screenshots → draft) and deleting custom friends.
 *
 *   API on :8000 (FR_LLM=0) + `npm run preview`, then `node scripts/real-friend.mjs`
 *
 * /api/friends/analyze is mocked with page.route for each urgency (the real reader needs the AI), and
 * the mock inspects what was uploaded: a JPEG, at most 1280 px, with the covered pixels really black.
 * One pass runs against the real backend (FR_LLM=0) to show the needs_ai message and the manual form.
 * Redaction is also driven by keyboard only. axe must report 0 serious/critical issues on every step.
 * Screenshots go to screenshots/brand/real-friend/. Against the prod server (strict CSP), run with
 * FR_UI=http://localhost:7860 NO_AXE=1: the flow then also proves the CSP allows it (no violations).
 */
import { chromium } from 'playwright-core';
import { createRequire } from 'node:module';
import { mkdirSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const require = createRequire(import.meta.url);
const AXE = require.resolve('axe-core/axe.min.js');
const BASE = process.env.FR_UI ?? 'http://localhost:4173';
const EXECUTABLE = process.env.CHROMIUM_PATH ?? '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const OUT = new URL('../screenshots/brand/real-friend/', import.meta.url).pathname;
mkdirSync(OUT, { recursive: true });
const DEVICES = {
  desktop: { viewport: { width: 1440, height: 900 } },
  mobile: { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
};
const DRAFT = {
  personality: 'dry humor, short texts, lots of "idk"',
  situation: 'Their parents are splitting up and they stopped coming to practice. They say they are tired all the time.',
  sample_texts: ['idk its whatever', 'im just tired lol'],
  guardedness: 'guarded',
};
const SIGNS = { tell_an_adult_now: ['talks_about_dying', 'withdrawing', 'feels_like_a_burden'], check_in_soon: ['withdrawing', 'sleep_changes'], none: [] };

const browser = await chromium.launch({ executablePath: EXECUTABLE });
let problems = 0;
const fail = (msg) => {
  problems++;
  console.error('  FAIL', msg);
};

// A fake phone screenshot (1170×2532): a red contact name in the top bar and some bubbles.
async function makeScreenshotFile() {
  const page = await browser.newPage();
  const url = await page.evaluate(() => {
    const c = document.createElement('canvas');
    c.width = 1170;
    c.height = 2532;
    const x = c.getContext('2d');
    x.fillStyle = '#fff';
    x.fillRect(0, 0, c.width, c.height);
    x.fillStyle = '#f00';
    x.fillRect(300, 80, 570, 160); // "Alex · (555) 010-0199"
    x.fillStyle = '#e9e9eb';
    for (let i = 0; i < 6; i++) x.fillRect(60, 500 + i * 300, 700, 180);
    x.fillStyle = '#f00';
    x.fillRect(400, 1230, 370, 80); // a name in the middle, covered by the keyboard box
    return c.toDataURL('image/png');
  });
  await page.close();
  const file = join(tmpdir(), 'fr-screenshot.png');
  writeFileSync(file, Buffer.from(url.split(',')[1], 'base64'));
  return file;
}

async function axe(page, label) {
  if (process.env.NO_AXE) return; // e.g. against the prod server, whose CSP blocks injecting axe
  await page.waitForTimeout(400); // let button state transitions (disabled → enabled) finish
  await page.addScriptTag({ path: AXE });
  // eslint-disable-next-line no-undef
  const r = await page.evaluate(() => axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] } }));
  const bad = r.violations.filter((v) => v.impact === 'serious' || v.impact === 'critical');
  for (const v of r.violations) console.log(`  axe ${label}: ${v.impact} ${v.id} ${v.nodes.map((n) => n.target.join(' ')).slice(0, 2).join(' | ')}`);
  if (bad.length) fail(`axe ${label}: ${bad.length} serious/critical`);
}

/** Check the uploaded images in the browser: JPEG, ≤1280 px, and black where the boxes were. */
async function inspectUpload(page, images) {
  return page.evaluate(async (urls) => {
    const out = [];
    for (const url of urls) {
      const img = new Image();
      img.src = url;
      await img.decode();
      const c = document.createElement('canvas');
      c.width = img.width;
      c.height = img.height;
      const x = c.getContext('2d');
      x.drawImage(img, 0, 0);
      const at = (fx, fy) => Array.from(x.getImageData(Math.round(fx * img.width), Math.round(fy * img.height), 1, 1).data.slice(0, 3));
      out.push({ jpeg: url.startsWith('data:image/jpeg'), w: img.width, h: img.height, bytes: Math.round((url.length - url.indexOf(',') - 1) * 0.75), top: at(0.5, 0.06), middle: at(0.5, 0.5), bubble: at(0.2, 0.8) });
    }
    return out;
  }, images);
}

async function run({ theme, device, urgency, keyboard }) {
  const context = await browser.newContext({ ...DEVICES[device], colorScheme: theme });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (m) => /Content Security Policy|Refused to/.test(m.text()) && errors.push(m.text()));
  let uploaded = null;
  if (urgency) {
    await page.route('**/api/friends/analyze', async (route) => {
      uploaded = JSON.parse(route.request().postData() ?? '{}');
      await new Promise((r) => setTimeout(r, 600)); // let the progress state show
      await route.fulfill({ json: { draft: DRAFT, signs: SIGNS[urgency === 'imminent' ? 'tell_an_adult_now' : urgency], urgency: urgency === 'imminent' ? 'tell_an_adult_now' : urgency, imminent: urgency === 'imminent', removed_identifying: urgency === 'tell_an_adult_now' } });
    });
  }
  const tag = `${urgency ?? 'real-backend'}-${device}-${theme}`;
  const shot = (name, full = true) => page.screenshot({ path: `${OUT}${name}-${device}-${theme}.png`, fullPage: full });

  // Entry from the "Add your own friend" page (a click, not a URL).
  await page.goto(BASE + '/practice/new');
  await page.getByTestId('real-friend-entry').click();
  await page.waitForURL(/\/practice\/real$/);
  if (await page.getByTestId('consent-continue').isEnabled()) fail(`${tag}: continue enabled before consent`);
  if (urgency === 'tell_an_adult_now') {
    await axe(page, `${tag} explain`);
    await shot('01-explain');
  }
  await page.getByTestId('consent').check();
  await page.getByTestId('consent-continue').click();

  const file = await makeScreenshotFile();
  await page.getByTestId('pick-images').setInputFiles([file, file]);
  await page.getByTestId('redact-editor').first().waitFor();
  if (await page.getByTestId('analyze').isEnabled()) fail(`${tag}: analyze enabled before covering`);

  // Image 1: keyboard only (Add box → arrows → Shift+arrows). Image 2: "Cover the top bar".
  const first = page.getByTestId('redact-editor').nth(0);
  if (keyboard) {
    await first.getByTestId('add-box').focus();
    await page.keyboard.press('Enter');
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Shift+ArrowRight');
  } else {
    const canvas = first.getByTestId('redact-canvas');
    const box = await canvas.boundingBox();
    const at = (fx, fy) => ({ clientX: box.x + box.width * fx, clientY: box.y + box.height * fy });
    if (device === 'mobile') {
      // A finger drag: touch-type pointer events (the canvas is touch-action: none).
      const ev = (type, p) => canvas.dispatchEvent(type, { pointerId: 7, pointerType: 'touch', isPrimary: true, bubbles: true, ...p });
      await ev('pointerdown', at(0.3, 0.47));
      for (const f of [0.4, 0.5, 0.6, 0.72]) await ev('pointermove', at(f, 0.47 + (f - 0.3) * 0.15));
      await ev('pointerup', at(0.72, 0.53));
    } else {
      await page.mouse.move(at(0.3, 0.47).clientX, at(0.3, 0.47).clientY);
      await page.mouse.down();
      await page.mouse.move(at(0.72, 0.53).clientX, at(0.72, 0.53).clientY, { steps: 6 });
      await page.mouse.up();
    }
  }
  await first.getByTestId('cover-top').click();
  await page.getByTestId('redact-editor').nth(1).getByTestId('cover-top').click();
  if ((await first.getByTestId('box-count').innerText()).trim() !== '2 box(es) drawn') fail(`${tag}: box count ${await first.getByTestId('box-count').innerText()}`);
  if (urgency === 'tell_an_adult_now') {
    await axe(page, `${tag} redact`);
    await shot('02-redact');
  }
  await page.getByTestId('analyze').click();

  if (!urgency) {
    // Real backend with FR_LLM=0: the needs_ai message, and "Fill it in myself" opens the form.
    const err = page.getByTestId('analyze-error');
    await err.waitFor({ timeout: 30000 });
    if (!/needs the AI/.test(await err.innerText())) fail(`${tag}: expected needs_ai message, got ${await err.innerText()}`);
    await axe(page, `${tag} needs_ai`);
    await shot('05-needs-ai', false);
    await err.getByRole('button', { name: 'Fill it in myself' }).click();
    await page.waitForURL(/\/practice\/new$/);
    if ((await page.locator('#f-situation').inputValue()) !== '') fail(`${tag}: manual form should start empty`);
    await context.close();
    console.log(`  ${tag}: needs_ai message + manual form OK`);
    return;
  }

  await page.getByTestId('noticed').waitFor({ timeout: 20000 });
  const imgs = await inspectUpload(page, uploaded.images);
  for (const [i, m] of imgs.entries()) {
    if (!m.jpeg || Math.max(m.w, m.h) > 1280 || m.bytes > 1_500_000) fail(`${tag}: image ${i} not a ≤1280px JPEG under 1.5 MB: ${JSON.stringify(m)}`);
    if (Math.max(...m.top) > 40) fail(`${tag}: image ${i} top bar not black ${m.top}`);
    if (Math.min(...m.bubble) < 150) fail(`${tag}: image ${i} uncovered area changed ${m.bubble}`);
  }
  if (Math.max(...imgs[0].middle) > 40) fail(`${tag}: drawn box not flattened ${imgs[0].middle}`);
  if (uploaded.locale !== 'en') fail(`${tag}: locale ${uploaded.locale}`);

  const help = page.getByTestId('urgent-help');
  const imminentCard = page.getByTestId('imminent-help');
  if (urgency === 'imminent') {
    const before = await page.evaluate(() => {
      const a = document.querySelector('[data-testid="imminent-help"]');
      const b = document.querySelector('[data-testid="urgent-help"]');
      return !!(a && b && a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
    });
    if (!before) fail(`${tag}: the imminent card must sit above the urgent card`);
    if (!(await imminentCard.locator('a[href^="tel:"]').count())) fail(`${tag}: no call buttons on the imminent card`);
    if (await imminentCard.evaluate((el) => [el, ...el.querySelectorAll('*')].some((n) => getComputedStyle(n).animationName !== 'none'))) fail(`${tag}: imminent card animates`);
  } else if (await imminentCard.count()) fail(`${tag}: imminent card shown for ${urgency}`);
  if (urgency === 'tell_an_adult_now' || urgency === 'imminent') {
    if (!(await help.isVisible())) fail(`${tag}: no real-help card`);
    const order = await page.evaluate(() => {
      const a = document.querySelector('[data-testid="urgent-help"]');
      const b = document.querySelector('[data-testid="noticed"]');
      return !!(a && b && a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING);
    });
    if (!order) fail(`${tag}: real help must come before the signs and the form`);
    const animated = await help.evaluate((el) => [el, ...el.querySelectorAll('*')].some((n) => getComputedStyle(n).animationName !== 'none'));
    if (animated) fail(`${tag}: the real-help card must not animate`);
  } else if (await help.count()) fail(`${tag}: real-help card shown for ${urgency}`);
  if (urgency === 'check_in_soon' && !(await page.getByTestId('check-in-soon').isVisible())) fail(`${tag}: no check-in line`);
  await axe(page, `${tag} noticed`);
  await shot(`03-noticed-${urgency}`);

  if (urgency === 'tell_an_adult_now') {
    // Continue → the form is pre-filled, name empty with "Use a nickname"; create; chat is labelled;
    // delete from the chat header → back to /practice.
    await page.getByTestId('to-form').click();
    await page.waitForURL(/\/practice\/new$/);
    await page.getByTestId('from-screenshots').waitFor();
    if (!(await page.getByTestId('removed-identifying').isVisible())) fail(`${tag}: no "we removed identifying details" note`);
    if ((await page.locator('#f-situation').inputValue()) !== DRAFT.situation) fail(`${tag}: situation not pre-filled`);
    if ((await page.locator('#f-name').inputValue()) !== '' || (await page.locator('#f-name').getAttribute('placeholder')) !== 'Use a nickname') fail(`${tag}: name must be empty with the nickname hint`);
    await axe(page, `${tag} prefilled form`);
    await shot('04-prefilled-form');
    await page.locator('#f-name').fill('Sky');
    await page.getByTestId('friend-create').click();
    const realHelp = page.getByTestId('friend-real-help');
    const warning = page.getByTestId('content-warning');
    await realHelp.or(warning).first().waitFor({ timeout: 30000 });
    if (await realHelp.isVisible()) await page.getByRole('button', { name: 'Continue to practice' }).click();
    await warning.waitFor();
    await warning.getByRole('button').last().click();
    await page.waitForURL(/\/chat\//);
    await page.getByTestId('real-friend-chip').waitFor();
    await shot('06-chat-real-friend', false);
    await page.getByTestId('delete-friend').click();
    const deleted = page.waitForResponse((r) => r.request().method() === 'DELETE' && r.url().includes('/api/friends/'));
    await page.getByTestId('delete-friend-confirm').click();
    const res = await deleted;
    if (res.status() !== 204 || !res.request().headers()['x-friend-token']) fail(`${tag}: DELETE with owner token should be 204, got ${res.status()}`);
    await page.waitForURL(/\/practice$/);
    if (await page.getByText('Sky', { exact: true }).count()) fail(`${tag}: deleted friend still listed`);
  }
  if (errors.length) fail(`${tag}: page errors ${errors.join(' | ')}`);
  await context.close();
  console.log(`  ${tag}${keyboard ? ' (keyboard)' : ''}: OK`);
}

// Delete from the practice card: create a friend by hand, go to /practice, delete it there.
async function deleteFromCard() {
  const context = await browser.newContext({ ...DEVICES.desktop, colorScheme: 'light' });
  const page = await context.newPage();
  await page.goto(BASE + '/practice/new');
  await page.locator('#f-name').fill('Rio');
  await page.locator('#f-situation').fill('Rio failed a big test and has been skipping lunch to sit alone.');
  await page.getByTestId('friend-create').click();
  const realHelp = page.getByTestId('friend-real-help');
  const warning = page.getByTestId('content-warning');
  await realHelp.or(warning).first().waitFor({ timeout: 30000 });
  if (await realHelp.isVisible()) await page.getByRole('button', { name: 'Continue to practice' }).click();
  await warning.waitFor();
  await page.keyboard.press('Escape');
  await page.getByRole('link', { name: 'Practice', exact: true }).first().click();
  await page.waitForURL(/\/practice$/);
  await page.getByTestId('delete-friend').waitFor();
  await axe(page, 'practice with custom friend');
  await shot.call(null);
  async function shot() {
    await page.screenshot({ path: `${OUT}07-practice-delete-desktop-light.png` });
  }
  await page.getByTestId('delete-friend').click();
  await page.screenshot({ path: `${OUT}08-delete-confirm-desktop-light.png` });
  const deleted = page.waitForResponse((r) => r.request().method() === 'DELETE' && r.url().includes('/api/friends/'));
  await page.getByTestId('delete-friend-confirm').click();
  const res = await deleted;
  if (res.status() !== 204) fail(`card delete: DELETE with owner token should be 204, got ${res.status()}`);
  // Without the token the server refuses (404), so nobody else can delete your friend.
  const id = new URL(res.url()).pathname.split('/').pop();
  const anon = await page.request.delete(`${BASE}/api/friends/${id}`);
  if (anon.status() !== 404) fail(`card delete: tokenless DELETE should be 404, got ${anon.status()}`);
  await page.getByTestId('delete-friend').waitFor({ state: 'detached' });
  if (await page.getByText('Rio', { exact: true }).count()) fail('card delete: Rio still listed');
  await context.close();
  console.log('  delete from practice card: OK');
}

await run({ theme: 'dark', device: 'desktop', urgency: 'tell_an_adult_now', keyboard: true });
await run({ theme: 'light', device: 'desktop', urgency: 'tell_an_adult_now', keyboard: false });
await run({ theme: 'light', device: 'mobile', urgency: 'tell_an_adult_now', keyboard: false });
await run({ theme: 'dark', device: 'mobile', urgency: 'check_in_soon', keyboard: true });
await run({ theme: 'light', device: 'desktop', urgency: 'none', keyboard: false });
await run({ theme: 'dark', device: 'desktop', urgency: 'imminent', keyboard: true });
await run({ theme: 'light', device: 'mobile', urgency: 'imminent', keyboard: false });
await run({ theme: 'light', device: 'desktop', urgency: null, keyboard: true });
await deleteFromCard();
await browser.close();
if (problems) {
  console.error(`real friend: ${problems} problem(s)`);
  process.exit(1);
}
console.log('real friend OK');
