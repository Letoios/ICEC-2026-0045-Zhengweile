# -*- coding: utf-8 -*-
"""课题06 回放仿真的四张图

fig8   15 段「声级曲线 + 灯色带」——看灯为什么这么亮
fig9   闪烁 vs 准确率 的帕累托前沿——回答「参数凭什么定在这」
fig10  能量构成——爆发型 vs 持续型
fig11  冲击通道阈值敏感性——回答「85 该不该降」
"""
import json
import math
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE) if os.path.basename(HERE) == "code" else os.path.join(HERE, "deliver")
RES = os.path.join(HERE, "build") if os.path.isdir(os.path.join(HERE, "build")) else os.path.join(PKG, "results")
BUILD = RES
OUT = os.path.join(PKG, "figs")
FONT = r"C:\Windows\Fonts\msyh.ttc"
FONTB = r"C:\Windows\Fonts\msyhbd.ttc"

C = ["#00C2FF", "#22C55E", "#FACC15", "#FB923C", "#EF4444"]
CN = ["S0 安静", "S1 达标", "S2 轻度", "S3 中度", "S4 重度"]
NAVY = "#1F3864"
GREY = "#6B7280"

SITES = ["图书馆", "食堂", "主干道", "运动场", "实训室走廊"]
PERIODS = ["早", "中", "晚"]


def F(sz, bold=False):
    return ImageFont.truetype(FONTB if bold else FONT, sz)


# ---------------------------------------------------------------- fig8
def fig8():
    runs = json.load(open(os.path.join(BUILD, "sim_runs.json"), encoding="utf-8"))
    by = {(r["site"], r["period"]): r for r in runs}

    W = 1620
    cw, ch = 320, 150
    left, top = 176, 158
    gapx, gapy = 40, 96
    H = top + 5 * (ch + gapy) + 118
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    d.text((44, 26), "课题 06　把 15 段实测序列喂进状态机——灯为什么这么亮",
           font=F(26, True), fill=NAVY)
    d.text((44, 72), "上半部灰线 = 每秒的 Δ（1 s Leq − 限值），虚线是 0（限值）；"
                     "下半部色带 = 灯当时的状态。",
           font=F(13), fill=GREY)
    d.text((44, 96), "曲线在虚线上下抖，但色带很少跟着抖——这就是去抖和回差在干活。",
           font=F(13), fill=GREY)

    band = 40
    plot_h = ch - band - 42
    for i, site in enumerate(SITES):
        y = top + i * (ch + gapy)
        d.text((44, y + ch / 2 - 10), site, font=F(16, True), fill="#333")
        for j, per in enumerate(PERIODS):
            x = left + j * (cw + gapx)
            r = by.get((site, per))
            if not r:
                continue
            hot = r["sid"] in ("S06", "S15")
            d.rectangle([x, y, x + cw, y + ch],
                        outline="#C00000" if hot else "#D8DEE9",
                        width=2 if hot else 1)
            n = len(r["states"])
            ds = r["deltas"][:n]
            y0, y1 = y + 28, y + 28 + plot_h
            lo, hi = -16.0, 20.0
            py = lambda v: y1 - (max(lo, min(hi, v)) - lo) / (hi - lo) * (y1 - y0)
            yy0 = py(0)
            for dx0 in range(x + 2, x + cw - 4, 10):
                d.line([dx0, yy0, dx0 + 5, yy0], fill="#E06666", width=1)
            pts = [(x + 2 + k / float(max(1, n - 1)) * (cw - 4), py(v))
                   for k, v in enumerate(ds)]
            if len(pts) > 1:
                d.line(pts, fill="#94A3B8", width=1)
            bw = (cw - 4) / float(n)
            for k, s in enumerate(r["states"]):
                d.rectangle([x + 2 + k * bw, y + ch - band - 4,
                             x + 2 + (k + 1) * bw + 0.6, y + ch - 6], fill=C[s])
            d.text((x + 5, y + 6), "%s · %s" % (r["sid"], per), font=F(12), fill="#555")
            d.text((x + cw - 5, y + 6),
                   "Δ均 %+.1f｜切换 %d" % (r["leq"] - r["limit"], r["switches"]),
                   font=F(12), fill="#555", anchor="ra")


    ly = top + 5 * (ch + gapy) + 10
    lx = left
    for i in range(5):
        d.rectangle([lx, ly, lx + 22, ly + 15], fill=C[i])
        d.text((lx + 28, ly - 2), CN[i], font=F(13), fill="#444")
        lx += 150

    d.text((44, H - 66),
           "红框两格：S06 曲线有两根冲天尖峰，色带却稳稳停在黄色；S15 是唯一会来回变的一段（%d 次）。" % next(x["switches"] for x in runs if x["sid"] == "S15"),
           font=F(13, True), fill="#C00000")
    d.text((44, H - 40),
           "曲线抖得厉害而色带不动，说明阈值恰好卡在抖动带上——差一档的现象就是从这里来的。",
           font=F(13), fill=GREY)

    p = os.path.join(OUT, "fig8_灯色回放时间线.png")
    img.save(p)
    print("saved", p, img.size)


