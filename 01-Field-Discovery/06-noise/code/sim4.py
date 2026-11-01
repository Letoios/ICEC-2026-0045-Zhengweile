# -*- coding: utf-8 -*-
"""在对称回差的基础上再扫「保持时长 × 最短驻留」。

这两个参数原来固定在 5 s / 10 s，是从课题06 光效文档里带过来的经验值，
从来没被数据检验过。这里补上：看它们各自值多少准确率。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sim import grade, load_index  # noqa: E402
from sim3 import frames_of, run, score, smooth  # noqa: E402

BASE = os.path.dirname(os.path.abspath(__file__))


def main():
    idx = load_index()
    cache = []
    for r in idx:
        fr = frames_of(r["vals"], r["fs"])
        t1 = [grade(f - r["limit"]) for f in fr]
        t3 = [grade(f - r["limit"]) for f in smooth(fr, 3)]
        cache.append((fr, r["limit"], t1, t3))

    rows = []
    for hold in (2.0, 3.0, 5.0):
        for dwell in (0.0, 5.0, 10.0):
            sw_tot, a1, a3, w1 = 0, [], [], []
            for fr, lim, t1, t3 in cache:
                st, sw = run(fr, lim, "sym", confirm=3.0, band=2.0,
                             hold=hold, min_dwell=dwell)
                sw_tot += sw
                a1.append(score(st, t1)[0])
                x, y = score(st, t3)
                a3.append(x)
                w1.append(y)
            rec = {"hold": hold, "dwell": dwell, "flicker": sw_tot,
                   "agree1": round(sum(a1) / 15, 2),
                   "agree3": round(sum(a3) / 15, 2),
                   "within1": round(sum(w1) / 15, 2)}
            rows.append(rec)
            print("保持 %.0fs 最短驻留 %2.0fs → 切换 %3d | 一致1s %5.1f%% | "
                  "一致3s %5.1f%% | 差一档内 %5.1f%%"
                  % (hold, dwell, sw_tot, rec["agree1"], rec["agree3"], rec["within1"]))
    json.dump(rows, open(os.path.join(BASE, "build", "sim4.json"), "w",
                         encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\nsaved sim4.json")


if __name__ == "__main__":
    main()
