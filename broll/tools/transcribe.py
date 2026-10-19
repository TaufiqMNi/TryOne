"""Transkrip video -> SRT kapsyen (2-4 perkataan) + JSON perkataan bertimestamp.

Guna: python3 transcribe.py <video> <out_prefix> [model]
Hasil: <out_prefix>.srt, <out_prefix>.words.json, <out_prefix>.txt
"""
import json
import subprocess
import sys

import numpy as np

from faster_whisper import WhisperModel

from captions import write_outputs

video, out = sys.argv[1], sys.argv[2]
model_name = sys.argv[3] if len(sys.argv) > 3 else "large-v3-turbo"

model = WhisperModel(model_name, device="cpu", compute_type="int8")
# nyahkod audio guna ffmpeg (elak isu versi PyAV)
pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", video, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                     capture_output=True, check=True).stdout
audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768
segments, info = model.transcribe(
    audio, language="ms", word_timestamps=True, vad_filter=True, beam_size=5,
    condition_on_previous_text=False,   # elak gelung ulangan
    initial_prompt="Transkrip Bahasa Melayu santai: korang, dorang, benda ni, Palestin, Gaza, NGO.",
)
# Pembetulan istilah biasa (tambah bila jumpa salah dengar baru)
PROPER = {"Palestin", "Gaza", "Israel", "Malaysia", "Eropah", "Canada", "Texas", "The", "Holy", "Al-Aqsa", "Taufan"}
GLOSSARY = {"dinosid": "genosid", "genocide": "genosid", "palestine": "Palestin", "diorang": "dorang"}

words = []
for seg in segments:
    for k, w in enumerate(seg.words):
        t = w.word.strip()
        # huruf besar awal ayat -> kecil (gaya kapsyen); nama khas & akronim kekal
        if k == 0 and t[:1].isupper() and not t[1:2].isupper() and t.strip(".,?!") not in PROPER:
            t = t[0].lower() + t[1:]
        if not t:
            continue
        if t.startswith("-") and words:                 # "kuasa -kuasa" -> "kuasa-kuasa"
            words[-1]["word"] += t
            words[-1]["end"] = round(w.end, 2)
            continue
        core = t.strip(".,?!").lower()
        if core in GLOSSARY:
            t = t.lower().replace(core, GLOSSARY[core])
        words.append({"start": round(w.start, 2), "end": round(w.end, 2), "word": t})


write_outputs(words, out)
print("ok", len(words), "perkataan, bahasa", info.language)
