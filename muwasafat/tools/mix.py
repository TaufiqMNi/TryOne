#!/usr/bin/env python3
"""Mix the VO with the SFX cues into vo/mix.wav, padded to the composition length.

Cue times follow the animation cues in intro.html (both are locked to vo/words.json).
Run from the muwasafat/ folder:  python3 tools/mix.py
"""
import subprocess

DURATION = 53.4
VO = 'vo/take1.mp3'

# name -> (raw file, trim seconds, gain)
SFX = {
    'pop':     ('sfx/raw/pop.mp3',     0.45, 0.30),
    'slide':   ('sfx/raw/slide.mp3',   0.90, 0.35),
    'pen':     ('sfx/raw/pen.mp3',     0.50, 0.35),
    'stamp':   ('sfx/raw/stamp.mp3',   0.40, 0.45),
    'lock':    ('sfx/raw/lock.mp3',    0.12, 0.30),
    'unlock':  ('sfx/raw/unlock.mp3',  1.80, 0.40),
    'crumple': ('sfx/raw/crumple.mp3', 0.60, 0.40),
}

CUES = [
    ('slide', 1.10), ('pop', 3.36), ('pen', 4.72),
    ('pop', 8.40), ('pop', 9.60), ('stamp', 10.84), ('pop', 12.60), ('pop', 13.20),
    ('slide', 15.22), ('stamp', 16.24), ('pen', 17.40),
    ('pop', 20.24), ('pen', 21.40), ('pop', 23.20), ('pop', 24.64), ('pop', 25.36), ('pop', 27.32),
    ('slide', 28.20), *[('lock', 29.62 + i * 0.13) for i in range(10)], ('pop', 31.08), ('pen', 32.04),
    ('pop', 35.87), ('pen', 36.60), ('pop', 37.68), ('pop', 39.16), ('crumple', 40.85),
    ('pop', 42.96), ('pen', 43.50), ('pop', 44.95), ('pen', 45.50),
    ('pop', 46.32), ('pop', 46.80), ('slide', 47.40),
    ('slide', 48.70), ('pop', 48.99), ('unlock', 49.90), ('stamp', 50.44),
]

inputs, chains, labels = ['-i', VO], [], []
for i, (name, t) in enumerate(CUES, start=1):
    src, trim, gain = SFX[name]
    inputs += ['-i', src]
    ms = int(t * 1000)
    chains.append(f'[{i}:a]atrim=0:{trim},afade=t=out:st={trim * 0.7:.3f}:d={trim * 0.3:.3f},volume={gain},'
                  f'aresample=44100,aformat=channel_layouts=mono,adelay={ms}|{ms}[s{i}]')
    labels.append(f'[s{i}]')
chains.append(f'[0:a]aresample=44100,aformat=channel_layouts=mono,apad=whole_dur={DURATION}[vo]')
chains.append(f'[vo]{"".join(labels)}amix=inputs={len(labels) + 1}:normalize=0:duration=first,'
              f'loudnorm=I=-14:TP=-1.5:LRA=11,atrim=0:{DURATION}[out]')
subprocess.run(['ffmpeg', '-v', 'error', '-y', *inputs, '-filter_complex', ';'.join(chains),
                '-map', '[out]', '-ac', '2', 'vo/mix.wav'], check=True)
print('vo/mix.wav')
