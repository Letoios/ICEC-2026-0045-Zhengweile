# -*- coding: utf-8 -*-
"""按批次分组交叉验证。批次 = 组内按文件名序号每 5 段一批。"""
import csv
import numpy as np

rows = list(csv.DictReader(open(r"D:\deepseek工作\proj03\results\features.csv", encoding="utf-8-sig")))
COLS = ["f0", "e_mid", "e_high", "h2", "h3", "h4"]
X = np.array([[float(r[c]) for c in COLS] for r in rows])
y5 = np.array([int(r["group"][1]) - 1 for r in rows])
y3 = np.array([0 if v < 3 else v - 2 for v in y5])
num = np.array([int(r["file"].split("_")[1].split(".")[0]) for r in rows])
batch = np.array(["%s_%d" % (r["group"], n // 5) for r, n in zip(rows, num)])

groups = sorted(set(batch))
print("样本 %d 段，批次 %d 个" % (len(rows), len(groups)))
for g in groups:
    m = batch == g
    print("  %-8s n=%2d  %s" % (g, m.sum(), "".join("C%d" % (v + 1) for v in sorted(set(y5[m])))))

def knn(Xtr, ytr, Xte, K, k=3):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    A_ = (Xtr - mu) / sd; B_ = (Xte - mu) / sd
    out = []
    for b in B_:
        d = ((A_ - b) ** 2).sum(1); nn = np.argsort(d)[:k]
        out.append(int(np.bincount(ytr[nn], minlength=K).argmax()))
    return np.array(out)

print()
for name, y, K in (("五类", y5, 5), ("三类", y3, 3)):
    ok = tot = 0
    for g in groups:
        te = batch == g; tr = ~te
        if te.sum() == 0 or len(set(y[tr])) < K: continue
        p = knn(X[tr], y[tr], X[te], K)
        ok += int((p == y[te]).sum()); tot += int(te.sum())
    print("%s 分组交叉验证：%d/%d = %.1f%%" % (name, ok, tot, 100.0 * ok / tot))

for name, y, K in (("五类", y5, 5), ("三类", y3, 3)):
    ok = 0
    for i in range(len(y)):
        m = np.ones(len(y), bool); m[i] = False
        ok += int(knn(X[m], y[m], X[i:i+1], K)[0] == y[i])
    print("%s 留一法（旧口径）：%d/%d = %.1f%%" % (name, ok, len(y), 100.0 * ok / len(y)))
