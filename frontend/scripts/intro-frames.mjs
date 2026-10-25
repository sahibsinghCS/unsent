/**
 * Frame sequence of the landing's opening animation, for reviewing the motion without a video:
 * 0 / 0.4 / 0.8 / 1.2 / 1.8 / 2.5 s after the page is ready, in dark and light, desktop and mobile.
 * Also checks that reduced motion shows the final state at once (headline, phone and CTAs visible).
 *
 *   npm run build && npm run preview; node scripts/intro-frames.mjs   → screenshots/brand/intro/
 */
import { chromium } from 'playwright-core';
import { mkdirSync } from 'node:fs';

const BASE = process.env.FR_UI ?? 'http://localhost:4173';
const OUT = new URL('../screenshots/brand/intro/', import.meta.url).pathname;
const EXECUTABLE = process.env.CHROMIUM_PATH ?? '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';
const FRAMES = [0, 400, 800, 1200, 1800, 2500];
const DEVICES = {
  desktop: { viewport: { width: 1440, height: 900 } },
  mobile: { viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true },
};
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ executablePath: EXECUTABLE });
for (const theme of ['dark', 'light']) {
  for (const [device, opts] of Object.entries(DEVICES)) {
    const page = await (await browser.newContext({ ...opts, colorScheme: theme })).newPage();
    await page.goto(BASE + '/', { waitUntil: 'domcontentloaded' });
    await page.locator('h1').waitFor();
    const t0 = Date.now();
    for (const at of FRAMES) {
      const wait = at - (Date.now() - t0);
      if (wait > 0) await page.waitForTimeout(wait);
      await page.screenshot({ path: `${OUT}intro-${theme}-${device}-${String(at).padStart(4, '0')}ms.png` });
    }
    // After the intro the headline is plain text, and a resize (desktop 1440 → 1200 → 1440) or a
    // rotation (mobile portrait → landscape → portrait) brings back exactly the same size and leading.
    await page.waitForTimeout(1500);
    const measure = () =>
      page.evaluate(() => {
        const h = document.querySelector('h1');
        const cs = getComputedStyle(h);
        return { size: cs.fontSize, leading: cs.lineHeight, height: Math.round(h.getBoundingClientRect().height), spans: h.querySelectorAll('[data-word]').length };
      });
    const before = await measure();
    if (before.spans) throw new Error(`${theme} ${device}: headline still split into animated words after the intro`);
    const vp = page.viewportSize();
    await page.setViewportSize(device === 'desktop' ? { width: 1200, height: 900 } : { width: vp.height, height: vp.width });
    await page.waitForTimeout(300);
    await page.setViewportSize(vp);
    await page.waitForTimeout(300);
    const after = await measure();
    if (JSON.stringify(before) !== JSON.stringify(after)) throw new Error(`${theme} ${device}: headline changed after resize ${JSON.stringify(before)} → ${JSON.stringify(after)}`);
    if (device === 'desktop' && before.size !== '83.2px') throw new Error(`${theme} desktop: headline ${before.size}, expected 83.2px (5.2rem)`);
    await page.context().close();
  }
  // Reduced motion: everything is in its final state immediately.
  const page = await (await browser.newContext({ ...DEVICES.desktop, colorScheme: theme, reducedMotion: 'reduce' })).newPage();
  await page.goto(BASE + '/');
  await page.locator('h1').waitFor();
  await page.waitForTimeout(100);
  const hidden = await page.evaluate(() =>
    ['h1', '[data-testid="start-practicing"]', '.im-bubble'].filter((sel) => {
      const el = document.querySelector(sel);
      return !el || Number(getComputedStyle(el.closest('.animate-fade-in, .animate-rise-phone') ?? el).opacity) < 0.99 || Number(getComputedStyle(el).opacity) < 0.99;
    }),
  );
  if (hidden.length) throw new Error(`reduced motion (${theme}): not in final state: ${hidden.join(', ')}`);
  await page.screenshot({ path: `${OUT}intro-${theme}-desktop-reduced.png` });
  await page.context().close();
  console.log(`  ${theme}: ${FRAMES.length} frames × 2 devices, resize/rotate keeps the headline, reduced motion static OK`);
}
await browser.close();
