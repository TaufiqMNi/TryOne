"""Bina reel 9:16 dari klip podcast ikut template/STYLE_GUIDE.md (seksyen 2-13).

Konfigurasi setiap reel: reels/<id>.json (sumber, masa, cue B-roll, pembetulan transkrip).
Guna (dalam folder broll/):
  python3 tools/build_reel.py <id> faces      -> jejak muka penutur (crop 9:16)
  python3 tools/build_reel.py <id> transcribe -> transkrip asal + pembetulan (reels/<id>.fixes.json)
  python3 tools/build_reel.py <id> capture    -> screencap artikel B-roll (config "articles")
  python3 tools/build_reel.py <id> plan       -> EDL (jump cut pada senyap), shot + punch-in, cue B-roll
  python3 tools/build_reel.py <id> vo         -> transkrip semula audio suntingan (masa kapsyen tepat), kemudian plan semula
  python3 tools/build_reel.py <id> render     -> render B-roll (photo/footage penuh skrin bertekstur, templates/) & kad (Remotion)
  python3 tools/build_reel.py <id> audio      -> music bed + SFX sintetik (halus setiap B-roll, whoosh/hit peralihan besar)
  python3 tools/build_reel.py <id> assemble   -> grade, hook PiP, B-roll + peralihan, kapsyen terkumpul, mix, master ~-8 LUFS
  python3 tools/build_reel.py <id> final      -> tampal overlay (template/apply_overlay.sh) -> work/<id>_final.mp4
  python3 tools/build_reel.py <id> still T    -> screencap satu frame pada saat T (semakan)
Semua fail kerja dalam work/ (tak masuk git).
"""
import json, os, re, statistics as st, subprocess, sys, wave

import numpy as np

BROLL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.dirname(BROLL)
REMOTION = f"{REPO}/remotion"
WORK = f"{BROLL}/work"
FPS = 30


def cfg(cid):
    global FPS
    C = json.load(open(f"{BROLL}/reels/{cid}.json"))
    if C.get("preset"):                          # template gaya (template/presets/<nama>.json); config reel mengatasi
        pre = json.load(open(f"{REPO}/template/presets/{C['preset']}.json"))
        C = {**{k: v for k, v in pre.items() if not k.startswith("_")}, **C}
        C["proper"] = sorted(set(pre.get("proper", [])) | set(C.get("proper", [])))   # nama khas: gabung, bukan ganti
    C["src"] = os.path.join(BROLL, C["src"])
    FPS = C.get("fps", 30)                       # footage precut 25fps -> kekal 25 (elak frame berganda)
    C.setdefault("cta", None)                    # v2: tiada kad CTA lalai; penutup = B-roll terang (until_end)
    C.setdefault("hook", None)
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


