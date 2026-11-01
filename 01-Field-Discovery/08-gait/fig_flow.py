# -*- coding: utf-8 -*-
"""课题 08　判定流程图（与 gait_classify.py 的六个分支一一对应）

用法：python fig_flow.py      → figs/fig3_判定流程.png
依赖：Pillow，字体用 Windows 自带微软雅黑。
"""
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "figs", "fig3_判定流程.png")

W, H = 1020, 1000
NAVY = "#1F3864"
GREY = "#6B7280"
LINE = "#9AA7B8"
FILL = "#F4F7FB"
EDGE = "#C9D4E3"

# (条件文本, 命中label, label颜色)
STEPS = [
    ("① 竖直 RMS < 1.5  且  自相关 < 0.35", "静止", "#8C8C8C"),
    ("② RMS × 自相关 < 1.0（没有步态信息）", "无法判定", "#7A6FB0"),
    ("③ 步频 > 2.0 且 RMS > 6.0，或 RMS > 10", "跑步", "#C00000"),
    ("④ 正−负 > +0.035  且  偏度 > +0.25", "下台阶", "#ED7D31"),
    ("⑤ 自相关 > 0.70", "平地走", "#22A75A"),
]


def font(size, bold=False):
    p = r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"
    return ImageFont.truetype(p, size)


def arrow(d, p0, p1, color=LINE, w=2):
    d.line([p0, p1], fill=color, width=w)
    x0, y0 = p0
    x1, y1 = p1
    if abs(x1 - x0) > abs(y1 - y0):          # 水平箭头
        s = 1 if x1 > x0 else -1
        d.polygon([(x1, y1), (x1 - 10 * s, y1 - 6), (x1 - 10 * s, y1 + 6)], fill=color)
    else:                                     # 垂直箭头
        s = 1 if y1 > y0 else -1
        d.polygon([(x1, y1), (x1 - 6, y1 - 10 * s), (x1 + 6, y1 - 10 * s)], fill=color)


def main():
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    f_title = font(23, True)
    f_box = font(16)
    f_lab = font(17, True)
    f_small = font(13)

    d.text((46, 30), "课题 08　六步判定流程（自上而下，先答「是」者直接出结果）", font=f_title, fill=NAVY)

    bx, bw, bh = 100, 470, 78
    ys = [96, 228, 360, 492, 624]
    lx, lw, lh = 630, 250, 56

    for i, (cond, label, color) in enumerate(STEPS):
        y = ys[i]
        d.rounded_rectangle([bx, y, bx + bw, y + bh], radius=12, fill=FILL, outline=EDGE, width=2)
        d.text((bx + bw / 2, y + bh / 2), cond, font=f_box, fill=NAVY, anchor="mm")
        # 是 → label
        my = y + bh / 2
        arrow(d, (bx + bw, my), (lx - 4, my), color=color, w=2)
        d.text(((bx + bw + lx) / 2, my - 16), "是", font=f_small, fill=color, anchor="mm")
        d.rounded_rectangle([lx, my - lh / 2, lx + lw, my + lh / 2], radius=10, fill=color)
        d.text((lx + lw / 2, my), label, font=f_lab, fill="white", anchor="mm")
        # 否 ↓
        if i < len(STEPS) - 1:
            arrow(d, (bx + bw / 2, y + bh), (bx + bw / 2, ys[i + 1]))
            d.text((bx + bw / 2 + 14, (y + bh + ys[i + 1]) / 2), "否", font=f_small,
                   fill=GREY, anchor="lm")

    # 兜底
    ty = ys[-1] + bh + 44
    arrow(d, (bx + bw / 2, ys[-1] + bh), (bx + bw / 2, ty))
    d.text((bx + bw / 2 + 14, (ys[-1] + bh + ty) / 2), "否", font=f_small, fill=GREY, anchor="lm")
    d.rounded_rectangle([bx, ty, bx + bw, ty + bh], radius=12, fill="#2E75B6")
    d.text((bx + bw / 2, ty + bh / 2), "⑥ 上台阶（兜底）", font=f_lab, fill="white", anchor="mm")

    note = ("注：① 是绝对量级 + 周期性守卫（防止轻手轻脚上楼被当成静止），② 是信息量门槛（信号里没有步态就拒答），\n"
            "③④ 是波形形状量；阈值在 8 段实测数据上标定，各条边界余量见《阈值规则.md》第五节。")
    d.text((46, ty + bh + 46), note, font=f_small, fill=GREY)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    im.save(OUT)
    print("saved", OUT, im.size)


if __name__ == "__main__":
    main()
