#!/usr/bin/env python3
"""Photo -> transparent PNG cut-out for the collage style (uses rembg, runs offline after first model download).

  python3 tools/cutout.py photo.jpg assets/person.png            # colour, tight crop
  python3 tools/cutout.py photo.jpg assets/person.png --bw       # B&W high-contrast (v1/v3 look)
  python3 tools/cutout.py photo.jpg out.png --model u2net_human_seg --pad 12

Then in a composition: <img src="../assets/person.png"> + c.cutout(el, { style: 'news' | 'outline' | 'sticker' | 'offset' }).
Install once:  pip install "rembg[cpu]" onnxruntime
"""
import argparse, sys
from PIL import Image, ImageOps, ImageEnhance, ImageFilter

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('dst')
ap.add_argument('--model', default='isnet-general-use', help='rembg model: isnet-general-use | u2net | u2net_human_seg | birefnet-portrait')
ap.add_argument('--bw', action='store_true', help='greyscale + contrast 1.35 (editorial B&W)')
ap.add_argument('--pad', type=int, default=8, help='transparent padding around the tight crop (px)')
ap.add_argument('--max', type=int, default=1600, help='longest side of the output (px)')
ap.add_argument('--feather', type=float, default=0.6, help='alpha edge softening radius (px); 0 = hard cut like scissors')
a = ap.parse_args()

try:
    from rembg import remove, new_session
except ImportError:
    sys.exit('rembg missing: pip install "rembg[cpu]" onnxruntime')

img = Image.open(a.src).convert('RGB')
out = remove(img, session=new_session(a.model)).convert('RGBA')
alpha = out.getchannel('A')
alpha = alpha.point(lambda v: 255 if v > 128 else (0 if v < 40 else v))          # crisp scissor edge
if a.feather: alpha = alpha.filter(ImageFilter.GaussianBlur(a.feather))
rgb = out.convert('RGB')
if a.bw:
    rgb = ImageEnhance.Contrast(ImageOps.grayscale(rgb)).enhance(1.35).convert('RGB')
out = Image.merge('RGBA', (*rgb.split(), alpha))
box = alpha.getbbox()
if box:
    l, t, r, b = box
    out = out.crop((max(0, l - a.pad), max(0, t - a.pad), min(out.width, r + a.pad), min(out.height, b + a.pad)))
out.thumbnail((a.max, a.max), Image.LANCZOS)
out.save(a.dst)
print(f'{a.dst}: {out.width}x{out.height}')
