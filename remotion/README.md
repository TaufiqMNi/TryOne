# Remotion

Projek Remotion asas untuk video 9:16 (komposisi `Main`: 1080x1920, 30fps, H.264).

Pasang sekali: `npm install` (dalam folder `remotion/`).

```
npm run studio                          # buka Remotion Studio
npx remotion compositions               # senarai komposisi
npm run render -- Main out/main.mp4     # render (hanya selepas pengguna beri kebenaran)
```

## Kad teks B-roll (`Card`)
Port `broll/templates/card.html` — tajuk hook, hadis/ayat Arab, CTA. Props sama dengan `data` kad dalam
`broll/reels/*.json`: `kind` (`title` | `hadith` | `cta`), `lines`, `highlight` (kuning #FFD400), `arabic`,
`source`, `duration` (saat, min 2 — panjang komposisi ikut medan ini), `full` (latar ungu gelap penuh; lalai lutsinar),
`instant` (teks penuh dari frame pertama, untuk hook).

```
npx remotion still Card out/card.png --props=props/card_title.json --frame=48       # semakan satu frame
npm run render -- Card out/card.mp4 --props=props/card_hadith.json                  # selepas kebenaran
npm run render -- Card out/card.mov --props=props/card_cta.json \
  --codec=prores --prores-profile=4444 --image-format=png --pixel-format=yuva444p10le  # lutsinar (full: false)
```
- Contoh props dalam `props/` (dari reel EP6).
- Tambahan ikut v2.0: zoom perlahan 100%→103% sepanjang kad, grain berkelip setiap frame.
- Fon Bebas Neue & Amiri (OFL) dalam `public/fonts/`.

## Struktur
- Kod komposisi dalam `src/` (`Root.tsx` daftar komposisi, `Main.tsx` kandungan).
- `remotion.config.ts` guna Chromium dari `PLAYWRIGHT_BROWSERS_PATH` kalau ada.
- Output render tetap perlu `template/apply_overlay.sh` (lihat `CLAUDE.md`).
- `out/` tak masuk git.
