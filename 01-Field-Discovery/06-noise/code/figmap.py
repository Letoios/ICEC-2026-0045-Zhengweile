# -*- coding: utf-8 -*-
"""课题 06　噪声地图：在校园平面图上标出 5 个测点与三时段结果。

输入：build/campus_map.jpg（学校官方平面图）
输出：deliver/figs/fig7_噪声地图.png
"""
import os
import json
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
MAP = os.path.join(BASE, "build", "campus_map.jpg")
OUT = os.path.join(BASE, "deliver", "figs", "fig7_噪声地图.png")

FONTS = r"C:\Windows\Fonts"


def F(sz, bold=False):
    name = "msyhbd.ttc" if bold else "msyh.ttc"
    return ImageFont.truetype(os.path.join(FONTS, name), sz)


NAVY = "#1F3864"
GREY = "#666666"
RED = "#C00000"

# 点位 → (功能区, 昼间限值, 在平面图上的相对坐标)
SITES = {
    # 2026-11-23 修正：食堂实测点是 F2 百味园（不是 F1 天香园）；
    # 主干道的点原来压在 B1 楼上，改到行知中路路面；实训室走廊改到 B4 天工楼块心。
    "图书馆":     ("1 类", 55, 0.528, 0.529, "A2 图书馆",   0.548, 0.470),
    "食堂":       ("2 类", 60, 0.262, 0.357, "F2 百味园",   0.283, 0.298),
    "主干道":     ("4a 类", 70, 0.4583, 0.4030, "行知中路（B1·B4·F1 之间）", 0.352, 0.300),
    "运动场":     ("2 类", 60, 0.352, 0.500, "体育场",      0.372, 0.548),
    "实训室走廊": ("1 类", 55, 0.492, 0.432, "B4 天工楼 走廊", 0.512, 0.442),
}
ORDER = ["图书馆", "食堂", "主干道", "运动场", "实训室走廊"]


def dcolor(v, lo=-13.0, hi=7.0):
    """Δ 越大越红，越小越蓝。"""
    t = max(0.0, min(1.0, (v - lo) / (hi - lo)))
    if t < 0.5:
        k = t / 0.5
        c1, c2 = (66, 133, 244), (255, 255, 255)
    else:
        k = (t - 0.5) / 0.5
        c1, c2 = (255, 255, 255), (224, 74, 54)
    return tuple(int(a + (b - a) * k) for a, b in zip(c1, c2))


def main():
    st = json.load(open(os.path.join(BASE, "build", "stats.json"), encoding="utf-8"))
    rows = {}
    for r in st:
        rows.setdefault(r["loc"], {})[r["per"]] = r

    src = Image.open(MAP).convert("RGB")
    W0, H0 = src.size
    SCALE = 1.0
    W, H = int(W0 * SCALE), int(H0 * SCALE)
    src = src.resize((W, H), Image.LANCZOS)

    TOP = 96                       # 顶部标题带
    BOT = 300                      # 底部：5 行点位表 + 两行图注
    img = Image.new("RGB", (W, H + TOP + BOT), "white")
    img.paste(src, (0, TOP))
    d = ImageDraw.Draw(img)

    d.rectangle([0, 0, W, TOP], fill=NAVY)
    d.text((44, 20), "课题 06　校园昼夜声学噪声地图（5 点位 × 3 时段）",
           font=F(34, True), fill="white")
    d.text((44, 62), "深圳城市职业学院 / 深圳技师学院　｜　判定口径：GB 3096-2008 昼间限值　｜　圆点颜色 = 三时段中最差的超出量 Δ",
           font=F(17), fill="#C9D3E3")

    # ---- 标记 ----
    for loc in ORDER:
        cls, lim, fx, fy, note, lx, ly = SITES[loc]
        x, y = int(fx * W), int(fy * H) + TOP
        per = rows[loc]
        ds = [per[p]["over"] for p in ("早", "中", "晚")]
        worst = max(ds)
        col = dcolor(worst)

        r = 21
        d.ellipse([x - r - 5, y - r - 5, x + r + 5, y + r + 5], fill="white")
        d.ellipse([x - r, y - r, x + r, y + r], fill=col, outline="#333333", width=2)

        # 小标签：点位名贴在圆点旁，白描边保证任何底色上都能读
        nm = loc
        dxs = {"图书馆": -1, "食堂": -1, "主干道": 1, "运动场": -1, "实训室走廊": 1}[loc]
        tx = x + (r + 8) * dxs
        ty = y - 8
        d.text((tx, ty), nm, font=F(19, True), fill="#1F3864",
               anchor=("lm" if dxs > 0 else "rm"),
               stroke_width=4, stroke_fill="white")

    # ---- 底部：5 行点位表 ----
    yt = H + TOP + 18
    cols = [44, 200, 640, 730, 820, 910, 1050]
    heads = ["点位", "位置", "早 Δ", "中 Δ", "晚 Δ", "判定", "最差"]
    d.text((44, yt - 6), "15 组实测：5 点位 × 早/中/晚", font=F(22, True), fill=NAVY)
    yh = yt + 34
    d.line([cols[0], yh + 30, W - 44, yh + 30], fill=NAVY, width=2)
    for k, hd in enumerate(heads):
        anchor = "lm" if k < 2 else "mm"
        d.text((cols[k], yh + 12), hd, font=F(18, True), fill=NAVY, anchor=anchor)

    ry = yh + 46
    verdict_ok = 0
    for loc in ORDER:
        cls, lim, fx, fy, note = SITES[loc][:5]
        per = rows[loc]
        ds = [per[p]["over"] for p in ("早", "中", "晚")]
        n_over = sum(1 for v in ds if v > 0)
        verdict_ok += (len(ds) - n_over)
        vert = "达标 %d / 超标 %d" % (len(ds) - n_over, n_over)
        col = RED if n_over else "#1F7A3D"
        d.text((cols[0], ry), loc, font=F(19, True), fill="#1F3864", anchor="lm")
        d.text((cols[1], ry), "%s（%s · 限值 %d dB）" % (note, cls, lim),
               font=F(17), fill="#555555", anchor="lm")
        for k, v in enumerate(ds):
            d.text((cols[2 + k], ry), "%+.1f" % v, font=F(19, True),
                   fill=(RED if v > 0 else "#1F7A3D"), anchor="mm")
        d.text((cols[5], ry), vert, font=F(18, True), fill=col, anchor="mm")
        d.text((cols[6], ry), "%+.1f" % max(ds), font=F(19, True),
               fill=dcolor(max(ds)), anchor="mm")
        ry += 40

    # ---- 两行图注 ----
    d.line([44, ry + 6, W - 44, ry + 6], fill="#D6DEEA", width=1)
    d.text((44, ry + 18), "Δ = Leq − 该点位昼间限值（dB）。主干道是 4a 类、限值 70 dB，因此负值最多；"
                          "图书馆与实训室走廊是 1 类、限值 55 dB，最容易超过。",
           font=F(17), fill=GREY)
    d.text((44, ry + 48), "15 组中 12 组超标、3 组达标（达标全部是主干道）。"
                          "同一批声级若改按夜间限值评价，15 组会全部超标——差的那 10 dB 全部来自限值换挡。",
           font=F(17), fill=RED)

    img.save(OUT)
    print("saved", OUT, img.size)


if __name__ == "__main__":
    main()
