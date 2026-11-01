# -*- coding: utf-8 -*-
"""课题06 稳健性两张图：结果 13（Δ 误差棒）、结果 14（时长收敛）。"""
import os
import io
import json
import math
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE) if os.path.basename(HERE) == "code" else os.path.join(HERE, "deliver")
RES = os.path.join(HERE, "build") if os.path.isdir(os.path.join(HERE, "build")) else os.path.join(PKG, "results")
OUT = os.path.join(PKG, "figs")
ROWS = json.load(io.open(os.path.join(RES, "robust.json"), encoding="utf-8"))

CN = "C:\\Windows\\Fonts\\msyh.ttc"
CNB = "C:\\Windows\\Fonts\\msyhbd.ttc"
NAVY, RED, ORANGE, GREY, LGREY = "#1F3864", "#C00000", "#E36C0A", "#7F7F7F", "#BFBFBF"


def F(sz, bold=False):
    return ImageFont.truetype(CNB if bold else CN, sz)


def fig13():
    W, H = 1180, 960
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((44, 26), "课题 06　每一条判定的误差棒：真正擦线的只有两组", font=F(23, True), fill=NAVY)
    d.text((44, 62), "黑点 = Δ（整段 Leq − 限值）；横条 = 独立分量 95% 区间（采样重采样 + 点位挪动 1~2 m）；"
                    "红色 = 翻转率 > 10%", font=F(13), fill="#666")

    L, R, T = 250, W - 190, 130
    step = 40
    lo = -16.0
    hi = max(10.0, max(r["delta"] + r["half_indep"] for r in ROWS) + 1.0)   # 留出余量，别把误差棒切掉
    px = lambda v: L + (v - lo) / (hi - lo) * (R - L)

    for v in range(-16, int(hi) + 1, 4):
        d.line([px(v), T - 8, px(v), T + step * len(ROWS) + 6], fill="#EEF1F5")
        d.text((px(v), T + step * len(ROWS) + 22), "%+d" % v, font=F(12), fill=GREY, anchor="ma")
    d.line([px(0), T - 14, px(0), T + step * len(ROWS) + 6], fill=NAVY, width=2)
    d.text((px(0), T - 26), "限值线 Δ = 0", font=F(13, True), fill=NAVY, anchor="ma")

    for i, r in enumerate(ROWS):
        y = T + i * step + step / 2
        hot = r["flip"] > 0.10
        col = RED if hot else ORANGE
        d.text((L - 16, y), "%s %s%s" % (r["sid"], r["per"], r["loc"]), font=F(13),
               fill=NAVY if hot else "#444", anchor="rm")
        a, b = px(r["delta"] - r["half_indep"]), px(r["delta"] + r["half_indep"])
        d.line([a, y, b, y], fill=col, width=6)
        for xx in (a, b):
            d.line([xx, y - 7, xx, y + 7], fill=col, width=2)
        d.ellipse([px(r["delta"]) - 5, y - 5, px(r["delta"]) + 5, y + 5], fill="#222222")
        d.text((R + 12, y), "%+.1f  翻转 %.1f%%" % (r["delta"], r["flip"] * 100),
               font=F(12, hot), fill=col if hot else "#666", anchor="lm")

    hot = [r for r in ROWS if r["flip"] > 0.10]
    hot.sort(key=lambda r: -r["flip"])
    yf = T + step * len(ROWS) + 62
    d.text((44, yf), "读法：横条跨过 0 线 = 凭这段数据说不清达标还是超标。翻转率 > 10%% 的只有 %d 组："
           % len(hot), font=F(13), fill="#666")
    segr = "%s %s%s　Δ %+.1f，翻转 %.1f%%"
    d.text((60, yf + 26), "　　".join("· " + segr % (r["sid"], r["per"], r["loc"],
                                                    r["delta"], r["flip"] * 100) for r in hot),
           font=F(13), fill=RED)
    d.text((44, yf + 54), "其余 %d 组的 |Δ| 都在 2.5 dB 以上，翻转率全部低于 10%%，抽样再随机也翻不了。"
           % (len(ROWS) - len(hot)), font=F(13), fill="#666")
    d.text((44, yf + 84), "注意：这里只算「逐组独立」的分量。校准漂移与计权口径是全组同向的，"
                          "它们不翻转单组结论，只整体抬高或压低全部 15 组（见另图）。",
           font=F(13, True), fill=RED)
    img.save(os.path.join(OUT, "fig13_判定误差棒.png"))
    print("saved fig13", img.size)


def fig14():
    W, H = 1120, 760
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((44, 26), "课题 06　要站多久才算数：30 秒够不够，看你在哪个点位", font=F(23, True), fill=NAVY)
    d.text((44, 62), "横轴 = 只用前 x% 的记录；纵轴 = 重算 Leq 相对全段的变化（dB）。"
                    "曲线在 0 附近收拢 = 那一段已经稳定。", font=F(13), fill="#666")

    L, R, T, B = 110, W - 250, 140, H - 130
    pcts = [30, 45, 60, 75, 90, 100]
    lo, hi = -5.0, 3.0
    px = lambda p: L + (p - 30) / 70.0 * (R - L)
    py = lambda v: B - (v - lo) / (hi - lo) * (B - T)

    for v in range(-5, 4, 1):
        d.line([L, py(v), R, py(v)], fill="#EEF1F5")
        d.text((L - 12, py(v)), "%+d" % v, font=F(12), fill=GREY, anchor="rm")
    d.line([L, py(0), R, py(0)], fill=NAVY, width=2)
    for p in pcts:
        d.text((px(p), B + 18), "%d%%" % p, font=F(12), fill=GREY, anchor="ma")

    for r in ROWS:
        c = r["conv"]
        pts = [(px(p), py(c[str(p)] - c["100"])) for p in pcts]
        flat = math.hypot(pts[-1][0] - pts[0][0], pts[-1][1] - pts[0][1])
        far = abs(c["30"] - c["100"])
        if far > 1.2:
            d.line(pts, fill=RED, width=3)
            d.text((pts[0][0] + 10, pts[0][1] - 10), "%s %s%s  %+.1f dB" % (
                r["sid"], r["per"], r["loc"], c["30"] - c["100"]),
                font=F(12, True), fill=RED, anchor="lm",
                stroke_width=4, stroke_fill="white")
        else:
            d.line(pts, fill="#CBD5E1", width=1)

    d.text((44, H - 96), "红线是「30 秒还不够」的那几段：S06 图书馆午间 +4.5 dB、S13 主干道晚 +2.7 dB、"
                         "S04 早运动场 −2.7 dB、S10 实训室午间 −1.5 dB。", font=F(13), fill=RED)
    d.text((44, H - 68), "S06 最典型：前 30 秒只有 56.7 dB，整段 61.2 dB —— 那 4.5 dB 全在最后 10 秒的一次爆发里。"
                         "灰线 11 段在 30% 处已进 ±1 dB。", font=F(13), fill="#666")
    d.text((44, H - 38), "落地结论：常规点位 60 秒足够；食堂、走廊这类「间歇爆发」场景至少 120 秒，"
                         "否则会把爆发漏在采样窗口外。", font=F(13, True), fill=NAVY)
    img.save(os.path.join(OUT, "fig14_时长收敛.png"))
    print("saved fig14", img.size)


if __name__ == "__main__":
    fig13()
    fig14()
