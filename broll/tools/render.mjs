// Render templat HTML animasi -> MP4 1080x1920 30fps.
// Templat mesti sediakan window.DURATION (saat) dan window.seek(t).
// Guna: node render.mjs <templat.html> <data.json> <out.mp4>
import { chromium } from 'playwright';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const [tpl, dataFile, out] = process.argv.slice(2);
const data = JSON.parse(fs.readFileSync(dataFile, 'utf8'));
const FPS = data.fps || 30;
const alpha = !!data.alpha;   // latar lutsinar -> .mov qtrle (ARGB) untuk ditindih atas footage
data.baseDir = 'file://' + path.resolve(path.dirname(dataFile)) + '/';

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
await page.addInitScript(d => { window.DATA = d; }, data);
await page.goto('file://' + path.resolve(tpl));
await page.evaluate(() => document.fonts.ready);
await page.waitForFunction(() => window.READY === true, null, { timeout: 15000 });
const dur = await page.evaluate(() => window.DURATION);

const enc = alpha ? ['-c:v', 'qtrle', '-pix_fmt', 'argb'] : ['-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p'];
const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-i', '-',
  ...enc, '-r', String(FPS), out], { stdio: ['pipe', 'inherit', 'inherit'] });
const frames = Math.round(dur * FPS);
for (let f = 0; f < frames; f++) {
  await page.evaluate(t => window.seek(t), f / FPS);
  const buf = await page.screenshot(alpha ? { type: 'png', omitBackground: true } : { type: 'jpeg', quality: 92 });
  if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
}
ff.stdin.end();
await new Promise(r => ff.on('close', r));
await browser.close();
console.log('ok', out, frames, 'frame');