def edl_shots(cid, C, words):
    """Klip podcast mentah: jump cut pada senyap, shot ~3s, crop 9:16 ikut muka dari footage 16:9."""
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
    # config "skip": [[a, b], ...] saat sumber dibuang (soalan host, filler, ayat berisiko)
    for a0, b0 in C.get("skip", []):
        segs = [p for a, b in segs for p in ([a, min(b, a0)], [max(a, b0), b]) if p[1] - p[0] > 0.25]
    segs = [[round(a, 3), round(b, 3)] for a, b in segs]
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
    # config "cuts": tukar kamera dalam sumber -> sempadan shot (crop ikut muka dikira semula selepas setiap tukar)
    pieces = []
    for a, b in segs:
        edges = [a] + [t for t in C.get("cuts", []) if a + 0.3 < t < b - 0.3] + [b]
        pieces += [[x, y] for x, y in zip(edges, edges[1:])]
    lo, hi, mx = (4.0, 6.0, 7.0) if C.get("tall") else (2.4, 3.8, 4.2)   # tall: shot host 4-6s (zum bersilih tak melompat)
    for a, b in pieces:
        ends = [w["end"] for w in words if a < w["end"] < b - 0.8]
        cur = a
        while b - cur > mx:
            cands = [e for e in ends if lo <= e - cur <= hi]
            if not cands:
                break
            pref = [e for e in cands if any(abs(w["end"] - e) < 1e-6 and (w["word"][-1:] in ",.?" ) for w in words)]
            cut = (pref or cands)[len(pref or cands) // 2]
            shots.append([cur, cut + 0.04])
            cur = cut + 0.04
        shots.append([cur, b])

    # 3. Crop ikut muka (median dalam shot): medium close-up, zum selang-seli 1.15 / 1.3 (punch-in),
    #    host di sepertiga kiri/kanan bersilih setiap potongan (config "host_thirds": false -> tengah)
    faces = [f for f in json.load(open(f"{WORK}/{cid}_faces.json")) if f["box"]]
    allcx = st.median(f["box"][0] + f["box"][2] / 2 for f in faces)
    allcy = st.median(f["box"][1] + f["box"][3] / 2 for f in faces)
    thirds = C.get("host_thirds", True)
    out_shots, face_y = [], []
    for k, (a, b) in enumerate(shots):
        fs = [f["box"] for f in faces if a <= f["t"] <= b]
        cx = st.median(x + w / 2 for x, y, w, h in fs) if fs else allcx
        cy = st.median(y + h / 2 for x, y, w, h in fs) if fs else allcy
        if C.get("tall"):
            # gaya raw footage pengguna: crop 9:16 setinggi penuh pada muka (zum 1.0 / 1.1 bersilih), push/pull halus
            z = 1.0 if k % 2 == 0 else 1.1
            h = round(1080 / z / 2) * 2
            w = round(h * 9 / 16 / 2) * 2
            y0 = int(min(max(cy - 0.30 * h, 0), 1080 - h))
            x0 = int(min(max(cx - 0.5 * w, 0), 1920 - w))
            out_shots.append(dict(src=[round(a, 3), round(b, 3)], crop=[w, h, x0, y0], z=z, move="push" if k % 2 == 0 else "pull"))
            face_y.append((cy - y0) * 1920 / h - C.get("lift", 0))
            continue
        z = 1.15 if k % 2 == 0 else 1.3
        h = round(1080 / z / 2) * 2
        w = round(h * 9 / 16 / 2) * 2
        y0 = int(min(max(cy - 0.42 * h, 0), 1080 - h))
        fx = (1 / 3 if k % 2 == 0 else 2 / 3) if thirds else 0.5
        x0 = int(min(max(cx - fx * w, 0), 1920 - w))
        out_shots.append(dict(src=[round(a, 3), round(b, 3)], crop=[w, h, x0, y0], z=z))
        face_y.append((cy - y0) * 1920 / h)      # pusat muka dalam frame output (untuk PiP hook)
    return segs, out_shots, face_y, out_t, total


def precut_shots(cid, C, words):
    """Footage 9:16 yang sudah dipotong pengguna (config "precut": true): tiada buang senyap.
    Shot = potongan asal pengguna (config "cuts", saat sumber); shot > 7s dipecah pada hujung frasa.
    Komposisi asal pengguna dikekalkan (ruang banner di bawah sudah disediakan): tiada zum/anjakan, hanya
    gerakan halus push-in / push-out 3% bersilih supaya tiada shot statik."""
    a0, b0 = C["start"], C["end"]
    segs = [[a0, b0]]
    edges = [a0] + [t for t in C.get("cuts", []) if a0 + 0.5 < t < b0 - 0.5] + [b0]
    ends = [w["end"] for w in words]
    shots = []
    for a, b in zip(edges, edges[1:]):
        cur = a
        while b - cur > 7.0:
            cands = [e for e in ends if 3.5 <= e - cur <= 6.0 and b - e > 2.0]
            if not cands:
                break
            pref = [e for e in cands if any(abs(w["end"] - e) < 1e-6 and w["word"][-1:] in ",.?" for w in words)]
            cut = (pref or cands)[len(pref or cands) // 2] + 0.04
            shots.append([cur, cut]); cur = cut
        shots.append([cur, b])
    faces = [f for f in json.load(open(f"{WORK}/{cid}_faces.json")) if f["box"]]
    out_shots, face_y = [], []
    for k, (a, b) in enumerate(shots):
        fs = [f["box"] for f in faces if a <= f["t"] <= b] or [f["box"] for f in faces]
        cy = st.median(y + h / 2 for x, y, w, h in fs)
        z = 1.0                                     # komposisi asal pengguna dikekalkan (tiada zum / anjakan)
        w, h, x0, y0 = 1080, 1920, 0, 0
        move = "push" if k % 2 == 0 else "pull"
        out_shots.append(dict(src=[round(a, 3), round(b, 3)], crop=[w, h, x0, y0], z=z, move=move))
        face_y.append((cy - y0) * 1920 / h)
    total = round(b0 - a0, 3)
    return segs, out_shots, face_y, (lambda t: max(0.0, t - a0)), total


def plan(cid):
    C = cfg(cid); CTA = C["cta"]
    words = [w for w in load_words(cid) if C["start"] <= w["start"] < C["end"]]
    segs, out_shots, face_y, out_t, total = (precut_shots if C.get("precut") else edl_shots)(cid, C, words)

    # 4. Cue B-roll -> masa output
    # hanya perkataan yang kekal selepas potongan (titik tengah dalam segmen) dapat kapsyen
    kept = [w for w in words if any(a <= (w["start"] + w["end"]) / 2 <= b for a, b in segs)]
    src_mapped = [dict(w, start=round(out_t(w["start"]), 3), end=round(out_t(w["end"]), 3)) for w in kept]
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
        # sfx: "soft" (lalai, SFX halus setiap B-roll) | "hit" (peralihan besar) | "none"
        # trans: "flash" (lalai) | "dissolve" (crossfade double-exposure) | "streak" (glitch streak putih) | "cut"
        cues.append(dict(name=f"{cid}_b{n}", t=round(max(0.0, t0), 3), dur=round(dur, 2), tpl=q["tpl"], data=q["data"],
                         source=q.get("source"), sfx=q.get("sfx", "soft"), riser=q.get("riser", False), trans=q.get("trans", "flash"),
                         hold=bool(q.get("until_end"))))
    H = C["hook"]
    # hook.style: "pip" (lalai: B-roll penuh + host dalam kad PiP) | "bgswap" (host penuh, latar studio diganti B-roll)
    #             | "type" (tipografi kinetik atas B-roll gelap, tiada host) | "host" (wajah host terus, teks hook slam)
    hs = (H or {}).get("style", "pip")
    #             | "broll" (B-roll / peta penuh skrin + teks hook, tiada host) | "glass" (host + kad kaca kabur berisi hook)
    if H and hs not in ("host", "glass"):
        pip_y = int(min(max(face_y[0] - 270, 0), 1920 - 540))
        cues.insert(0, dict(name=f"{cid}_hook", t=0.0, dur=H["dur"], tpl=H.get("tpl", "photo"),
                            data={k: v for k, v in H.items() if k not in ("dur", "tpl", "style", "text", "kicker", "highlight", "size", "small", "delay", "strike",
                                                                  "matting", "no_hair")},
                            source=None, sfx="hit", riser=False, trans="cut",
                            pip=pip_y if hs == "pip" else None, bgswap=hs == "bgswap"))
        if hs == "type":
            cues.insert(1, dict(name=f"{cid}_hooktype", t=0.0, dur=H["dur"], tpl="kinetic", source=None, sfx="none",
                                riser=False, trans="cut", data=dict(lines=H["text"], kicker=H.get("kicker"),
                                                                    highlight=H.get("highlight"), size=H.get("size", 150),
                                                                    small=H.get("small", []), delay=H.get("delay", []),
                                                                    strike=H.get("strike"))))
    if CTA:
        cues.append(dict(name=f"{cid}_cta", t=round(total, 3), dur=CTA["dur"], tpl=CTA["tpl"], data=CTA["data"], sfx="hit",
                         riser=False, source=None, trans="flash"))
    for a, b in zip(cues, cues[1:]):          # elak bertindih (lapisan hook boleh bertindih sesama sendiri)
        if a["t"] + a["dur"] > b["t"] - 0.3 and b["name"] != f"{cid}_cta" and not b["name"].startswith(f"{cid}_hook"):
            a["dur"] = round(b["t"] - 0.3 - a["t"], 2)

    # 5. JSON data B-roll
    for c in cues:
        if c["tpl"] == "highlight":
            d = json.load(open(f"{WORK}/{c['data']}.json"))
            d.update(duration=c["dur"], source=c["source"])
        else:
            d = dict(c["data"], duration=c["dur"])
            if c["source"]:
                d["source"] = c["source"]
        json.dump(d, open(f"{WORK}/{c['name']}.json", "w"), ensure_ascii=False)

    mapped = src_mapped
    end = total + (CTA["dur"] if CTA else 0)
    P = dict(segs=segs, shots=out_shots, cues=cues, total=round(total, 3), end=round(end, 3),
             hook_end=H["dur"] if H else 0, words=mapped)
    json.dump(P, open(f"{WORK}/{cid}.plan.json", "w"), ensure_ascii=False, indent=1)
    lens = [s["src"][1] - s["src"][0] for s in out_shots]
    print(f"{cid}: {len(segs)} segmen, {len(out_shots)} shot (purata {st.mean(lens):.2f}s), tempoh {total:.2f}s"
          + (f" + CTA {CTA['dur']}s" if CTA else ""))
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


def shot_chain(C, s, nfr):
    """Rantai penapis satu shot host (input -ss di s["src"][0]): crop -> 1080x1920 -> gerakan -> lift."""
    a, b = s["src"]; w, h, x, y = s["crop"]
    return (f"setpts=PTS-STARTPTS,crop={w}:{h}:{x}:{y},scale=1080:1920:flags=lanczos,setsar=1,fps={FPS},"
            f"{MOVES[s['move']].format(d=b - a) + ',' if s.get('move') else ''}"
            # config "lift" (px): naikkan footage, buang logo tertanam di atas; bawah hitam (ditutup banner)
            f"{'crop=1080:%d:0:%d,pad=1080:1920:0:0:black,' % (1920 - C['lift'], C['lift']) if C.get('lift') else ''}"
            f"tpad=stop_mode=clone:stop_duration=0.2,trim=end_frame={nfr},setpts=PTS-STARTPTS")


def render(cid):
    C = cfg(cid); P = json.load(open(f"{WORK}/{cid}.plan.json"))
    for c in P["cues"]:
        if c.get("bgswap"):                        # topeng orang untuk hook bgswap
            # topeng dikira atas shot pertama yang sudah diproses (crop/gerakan/lift) -> sepadan tepat dengan [vg]
            s0 = P["shots"][0]; hsrc = f"{WORK}/{cid}_hooksrc.mp4"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{s0['src'][0]:.3f}", "-t", f"{s0['src'][1] - s0['src'][0] + 0.1:.3f}",
                            "-i", C["src"], "-vf", shot_chain(C, s0, round((s0['src'][1] - s0['src'][0]) * FPS)), "-an",
                            "-c:v", "libx264", "-crf", "12", hsrc], check=True)
            subprocess.run(["python3", f"{BROLL}/tools/person_mask.py", hsrc, str(c["dur"] + 0.2),
                            f"{WORK}/{cid}_hookmask.mp4"] + (["--no-hair"] if C["hook"].get("no_hair") else [])
                           + (["--birefnet"] if C["hook"].get("matting") == "birefnet" else []), check=True)
    for c in P["cues"]:
        out = f"{WORK}/{c['name']}.mp4"
        if c["tpl"] == "footage":
            footage(f"{WORK}/{c['name']}.json", out)
            continue
        if c["tpl"] == "card":
            # kad teks: komposisi Remotion `Card` (remotion/src/card/Card.tsx), data JSON sama dengan card.html
            subprocess.run([f"{REMOTION}/node_modules/.bin/remotion", "render", "Card", out,
                            f"--props={WORK}/{c['name']}.json", "--log=error"], cwd=REMOTION, check=True)
            continue
        tpl = f"{BROLL}/templates/{c['tpl']}.html"
        if c["tpl"] == "kinetic":                  # tipografi kinetik lutsinar (ditindih atas host)
            d = json.load(open(f"{WORK}/{c['name']}.json")); d.update(alpha=True, fps=FPS)
            json.dump(d, open(f"{WORK}/{c['name']}.json", "w"), ensure_ascii=False)
            out = out[:-4] + ".mov"
        subprocess.run(["node", f"{BROLL}/tools/render.mjs", tpl, f"{WORK}/{c['name']}.json", out], check=True)


