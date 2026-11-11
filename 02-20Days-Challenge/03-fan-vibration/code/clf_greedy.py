# -*- coding: utf-8 -*-
"""贪心前向选择特征（目标：五类分组CV），并给出每一步的三类。"""
import csv
import numpy as np
rows=list(csv.DictReader(open(r"D:\deepseek工作\proj03\results\features.csv",encoding="utf-8-sig")))
ALL=["f0","rms","crest","centroid","e_low","e_mid","e_high","h2","h3","h4"]
Xall=np.array([[float(r[c]) for c in ALL] for r in rows])
y5=np.array([int(r["group"][1])-1 for r in rows]); y3=np.array([0 if v<3 else v-2 for v in y5])
num=np.array([int(r["file"].split("_")[1].split(".")[0]) for r in rows])
batch=np.array(["%s_%d"%(r["group"],n//5) for r,n in zip(rows,num)])
groups=sorted(set(batch)); COL={c:i for i,c in enumerate(ALL)}

def knn(A,ytr,B,K,k=3):
    out=[]
    for b in B:
        d=((A-b)**2).sum(1); nn=np.argsort(d)[:k]
        out.append(int(np.bincount(ytr[nn],minlength=K).argmax()))
    return np.array(out)

def cv(cols,K,y,k=3):
    X=Xall[:,[COL[c] for c in cols]]; ok=tot=0
    for g in groups:
        te=batch==g; tr=~te
        if te.sum()==0 or len(set(y[tr]))<K: continue
        mu,sd=X[tr].mean(0),X[tr].std(0)+1e-9
        p=knn((X[tr]-mu)/sd,y[tr],(X[te]-mu)/sd,K,k)
        ok+=int((p==y[te]).sum()); tot+=int(te.sum())
    return 100.0*ok/tot

sel=[]; rest=ALL[:]
print("步 加入特征      五类     三类")
best5=cv(sel+["f0"],5,y5) if False else 0
cur5=cv(["f0"],5,y5); cur3=cv(["f0"],3,y3)
sel=["f0"]; rest=[c for c in ALL if c!="f0"]
print(" 1 %-12s %6.1f%% %6.1f%%" % ("f0",cur5,cur3))
for step in range(2,11):
    best=None
    for c in rest:
        v5=cv(sel+[c],5,y5)
        if best is None or v5>best[0]: best=(v5,c)
    v5,c=best; v3=cv(sel+[c],3,y3)
    sel.append(c); rest.remove(c)
    print("%2d %-12s %6.1f%% %6.1f%%" % (step,c,v5,v3))
print()
print("最优（五类）子集:", sel, " 五类 %.1f%% / 三类 %.1f%%" % (cv(sel,5,y5), cv(sel,3,y3)))
for k in (1,2,4,5):
    print("  同子集 k=%d: 五类 %.1f%% / 三类 %.1f%%" % (k, cv(sel,5,y5,k), cv(sel,3,y3,k)))