# ---------------------------------------------------------------- fig9
def fig9(sim2):
    g = sim2["grid"]
    W, H = 1140, 760
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((44, 24), "课题 06　参数不能只看「闪几次」——稳定性和准确性是矛盾的",
           font=F(22, True), fill=NAVY)
    d.text((44, 62), "横轴 = 15 段合计切换次数（对数刻度，越左越稳）；"
                     "纵轴 = 逐秒一致率（灯的状态与瞬时档位相同的比例，越高越准）。",
           font=F(13), fill=GREY)

    L, R, T, Bm = 120, W - 60, 130, H - 190
    xs = [max(13.0, x["flicker"]) for x in g]
    ys = [x["agree"] for x in g]
    lx0, lx1 = math.log10(13.0), math.log10(max(xs) * 1.15)
    y0, y1 = math.floor(min(ys)) - 1.0, math.ceil(max(ys)) + 0.6

    def X(v):
        return L + (math.log10(max(13.0, v)) - lx0) / (lx1 - lx0) * (R - L)

    def Y(v):
        return Bm - (v - y0) / (y1 - y0) * (Bm - T)

    gy = math.ceil(y0 / 2.0) * 2
    while gy <= y1:
        d.line([L, Y(gy), R, Y(gy)], fill="#EEF1F5")
        d.text((L - 12, Y(gy)), "%d%%" % gy, font=F(12), fill="#999", anchor="rm")
        gy += 2
    for gx in (15, 20, 30, 50, 80, 120):
        if math.log10(gx) <= lx1:
            d.line([X(gx), T - 6, X(gx), Bm], fill="#F7F9FC")
            d.text((X(gx), Bm + 10), "%d" % gx, font=F(12), fill="#999", anchor="ma")
    d.line([L, Bm, R, Bm], fill="#BBB")
    d.line([L, T - 6, L, Bm], fill="#BBB")
    d.text(((L + R) / 2, Bm + 34), "15 段合计切换次数（对数刻度，越左越稳）",
           font=F(13), fill=GREY, anchor="ma")
    d.text((L - 66, (T + Bm) / 2), "逐秒\n一致率", font=F(13), fill=GREY,
           anchor="mm", align="center")

    def dominated(pt):
        for q in g:
            if q is pt:
                continue
            if q["flicker"] <= pt["flicker"] and q["agree"] >= pt["agree"] and \
                    (q["flicker"] < pt["flicker"] or q["agree"] > pt["agree"]):
                return True
        return False

    for pt in g:
        x, y = X(pt["flicker"]), Y(pt["agree"])
        if dominated(pt):
            d.ellipse([x - 4, y - 4, x + 4, y + 4], fill="#AAB4C4")
        else:
            d.ellipse([x - 7, y - 7, x + 7, y + 7], fill="#C00000")

    front = sorted([x for x in g if not dominated(x)], key=lambda r: r["flicker"])
    d.line([(X(x["flicker"]), Y(x["agree"])) for x in front],
           fill="#C00000", width=2)

    def tag(c, rel, txt, lx, ly):
        pt = next((x for x in g if x["confirm"] == c and x["release"] == rel), None)
        if not pt:
            return
        x, y = X(pt["flicker"]), Y(pt["agree"])
        tx, ty = X(lx), Y(ly)
        d.line([x, y, tx, ty], fill="#7F1D1D", width=1)
        d.text((tx, ty - 10), txt, font=F(12, True), fill="#7F1D1D",
               anchor="ma", stroke_width=4, stroke_fill="white")

    tag(5.0, 3.0, "5 s / 3 dB：%d 次，最迟钝" % next(x["flicker"] for x in g if x["confirm"] == 5.0 and x["release"] == 3.0), 22, y0 + 1.2)
    tag(1.0, 0.0, "1 s / 0 dB：最激进，却最不准", 55, y0 + 1.2)
    tag(3.0, 0.0, "3 s / 0 dB：准确率最高", 34, y1 - 0.6)
    tag(3.0, 1.0, "3 s / 1 dB（本设计）", 17, y0 + 4.2)

    d.text((44, H - 88), "红点是帕累托前沿——同一闪烁水平下准确率最高的点；灰点被某个红点同时压住，"
                         "在任何意义上都不如前者。", font=F(13), fill="#444")
    d.text((44, H - 60), "本设计取 3 s / 1 dB：24 次切换、74.4% 一致率。"
                         "比原设计（单边回差 2 dB）少闪 4 次，还准 3.4 个点。", font=F(13, True), fill="#C00000")
    d.text((44, H - 32), "再往左（更稳）要掉准确率，再往右（更准）就回到抖个不停——这就是曲线拐点。",
           font=F(13), fill="#444")

    img.save(os.path.join(OUT, "fig9_参数扫描矩阵.png"))
    print("saved fig9")


