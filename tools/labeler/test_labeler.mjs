// Headless smoke test for the labeler. Run: node tools/labeler/test_labeler.mjs (PLAYWRIGHT_PATH overrides the module path)
import { createRequire } from "node:module";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_PATH || "/opt/node22/lib/node_modules/playwright");
const here = path.dirname(fileURLToPath(import.meta.url));
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "labeler-"));
const L = ["checked_in","validated","asked_directly","encouraged_help","referred_adult","referred_988","follow_up","dismissed","advice_dump","promised_secrecy"];
const mk = (t) => Object.fromEntries(L.map((l) => [l, t.includes(l)]));
const rows = [
  { id: "t1", kind: "disagreement", scenario_id: "group-chat", level: 1, context: ["idc", "whatever"], text: "u ok??", intended: mk(["checked_in"]), blind: mk(["checked_in", "validated"]), disagree: ["validated"] },
  { id: "t2", kind: "audit", scenario_id: "new-school", level: 3, context: ["hi haha"], text: "I promise I won't tell anyone.", intended: mk(["promised_secrecy"]), blind: mk(["promised_secrecy"]), disagree: [] },
];
const q = path.join(tmp, "queue.jsonl");
fs.writeFileSync(q, rows.map((r) => JSON.stringify(r)).join("\n") + "\n");

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || "/opt/pw-browsers/chromium-1194/chrome-linux/chrome" });
const ctx = await browser.newContext({ viewport: { width: 390, height: 800 }, acceptDownloads: true });
const page = await ctx.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
await page.goto("file://" + path.join(here, "index.html"));
await page.setInputFiles("#qfile", q);
const ok = (c, m) => { if (!c) { console.error("FAIL:", m); process.exit(1); } };
ok((await page.textContent("#reply")) === "u ok??", "first reply shown");
ok((await page.locator("button.lab.on").count()) === 1, "only agreed label pre-checked (checked_in)");
ok((await page.locator("button.lab.dis").count()) === 1, "disagreement highlighted");
await page.keyboard.press("2"); // toggle validated on (human decides yes)
await page.keyboard.press("Enter");
ok((await page.textContent("#reply")).includes("promise"), "advanced to row 2");
await page.locator("button.lab", { hasText: "dismissed" }).click(); // tap works
await page.keyboard.press("0"); // toggle promised_secrecy off
await page.keyboard.press("b");
ok((await page.locator("button.lab.on").count()) === 2, "back restores saved labels for row 1");
await page.keyboard.press("Enter");
await page.keyboard.press("Enter");
const [dl] = await Promise.all([page.waitForEvent("download"), page.click("#export")]);
const out = fs.readFileSync(await dl.path(), "utf8").trim().split("\n").map((s) => JSON.parse(s));
ok(out.length === 2 && out[0].labels.validated && out[0].labels.checked_in, "row 1 exported");
ok(out[1].labels.dismissed && !out[1].labels.promised_secrecy, "row 2 exported with edits");
ok(out[0].label_source === "human", "label_source human");
// autosave survives reload
await page.reload();
await page.setInputFiles("#qfile", q);
ok(/2 labeled/.test(await page.textContent("#prog")), "progress autosaved in localStorage");
ok(errors.length === 0, "no page errors: " + errors.join(";"));
await browser.close();
console.log("labeler: OK");
