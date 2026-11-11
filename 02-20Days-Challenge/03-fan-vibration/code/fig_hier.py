# -*- coding: utf-8 -*-
"""fig12：把 61.2% 拆成 90.8 / 100 / 43.1。"""
from PIL import Image, ImageDraw, ImageFont
F = lambda s, b=False: ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc" if b else r"C:\Windows\Fonts\msyh.ttc", s)
W, H = 1160, 700
img = Image.new("RGB", (W, H), "white"); d = ImageDraw.Draw(img)
d.text((44, 22), "项目三　五分类只有 61.2%，但那是三件事的平均分", font=F(22, True), fill="#1F3864")
d.text((44, 58), "同一套特征、同一套分组交叉验证（每次留出一整个录制批次）；把一个数拆成三个各自能解释的数", font=F(13), fill="#666")

rows = [("① 有没有故障", "正常 vs 失衡/遮挡", 90.8, 89, 98, "#22A75A", "关键任务"),
        ("② 是哪一种故障", "胶带 vs 遮挡", 100.0, 33, 33, "#22A75A", "关键任务"),
        ("③ 正常里是哪一档", "一档 / 三档 / 五档", 43.1, 28, 65, "#EA580C", "附加功能")]
L, R, y0, bh, gap = 300, 900, 132, 74, 40
for i, (t1, t2, v, ok, tot, col, tag) in enumerate(rows):
    y = y0 + i * (bh + gap)
    d.text((44, y + 12), t1, font=F(16, True), fill="#1F3864")
    d.text((44, y + 40), t2, font=F(12), fill="#64748B")
    d.rectangle([L, y + 8, L + 300, y + 8 + bh - 16], fill="#F1F5F9")
    w = int(300 * v / 100.0)
    d.rectangle([L, y + 8, L + w, y + 8 + bh - 16], fill=col)
    d.text((L + w + 12, y + 8 + (bh - 16) / 2), "%.1f%%  (%d/%d)" % (v, ok, tot), font=F(15, True), fill=col, anchor="lm")
    d.text((L - 10, y + 8 + (bh - 16) / 2), tag, font=F(12), fill="#94A3B8", anchor="rm")

y = y0 + 3 * (bh + gap) + 6
d.line([44, y, R, y], fill="#E2E8F0")
d.text((44, y + 16), "对照：直接五分类", font=F(16, True), fill="#1F3864")
d.rectangle([L, y + 14, L + 184, y + 14 + bh - 30], fill="#94A3B8")
d.text((L + 196, y + 14 + (bh - 30) / 2), "61.2%   (60/98)", font=F(15, True), fill="#475569", anchor="lm")

bx = 940
d.text((bx, 128), "怎么读", font=F(15, True), fill="#1F3864")
for k, (t, c) in enumerate([
    ("①② 合起来 90.8% × 100%", "#334155"),
    ("＝ 认出故障，就一定能说出", "#334155"),
    ("是哪一种。这两件是诊断仪", "#334155"),
    ("的本职。", "#334155"),
    ("", "#000"),
    ("③ 只有 43.1%，随机是 33%。", "#EA580C"),
    ("三档转速只差 20%，比录音", "#EA580C"),
    ("位置造成的差别还小 ——", "#EA580C"),
    ("这是物理上限，不是调参", "#EA580C"),
    ("不够。", "#EA580C"),
    ("", "#000"),
    ("所以 61.2% 低，不是系统", "#334155"),
    ("差，是把它附加功能也算了", "#334155"),
    ("进去。", "#334155"),
]):
    if t: d.text((bx, 160 + k * 24), t, font=F(13, c == "#1F3864"), fill=c)
d.text((44, H - 44), "一句提醒：61.2% 这个数我改不动 —— 加特征贪心跳出 72.4%，嵌套验证后回到 61.2%（见《创新点》创新七）。", font=F(13, True), fill="#B45309")
img.save(r"D:\deepseek工作\proj03\figs\fig12_分层判定.png")
print("saved fig12")
