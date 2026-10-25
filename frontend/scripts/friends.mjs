/**
 * "Add your own friend" end to end against the real backend: create a friend from the form (live
 * preview), start the chat, 3 turns, Finish → feedback, then What-if. English and Spanish, mobile
 * and desktop. Also runs axe on the new page and on the custom-friend chat, and takes screenshots.
 * Usage: API on :8000 + `npm run preview`, then `node scripts/friends.mjs`.
 */
import { chromium } from 'playwright-core';
import { screenshot } from './lib/fullshot.mjs';
import { createRequire } from 'node:module';
import { mkdirSync } from 'node:fs';

const require = createRequire(import.meta.url);
const AXE = require.resolve('axe-core/axe.min.js');
const BASE = process.env.FR_UI ?? 'http://localhost:4173';
const EXECUTABLE = process.env.CHROMIUM_PATH ?? '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const OUT = new URL('../screenshots/', import.meta.url).pathname;
mkdirSync(OUT, { recursive: true });

const COPY = {
  en: {
    name: 'Alex', personality: 'funny, gets quiet and sarcastic when stressed, types in lowercase',
    situation: "their parents are splitting up and they've stopped coming to practice",
    texts: ['idk im just tired lol', 'its whatever'],
    turns: ["hey, you've seemed really down lately. are you ok?", "that sounds really hard, i'm sorry", 'are you thinking about killing yourself?'],
    begin: /I understand/, finish: 'Finish', cont: 'Continue', whatif: 'What if?',
  },
  es: {
    name: 'Alex', personality: 'gracioso, se pone callado y sarcástico cuando está estresado, escribe en minúsculas',
    situation: 'sus papás se están separando y dejó de ir a los entrenamientos',
    texts: ['no sé, solo estoy cansado jaja', 'da igual'],
    turns: ['oye, te he notado muy bajoneado. ¿estás bien?', 'eso suena muy difícil, lo siento', '¿estás pensando en suicidarte?'],
    begin: /Entiendo/, finish: 'Terminar', cont: 'Continuar', whatif: '¿Y si…?',
  },
};
const DEVICES = {
  mobile: { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
  desktop: { viewport: { width: 1440, height: 900 } },
};

async function axe(page, label) {
  await page.waitForTimeout(900); // let pop-in animations finish (mid-fade text has lower contrast)
  await page.addScriptTag({ path: AXE });
  // eslint-disable-next-line no-undef
  const r = await page.evaluate(() => axe.run(document, { runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] } }));
  for (const v of r.violations) console.log(`    axe ${label}: ${v.impact} ${v.id} ${v.nodes.map((n) => n.target.join(' ')).slice(0, 2).join(' | ')}`);
  return r.violations.length;
}

let violations = 0;
async function run(browser, lang, device) {
  const c = COPY[lang];
  const context = await browser.newContext({ ...DEVICES[device], colorScheme: lang === 'es' ? 'dark' : 'light' });
  await context.addInitScript((l) => localStorage.setItem('fr.lang', l), lang);
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  const shot = async (name, full = false) => {
    if (full) await page.evaluate(() => window.scrollTo(0, 0));
    await page.waitForTimeout(400);
    await screenshot(page, `${OUT}${name}-${lang}-${device}.png`, full);
    console.log(`   ${name}-${lang}-${device}.png`);
  };
  const waitIdle = () => page.locator('[role="status"][aria-label*="typ"], [role="status"][aria-label*="escrib"]').first().waitFor({ state: 'detached', timeout: 40000 }).catch(() => {});

  // Practice → "Add your own friend" (a click, not a URL)
  await page.goto(BASE + '/practice');
  await page.getByTestId('add-friend').click();
  await page.waitForURL(/\/practice\/new$/);
  await page.getByTestId('friend-form').waitFor();
  await page.locator('#f-name').fill(c.name);
  await page.locator('#f-personality').fill(c.personality);
  await page.locator('#f-situation').fill(c.situation);
  await page.getByTestId('friend-text').first().fill(c.texts[0]);
  await page.getByRole('button', { name: lang === 'es' ? 'Agregar otro mensaje' : 'Add another text' }).click();
  await page.getByTestId('friend-text').nth(1).fill(c.texts[1]);
  await page.getByTestId('friend-preview').getByText(c.texts[1]).waitFor();
  violations += await axe(page, `new-friend ${lang} ${device}`);
  await shot('40-friend-form', true);

  // Create → (real help notice if any) → content warning → chat
  await page.getByTestId('friend-create').click();
  const help = page.getByTestId('friend-real-help');
  const warning = page.getByTestId('content-warning');
  await help.or(warning).first().waitFor({ timeout: 30000 });
  if (await help.isVisible()) await page.getByRole('button', { name: lang === 'es' ? 'Continuar a la práctica' : 'Continue to practice' }).click();
  await warning.waitFor();
  await page.getByRole('button', { name: c.begin }).click();
  await page.waitForURL(/\/chat\//);
  const sessionId = page.url().split('/chat/')[1];
  await page.getByTestId('composer').waitFor();
  for (const text of c.turns) {
    await page.fill('[data-testid="composer"]', text);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(200);
    await waitIdle();
  }
  await page.getByTestId('xray-toggle').click();
  await page.locator('[data-testid="xray-helper"]').first().waitFor();
  violations += await axe(page, `custom chat ${lang} ${device}`);
  await shot('41-friend-chat');

  // Finish → feedback → What-if
  await page.getByTestId('finish').click();
  await page.waitForURL(/\/feedback\//);
  await page.getByTestId('checkin').waitFor();
  await page.getByRole('button', { name: c.cont }).click();
  await page.getByTestId('turning-point').waitFor({ timeout: 40000 });
  await page.getByRole('link', { name: c.whatif }).first().click();
  await page.waitForURL(/\/whatif\//);
  await page.locator('[data-testid="whatif-path"], [data-testid="whatif-empty"]').first().waitFor({ timeout: 60000 });
  await shot('42-friend-whatif', true);

  // Back on Practice, "Your friend" is listed (React state only) with the not-reviewed chip
  await page.getByRole('link', { name: lang === 'es' ? 'Practicar' : 'Practice', exact: true }).filter({ visible: true }).first().click();
  await page.getByTestId('custom-chip').waitFor();
  await shot('43-practice-your-friend', true);

  const storage = await page.evaluate(() => Object.keys(localStorage).concat(Object.keys(sessionStorage)).filter((k) => !/^fr\.(lang|theme|country|xray|checkin\.)/.test(k)));
  if (storage.length) throw new Error(`friend data leaked into browser storage: ${storage.join(', ')}`);
  if (errors.length) throw new Error(`page errors: ${errors.join(' | ')}`);
  console.log(`  ${lang} ${device}: created, 3 turns, feedback, what-if OK (session ${sessionId})`);
  await context.close();
}

const browser = await chromium.launch({ executablePath: EXECUTABLE });
for (const lang of ['en', 'es']) for (const device of ['mobile', 'desktop']) await run(browser, lang, device);
await browser.close();
if (violations) throw new Error(`${violations} axe violations`);
console.log('custom friend OK');
