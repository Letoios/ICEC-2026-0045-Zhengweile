# -*- coding: utf-8 -*-
"""fig12：把「准确率怎么提上来的」画成一条路径。

横轴 = 15 段合计切换次数（越小越稳），纵轴 = 逐秒一致率（3 s 基准，越高越准）。
四个点在图上，三条箭头说明每一步改了什么、换来了什么。
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE) if os.path.basename(HERE) == "code" else os.path.join(HERE, "deliver")
RES = os.path.join(HERE, "build") if os.path.isdir(os.path.join(HERE, "build")) else os.path.join(PKG, "results")
OUT = os.path.join(PKG, "figs")
FONT = r"C:\Windows\Fonts\msyh.ttc"
FONTB = r"C:\Windows\Fonts\msyhbd.ttc"

NAVY, GREY, RED, BLUE, GREEN = "#1F3864", "#888888", "#C00000", "#2E75B6", "#2E9E4F"


def F(n, bold=False):
    return ImageFont.truetype(FONTB if bold else FONT, n)


def main():
    s3 = json.load(open(os.path.join(RES, "sim3.json"), encoding="utf-8"))
    s4 = json.load(open(os.path.join(RES, "sim4.json"), encoding="utf-8"))

    def pick(rows, variant, confirm):
        for r in rows:
            if r["variant"].startswith(variant) and r["confirm"] == confirm:
                return r
        raise KeyError(variant)

    A = pick(s3, "A", 3.0)
    B = pick(s3, "B", 3.0)
    D = pick(s3, "D", 3.0)
    hold2 = [r for r in s4 if r["hold"] == 2.0 and r["dwell"] == 0.0][0]

    pts = [
        ("B2", B["flicker"], B["agree3"], "② 对称回差", BLUE, "lb"),
        ("A", A["flicker"], A["agree3"], "① 原设计", GREY, "rt"),
        ("C", hold2["flicker"], hold2["agree3"], "③ 保持 5→2 s", GREEN, "lb"),
        ("D", D["flicker"], D["agree3"], "④ 3 s 输入 + 回差 1 dB", RED, "lt"),
    ]

    W, H = 1080, 700
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((52, 26), "课题 06　准确率是怎么一步步提上来的", font=F(23, True), fill=NAVY)
    d.text((52, 64), "横轴 = 15 段合计切换次数（越小越稳）；纵轴 = 逐秒一致率（3 s 基准，越高越准）。"
                     "四个点都在帕累托前沿上，往上往左都更好。", font=F(13), fill=GREY)

    L, R, T, Bm = 130, W - 70, 140, H - 150
    x0, x1 = 14.0, 40.0
    y0, y1 = 71.0, 81.0

    def X(v):
        return L + (v - x0) / (x1 - x0) * (R - L)

    def Y(v):
        return Bm - (v - y0) / (y1 - y0) * (Bm - T)

    for gy in range(72, 82, 2):
        d.line([L, Y(gy), R, Y(gy)], fill="#EEF1F5")
        d.text((L - 12, Y(gy)), "%d%%" % gy, font=F(12), fill="#999", anchor="rm")
    for gx in range(16, 41, 4):
        d.text((X(gx), Bm + 10), "%d" % gx, font=F(12), fill="#999", anchor="ma")
    d.line([L, Bm, R, Bm], fill="#BBB", width=1)
    d.line([L, T - 10, L, Bm], fill="#BBB", width=1)
    d.text(((L + R) / 2, Bm + 42), "15 段合计切换次数（越左越稳）", font=F(13), fill=GREY, anchor="ma")
    d.text((L - 72, (T + Bm) / 2), "逐秒\n一致率", font=F(13), fill=GREY, anchor="mm", align="center")

    # 箭头：A → B → C → D
    seq = [A, B, hold2, D]
    for i in range(len(seq) - 1):
        p, q = seq[i], seq[i + 1]
        d.line([X(p["flicker"]), Y(p["agree3"]), X(q["flicker"]), Y(q["agree3"])],
               fill="#C9D3E3", width=2)


    for _, fx, ay, txt, col, anchor in pts:
        cx, cy = X(fx), Y(ay)
        d.ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=col, outline="white", width=2)
        if anchor == "rt":
            d.text((cx - 14, cy + 4), txt, font=F(14, True), fill=col, anchor="rm")
        else:
            d.text((cx, cy - 16), txt, font=F(14, True), fill=col, anchor=anchor)

    d.text((52, H - 88), "① → ② 只是把单边回差改成以边界为中心的对称回差：准确率不变，闪烁少了 32%。",
           font=F(14), fill="#444")
    d.text((52, H - 62), "② → ③ 保持时长从 5 s 收到 2 s：闪烁不变，一致率 +1.2 个点。",
           font=F(14), fill="#444")
    d.text((52, H - 36), "③ → ④ 再把输入换成 3 s 能量均、回差收到 1 dB：换来 79.0%，代价是闪烁回到 35 次。这就是天花板。",
           font=F(14, True), fill=RED)

    p = os.path.join(OUT, "fig12_准确率提升路径.png")
    img.save(p)
    print("saved", p, img.size)


if __name__ == "__main__":
    main()
