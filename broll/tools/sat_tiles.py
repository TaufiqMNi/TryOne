"""Muat turun imej satelit untuk peta "satellite" (templates/map.html) ikut keyframe kamera.

Guna: python3 sat_tiles.py <data.json>   (data cue peta; tulis medan "satellite" ke dalam JSON yang sama)
Sumber: EOxCloudless 2016 (s2cloudless_3857) — https://cloudless.eox.at, EOX IT Services GmbH, mengandungi data
Copernicus Sentinel 2016 yang diubah suai, lesen CC BY 4.0 (komersial dibenarkan dengan kredit). Tahun lain = CC BY-NC-SA: jangan guna.
Setiap keyframe -> satu mozek pada zum yang padan resolusi skrin (maks 14 ≈ 10 m/piksel), disimpan di sebelah JSON.
"""
import io
import json
import math
import os
import sys
import urllib.request

from PIL import Image

URL = "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg"
H, W, SH, CY = 1500, 1080, 1920, 820          # sama dengan map.html: tinggi span, lebar & tinggi skrin, pusat menegak


def mer_y(lat):
    return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))


def inv_y(m):
    return math.degrees(2 * math.atan(math.exp(m)) - math.pi / 2)


def tile_xy(lon, lat, z):
    n = 2 ** z
    return (lon + 180) / 360 * n, (1 - mer_y(lat) / math.pi) / 2 * n


def fetch(z, x, y):
    req = urllib.request.Request(URL.format(z=z, x=x, y=y), headers={"User-Agent": "TryOne-broll/1.0"})
    return Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")


data_file = sys.argv[1]
D = json.load(open(data_file))
out_dir = os.path.dirname(os.path.abspath(data_file))
name = os.path.basename(data_file)[:-5]
layers = []
for k, cam in enumerate(D["camera"]):
    (lon, lat), span = cam["c"], cam["span"]
    s = H / abs(mer_y(lat + span / 2) - mer_y(lat - span / 2))          # piksel per unit mercator (radian)
    m0 = mer_y(lat)
    top, bot = inv_y(m0 + CY / s), inv_y(m0 - (SH - CY) / s)
    half_lon = math.degrees(W / 2 / s) * 1.1
    lon0, lon1 = lon - half_lon, lon + half_lon
    z = max(3, min(14, round(math.log2(s * 2 * math.pi / 256))))
    x0, y0 = tile_xy(lon0, top, z); x1, y1 = tile_xy(lon1, bot, z)
    xs, ys = range(int(x0), int(x1) + 1), range(int(y0), int(y1) + 1)
    mos = Image.new("RGB", (256 * len(xs), 256 * len(ys)))
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            mos.paste(fetch(z, x, y), (256 * i, 256 * j))
    n = 2 ** z
    bbox = [xs[0] / n * 360 - 180, inv_y(math.pi * (1 - 2 * (ys[-1] + 1) / n)),
            (xs[-1] + 1) / n * 360 - 180, inv_y(math.pi * (1 - 2 * ys[0] / n))]   # [lon0, lat0, lon1, lat1]
    fn = f"{name}_sat{k}.jpg"
    mos.save(os.path.join(out_dir, fn), quality=90)
    layers.append({"img": fn, "bbox": [round(v, 6) for v in bbox]})
    print("ok", fn, "z", z, mos.size)
D["satellite"] = layers
D.setdefault("source", "Imej satelit: EOxCloudless 2016 (EOX, CC BY 4.0), data Copernicus Sentinel")
json.dump(D, open(data_file, "w"), ensure_ascii=False)
