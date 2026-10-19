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

## 4. Reel penuh dari klip podcast
Satu konfigurasi setiap reel dalam `reels/<id>.json` (sumber, masa mula/tamat, cue B-roll ikut frasa transkrip,
artikel, istilah Inggeris/nama khas/Arab untuk kapsyen) + `reels/<id>.fixes.json` (pembetulan proofread).
Letak footage di `work/footage/` (laluan `src` dalam config), kemudian:
```
pip install faster-whisper "opencv-python-headless<5" numpy pillow   # sekali
for s in faces transcribe capture plan vo render audio assemble final; do python3 tools/build_reel.py <id> $s; done
python3 tools/build_reel.py <id> still 12.5      # screencap semakan
```
- Jump cut pada setiap senyap > 0.45s, shot ~2.5s dengan punch-in 1.0/1.15 selang-seli, crop 9:16 ikut muka
  (muka 25-65% tinggi, dagu atas 1450px), gred low-key + vignette, gradien atas tutup logo asal footage.
- Kapsyen 2-4 perkataan (maks 22 aksara) di y≈1356; istilah Inggeris kuning #FFD400 italic.
- Bed muzik ambient + whoosh/hit/riser disintesis (tiada aset berlesen diperlukan); master ~-8 LUFS.
- Langkah `vo` transkrip semula audio suntingan supaya masa kapsyen tepat; `src_windows` ambil semula bahagian
  yang Whisper tertinggal (cth. bacaan Arab), `tail_words` sematkan perkataan akhir.
- Contoh: `reels/ep6_c1.json`, `reels/ep6_c2.json` (Podcast Bumi Merdeka EP6, perjanjian damai Gaza).

## Semakan satu frame
```
node tools/still.mjs <templat.html> <data.json> <out.png> [saat]
```
Screencap satu frame sahaja — guna untuk semakan sebelum pengguna benarkan render.

## Nota
- Sesetengah laman sekat bot (cth. Reuters, Pexels) — guna sumber lain.
- Footage berita berhak cipta: beri link + timestamp sahaja, muat turun manual.
- `work/` tak masuk git.
