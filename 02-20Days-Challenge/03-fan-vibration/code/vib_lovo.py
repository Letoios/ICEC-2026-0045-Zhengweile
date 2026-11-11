# -*- coding: utf-8 -*-
"""振动通道 15 段的留一法可分性（3 特征：log 水平、log 垂直、log 主频）。"""
import json, math
import numpy as np
D = json.load(open(r"D:\deepseek工作\proj03\results\vibration.json", encoding="utf-8"))
rows = D["rows"]
X = np.array([[math.log10(r["hor"]), math.log10(r["ver"]), math.log10(r["f1"])] for r in rows])
y = [r["g"] for r in rows]
mu, sd = X.mean(0), X.std(0) + 1e-9
Z = (X - mu) / sd

def loo(k=1):
    ok = 0; wrong = []
    for i in range(len(Z)):
        d = np.sqrt(((Z - Z[i]) ** 2).sum(1)); d[i] = 1e9
        idx = np.argsort(d)[:k]
        pred = max(set(y[j] for j in idx), key=[y[j] for j in idx].count)
        if pred == y[i]: ok += 1
        else: wrong.append((rows[i]["s"], y[i], pred))
    return ok, wrong

for k in (1, 3):
    ok, wrong = loo(k)
    print("kNN k=%d 留一法：%d/%d = %.1f%%" % (k, ok, len(Z), 100.0 * ok / len(Z)))
    for w in wrong: print("   错：", w)

# 只用两个 RMS，不含频率
X2 = Z[:, :2]
ok = 0; wrong = []
for i in range(len(X2)):
    d = np.sqrt(((X2 - X2[i]) ** 2).sum(1)); d[i] = 1e9
    j = int(np.argmin(d))
    if y[j] == y[i]: ok += 1
    else: wrong.append((rows[i]["s"], y[i], y[j]))
print("只用 2 个 RMS（不含主频）k=1：%d/%d = %.1f%%" % (ok, len(X2), 100.0*ok/len(X2)))
for w in wrong: print("   错：", w)
