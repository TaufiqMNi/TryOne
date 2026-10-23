"""Build the girly/cute voiceless affiliate edit from the raw clips.

Usage: python3 build.py            -> out/final.mp4
Steps: cut + grade segments (ffmpeg) -> composite graphics per frame (Pillow)
       -> synth SFX (numpy) -> mux.
"""
import math
import os
import random
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(HERE, "out")
TMP = os.path.join(OUT, "tmp")
FONT = os.path.join(HERE, "fonts", "Kindergarten.ttf")
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"

W, H, FPS = 1080, 1920, 30
SR = 44100

PINK = (255, 61, 139)
PINK_LIGHT = (255, 182, 213)
PINK_SOFT = (255, 222, 236)
WHITE = (255, 255, 255)

# src, start (s), output duration (s), speed, caption, emojis [(char, dx, dy, size, angle)], extra fx
SEGMENTS = [
    dict(src="IMG_6889.MOV", ss=0.0, dur=2.6, speed=1.0,
         text="obsessed gila\ndgn kasut ni",
         emojis=[("🥹", 380, -95, 120, 12), ("🎀", -400, -110, 110, -18)], fx=["hearts_burst"]),
    dict(src="IMG_6868.MOV", ss=0.6, dur=2.0, speed=1.0,
         text="before: plain & boring...", emojis=[("😐", 330, -60, 100, 10)], fx=[]),
    dict(src="IMG_6875.MOV", ss=26.0, dur=2.6, speed=1.0,
         text="after letak charms,\nso cute!!",
         emojis=[("✨", -360, -80, 110, -10), ("💖", 360, -70, 110, 12)], fx=["sparkles", "chime"]),
    dict(src="IMG_6877.MOV", ss=0.0, dur=3.0, speed=1.0,
         text="charms pink + ribbon\nsuper comel", emojis=[("🎀", 380, -100, 120, 15)], fx=[]),
    dict(src="IMG_6890.MOV", ss=4.0, dur=3.0, speed=1.0,
         text="ada flower, heart &\nribbon gingham",
         emojis=[("🌸", -390, -100, 105, -12), ("💗", 390, -90, 100, 14)], fx=["sparkles"]),
    dict(src="IMG_6890.MOV", ss=0.0, dur=2.2, speed=1.0,
         text="gummy bear berkilat\ncute gila", emojis=[("🧸", 380, -70, 110, 10)], fx=["sparkles"]),
    dict(src="IMG_6889.MOV", ss=10.0, dur=2.6, speed=1.0,
         text="strap boleh adjust\njadi mary jane look",
         emojis=[("🥿", 390, -100, 115, 12), ("✨", -390, -95, 95, -10)], fx=["boing"]),
    dict(src="IMG_6876.MOV", ss=0.2, dur=2.6, speed=1.0,
         text="super ringan & selesa\npakai all day pun ok", emojis=[("☁️", 370, -100, 115, 12)], fx=[]),
    dict(src="IMG_6889.MOV", ss=31.0, dur=3.6, speed=1.0,
         text="nak jugak?\ntekan beg kuning!",
         emojis=[("🛒", 390, -110, 120, 12), ("💕", -390, -100, 105, -12)],
         fx=["cta", "sparkles", "hearts_burst"]),
]


# ---------------------------------------------------------------- helpers

