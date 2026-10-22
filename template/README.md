# Template overlay video (9:16)

Overlay tetap (logo + banner) untuk setiap video. Kapsyen dan gaya edit ikut rujukan pertama.

## Kedudukan (kanvas 1080x1920)

| Elemen | x | y | Saiz |
|---|---|---|---|
| SIYASEE | 91 | 235 | 134x22 |
| HALUAN | 262 | 222 | 48x48 |
| LANGITILAHI | 340 | 226 | 174x41 |
| podcast bumimerdeka | 802 (rata kanan, margin 100) | 221 | 178x50 |
| Banner iklan | 0 | 1471 | 1080x449 (rata bawah) |

- Semua logo sejajar pada garis tengah y=246.
- Gradient gelap halus 0-380px di atas untuk bacaan logo.
- Kapsyen: tengah, y≈1356 (~70%), mesti di atas banner (y<1471).
- Framing: dagu host di atas ~1450px supaya tak tertutup banner.

## Fail
- `overlay_1080x1920.png` — overlay lutsinar siap guna (import terus ke CapCut/Premiere sebagai layer paling atas).
- `apply_overlay.sh input.mp4 output.mp4` — tampal overlay guna ffmpeg.
- `build_overlay.py` — jana semula overlay kalau logo/banner ditukar (`python3 build_overlay.py ./ assets/`).
- `preview.jpg` — contoh hasil.
