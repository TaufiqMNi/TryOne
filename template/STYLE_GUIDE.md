# Brand guideline & style guide — v2.0 (muktamad, 20 Okt 2026)

Diganti dari v1.0 berdasarkan video rujukan kedua (klip podcast bumi merdeka, 65s).

## 1. Identiti & nada
- Klip podcast reflektif: host berkongsi pandangan tentang isu Palestin / Baitul Maqdis dengan nada tenang, insaf dan memberi harapan.
- Bahasa Melayu santai-formal ("kita", "saudara kita", "insyaAllah"), ayat pendek, penekanan emosi.

## 2. Format
- 9:16, 1080x1920, 30fps, H.264, 60-70s. Audio master ~-8 LUFS.

## 3. Struktur cerita
1. Hook (0-3s): imej arkib/B-roll bertekstur penuh skrin + host dalam kad PiP + kapsyen kuning besar menyatakan tema.
2. Isi: host bersilih dengan B-roll bertekstur pada setiap kata kunci visual.
3. Montaj laju pada titik emosi (realiti semasa: kebuluran, khemah, senjata).
4. Penutup: imej terang, lembut, penuh harapan (cth. Kubah As-Sakhrah overexposed).

## 4. Editing
- Purata shot ~2.5s: host 3-5s, B-roll 1.5-3s. Durasi tepat ikut transkrip.
- Host: jump cut + punch-in, kedudukan bertukar kiri/kanan setiap potongan.
- Potong ke B-roll setiap kali sebut kata nama / imej (tempat, orang, objek, peristiwa).
- Peralihan: flash putih / overexpose, crossfade double-exposure, glitch streak putih menegak, motion blur.
- Montaj laju 3-4 shot pada titik penekanan.

## 5. Framing host
- Medium close-up ketat, host di sepertiga kiri atau kanan, mikrofon podcast di tepi frame.
- Latar studio: panel akustik ungu gelap + backdrop percikan hijau neon (huruf "bu" putih).
- Muka antara 25-65% tinggi frame, dagu di atas ~1450px (tak tertutup banner).
- Hook: host dalam kad PiP bucu bulat (~28px), separuh bawah zon kandungan.

## 6. Warna
| Peranan | Hex |
|---|---|
| Ungu gelap studio | #150F20 / #1E122F / #251634 |
| Hijau neon backdrop | #A5E09F |
| Kulit hangat | #AF9073 / #9B8871 |
| Kuning hook / marker artikel / kad tajuk | #FFD400 |
| Merah (banner sahaja) | GAZA pada banner |

- Shot host: warna asal studio, kulit hangat, kontras sederhana.
- B-roll: **warna bebas** ikut tema video (warna asal, hitam-putih, sepia, dll.) — tapi **wajib bertekstur** (lihat seksyen 11).
- Warna terang/neon hanya dari studio & banner.

## 7. Tipografi & kapsyen
- Kapsyen: sans-serif bold putih (Inter / SF Pro Display Bold), tracking rapat, bayang lembut, tengah di y≈1356 (~70%).
- Muncul perkataan demi perkataan secara terkumpul (1-4 perkataan), kemudian reset.
- Huruf kecil, kecuali nama khas & akronim (Allah, Gaza, al-Aqsa).
- Perkataan terpotong dalam ucapan ditanda sempang ("berita-", "duga-").
- Hook: kuning #FFD400, bold besar dua baris (baris 2 lebih kecil), atas zon kandungan.
- **Perkataan/istilah yang tak pasti (nama orang, organisasi, tempat, istilah teknikal, slang, ejaan) — TANYA dulu sebelum guna dalam kapsyen. Jangan teka.**
- Pilihan: overlay kaligrafi Arab samar (putih, legap rendah) pada B-roll keagamaan.

## 8. Overlay tetap (wajib setiap video)
| Elemen | Kedudukan (1080x1920) |
|---|---|
| SIYASEE | x 91, y 235 (134x22) |
| HALUAN | x 262, y 222 (48x48) |
| LANGITILAHI | x 340, y 226 (174x41) |
| podcast bumimerdeka | rata kanan margin 100px, y 221 (178x50) |
| Banner iklan | rata bawah, y 1471 (1080x449) — kedudukan dikekalkan |

- Layer paling atas: `template/overlay_1080x1920.png` (`template/apply_overlay.sh`).

## 9. Peta zon skrin
| Zon | Julat Y | Kegunaan |
|---|---|---|
| UI platform | 0-200 | Kosong (B-roll penuh skrin boleh lalu) |
| Logo bar | 220-275 | Logo |
| Hook kuning | ~450-650 | Kapsyen hook (0-3s sahaja) |
| Kandungan | 300-1300 | Muka host, subjek utama B-roll |
| Kapsyen | ~1325-1390 | Kapsyen |
| Banner | 1471-1920 | Iklan kempen |

- B-roll penuh skrin 1080x1920, tapi subjek utama mesti dalam zon kandungan.

## 10. Transkrip (dibuat oleh Claude)
1. `broll/tools/transcribe.py` — transkrip automatik (Whisper large-v3-turbo, Bahasa Melayu) → SRT kapsyen + timestamp setiap perkataan.
2. Claude proofread: betulkan salah dengar yang jelas → `<video>.fixes.json`. Senaraikan semua perkataan/istilah yang tak pasti (dengan timestamp & cadangan) dan **tanya pengguna dulu** sebelum kapsyen dimuktamadkan.
3. `broll/tools/fix_transcript.py` — kenakan pembetulan, timestamp kekal.
4. Segmen bahasa Arab / Inggeris disemak manual.

