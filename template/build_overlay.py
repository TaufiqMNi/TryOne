import sys
from PIL import Image
S, d = sys.argv[1], sys.argv[2]
def L(f):
    im = Image.open(d + f).convert('RGBA'); return im.crop(im.getchannel('A').getbbox())
def byW(im, w): return im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
def byH(im, h): return im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
W, H, CY = 1080, 1920, 246          # CY = garis tengah logo bar
ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
g = Image.new('L', (1, 380))         # gradient gelap halus di atas
for y in range(380): g.putpixel((0, y), int(110 * (1 - y / 380) ** 1.5))
ov.alpha_composite(Image.merge('RGBA', [Image.new('L', (W, 380))] * 3 + [g.resize((W, 380))]))
logos = [('SIYASEE', byW(L('logo_siyasee.png'), 134), 91),
         ('HALUAN', byH(L('logo_haluan.png'), 48), 262),
         ('LANGITILAHI', byW(L('logo_langitilahi.webp'), 174), 340),
         ('podcast bumimerdeka', byH(L('logo_podcast_bumimerdeka.webp'), 50), None)]   # None = rata kanan, margin 100
for n, im, x in logos:
    if x is None: x = W - 100 - im.width
    y = CY - im.height // 2; ov.alpha_composite(im, (x, y)); print(n, 'x', x, 'y', y, 'size', im.size)
b = Image.open(d + 'banner.webp').convert('RGBA'); ov.alpha_composite(b, (0, H - b.height))
print('banner x 0 y', H - b.height, 'size', b.size)
ov.save(S + '/overlay_1080x1920.png')
