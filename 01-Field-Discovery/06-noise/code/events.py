# -*- coding: utf-8 -*-
"""事件归因：Leq 里有多少是被少数「事件」拉上去的？

事件定义：连续 ≥0.3 s 高于本段 L90 + 10 dB（0.3 s 折算样本数 = fs*0.3）。
统计：事件次数、事件总时长占比、事件能量占总能量比。
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import load_index, RES  # noqa: E402

EV_DB = 10.0
EV_MIN_S = 0.3


def pct(sorted_vals, q):
    if not sorted_vals:
        return 0.0
    k = (len(sorted_vals) - 1) * q / 100.0
    lo, hi = int(math.floor(k)), int(math.ceil(k))
    if lo == hi:
        return sorted_vals[lo]
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def main():
    idx = load_index()
    rows = []
    for r in idx:
        v = r["vals"]
        fs = r["fs"]
        s = sorted(v)
        l90 = pct(s, 90)
        thr = l90 + EV_DB
        need = max(1, int(round(fs * EV_MIN_S)))
        energy = [10 ** (x / 10.0) for x in v]
        tot_e = sum(energy)
        ev_n, ev_cnt, ev_e = 0, 0, 0.0
        run = 0
        ev_s = 0
        for i, x in enumerate(v):
            if x >= thr:
                run += 1
                ev_e += energy[i]
            else:
                if run >= need:
                    ev_n += 1
                    ev_s += run
                run = 0
        if run >= need:
            ev_n += 1
            ev_s += run
        rows.append({"sid": r["sid"], "site": r["loc"], "per": r["per"],
                     "l90": l90, "thr": thr, "n": ev_n,
                     "t_pct": ev_s / len(v) * 100.0, "e_pct": ev_e / tot_e * 100.0, "secs": len(v) / fs})
        print("%s %-6s %-2s  L90 %5.1f  阈值 %5.1f  事件 %2d 次  能量占比 %5.1f%%"
              % (r["sid"], r["loc"], r["per"], l90, thr, ev_n, ev_e / tot_e * 100))
    json.dump(rows, open(os.path.join(RES, "events.json"), "w", encoding="utf-8"),
              ensure_ascii=False)


if __name__ == "__main__":
    main()
