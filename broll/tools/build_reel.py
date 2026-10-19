"""Bina reel 9:16 dari klip podcast ikut template/STYLE_GUIDE.md (seksyen 2-13).

Konfigurasi setiap reel: reels/<id>.json (sumber, masa, cue B-roll, pembetulan transkrip).
Guna (dalam folder broll/):
  python3 tools/build_reel.py <id> faces      -> jejak muka penutur (crop 9:16)
  python3 tools/build_reel.py <id> transcribe -> transkrip asal + pembetulan (reels/<id>.fixes.json)
  python3 tools/build_reel.py <id> capture    -> screencap artikel B-roll (config "articles")
  python3 tools/build_reel.py <id> plan       -> EDL (jump cut pada senyap), shot + punch-in, cue B-roll
  python3 tools/build_reel.py <id> vo         -> transkrip semula audio suntingan (masa kapsyen tepat), kemudian plan semula
  python3 tools/build_reel.py <id> render     -> render B-roll & kad (templates/)
  python3 tools/build_reel.py <id> audio      -> music bed + SFX sintetik (whoosh/hit/riser)
  python3 tools/build_reel.py <id> assemble   -> grade, B-roll, kapsyen, mix, master ~-8 LUFS
  python3 tools/build_reel.py <id> final      -> tampal overlay (template/apply_overlay.sh) -> work/<id>_final.mp4
  python3 tools/build_reel.py <id> still T    -> screencap satu frame pada saat T (semakan)
Semua fail kerja dalam work/ (tak masuk git).
"""
import json, os, re, statistics as st, subprocess, sys, wave

import numpy as np

BROLL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BROLL)
WORK = f"{BROLL}/work"
FPS = 30


def cfg(cid):
    C = json.load(open(f"{BROLL}/reels/{cid}.json"))
    C["src"] = os.path.join(BROLL, C["src"])
    C.setdefault("cta", dict(dur=2.4, tpl="card", data=dict(kind="cta", lines=["cuba korang", "share"], highlight="share", full=True)))
    C.setdefault("english", []); C.setdefault("proper", []); C.setdefault("arabic", []); C.setdefault("groups", [])
    return C


def norm(w):
    return w.strip(".,?!").lower()


def load_words(cid):
    return json.load(open(f"{WORK}/{cid}.words.json"))


def find(words, phrase, after=0):
    pat = [norm(x) for x in phrase.split()]
    for i in range(after, len(words) - len(pat) + 1):
        if [norm(w["word"]) for w in words[i:i + len(pat)]] == pat:
            return i
    raise SystemExit(f"frasa tak jumpa: {phrase}")


