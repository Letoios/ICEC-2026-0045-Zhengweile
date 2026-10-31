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
    "图书馆":     ("1 类", 55, 0.528, 0.529, "A2 图书馆"),
    "食堂":       ("2 类", 60, 0.508, 0.317, "F1 天香园"),
    "主干道":     ("4a 类", 70, 0.448, 0.596, "行知中路 × 行知南路"),
    "运动场":     ("2 类", 60, 0.352, 0.500, "体育场"),
    "实训室走廊": ("1 类", 55, 0.452, 0.388, "B4 天工楼"),
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
    BOT = 118                      # 底部图注带
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
        cls, lim, fx, fy, note = SITES[loc]
        x, y = int(fx * W), int(fy * H) + TOP
        per = rows[loc]
        ds = [per[p]["over"] for p in ("早", "中", "晚")]
        worst = max(ds)
        col = dcolor(worst)

        r = 21
        d.ellipse([x - r - 5, y - r - 5, x + r + 5, y + r + 5], fill="white")
        d.ellipse([x - r, y - r, x + r, y + r], fill=col, outline="#333333", width=2)

        # 标签：点位名 + 三时段 Δ
        head = "%s（%s）" % (loc, note)
        tail = "　".join("%+.1f" % v for v in ds)
        tw1 = d.textbbox((0, 0), head, font=F(20, True))
        tw2 = d.textbbox((0, 0), tail, font=F(18))
        bw = max(tw1[2] - tw1[0], tw2[2] - tw2[0]) + 24
        bh = 62
        # 上/左方向避让：靠右的放左边
        bx = x + r + 12 if fx < 0.72 else x - r - 12 - bw
        by = y - bh // 2
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=8,
                            fill="white", outline="#B4C0D3", width=2)
        d.text((bx + 12, by + 6), head, font=F(20, True), fill=NAVY)
        d.text((bx + 12, by + 34), tail, font=F(18), fill="#333333")

        # 简单引线
        if fx < 0.72:
            d.line([x + r + 4, y, bx, y], fill="#B4C0D3", width=2)
        else:
            d.line([x - r - 4, y, bx + bw, y], fill="#B4C0D3", width=2)

    # ---- 底部图注 ----
    yb = H + TOP + 16
    d.text((44, yb), "读法：三时段数值依次为 早 / 中 / 晚 的 Δ（Leq − 该点位昼间限值，dB）。"
                     "主干道是 4a 类、限值 70 dB，因此负值最多；图书馆与实训室走廊是 1 类、限值 55 dB，最容易超过。",
           font=F(17), fill=GREY)
    d.text((44, yb + 30), "15 组中 12 组超标、3 组达标（达标全部是主干道）。"
                          "同一批声级若改按夜间限值评价，15 组会全部超标——差的那 10 dB 全部来自限值换挡。",
           font=F(17), fill=RED)

    img.save(OUT)
    print("saved", OUT, img.size)


if __name__ == "__main__":
    main()