# Footage B-roll (video): sama gaya dengan templates/photo.html — warna bebas, tekstur & gerakan halus wajib.
# Data: { video (relatif work/), in (saat mula), duration, grade?, texture?, motion?, focus? }
# Tekstur: grain sentiasa (ffmpeg noise); 'halftone' / 'paper' ditindih dari photo.html (textureOnly).
FOOT_GRADE = dict(none="null", color="eq=contrast=1.08:saturation=0.95", bw="hue=s=0,eq=contrast=1.35:brightness=0.02",
                  sepia="hue=s=0,colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,eq=contrast=1.15",
                  bright="eq=brightness=0.12:contrast=0.82:saturation=0.85")
FOOT_MOVE = {"zoom-in": ("1+0.08*on/{n}", "{fx}*(iw-iw/zoom)", "{fy}*(ih-ih/zoom)"),
             "zoom-out": ("1.08-0.08*on/{n}", "{fx}*(iw-iw/zoom)", "{fy}*(ih-ih/zoom)"),
             "pan-left": ("1.1", "(iw-iw/zoom)*on/{n}", "{fy}*(ih-ih/zoom)"),
             "pan-right": ("1.1", "(iw-iw/zoom)*(1-on/{n})", "{fy}*(ih-ih/zoom)"),
             "pan-up": ("1.1", "{fx}*(iw-iw/zoom)", "(ih-ih/zoom)*on/{n}"),
             "pan-down": ("1.1", "{fx}*(iw-iw/zoom)", "(ih-ih/zoom)*(1-on/{n})")}