def plan(cid):
    C = cfg(cid); CTA = C["cta"]
    words = [w for w in load_words(cid) if C["start"] <= w["start"] < C["end"]]
    # 1. EDL: buang senyap > 0.45s (silencedetect, tinggal ~0.34s) -> jump cut
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", C["src"], "-af", "silencedetect=n=-36dB:d=0.45", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    st_ = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", r)]
    en_ = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r)]
    segs, s = [], C["start"]
    for a, b in zip(st_, en_):
        if a + 0.17 > s + 0.3 and b - 0.17 < C["end"]:
            segs.append([round(s, 3), round(a + 0.17, 3)])
            s = b - 0.17
    segs.append([round(s, 3), C["end"]])
    def out_t(t):
        acc = 0.0
        for a, b in segs:
            if t <= b:
                return acc + max(0.0, t - a)
            acc += b - a
        return acc
    total = sum(b - a for a, b in segs)

    # 2. Shot ~3s dalam setiap segmen, potong pada hujung perkataan (utamakan tanda baca/jeda)
    shots = []
    for a, b in segs:
        ends = [w["end"] for w in words if a < w["end"] < b - 0.8]
        cur = a
        while b - cur > 4.2:
            cands = [e for e in ends if 2.4 <= e - cur <= 3.8]
            if not cands:
                break
            pref = [e for e in cands if any(abs(w["end"] - e) < 1e-6 and (w["word"][-1:] in ",.?" ) for w in words)]
            cut = (pref or cands)[len(pref or cands) // 2]
            shots.append([cur, cut + 0.04])
            cur = cut + 0.04
        shots.append([cur, b])

    # 3. Crop ikut muka (median dalam shot), zum selang-seli 1.0 / 1.15 (punch-in)
    faces = [f for f in json.load(open(f"{WORK}/{cid}_faces.json")) if f["box"]]
    allcx = st.median(f["box"][0] + f["box"][2] / 2 for f in faces)
    allcy = st.median(f["box"][1] + f["box"][3] / 2 for f in faces)
    out_shots = []
    for k, (a, b) in enumerate(shots):
        fs = [f["box"] for f in faces if a <= f["t"] <= b]
        cx = st.median(x + w / 2 for x, y, w, h in fs) if fs else allcx
        cy = st.median(y + h / 2 for x, y, w, h in fs) if fs else allcy
        z = 1.0 if k % 2 == 0 else 1.15
        h = round(1080 / z / 2) * 2
        w = round(h * 9 / 16 / 2) * 2
        y0 = 0 if z == 1.0 else int(min(max(cy - 0.45 * h, 0), 1080 - h))
        x0 = int(min(max(cx + 60 - w / 2, 0), 1920 - w))
        out_shots.append(dict(src=[round(a, 3), round(b, 3)], crop=[w, h, x0, y0], z=z))

    # 4. Cue B-roll -> masa output
    src_mapped = [dict(w, start=round(out_t(w["start"]), 3), end=round(out_t(w["end"]), 3)) for w in words]
    if os.path.exists(f"{WORK}/{cid}e.words.json"):
        # transkrip semula audio suntingan (masa tepat); bahagian yang Whisper tertinggal (bacaan Arab)
        # diambil dari transkrip asal, perkataan akhir disematkan ikut analisis tenaga audio
        E = load_words(cid + "e")
        for pa, pb in C.get("src_windows", []):
            i, j = find(src_mapped, pa), find(src_mapped, pb)
            win = src_mapped[i:j + 1]; t0, t1 = win[0]["start"], win[-1]["end"]
            E = [w for w in E if w["end"] <= t0 + 0.05 or w["start"] >= t1 - 0.05] + win
        for wd, a, b in C.get("tail_words", []):
            E = [w for w in E if w["start"] < total + a - 0.02] + [dict(word=wd, start=round(total + a, 3), end=round(total + b, 3))]
        words = sorted(E, key=lambda w: w["start"]); out_t = lambda t: t
        src_mapped = words
    cues = []
    for n, q in enumerate(C["cues"]):
        if "at" in q:
            t0 = q["at"]
        else:
            i = find(words, q["phrase"])
            t0 = out_t(words[i]["start"]) - q.get("pre", 0.0)
        if "until_phrase" in q:
            j = find(words, q["until_phrase"])
            dur = out_t(words[j]["end"]) + q.get("post", 0.0) - t0
        elif q.get("until_end"):
            dur = total - t0 + 0.15
        else:
            dur = q["dur"]
        cues.append(dict(name=f"{cid}_b{n}", t=round(max(0.0, t0), 3), dur=round(dur, 2), tpl=q["tpl"], data=q["data"],
                         source=q.get("source"), sfx=q.get("sfx", "whoosh"), riser=q.get("riser", False)))
    cues.append(dict(name=f"{cid}_cta", t=round(total, 3), dur=CTA["dur"], tpl=CTA["tpl"], data=CTA["data"], sfx="hit", riser=False, source=None))
    for a, b in zip(cues, cues[1:]):          # elak bertindih
        if a["t"] + a["dur"] > b["t"] - 0.3 and b["name"] != f"{cid}_cta":
            a["dur"] = round(b["t"] - 0.3 - a["t"], 2)

    # 5. JSON data B-roll
    for c in cues:
        if c["tpl"] == "highlight":
            d = json.load(open(f"{WORK}/{c['data']}.json"))
            d.update(duration=c["dur"], source=c["source"])
        else:
            d = dict(c["data"], duration=c["dur"])
        json.dump(d, open(f"{WORK}/{c['name']}.json", "w"), ensure_ascii=False)

    mapped = src_mapped
    P = dict(segs=segs, shots=out_shots, cues=cues, total=round(total, 3), words=mapped)
    json.dump(P, open(f"{WORK}/{cid}.plan.json", "w"), ensure_ascii=False, indent=1)
    lens = [s["src"][1] - s["src"][0] for s in out_shots]
    print(f"{cid}: {len(segs)} segmen, {len(out_shots)} shot (purata {st.mean(lens):.2f}s), tempoh {total:.2f}s + CTA {CTA['dur']}s")
    for c in cues:
        print(f"  {c['t']:6.2f}s  {c['dur']:4.2f}s  {c['name']}  {c['tpl']}")


def vo(cid):
    """Eksport audio suntingan (ikut EDL) untuk ditranskrip semula -> masa kapsyen tepat."""
    C = cfg(cid); P = json.load(open(f"{WORK}/{cid}.plan.json"))
    parts = "".join(f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS[a{k}];" for k, (a, b) in enumerate(P["segs"]))
    fc = parts + "".join(f"[a{k}]" for k in range(len(P["segs"]))) + f"concat=n={len(P['segs'])}:v=0:a=1[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", C["src"], "-filter_complex", fc, "-map", "[o]", f"{WORK}/{cid}_vo.wav"], check=True)
    subprocess.run(["python3", "transcribe.py", f"{WORK}/{cid}_vo.wav", f"{WORK}/{cid}e"], cwd=f"{BROLL}/tools", check=True)
    subprocess.run(["python3", "fix_transcript.py", f"{WORK}/{cid}e", f"{BROLL}/reels/{cid}.fixes.json"], cwd=f"{BROLL}/tools", check=True)
    plan(cid)


