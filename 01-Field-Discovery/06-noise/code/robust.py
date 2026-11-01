# -*- coding: utf-8 -*-
"""课题06 稳健性分析：bootstrap 置信区间、结论翻转率、共同平移敏感性、时长收敛。

核心区分（本脚本的论点）：
  · 共同分量（校准漂移、计权口径、同一台手机）→ 15 组同向平移，不改变组间比较与排序
  · 独立分量（采样随机性、点位挪动、时段差）→ 逐组独立，才会翻转单组判定
把两者混在一起算「±3 dB」是错的：会让每一组都显得不确定，掩盖真正擦线的那两三组。

只读本包 data/ 与 build/stats.json，不依赖第三方库。
"""
import os
import io
import csv
import json
import math
import random

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE) if os.path.basename(HERE) == "code" else os.path.join(HERE, "deliver")
DATA = os.path.join(PKG, "data")
RES = os.path.join(HERE, "build") if os.path.isdir(os.path.join(HERE, "build")) else os.path.join(PKG, "results")
BUILD = RES                          # 包里没有 build/，统一用 results/

random.seed(20261031)

U_CAL = 3.0      # 校准漂移：偏移 80.49~102.83，跨度 22.35 dB，取保守 3 dB（共同）
U_WGT = 1.0      # 计权口径：A 计权是否真加上（共同）
U_POS = 1.5      # 点位代表性：同区域挪 1~2 m（独立）
K95 = 1.96


def read_db(path):
    vals = []
    with io.open(path, "r", encoding="utf-8-sig", newline="") as f:
        r = csv.reader(f)
        next(r, None)
        for row in r:
            if len(row) < 2:
                continue
            try:
                v = float(row[1])
            except ValueError:
                continue
            if v > 0 and not math.isinf(v):
                vals.append(v)
    return vals


def leq(vals):
    if not vals:
        return float("nan")
    return 10 * math.log10(sum(10 ** (v / 10.0) for v in vals) / len(vals))


def to_frames(vals, fs):
    n = max(1, int(round(fs)))
    return [leq(vals[i:i + n]) for i in range(0, len(vals) - n + 1, n)]


def block_boot(fr, k=400, L=5):
    m = len(fr)
    if m < 10:
        return float("nan"), float("nan")
    nb = int(math.ceil(m / float(L)))
    est = []
    for _ in range(k):
        acc = []
        for _ in range(nb):
            s = random.randrange(0, m - L + 1)
            acc.extend(fr[s:s + L])
        est.append(leq(acc))
    est.sort()
    return est[int(0.025 * k)], est[int(0.975 * k) - 1]


def converge(fr):
    m = len(fr)
    out = {}
    for pct in (30, 45, 60, 75, 90, 100):
        k = max(2, int(round(m * pct / 100.0)))
        out[pct] = round(leq(fr[:k]), 2)
    return out


def main():
    stats = json.load(io.open(os.path.join(BUILD, "stats.json"), encoding="utf-8"))
    idx = {(s["per"], s["loc"]): s for s in stats}

    rows = []
    for name in sorted(os.listdir(DATA)):
        d = os.path.join(DATA, name)
        if not os.path.isdir(d):
            continue
        parts = name.split("_")
        if len(parts) < 3:
            continue
        sid, per, loc = parts[0], parts[1], parts[2]
        csvp = os.path.join(d, "Amplitudes.csv")
        if not os.path.exists(csvp):
            continue
        st = idx.get((per, loc))
        if not st:
            continue

        limit = float(st["limit"])
        dur = float(st["dur"])
        vals = read_db(csvp)
        fs = len(vals) / dur if dur > 0 else 9.2

        fr = to_frames(vals, fs)
        full = leq(vals)
        lo, hi = block_boot(fr)
        ci_s = (hi - lo) / 2.0

        u_ind = math.sqrt((ci_s / K95) ** 2 + U_POS ** 2)
        half_ind = K95 * u_ind
        u_com = math.sqrt(U_CAL ** 2 + U_WGT ** 2)

        dlt = full - limit
        z = abs(dlt) / u_ind if u_ind > 0 else 99
        flip = 0.5 * math.erfc(z / math.sqrt(2))

        rows.append({
            "sid": sid, "per": per, "loc": loc, "limit": limit,
            "dur": round(dur, 1), "fs": round(fs, 2), "n": len(vals),
            "leq": round(full, 2), "delta": round(dlt, 2),
            "ci_sampling": round(ci_s, 2),
            "half_indep": round(half_ind, 2),
            "u_common": round(u_com, 2),
            "flip": round(flip, 4),
            "conv": converge(fr),
        })

    rows.sort(key=lambda r: r["sid"])
    os.makedirs(BUILD, exist_ok=True)
    with io.open(os.path.join(BUILD, "robust.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)

    hdr = "%-4s %-3s %-7s %5s %5s %7s %7s %8s %8s %7s" % (
        "编号", "时段", "点位", "限值", "时长", "Leq", "Δ", "采样CI", "±独立", "翻转率")
    print(hdr)
    print("-" * (len(hdr) + 4))
    for r in rows:
        print("%-4s %-3s %-7s %5.0f %5.1f %7.2f %+7.2f %8.2f %8.2f %6.1f%%" % (
            r["sid"], r["per"], r["loc"], r["limit"], r["dur"],
            r["leq"], r["delta"], r["ci_sampling"], r["half_indep"], r["flip"] * 100))
    n = sum(1 for r in rows if r["flip"] > 0.10)
    print("-" * (len(hdr) + 4))
    print("独立分量下翻转率 > 10%% 的段：%d / %d" % (n, len(rows)))
    for r in rows:
        if r["flip"] > 0.10:
            print("  擦线：%s %s%s  Δ%+.1f  ±%.1f dB  翻转率 %.1f%%" % (
                r["sid"], r["per"], r["loc"], r["delta"], r["half_indep"], r["flip"] * 100))

    print()
    print("共同平移敏感性（全部 15 组同时加减一个偏移后，还剩几组超标）：")
    base = sum(1 for r in rows if r["delta"] > 0)
    print("  偏移  " + "".join("%+6.0f" % d for d in (-4, -3, -2, -1, 0, 1, 2, 3, 4)))
    cnts = []
    for d in (-4, -3, -2, -1, 0, 1, 2, 3, 4):
        cnts.append(sum(1 for r in rows if r["delta"] + d > 0))
    print("  超标数" + "".join("%6d" % c for c in cnts) + "   （无偏移 = %d）" % base)

    print()
    print("时长收敛（取前 x%% 帧算 Leq）：")
    print("%-4s %7s %7s %7s %7s %7s %7s %7s" % (
        "编号", "30%", "45%", "60%", "75%", "90%", "100%", "30%-100%"))
    for r in rows:
        c = r["conv"]
        print("%-4s %7.2f %7.2f %7.2f %7.2f %7.2f %7.2f %+7.2f" % (
            r["sid"], c[30], c[45], c[60], c[75], c[90], c[100], c[30] - c[100]))


if __name__ == "__main__":
    main()
