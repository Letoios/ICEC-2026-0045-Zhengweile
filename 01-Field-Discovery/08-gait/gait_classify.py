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
T_INFO      = 1.0    # 绝对量：RMS × 自相关，低于此值说明这一段没有步态信息
T_DIFF      = 0.035  # 无量纲：正峰% − 负谷%
T_SKEW      = 0.25   # 无量纲：偏度
T_AC        = 0.70   # 无量纲：自相关强度


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
    if f["rms"] * f["ac"] < T_INFO:
        return "无法判定", "RMS×自相关 %.2f < %.1f（信号里没有步态信息）" % (
            f["rms"] * f["ac"], T_INFO)
    # ③ 跑步：步频高且幅度也大，或幅度极大
    if (f["cad"] > T_RUN_CAD and f["rms"] > T_RUN_MIN) or f["rms"] > T_RUN_RMS:
        return "跑步", "步频 %.2f Hz 且 RMS %.2f（或 RMS %.2f > %.1f）" % (
            f["cad"], f["rms"], f["rms"], T_RUN_RMS)
    # ④ 下台阶：触地尖峰型 —— 正向时间占比高且分布右偏
    if f["diff"] > T_DIFF and f["skew"] > T_SKEW:
        return "下台阶", "正−负 %+.3f > %.3f 且 偏度 %+.2f > %.2f" % (
            f["diff"], T_DIFF, f["skew"], T_SKEW)
    # ⑤ 平地走：波形最规整，周期性最强
    if f["ac"] > T_AC:
        return "平地走", "自相关 %.2f > %.2f" % (f["ac"], T_AC)
    # ⑥ 其余：上台阶（蹬起缓、波形对称、周期性弱）
    return "上台阶", "以上均不满足（正−负 %+.3f，偏度 %+.2f，自相关 %.2f）" % (
        f["diff"], f["skew"], f["ac"])


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
