# -*- coding: utf-8 -*-
"""留一法分类：五类工况 + 三类故障。输出混淆矩阵与报告。"""
import os, csv, json
import numpy as np

FEAT = ["f0", "centroid", "e_low", "e_mid", "e_high", "h2", "h3", "h4"]
G5 = ["C1","C2","C3","C4","C5"]
G3 = ["正常","失衡","遮挡"]
rows = list(csv.DictReader(open(r"D:\deepseek工作\proj03\results\features.csv", encoding="utf-8-sig")))
X = np.array([[float(r[k]) for k in FEAT] for r in rows])
y5 = np.array([G5.index(r["group"]) for r in rows])
y3 = np.array([0 if r["group"] in ("C1","C2","C3") else (1 if r["group"]=="C4" else 2) for r in rows])
Xs = (X - X.mean(0)) / (X.std(0) + 1e-9)

def loo_centroid(Xs, y, K, w=None):
    if w is not None: Xs = Xs * w
    conf = np.zeros((K, K), int)
    for i in range(len(y)):
        m = np.ones(len(y), bool); m[i] = False
        mu = np.array([Xs[m & (y == k)].mean(0) for k in range(K)])
        pred = int(((mu - Xs[i])**2).sum(1).argmin())
        conf[y[i], pred] += 1
    return conf

def loo_knn(Xs, y, K, k=3):
    conf = np.zeros((K, K), int)
    for i in range(len(y)):
        d = ((Xs - Xs[i])**2).sum(1); d[i] = 1e18
        nn = np.argsort(d)[:k]
        votes = np.bincount(y[nn], minlength=K)
        conf[y[i], int(votes.argmax())] += 1
    return conf

def report(conf, names):
    acc = np.trace(conf) / conf.sum()
    print("  总体 %.1f%%  (%d/%d)" % (100*acc, np.trace(conf), conf.sum()))
    print("       " + " ".join("%6s" % n for n in names) + "   召回")
    for k, n in enumerate(names):
        rec = conf[k, k] / max(1, conf[k].sum())
        print("  %-4s " % n + " ".join("%6d" % v for v in conf[k]) + "   %.0f%%" % (100*rec))
    return acc

out = {}
print("=== 五分类（1/3/5 档 / 贴胶带 / 半遮挡），留一法 ===")
c5 = loo_centroid(Xs, y5, 5); out["acc5_centroid"] = report(c5, G5)
print()
print("=== 五分类 · kNN(k=3) ===")
c5k = loo_knn(Xs, y5, 5); out["acc5_knn"] = report(c5k, G5)
print()
print("=== 三分类（正常 / 失衡 / 遮挡），留一法 ===")
c3 = loo_centroid(Xs, y3, 3); out["acc3_centroid"] = report(c3, G3)
print()
print("=== 三分类 · kNN(k=3) ===")
c3k = loo_knn(Xs, y3, 3); out["acc3_knn"] = report(c3k, G3)

json.dump(dict(features=FEAT, conf5=c5.tolist(), conf5_knn=c5k.tolist(),
               conf3=c3.tolist(), conf3_knn=c3k.tolist(), **{k: float(v) for k, v in out.items()}),
          open(r"D:\deepseek工作\proj03\results\clf_report.json","w",encoding="utf-8"),
          ensure_ascii=False, indent=1)
print()
print("报告已写入 results/clf_report.json")
