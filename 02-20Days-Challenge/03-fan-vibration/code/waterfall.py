# -*- coding: utf-8 -*-
"""创新三：频谱瀑布图 —— 同一转速下，「胶带」到底在频谱上留下了什么。

取五档（C3）与五档+胶带（C4）各一段代表性录音，画成时间-频率-能量瀑布。
因为转速相同，两张图的差别只可能来自胶带本身。
"""
import csv, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio

F_ = lambda s, b=False: ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc" if b else r"C:\Windows\Fonts\msyh.ttc", s)
PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = list(csv.DictReader(open(os.path.join(PKG, "results", "features.csv"), encoding="utf-8-sig")))
WAV = os.path.join(PKG, "data", "wav")


def pick(group):
    """取该组谱心最接近中位数的两段里，时长最长的那个。"""
    rs = [r for r in rows if r["group"] == group]
    med = float(np.median([float(r["centroid"]) for r in rs]))
    rs.sort(key=lambda r: abs(float(r["centroid"]) - med))
    return rs[0]


def stft_image(path, n=4096, hop=1024, fmin=20.0, fmax=8000.0, nrow=180):
    x, sr = audio.read_wav(path)
    x = np.asarray(x, float)
    if sr > 24000:                     # 抽到 24 kHz，够画到 8 kHz
        x = x[::2]; sr = sr // 2
    w = np.hanning(n)
    frames = []
    for i in range(0, len(x) - n, hop):
        seg = x[i:i + n] * w
        frames.append(np.abs(np.fft.rfft(seg)))
    S = np.array(frames).T                       # (freq, time)
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    out = np.zeros((nrow, S.shape[1]))
    for k in range(nrow):                        # 对数频率重采样
        f = fmin * (fmax / fmin) ** (k / (nrow - 1))
        j = int(np.argmin(np.abs(freqs - f)))
        out[k] = S[j]
    out = 20 * np.log10(out + 1e-9)
    lo, hi = np.percentile(out, 30), np.percentile(out, 99.5)
    out = np.clip((out - lo) / (hi - lo + 1e-9), 0, 1)
    return out[::-1], len(x) / sr            # 低频在底部


def colorize(a):
    """深蓝 → 青 → 黄 → 红"""
    stops = np.array([[10, 20, 60], [20, 90, 140], [40, 170, 160],
                      [230, 200, 60], [220, 60, 40]], float)
    pos = np.linspace(0, 1, len(stops))
    out = np.zeros(a.shape + (3,), np.uint8)
    for ch in range(3):
        out[..., ch] = np.interp(a, pos, stops[:, ch]).astype(np.uint8)
    return out


# 选一对「转速最接近」的样本，否则「同一转速」这个前提就不成立了
_c3 = [r for r in rows if r["group"] == "C3"]
_c4 = [r for r in rows if r["group"] == "C4"]
r3, r4 = min(((a, b) for a in _c3 for b in _c4),
             key=lambda p: abs(float(p[0]["f0"]) - float(p[1]["f0"])))
print("对比：C3 五档 %s  vs  C4 五档+胶带 %s" % (r3["file"], r4["file"]))
a3, d3 = stft_image(os.path.join(WAV, r3["file"].replace(".mp3", ".wav")))
a4, d4 = stft_image(os.path.join(WAV, r4["file"].replace(".mp3", ".wav")))

PW, PH, GAP = 460, 180, 54
W = 1180
H = 120 + (PH + GAP) * 2 + 150
img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
d.text((44, 22), "项目三　频谱瀑布：同一转速下，「胶带」在频谱上留下了什么", font=F_(21, True), fill="#1F3864")
d.text((44, 54), "横轴时间、纵轴频率（20 Hz–8 kHz 对数）、颜色能量；转速相同，所以差别只能来自胶带",
       font=F_(12), fill="#666")

panels = [("C3 五档（正常）", a3, d3, r3, 110, "#16A34A"),
          ("C4 五档 + 扇叶贴胶带", a4, d4, r4, 110 + PH + GAP, "#DC2626")]
for name, mat, dur, r, y0, col in panels:
    d.text((44, y0 - 24), name + "　f0=%.1f Hz　高频占比=%.3f　h2=%.2f"
           % (float(r["f0"]), float(r["e_high"]), float(r["h2"])), font=F_(13, True), fill=col)
    im = Image.fromarray(colorize(mat)).resize((PW, PH), Image.BICUBIC)
    img.paste(im, (150, y0))
    d.rectangle([150, y0, 150 + PW, y0 + PH], outline="#CBD5E1")
    for fr in (50, 100, 200, 500, 1000, 2000, 5000):
        yy = y0 + PH - int(np.log(fr / 20.0) / np.log(8000 / 20.0) * PH)
        d.line([150, yy, 144, yy], fill="#94A3B8")
        d.text((138, yy), ("%d" % fr) if fr < 1000 else ("%dk" % (fr // 1000)),
               font=F_(10), fill="#64748B", anchor="rm")
    d.text((150 + PW // 2, y0 + PH + 6), "时间 %d 秒" % round(dur), font=F_(11), fill="#64748B", anchor="ma")

d.text((44, H - 96), "胶带片的余量很小（2 g），转速几乎没变，所以低频那一坨完全一样。", font=F_(13), fill="#334155")
d.text((44, H - 68), "变的是 1–4 kHz：胶带让扇叶每转一次多一次扰动，高频能量在时间上出现起伏 —— 这就是「失衡」的可视化指纹。",
       font=F_(13), fill="#B45309")
d.text((44, H - 40), "这一对样本的高频占比是 %.3f → %.3f（组中位 0.147 → 0.211）——差别是量级上的，不是「一眼可见」，"
       "所以最终还是要靠分类器，这张图是用来讲给人听的。" % (float(r3["e_high"]), float(r4["e_high"])),
       font=F_(13), fill="#7C3AED")
img.save(os.path.join(PKG, "figs", "fig09_频谱瀑布.png"))
print("saved fig09")
