# Brand guideline & style guide (Draf v2 — belum dimuktamadkan)

## 1. Identiti & nada
- Pencerita yang dipercayai, menerangkan isu berat (geopolitik, kemanusiaan, Palestin) dengan bahasa santai.
- Serius, mendesak, mendidik — tapi mesra. Bahasa Melayu santai ("korang", "dorang", "benda ni"), ayat pendek, soalan retorik.

## 2. Format
- 9:16, 1080x1920, 30fps, H.264, 60-90s. Audio master ~-8 LUFS.

## 3. Struktur cerita
1. Hook (0-1s): soalan retorik ("Korang perasan tak...")
2. Konteks: kad tajuk tarikh/peristiwa
3. Isu + bukti: fakta, artikel, footage arkib
4. Kaitan masa kini
5. CTA: "cuba korang share"

## 4. Editing
- Purata shot ~2.5s (rujukan: ~2.2s). Durasi tepat ikut transkrip.
- Talking head: jump cut + punch-in zoom.
- Potong ke B-roll setiap kali sebut fakta, nama, tarikh atau tempat.
- Peralihan flash putih / fade cepat. Montaj laju 3-4 shot pada titik penekanan.

## 5. Framing host
- Tengah, medium shot paras dada, mikrofon podcast dalam frame, tangan aktif.
- Latar studio gelap (rak buku, lampu practical), depth of field cetek + bokeh.
- Muka antara 25-65% tinggi frame, dagu di atas ~1450px (tak tertutup banner).

## 6. Warna
| Peranan | Hex |
|---|---|
| Hitam asas | #070306 |
| Gelap 2 | #181418 |
| Maroon gelap (latar) | #322528 |
| Burgundy aksen | #662A34 |
| Kelabu warm | #5B5A58 / #9A9691 |
| Neutral hangat | #857270 |
| Sage | #AAB8A8 |
| Kuning penekanan / marker | #FFD400 |
| Emas motion graphic | #E0B04A |

- Low-key sinematik: hitam di-crush, vignette kuat, kulit hangat.
- Arkib dinyahtepu + tekstur halftone halus. Elak warna neon/terang dan latar cerah.

## 7. Tipografi & kapsyen
- Kapsyen: 2-4 perkataan, sans-serif bold putih + bayang lembut, tengah di y≈1356 (~70%).
- Huruf kecil, kecuali nama khas & akronim (Palestin, Gaza, NGO, US).
- Petikan Inggeris: kuning #FFD400, bold italic, satu perkataan sekali.
- Kad tajuk: condensed bold putih uppercase (Bebas Neue / Oswald), nombor ditaip masuk.

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
| UI platform | 0-200 | Kosong |
| Logo bar | 220-275 | Logo |
| Kad B-roll | 300-1275 | Artikel, carian, gambar, footage |
| Kredit sumber | ~1290 | Teks kecil kelabu |
| Kapsyen | ~1325-1390 | Kapsyen |
| Banner | 1471-1920 | Iklan kempen |

## 10. Transkrip (dibuat oleh Claude)
1. `broll/tools/transcribe.py` — transkrip automatik (Whisper large-v3-turbo, Bahasa Melayu) → SRT kapsyen + timestamp setiap perkataan.
2. Claude proofread: betulkan salah dengar, ejaan nama khas & istilah → `<video>.fixes.json`.
3. `broll/tools/fix_transcript.py` — kenakan pembetulan, timestamp kekal.
4. Segmen bahasa Inggeris (klip arkib) disemak manual.

## 11. B-roll
**Jenis (ikut keutamaan):**
1. Screencap artikel + highlight marker (tajuk → zoom ke ayat → marker kuning sapu baris demi baris)
2. Carian gaya Google — kad putih (taip query → hasil sebenar → marker pada hasil berkaitan)
3. Footage berita/arkib (dinyahtepu, dalam kad)
4. Gambar (Unsplash / Wikimedia) + Ken Burns perlahan
5. Motion graphic simbolik 3D/AI (emas atas biru gelap)

**Gaya kad:** bucu bulat 28px, latar hitam + vignette maroon, bayang dalam, grain halus.
Masuk pop (scale 0.88→1), keluar fade 0.25s.

**Durasi:** ikut panjang cue dalam transkrip, purata ~2.5s (min 2s). Animasi dimampatkan ikut durasi.

**Peraturan sumber:**
- Fakta, tajuk & URL mesti dari sumber sebenar — tak boleh direka.
- Kredit sumber wajib pada setiap B-roll pihak ketiga.
- Footage berhak cipta: link + timestamp sahaja, muat turun manual.
- Laman yang sekat akses automatik → guna sumber lain.

## 12. Audio
- VO jelas di atas, music bed tension/ambient perlahan sepanjang video.
- SFX whoosh/hit setiap potongan, riser sebelum pendedahan. Tiada senyap.

## 13. Semakan
- Screencap frame sahaja — tiada render pratonton video.

## Prompt tetap
```
Create a 9:16 vertical short-form video (1080x1920, 30fps, 60–90s) in a
documentary-essay talking-head style about [TOPIK], from [VIDEO MENTAH].

TRANSCRIPT: Transcribe the video (Malay), proofread names/terms, keep
word-level timestamps. Use it for captions and B-roll cues.

STRUCTURE: Hook question in first 1s ("Korang perasan tak...") → context with
date/event title card → core issue with evidence → link to present day →
CTA ("cuba korang share").

HOST: Centered medium shot, chest-up, podcast mic in frame, expressive hands.
Dark home-studio bookshelf background, shallow depth of field. Keep face
between 25–65% frame height, chin above 1450px.

EDITING: Average shot ~2.5s, timed to the transcript. Jump cuts with punch-in
zoom on host. Cut to B-roll on every fact, name, date or place. White flash /
quick fade transitions. Rapid 3–4 shot montage on emphasis beats.

B-ROLL ASSISTANT: From the transcript, build a cue list (timestamp, line,
B-roll type, search query). Source only real material and never invent facts,
headlines or URLs. Priority:
 1. Article screenshot + yellow highlight marker on the key sentence
 2. Google-style search animation, white card (typed query → real results → marker)
 3. Archival/news footage (links + timestamps only; manual download)
 4. Photos (Unsplash / Wikimedia) with slow Ken Burns
 5. Symbolic 3D/AI motion graphics (glowing gold on dark navy)
Each clip lasts as long as its cue (avg ~2.5s, min 2s). Present all B-roll as
rounded (28px) cards inside y 300–1275 on black with maroon vignette and subtle
grain; pop-in 0.88→1, 0.25s fade out; small grey source credit under the card.

COLOR: Low-key cinematic grade, crushed blacks, strong vignette, warm skin,
maroon shadows (#322528, #070306), burgundy accent (#662A34). Archival
desaturated with halftone. Highlight/emphasis #FFD400, motion graphics #E0B04A.

CAPTIONS: 2–4 words, bold white sans with soft shadow, centered at y≈1356,
casual Malay, lowercase except proper nouns/acronyms. English quotes: #FFD400
bold italic, one word at a time. Title cards: bold condensed white uppercase.

AUDIO: Clear VO, low tension/ambient music bed, whoosh/hit on every cut,
riser before reveals, master ~-8 LUFS, no dead air.

TEMPLATE OVERLAY (mandatory, top layer): template/overlay_1080x1920.png —
partner logos (y 220–275) and donation banner (y 1471–1920). Nothing important
may sit under the logo bar or banner.

REVIEW: Provide single-frame screenshots only, no preview renders.
```
