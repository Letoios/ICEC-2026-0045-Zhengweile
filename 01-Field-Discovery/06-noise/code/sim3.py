# -*- coding: utf-8 -*-
"""回放仿真第三步：把准确率提上去。

三处改动，各自解决一个真问题：

1) 评价基准错了。
   原来拿「1 s Leq 的档位」当真值，但 1 s 只有 9 个样本，能量均值抖得厉害，
   一个"完美跟随"的灯反而会疯狂闪。人耳响度积分约 1–3 s，所以真值应取 3 s 能量均的档位。

2) 回差是单边的，系统性偏低一档。
   原规则：升档要 Δ>边界，降档要 Δ<边界−2 dB。门槛一升一降不对称，
   平衡点整体下移，于是出现「能量均值判中度、灯停在轻度」（发现 3）。
   改法：以边界为中心对称开带。

3) 输入的时间尺度与判据不匹配。
   状态机吃的是 1 s Leq，而人看到一个档位需要几百毫秒才认。
   把输入也换成 3 s 能量均，输入抖动变小，状态自然更稳更准。

输出 build/sim3.json。
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import EDGES, grade, load_index  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE) if os.path.basename(HERE) == "code" else os.path.join(HERE, "deliver")
RES = os.path.join(HERE, "build") if os.path.isdir(os.path.join(HERE, "build")) else os.path.join(PKG, "results")


def frames_of(vals, fs):
    n = max(1, int(round(fs)))
    out = []
    for i in range(0, len(vals) - n + 1, n):
        seg = vals[i:i + n]
        out.append(10 * math.log10(sum(10 ** (v / 10.0) for v in seg) / len(seg)))
    return out


def smooth(ref, win):
    out, acc = [], []
    for v in ref:
        acc.append(v)
        if len(acc) > win:
            acc.pop(0)
        out.append(10 * math.log10(sum(10 ** (x / 10.0) for x in acc) / len(acc)))
    return out


def run(frames, limit, mode, confirm=3.0, band=2.0, hold=5.0, min_dwell=10.0):
    """mode='old' 单边回差（升档不加带、降档减 2 dB）；
       mode='sym' 对称回差（升档加带、降档减带）。"""
    st, cur, since = [], 0, 0.0
    cand, cand_run = None, 0
    hold_run = 0
    switches = 0
    for f in frames:
        d = f - limit
        g = grade(d)
        if g > cur:
            need = EDGES[cur][1] + (band if mode == "sym" else 0.0)
            if d > need:
                cand, cand_run = (g, cand_run + 1) if cand == g else (g, 1)
            else:
                cand, cand_run = None, 0
            if cand_run >= confirm:
                cur, since, cand, cand_run, hold_run = g, 0, None, 0, 0
                switches += 1
        else:
            cand, cand_run = None, 0
        if g < cur:
            hold_run = hold_run + 1 if d < EDGES[cur][0] - band else 0
            if hold_run >= hold and since >= min_dwell:
                cur, since, hold_run = g, 0, 0
                switches += 1
        else:
            hold_run = 0
        st.append(cur)
        since += 1
    return st, switches


def score(states, truth):
    n = min(len(states), len(truth))
    ok = sum(1 for i in range(n) if states[i] == truth[i])
    within = sum(1 for i in range(n) if abs(states[i] - truth[i]) <= 1)
    return ok / float(n) * 100.0, within / float(n) * 100.0


VARIANTS = [
    ("A 原设计（1 s 输入·单边回差）", "old", 1, 2.0),
    ("B 对称回差（1 s 输入）", "sym", 1, 2.0),
    ("C 3 s 输入·对称回差", "sym", 3, 2.0),
    ("D 3 s 输入·回差 1 dB", "sym", 3, 1.0),
    ("E 3 s 输入·回差 2 dB·确认 2 s", "sym", 3, 2.0),
]


def main():
    idx = load_index()
    rows = []
    for name, mode, inwin, band in VARIANTS:
        for confirm in (2.0, 3.0, 4.0, 5.0):
            sw_tot = 0
            a1, a3, w1 = [], [], []
            for r in idx:
                fr = frames_of(r["vals"], r["fs"])
                fin = smooth(fr, inwin) if inwin > 1 else fr
                st, sw = run(fin, r["limit"], mode, confirm=confirm, band=band)
                sw_tot += sw
                t1 = [grade(f - r["limit"]) for f in fr]
                t3 = [grade(f - r["limit"]) for f in smooth(fr, 3)]
                a1.append(score(st, t1)[0])
                x, y = score(st, t3)
                a3.append(x)
                w1.append(y)
            rows.append({"variant": name, "confirm": confirm,
                         "flicker": sw_tot,
                         "agree1": round(sum(a1) / 15, 2),
                         "agree3": round(sum(a3) / 15, 2),
                         "within1": round(sum(w1) / 15, 2)})
            print("%-28s 确认 %.0fs → 切换 %3d | 一致1s %5.1f%% | 一致3s %5.1f%% | 差一档内 %5.1f%%"
                  % (name, confirm, sw_tot, rows[-1]["agree1"],
                     rows[-1]["agree3"], rows[-1]["within1"]))
        print("")

    json.dump(rows, open(os.path.join(RES, "sim3.json"), "w",
                         encoding="utf-8"), ensure_ascii=False, indent=1)
    best = max(rows, key=lambda r: r["agree3"])
    print("best by agree3:", best)


if __name__ == "__main__":
    main()
