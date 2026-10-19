"""Tulis SRT kapsyen (maks 4 perkataan), JSON perkataan dan teks penuh."""
import json


def ts(t):
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h:02}:{m:02}:{int(s):02},{int(s % 1 * 1000):03}"


def write_outputs(words, out):
    # Kapsyen: maks 4 perkataan, pecah juga pada jeda > 0.35s atau tanda baca
    caps, cur = [], []
    for i, w in enumerate(words):
        cur.append(w)
        gap = words[i + 1]["start"] - w["end"] if i + 1 < len(words) else 9
        if len(cur) >= 4 or gap > 0.35 or w["word"][-1:] in ".,?!":
            caps.append(cur)
            cur = []
    if cur:
        caps.append(cur)
    with open(out + ".srt", "w") as f:
        for n, c in enumerate(caps, 1):
            text = " ".join(w["word"] for w in c).strip(".,")
            f.write(f"{n}\n{ts(c[0]['start'])} --> {ts(c[-1]['end'])}\n{text}\n\n")
    with open(out + ".words.json", "w") as f:
        json.dump(words, f, ensure_ascii=False, indent=0)
    with open(out + ".txt", "w") as f:
        f.write(" ".join(w["word"] for w in words))
    return len(caps)