def render(cid):
    P = json.load(open(f"{WORK}/{cid}.plan.json"))
    for c in P["cues"]:
        out = f"{WORK}/{c['name']}.mp4"
        tpl = f"{BROLL}/templates/{c['tpl']}.html"
        subprocess.run(["node", f"{BROLL}/tools/render.mjs", tpl, f"{WORK}/{c['name']}.json", out], check=True)


# ---------------- audio sintetik ----------------
SR = 48000


def onepole(x, coef):
    y = np.empty_like(x); acc = 0.0
    for i in range(len(x)):
        acc += coef[i] * (x[i] - acc); y[i] = acc
    return y


def whoosh(rng, dur=0.55, peak=0.35):
    n = int(dur * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    coef = np.interp(t, [0, dur * .55, dur], [0.02, 0.35, 0.05])
    s = onepole(noise, coef) - onepole(noise, coef * 0.08)
    env = np.interp(t, [0, dur * .55, dur], [0, 1, 0]) ** 1.5
    return s / (np.abs(s).max() + 1e-9) * env * peak


def hit(rng, dur=0.9, peak=0.6):
    n = int(dur * SR); t = np.arange(n) / SR
    f = 58 * np.exp(-t * 2.2) + 38
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4.5)
    click = rng.standard_normal(n) * np.exp(-t * 60) * .25
    return (body + click) * peak


def riser(rng, dur=1.6, peak=0.22):
    n = int(dur * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    coef = np.interp(t, [0, dur], [0.01, 0.5])
    s = onepole(noise, coef)
    s = s / (np.abs(s).max() + 1e-9)
    return s * (t / dur) ** 2.2 * peak


def bed(total):
    n = int(total * SR); t = np.arange(n) / SR
    out = np.zeros(n)
    for f, a in [(55, .5), (82.41, .32), (110, .22), (130.81, .16), (164.81, .08)]:
        lfo = 0.75 + 0.25 * np.sin(2 * np.pi * t / (7 + f % 5) + f)
        out += a * np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 0.11 * t)) * lfo
    rng = np.random.default_rng(7)
    air = onepole(rng.standard_normal(n), np.full(n, 0.015))
    out += air / (np.abs(air).max() + 1e-9) * 0.25 * (0.6 + 0.4 * np.sin(2 * np.pi * t / 11))
    pulse = (np.sin(2 * np.pi * t * 1.0) > 0.97) * 0  # tiada beat — ambient sahaja
    out += pulse
    fade = np.minimum(1, np.minimum(t / 1.5, (total - t) / 1.8))
    return out / np.abs(out).max() * fade


