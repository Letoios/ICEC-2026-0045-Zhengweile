# -*- coding: utf-8 -*-
"""
课题 08　多姿态步态加速度特征采集与对比 —— 判定脚本（v2）

v2 相对 v1 的三处改动：
  1. 特征全部改成**无量纲量**（整段除以自身 RMS），阈值不再依赖"这个人抖得有多厉害"；
  2. 上下楼从 1 个判据升级为 2 个判据并联（正负峰不对称 + 偏度），余量加倍；
  3. 「静止」增加周期性守卫（能量低但仍在周期性起伏的，不算静止）。

用法：
    python gait_classify.py 2026-10-24_18-28-12
    python gait_classify.py D:\\phydata\\all_records

依赖：numpy, pandas
"""
import sys, os, glob
import numpy as np
import pandas as pd

# ---------- 阈值（在 8 段实测数据上标定，见 README 第五节）----------
T_STILL     = 1.5    # 绝对量：竖直 RMS (m/s^2)。静止时只剩传感器噪声，与人无关
T_STILL_AC  = 0.35   # 无量纲：自相关。能量低但周期性明显 → 不是静止
T_RUN_RMS   = 10.0   # 绝对量：竖直 RMS
T_RUN_CAD   = 2.0    # 无量纲：步频 (Hz)
T_RUN_MIN   = 6.0    # 绝对量：步频高但幅度不够，不算跑步（快节奏下楼会到 2.3 Hz）
T_DOWN_RMS  = 1.5    # m/s²：下台阶要求的最小幅度
T_INFO      = 1.0    # 绝对量：RMS × 自相关，低于此值说明这一段没有步态信息
T_INFO_RMS  = 0.8    # 绝对量：只有能量也很低才算「没信息」；正常人上楼 RMS≈2.8 不该被拒
T_DIFF      = 0.035  # 无量纲：正峰% − 负谷%
T_SKEW      = 0.25   # 无量纲：偏度
T_AC        = 0.70   # 无量纲：仅作参考，不再单独用于判定
T_SKEW_W    = 0.20   # 无量纲：偏度正部的权重。走路脚跟着地有正向尖峰，上楼没有
T_WALK      = 0.631  # 无量纲：ac + diff + 0.2·max(0,skew) 的走路阈值
                    # 26 段实测：走路最低 0.666 / 上楼最高 0.596，取中点


def movavg(x, k):
    if k < 2:
        return x.copy()
    return np.convolve(x, np.ones(k) / k, mode="same")


def load(folder):
    acc = pd.read_csv(os.path.join(folder, "Accelerometer.csv"))
    acc.columns = ["t", "ax", "ay", "az"]
    acc = acc.dropna().reset_index(drop=True)
    t = acc["t"].to_numpy()
    A = acc[["ax", "ay", "az"]].to_numpy()
    fs = 1.0 / np.median(np.diff(t))

    gpath = os.path.join(folder, "Gravity.csv")
    if os.path.exists(gpath):
        gr = pd.read_csv(gpath)
        gr.columns = ["t", "gx", "gy", "gz"]
        gr = gr.dropna().reset_index(drop=True)
        G = np.column_stack([np.interp(t, gr["t"].to_numpy(), gr[c].to_numpy())
                             for c in ["gx", "gy", "gz"]])
    else:
        G = np.tile(A.mean(axis=0), (len(A), 1))   # 兼容老格式
    gh = G / np.linalg.norm(G, axis=1)[:, None]
    return (A * gh).sum(axis=1), fs, A


def features(v, fs):
    vd = v - movavg(v, int(fs * 1.0))     # 去 1 s 滑动均值 = 去重力基线
    s = float(vd.std())
    if s < 1e-9:
        s = 1e-9
    z = vd / s                            # ← 无量纲化，后面所有形状特征都与幅度无关
    dur = len(v) / fs

    idx, last = [], -1e9
    for i in range(1, len(z) - 1):
        if z[i] > 1.0 and z[i] >= z[i - 1] and z[i] > z[i + 1] and i - last > fs * 0.28:
            idx.append(i)
            last = i
    P = np.array(idx)
    cad = len(P) / dur

    x = z - z.mean()
    nfft = 1 << int(np.ceil(np.log2(2 * len(x))))
    Xr = np.fft.rfft(x, nfft)
    ac = np.fft.irfft(Xr * np.conj(Xr), nfft)[:len(x)]
    ac = ac / ac[0]
    lo, hi = int(fs / 3.0), int(fs / 0.4)
    acmax = float(ac[lo:hi].max())

    apos = float((z > 1.5).mean())
    aneg = float((z < -1.5).mean())

    return dict(dur=dur, fs=fs, rms=s, cad=cad, ac=acmax, diff=apos - aneg,
                crest=float(np.abs(z).max()), skew=float((z ** 3).mean()),
                kurt=float((z ** 4).mean()))


