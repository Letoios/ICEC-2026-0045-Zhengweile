# -*- coding: utf-8 -*-
import csv
import numpy as np
rows = list(csv.DictReader(open(r"D:\deepseek工作\proj03\results\features.csv", encoding="utf-8-sig")))
ALL = ["f0","centroid","e_low","e_mid","e_high","h2","h3","h4"]
y5 = np.array([int(r["group"][1])-1 for r in rows])
y3 = np.array([0 if v<3 else v-2 for v in y5])

def acc(cols, y, K, k=3):
    X = np.array([[float(r[c]) for c in cols] for r in rows])
    Xs = (X-X.mean(0))/(X.std(0)+1e-9)
    ok=0
    for i in range(len(y)):
        d=((Xs-Xs[i])**2).sum(1); d[i]=1e18
        nn=np.argsort(d)[:k]
        ok += (int(np.bincount(y[nn],minlength=K).argmax())==y[i])
    return 100*ok/len(y)

cur = list(ALL); best = acc(cur,y5,5)+acc(cur,y3,3)
print("起点 %-40s 五类 %.1f 三类 %.1f  合计 %.1f" % (",".join(cur), acc(cur,y5,5), acc(cur,y3,3), best))
improved = True
while improved:
    improved = False
    for c in list(cur):
        trial = [x for x in cur if x != c]
        if not trial: continue
        s = acc(trial,y5,5)+acc(trial,y3,3)
        if s > best + 1e-9:
            cur, best, improved = trial, s, True
            print("  去掉 %-8s -> 五类 %.1f 三类 %.1f  合计 %.1f" % (c, acc(trial,y5,5), acc(trial,y3,3), s))
print()
print("最终特征：", cur)
print("  五类 %.1f%%   三类 %.1f%%" % (acc(cur,y5,5), acc(cur,y3,3)))