def audio(cid):
    P = json.load(open(f"{WORK}/{cid}.plan.json"))
    total = P["total"] + cfg(cid)["cta"]["dur"]
    rng = np.random.default_rng(1)
    n = int(total * SR) + SR
    music = np.zeros(n); sfx = np.zeros(n)
    b = bed(total); music[:len(b)] += b

    def put(sig, t):
        i = int(t * SR)
        if i < 0: sig, i = sig[-i:], 0
        e = min(n, i + len(sig)); sfx[i:e] += sig[:e - i]
    # setiap jump cut: whoosh lembut
    acc = 0.0
    for s in P["shots"][:-1]:
        acc += s["src"][1] - s["src"][0]
        put(whoosh(rng, .4, .10), acc - .22)
    for c in P["cues"]:
        put(whoosh(rng, .55, .32), c["t"] - .3)
        if c["sfx"] == "hit":
            put(hit(rng), c["t"])
        if c["riser"]:
            put(riser(rng), c["t"] - 1.6)
    for name, sig in (("music", music), ("sfx", sfx)):
        x = np.clip(sig, -1, 1)
        with wave.open(f"{WORK}/{cid}_{name}.wav", "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((x * 32767).astype(np.int16).tobytes())
    print("ok audio", cid, round(total, 2), "s")


# ---------------- kapsyen ASS ----------------
def ass_time(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02}:{s:05.2f}"


def captions(cid, P):
    C = cfg(cid)
    ENGLISH = {w.lower() for g in C["english"] for w in g.split()}
    PROPER = {w.lower(): w for w in C["proper"]}
    ARABIC = {w.lower() for w in C["arabic"]}
    words = P["words"]
    for w in words:
        core = w["word"].rstrip(".,?!")
        tail = "?" if w["word"].endswith("?") else ""
        low = core.lower()
        w["eng"] = low in ENGLISH
        w["arab"] = low.strip(",") in ARABIC
        if low in PROPER:
            core = PROPER[low]
        elif not w["arab"]:
            core = low
        w["txt"] = core.strip(",") + tail
        w["brk"] = w["word"][-1:] in ",.?!"
    # gabung token yang tak boleh dipisah (config "groups", cth. "Allah SWT"); frasa Inggeris berbilang
    # perkataan (config "english", cth. "Board of Peace") jadi satu kapsyen kuning
    groups = [(g.split(), False) for g in C["groups"]] + [(g.split(), True) for g in C["english"] if " " in g]
    single_eng = {g.lower() for g in C["english"] if " " not in g}
    merged, i = [], 0
    while i < len(words):
        w = words[i]
        for grp, eng in groups:
            if [x["txt"].lower() for x in words[i:i + len(grp)]] == [g.lower() for g in grp]:
                last = words[i + len(grp) - 1]
                w = dict(w, txt=" ".join(grp), end=last["end"], brk=last["brk"], eng=eng)
                i += len(grp) - 1
                break
        else:
            w = dict(w, eng=w["txt"].lower() in single_eng)
        merged.append(w); i += 1
    words = merged
    caps, cur = [], []
    for i, w in enumerate(words):
        if w["eng"]:
            if cur: caps.append(cur); cur = []
            caps.append([w]); continue
        cur.append(w)
        nxt = words[i + 1] if i + 1 < len(words) else None
        gap = nxt["start"] - w["end"] if nxt else 9
        width = len(" ".join(x["txt"] for x in cur))
        too_wide = nxt is not None and width + 1 + len(nxt["txt"]) > 22
        if len(cur) >= 4 or w["brk"] or gap > 0.3 or (nxt and nxt["eng"]) or too_wide:
            caps.append(cur); cur = []
    if cur: caps.append(cur)
    # elak kapsyen 1 perkataan (bukan Inggeris) jika boleh gabung
    merged = []
    for c in caps:
        if merged and len(c) == 1 and not c[0]["eng"] and not merged[-1][-1]["eng"] and len(merged[-1]) < 4 \
                and len(" ".join(x["txt"] for x in merged[-1] + c)) <= 22 \
                and c[0]["start"] - merged[-1][-1]["end"] < 0.3 and not merged[-1][-1]["brk"]:
            merged[-1] += c
        else:
            merged.append(c)
    caps = merged
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter ExtraBold,66,&H00FFFFFF,&H00FFFFFF,&H64000000,&H8C000000,1,0,0,0,100,100,0,0,1,2,4,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    for k, c in enumerate(caps):
        a = c[0]["start"]
        nxt = caps[k + 1][0]["start"] if k + 1 < len(caps) else P["total"] + 0.3
        b = nxt if nxt - c[-1]["end"] < 0.45 else c[-1]["end"] + 0.2
        b = min(max(b, a + 0.25), nxt) if nxt > a else b
        text = " ".join(w["txt"] for w in c)
        if c[0]["eng"]:
            text = r"{\c&H00D4FF&\i1}" + text
        elif all(w["arab"] for w in c):
            text = r"{\i1}" + text
        pop = r"{\pos(540,1356)\fscx88\fscy88\t(0,90,\fscx100\fscy100)}"
        lines.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},Cap,,0,0,0,,{pop}{text}")
    open(f"{WORK}/{cid}.ass", "w").write(head + "\n".join(lines) + "\n")
    return len(caps)


