/**
 * Full-page screenshot that renders like a real (tall) browser window.
 *
 * Playwright's `fullPage: true` capture in Chromium sometimes styles the page as if the viewport were
 * narrow (min-width media queries and vw units briefly fail), so a big headline can come out at its
 * small-screen size in the PNG even though the live page is correct. Instead we grow the viewport to
 * the page's height, take a normal screenshot, and put the viewport back.
 */
export async function screenshot(page, path, full = false) {
  if (!full) return page.screenshot({ path });
  const viewport = page.viewportSize();
  const height = await page.evaluate(() => Math.ceil(document.documentElement.scrollHeight));
  await page.setViewportSize({ width: viewport.width, height: Math.max(viewport.height, height) });
  await page.waitForTimeout(250);
  try {
    return await page.screenshot({ path });
  } finally {
    await page.setViewportSize(viewport);
  }
}
