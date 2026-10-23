# B-roll assistant

Alat untuk jana B-roll animasi 1080x1920 ikut `template/STYLE_GUIDE.md` v2.0:
B-roll penuh skrin, warna bebas, **tekstur & gerakan halus wajib**, SFX halus setiap B-roll.
Kad artikel/carian/teks (latar ungu gelap) hanya bila perlu bukti fakta; kad duduk di y 300-1275.

Pasang sekali: `npm install` (dalam folder `broll/`).

## 0. Transkrip
```
pip install faster-whisper   # sekali
python3 tools/transcribe.py <video> work/v1          # -> v1.srt, v1.words.json, v1.txt
python3 tools/fix_transcript.py work/v1 work/v1.fixes.json   # pembetulan proofread, timestamp kekal
```

## 1. B-roll penuh skrin (utama)
```
node tools/render.mjs templates/photo.html work/b1.json work/b1.mp4
```
Data: `image` (relatif folder JSON), `duration`, `grade` (`color` lalai | `bw` | `sepia` | `bright` | `none`, atau `filter` CSS),
`texture` (`grain` | `halftone` | `paper` | `scratches`; kosong -> `grain`), `motion` (`zoom-in` lalai 100%->108% | `zoom-out` |
`pan-left` | `pan-right` | `pan-up` | `pan-down`), `focus` {x,y} 0..1, `calligraphy` (teks Arab samar — tanya pengguna dulu), `source`.

Footage video: `tpl: "footage"` dalam config reel (ffmpeg, tiada Playwright) — data `video` (relatif `work/`), `in`,
`duration`, `grade`, `texture` (grain sentiasa; `halftone`/`paper` ditindih), `motion`, `focus`.

## 1b. Screencap artikel + highlight marker
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
Dirender dengan Remotion — komposisi `Card` dalam `../remotion/` (pasang sekali: `npm install` dalam `remotion/`).
`build_reel.py render` guna Remotion secara automatik untuk cue `tpl: "card"`. Render sendiri:
```
cd ../remotion && npx remotion render Card out/card.mp4 --props=../broll/work/card_hook.json
```
Data: `kind` (`title` | `hadith` | `cta`), `lines`, `highlight` (teks kuning #FFD400), `arabic` (teks atau senarai baris),
`source` (kredit di bawah kad), `duration`, `full` (true = latar ungu gelap penuh; lalai lutsinar untuk tindih atas footage),
`instant` (teks penuh dari frame pertama, untuk hook). Lihat `remotion/README.md`.
`templates/card.html` disimpan sebagai rujukan lama (masih boleh guna `tools/render.mjs`).

## 4. Reel penuh dari klip podcast
Satu konfigurasi setiap reel dalam `reels/<id>.json` (sumber, masa mula/tamat, `hook`, cue B-roll ikut frasa transkrip,
artikel, istilah Inggeris/nama khas/Arab untuk kapsyen) + `reels/<id>.fixes.json` (pembetulan proofread).

Medan v2.0:
- `hook`: `{dur, image, grade, texture, motion}` — B-roll penuh skrin 0-dur + host dalam kad PiP bucu bulat (900x450, y 1000)
  + kapsyen hook kuning besar di atas (y≈460, baris 2 lebih kecil).
- Cue: `tpl` `photo` | `footage` | `highlight` | `google` | `card`; `trans` `flash` (lalai) | `dissolve` | `streak` | `cut`;
  `sfx` `soft` (lalai, whoosh lembut + swell) | `hit` (peralihan besar) | `none`; `riser`; `until_end` untuk imej penutup terang.
- `host_thirds` (lalai true): host di sepertiga kiri/kanan bersilih. `cta` pilihan (tiada lalai).
Letak footage di `work/footage/` (laluan `src` dalam config), kemudian:
```
pip install faster-whisper "opencv-python-headless<5" numpy pillow   # sekali
for s in faces transcribe capture plan vo render audio assemble final; do python3 tools/build_reel.py <id> $s; done
python3 tools/build_reel.py <id> still 12.5      # screencap semakan
```
- Jump cut pada setiap senyap > 0.45s, shot ~2.5s, medium close-up dengan punch-in 1.15/1.3 selang-seli, host di
  sepertiga kiri/kanan bersilih (muka 25-65% tinggi, dagu atas 1450px), gred warna asal studio + kulit hangat +
  vignette ringan, gradien atas tutup logo asal footage.
- Kapsyen terkumpul perkataan demi perkataan (1-4, maks 22 aksara) di y≈1356, putih; Inggeris/Arab italic.
- Bed muzik berterusan + SFX halus setiap B-roll + whoosh/hit/riser peralihan besar, semua disintesis
  (tiada aset berlesen diperlukan); master ~-8 LUFS.
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

## Topeng orang (hook `bgswap`)
Disyorkan: `"matting": "birefnet"` dalam hook (BiRefNet-portrait, ~20s/frame CPU, frame dicache dalam `<out>.frames/`,
boleh sambung semula). Model: `pip install "rembg[cpu]"`, jalankan `rembg` sekali dengan `birefnet-portrait`, pindahkan
`~/.rembg/models/birefnet-portrait/birefnet-portrait.onnx` ke `work/models/`. Laluan MediaPipe (di bawah) lebih laju tapi kasar.

`tools/person_mask.py` guna MediaPipe (`pip install mediapipe`, perlu `libegl1`) + model
`selfie_multiclass_256x256.tflite` di `work/models/`:
`curl -O https://storage.googleapis.com/mediapipe-models/image_segmenter/selfie_multiclass_256x256/float32/latest/selfie_multiclass_256x256.tflite`
