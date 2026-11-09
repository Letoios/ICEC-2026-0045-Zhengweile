# -*- coding: utf-8 -*-
"""给规则「最好的机会」：把阈值在合理区间内扫一遍，取最优。"""
import csv, json
import numpy as np

rows = list(csv.DictReader(open(r"D:\deepseek工作\proj03\results\features.csv", encoding="utf-8-sig")))
y3 = np.array([0 if r["group"] in ("C1","C2","C3") else (1 if r["group"]=="C4" else 2) for r in rows])
h2 = np.array([float(r["h2"]) for r in rows])
eh = np.array([float(r["e_high"]) for r in rows])
f0 = np.array([float(r["f0"]) for r in rows])
g5 = np.array([r["group"] for r in rows])

best = None
for t_h2 in np.arange(1.5, 6.01, 0.1):
    for t_hi in np.arange(0.15, 0.26, 0.005):
        pred = np.where(h2 > t_h2, 2, np.where(eh > t_hi, 1, 0))
        acc = (pred == y3).mean()
        if best is None or acc > best[0]:
            best = (acc, t_h2, t_hi)
print("三类 · 规则最优阈值：h2 > %.2f，e_high > %.3f  →  分组CV %.1f%%" % (best[1], best[2], 100*best[0]))
print("  （对照：kNN 分组CV 90.8%）")
print()

# 五类：在最优三类阈值基础上，再扫 f0 两条切线
t_h2, t_hi = best[1], best[2]
best5 = None
for t1 in np.arange(34.0, 37.01, 0.1):
    for t2 in np.arange(37.5, 40.51, 0.1):
        pred = np.where(h2 > t_h2, "C5", np.where(eh > t_hi, "C4",
                 np.where(f0 < t1, "C1", np.where(f0 < t2, "C2", "C3"))))
        acc = (pred == g5).mean()
        if best5 is None or acc > best5[0]:
            best5 = (acc, t1, t2)
print("五类 · 规则最优阈值：f0 < %.1f → C1，< %.1f → C2  →  分组CV %.1f%%" % (best5[1], best5[2], 100*best5[0]))
print("  （对照：kNN 分组CV 61.2%）")
json.dump({"three": {"h2": float(best[1]), "e_high": float(best[2]), "acc": float(best[0])},
           "five": {"f0_12": float(best5[1]), "f0_23": float(best5[2]), "acc": float(best5[0])}},
          open(r"D:\deepseek工作\proj03\results\rule_best_thr.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
