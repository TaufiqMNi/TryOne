# Remotion

Projek Remotion asas untuk video 9:16 (komposisi `Main`: 1080x1920, 30fps, H.264).

Pasang sekali: `npm install` (dalam folder `remotion/`).

```
npm run studio                          # buka Remotion Studio
npx remotion compositions               # senarai komposisi
npm run render -- Main out/main.mp4     # render (hanya selepas pengguna beri kebenaran)
```

- Kod komposisi dalam `src/` (`Root.tsx` daftar komposisi, `Main.tsx` kandungan).
- `remotion.config.ts` guna Chromium dari `PLAYWRIGHT_BROWSERS_PATH` kalau ada.
- Output render tetap perlu `template/apply_overlay.sh` (lihat `CLAUDE.md`).
- `out/` tak masuk git.