# Gerakan halus shot host (mod precut), d = tempoh shot: push-in 0->3% atau push-out 3%->0, komposisi asal kekal
MOVES = {"push": "scale=w='trunc(1080*(1+0.03*t/{d})/2)*2':h='trunc(1920*(1+0.03*t/{d})/2)*2':eval=frame:flags=bicubic,"
                 "crop=1080:1920:(iw-1080)/2:(ih-1920)*0.3,setsar=1",
         "pull": "scale=w='trunc(1080*(1.03-0.03*t/{d})/2)*2':h='trunc(1920*(1.03-0.03*t/{d})/2)*2':eval=frame:flags=bicubic,"
                 "crop=1080:1920:(iw-1080)/2:(ih-1920)*0.3,setsar=1"}


def footage(data_file, out):
    d = json.load(open(data_file))
    dur = max(1.5, d.get("duration", 2.5)); n = round(dur * FPS)
    foc = d.get("focus", {}); fx, fy = foc.get("x", 0.5), foc.get("y", 0.5)
    z, x, y = (e.format(n=n, fx=fx, fy=fy) for e in FOOT_MOVE[d.get("motion", "zoom-in")])
    vf = (f"scale=2160:3840:force_original_aspect_ratio=increase,crop=2160:3840:(iw-ow)*{fx}:(ih-oh)*{fy},fps={FPS},"
          f"{d.get('ffilter') or FOOT_GRADE[d.get('grade', 'color')]},"
          f"zoompan=z='{z}':x='{x}':y='{y}':d=1:s=1080x1920:fps={FPS},"
          "noise=c0s=16:allf=t+u,vignette=angle=PI/4.5")
    inp = ["-ss", str(d.get("in", 0)), "-t", f"{dur + 0.5}", "-i", os.path.join(WORK, d["video"])]
    extra = [k for k in d.get("texture", []) if k in ("halftone", "paper")]
    if extra:
        tj, tp = data_file[:-5] + "_tex.json", data_file[:-5] + "_tex.png"
        json.dump(dict(textureOnly=True, texture=extra), open(tj, "w"))
        subprocess.run(["node", f"{BROLL}/tools/still.mjs", f"{BROLL}/templates/photo.html", tj, tp, "0"], check=True,
                       capture_output=True)
        inp += ["-i", tp]
        fc = f"[0:v]{vf}[v];[v][1:v]overlay=0:0,format=yuv420p[o]"
    else:
        fc = f"[0:v]{vf},format=yuv420p[o]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex", fc, "-map", "[o]", "-frames:v", str(n),
                    "-c:v", "libx264", "-crf", "18", "-r", str(FPS), "-an", out], check=True)
    print("ok", out, n, "frame")


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


