# Muwasafat Muslim · intro siri

Video faceless 9:16 (1080×1920, ~53 s) gaya Vox kertas-kolaj (Look D, kinetic vertical).

| Fail | Isi |
|---|---|
| `storyboard.html` | Storyboard 10 scene yang diluluskan |
| `intro.html` | Komposisi animasi (HTML + GSAP, enjin `engine/vox.js`) |
| `vo/take1.mp3` | VO terpilih (ElevenLabs, suara Shahrul – Natural Podcast Host) |
| `vo/words.json` | Masa setiap perkataan VO, semua gerakan dikunci pada masa ini |
| `vo/mix.wav` | VO + SFX, dinormalkan ke -14 LUFS |
| `sfx/raw/` | SFX ElevenLabs (pop, kertas, pen, cop, mangga) |
| `assets/albanna-outline.png` | Cut-out hitam-putih Imam Hassan Al-Banna dengan garis kuning |
| `out/muwasafat-intro.mp4` | Video akhir |

## Render semula

```bash
cd engine && npm install                 # sekali sahaja (playwright-core)
cd .. && python3 tools/mix.py            # bina vo/mix.wav
cd engine && node render.mjs ../intro.html ../qa --stills 5,18,30   # semak gambar pegun
node render.mjs ../intro.html ../out/muwasafat-intro.mp4 --fps 30 --workers 4 --audio ../vo/mix.wav
```

Pratonton dalam browser: buka `intro.html?play` (atau `?t=18.5` untuk satu frame).