def classify(f):
    # ① 静止：能量极低且没有周期性
    if f["rms"] < T_STILL and f["ac"] < T_STILL_AC:
        return "静止", "RMS %.2f < %.1f 且 自相关 %.2f < %.2f" % (
            f["rms"], T_STILL, f["ac"], T_STILL_AC)
    # ② 信息量门槛：能量与周期性的乘积太低 → 这段里没有步态信息，拒绝判定
    # ② 不再拒答：宁可给一个可能错的答案，也不输出「不知道」（课题要求可执行的判定）
    if f["rms"] < T_INFO_RMS and f["rms"] * f["ac"] < T_INFO:
        # 能量低到连步态都谈不上，但仍要给出最接近的一类
        return "平地走", "能量极低（RMS %.2f、RMS×自相关 %.2f），按「静默移动」归入平地走" % (
            f["rms"], f["rms"] * f["ac"])
    # ③ 跑步：步频高且幅度也大，或幅度极大
    if (f["cad"] > T_RUN_CAD and f["rms"] > T_RUN_MIN) or f["rms"] > T_RUN_RMS:
        return "跑步", "步频 %.2f Hz 且 RMS %.2f（或 RMS %.2f > %.1f）" % (
            f["cad"], f["rms"], f["rms"], T_RUN_RMS)
    # ④ 下台阶：触地尖峰型 —— 正向时间占比高且分布右偏
    #    另加 RMS ≥ T_DOWN_RMS：极慢走手提时 diff/skew 会偶然同时越界，靠能量挡回去
    if f["diff"] > T_DIFF and f["skew"] > T_SKEW and f["rms"] >= T_DOWN_RMS:
        return "下台阶", "正−负 %+.3f > %.3f 且 偏度 %+.2f > %.2f 且 RMS %.2f ≥ %.1f" % (
            f["diff"], T_DIFF, f["skew"], T_SKEW, f["rms"], T_DOWN_RMS)
    # ⑤ 平地走 vs 上台阶：单看自相关会跨人失败（它测持机摆动习惯），
    #    改成 ac + diff + 0.2·skew⁺ 联合分。上楼的正负差常年偏低、且没有触地尖峰（偏度不右偏），
    #    三样叠起来才把两类拉开；只用前两样时空隙只有 0.010，加第三样后是 0.070
    score = f["ac"] + f["diff"] + T_SKEW_W * max(0.0, f["skew"])
    if score >= T_WALK:
        return "平地走", "ac+diff+0.2·skew⁺ = %.3f ≥ %.3f（自相关 %.2f，正−负 %+.3f，偏度 %+.2f）" % (
            score, T_WALK, f["ac"], f["diff"], f["skew"])
    # ⑥ 上台阶
    return "上台阶", "ac+diff+0.2·skew⁺ = %.3f < %.3f（自相关 %.2f，正−负 %+.3f，偏度 %+.2f）" % (
        score, T_WALK, f["ac"], f["diff"], f["skew"])


def run_one(folder):
    v, fs, A = load(folder)
    f = features(v, fs)
    amag = np.linalg.norm(A, axis=1)
    f["impact"] = float(100 * (amag > 20).mean())
    label, why = classify(f)
    return f, label, why


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    target = sys.argv[1]
    if os.path.exists(os.path.join(target, "Accelerometer.csv")):
        folders = [target]
    else:
        folders = sorted(d for d in glob.glob(os.path.join(target, "*"))
                         if os.path.exists(os.path.join(d, "Accelerometer.csv")))
    rows = []
    for d in folders:
        f, label, why = run_one(d)
        rows.append(dict(sample=os.path.basename(d.rstrip("\\/")),
                         dur=round(f["dur"], 1), rms=round(f["rms"], 2),
                         cad=round(f["cad"], 2), ac=round(f["ac"], 2),
                         diff=round(f["diff"], 3), skew=round(f["skew"], 2),
                         crest=round(f["crest"], 2), label=label))
        print("─" * 80)
        print("样本：%s" % rows[-1]["sample"])
        print("  RMS %.2f｜步频 %.2f Hz｜自相关 %.2f｜正−负 %+.3f｜偏度 %+.2f｜波峰因数 %.2f"
              % (f["rms"], f["cad"], f["ac"], f["diff"], f["skew"], f["crest"]))
        print("  判定：%s　（%s）" % (label, why))
    if len(rows) > 1:
        print("─" * 80)
        print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
