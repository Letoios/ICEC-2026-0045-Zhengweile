# -*- coding: utf-8 -*-
"""回放仿真的第二步：把「切换次数」和「判得准不准」放在一起看。

单看切换次数会得出「越保守越好」的错误结论——把确认时长调到 60 秒，
灯一次都不闪，但也早就不跟真值了。所以必须给两个指标：

  flicker   15 段合计切换次数（越少越稳）
  agree     逐秒一致率：灯当前状态 == 按 1 s Leq 应得的档位 的比例（越高越准）

两者的帕累托前沿才是「参数选在哪」的依据。

另外算冲击通道的阈值敏感性：Lmax 阈值取 78/80/82/84/85 时，各段会触发多少次。
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import EDGES, grade, load_index, simulate  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE) if os.path.basename(HERE) == "code" else os.path.join(HERE, "deliver")
RES = os.path.join(HERE, "build") if os.path.isdir(os.path.join(HERE, "build")) else os.path.join(PKG, "results")


def agree_rate(states, vals, fs, limit):
    """逐秒一致率：灯的状态与「瞬时档位」相同的比例。"""
    n = max(1, int(round(fs)))
    frames = []
    for i in range(0, len(vals) - n + 1, n):
        seg = vals[i:i + n]
        frames.append(10 * math.log10(sum(10 ** (v / 10.0) for v in seg) / len(seg)))
    ok = sum(1 for k, f in enumerate(frames[:len(states)])
             if states[k] == grade(f - limit))
    return ok / float(min(len(states), len(frames))) * 100.0


def main():
    idx = load_index()
    grid = []
    for confirm in (1.0, 2.0, 3.0, 5.0):
        for rel in (0.0, 1.0, 2.0, 3.0):
            sw_tot, ag_vals = 0, []
            for r in idx:
                st, sw, _, _, _ = simulate(r["vals"], r["fs"], r["limit"],
                                        confirm_s=confirm, release_db=rel)
                sw_tot += sw
                ag_vals.append(agree_rate(st, r["vals"], r["fs"], r["limit"]))
            ag = sum(ag_vals) / len(ag_vals)
            grid.append({"confirm": confirm, "release": rel,
                         "flicker": sw_tot, "agree": round(ag, 2)})
            print("confirm %.0fs release %.0fdB  →  切换 %3d   一致率 %5.1f%%"
                  % (confirm, rel, sw_tot, ag))

    # 帕累托前沿
    pts = sorted(grid, key=lambda x: (x["flicker"], -x["agree"]))
    front, best = [], -1
    for p in pts:
        if p["agree"] > best:
            front.append({"confirm": p["confirm"], "release": p["release"]})
            best = p["agree"]
    print("\n帕累托前沿:", front)

    # ---- 冲击通道阈值敏感性 ----
    # 冲击通道按「每秒采样峰值」判定（设计里就是这么定义的），不是 1 s 能量均
    sp = []
    for thr in (78, 80, 82, 84, 85):
        hits, segs, per = 0, 0, []
        for r in idx:
            n = max(1, int(round(r["fs"])))
            h = 0
            for i in range(0, len(r["vals"]) - n + 1, n):
                if max(r["vals"][i:i + n]) >= thr:
                    h += 1
            hits += h
            if h:
                segs += 1
            per.append(h)
        sp.append({"thr": thr, "seg_frames": hits, "seg_hit": segs, "per": per})
        print("SP 阈值 %d dB → 触发帧 %3d，涉及 %2d/15 段" % (thr, hits, segs))

    json.dump({"grid": grid, "pareto": front, "sp": sp},
              open(os.path.join(RES, "sim2.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    print("\nsaved sim2.json")


if __name__ == "__main__":
    main()
