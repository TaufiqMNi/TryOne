"""Topeng orang (alfa) untuk hook "bgswap": host kekal, latar studio diganti B-roll.

Guna: python3 person_mask.py <video> <tempoh_saat> <out.mp4> [model.tflite] [--no-hair] [--birefnet]
Hasil: video kelabu 1080x1920 (putih = orang), fps sama dengan sumber.
Model: MediaPipe selfie_multiclass_256x256 (kelas 0 = latar) — muat turun ke work/models/ (lihat README).
Tepi diperhalus guided filter (opencv-contrib) pada resolusi penuh + purata masa (EMA) supaya tiada kelip.
"""
import subprocess
import sys

import cv2
import mediapipe as mp
import numpy as np

NO_HAIR = "--no-hair" in sys.argv
BIREFNET = "--birefnet" in sys.argv     # BiRefNet-portrait (ONNX, ~20s/frame CPU): tepi kepala/bahu tepat, tiada tompok
args = [a for a in sys.argv[1:] if a not in ("--no-hair", "--birefnet")]
video, dur, out = args[0], float(args[1]), args[2]
model = args[3] if len(args) > 3 else __file__.rsplit("/tools/", 1)[0] + "/work/models/selfie_multiclass_256x256.tflite"

if BIREFNET:
    import onnxruntime as ort
    so = ort.SessionOptions(); so.enable_cpu_mem_arena = False; so.enable_mem_pattern = False   # elak memori membengkak
    bnet = ort.InferenceSession(__file__.rsplit("/tools/", 1)[0] + "/work/models/birefnet-portrait.onnx", so,
                                providers=["CPUExecutionProvider"])

    def birefnet(bgr):
        x = cv2.resize(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), (1024, 1024), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255
        x = ((x - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225]).transpose(2, 0, 1)[None].astype(np.float32)
        y = bnet.run(None, {bnet.get_inputs()[0].name: x})[0][0, 0]
        return cv2.resize(1 / (1 + np.exp(-y)), (bgr.shape[1], bgr.shape[0]), interpolation=cv2.INTER_LINEAR)

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
    if BIREFNET:
        m = cv2.GaussianBlur(birefnet(f).astype(np.float32), (0, 0), 0.8)
        prev = m if prev is None else 0.85 * m + 0.15 * prev
        ff.stdin.write((prev * 255).astype(np.uint8).tobytes())
        print(i, flush=True)
        continue
    img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
    cm = seg.segment_for_video(img, int(i * 1000 / fps)).confidence_masks
    # orang = bukan latar (rambut termasuk; --no-hair buang kelas rambut — boleh potong kepala botak, elak)
    p = 1.0 - cm[0].numpy_view() - (cm[1].numpy_view() if NO_HAIR else 0)
    m = cv2.resize(np.clip(p, 0, 1), (w, h), interpolation=cv2.INTER_CUBIC).clip(0, 1)
    # komponen terbesar sahaja: hakis dulu supaya tompok palsu (tulisan gelap di latar) terputus dari kepala
    core = cv2.erode((m > 0.5).astype(np.uint8), np.ones((31, 31), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(core)
    if n > 1:
        keep = (lab == 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
        m *= cv2.dilate(keep, np.ones((61, 61), np.uint8)).astype(np.float32)
    # guided filter resolusi penuh: tepi topeng ikut tepi sebenar dalam imej (kepala, bahu), bukan grid 256px
    g = cv2.ximgproc.guidedFilter(f, m.astype(np.float32), 10, 1e-4)
    m = np.clip((g - 0.3) / 0.4, 0, 1)
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    prev = m if prev is None else 0.7 * m + 0.3 * prev
    ff.stdin.write((prev * 255).astype(np.uint8).tobytes())
ff.stdin.close(); ff.wait(); seg.close()
print("ok", out, i + 1, "frame")
