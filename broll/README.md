# B-roll assistant (draf, belum dimuktamadkan)

Alat untuk jana B-roll animasi 1080x1920 ikut gaya `template/STYLE_GUIDE.md`
(kad bucu bulat atas hitam + vignette, marker kuning #FFD400). Kad duduk di y 300-1275,
jadi zon logo, kapsyen (~1356) dan banner (≥1471) kekal kosong.

Pasang sekali: `npm install` (dalam folder `broll/`).

## 0. Transkrip
```
pip install faster-whisper   # sekali
python3 tools/transcribe.py <video> work/v1          # -> v1.srt, v1.words.json, v1.txt
python3 tools/fix_transcript.py work/v1 work/v1.fixes.json   # pembetulan proofread, timestamp kekal
```

## 1. Screencap artikel + highlight marker
```
node tools/capture_article.mjs <url> "<frasa tepat dari artikel>" work/art1
node tools/render.mjs templates/highlight.html work/art1.json work/highlight_art1.mp4
```
Animasi: kad masuk → tunjuk tajuk → pan/zoom ke ayat → marker sapu baris demi baris → Ken Burns perlahan.
Kredit sumber automatik di bawah kad. Tambah `"duration": 2.5` dalam JSON untuk ikut panjang cue.

## 2. Carian gaya Google
```
node tools/render.mjs templates/google.html samples/google_example.json work/google1.mp4
```
Data: `query`, `results` (site, url, title, snippet pilihan), `highlight` (indeks hasil untuk marker).
Isi hasil carian dengan tajuk/URL sebenar — jangan reka.

## 3. Kad teks (tajuk hook, hadis/ayat Arab, CTA)
```
node tools/render.mjs templates/card.html work/card_hook.json work/card_hook.mp4
```
Data: `kind` (`title` | `hadith` | `cta`), `lines`, `highlight` (teks kuning #FFD400), `arabic` (teks atau senarai baris),
`source` (kredit di bawah kad), `duration`, `full` (true = latar hitam penuh; lalai lutsinar untuk tindih atas footage).
Fon: Bebas Neue (tajuk) & Amiri (Arab) dalam `fonts/` (OFL).

## Semakan satu frame
```
node tools/still.mjs <templat.html> <data.json> <out.png> [saat]
```
Screencap satu frame sahaja — guna untuk semakan sebelum pengguna benarkan render.

## Nota
- Sesetengah laman sekat bot (cth. Reuters, Pexels) — guna sumber lain.
- Footage berita berhak cipta: beri link + timestamp sahaja, muat turun manual.
- `work/` tak masuk git.