def ease_out_back(x, s=1.9):
    x = min(max(x, 0.0), 1.0) - 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def ease_out(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def emoji_sprite(ch, size):
    f = ImageFont.truetype(EMOJI_FONT, 109)
    im = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    im = im.crop(im.getbbox())
    s = size / max(im.size)
    im = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    # white sticker outline
    pad = 14
    big = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    big.paste(im, (pad, pad), im)
    a = big.split()[3].filter(ImageFilter.MaxFilter(13))
    outline = Image.new("RGBA", big.size, WHITE + (0,))
    outline.putalpha(a)
    shadow = Image.new("RGBA", big.size, PINK_LIGHT + (0,))
    shadow.putalpha(a.point(lambda v: int(v * 0.9)))
    res = Image.new("RGBA", (big.width + 8, big.height + 8), (0, 0, 0, 0))
    res.alpha_composite(shadow, (8, 8))
    res.alpha_composite(outline, (0, 0))
    res.alpha_composite(big, (0, 0))
    return res


def heart_sprite(size, color):
    s = 4
    im = Image.new("RGBA", (size * s, size * s), (0, 0, 0, 0))
    pts = []
    for i in range(200):
        t = 2 * math.pi * i / 200
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((size * s / 2 + x * size * s / 36, size * s / 2.2 - y * size * s / 36))
    ImageDraw.Draw(im).polygon(pts, fill=color)
    return im.resize((size, size), Image.LANCZOS)


def sparkle_sprite(size):
    s = 4
    n = size * s
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = n / 2
    k = n * 0.09
    d.polygon([(c, 0), (c + k, c - k), (n, c), (c + k, c + k), (c, n), (c - k, c + k), (0, c), (c - k, c - k)],
              fill=WHITE + (255,))
    glow = im.filter(ImageFilter.GaussianBlur(n * 0.06))
    tint = Image.new("RGBA", im.size, PINK + (0,))
    tint.putalpha(glow.split()[3])
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(tint)
    out.alpha_composite(tint)
    out.alpha_composite(im)
    return out.resize((size, size), Image.LANCZOS)


def caption_card(text, size=88):
    font = ImageFont.truetype(FONT, size)
    lines = text.split("\n")
    tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    boxes = [tmp.textbbox((0, 0), ln, font=font, stroke_width=1) for ln in lines]
    lw = [b[2] - b[0] for b in boxes]
    lh = int(size * 1.15)
    tw, th = max(lw), lh * len(lines)
    px, py = 58, 40
    cw, ch = tw + px * 2, th + py * 2
    pad = 30
    card = Image.new("RGBA", (cw + pad * 2, ch + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(card)
    r = 56
    # soft pink drop shadow
    sh = Image.new("RGBA", card.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle((pad + 10, pad + 14, pad + cw + 10, pad + ch + 14), r, fill=PINK_LIGHT + (255,))
    card.alpha_composite(sh)
    d.rounded_rectangle((pad, pad, pad + cw, pad + ch), r, fill=WHITE + (245,), outline=PINK_LIGHT + (255,), width=8)
    # dotted inner trim
    inset = 20
    x0, y0, x1, y1 = pad + inset, pad + inset, pad + cw - inset, pad + ch - inset
    step = 22
    for x in range(int(x0 + r / 2), int(x1 - r / 2), step):
        d.ellipse((x - 3, y0 - 3, x + 3, y0 + 3), fill=PINK_LIGHT + (255,))
        d.ellipse((x - 3, y1 - 3, x + 3, y1 + 3), fill=PINK_LIGHT + (255,))
    for i, ln in enumerate(lines):
        b = boxes[i]
        x = pad + px + (tw - lw[i]) / 2 - b[0]
        y = pad + py + i * lh + (lh - size) / 2 - size * 0.12
        d.text((x, y), ln, font=font, fill=PINK, stroke_width=1, stroke_fill=PINK)
    return card


def paste_center(base, sprite, cx, cy, scale=1.0, angle=0.0, alpha=1.0):
    if scale <= 0.01 or alpha <= 0.01:
        return
    sp = sprite
    if abs(scale - 1) > 1e-3:
        sp = sp.resize((max(1, int(sp.width * scale)), max(1, int(sp.height * scale))), Image.BILINEAR)
    if abs(angle) > 0.1:
        sp = sp.rotate(angle, expand=True, resample=Image.BICUBIC)
    if alpha < 1:
        a = sp.split()[3].point(lambda v: int(v * alpha))
        sp = sp.copy()
        sp.putalpha(a)
    x, y = int(cx - sp.width / 2), int(cy - sp.height / 2)
    if x >= base.width or y >= base.height or x + sp.width <= 0 or y + sp.height <= 0:
        return
    base.alpha_composite(sp, (max(x, 0), max(y, 0)), (max(-x, 0), max(-y, 0)))


# ---------------------------------------------------------------- video

def cut_segments():
    os.makedirs(TMP, exist_ok=True)
    paths = []
    for i, s in enumerate(SEGMENTS):
        p = os.path.join(TMP, f"seg{i}.mp4")
        n = round(s["dur"] * FPS)
        vf = (f"setpts=PTS/{s['speed']},fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,"
              f"crop={W}:{H},eq=saturation=1.08:brightness=0.025:contrast=1.03,"
              f"colorbalance=rs=0.05:gs=-0.01:bs=0.03:rm=0.04:bm=0.02")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(s["ss"]), "-i", os.path.join(RAW, s["src"]),
                        "-vf", vf, "-frames:v", str(n), "-an", "-pix_fmt", "yuv420p",
                        "-c:v", "libx264", "-crf", "14", "-preset", "fast", p], check=True)
        paths.append((p, n))
    return paths


def read_frames(path, n):
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                            stdout=subprocess.PIPE)
    last = None
    for _ in range(n):
        buf = proc.stdout.read(W * H * 3)
        if len(buf) == W * H * 3:
            last = Image.frombuffer("RGB", (W, H), buf, "raw", "RGB", 0, 1)
        yield last
    proc.stdout.close()
    proc.wait()


def render_video(segs):
    rng = random.Random(7)
    sparkle = sparkle_sprite(90)
    hearts = [heart_sprite(sz, c + (230,)) for sz in (40, 56, 72) for c in (PINK, PINK_LIGHT, WHITE)]
    arrow = Image.new("RGBA", (200, 230), (0, 0, 0, 0))
    ad = ImageDraw.Draw(arrow)
    ad.polygon([(60, 0), (140, 0), (140, 120), (195, 120), (100, 225), (5, 120), (60, 120)],
               fill=PINK + (255,), outline=WHITE + (255,), width=8)

    # ambient floating hearts across the whole video
    total = sum(n for _, n in segs)
    floaters = [dict(x=rng.uniform(60, W - 60), t0=rng.uniform(-120, total), spd=rng.uniform(2.2, 4.0),
                     sp=rng.choice(hearts), ph=rng.uniform(0, 6.28)) for _ in range(8)]

    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                            "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-crf", "17", "-preset", "medium",
                            "-pix_fmt", "yuv420p", os.path.join(TMP, "video.mp4")], stdin=subprocess.PIPE)
    g = 0
    for si, (path, n) in enumerate(segs):
        s = SEGMENTS[si]
        card = caption_card(s["text"], 96 if "cta" in s["fx"] else 88)
        cap_y = 640 if "cta" in s["fx"] else 360
        emo = [(emoji_sprite(c, sz), dx, dy, ang) for (c, dx, dy, sz, ang) in s["emojis"]]
        sparks = [(rng.uniform(140, W - 140), rng.uniform(700, 1500), rng.uniform(0.6, 1.2), rng.uniform(0, 6.28))
                  for _ in range(7)]
        burst = [(rng.uniform(0, 2 * math.pi), rng.uniform(9, 22), rng.choice(hearts)) for _ in range(16)]
        for f, frame in enumerate(read_frames(path, n)):
            # punch-in at the cut + slow push
            z = 1.0 + 0.10 * (1 - ease_out(f / 9)) + 0.035 * f / n
            fr = frame
            if z > 1.001:
                cw, ch = W / z, H / z
                fr = frame.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
            im = fr.convert("RGBA")

            # pink flash on cut
            if si > 0 and f < 5:
                fl = Image.new("RGBA", (W, H), (255, 225, 238, int(170 * (1 - f / 5))))
                im.alpha_composite(fl)

            # floating hearts
            for fl in floaters:
                age = g - fl["t0"]
                if age < 0:
                    continue
                y = H + 60 - age * fl["spd"]
                if -80 < y < H + 80:
                    x = fl["x"] + 30 * math.sin(age / 18 + fl["ph"])
                    paste_center(im, fl["sp"], x, y, angle=15 * math.sin(age / 22 + fl["ph"]), alpha=0.85)

            if "hearts_burst" in s["fx"] and f < 26:
                k = f / 26
                for (ang, sp, hs) in burst:
                    dist = sp * f
                    paste_center(im, hs, W / 2 + math.cos(ang) * dist, cap_y + math.sin(ang) * dist,
                                 scale=1.0 - 0.4 * k, alpha=1 - k)

            if "sparkles" in s["fx"]:
                for (x, y, sc, ph) in sparks:
                    v = math.sin(f / 5 + ph)
                    if v > 0:
                        paste_center(im, sparkle, x, y, scale=sc * v, angle=f * 3)

            # caption pop + bob
            ct = f - 2
            if ct >= 0:
                sc = ease_out_back(ct / 10)
                bob = 7 * math.sin(f / 9)
                paste_center(im, card, W / 2, cap_y + bob, scale=sc, angle=1.5 * math.sin(f / 13))
                cw2, ch2 = card.width, card.height
                for j, (sp, dx, dy, ang) in enumerate(emo):
                    et = ct - 5 - 3 * j
                    if et < 0:
                        continue
                    esc = ease_out_back(et / 9, 2.4)
                    # sit on the card's top-left / top-right corner, kept inside the frame
                    ex = min(max(W / 2 + math.copysign(cw2 / 2 - 40, dx), 100), W - 100)
                    ey = cap_y - ch2 / 2 + 30
                    paste_center(im, sp, ex, ey + 6 * math.sin(f / 7 + j), scale=esc,
                                 angle=ang + 8 * math.sin(f / 8 + j))

            if "cta" in s["fx"] and f > 12:
                b = 26 * abs(math.sin((f - 12) / 6))
                paste_center(im, arrow, 230, 1480 + b, scale=ease_out_back((f - 12) / 8), angle=-28)

            enc.stdin.write(im.convert("RGB").tobytes())
            g += 1
    enc.stdin.close()
    enc.wait()
    return g


