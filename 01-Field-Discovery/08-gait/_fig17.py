# -*- coding: utf-8 -*-
"""fig17：每步冲量 rms/cad 把「用力上楼」从「快下楼」里摘出去。"""
import csv
from PIL import Image, ImageDraw, ImageFont
F_ = lambda s, b=False: ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc" if b else r"C:\Windows\Fonts\msyh.ttc", s)
rows = list(csv.DictReader(open(r"D:\deepseek工作\gait08\deliver\features_all.csv", encoding="utf-8-sig")))
pts = [(float(r["cad"]), float(r["impulse"]), r["truth"], r["file"].split("/")[-1]) for r in rows]
up = [p for p in pts if p[2] == "上台阶"]
dn = [p for p in pts if p[2] == "下台阶"]

W, H = 1160, 760
img = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(img)
d.text((44, 20), "课题 08　一次被新样本打破的规则：④b 为什么要再加「每步冲量」", font=F_(21, True), fill="#1F3864")
d.text((44, 54), "横轴＝步频 Hz，纵轴＝每步冲量 rms/cad；红线是 ④b 的冲量上界 5.0", font=F_(13), fill="#666")
L, R, T, B = 100, 790, 108, 600
x0, x1 = 1.1, 1.9; y0, y1 = 0.5, 7.2
X = lambda v: L + (v - x0) / (x1 - x0) * (R - L)
Y = lambda v: B - (v - y0) / (y1 - y0) * (B - T)
d.rectangle([L, T, R, B], outline="#E2E8F0")
for v in (1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8):
    d.text((X(v), B + 8), "%.1f" % v, font=F_(11), fill="#94A3B8", anchor="ma")
for v in range(1, 8):
    d.line([L, Y(v), R, Y(v)], fill="#F1F5F9")
    d.text((L - 8, Y(v)), str(v), font=F_(11), fill="#94A3B8", anchor="rm")
d.text(((L + R) / 2, B + 28), "步频 Hz", font=F_(12), fill="#475569", anchor="ma")
d.text((L - 62, (T + B) / 2), "rms/cad", font=F_(12), fill="#475569", anchor="ma")
d.line([L, Y(5.0), R, Y(5.0)], fill="#DC2626", width=2)
d.text((R - 6, Y(5.0) - 10), "冲量上界 5.0", font=F_(12, True), fill="#DC2626", anchor="rs")
for x, y, t, nm in up:
    d.ellipse([X(x) - 6, Y(y) - 6, X(x) + 6, Y(y) + 6], fill="#2563EB")
for x, y, t, nm in dn:
    d.ellipse([X(x) - 6, Y(y) - 6, X(x) + 6, Y(y) + 6], fill="#EA580C")
for nm, tx, ty, col, dx, dy, anc in (
        ("用力上楼 6.17", 1.47, 6.17, "#1E40AF", -14, -6, "rm"),
        ("用力上楼2 6.49", 1.49, 6.49, "#1E40AF", 12, -8, "lm"),
        ("用力下楼 5.86", 1.61, 5.86, "#9A3412", 12, -6, "lm"),
        ("快下楼 4.29", 1.63, 4.29, "#9A3412", 12, 10, "lm")):
    x, y = X(tx), Y(ty)
    d.ellipse([x - 9, y - 9, x + 9, y + 9], outline=col, width=2)
    d.text((x + dx, y + dy), nm, font=F_(12, True), fill=col, anchor=anc,
           stroke_width=4, stroke_fill="white")
d.text((826, 118), "■ 上台阶（%d 段）" % len(up), font=F_(13), fill="#2563EB")
d.text((826, 144), "■ 下台阶（%d 段）" % len(dn), font=F_(13), fill="#EA580C")
lines = [
 ("第一版 ④b：RMS ≥ 6.0 且步频 < 1.9", "#334155"),
 ("→ 快下楼修好了，但「用力上楼」", "#334155"),
 ("   RMS 9.08 也被判成下台阶。", "#B91C1C"),
 ("", "#000000"),
 ("第二版：再加一条 每步冲量 < 5.0", "#334155"),
 ("→ 用力上楼 6.17/6.49 不再触发，", "#166534"),
 ("   快下楼 3.66 / 4.29 仍触发。", "#166534"),
 ("", "#000000"),
 ("共 37 段全部判对（37/37）。", "#7C3AED"),
]
for k, (t, c) in enumerate(lines):
    d.text((826, 190 + k * 26), t, font=F_(13, k in (0, 4, 8)), fill=c)
d.text((44, H - 88), "为什么是「冲量」不是「步频」：快下楼冲击短、步频高，每步冲量反而小；用力上楼每步要抬高一整级，冲量大。", font=F_(13), fill="#334155")
d.text((44, H - 58), "为什么不用「把门槛从 6.0 抬到 9.5」：那样快下楼（6.43 / 6.98）就漏回去了。", font=F_(13), fill="#334155")
d.text((44, H - 28), "坦白：5.0~5.86 之间仍没有样本，上界一侧只有 down_power 5.86 撑着。", font=F_(13, True), fill="#B45309")
img.save(r"D:\deepseek工作\gait08\deliver\figs\fig17_每步冲量.png")
print("saved", len(pts), "点")
