// Screencap satu frame templat (untuk semakan — tiada render video).
// Guna: node still.mjs <templat.html> <data.json> <out.png> [saat]
import { chromium } from 'playwright';
import fs from 'node:fs';
import path from 'node:path';

const [tpl, dataFile, out, at] = process.argv.slice(2);
const data = JSON.parse(fs.readFileSync(dataFile, 'utf8'));
data.baseDir = 'file://' + path.resolve(path.dirname(dataFile)) + '/';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.addInitScript(d => { window.DATA = d; }, data);
await page.goto('file://' + path.resolve(tpl));
await page.waitForFunction(() => window.READY === true, null, { timeout: 15000 });
const t = at !== undefined ? Number(at) : await page.evaluate(() => window.DURATION * 0.7);
await page.evaluate(t => window.seek(t), t);
await page.screenshot({ path: out, omitBackground: true });
await browser.close();
console.log('ok', out, 't=' + t);
