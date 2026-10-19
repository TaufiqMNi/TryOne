# B-roll assistant (draf, belum dimuktamadkan)

Alat untuk jana B-roll animasi 1080x1920 ikut gaya `template/STYLE_GUIDE.md`
(kad bucu bulat atas hitam + vignette, marker kuning #FFD400). Kad duduk di y 300-1275,
jadi zon logo, kapsyen (~1356) dan banner (≥1471) kekal kosong.

Pasang sekali: `npm install` (dalam folder `broll/`).

## 1. Screencap artikel + highlight marker
```
node tools/capture_article.mjs <url> "<frasa tepat dari artikel>" work/art1
node tools/render.mjs templates/highlight.html work/art1.json work/highlight_art1.mp4
```
Animasi: kad masuk → tunjuk tajuk → pan/zoom ke ayat → marker sapu baris demi baris → Ken Burns perlahan.
Kredit sumber automatik di bawah kad.

## 2. Carian gaya Google
```
node tools/render.mjs templates/google.html samples/google_example.json work/google1.mp4
```
Data: `query`, `results` (site, url, title, snippet pilihan), `highlight` (indeks hasil untuk marker).
Isi hasil carian dengan tajuk/URL sebenar — jangan reka.

## Nota
- Sesetengah laman sekat bot (cth. Reuters, Pexels) — guna sumber lain.
- Footage berita berhak cipta: beri link + timestamp sahaja, muat turun manual.
- `work/` tak masuk git.
