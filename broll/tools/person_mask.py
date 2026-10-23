"""Topeng orang (alfa) untuk hook "bgswap": host kekal, latar studio diganti B-roll.

Guna: python3 person_mask.py <video> <tempoh_saat> <out.mp4> [model.tflite] [--no-hair]
Hasil: video kelabu 1080x1920 (putih = orang), fps sama dengan sumber.
Model: MediaPipe selfie_multiclass_256x256 (kelas 0 = latar) — muat turun ke work/models/ (lihat README).
Tepi dilembutkan (blur 2px) + purata masa (EMA) supaya tiada kelip.
"""
import subprocess
import sys

import cv2
import mediapipe as mp
import numpy as np

NO_HAIR = "--no-hair" in sys.argv
args = [a for a in sys.argv[1:] if a != "--no-hair"]
video, dur, out = args[0], float(args[1]), args[2]
model = args[3] if len(args) > 3 else __file__.rsplit("/tools/", 1)[0] + "/work/models/selfie_multiclass_256x256.tflite"

opts = mp.tasks.vision.ImageSegmenterOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model),
    running_mode=mp.tasks.vision.RunningMode.VIDEO, output_confidence_masks=True)
seg = mp.tasks.vision.ImageSegmenter.create_from_options(opts)

cap = cv2.VideoCapture(video)
fps = cap.get(cv2.CAP_PROP_FPS)
w, h = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{w}x{h}", "-r", str(fps),
                       "-i", "-", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", out], stdin=subprocess.PIPE)
prev = None
for i in range(round(dur * fps) + 2):
    ok, f = cap.read()
    if not ok:
        break
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
    cm = seg.segment_for_video(img, int(i * 1000 / fps)).confidence_masks
    # orang = bukan latar; kelas rambut (1) dibuang pilihan (--no-hair: host botak, elak tulisan gelap dikira rambut)
    p = 1.0 - cm[0].numpy_view() - (cm[1].numpy_view() if NO_HAIR else 0)
    m = cv2.resize(np.clip(p, 0, 1), (w, h), interpolation=cv2.INTER_LINEAR)
    m = np.clip((m - 0.35) / 0.3, 0, 1)                     # tepi lebih tegas, kemudian lembut
    # kekalkan komponen terbesar sahaja (buang tompok palsu dari tulisan gelap di latar)
    n, lab, stats, _ = cv2.connectedComponentsWithStats((m > 0.5).astype(np.uint8))
    if n > 1:
        keep = (lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
        m *= cv2.dilate(keep, np.ones((9, 9), np.uint8)).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 2)
    prev = m if prev is None else 0.55 * m + 0.45 * prev
    ff.stdin.write((prev * 255).astype(np.uint8).tobytes())
ff.stdin.close(); ff.wait(); seg.close()
print("ok", out, i + 1, "frame")
