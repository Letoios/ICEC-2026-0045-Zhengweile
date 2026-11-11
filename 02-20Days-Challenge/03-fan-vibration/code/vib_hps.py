# -*- coding: utf-8 -*-
"""用谐波梳(HPS)找转子基频 f0，再判断主峰是 f0 的几倍。3 片叶片时叶片通过频率 = 3f0。"""
import os, csv
import numpy as np
ROOT = r"D:\deepseek工作\proj03\data\振动"
S = ["1档","1档1","1档2","3档","3档1","3档2","5档","5档1","5档2",
     "5档带胶带","5档带胶带1","5档带胶带2","半遮挡","半遮挡1","半遮挡2"]

def load(p):
    t,x,y,z=[],[],[],[]
    with open(p, encoding="utf-8-sig", newline="") as f:
        r=csv.reader(f); next(r)
        for row in r:
            if len(row)<4: continue
            try: t.append(float(row[0])); x.append(float(row[1])); y.append(float(row[2])); z.append(float(row[3]))
            except ValueError: continue
    return np.array(t),np.array(x),np.array(y),np.array(z)

print("%-12s %7s %8s %8s %9s %9s  %s" % ("样本","f0/Hz","rpm","主峰","主峰/f0","3f0","主峰=3f0?"))
print("-"*92)
for s in S:
    p=os.path.join(ROOT,s,"Raw Data.csv")
    if not os.path.exists(p): continue
    t,x,y,z=load(p); fs=1.0/np.median(np.diff(t))
    zd=z-z.mean()
    n=1
    while n<len(zd): n*=2
    Z=np.abs(np.fft.rfft(zd*np.hanning(len(zd)),n)); fr=np.fft.rfftfreq(n,1.0/fs)
    band=(fr>=10)&(fr<=520); f_,z_=fr[band],Z[band]
    k=int(np.argmax(z_)); fpk=float(f_[k])
    # HPS: 对候选 f0 累乘 1..4 次谐波幅度
    best=(0,0)
    for cand in np.arange(10.0, 120.0, 0.05):
        sc=1.0
        for h in (1,2,3,4):
            idx=np.argmin(np.abs(f_-cand*h))
            sc*=z_[idx]+1e-9
        if sc>best[0]: best=(sc,cand)
    f0=best[1]
    ratio=fpk/f0
    near3 = "是" if abs(ratio-3)<0.35 else ("%.2f×" % ratio)
    print("%-12s %7.2f %8.0f %8.1f %9.2f %9.1f  %s" % (s, f0, f0*60, fpk, ratio, 3*f0, near3))
