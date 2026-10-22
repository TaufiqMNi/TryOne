#!/usr/bin/env node
// Deterministic frame-by-frame renderer: HTML composition -> MP4.
// The page must expose window.__comp = { duration, width, height, seek(t) }.
// Usage: node render.mjs <comp.html> <out.mp4> [--fps 30] [--workers 4] [--scale 1] [--from 0] [--to <dur>] [--crf 16] [--audio vo.wav] [--jpeg]
//        node render.mjs <comp.html> <out_dir> --stills 0.5,1.2,3   (PNG stills for QA, post FX not applied)
import { chromium } from 'playwright-core';
import { spawn } from 'node:child_process';
import { mkdtempSync, writeFileSync, rmSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { pathToFileURL } from 'node:url';

const args = process.argv.slice(2);
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const [compPath, outPath] = args.filter((a, i) => !a.startsWith('--') && !(args[i - 1] || '').startsWith('--'));
if (!compPath || !outPath) { console.error('usage: node render.mjs comp.html out.mp4 [--fps 30] [--workers 4]'); process.exit(1); }

const FPS = +opt('fps', 30);
const WORKERS = +opt('workers', 4);
const SCALE = +opt('scale', 1);          // 2 = render at 2x pixel density (4K from a 1080p layout)
const CRF = opt('crf', '16');
const EXE = ['/opt/pw-browsers/chromium-1194/chrome-linux/chrome', process.env.CHROMIUM_PATH].find(p => p && existsSync(p));
const JPEG = args.includes('--jpeg');   // faster, visually lossless at q95
const url = pathToFileURL(path.resolve(compPath)).href;

// Film-look post FX done in ffmpeg (fast + keeps PNG capture compressible).
// post = { grain: 0-30 (noise strength), rgb: px chromatic split, vignette: 0-1, blur: px softness }
function postFilters(post, w, h, f0) {
  const f = [];
  if (post.blur) f.push(`gblur=sigma=${post.blur}`);
  if (post.rgb) f.push(`rgbashift=rh=${-Math.round(post.rgb * SCALE)}:bh=${Math.round(post.rgb * SCALE * 1.1)}`);   // v5: horizontal-only split
  if (post.vignette) f.push(`vignette=angle=${(0.3 + post.vignette * 0.5).toFixed(2)}`);
  if (post.grain) f.push(`noise=alls=${post.grain}:allf=t:all_seed=${1000 + f0}`);
  return f.join(',');
}

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: SCALE });
  page.on('console', m => m.type() === 'error' && console.error('[page]', m.text()));
  page.on('pageerror', e => console.error('[page error]', e.message));
  await page.goto(url, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__comp && window.__comp.ready, null, { timeout: 30000 });
  const info = await page.evaluate(() => ({ w: __comp.width, h: __comp.height, d: __comp.duration, post: __comp.post || {} }));
  await page.setViewportSize({ width: info.w, height: info.h });
  await page.evaluate(() => document.fonts.ready);
  return { page, info };
}

async function renderRange(browser, f0, f1, file) {
  const { page, info } = await openPage(browser);
  const cdp = await page.context().newCDPSession(page);
  const vf = postFilters(info.post, info.w * SCALE, info.h * SCALE, f0);
  const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', JPEG ? 'mjpeg' : 'png', '-i', '-',
    ...(vf ? ['-vf', vf] : []), '-c:v', 'libx264', '-preset', 'medium', '-crf', CRF, '-pix_fmt', 'yuv420p', file], { stdio: ['pipe', 'inherit', 'inherit'] });
  const shot = JPEG ? { format: 'jpeg', quality: 95, optimizeForSpeed: true } : { format: 'png', optimizeForSpeed: true };
  for (let f = f0; f < f1; f++) {
    await page.evaluate(t => __comp.seek(t), f / FPS);
    const { data } = await cdp.send('Page.captureScreenshot', { ...shot, clip: { x: 0, y: 0, width: info.w, height: info.h, scale: 1 } });
    const buf = Buffer.from(data, 'base64');
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (f0 === 0 && (f - f0) % 60 === 0) process.stdout.write(`\r  frame ${f}/${f1}`);
  }
  ff.stdin.end();
  await new Promise((res, rej) => ff.on('close', c => c ? rej(new Error('ffmpeg ' + c)) : res()));
  await page.close();
}

const t0 = Date.now();
const browser = await chromium.launch({ executablePath: EXE, args: ['--disable-web-security', '--allow-file-access-from-files', '--font-render-hinting=none'] });
const { page, info } = await openPage(browser);
if (opt('stills')) {
  const { mkdirSync } = await import('node:fs');
  mkdirSync(outPath, { recursive: true });
  for (const t of opt('stills').split(',').map(Number)) {
    await page.evaluate(t => __comp.seek(t), t);
    await page.screenshot({ path: path.join(outPath, `t${t.toFixed(2).padStart(6, '0')}.png`) });
  }
  await browser.close(); console.log(`stills -> ${outPath}`); process.exit(0);
}
await page.close();
const from = +opt('from', 0), to = +opt('to', info.d);
const F0 = Math.round(from * FPS), F1 = Math.round(to * FPS), N = F1 - F0;
console.log(`${path.basename(compPath)}: ${info.w}x${info.h} @${FPS}fps x${SCALE}, ${N} frames, ${WORKERS} workers`);

const tmp = mkdtempSync(path.join(tmpdir(), 'vox-'));
const per = Math.ceil(N / WORKERS);
const parts = [];
for (let i = 0; i < WORKERS && F0 + i * per < F1; i++) parts.push([F0 + i * per, Math.min(F1, F0 + (i + 1) * per), path.join(tmp, `p${i}.mp4`)]);
await Promise.all(parts.map(([a, b, f]) => renderRange(browser, a, b, f)));
await browser.close();

writeFileSync(path.join(tmp, 'list.txt'), parts.map(p => `file '${p[2]}'`).join('\n'));
const audio = opt('audio');
const cat = ['-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', path.join(tmp, 'list.txt')];
if (audio) cat.push('-i', audio, '-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-shortest');
cat.push('-c:v', 'copy', '-movflags', '+faststart', outPath);
await new Promise((res, rej) => spawn('ffmpeg', cat, { stdio: 'inherit' }).on('close', c => c ? rej(new Error('concat ' + c)) : res()));
rmSync(tmp, { recursive: true, force: true });
console.log(`done -> ${outPath} in ${((Date.now() - t0) / 1000).toFixed(1)}s`);