## 11. B-roll
**Jenis (ikut keutamaan):**
1. Foto / footage penuh skrin ikut kata kunci (tempat, orang, objek, peristiwa)
2. Footage berita/arkib, penuh skrin
3. Imej arkib sejarah (untuk hook / konteks)
4. Screencap artikel / carian Google / kad teks (latar ungu gelap) — hanya bila perlu bukti fakta

Alat: `broll/templates/photo.html` (gambar) & `tpl: "footage"` (video) dalam `broll/tools/build_reel.py` — lihat `broll/README.md`.

**Gaya:** penuh skrin, kontras tinggi, vignette. Warna bebas ikut tema video.

**Tekstur (WAJIB pada setiap B-roll):** sekurang-kurangnya satu lapisan — grain filem, halftone, tekstur kertas lama, atau habuk & calar filem. B-roll licin/bersih tanpa tekstur tidak dibenarkan.

**Animasi (WAJIB pada setiap B-roll):** gerakan halus sepanjang klip — zoom in perlahan (~100%→108%) atau Ken Burns/pan perlahan. Tiada B-roll statik.

**SFX B-roll:** setiap B-roll masuk dengan SFX halus (whoosh lembut / swell rendah), perlahan di bawah VO — bukan hentakan kuat.

**Peralihan:** masuk dengan flash putih / double-exposure; keluar crossfade atau glitch streak.

**Durasi:** ikut panjang cue dalam transkrip, purata ~2.5s (min 1.5s). Animasi dimampatkan ikut durasi.

**Peraturan sumber:**
- Fakta, tajuk & URL mesti dari sumber sebenar — tak boleh direka.
- Footage berhak cipta: link + timestamp sahaja, muat turun manual.
- Laman yang sekat akses automatik → guna sumber lain.

## 12. Audio
- VO jelas di atas, music bed emosi/reflektif berterusan sepanjang video — tiada senyap.
- SFX halus pada setiap B-roll (whoosh lembut / swell, di bawah VO).
- SFX whoosh/impact lebih kuat hanya pada peralihan besar (hook, masuk montaj, flash putih). Riser sebelum penutup.

## 13. Semakan
- Semakan guna screencap frame sahaja.
- **Jangan render pratonton (video atau klip ujian) selagi pengguna belum beri kebenaran untuk proceed.**

## Prompt tetap
```
Create a 9:16 vertical short (1080x1920, 30fps, H.264, 60–70s) in a reflective
podcast-clip style about [TOPIC], from [RAW PODCAST FOOTAGE].

TRANSCRIPT: Transcribe the video (Malay), proofread names/terms, keep
word-level timestamps. Use it for captions and B-roll cues.

HOOK (0–3s): Full-frame textured archival/B-roll image with the host in a rounded
(28px) picture-in-picture card; big two-line yellow (#FFD400) bold caption
in the upper content area stating the theme.

HOST: Tight medium close-up, alternating left/right third on each cut,
podcast mic visible at frame edge. Studio: dark purple acoustic panels,
green neon splatter backdrop. Jump cuts with punch-in. Face 25–65% of frame
height, chin above 1450px.

B-ROLL: Full-frame (no cards), high contrast, vignette. Color treatment is
free to suit each video's theme, but EVERY B-roll MUST carry texture: film
grain, halftone, aged paper, or film dust & scratches — never clean/flat.
Cut to B-roll on every key noun/image in the speech. Optional faint white
Arabic calligraphy overlay on religious imagery. Article/search cards only
when a fact needs proof. Every B-roll MUST move subtly for its whole
duration: slow zoom-in (~100%→108%) or slow Ken Burns/pan — never static —
and enter with a subtle, soft SFX (gentle whoosh/swell) sitting under the VO. Source only real material; never invent facts, headlines or URLs.

EDITING: Average ~2.5s per shot (host 3–5s, B-roll 1.5–3s), timed to the
transcript. Transitions: white flash, double-exposure crossfade, vertical
white-streak glitch, motion blur. Rapid 3–4 shot montage on emphasis
beats. Close on a bright, soft, hopeful image.

COLOR: Host shots — deep purple #150F20/#251634, neon green #A5E09F, warm
skin. B-roll — color free per video, always textured. Yellow only for the
hook, article marker and title cards; red only in the banner.

CAPTIONS: Bold white sans (Inter/SF Pro Display Bold), tight tracking, soft
shadow, centered at y≈1356. Words appear cumulatively (1–4 words) then
reset; lowercase except proper nouns; hyphen on cut-off words. If any word
or term is uncertain (names, organisations, places, jargon, slang,
spelling), ASK the user before using it — never guess.

AUDIO: Continuous emotive/reflective music bed (no dead air), subtle soft
SFX on every B-roll, stronger whoosh/impact only on major transitions, riser before the closing, clear VO on top, master
~-8 LUFS.

TEMPLATE OVERLAY (mandatory, top layer): template/overlay_1080x1920.png —
partner logos (y 220–275) and donation banner (y 1471–1920). Nothing
important may sit under the logo bar or banner.

REVIEW: Provide single-frame screenshots only. Do not render any preview
(video or test clip) until the user explicitly allows proceeding.
```
