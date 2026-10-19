"""Kenakan pembetulan proofread pada transkrip, timestamp dikekalkan.

Guna: python3 fix_transcript.py <prefix> <fixes.json>
fixes.json: {"frasa salah": "frasa betul", ...}  (tak sensitif huruf besar/kecil)
Frasa berbilang perkataan diganti sebagai satu span (mula perkataan pertama -> tamat perkataan akhir).
"""
import json
import sys

from captions import write_outputs

prefix, fixes_file = sys.argv[1], sys.argv[2]
words = json.load(open(prefix + ".words.json"))
fixes = json.load(open(fixes_file))
norm = lambda s: s.strip(".,?!").lower()

for wrong, right in fixes.items():
    pat = [norm(x) for x in wrong.split()]
    i, hits = 0, 0
    while i <= len(words) - len(pat):
        if [norm(w["word"]) for w in words[i:i + len(pat)]] == pat:
            tail = words[i + len(pat) - 1]["word"]
            punct = tail[len(tail.rstrip(".,?!")):]
            new = right.split()
            span_s, span_e = words[i]["start"], words[i + len(pat) - 1]["end"]
            step = (span_e - span_s) / len(new)
            words[i:i + len(pat)] = [{"start": round(span_s + k * step, 2), "end": round(span_s + (k + 1) * step, 2),
                                      "word": wd + (punct if k == len(new) - 1 else "")} for k, wd in enumerate(new)]
            i += len(new)
            hits += 1
        else:
            i += 1
    print(f"{wrong!r} -> {right!r}: {hits}")

n = write_outputs(words, prefix)
print("ok", len(words), "perkataan,", n, "kapsyen")