def swell(rng, dur=0.9, peak=0.07):
    """SFX halus masuk B-roll: nada rendah naik perlahan + udara, di bawah VO."""
    n = int(dur * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(np.interp(t, [0, dur], [62, 96])) / SR)
    air = onepole(rng.standard_normal(n), np.full(n, 0.03))
    s = 0.6 * body + 0.4 * air / (np.abs(air).max() + 1e-9)
    return s * np.sin(np.pi * t / dur) ** 2 * peak


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
    total = P["end"]
    rng = np.random.default_rng(1)
    n = int(total * SR) + SR
    music = np.zeros(n); sfx = np.zeros(n)
    M = cfg(cid).get("music")
    if M:   # fail muzik pengguna: ulang/potong ikut tempoh, fade out 2s di hujung
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-stream_loop", "-1", "-i", os.path.join(BROLL, M["file"]), "-t", f"{total:.3f}",
                        "-af", f"afade=t=in:d=0.3,afade=t=out:st={max(0, total - 2):.3f}:d=2", "-ar", str(SR), "-ac", "2",
                        f"{WORK}/{cid}_music.wav"], check=True)
    else:
        b = bed(total); music[:len(b)] += b

    def put(sig, t):
        i = int(t * SR)
        if i < 0: sig, i = sig[-i:], 0
        e = min(n, i + len(sig)); sfx[i:e] += sig[:e - i]
    # jump cut host tanpa SFX; setiap B-roll: SFX halus; peralihan besar ("hit"): whoosh kuat + impact
    for c in P["cues"]:
        if c["sfx"] == "hit":
            put(whoosh(rng, .55, .32), c["t"] - .3)
            put(hit(rng), c["t"])
        elif c["sfx"] != "none":
            put(whoosh(rng, .7, .12), c["t"] - .45)
            put(swell(rng), c["t"] - .3)
        if c["riser"]:
            put(riser(rng), c["t"] - 1.6)
    for name, sig in ((("sfx", sfx),) if M else (("music", music), ("sfx", sfx))):
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
{{STYLES}}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    def fmt(ws, hook, pop=None):
        # Inggeris & Arab: italic (putih); hook: baris 1 besar, selebihnya baris 2 lebih kecil
        parts = [(r"{\i1}" + w["txt"] + r"{\i0}") if w["eng"] or w["arab"] else w["txt"] for w in ws]
        if pop:   # perkataan baru "pop" masuk: pudar + skala 75% -> 106% -> 100% (pop = alfa sasaran lapisan)
            parts[-1] = (r"{\1a&HFF&\fscx75\fscy75\t(0,80,\1a&H" + pop + r"&\fscx106\fscy106)\t(80,160,\fscx100\fscy100)}"
                         + parts[-1])
        if not hook:
            return " ".join(parts)
        n1, width = 0, 0
        while n1 < len(ws) and (n1 == 0 or width + 1 + len(ws[n1]["txt"]) <= 11):
            width += (1 if n1 else 0) + len(ws[n1]["txt"]); n1 += 1
        line2 = " ".join(parts[n1:])
        return " ".join(parts[:n1]) + (r"\N{\fs72}" + line2 if line2 else "")

    # config "soft_caps" (Ep7): Inter Bold, jarak huruf -1, tiada stroke, bayang lembut kabur (lapisan bayang
    # berasingan dengan \blur), setiap perkataan baru animasi pop. Lalai: gaya v2 (Inter ExtraBold + outline).
    soft = C.get("soft_caps")
    if soft:
        STYLES = ("Style: Cap,Inter,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,-1,0,1,0,0,5,60,60,0,1\n"
                  "Style: Hook,Inter,104,&H0000D4FF,&H0000D4FF,&H00000000,&H00000000,1,0,0,0,100,100,-1,0,1,0,0,8,60,60,0,1\n"
                  "Style: CapSh,Inter,66,&H6E000000,&H6E000000,&H00000000,&H00000000,1,0,0,0,100,100,-1,0,1,0,0,5,60,60,0,1\n"
                  "Style: HookSh,Inter,104,&H5A000000,&H5A000000,&H00000000,&H00000000,1,0,0,0,100,100,-1,0,1,0,0,8,60,60,0,1")
    else:
        STYLES = ("Style: Cap,Inter ExtraBold,66,&H00FFFFFF,&H00FFFFFF,&H64000000,&H8C000000,1,0,0,0,100,100,-2,0,1,2,4,5,60,60,0,1\n"
                  "Style: Hook,Inter ExtraBold,104,&H0000D4FF,&H0000D4FF,&H64000000,&H8C000000,1,0,0,0,100,100,-3,0,1,2,5,8,60,60,0,1")
    head = head.replace("{STYLES}", STYLES)

    def emit(s_, e_, style, x, y, tags, text_fn):
        """Satu kapsyen; soft: lapisan bayang kabur (offset 5px) di bawah teks tanpa stroke."""
        if soft:
            lines.append(f"Dialogue: 0,{ass_time(s_)},{ass_time(e_)},{style}Sh,,0,0,0,,"
                         + "{" + f"\\pos({x},{y + 5})\\blur9" + tags + "}" + text_fn("6E" if style == "Cap" else "5A"))
            lines.append(f"Dialogue: 1,{ass_time(s_)},{ass_time(e_)},{style},,0,0,0,,"
                         + "{" + f"\\pos({x},{y})" + tags + "}" + text_fn("00"))
        else:
            lines.append(f"Dialogue: 0,{ass_time(s_)},{ass_time(e_)},{style},,0,0,0,,"
                         + "{" + f"\\pos({x},{y})" + tags + "}" + text_fn(None))

    # kapsyen terkumpul: perkataan muncul satu demi satu dalam kumpulan 1-4, kemudian reset
    lines = []
    H = C["hook"] or {}
    if H.get("text"):
        # hook bertulis (config hook.text = [baris 1, baris 2]): kuning besar di atas sepanjang hook,
        # kapsyen ucapan bermula selepas hook
        if soft:
            # Ep7: Inter Black, saiz seragam terbesar yang muat lebar 960px (maks 150px), satu baris setiap item
            from PIL import ImageFont
            def width(sz):
                f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Black.otf", sz)
                return max(f.getlength(t) - sz * 0.01 * (len(t) - 1) for t in H["text"])
            hs = H.get("style", "pip")
            fs, maxw = 150, (820 if hs == "glass" else 960)
            while fs > 60 and width(fs) > maxw:
                fs -= 2
            base = r"\an8\fnInter Black\b0\fs" + str(fs)
            # host penuh skrin: teks di bawah muka (atas baju); glass: dalam kad kaca
            y = {"pip": 400, "broll": 400, "glass": 1050}.get(hs, 990)
            if hs == "host":
                # slam perkataan demi perkataan: 140% -> 100%, pudar masuk 0.12s
                ws = [(w, li) for li, t in enumerate(H["text"]) for w in t.split()]
                step = min(0.22, 0.55 * P["hook_end"] / len(ws))
                for k in range(len(ws)):
                    def txt(al, k=k):
                        out, prev_li = "", 0
                        for j, (w, li) in enumerate(ws[:k + 1]):
                            out += (r"\N" if li != prev_li else (" " if j else "")); prev_li = li
                            out += (r"{\1a&HFF&\fscx140\fscy140\t(0,120,\1a&H" + al + r"&\fscx100\fscy100)}" + w
                                    + r"{\fscx100\fscy100}") if j == k else w
                        return out
                    end = P["hook_end"] if k == len(ws) - 1 else 0.12 + (k + 1) * step
                    emit(0.12 + k * step, end, "Hook", 540, y, base, txt)
            elif hs != "type":                          # "type": teks hook dalam lapisan kinetik
                emit(0, P["hook_end"], "Hook", 540, y, r"\fad(120,150)" + base, lambda _a: r"\N".join(H["text"]))
        else:
            l1, l2 = H["text"]
            emit(0, P["hook_end"], "Hook", 540, 430, r"\an8\fad(120,150)\fs90", lambda _a: l1 + r"\N{\fs66}" + l2)
        caps = [c for c in caps if c[0]["start"] >= P["hook_end"] - 0.05]
    for k, c in enumerate(caps):
        a = c[0]["start"]
        nxt = caps[k + 1][0]["start"] if k + 1 < len(caps) else P["total"] + 0.3
        b = nxt if nxt - c[-1]["end"] < 0.45 else c[-1]["end"] + 0.2
        b = min(max(b, a + 0.25), nxt) if nxt > a else b
        hook = a < P.get("hook_end", 0) and not H.get("text")
        style, x, y, tags = ("Hook", 540, 460, r"\an8") if hook else ("Cap", 540, 1356, "")
        for j in range(len(c)):
            s = a if j == 0 else max(a, c[j]["start"])
            e = b if j == len(c) - 1 else min(b, c[j + 1]["start"])
            if e - s < 0.02:
                continue
            emit(s, e, style, x, y, tags, lambda al, ws=c[:j + 1], hk=hook: fmt(ws, hk, al if soft else None))
    open(f"{WORK}/{cid}.ass", "w").write(head + "\n".join(lines) + "\n")
    return len(caps)


