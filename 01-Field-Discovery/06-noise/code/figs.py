# -*- coding: utf-8 -*-
"""课题06 全部插图（Pillow 手绘，不依赖 matplotlib）。

输入 noise06\build\stats.json + meta.json
输出 noise06\deliver\figs\*.png
"""
import os, json, math, glob, zipfile, csv

from PIL import Image, ImageDraw, ImageFont

BUILD = r"D:\deepseek工作\noise06\build"
OUT = r"D:\deepseek工作\noise06\deliver\figs"
os.makedirs(OUT, exist_ok=True)

NAVY = "#1F3864"
GREY = "#666666"
LGREY = "#AAAAAA"
GRID = "#DDE3EC"
RED = "#C00000"
ORANGE = "#ED7D31"
GREEN = "#22A75A"
YELLOW = "#D6A800"
BLUE = "#2E75B6"

ORDER = ["图书馆", "食堂", "主干道", "运动场", "实训室走廊"]
PERIODS = ["早", "中", "晚"]
FONT_CAND = [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\msyhbd.ttc"]


def F(size, bold=False):
    path = FONT_CAND[1] if bold else FONT_CAND[0]
    return ImageFont.truetype(path, size)


def ctext(d, cx, y, s, font, fill, anchor="mm"):
    d.text((cx, y), s, font=font, fill=fill, anchor=anchor)


STATS = json.load(open(os.path.join(BUILD, "stats.json"), encoding="utf-8"))
META = {m["folder"]: m for m in json.load(open(os.path.join(BUILD, "meta.json"), encoding="utf-8"))}
IDX = {(r["per"], r["loc"]): r for r in STATS}


def dcolor(v, lo=-13.0, hi=7.0):
    """Δ 值 -> 颜色（蓝-白-红）"""
    t = max(0.0, min(1.0, (v - 0.0) / hi)) if v > 0 else -max(0.0, min(1.0, v / lo)) if v < 0 else 0.0
    if v >= 0:
        r, g, b = 255, int(255 - 150 * t), int(255 - 210 * t)
    else:
        t2 = -t
        r, g, b = int(255 - 180 * t2), int(255 - 90 * t2), 255
    return (r, g, b)


# ============================================================ 图 1 雷达图
def fig1():
    W, H = 1080, 940
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((60, 34), "课题 06　三分时段「超出量 Δ」雷达图", font=F(26, True), fill=NAVY)
    d.text((60, 74), "Δ = Leq − 该点位·该时段的适用限值（dB）；0 线是限值线，越往外越超标",
           font=F(14), fill=GREY)

    cx, cy, R = 540, 500, 300
    n = 5
    ang = [-math.pi / 2 + 2 * math.pi * i / n for i in range(n)]
    LO, HI = -13.0, 8.0

    def pt(i, v):
        rr = (v - LO) / (HI - LO) * R
        return (cx + rr * math.cos(ang[i]), cy + rr * math.sin(ang[i]))

    # 网格环
    for v in range(-10, 9, 5):
        pts = [pt(i, v) for i in range(n)]
        col = "#9AA7B8" if v != 0 else "#1F3864"
        d.polygon(pts, outline=col)
        if v != 0:
            ly = cy - (v - LO) / (HI - LO) * R
            s = "%+d" % v
            bb = d.textbbox((0, 0), s, font=F(12))
            w_, h_ = bb[2] - bb[0], bb[3] - bb[1]
            d.rectangle([cx + 8, ly - 9, cx + 16 + w_, ly + 9], fill="white")
            d.text((cx + 12, ly), s, font=F(12), fill=LGREY, anchor="lm")
    for i in range(n):
        d.line([ (cx, cy), pt(i, HI) ], fill=GRID, width=2)

    series = [("早（昼间限值）", "早", BLUE), ("中（昼间限值）", "中", RED), ("晚 19:00（昼间限值）", "晚", GREEN)]
    for name, per, col in series:
        pts = [pt(i, IDX[(per, loc)]["over"]) for i, loc in enumerate(ORDER)]
        d.polygon(pts, outline=col)
        d.line(pts + [pts[0]], fill=col, width=3, joint="curve")
        for p in pts:
            d.ellipse([p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5], fill=col, outline="white", width=2)

    # 轴标签
    for i, loc in enumerate(ORDER):
        x = cx + (R + 52) * math.cos(ang[i])
        y = cy + (R + 52) * math.sin(ang[i])
        c = IDX[("早", loc)]
        anchor = "mm"
        if abs(math.cos(ang[i])) > 0.8:
            anchor = "lm" if math.cos(ang[i]) > 0 else "rm"
        d.text((x, y - 10), loc, font=F(17, True), fill=NAVY, anchor=anchor)
        d.text((x, y + 12), "%s 限值 %d/%d" % (c["cat"], c["dayLimit"], c["nightLimit"]),
               font=F(12), fill=GREY, anchor=anchor)

    # 图例
    lx, ly = 60, 800
    for i, (name, _, col) in enumerate(series):
        yy = ly + i * 30
        d.line([(lx, yy), (lx + 34, yy)], fill=col, width=4)
        d.text((lx + 44, yy), name, font=F(15), fill="#333", anchor="lm")

    d.text((W - 40, 800), "读法", font=F(15, True), fill=NAVY, anchor="rt")
    tips = ["同一方向：径向距离 = 超出量",
            "越靠外越吵，0 环即限值",
            "三个时段都按昼间限值：傍晚并不比白天吵"]
    for i, t in enumerate(tips):
        d.text((W - 40, 826 + i * 24), t, font=F(13), fill=GREY, anchor="rt")

    img.save(os.path.join(OUT, "fig1_三分时段雷达图.png"))
    print("fig1 ok")


# ============================================================ 图 2 热力图
def fig2():
    W, H = 1040, 800
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((50, 30), "课题 06　点位 × 时段 超出量热力图（Δ dB）", font=F(24, True), fill=NAVY)
    d.text((50, 68), "格子颜色 = 超出量；格内上排 Δ、下排实测 Leq 与限值", font=F(13), fill=GREY)

    x0, y0, cw, chh = 210, 130, 240, 96
    for i, per in enumerate(PERIODS):
        ctext(d, x0 + i * cw + cw / 2, y0 - 26, "%s（%s）" % (per, "19:00" if per == "晚" else "昼间"),
              F(16, True), NAVY)
    for j, loc in enumerate(ORDER):
        d.text((x0 - 18, y0 + j * chh + chh / 2), loc, font=F(16, True), fill=NAVY, anchor="rm")

    for j, loc in enumerate(ORDER):
        for i, per in enumerate(PERIODS):
            r = IDX[(per, loc)]
            v = r["over"]
            box = [x0 + i * cw + 3, y0 + j * chh + 3, x0 + i * cw + cw - 3, y0 + j * chh + chh - 3]
            d.rectangle(box, fill=dcolor(v), outline="white", width=3)
            txt = ("%+.1f" % v)
            ctext(d, (box[0] + box[2]) / 2, box[1] + 30, txt, F(24, True),
                  "#7F1D1D" if v > 6 else ("#1F3864" if v < -3 else "#333333"))
            ctext(d, (box[0] + box[2]) / 2, box[3] - 26,
                  "Leq %.1f / 限 %d" % (r["leq"], r["limit"]), F(12), "#444444")

    leg_y = y0 + len(ORDER) * chh + 40
    d.text((x0 - 18, leg_y), "色标", font=F(13, True), fill=NAVY, anchor="rm")
    for k in range(21):
        v = -13 + k
        d.rectangle([x0 + k * 18, leg_y - 10, x0 + k * 18 + 18, leg_y + 10], fill=dcolor(v))
    d.text((x0, leg_y + 22), "−13 dB（远低于限值）", font=F(11), fill=GREY)
    d.text((x0 + 21 * 18, leg_y + 22), "+7 dB（超出限值）", font=F(11), fill=GREY, anchor="ra")

    d.text((50, H - 54), "结论：15 格里只有主干道三格是冷的（4a 类限值 70 最宽）；其余 12 格都在限值线之上，"
                         "但多数只超 2~6 dB——不是「很吵」，是「刚好越线」。",
           font=F(13), fill="#333")
    img.save(os.path.join(OUT, "fig2_点位时段热力图.png"))
    print("fig2 ok")


# ============================================================ 图 3 昼夜阶跃
def fig3():
    W, H = 1080, 700
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((50, 30), "课题 06　同一批声级，两把尺子——22:00 限值降 10 dB，声级只动了不到 2 dB",
           font=F(21, True), fill=NAVY)
    d.text((50, 68), "左：傍晚与白天的声级几乎相同　｜　右：标准在 22:00 把限值又压了一档",
           font=F(13), fill=GREY)

    # 左图：分组柱
    L, R, T, B = 90, 520, 130, 560
    vmin, vmax = 40, 75
    n = len(ORDER)
    gw = (R - L) / n
    for gv in range(40, 76, 5):
        y = B - (gv - vmin) / (vmax - vmin) * (B - T)
        d.line([(L, y), (R, y)], fill=GRID)
        d.text((L - 10, y), str(gv), font=F(11), fill=LGREY, anchor="rm")
    d.text((L - 46, (T + B) / 2), "dB(A)", font=F(12), fill=GREY, anchor="mm")

    for j, loc in enumerate(ORDER):
        e, nn = IDX[("早", loc)], IDX[("晚", loc)]
        x = L + j * gw + gw / 2
        for k, (r, col) in enumerate([(e, BLUE), (nn, GREEN)]):
            bx = x - 26 + k * 28
            y2 = B - (r["leq"] - vmin) / (vmax - vmin) * (B - T)
            d.rectangle([bx, y2, bx + 24, B], fill=col)
            d.text((bx + 12, y2 - 10), "%.1f" % r["leq"], font=F(10), fill=col, anchor="mb")
        d.text((x, B + 18), loc, font=F(12, True), fill=NAVY, anchor="ma")

    # 右图：限值对比
    L2, R2 = 600, 1040
    d.text((L2, 110), "同一批点位的适用限值", font=F(15, True), fill=NAVY)
    for j, loc in enumerate(ORDER):
        e, nn = IDX[("早", loc)], IDX[("晚", loc)]
        y = 150 + j * 78
        # 昼间限值条
        x1 = L2 + (e["dayLimit"] - vmin) / (vmax - vmin) * (R2 - L2)
        x2 = L2 + (nn["nightLimit"] - vmin) / (vmax - vmin) * (R2 - L2)
        d.text((L2 - 8, y), loc, font=F(12, True), fill=NAVY, anchor="rm")
        d.rectangle([x1, y - 6, R2 - 6, y + 8], fill="#F6E7D2")
        d.rectangle([x2, y - 6, x1, y + 8], fill="#FBDCE0")
        d.text((x2 - 8, y + 1), "夜间限值 %d" % nn["nightLimit"], font=F(11), fill=RED, anchor="rm")
        d.text((x1 + 8, y + 1), "昼间限值 %d" % e["dayLimit"], font=F(11), fill="#8A5A00", anchor="lm")
        d.text((R2 - 6, y + 26), "Δ 从 %+.1f 变 %+.1f（声级只变 %+.1f）"
               % (e["over"], nn["over"], nn["leq"] - e["leq"]), font=F(11), fill=GREY, anchor="rt")

    d.text((50, H - 40), "这就是「制度性阶跃」：22:00 一到，同样的声级会因为限值换档而由绿变红——而那时校园已经基本没人。"
                         "光效逻辑必须为此单独处理（见《创新体系》第 3 节）。", font=F(13), fill=RED)
    img.save(os.path.join(OUT, "fig3_昼夜限值阶跃.png"))
    print("fig3 ok")


# ============================================================ 图 4 不确定度
def fig4():
    W, H = 1140, 820
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((44, 24), "课题 06　把「点判定」改成「区间判定」（±3 dB 未量化偏差）",
           font=F(22, True), fill=NAVY)
    d.text((44, 62), "每行一个测点：黑点是 Leq，横线是 ±3 dB 区间，竖线是限值线 Δ=0；"
                     "区间整体在右=确定超标，压线=不确定，整体在左=确定达标", font=F(12), fill=GREY)

    rows = sorted(STATS, key=lambda r: r["over"])
    L, R = 440, 1050
    T, base = 160, 660
    lo, hi = -18, 18
    for gv in range(lo, hi + 1, 3):
        x = L + (gv - lo) / (hi - lo) * (R - L)
        d.line([(x, T - 8), (x, base + 4)], fill=GRID)
        d.text((x, base + 10), "%+d" % gv, font=F(11), fill=LGREY, anchor="ma")

    step = (base - T) / len(rows)
    for k, r in enumerate(rows):
        y = T + k * step + step / 2
        d.text((L - 16, y), "%s %s" % (r["per"], r["loc"]), font=F(13), fill="#333", anchor="rm")
        x0 = max(L, L + (r["over"] - 3 - lo) / (hi - lo) * (R - L))
        x1 = min(R, L + (r["over"] + 3 - lo) / (hi - lo) * (R - L))
        xc = L + (r["over"] - lo) / (hi - lo) * (R - L)
        if r["over"] - 3 > 3:
            col, tag = RED, "确定超标"
        elif r["over"] - 3 > 0:
            col, tag = ORANGE, "确定超标"
        elif r["over"] + 3 < 0:
            col, tag = GREEN, "确定达标"
        else:
            col, tag = YELLOW, "不确定"
        d.line([(x0, y), (x1, y)], fill=col, width=8)
        d.ellipse([xc - 6, y - 6, xc + 6, y + 6], fill="#222", outline="white", width=2)
        if x1 > R - 150:
            d.text((x0 - 12, y), tag, font=F(12, True), fill=col, anchor="rm")
        else:
            d.text((x1 + 12, y), tag, font=F(12, True), fill=col, anchor="lm")

    xz = L + (0 - lo) / (hi - lo) * (R - L)
    d.line([(xz, T - 16), (xz, base + 4)], fill=NAVY, width=2)
    d.text((xz + 6, T - 22), "限值线 Δ = 0", font=F(12, True), fill=NAVY)

    d.text((L, base + 34), "超出量 Δ (dB)", font=F(12), fill=GREY)

    n_red = sum(1 for r in rows if r["over"] - 3 > 0)
    n_grn = sum(1 for r in rows if r["over"] + 3 < 0)
    n_gry = len(rows) - n_red - n_grn
    d.text((44, H - 72), "15 组里：确定超标 %d 组、确定达标 %d 组、不确定 %d 组。"
                         % (n_red, n_grn, n_gry), font=F(14, True), fill=NAVY)
    grey = [r for r in rows if not (r["over"] - 3 > 0) and not (r["over"] + 3 < 0)]
    d.text((44, H - 44), "不确定的正是贴着限值线的那几组：%s。"
                         "其余 %d 组的结论离限值超过 3 dB，即使仪器有偏差也不会翻转。"
           % ("、".join("%s%s（%+.1f）" % (r["per"], r["loc"], r["over"]) for r in grey),
              n_red + n_grn),
           font=F(12), fill="#333")
    img.save(os.path.join(OUT, "fig4_不确定度区间判定.png"))
    print("fig4 ok")

# ============================================================ 图 5 状态机
def fig5():
    W, H = 1320, 640
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((40, 26), "课题 06　声学超标自动提醒——光效状态机", font=F(24, True), fill=NAVY)
    d.text((40, 64), "六态 / 上升即时 / 下降带回差与保持 / 冲击另走一条通道", font=F(13), fill=GREY)

    states = [("S0\n安静", "#00C2FF", "Δ ≤ −10"),
              ("S1\n达标", "#22C55E", "−10 < Δ ≤ 0"),
              ("S2\n轻度", "#FACC15", "0 < Δ ≤ +5"),
              ("S3\n中度", "#FB923C", "+5 < Δ ≤ +10"),
              ("S4\n重度", "#EF4444", "Δ > +10")]
    bw, gap, y = 200, 40, 170
    x = 60
    centers = []
    for name, col, cond in states:
        d.rounded_rectangle([x, y, x + bw, y + 110], radius=14, fill=col, outline="white", width=3)
        tc = "white" if col in ("#EF4444", "#00C2FF", "#22C55E", "#FB923C") else "#3A2E00"
        ctext(d, x + bw / 2, y + 40, name.split("\n")[0], F(20, True), tc)
        ctext(d, x + bw / 2, y + 74, name.split("\n")[1], F(18, True), tc)
        d.text((x + bw / 2, y + 132), cond, font=F(12), fill="#444444", anchor="ma")
        centers.append(x + bw / 2)
        x += bw + gap

    for i in range(len(states) - 1):
        a = centers[i] + bw / 2 + 2
        b = centers[i + 1] - bw / 2 - 2
        d.line([(a, y + 40), (b, y + 40)], fill=RED, width=3)
        d.polygon([(b, y + 40), (b - 10, y + 34), (b - 10, y + 46)], fill=RED)
        d.line([(b, y + 72), (a, y + 72)], fill=BLUE, width=3)
        d.polygon([(a, y + 72), (a + 10, y + 66), (a + 10, y + 78)], fill=BLUE)

    d.text((60, 344), "上升沿：连续 3 s 满足即切换（安全优先，宁可早报不可晚报）", font=F(13), fill=RED)
    d.text((60, 372), "下降沿：低于下一档阈值 2 dB 且保持 5 s 才降级（回差 + 保持）", font=F(13), fill=BLUE)

    # 冲击通道
    d.rounded_rectangle([60, 400, 460, 510], radius=14, fill="#B91C1C", outline="white", width=3)
    ctext(d, 260, 436, "SP　瞬时冲击", F(20, True), "white")
    ctext(d, 260, 474, "红白快闪 5 Hz · 持续 3 s", F(15), "white")
    d.text((60, 524), "触发：Lmax ≥ 85 dB(A)，不参与平滑、不排队去抖", font=F(12), fill=RED)

    d.rounded_rectangle([520, 400, 1280, 510], radius=12, fill="#F4F7FB", outline="#C9D3E3", width=2)
    d.text((544, 420), "优先级仲裁：SP > S4 > S3 > S2 > S1 > S0", font=F(15, True), fill=NAVY)
    d.text((544, 452), "高优先级可立即抢占；低优先级不得覆盖高优先级，", font=F(12), fill=GREY)
    d.text((544, 474), "必须等高优先级满足退出条件后才能接管。", font=F(12), fill=GREY)

    d.text((520, 524), "夜间 22:00—6:00：亮度 ×0.4、闪烁频率上限 1 Hz（避免光污染）",
           font=F(12), fill="#8A5A00")

    img.save(os.path.join(OUT, "fig5_光效状态机.png"))
    print("fig5 ok")


# ============================================================ 图 6 时序示例
def fig6():
    """取中午食堂一段原始 20 Hz 序列，画 1 s RMS 包络 + 限值线 + 瞬时峰值。"""
    zp = glob.glob(os.path.join(r"D:\分贝项目", "中午食堂", "*.zip"))[0]
    ts, vals = [], []
    with zipfile.ZipFile(zp) as z:
        for line in z.read("Amplitudes.csv").decode("utf-8-sig").splitlines()[1:]:
            p = line.split(",")
            if len(p) != 2:
                continue
            try:
                t, v = float(p[0]), float(p[1])
            except Exception:
                continue
            if v > -50:
                ts.append(t)
                vals.append(v)

    # 0.5 s 能量均
    step = 0.5
    env_t, env_v = [], []
    i = 0
    T = ts[-1] - ts[0]
    while i * step < T:
        lo, hi = i * step, (i + 1) * step
        seg = [v for t, v in zip(ts, vals) if lo <= t - ts[0] < hi]
        if seg:
            env_t.append(lo + step / 2)
            env_v.append(10 * math.log10(sum(10 ** (v / 10) for v in seg) / len(seg)))
        i += 1

    W, H = 1120, 520
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)
    d.text((44, 24), "课题 06　一段原始记录的时间结构（中午　食堂　2026-10-29 12:03）",
           font=F(20, True), fill=NAVY)
    d.text((44, 60), "点线 = 0.5 s 能量均；虚线 = 2 类昼间限值 60 dB；灰带 = 瞬时峰值的上下包络",
           font=F(12), fill=GREY)

    L, R, T, B = 90, 1060, 110, 430
    vmin, vmax = 40, 95
    for gv in range(40, 96, 5):
        y = B - (gv - vmin) / (vmax - vmin) * (B - T)
        d.line([(L, y), (R, y)], fill=GRID)
        d.text((L - 10, y), str(gv), font=F(11), fill=LGREY, anchor="rm")
    d.text((L - 46, (T + B) / 2), "dB(A)", font=F(12), fill=GREY, anchor="mm")

    def X(t):
        return L + t / T * (R - L)

    def Y(v):
        return B - (v - vmin) / (vmax - vmin) * (B - T)

    # 峰值包络
    for k in range(len(env_t)):
        lo = (k) * step
        hi = (k + 1) * step
        seg = [v for t, v in zip(ts, vals) if lo <= t - ts[0] < hi]
        if not seg:
            continue
        x = X(env_t[k])
        d.line([(x, Y(min(seg))), (x, Y(max(seg)))], fill="#DDDDDD", width=3)

    pts = [(X(t), Y(v)) for t, v in zip(env_t, env_v)]
    d.line(pts, fill=BLUE, width=2)
    yl = Y(60)
    for xx in range(L, R, 16):
        d.line([(xx, yl), (xx + 8, yl)], fill=RED, width=2)
    d.text((R - 8, yl - 10), "2 类昼间限值 60 dB", font=F(12, True), fill=RED, anchor="rs")
    d.text((L + 8, yl + 14), "限值线", font=F(11), fill=RED, anchor="ls")

    # Leq 水平线
    r = IDX[("中", "食堂")]
    yle = Y(r["leq"])
    d.line([(L, yle), (R, yle)], fill="#7F7F7F", width=1)
    _s = "整段 Leq = %.1f dB" % r["leq"]
    _bb = d.textbbox((0, 0), _s, font=F(12, True))
    d.rectangle([L + 6, yle - 10 - (_bb[3] - _bb[1]) - 3, L + 12 + _bb[2] - _bb[0], yle - 4], fill="white")
    d.text((L + 8, yle - 8), _s, font=F(12, True), fill="#5A5A5A", anchor="ls")

    d.text((L, B + 22), "0 s", font=F(11), fill=GREY)
    d.text((R, B + 22), "%.0f s" % T, font=F(11), fill=GREY, anchor="ra")

    d.text((44, H - 44),
           "读法：多数时间在限值上方徘徊（背景本身就是 60 dB 左右），偶尔冲到 70 dB 以上。"
           "只用 Leq 会把这 70 dB 的冲击抹平，所以要另开 Lmax 通道。", font=F(12), fill="#333")
    img.save(os.path.join(OUT, "fig6_原始记录时间结构.png"))
    print("fig6 ok")


fig1(); fig2(); fig3(); fig4(); fig5(); fig6()
print("all figs ->", OUT)
