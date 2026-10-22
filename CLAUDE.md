# Projek video pendek 9:16

## Template tersimpan
- **PODCAST BUMI MERDEKA** — lalai untuk klip Podcast Bumi Merdeka yang pengguna sudah potong sendiri:
  `template/PODCAST_BUMI_MERDEKA.md` + preset `template/presets/PODCAST_BUMI_MERDEKA.json`
  (config reel: `"preset": "PODCAST_BUMI_MERDEKA"`; skill `/podcast-bumi-merdeka`). Mengatasi STYLE_GUIDE v2.0 di mana berbeza.

## Peraturan tetap untuk SETIAP video
1. Edit ikut gaya dalam `template/STYLE_GUIDE.md` (v2.0, dari video rujukan kedua), atau template tersimpan di atas.
2. Output akhir: 1080x1920, 30fps (template PODCAST BUMI MERDEKA: ikut fps footage), H.264, audio ~-8 LUFS.
3. **Wajib** tampal overlay logo + banner sebagai layer paling atas:
   `template/apply_overlay.sh input.mp4 output.mp4`
   (overlay: `template/overlay_1080x1920.png`, kedudukan dalam `template/README.md`).
4. Kapsyen tengah di y≈1356 (~70%), jangan bertindih banner (y≥1471) atau logo bar (y 220-275).
5. Framing host: muka antara 25-65% tinggi, dagu di atas ~1450px.
6. **Jangan render pratonton (video atau klip ujian) selagi pengguna belum beri kebenaran untuk proceed.** Semakan guna screencap satu frame.
7. **Kapsyen: kalau ada perkataan atau istilah yang tak pasti (nama, organisasi, tempat, istilah, slang, ejaan), tanya pengguna dulu — jangan teka.**

## Aliran kerja
- Transkrip & B-roll → ikut seksyen 10 & 11 dalam `template/STYLE_GUIDE.md`.
- Alat transkrip & B-roll: `broll/` (lihat `broll/README.md`).

## Tukar logo / banner
Ganti fail dalam `template/assets/` (nama fail sama), kemudian:
`python3 template/build_overlay.py template/ template/assets/`
