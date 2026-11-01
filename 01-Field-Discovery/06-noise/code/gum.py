# -*- coding: utf-8 -*-
"""不确定度预算（GUM）。

目的：把「绝对声级不可信」从一句定性的话，变成一张能算的账。

关键物理事实：
- 校准偏移是**每段一个**（每次开录重新自动校准），所以它不是公共零点，
  不能用「整体平移」把它抹掉；它直接落在每一段的 Δ 上。
- 反过来说，**一段之内**这个偏移是常数，段内的相对起伏不受它影响。

所以本脚本给两个数字：
  ① 绝对判定（Δ = Leq − 限值）的不确定度 → 含校准项，很大
  ② 段内相对量（同一段里两个时刻的比较）的不确定度 → 不含校准项，很小
"""
import io
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE) if os.path.basename(HERE) == "code" else os.path.join(HERE, "deliver")
RES = os.path.join(PKG, "results")
OUT = os.path.join(PKG, "docs")

U_WGT = 2.0 / math.sqrt(3)   # 计权口径：未计权 RMS vs A 计权，按 ±2 dB 矩形分布
U_POS = 1.5                  # 点位代表性：同一点位挪动 1~2 m 的差异
U_RES = 0.1 / math.sqrt(12)  # 读数分辨率 0.1 dB
K = 2.0                      # 95% 覆盖因子


def load():
    stats = json.load(io.open(os.path.join(RES, "stats.json"), encoding="utf-8"))
    rob = json.load(io.open(os.path.join(RES, "robust.json"), encoding="utf-8"))
    meta = json.load(io.open(os.path.join(RES, "meta.json"), encoding="utf-8"))
    return stats, rob, meta


def pflip(d, u):
    """|Δ|=d、标准不确定度 u 时，结论翻转的概率（正态近似）。"""
    if u <= 0:
        return 0.0
    return 0.5 * math.erfc(d / (u * math.sqrt(2)))


def main():
    stats, rob, meta = load()
    cals = [m["cal"] for m in meta]
    n = len(cals)
    mean = sum(cals) / n
    sd = math.sqrt(sum((c - mean) ** 2 for c in cals) / (n - 1))
    print("校准偏移：n=%d 均值 %.2f 样本标准差 %.2f 极差 %.2f" %
          (n, mean, sd, max(cals) - min(cals)))

    U_CAL = sd
    rows = []
    for s, r in zip(stats, rob):
        u_samp = r["ci_sampling"] / 1.96
        rest = math.sqrt(U_WGT ** 2 + u_samp ** 2 + U_POS ** 2 + U_RES ** 2)
        u_abs = math.sqrt(U_CAL ** 2 + rest ** 2)
        rows.append({
            "sid": r["sid"], "per": r["per"], "loc": r["loc"],
            "delta": r["delta"], "limit": r["limit"], "leq": r["leq"],
            "u_samp": u_samp, "u_rest": rest,
            "u_abs": u_abs, "U_abs": K * u_abs, "U_rel": K * rest,
        })

    print("\n如果校准项只有 ±u_cal 的把握，有多少组的结论会翻（翻转率 > 10%）：")
    sens = []
    for uc in (0.0, 1.0, 2.0, 3.0, round(U_CAL, 2)):
        k = 0
        for x in rows:
            u = math.sqrt(uc ** 2 + x["u_rest"] ** 2)
            if pflip(abs(x["delta"]), u) > 0.10:
                k += 1
        sens.append((uc, k))
        print("  u_cal = %.2f dB → %d / 15 组" % (uc, k))

    print("\n每组：Δ、绝对 95%% 区间（含校准）、段内 95%% 区间（不含校准）")
    for x in rows:
        print("  %s %s%-6s Δ%+5.1f   ±%4.1f   ±%4.1f" %
              (x["sid"], x["per"], x["loc"], x["delta"], x["U_abs"], x["U_rel"]))

    data = {"u_cal": U_CAL, "u_wgt": U_WGT, "u_pos": U_POS, "u_res": U_RES, "k": K,
            "cal_mean": mean, "cal_sd": sd, "cal_min": min(cals), "cal_max": max(cals),
            "sens": sens, "rows": rows}
    io.open(os.path.join(RES, "gum.json"), "w", encoding="utf-8").write(
        json.dumps(data, ensure_ascii=False, indent=1))
    print("\nsaved results/gum.json")


if __name__ == "__main__":
    main()