def fig10():
    ev = json.load(open(os.path.join(BUILD, "events.json"), encoding="utf-8"))
    ev.sort(key=lambda r: -r["e_pct"])
    W, H = 1140, 780
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((44, 26), "课题 06　同样是超标，「吵了一下」和「一直吵」完全不是一回事",
           font=F(23, True), fill=NAVY)
    d.text((44, 68), "横条 = 高于本段 L90+10 dB 的样本占总能量的比例。"
                     "占比越高，说明 Leq 是被少数几秒拉上去的。", font=F(13), fill=GREY)
    L, R, T = 250, W - 130, 122
    step = 31
    for i, r in enumerate(ev):
        y = T + i * step
        d.text((L - 12, y + 11), "%s %s %s" % (r["sid"], r["site"], r["per"]),
               font=F(13), fill="#333", anchor="rm")
        w = r["e_pct"] / 100.0 * (R - L)
        col = "#C00000" if r["e_pct"] >= 20 else ("#FB923C" if r["e_pct"] >= 5 else "#9CA3AF")
        d.rectangle([L, y, L + max(2, w), y + 22], fill=col)
        d.text((L + max(2, w) + 8, y + 11), "%.1f%%" % r["e_pct"], font=F(12),
               fill="#444", anchor="lm")
    d.line([L, T - 12, L, T + len(ev) * step], fill="#CBD5E1", width=2)
    d.text((44, H - 104), "S06 图书馆午间：51.4% 的能量来自极少数样本 —— 那是一次爆发，"
                          "其余 100 秒很安静。", font=F(14, True), fill="#C00000")
    d.text((44, H - 76), "S07 食堂午间：0.0%，整段平稳抬高；S05 / S11 分别为 15.1% / 10.9%。",
           font=F(13), fill=GREY)
    d.text((44, H - 48), "所以光效必须双通道：爆发型该闪（冲击提示），持续型该常亮（等级提示）。",
           font=F(13, True), fill=NAVY)
    p = os.path.join(OUT, "fig10_能量构成.png")
    img.save(p)
    print("saved", p, img.size)


# ---------------------------------------------------------------- fig11
def fig11():
    d2 = json.load(open(os.path.join(BUILD, "sim2.json"), encoding="utf-8"))
    sp = d2["sp"]
    W, H = 1060, 620
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((44, 26), "课题 06　冲击通道该不该降到 80 dB？先看数据里到底有没有「冲击」",
           font=F(22, True), fill=NAVY)
    d.text((44, 68), "柱子 = 15 段里「某秒的采样峰值 ≥ 阈值」的秒数；括号内是涉及的段数。"
                     "15 段合计约 1500 秒。", font=F(13), fill=GREY)

    L, R, T, B = 120, W - 120, 150, H - 150
    mx = max(s["seg_frames"] for s in sp) or 1
    n = len(sp)
    step = (R - L) / float(n)
    bw = step * 0.52
    for i, s in enumerate(sp):
        xx = L + i * step + (step - bw) / 2
        h = s["seg_frames"] / float(mx) * (B - T)
        col = "#C00000" if s["thr"] == 85 else "#94A3B8"
        d.rectangle([xx, B - max(h, 3), xx + bw, B], fill=col)
        d.text((xx + bw / 2, B - max(h, 3) - 12), "%d 次" % s["seg_frames"],
               font=F(14, True), fill="#333", anchor="ma")
        d.text((xx + bw / 2, B + 10), "%d dB" % s["thr"], font=F(14, True),
               fill="#333", anchor="ma")
        d.text((xx + bw / 2, B + 32), "(%d/15 段)" % s["seg_hit"], font=F(11),
               fill=GREY, anchor="ma")
    d.line([L, B, R, B], fill="#999", width=2)

    d.text((44, H - 92),
           "85 dB（GBZ 2.2 职业限值）：0 次。这批数据里一秒都没到过。",
           font=F(14, True), fill="#C00000")
    d.text((44, H - 62),
           "哪怕降到 78 dB（比职业限值低 7 dB），1500 秒里也只有 5 秒触发、摊在 4 段上。",
           font=F(13), fill="#444")
    d.text((44, H - 34),
           "结论：不是阈值设错了，是这 15 段场景本来就没有脉冲型噪声。这条要写进局限，而不是调参掩盖。",
           font=F(13, True), fill=NAVY)

    p = os.path.join(OUT, "fig11_冲击阈值敏感性.png")
    img.save(p)
    print("saved", p, img.size)


SIM2 = json.load(open(os.path.join(RES, "sim2.json"), encoding="utf-8"))

if __name__ == "__main__":
    fig8()
    fig9(SIM2)
    fig10()
    fig11()