def assemble(cid):
    C = cfg(cid); CTA = C["cta"]; P = json.load(open(f"{WORK}/{cid}.plan.json"))
    ncap = captions(cid, P)
    total = P["total"] + CTA["dur"]
    # gradien gelap atas: tutup logo asal dalam footage (zon UI platform)
    from PIL import Image
    g = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); px = g.load()
    for y in range(0, 360):
        a = 255 if y < 215 else int(255 * (1 - (y - 215) / 145) ** 1.6)
        for x in range(1080): px[x, y] = (7, 3, 6, a)
    g.save(f"{WORK}/topfade.png")

    inp = ["-i", C["src"], "-i", f"{WORK}/topfade.png", "-i", f"{WORK}/{cid}_music.wav", "-i", f"{WORK}/{cid}_sfx.wav"]
    for c in P["cues"]:
        inp += ["-i", f"{WORK}/{c['name']}.mp4"]
    fc = []
    vs, as_ = [], []
    acc = 0.0
    for k, s in enumerate(P["shots"]):
        a, b = s["src"]; w, h, x, y = s["crop"]
        # bilangan frame ikut masa audio kumulatif tepat -> tiada drift A/V terkumpul (maks 1/2 frame)
        nfr = round((acc + b - a) * FPS) - round(acc * FPS); acc += b - a
        fc.append(f"[0:v]trim=start={a}:end={b + 0.1},setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y},scale=1080:1920:flags=lanczos,setsar=1,fps={FPS},"
                  f"tpad=stop_mode=clone:stop_duration=0.2,trim=end_frame={nfr},setpts=PTS-STARTPTS[v{k}]")
        fc.append(f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b - a - (0.08 if k == len(P["shots"]) - 1 else 0.012):.3f}:d={0.08 if k == len(P["shots"]) - 1 else 0.012}[a{k}]")
        vs.append(f"[v{k}]"); as_.append(f"[a{k}]")
    n = len(P["shots"])
    fc.append("".join(v + a for v, a in zip(vs, as_)) + f"concat=n={n}:v=1:a=1[vc][ac]")
    fc.append(f"[vc]tpad=stop_mode=clone:stop_duration={CTA['dur'] + 0.5},"
              "eq=contrast=1.09:brightness=-0.025:saturation=0.82:gamma=0.96,"
              "colorbalance=rs=0.05:gs=-0.01:bs=-0.03:rm=0.03:bm=-0.03:rh=0.02:bh=-0.03,"
              "vignette=angle=PI/4.2,noise=alls=5:allf=t,format=yuv420p[vg]")
    fc.append("[vg][1:v]overlay=0:0[vt]")
    last = "[vt]"
    for i, c in enumerate(P["cues"]):
        t, d = c["t"], c["dur"]
        fc.append(f"[{4 + i}:v]setpts=PTS-STARTPTS+{t}/TB[b{i}]")
        fc.append(f"{last}[b{i}]overlay=0:0:eof_action=pass:enable='between(t,{t},{t + d - 0.02})'[o{i}]")
        last = f"[o{i}]"
    flashes = ",".join(f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.5:t=fill:enable='between(t,{c['t'] - 0.03},{c['t'] + 0.06})'" for c in P["cues"])
    fc.append(f"{last}{flashes},ass={WORK}/{cid}.ass:fontsdir=/usr/share/fonts/opentype/inter,trim=duration={total},format=yuv420p[vout]")
    # audio: VO bersih + bed + SFX, kemudian master
    fc.append("[ac]highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2,"
              f"apad=whole_dur={total},aresample=48000,aformat=channel_layouts=stereo[vo]")
    fc.append(f"[2:a]volume=0.075,aformat=channel_layouts=stereo[mu]")
    fc.append(f"[3:a]volume=0.55,aformat=channel_layouts=stereo[fx]")
    fc.append(f"[vo][mu][fx]amix=inputs=3:normalize=0:duration=first,atrim=duration={total}[mix]")
    open(f"{WORK}/{cid}.fc.txt", "w").write(";\n".join(fc))
    pre = f"{WORK}/{cid}_pre.mp4"
    if not os.environ.get("MASTER_ONLY"):          # MASTER_ONLY=1: ulang master audio sahaja
        subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex_script", f"{WORK}/{cid}.fc.txt",
                        "-map", "[vout]", "-map", "[mix]", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS),
                        "-c:a", "pcm_s16le", f"{WORK}/{cid}_mix.mkv"], check=True)
    # master: kompres + gain + limiter, ulang sehingga ~-8 LUFS (puncak <= -1 dBTP)
    mkv = f"{WORK}/{cid}_mix.mkv"
    def lufs(path, af=None):
        cmd = ["ffmpeg", "-v", "info", "-i", path] + (["-af", af + ",ebur128=peak=true"] if af else ["-af", "ebur128=peak=true"]) + ["-f", "null", "-"]
        r = subprocess.run(cmd, capture_output=True, text=True).stderr
        summ = r[r.rindex("Summary:"):]
        return float(re.search(r"I:\s+(-?[0-9.]+)", summ).group(1)), float(re.search(r"Peak:\s+(-?[0-9.]+)", summ).group(1))
    chain = lambda g: ("acompressor=threshold=-30dB:ratio=4:attack=8:release=120:knee=6,"
                       "acompressor=threshold=-20dB:ratio=10:attack=0.5:release=30:knee=2,"
                       f"volume={g:.2f}dB,alimiter=limit=0.66:attack=1:release=40:level=false")
    i0, _ = lufs(mkv)
    g = -8 - i0 + 3
    for _ in range(8):
        i1, pk = lufs(mkv, chain(g))
        if abs(i1 + 8) < 0.3: break
        g += 1.3 * (-8 - i1)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mkv, "-c:v", "copy", "-af", chain(g), "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", pre], check=True)
    print("ok", pre, ncap, "kapsyen,", f"{i0} -> {i1} LUFS, puncak {pk} dBFS, gain {g:.1f} dB")