def assemble(cid):
    C = cfg(cid); P = json.load(open(f"{WORK}/{cid}.plan.json"))
    ncap = captions(cid, P)
    total = P["end"]
    # gradien gelap atas: tutup logo asal dalam footage (zon UI platform)
    from PIL import Image, ImageDraw, ImageFilter
    g = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0)); px = g.load()
    for y in range(0, 360):
        a = 255 if y < 215 else int(255 * (1 - (y - 215) / 145) ** 1.6)
        for x in range(1080): px[x, y] = (0, 0, 0, a)
    g.save(f"{WORK}/topfade.png")
    # peralihan glitch streak: 2 frame jalur putih menegak
    rng = np.random.default_rng(3)
    for k in range(2):
        al = np.full((1920, 1080), 0.12, np.float32)
        for _ in range(70):
            x0 = int(rng.integers(0, 1080)); al[:, x0:x0 + int(rng.integers(1, 12))] = rng.uniform(.25, .95)
        al *= rng.uniform(.7, 1, (1920, 1)).astype(np.float32)
        s = Image.merge("RGBA", [Image.new("L", (1080, 1920), 255)] * 3 + [Image.fromarray((al * 255).astype(np.uint8))])
        s.filter(ImageFilter.GaussianBlur(1.5)).save(f"{WORK}/streak{k}.png")
    # topeng bucu bulat 28px untuk PiP host (hook)
    m = Image.new("L", (900, 450), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 899, 449), 28, fill=255)
    m.save(f"{WORK}/pipmask.png")

    inp = ["-i", C["src"], "-i", f"{WORK}/topfade.png", "-i", f"{WORK}/{cid}_music.wav", "-i", f"{WORK}/{cid}_sfx.wav",
           "-i", f"{WORK}/streak0.png", "-i", f"{WORK}/streak1.png", "-i", f"{WORK}/pipmask.png"]
    B0 = 7                                         # indeks input B-roll pertama
    for c in P["cues"]:
        inp += ["-i", f"{WORK}/{c['name']}.{'mov' if c['tpl'] == 'kinetic' else 'mp4'}"]
    swap = [c for c in P["cues"] if c.get("bgswap")]
    if swap:
        inp += ["-i", f"{WORK}/{cid}_hookmask.mp4"]
    fc, chains = [], []
    as_ = []
    acc = 0.0
    for k, s in enumerate(P["shots"]):
        a, b = s["src"]; w, h, x, y = s["crop"]
        # bilangan frame ikut masa audio kumulatif tepat -> tiada drift A/V terkumpul (maks 1/2 frame)
        nfr = round((acc + b - a) * FPS) - round(acc * FPS); acc += b - a
        # setiap shot = input sendiri (-ss/-t): trim dari satu [0:v] menimbun frame dalam RAM (OOM untuk sumber panjang)
        chains.append(shot_chain(C, s, nfr))
        fc.append(f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,afade=t=in:d=0.012,afade=t=out:st={b - a - (0.08 if k == len(P["shots"]) - 1 else 0.012):.3f}:d={0.08 if k == len(P["shots"]) - 1 else 0.012}[a{k}]")
        as_.append(f"[a{k}]")
    n = len(P["shots"])
    # shot host dirender satu-satu ke klip cache (-ss/-t, RAM rendah), dicantum -> satu input [hv]
    # (trim banyak cabang dari satu [0:v] menimbun frame dalam RAM -> OOM untuk sumber panjang)
    import hashlib
    os.makedirs(f"{WORK}/shots", exist_ok=True)
    clips = []
    for k, (s, ch) in enumerate(zip(P["shots"], chains)):
        a, b = s["src"]
        key = hashlib.md5(f"{C['src']}|{a}|{b}|{ch}".encode()).hexdigest()[:10]
        clip = f"{WORK}/shots/{cid}_{k:02d}_{key}.mp4"
        if not os.path.exists(clip):
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a + 0.1:.3f}", "-i", C["src"],
                            "-vf", ch, "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "12", "-r", str(FPS), clip + ".tmp.mp4"], check=True)
            os.replace(clip + ".tmp.mp4", clip)
        clips.append(clip)
    open(f"{WORK}/{cid}_shots.txt", "w").write("".join(f"file '{c}'\n" for c in clips))
    host = f"{WORK}/{cid}_host.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{WORK}/{cid}_shots.txt", "-c", "copy", host], check=True)
    hv = len([x for x in inp if x == "-i"]); inp += ["-i", host]
    fc.append(f"[{hv}:v]setpts=PTS-STARTPTS[vc]")
    fc.append("".join(as_) + f"concat=n={n}:v=0:a=1[ac]")
    # gred host v2: warna asal studio (ungu/hijau), kulit hangat, kontras sederhana, vignette ringan
    # config "grade": rantai penapis ffmpeg ganti gred lalai (cth. Ep7: hitam dalam, kulit hangat, vignette pada muka)
    grade = C.get("grade") or "eq=contrast=1.05:saturation=1.04,colorbalance=rm=0.025:gm=0.005:bm=-0.02,vignette=angle=PI/5"
    fc.append(f"[vc]tpad=stop_mode=clone:stop_duration={total - P['total'] + 0.5},"
              f"{grade},noise=alls=4:allf=t,format=yuv420p[vg]")
    pip = [c for c in P["cues"] if c.get("pip") is not None]
    if (C.get("hook") or {}).get("style") == "glass":
        # kad kaca (glassmorphism): kawasan footage di belakang kad di-blur + digelapkan (kaca asap, teks kuning kontras), bucu bulat, tepi & kilauan, lencana LIVE
        gx, gy, gw, gh, hd = 80, 960, 920, 460, P["hook_end"]
        gm = Image.new("L", (gw, gh), 0); ImageDraw.Draw(gm).rounded_rectangle((0, 0, gw - 1, gh - 1), 44, fill=255)
        gm.save(f"{WORK}/glassmask.png")
        ge = Image.new("RGBA", (gw, gh), (0, 0, 0, 0)); d = ImageDraw.Draw(ge)
        for yy in range(gh // 2):                          # kilauan atas
            d.line([(0, yy), (gw, yy)], fill=(255, 255, 255, int(38 * (1 - yy / (gh / 2)) ** 2)))
        ge.putalpha(Image.composite(ge.getchannel("A"), Image.new("L", (gw, gh), 0), gm))
        d = ImageDraw.Draw(ge)
        d.rounded_rectangle((1, 1, gw - 2, gh - 2), 44, outline=(255, 255, 255, 110), width=3)
        from PIL import ImageFont
        fnt = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 30)
        d.rounded_rectangle((36, 30, 176, 78), 24, fill=(227, 38, 43, 235))
        d.ellipse((54, 46, 70, 62), fill=(255, 255, 255, 255)); d.text((80, 35), "LIVE", font=fnt, fill=(255, 255, 255, 255))
        ge.save(f"{WORK}/glassedge.png")
        inp += ["-loop", "1", "-i", f"{WORK}/glassmask.png", "-loop", "1", "-i", f"{WORK}/glassedge.png"]
        gi = len([x for x in inp if x == "-i"]) - 2
        fc.append(f"[vg]split=2[vgm][vgk]")
        fc.append(f"[vgk]crop={gw}:{gh}:{gx}:{gy},gblur=sigma=26,eq=brightness=-0.22:saturation=1.1,format=yuva420p[gk0];"
                  f"[{gi}:v]format=gray[gkm];[gk0][gkm]alphamerge,fade=t=in:d=0.25:alpha=1,"
                  f"fade=t=out:st={hd - 0.25:.3f}:d=0.25:alpha=1[gk]")
        fc.append(f"[vgm][gk]overlay={gx}:{gy}:enable='between(t,0,{hd})'[vg1];"
                  f"[{gi + 1}:v]format=rgba,fade=t=in:d=0.25:alpha=1,fade=t=out:st={hd - 0.25:.3f}:d=0.25:alpha=1[ge];"
                  f"[vg1][ge]overlay={gx}:{gy}:enable='between(t,0,{hd})'[vt]")
    elif swap:
        # host penuh (gerakan sama dengan shot pertama) dipotong keluar guna topeng -> atas B-roll hook
        hd, s0 = swap[0]["dur"], P["shots"][0]
        mv = ""                                    # topeng sudah termasuk gerakan shot pertama (lihat render)
        fc.append("[vg]split=2[vgm][vgp]")
        fc.append(f"[vgp]trim=end={hd},setpts=PTS-STARTPTS,format=yuva420p[pp0]")
        fc.append(f"[{B0 + len(P['cues'])}:v]trim=end={hd},setpts=PTS-STARTPTS,fps={FPS},{mv}format=gray[pm];[pp0][pm]alphamerge[pp]")
        fc.append("[vgm]null[vt]")
    elif pip:
        hd = pip[0]["dur"]
        fc.append("[vg]split=2[vgm][vgp]")
        fc.append(f"[vgp]trim=end={hd},setpts=PTS-STARTPTS,crop=1080:540:0:{pip[0]['pip']},scale=900:450,format=yuva420p[pp0]")
        fc.append("[6:v]format=gray[pm];[pp0][pm]alphamerge[pp]")
        fc.append("[vgm][1:v]overlay=0:0[vt]" if C.get("topfade", True) else "[vgm]null[vt]")
    else:
        # gradien gelap atas hanya untuk footage yang ada logo asal (config "topfade": false -> komposisi asal)
        fc.append("[vg][1:v]overlay=0:0[vt]" if C.get("topfade", True) else "[vg]null[vt]")
    last = "[vt]"
    for i, c in enumerate(P["cues"]):
        t, d = c["t"], c["dur"]
        if c["tpl"] in ("photo", "footage", "map", "news"):
            # B-roll penuh skrin: fade alpha (dissolve = crossfade double-exposure 0.3s), keluar crossfade 0.2s
            fin = f"fade=t=in:st=0:d=0.3:alpha=1," if c.get("trans") == "dissolve" else ""
            fout = "" if c.get("hold") else f"fade=t=out:st={max(0, d - 0.2):.3f}:d=0.2:alpha=1,"   # penutup: kekal hingga akhir
            # config "chroma" (px): chromatic aberration merah/biru pada B-roll (rujukan APHD)
            ca = f"rgbashift=rh=-{C['chroma']}:bh={C['chroma']}:rv=1:bv=-1:edge=smear," if C.get("chroma") else ""
            fc.append(f"[{B0 + i}:v]{ca}format=yuva420p,{fin}{fout}"
                      f"setpts=PTS-STARTPTS+{t}/TB[b{i}]")
        elif c["tpl"] == "kinetic" and c["name"].endswith("_hooktype"):
            fc.append(f"[{B0 + i}:v]setpts=PTS-STARTPTS+{t}/TB[b{i}]")   # intro tipografi: B-roll di bawah kekal tajam
        elif c["tpl"] == "kinetic":
            # host di bawah teks: blur + gelap, masuk/keluar beransur 0.35s
            # latar kabur dari input host sendiri (-ss): cabang split+trim menahan semua frame sebelum t dalam RAM
            ki = len([x for x in inp if x == "-i"]); inp += ["-ss", f"{t:.3f}", "-t", f"{d + 0.2:.3f}", "-i", host]
            fc.append(f"[{ki}:v]setpts=PTS-STARTPTS,tpad=stop_mode=clone:stop_duration={d},trim=duration={d},{grade},gblur=sigma=16,"
                      f"eq=brightness=-0.16:saturation=0.75,format=yuva420p,fade=t=in:d=0.35:alpha=1,"
                      f"fade=t=out:st={max(0, d - 0.35):.3f}:d=0.35:alpha=1,setpts=PTS-STARTPTS+{t}/TB[k{i}c];"
                      f"{last}[k{i}c]overlay=0:0:eof_action=pass[k{i}d]")
            last = f"[k{i}d]"
            fc.append(f"[{B0 + i}:v]setpts=PTS-STARTPTS+{t}/TB[b{i}]")
        else:
            fc.append(f"[{B0 + i}:v]setpts=PTS-STARTPTS+{t}/TB[b{i}]")
        fc.append(f"{last}[b{i}]overlay=0:0:eof_action=pass:enable='between(t,{t},{t + d - 0.02})'[o{i}]")
        last = f"[o{i}]"
        if c.get("pip") is not None or c.get("bgswap"):
            xy = "0:0" if c.get("bgswap") else "90:1000"
            fc.append(f"{last}[pp]overlay={xy}:eof_action=pass:enable='between(t,0,{d - 0.02})'[o{i}p]")
            last = f"[o{i}p]"
    for i, c in enumerate(c for c in P["cues"] if c.get("trans") == "streak"):
        for k in range(2):
            a = c["t"] - 0.04 + k * 0.07
            fc.append(f"{last}[{4 + k}:v]overlay=0:0:enable='between(t,{a:.3f},{a + 0.07:.3f})'[s{i}{k}]")
            last = f"[s{i}{k}]"
    flashes = ",".join(f"drawbox=x=0:y=0:w=iw:h=ih:color=white@0.5:t=fill:enable='between(t,{c['t'] - 0.03},{c['t'] + 0.06})'"
                       for c in P["cues"] if c.get("trans", "flash") == "flash")
    fc.append(f"{last}{flashes + ',' if flashes else ''}ass={WORK}/{cid}.ass:fontsdir=/usr/share/fonts/opentype/inter,"
              f"trim=duration={total},format=yuv420p[vout]")
    # audio: VO bersih + bed + SFX, kemudian master
    fc.append("[ac]highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=120:makeup=2,"
              f"apad=whole_dur={total},aresample=48000,aformat=channel_layouts=stereo[vo]")
    fc.append(f"[2:a]volume={(C.get('music') or {}).get('volume', 0.075)},aformat=channel_layouts=stereo[mu]")
    fc.append(f"[3:a]volume=0.55,aformat=channel_layouts=stereo[fx]")
    fc.append(f"[vo][mu][fx]amix=inputs=3:normalize=0:duration=first,atrim=duration={total}[mix]")
    stills = os.environ.get("STILLS")              # STILLS="3.2,12,40": screencap satu frame (overlay penuh), tiada render video
    if stills:
        ts = sorted(float(x) for x in stills.split(","))     # select keluarkan frame ikut urutan masa
        sel = "+".join(f"eq(n,{round(t * FPS)})" for t in ts)
        fc.append(f"movie={REPO}/template/overlay_1080x1920.png[ov];[vout][ov]overlay=0:0,select='{sel}'[vs];[ac]anullsink")
        open(f"{WORK}/{cid}.fc.txt", "w").write(";\n".join(x for x in fc if not x.startswith(("[ac]", "[2:a]", "[3:a]", "[vo]"))))
        subprocess.run(["ffmpeg", "-v", "error", "-y", *inp, "-filter_complex_script", f"{WORK}/{cid}.fc.txt",
                        "-map", "[vs]", "-fps_mode", "passthrough", "-frames:v", str(len(ts)), f"{WORK}/{cid}_still_%02d.png"], check=True)
        for k, t in enumerate(ts, 1):
            os.replace(f"{WORK}/{cid}_still_{k:02d}.png", f"{WORK}/{cid}_t{t:05.1f}.png")
            print(f"{WORK}/{cid}_t{t:05.1f}.png")
        return
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
            off = 0 if side in ("left", "full") else f.shape[1] - 1100
            g = cv2.cvtColor(f[:, off:] if side == "full" else f[:, off:off + 1100], cv2.COLOR_BGR2GRAY)
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
    cfg(cid)
    subprocess.run([f"{REPO}/template/apply_overlay.sh", f"{WORK}/{cid}_pre.mp4", f"{WORK}/{cid}_final.mp4", str(FPS)],
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
