#!/usr/bin/env node
/**
 * Drive a running web build of the app with Playwright and save real screen
 * captures for store screenshots.
 *
 *   node capture_screens.cjs capture.config.json
 *
 * Config (paths relative to the config file):
 * {
 *   "baseUrl": "http://localhost:8090",
 *   "outDir": "captures",
 *   "viewport": { "width": 390, "height": 797 },   // phone height minus the 47pt status bar
 *   "scale": 3,
 *   "colorScheme": "light",
 *   "dismissAfterGoto": ["get started"],            // regexes clicked if present after each goto
 *   "steps": [
 *     { "goto": "/calculators/refill-date" },
 *     { "click": "calculate refill timeline" },       // case-insensitive regex, first match
 *     { "clickExact": "90" },                         // exact text match
 *     { "fill": { "label": "Days supply", "value": "30" } },
 *     { "scrollTo": "^Coverage timeline$", "offset": 20, "nth": 0 },
 *     { "scrollBy": 600 },
 *     { "closeIfPresent": "^done$" },
 *     { "colorScheme": "dark" },
 *     { "wait": 800 },
 *     { "shot": "refill-timeline" }
 *   ]
 * }
 *
 * Playwright: uses `playwright-core` or `playwright` resolvable from the current
 * directory, or the path in PLAYWRIGHT_CORE. Browser: config.browserPath,
 * CHROME_PATH, a system Chrome/Chromium, or Playwright's bundled browser.
 */
const fs = require('fs');
const path = require('path');

function loadPlaywright() {
  const tries = [process.env.PLAYWRIGHT_CORE, 'playwright-core', 'playwright'].filter(Boolean);
  for (const t of tries) {
    try {
      return require(require.resolve(t, { paths: [process.cwd(), __dirname] }));
    } catch {}
  }
  console.error('playwright-core not found. Install it somewhere outside the app, e.g.\n  mkdir -p /tmp/pw && cd /tmp/pw && npm i playwright-core\nthen run with PLAYWRIGHT_CORE=/tmp/pw/node_modules/playwright-core');
  process.exit(1);
}

function findBrowser(configured) {
  const candidates = [
    configured,
    process.env.CHROME_PATH,
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium-browser',
    '/usr/bin/chromium',
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  ].filter(Boolean);
  return candidates.find((p) => fs.existsSync(p));
}

(async () => {
  const configPath = process.argv[2];
  if (!configPath) {
    console.error('usage: node capture_screens.cjs capture.config.json');
    process.exit(1);
  }
  const cfg = JSON.parse(fs.readFileSync(configPath, 'utf8'));
  const base = path.dirname(path.resolve(configPath));
  const outDir = path.resolve(base, cfg.outDir || 'captures');
  fs.mkdirSync(outDir, { recursive: true });

  const { chromium } = loadPlaywright();
  const executablePath = findBrowser(cfg.browserPath);
  const browser = await chromium.launch({ headless: true, ...(executablePath ? { executablePath } : {}) });
  const ctx = await browser.newContext({
    viewport: cfg.viewport || { width: 390, height: 797 },
    deviceScaleFactor: cfg.scale || 3,
    colorScheme: cfg.colorScheme || 'light',
  });
  const page = await ctx.newPage();
  page.on('pageerror', (e) => console.log('  [pageerror]', e.message));

  const re = (s) => new RegExp(s, 'i');
  const wait = (ms) => page.waitForTimeout(ms);
  const settle = cfg.settleMs ?? 700;

  const dismiss = async () => {
    for (const d of cfg.dismissAfterGoto || []) {
      const loc = page.getByText(re(d));
      if (await loc.count()) {
        await loc.first().click();
        await wait(1200);
      }
    }
  };

  const scrollTo = async (text, offset = 24, nth = 0) => {
    const el = page.getByText(re(text)).nth(nth);
    await el.waitFor({ timeout: 15000 });
    await el.evaluate((node, off) => {
      let p = node.parentElement;
      while (p && !(p.scrollHeight > p.clientHeight + 4 && getComputedStyle(p).overflowY !== 'visible')) p = p.parentElement;
      const scroller = p || document.scrollingElement;
      const top = node.getBoundingClientRect().top - (p ? p.getBoundingClientRect().top : 0) + scroller.scrollTop - off;
      scroller.scrollTop = top;
    }, offset);
    await wait(500);
  };

  let i = 0;
  for (const step of cfg.steps) {
    i += 1;
    const label = JSON.stringify(step);
    try {
      if (step.goto !== undefined) {
        await page.goto(cfg.baseUrl.replace(/\/$/, '') + step.goto, { waitUntil: 'networkidle', timeout: 120000 });
        await wait(cfg.gotoWaitMs ?? 1500);
        if (!step.noDismiss) await dismiss();
      } else if (step.click !== undefined) {
        await page.getByText(re(step.click)).nth(step.nth || 0).click();
        await wait(settle);
      } else if (step.clickExact !== undefined) {
        await page.getByText(step.clickExact, { exact: true }).nth(step.nth || 0).click();
        await wait(settle);
      } else if (step.fill) {
        await page.getByLabel(re(step.fill.label)).first().fill(String(step.fill.value));
        await wait(300);
      } else if (step.scrollTo !== undefined) {
        await scrollTo(step.scrollTo, step.offset, step.nth);
      } else if (step.scrollBy !== undefined) {
        await page.mouse.move((cfg.viewport?.width || 390) / 2, (cfg.viewport?.height || 797) / 2);
        await page.mouse.wheel(0, step.scrollBy);
        await wait(500);
      } else if (step.closeIfPresent !== undefined) {
        const loc = page.getByText(re(step.closeIfPresent));
        if (await loc.count()) {
          await loc.last().click();
          await wait(500);
        }
      } else if (step.colorScheme) {
        await page.emulateMedia({ colorScheme: step.colorScheme });
        await wait(1200);
      } else if (step.wait) {
        await wait(step.wait);
      } else if (step.shot) {
        const file = path.join(outDir, step.shot + '.png');
        await page.screenshot({ path: file });
        console.log('shot', path.relative(process.cwd(), file));
      } else {
        console.log('  unknown step', label);
      }
    } catch (err) {
      await page.screenshot({ path: path.join(outDir, `_failed-step-${i}.png`) }).catch(() => {});
      console.error(`step ${i} failed: ${label}\n  ${err.message.split('\n')[0]}\n  saved _failed-step-${i}.png`);
      await browser.close();
      process.exit(1);
    }
  }
  await browser.close();
})();