def faces(cid):
    """Jejak muka penutur 5x sesaat (Haar frontal + profil, opencv-python-headless<5)."""
    import cv2
    C = cfg(cid)
    cap = cv2.VideoCapture(C["src"]); fps = cap.get(cv2.CAP_PROP_FPS)
    casc = [cv2.CascadeClassifier(cv2.data.haarcascades + n) for n in ("haarcascade_frontalface_default.xml", "haarcascade_profileface.xml")]
    side = C.get("speaker_side", "left")         # separuh frame tempat penutur
    res, i, step = [], 0, max(1, int(fps // 5))
    while True:
        ok, f = cap.read()
        if not ok: break
        if i % step == 0:
            off = 0 if side == "left" else f.shape[1] - 1100
            g = cv2.cvtColor(f[:, off:off + 1100], cv2.COLOR_BGR2GRAY)
            best = None
            for c in casc:
                for flip in (False, True):
                    gg = cv2.flip(g, 1) if flip else g
                    for (x, y, w, h) in c.detectMultiScale(gg, 1.1, 6, minSize=(150, 150)):
                        if flip: x = gg.shape[1] - x - w
                        if best is None or w * h > best[2] * best[3]: best = (int(x) + off, int(y), int(w), int(h))
            res.append({"t": round(i / fps, 2), "box": best})
        i += 1
    json.dump(res, open(f"{WORK}/{cid}_faces.json", "w"))
    print("ok faces", cid, len(res), "sampel,", sum(1 for r in res if r["box"]), "ada muka")


def transcribe(cid):
    C = cfg(cid)
    subprocess.run(["python3", "transcribe.py", C["src"], f"{WORK}/{cid}"], cwd=f"{BROLL}/tools", check=True)
    subprocess.run(["python3", "fix_transcript.py", f"{WORK}/{cid}", f"{BROLL}/reels/{cid}.fixes.json"], cwd=f"{BROLL}/tools", check=True)


def capture(cid):
    for name, (url, phrase) in cfg(cid).get("articles", {}).items():
        subprocess.run(["node", f"{BROLL}/tools/capture_article.mjs", url, phrase, f"{WORK}/{name}"], check=True)


def final(cid):
    subprocess.run([f"{REPO}/template/apply_overlay.sh", f"{WORK}/{cid}_pre.mp4", f"{WORK}/{cid}_final.mp4"],
                   check=True, capture_output=True)
    print("ok", f"{WORK}/{cid}_final.mp4")


def still(cid, t):
    final_ = f"{WORK}/{cid}_final.mp4"
    src = final_ if os.path.exists(final_) else f"{WORK}/{cid}_pre.mp4"
    out = f"{WORK}/{cid}_t{float(t):05.1f}.jpg"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", src, "-frames:v", "1", "-q:v", "3", out], check=True)
    print(out)


if __name__ == "__main__":
    cid, step = sys.argv[1], sys.argv[2]
    steps = dict(faces=faces, transcribe=transcribe, capture=capture, plan=plan, vo=vo, render=render, audio=audio,
                 assemble=assemble, final=final)
    if step == "still":
        still(cid, sys.argv[3])
    else:
        steps[step](cid)
