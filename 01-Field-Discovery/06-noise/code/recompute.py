# -*- coding: utf-8 -*-
"""课题 06　独立复核脚本（不依赖任何外部数据，只读本包内 data/）

用法（在本文件所在目录执行）：

    python recompute.py            # 打印 15 组指标表
    python recompute.py --csv      # 同时写出 recompute.csv

它做的事：读取 data/S01_早_图书馆/Amplitudes.csv 这一列原始 dB 序列，
按 README 第六节的公式重算 Leq / Lmax / 1s峰 / L10 / L50 / L90 / Δ / 情景Δ / 判定，
然后与 data/Sxx_*/meta.txt 里记录的指标逐行比对，报告最大偏差。

只要这个脚本能在你的机器上跑通、结果与 Excel 的「01 十五组汇总」一致，
就说明交付里的每一个数字都可以从原始序列独立复现。
"""
import os
import sys
import csv
import math

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
DATA = os.path.join(PKG, "data")

# 点位 -> (功能区, 昼间限值, 夜间限值)   GB 3096-2008
STD = {
    "图书馆":     ("1 类", 55, 45),
    "实训室走廊": ("1 类", 55, 45),
    "食堂":       ("2 类", 60, 50),
    "运动场":     ("2 类", 60, 50),
    "主干道":     ("4a 类", 70, 55),
}


def read_series(path):
    """读 Phyphox 导出的 Amplitudes.csv，返回 (时间序列, dB 序列)。"""
    ts, ds = [], []
    with open(path, encoding="utf-8-sig", newline="") as f:
        rd = csv.reader(f)
        next(rd, None)                      # 表头
        for row in rd:
            if len(row) < 2:
                continue
            try:
                t = float(row[0])
                d = float(row[1])
            except ValueError:
                continue                    # -∞ 与空行跳过
            if not math.isfinite(d):
                continue                    # Phyphox 偶尔写出 NaN 行
            ts.append(t)
            ds.append(d)
    return ts, ds


def leq(vals):
    """能量平均声级。"""
    return 10 * math.log10(sum(10 ** (d / 10) for d in vals) / len(vals))


def pct(sorted_vals, p):
    """线性插值分位数。"""
    k = (len(sorted_vals) - 1) * p
    f, c = math.floor(k), math.ceil(k)
    return sorted_vals[f] if f == c else sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


def peak1s(ts, vals):
    """1 s 滑窗能量平均的最大值。"""
    j, best = 0, -999.0
    for i, t in enumerate(ts):
        while ts[j] < t - 1.0:
            j += 1
        best = max(best, leq(vals[j:i + 1]))
    return best


def parse_meta(path):
    """data/Sxx/meta.txt 里的「指标：Leq 60.58  Lmax 79.02  1s峰 70.70  Δ +5.58  超标」一行。"""
    got = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("指标："):
                parts = line.replace("指标：", "").split()
                for i in range(0, len(parts) - 1):
                    if parts[i] in ("Leq", "Lmax", "1s峰", "Δ"):
                        got[parts[i]] = float(parts[i + 1])
    return got


def main():
    write_csv = "--csv" in sys.argv
    rows, worst = [], 0.0

    header = ("编号  时段  点位       类别    时长s   样本     Leq     Lmax     1s峰     "
              "L10     L50     L90      Δ    判定    情景Δ")
    print(header)
    print("-" * len(header))

    for name in sorted(os.listdir(DATA)):
        d = os.path.join(DATA, name)
        if not os.path.isdir(d):
            continue
        _, per, loc = name.split("_", 2)
        cls, ld, ln = STD[loc]

        ts, ds = read_series(os.path.join(d, "Amplitudes.csv"))
        lq = leq(ds)
        lx = max(ds)
        p1 = peak1s(ts, ds)
        srt = sorted(ds)
        l10, l50, l90 = pct(srt, 0.10), pct(srt, 0.50), pct(srt, 0.90)
        delta = lq - ld                      # 昼间口径（判定依据）
        dne = lq - ln                        # 夜间限值情景（仅对照）
        verdict = "超标" if delta > 0 else "达标"

        ref = parse_meta(os.path.join(d, "meta.txt"))
        for k, v in (("Leq", lq), ("Lmax", lx), ("1s峰", p1), ("Δ", delta)):
            if k in ref:
                worst = max(worst, abs(ref[k] - v))

        print("%-5s %-5s %-11s %-7s %-7.1f %-7d %-7.2f %-8.2f %-7.2f %-7.2f %-7.2f %-7.2f %+6.2f  %-6s  %+6.2f"
              % (name.split("_")[0], per, loc, cls, ts[-1] - ts[0], len(ds),
                 lq, lx, p1, l10, l50, l90, delta, verdict, dne))

        rows.append([name.split("_")[0], per, loc, cls, round(ts[-1] - ts[0], 1), len(ds),
                     round(lq, 2), round(lx, 2), round(p1, 2), round(l10, 2), round(l50, 2),
                     round(l90, 2), round(delta, 2), verdict, round(dne, 2)])

    n_over = sum(1 for r in rows if r[13] == "超标")
    print("-" * len(header))
    print("共 %d 组：超标 %d / 达标 %d　｜　与 meta.txt 记录的最大偏差 %.4f dB"
          % (len(rows), n_over, len(rows) - n_over, worst))
    print("（口径：判定一律用昼间限值；情景Δ 为改按夜间限值的对照，不参与判定）")

    if write_csv:
        out = os.path.join(HERE, "recompute.csv")
        with open(out, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(["编号", "时段", "点位", "类别", "时长s", "样本", "Leq", "Lmax", "1s峰",
                        "L10", "L50", "L90", "Δ", "判定", "情景Δ"])
            w.writerows(rows)
        print("已写出：" + out)


if __name__ == "__main__":
    main()
