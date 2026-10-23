/**
 * Headless-Chromium check that the Content-Security-Policy breaks nothing in the real built app.
 *
 *   node deploy/csp_check.mjs http://127.0.0.1:7860      (a prod-mode server serving frontend/dist)
 *
 * Walks every page (landing, practice, chat with X-ray and branches, feedback, what-if, real mode,
 * transparency + Guardian) in light and dark mode, and fails if the browser reports any CSP
 * violation, page error or console error. Uses playwright-core from frontend/node_modules and the
 * preinstalled Chromium (CHROMIUM_PATH overrides it).
 */
import { createRequire } from 'node:module';

const require = createRequire(new URL('../frontend/package.json', import.meta.url));
const { chromium } = require('playwright-core');

const BASE = (process.argv[2] ?? 'http://127.0.0.1:7860').replace(/\/$/, '');
const EXECUTABLE = process.env.CHROMIUM_PATH ?? '/opt/pw-browsers/chromium-1194/chrome-linux/chrome';

async function journey(browser, colorScheme) {
  const context = await browser.newContext({ colorScheme, viewport: { width: 1280, height: 900 } });
  await context.addInitScript(() => {
    window.__csp = [];
    document.addEventListener('securitypolicyviolation', (e) =>
      window.__csp.push(`${e.violatedDirective} blocked ${e.blockedURI || 'inline'} (${e.sourceFile}:${e.lineNumber})`),
    );
  });
  const page = await context.newPage();
  const problems = [];
  const visited = [];
  page.on('pageerror', (e) => problems.push(`pageerror: ${e.message}`));
  page.on('console', (m) => {
    const text = m.text();
    if (/Content Security Policy|Refused to/i.test(text)) problems.push(`console CSP: ${text}`);
    else if (m.type() === 'error' && !/Failed to load resource/.test(text)) problems.push(`console error: ${text}`);
  });
  const collect = async () => {
    visited.push(new URL(page.url()).pathname);
    const found = await page.evaluate(() => window.__csp.splice(0));
    problems.push(...found.map((v) => `CSP violation on ${page.url()}: ${v}`));
  };
  // (Not waitForFunction: Playwright evaluates its predicate as a string, which our CSP rightly blocks.)
  const waitIdle = () =>
    page.locator('[role="status"][aria-label*="typing"]').waitFor({ state: 'detached', timeout: 20000 });
  const send = async (text) => {
    await page.fill('[data-testid="composer"]', text);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(150);
    await waitIdle();
  };

  await page.goto(BASE + '/');
  await page.getByTestId('start-practicing').waitFor();
  await collect();

  await page.getByTestId('start-practicing').click();
  await page.getByTestId('scenarios').waitFor();
  await collect();
  await page.locator('[data-testid="scenarios"] button').first().click();
  await page.getByTestId('content-warning').waitFor();
  await page.getByRole('button', { name: /I understand/ }).click();

  await page.waitForURL(/\/chat\//);
  const sessionId = page.url().split('/chat/')[1];
  await page.getByTestId('composer').waitFor();
  await send('hey are you ok? you seemed really off at lunch');
  await send("lol you'll be fine"); // a weak reply, so feedback has a turning point for what-if
  await send('that sounds really hard. are you thinking about killing yourself?');
  await send("i'm really glad you told me. can we talk to the counselor tomorrow? i'll go with you");
  await page.getByTestId('xray-toggle').click();
  await page.locator('[data-testid="xray-helper"]').first().waitFor();
  await page.getByRole('button', { name: 'Branches' }).click();
  await page.getByTestId('tree').waitFor();
  await page.keyboard.press('Escape');
  await collect();

  await page.goto(`${BASE}/feedback/${sessionId}`);
  await page.getByTestId('checkin').waitFor();
  await page.getByRole('radio', { name: /Not great/ }).click();
  await page.getByRole('button', { name: 'Continue' }).click();
  await page.locator('[data-testid="message-card"]').first().waitFor();
  await page.waitForTimeout(500); // charts render
  await collect();

  await page.goto(`${BASE}/whatif/${sessionId}`);
  await page.locator('[data-testid="whatif-path"]').first().waitFor();
  await page.waitForTimeout(500);
  await collect();

  await page.getByTestId('help-now').click();
  await page.getByTestId('primary-line').waitFor();
  await collect();

  await page.goto(`${BASE}/how`);
  await page.getByTestId('guardian-box').waitFor();
  await page.getByTestId('llm-status').locator('dl').waitFor();
  await page.getByRole('button', { name: '“kms”' }).click();
  await page.getByTestId('guardian-result').waitFor();
  await page.waitForTimeout(500);
  await collect();

  const dark = await page.evaluate(() => document.documentElement.classList.contains('dark'));
  await context.close();
  return { colorScheme, visited, problems, darkApplied: dark };
}

const browser = await chromium.launch({ executablePath: EXECUTABLE });
let failed = false;
for (const scheme of ['light', 'dark']) {
  const result = await journey(browser, scheme);
  console.log(JSON.stringify(result));
  if (result.problems.length || result.darkApplied !== (scheme === 'dark')) failed = true;
}
await browser.close();
console.log(failed ? 'CSP CHECK FAILED' : 'CSP CHECK PASSED: zero violations');
process.exit(failed ? 1 : 0);
