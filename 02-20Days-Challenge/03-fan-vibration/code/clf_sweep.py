# -*- coding: utf-8 -*-
"""在 canonical 管线（features.csv / 分组交叉验证）上找能真正提高准确率的东西。"""
import csv, itertools
import numpy as np
rows=list(csv.DictReader(open(r"D:\deepseek工作\proj03\results\features.csv",encoding="utf-8-sig")))
ALL=["f0","rms","crest","centroid","e_low","e_mid","e_high","h2","h3","h4"]
Xall=np.array([[float(r[c]) for c in ALL] for r in rows])
y5=np.array([int(r["group"][1])-1 for r in rows]); y3=np.array([0 if v<3 else v-2 for v in y5])
num=np.array([int(r["file"].split("_")[1].split(".")[0]) for r in rows])
batch=np.array(["%s_%d"%(r["group"],n//5) for r,n in zip(rows,num)])
groups=sorted(set(batch))
COL={c:i for i,c in enumerate(ALL)}

def knn(Xtr,ytr,Xte,K,k=3,lda=False):
    mu,sd=Xtr.mean(0),Xtr.std(0)+1e-9
    A=(Xtr-mu)/sd; B=(Xte-mu)/sd
    if lda:
        Sw=np.zeros((A.shape[1],)*2); Sb=np.zeros_like(Sw); gm=A.mean(0)
        for c in range(K):
            Ac=A[ytr==c]
            if len(Ac)==0: continue
            mc=Ac.mean(0); Sw+= (Ac-mc).T@(Ac-mc); d=(mc-gm).reshape(-1,1); Sb+=len(Ac)*(d@d.T)
        Sw+=np.eye(len(Sw))*1e-6*np.trace(Sw)
        w,V=np.linalg.eigh(np.linalg.pinv(Sw)@Sb); V=V[:,np.argsort(w)[::-1][:K-1]]
        A=A@V; B=B@V
    out=[]
    for b in B:
        d=((A-b)**2).sum(1); nn=np.argsort(d)[:k]
        out.append(int(np.bincount(ytr[nn],minlength=K).argmax()))
    return np.array(out)

def cv(cols,K,y,k=3,lda=False):
    idx=[COL[c] for c in cols]; X=Xall[:,idx]; ok=tot=0
    for g in groups:
        te=batch==g; tr=~te
        if te.sum()==0 or len(set(y[tr]))<K: continue
        p=knn(X[tr],y[tr],X[te],K,k,lda); ok+=int((p==y[te]).sum()); tot+=int(te.sum())
    return ok,tot

BASE=["f0","e_mid","e_high","h2","h3","h4"]
print("%-42s %10s %10s" % ("配置","五类","三类"))
def line(tag,cols,k=3,lda=False):
    a=cv(cols,5,y5,k,lda); b=cv(cols,3,y3,k,lda)
    print("%-42s %4d/%d %.1f%%  %4d/%d %.1f%%" % (tag,a[0],a[1],100*a[0]/a[1],b[0],b[1],100*b[0]/b[1]))
    return a,b

line("基线（现行 6 特征, k=3）",BASE)
for k in (1,2,5,7):
    line("6 特征, k=%d"%k,BASE,k=k)
for extra in ("centroid","e_low","rms","crest","h4"):
    if extra in BASE: continue
    line("6 特征 + %s"%extra,BASE+[extra])
line("全部 10 特征",ALL)
line("基线 + LDA",BASE,lda=True)
line("基线 + LDA, k=1",BASE,k=1,lda=True)
line("全部 + LDA",ALL,lda=True)
