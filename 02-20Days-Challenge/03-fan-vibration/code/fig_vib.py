# -*- coding: utf-8 -*-
"""fig11：振动通道 —— 水平看档位，垂直看故障。"""
import json, math
from PIL import Image, ImageDraw, ImageFont
F = lambda s, b=False: ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc" if b else r"C:\Windows\Fonts\msyh.ttc", s)
D = json.load(open(r"D:\deepseek工作\proj03\results\vibration.json", encoding="utf-8"))
COL = {"C1 一档":"#3B82F6","C2 三档":"#22C55E","C3 五档":"#EAB308","C4 胶带":"#DC2626","C5 半遮挡":"#9333EA"}
W, H = 1200, 760
img = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(img)
d.text((44, 22), "项目三　振动通道：水平看转速，垂直看故障", font=F(22, True), fill="#1F3864")
d.text((44, 58), "横轴＝水平 RMS（x/y 两轴的矢量和，反映径向不平衡力）　纵轴＝垂直 RMS（z 轴，反映轴向窜动）　各轴为对数", font=F(13), fill="#666")
L, R, T, B = 130, 800, 120, 620
def LX(v): return L + (math.log10(v) - math.log10(0.018)) / (math.log10(0.20) - math.log10(0.018)) * (R - L)
def LY(v): return B - (math.log10(v) - math.log10(0.06)) / (math.log10(0.70) - math.log10(0.06)) * (B - T)
d.rectangle([L, T, R, B], outline="#E2E8F0")
for v in (0.02, 0.03, 0.05, 0.08, 0.12, 0.20):
    d.line([LX(v), T, LX(v), B], fill="#F1F5F9")
    d.text((LX(v), B + 8), "%.2f" % v, font=F(11), fill="#94A3B8", anchor="ma")
for v in (0.06, 0.09, 0.15, 0.25, 0.40, 0.60):
    d.line([L, LY(v), R, LY(v)], fill="#F1F5F9")
    d.text((L - 10, LY(v)), "%.2f" % v, font=F(11), fill="#94A3B8", anchor="rm")
d.text(((L + R) / 2, B + 36), "水平 RMS  m/s²（对数）", font=F(12), fill="#475569", anchor="ma")
d.text((10, (T + B) / 2), "垂直 RMS\nm/s²（对数）", font=F(12), fill="#475569", anchor="lm")
# 分区带
d.rectangle([L, T, R, LY(0.20)], fill="#FFF5F5")
d.text((L + 10, T + 8), "故障区（垂直 ≥ 0.20）", font=F(12, True), fill="#B91C1C")
for r in D["rows"]:
    x, y = LX(r["hor"]), LY(r["ver"])
    d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=COL[r["g"]], outline="white", width=1)
lab = [("C1 一档", 0.026, 0.066, "ma"), ("C2 三档", 0.035, 0.078, "ma"),
       ("C3 五档", 0.104, 0.066, "ma"), ("C4 胶带", 0.098, 0.685, "ma"),
       ("C5 半遮挡", 0.030, 0.395, "ma")]
for n, hx, vy, an in lab:
    d.text((LX(hx), LY(vy)), n, font=F(13, True), fill=COL[n], anchor=an)
# 说明栏
x0 = 838
d.text((x0, 128), "两个特征恰好正交", font=F(15, True), fill="#1F3864")
for k, (t, c) in enumerate([
    ("水平 RMS → 转速", "#1F3864"),
    ("低速 0.025/0.035，高速 0.098/0.116，", "#334155"),
    ("差 3 倍，单调、无重叠。", "#334155"),
    ("", "#000"),
    ("垂直 RMS → 故障", "#1F3864"),
    ("正常三档均值 0.088~0.094 挤在一起", "#334155"),
    ("（单段最高 0.116）；胶带 0.56、遮挡 0.32。", "#334155"),
    ("", "#000"),
    ("胶带：谱塌缩成 1×+2×", "#1F3864"),
    ("3 片叶片，基频 31.4、叶片通过 94 Hz；", "#334155"),
    ("正常时 229 Hz 最强，贴胶带后它归零，", "#334155"),
    ("能量全塌到 1×(29) 与 2×(58)。", "#334155"),
    ("", "#000"),
    ("与声学通道的关系", "#1F3864"),
    ("声学五类只有 61%，档位分不开；", "#334155"),
    ("振动这边档位在水平轴上直接拉开。", "#7C3AED"),
]):
    if not t:
        continue
    d.text((x0, 160 + k * 25), t, font=F(13, c == "#1F3864"), fill=c)
d.text((44, H - 66), "一句提醒：一档有两条的手机倾角是 2.9°、其余 13 条都是 1.2~1.4°，所以那两条的垂直 RMS 偏高（0.29 / 0.20），", font=F(13), fill="#334155")
d.text((44, H - 40), "那是姿态差 1.7° 把径向振动耦合进了 z 轴，不是风扇本身。同倾角的那条（1.3°）垂直只有 0.090 —— 与三档、五档一致。", font=F(13), fill="#334155")
img.save(r"D:\deepseek工作\proj03\figs\fig11_振动通道.png")
print("saved fig11")