# ---------------------------------------------------------------- audio

def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def tone(freq, dur, tau=0.15, harm=(1.0, 0.0, 0.0)):
    t = np.arange(int(dur * SR)) / SR
    w = sum(a * np.sin(2 * np.pi * freq * (k + 1) * t) for k, a in enumerate(harm))
    a = np.minimum(1, t / 0.004)
    return w * env_exp(len(t), tau) * a


def sfx_pop(pitch=1.0):
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    f = 900 * pitch * np.exp(-t * 28) + 260 * pitch
    ph = 2 * np.pi * np.cumsum(f) / SR
    return 0.8 * np.sin(ph) * env_exp(n, 0.025) * np.minimum(1, t / 0.002)


def sfx_whoosh(dur=0.32):
    n = int(dur * SR)
    rng = np.random.default_rng(3)
    x = rng.standard_normal(n)
    # sweeping one-pole low-pass
    t = np.linspace(0, 1, n)
    cut = 0.03 + 0.25 * np.sin(np.pi * t) ** 2
    y = np.zeros(n)
    acc = 0.0
    for i in range(n):
        acc += cut[i] * (x[i] - acc)
        y[i] = acc
    return 0.9 * y / np.abs(y).max() * np.sin(np.pi * t) ** 1.5


def sfx_chime():
    out = np.zeros(int(1.2 * SR))
    for i, fr in enumerate([1568, 2093, 2637, 3136]):
        tn = tone(fr, 1.0, 0.28, (1, 0.25, 0.08)) * 0.32
        o = int(i * 0.06 * SR)
        out[o:o + len(tn)] += tn
    return out


