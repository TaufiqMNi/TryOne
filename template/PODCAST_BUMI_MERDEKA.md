# Template edit: PODCAST BUMI MERDEKA (v1.0)

Diluluskan pengguna pada EP7 Short 01 (22 Okt 2026). Preset mesin: `template/presets/PODCAST_BUMI_MERDEKA.json`.
Gaya ini **mengatasi** `STYLE_GUIDE.md` v2.0 untuk klip Podcast Bumi Merdeka yang pengguna sudah potong sendiri.

## Input daripada pengguna
- Folder Google Drive: `Raw Footage/` (short 9:16 yang **sudah dipotong** — pause, ulangan sudah dibuang),
  MP3 podcast penuh (untuk konteks), dan fail muzik.
- Footage sengaja dinaikkan sedikit: ruang bawah untuk banner. **Jangan ubah komposisi** — tiada crop/zum/anjakan,
  tiada gradien hitam di atas.

## Rupa
| Elemen | Tetapan |
|---|---|
| Output | 1080x1920, ikut fps footage (EP7: 25fps), H.264, audio ~-8 LUFS |
| Shot host | komposisi asal; gerakan halus push-in / push-out 3% bersilih pada setiap potongan pengguna |
| Gred warna | hitam dalam, kulit hangat (tidak oren), highlight baju ditahan, vignette berpusat pada muka, sharpen ringan (`grade` dalam preset) |
| Overlay | `template/overlay_1080x1920.png` (logo + banner Bina Semula Gaza), layer paling atas |
| Kapsyen | Inter Bold 66px, jarak huruf -1, putih, **tiada stroke**, bayang lembut kabur; setiap perkataan baru animasi pop (75%→106%→100%); y≈1356; 1-4 perkataan terkumpul |
| Hook (0-3s) | **Bezakan setiap short** (`hook.style`): `bgswap` host penuh, latar studio diganti B-roll (topeng BiRefNet-portrait `"matting": "birefnet"` — MediaPipe 256px memotong kepala botak; jangan guna `no_hair`) · `type` tipografi Cinzel besar atas B-roll bertekstur, tiada host · `host` wajah host terus, teks hook slam perkataan demi perkataan · `pip` B-roll penuh + host dalam kad PiP bucu bulat. Teks hook (selain `type`): **Inter Black kuning #FFD400, BESAR** (saiz seragam terbesar yang muat 960px), 3-4 baris pendek, tiada stroke; atas muka untuk `pip`, bawah muka (y≈990) untuk `bgswap`/`host` |
| Tajuk / motion graphic | `tpl: "kinetic"` — Cinzel (serif sinematik) atas host yang di-blur + digelap; baris kecil Cormorant Italic (`kicker`); kata kunci emas berkilau; garis emas dilukis. **Bukan** kad ungu penuh skrin |
| B-roll | penuh skrin, bertekstur (grain/paper/halftone/scratches), gerakan perlahan, SFX halus; sumber berlesen (Unsplash) + kredit dalam `ep7/broll_credits.txt` |
| Peta (rujukan APHD) | `tpl: "map"` (`broll/templates/map.html`, data Natural Earth): daratan cerah, laut biru gelap, negara diserlah merah tua (atau `flag`), penanda titik/cincin, laluan, label Bebas atas latar hitam, tajuk besar + sub italic; kamera zum log-linear. Biar konteks sekeliling kelihatan (span tidak terlalu kecil) |
| Keratan berita / buku (rujukan APHD) | `tpl: "news"` (`broll/templates/news.html`): tajuk Bebas bergerak di latar gelap, kad kertas condong dengan masthead (Playfair), tajuk, petikan (Libre Baskerville), marker kuning menyapu frasa. **Teks mesti verbatim dari sumber sebenar** + kredit |
| Chromatic aberration | `chroma: 4` (px) pada semua B-roll, peta dan keratan |
| Penutup | B-roll terang `until_end` — **kekal hingga frame akhir** (tiada fade balik ke host) + riser |
| Muzik | fail pengguna (EP7: CapCut "Crime Investigation. News, reports, mysteries (1646362)"), volume 10%, fade out 2s |

## Aliran kerja (setiap episod)
1. Muat turun folder Drive (`gdown --folder <url>`); salin short ke `broll/work/footage/epN_sK.mp4`, muzik ke `broll/work/music/`.
2. Transkrip (Whisper large-v3, Bahasa Melayu, tanpa VAD) -> `broll/work/epN_sK.words.json`;
   proofread, **tanya pengguna** setiap perkataan/istilah tak pasti -> `broll/reels/epN_sK.fixes.json`.
3. Kesan potongan pengguna (`select='gt(scene,0.08)'`) -> `cuts` dalam config.
4. Config reel `broll/reels/epN_sK.json` (lihat contoh `ep7_s1.json`):
   `{"preset": "PODCAST_BUMI_MERDEKA", "src", "start", "end", "cuts", "hook": {dur, text: [...], image, grade, texture, motion},
   "english": [...], "cues": [...]}`.
5. Cadang hook kepada pengguna, kemudian semakan **screencap satu frame**:
   `STILLS="1.5,20" python3 tools/build_reel.py epN_sK assemble` (tiada render video).
6. Render **hanya selepas pengguna beri kebenaran**:
   `for s in faces plan render audio assemble final; do python3 tools/build_reel.py epN_sK $s; done`
   -> `broll/work/epN_sK_final.mp4`.

## Penambahbaikan seterusnya (permintaan pengguna selepas EP7)
- Pengguna mahu **look grafik baharu** untuk episod akan datang — cth. **glassmorphism** (kad kaca kabur lutsinar atas
  footage), lebih banyak tipografi **kinetik**. Cadangkan 2-3 arah gaya dengan screencap satu frame sebelum render.
