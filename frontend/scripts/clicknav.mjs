/**
 * Click-navigation test: moves between every page by CLICKING header/footer links, the logo, the
 * help button and the CTAs (never page.goto between pages), in English and Spanish. A second pass
 * patches window.scrollTo to return a value, as some browser extensions do; that used to blank the
 * page on navigation because an effect returned scrollTo's result as its "cleanup".
 * Usage: API on :8000 + `npm run preview`, then `node scripts/clicknav.mjs`.
 */
import { chromium } from 'playwright-core';

const BASE = process.env.FR_UI ?? 'http://localhost:4173';
const EXECUTABLE = process.env.CHROMIUM_PATH ?? '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';

const T = {
  en: { practice: 'Practice', how: 'How it works', real: "If it's real", privacy: 'Privacy', begin: /I understand/, finish: 'Finish', whatif: 'What if?', backFeedback: 'Back to feedback', backChat: 'Back to chat', backPractice: 'Back to practice', home: 'Go home', cont: 'Continue', seeHow: 'See how it works' },
  es: { practice: 'Practicar', how: 'Cómo funciona', real: 'Si es real', privacy: 'Privacidad', begin: /Entiendo/, finish: 'Terminar', whatif: '¿Y si…?', backFeedback: 'Volver a los comentarios', backChat: 'Volver al chat', backPractice: 'Volver a practicar', home: 'Ir al inicio', cont: 'Continuar', seeHow: 'Ver cómo funciona' },
};

async function run(browser, lang, patchScroll) {
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 }, reducedMotion: 'reduce' });
  await context.addInitScript(
    ([l, patch]) => {
      localStorage.setItem('fr.lang', l);
      if (patch) {
        const original = window.scrollTo.bind(window);
        window.scrollTo = (...args) => {
          original(...args);
          return 1; // like an extension's wrapper: a non-undefined return value
        };
      }
    },
    [lang, patchScroll],
  );
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(e.message));
  const t = T[lang];
  const header = page.locator('header');
  const footer = page.locator('footer');
  const steps = [];

  /** Click, then require the new URL and a visible marker inside <main> (a blank page fails). */
  async function go(label, click, url, marker) {
    await click();
    await page.waitForURL(url, { timeout: 15000 });
    try {
      await page.locator('main').getByTestId(marker).or(page.locator('main').getByText(marker)).first().waitFor({ timeout: 30000 });
    } catch {
      throw new Error(`[${lang}${patchScroll ? ', patched scrollTo' : ''}] page did not render after: ${label}${errors.length ? ` (page error: ${errors.join(' | ')})` : ''}`);
    }
    const text = (await page.locator('main').innerText()).trim();
    if (text.length < 20) throw new Error(`[${lang}${patchScroll ? ', patched scrollTo' : ''}] blank page after: ${label}`);
    if (errors.length) throw new Error(`[${lang}] page error after ${label}: ${errors.join(' | ')}`);
    steps.push(label);
  }
  const link = (scope, name) => () => scope.getByRole('link', { name, exact: true }).filter({ visible: true }).first().click();

  await page.goto(BASE + '/'); // the only goto: the starting point
  await page.getByTestId('start-practicing').waitFor();
  await go('help button → real', () => page.getByTestId('help-now').click(), /\/real$/, 'primary-line');
  await go('footer → how', link(footer, t.how), /\/how$/, 'guardian-box');
  await go('footer → privacy', link(footer, t.privacy), /\/privacy$/, t.privacy);
  await go('footer → real', link(footer, t.real), /\/real$/, 'primary-line');
  await go('logo → home', () => header.getByRole('link', { name: 'FirstReply home' }).click(), /\/$/, 'start-practicing');
  await go('hero "see how" → how', link(page.locator('main'), t.seeHow), /\/how$/, 'guardian-box');
  await go('header → practice', link(header, t.practice), /\/practice$/, 'scenarios');
  await go('header → how', link(header, t.how), /\/how$/, 'guardian-box');
  await go('logo → home', () => header.getByRole('link', { name: 'FirstReply home' }).click(), /\/$/, 'start-practicing');
  await go('hero CTA → practice', () => page.getByTestId('start-practicing').click(), /\/practice$/, 'scenarios');
  await page.locator('[data-testid="scenarios"] button').first().click();
  await page.getByTestId('content-warning').waitFor();
  await go('content warning → chat', () => page.getByRole('button', { name: t.begin }).click(), /\/chat\//, 'composer');
  await page.fill('[data-testid="composer"]', lang === 'es' ? 'oye, ¿estás bien?' : 'hey are you ok?');
  await page.keyboard.press('Enter');
  await page.locator('[role="status"][aria-label*="typ"], [role="status"][aria-label*="escrib"]').first().waitFor({ state: 'detached', timeout: 30000 }).catch(() => {});
  await page.getByTestId('finish').and(page.locator(':enabled')).waitFor({ timeout: 30000 });
  await go('Finish → feedback', () => page.getByTestId('finish').click(), /\/feedback\//, 'checkin');
  await page.getByRole('button', { name: t.cont }).click();
  await go('feedback → what if', link(page.locator('main'), t.whatif), /\/whatif\//, 'simulated');
  await go('what-if → back to feedback', link(page.locator('main'), t.backFeedback), /\/feedback\//, 'turning-point');
  await go('feedback → back to chat', link(page.locator('main'), t.backChat), /\/chat\//, 'composer');
  await go('help button (from chat) → real', () => page.getByTestId('help-now').click(), /\/real$/, 'primary-line');
  await go('real → back to practice', link(page.locator('main'), t.backPractice), /\/practice$/, 'scenarios');
  await page.goto(BASE + '/no-such-page'); // 404 can only be reached by URL
  await go('404 → go home', link(page.locator('main'), t.home), /\/$/, 'start-practicing');
  await go('browser back', () => page.goBack(), /\/no-such-page$/, t.home);
  await context.close();
  console.log(`  ${lang}${patchScroll ? ' + patched scrollTo' : ''}: ${steps.length} click navigations OK`);
}

const browser = await chromium.launch({ executablePath: EXECUTABLE });
for (const lang of ['en', 'es']) for (const patch of [false, true]) await run(browser, lang, patch);
await browser.close();
console.log('click navigation OK');