def sfx_boing():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 180 + 260 * (1 + np.sin(2 * np.pi * 9 * t)) * np.exp(-t * 5)
    return 0.55 * np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.16)


def sfx_ding():
    a = tone(1318, 0.9, 0.3, (1, 0.3, 0.1)) * 0.45
    b = tone(1760, 0.9, 0.35, (1, 0.3, 0.1)) * 0.45
    out = np.zeros(int(1.3 * SR))
    out[:len(a)] += a
    o = int(0.14 * SR)
    out[o:o + len(b)] += b
    return out


def render_audio(total_frames):
    total_s = total_frames / FPS
    mix = np.zeros(int((total_s + 2) * SR))  # SFX only; trending sound gets added in-app

    def add(sig, at, gain=1.0):
        o = int(at * SR)
        if o >= len(mix):
            return
        e = min(len(mix), o + len(sig))
        mix[o:e] += sig[:e - o] * gain

    t = 0.0
    for si, s in enumerate(SEGMENTS):
        if si > 0:
            add(sfx_whoosh(), t - 0.12, 0.35)
        add(sfx_pop(1.0), t + 2 / FPS, 0.7)
        for j in range(len(s["emojis"])):
            add(sfx_pop(1.6 + 0.3 * j), t + (7 + 3 * j) / FPS, 0.45)
        if "chime" in s["fx"]:
            add(sfx_chime(), t + 0.15, 0.8)
        if "boing" in s["fx"]:
            add(sfx_boing(), t + 0.5, 0.6)
        if "cta" in s["fx"]:
            add(sfx_ding(), t + 0.45, 0.8)
        t += round(s["dur"] * FPS) / FPS

    mix = mix[:int(total_s * SR)]
    mix = np.tanh(mix * 1.1) * 0.85
    pcm = (mix / max(1e-9, np.abs(mix).max()) * 0.89 * 32767).astype(np.int16)
    path = os.path.join(TMP, "audio.wav")
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    return path


def main():
    segs = cut_segments()
    frames = render_video(segs)
    audio = render_audio(frames)
    final = os.path.join(OUT, "final.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(TMP, "video.mp4"), "-i", audio,
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-ac", "2", "-shortest",
                    "-movflags", "+faststart", final], check=True)
    print("wrote", final, frames / FPS, "s")


if __name__ == "__main__":
    main()
