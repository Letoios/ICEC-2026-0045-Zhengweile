# -*- coding: utf-8 -*-
"""项目三 · 画一段录音的波形与频谱（诊断用，也是交付图的基础）"""
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import audio as A
import features as F

FONT = lambda s, b=False: ImageFont.truetype(
    r"C:\Windows\Fonts\msyhbd.ttc" if b else r"C:\Windows\Fonts\msyh.ttc", s)

NAVY, GREY, RED, BLUE = "#1F3864", "#888888", "#C00000", "#2563EB"


def draw(path, out, title=None):
    x, sr = A.read_wav(path)
    f = F.extract(path)
    freqs, amp = A.welch(x, sr, n=8192)

    W, H = 1180, 760
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((40, 22), title or ("频谱诊断 · " + os.path.basename(path)), font=FONT(23, True), fill=NAVY)
    d.text((40, 56), "采样率 %d Hz ｜ 时长 %.2f s ｜ 基频 %.1f Hz ｜ 谱心 %.0f Hz ｜ 高频占比 %.0f%%"
           % (sr, len(x) / sr, f["f0"], f["centroid"], f["e_high"] * 100),
           font=FONT(13), fill=GREY)

    # ---- 上：波形（每秒一个刻度，抽稀画）
    L, R = 90, W - 50
    y0, yh = 100, 150
    d.rectangle([L, y0, R, y0 + yh], outline="#E2E8F0")
    step = max(1, len(x) // (R - L))
    seg = x[::step][: R - L]
    mid = y0 + yh / 2
    amp_scale = (yh / 2 - 6) / max(1e-9, np.max(np.abs(seg)))
    pts = [(L + i, mid - v * amp_scale) for i, v in enumerate(seg)]
    d.line(pts, fill=BLUE, width=1)
    d.text((40, y0 + yh / 2 - 8), "波形", font=FONT(13, True), fill=NAVY)
    for t in range(1, int(len(x) / sr) + 1):
        px = L + t * sr / len(x) * (R - L)
        d.line([px, y0 + yh, px, y0 + yh + 5], fill="#CBD5E1")
        d.text((px - 6, y0 + yh + 8), "%ds" % t, font=FONT(11), fill=GREY)

    # ---- 下：频谱（对数纵轴，0–8000 Hz）
    y1, yh2 = 330, 300
    d.rectangle([L, y1, R, y1 + yh2], outline="#E2E8F0")
    sel = (freqs >= 20) & (freqs <= 8000)
    fr, am = freqs[sel], 20 * np.log10(np.maximum(amp[sel], 1e-12))
    top = am.max()
    for dbv in range(-70, 1, 10):
        yy = y1 + yh2 - (dbv + 70) / 70.0 * yh2
        d.line([L, yy, R, yy], fill="#F1F5F9" if dbv % 20 else "#E2E8F0")
        d.text((L - 34, yy - 8), "%d" % (int(top) + dbv - int(top)), font=FONT(10), fill=GREY)
    def XH(v):
        return L + (np.log10(np.maximum(v, 20.0)) - np.log10(20.0)) / (np.log10(8000.0) - np.log10(20.0)) * (R - L)

    px = XH(fr)
    py = y1 + yh2 - (am - top + 70) / 70.0 * yh2
    py = np.clip(py, y1, y1 + yh2)
    d.line(list(zip(px, py)), fill="#444444", width=1)
    d.text((40, y1 + 6), "频谱", font=FONT(13, True), fill=NAVY)

    # 标基频与谐波
    f0 = f["f0"]
    for k in range(1, 9):
        fk = f0 * k
        if fk > 8000:
            break
        X = XH(fk)
        d.line([X, y1, X, y1 + yh2], fill=RED if k == 1 else "#FCA5A5")
        if k <= 4:
            d.text((X - 9, y1 - 40 + (k - 1) * 13), ("f0" if k == 1 else "%df0" % k),
                   font=FONT(11, True), fill=RED)

    # 频段说明
    for lo, hi, lab, col in [(20, 500, "低频 20–500 Hz", "#F59E0B"),
                             (500, 2000, "中频 0.5–2 kHz", "#10B981"),
                             (2000, 8000, "高频 2–8 kHz", "#8B5CF6")]:
        X0 = XH(lo)
        X1 = XH(hi)
        d.line([X0, y1 + yh2 + 6, X1, y1 + yh2 + 6], fill=col, width=3)
        d.text(((X0 + X1) / 2 - 42, y1 + yh2 + 12), lab, font=FONT(11), fill=col)

    for lab, v in [("20", 20), ("50", 50), ("100", 100), ("200", 200), ("500", 500),
                   ("1k", 1000), ("2k", 2000), ("4k", 4000), ("8k", 8000)]:
        d.line([XH(v), y1 + yh2, XH(v), y1 + yh2 + 4], fill="#CBD5E1")
        d.text((XH(v) - 9, y1 + yh2 - 16), lab, font=FONT(10), fill="#999999")

    d.text((40, H - 46), "读法：f0 是转速（%.0f rpm），后面一排等间距的尖峰是它的谐波；谐波越整齐、越突出，转子越平稳"
           % (f0 * 60), font=FONT(13), fill="#B45309")

    img.save(out)
    print("saved", out, img.size)


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else r"D:\deepseek工作\proj03\data\_selftest\测试录音1.wav"
    o = sys.argv[2] if len(sys.argv) > 2 else r"D:\deepseek工作\proj03\figs\fig01_测试录音频谱.png"
    draw(p, o)
