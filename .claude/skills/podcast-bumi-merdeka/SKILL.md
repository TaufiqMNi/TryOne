---
name: podcast-bumi-merdeka
description: Edit klip pendek 9:16 Podcast Bumi Merdeka dengan template "PODCAST BUMI MERDEKA" (footage sudah dipotong pengguna, komposisi asal, kapsyen lembut Inter Bold, hook Inter Black besar, tajuk kinetik sinematik, muzik pengguna 10%). Guna bila pengguna minta edit short/reel Bumi Merdeka atau sebut template "PODCAST BUMI MERDEKA".
---

# Template PODCAST BUMI MERDEKA

Baca dahulu `template/PODCAST_BUMI_MERDEKA.md` (spesifikasi gaya + aliran kerja) dan `CLAUDE.md` (peraturan tetap).
Preset mesin: `template/presets/PODCAST_BUMI_MERDEKA.json` — setiap config reel cukup dengan `"preset": "PODCAST_BUMI_MERDEKA"`
serta `src`, `start`, `end`, `cuts`, `hook`, `english`, `cues` (contoh: `broll/reels/ep7_s1.json`).

Langkah ringkas:
1. Minta / guna link Google Drive pengguna: `Raw Footage/` (short sudah dipotong), MP3 podcast penuh, fail muzik.
2. Transkrip & proofread; **tanya pengguna** setiap perkataan tak pasti sebelum kapsyen dimuktamadkan.
3. Cadang hook (2-4 baris pendek) + pelan B-roll / tajuk kinetik ikut kata kunci; sumber gambar berlesen sahaja.
4. Semakan guna screencap satu frame (`STILLS=...`). **Jangan render video sebelum pengguna beri kebenaran.**
5. Selepas kebenaran: render, semak frame video siap, hantar kepada pengguna, commit & push.

Jangan: crop/zum footage host, gradien hitam di atas, kad ungu penuh skrin, stroke pada teks, fade penutup balik ke host.
