# -*- coding: utf-8 -*-
"""特征消融：哪几个特征真正在起作用。"""
import csv, itertools
import numpy as np

rows = list(csv.DictReader(open(r"D:\deepseek工作\proj03\results\features.csv", encoding="utf-8-sig")))
ALL = ["f0","centroid","e_low","e_mid","e_high","h2","h3","h4","crest","rms"]
y5 = np.array([int(r["group"][1])-1 for r in rows])
y3 = np.array([0 if v<3 else v-2 for v in y5])

def acc(cols, y, K, k=3):
    X = np.array([[float(r[c]) for c in cols] for r in rows])
    Xs = (X-X.mean(0))/(X.std(0)+1e-9)
    ok = 0
    for i in range(len(y)):
        d = ((Xs-Xs[i])**2).sum(1); d[i]=1e18
        nn = np.argsort(d)[:k]
        ok += (int(np.bincount(y[nn], minlength=K).argmax()) == y[i])
    return 100*ok/len(y)

try:
    base = ["f0","centroid","e_low","e_mid","e_high","h2","h3","h4"]
    print("%-52s %7s %7s" % ("特征组合","五类","三类"))
    print("%-52s %6.1f%% %6.1f%%" % ("全部 8 个", acc(base,y5,5), acc(base,y3,3)))
    for drop in base:
        sub = [c for c in base if c != drop]
        print("%-52s %6.1f%% %6.1f%%" % ("去掉 " + drop, acc(sub,y5,5), acc(sub,y3,3)))
    print()
    cand = [
        ["f0","e_low","e_high","h2"],
        ["f0","e_low","e_mid","e_high"],
        ["f0","h2","h3","h4"],
        ["e_low","e_mid","e_high","h2","h3"],
        ["f0","centroid","e_high","h2"],
        ["f0","e_low","e_high","h2","h3","h4"],
    ]
    for c in cand:
        print("%-52s %6.1f%% %6.1f%%" % ("+".join(c), acc(c,y5,5), acc(c,y3,3)))
except Exception as e:
    print("ERR", e)
