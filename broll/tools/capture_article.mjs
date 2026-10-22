// Screencap artikel: keratan dari tajuk (h1) hingga frasa penting + kedudukan frasa.
// Guna: node capture_article.mjs <url> "<frasa tepat dari artikel>" <out_prefix>
// Hasil: <out_prefix>.png dan <out_prefix>.json (kotak tajuk & frasa, piksel imej)
import { chromium } from 'playwright';
import fs from 'node:fs';

const [url, phrase, out] = process.argv.slice(2);
const W = 430, SCALE = 2.5;   // lebar mobile -> imej 1075px

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: W, height: 900 }, deviceScaleFactor: SCALE,
  userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
});
await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
await page.waitForTimeout(2500);

const info = await page.evaluate((phrase) => {
  // 1. Bersihkan: popup, cookie, newsletter, iklan, nav
  const junk = 'form,iframe,aside,nav,header,footer,video,[role=dialog],[aria-modal],' +
    '[id*=cookie i],[class*=cookie i],[class*=consent i],[class*=newsletter i],[class*=subscribe i],' +
    '[class*=promo i],[class*=advert i],[class*=ad-slot i],[id*=ad- i],[class*=paywall i],[class*=share i],[class*=social i]';
  document.querySelectorAll(junk).forEach(e => { if (!e.querySelector('h1')) e.remove(); });
  for (const el of document.querySelectorAll('body *')) {
    const s = getComputedStyle(el);
    if (s.position === 'fixed' || s.position === 'sticky') el.remove();
  }
  // buang bekas kosong yang tinggi (slot iklan)
  for (const el of document.querySelectorAll('div,section')) {
    if (el.offsetHeight > 80 && !el.innerText.trim() && !el.querySelector('img,picture,svg')) el.remove();
  }

  // 2. Cari frasa (abaikan huruf besar/kecil & ruang)
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  const nodes = []; let text = '';
  while (walker.nextNode()) { const n = walker.currentNode; nodes.push([n, text.length]); text += n.data; }
  let normText = ''; const map = [];
  for (let i = 0; i < text.length; i++) {
    const c = /\s/.test(text[i]) ? ' ' : text[i].toLowerCase();
    if (c === ' ' && normText.endsWith(' ')) continue;
    normText += c; map.push(i);
  }
  const at = normText.indexOf(phrase.replace(/\s+/g, ' ').toLowerCase());
  if (at < 0) return null;
  const locate = off => { for (let k = nodes.length - 1; k >= 0; k--) if (nodes[k][1] <= off) return [nodes[k][0], off - nodes[k][1]]; };
  const [sn, so] = locate(map[at]);
  const [en, eo] = locate(map[at + phrase.replace(/\s+/g, ' ').length - 1]);
  const r = document.createRange(); r.setStart(sn, so); r.setEnd(en, eo + 1);

  // 3. Koordinat halaman (bukan viewport)
  const sx = scrollX, sy = scrollY;
  const boxes = [...r.getClientRects()].filter(b => b.width > 2).map(b => ({ x: b.x + sx, y: b.y + sy, w: b.width, h: b.height }));
  const h1 = document.querySelector('h1');
  const hb = h1 && h1.getBoundingClientRect();
  const title = hb ? { x: hb.x + sx, y: hb.y + sy, w: hb.width, h: hb.height } : null;
  return { boxes, title, pageH: document.documentElement.scrollHeight };
}, phrase);
if (!info) { console.error('Frasa tak dijumpai dalam artikel'); process.exit(2); }

const pTop = Math.min(...info.boxes.map(b => b.y));
const pBot = Math.max(...info.boxes.map(b => b.y + b.h));
// mula dari tajuk kalau dekat (<1400px css), kalau tak mula sedikit atas frasa
const top = Math.max(0, (info.title && pTop - info.title.y < 1400 ? info.title.y : pTop - 260) - 40);
const bottom = Math.min(info.pageH, pBot + 420);
await page.screenshot({ path: out + '.png', fullPage: true, clip: { x: 0, y: top, width: W, height: bottom - top } });

const px = b => b && { x: b.x * SCALE, y: (b.y - top) * SCALE, w: b.w * SCALE, h: b.h * SCALE };
fs.writeFileSync(out + '.json', JSON.stringify({
  image: out.split('/').pop() + '.png', url, phrase, width: W * SCALE, height: Math.round((bottom - top) * SCALE),
  title: px(info.title && info.title.y >= top ? info.title : null), boxes: info.boxes.map(px),
}, null, 2));
console.log('ok', out + '.png', info.boxes.length, 'baris');
await browser.close();
