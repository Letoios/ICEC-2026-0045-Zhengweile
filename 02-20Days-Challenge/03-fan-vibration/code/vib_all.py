# -*- coding: utf-8 -*-
import os, csv, json
import numpy as np
ROOT = r"D:\deepseek工作\proj03\data\振动"
GROUPS = [
    ("C1 一档",   ["1档","1档1","1档2"]),
    ("C2 三档",   ["3档","3档1","3档2"]),
    ("C3 五档",   ["5档","5档1","5档2"]),
    ("C4 胶带",   ["5档带胶带","5档带胶带1","5档带胶带2"]),
    ("C5 半遮挡", ["半遮挡","半遮挡1","半遮挡2"]),
]

def load(p):
    t,x,y,z=[],[],[],[]
    with open(p, encoding="utf-8-sig", newline="") as f:
        r=csv.reader(f); next(r)
        for row in r:
            if len(row)<4: continue
            try: t.append(float(row[0])); x.append(float(row[1])); y.append(float(row[2])); z.append(float(row[3]))
            except ValueError: continue
    return np.array(t),np.array(x),np.array(y),np.array(z)

def spec(zd, fs):
    n=1
    while n<len(zd): n*=2
    Z=np.abs(np.fft.rfft(zd*np.hanning(len(zd)),n)); fr=np.fft.rfftfreq(n,1.0/fs)
    return fr, Z

def top_peaks(fr,Z,k=2):
    m=(fr>=15)&(fr<=500); f_,z_=fr[m],Z[m]
    idx=np.argsort(z_)[::-1]; out=[]
    for i in idx:
        if all(abs(f_[i]-q)>10 for q,_ in out): out.append((float(f_[i]), float(z_[i])))
        if len(out)>=k: break
    return out

rows=[]
for g, subs in GROUPS:
    for s in subs:
        p=os.path.join(ROOT,s,"Raw Data.csv")
        if not os.path.exists(p): print("缺",s); continue
        t,x,y,z=load(p); fs=1.0/np.median(np.diff(t))
        xd,yd,zd=x-x.mean(),y-y.mean(),z-z.mean()
        hor=np.hypot(xd,yd).std()
        fr,Z=spec(zd,fs)
        band=(fr>=15)&(fr<=500); hi=(fr>150)&(fr<=500)
        ehi=float((Z[hi]**2).sum()/max((Z[band]**2).sum(),1e-12))
        pk=top_peaks(fr,Z)
        rows.append(dict(g=g,s=s,dur=float(t[-1]-t[0]),fs=float(fs),
                         hor=float(hor),ver=float(zd.std()),
                         f1=pk[0][0],f2=pk[1][0] if len(pk)>1 else 0.0,
                         r=pk[1][1]/pk[0][1] if len(pk)>1 else 0.0,
                         ehi=ehi))
print("%-10s %-8s %7s %8s %8s %8s %8s %6s" % ("工况","样本","时长","水平RMS","垂直RMS","主峰","次峰","次/主"))
for r in rows:
    print("%-10s %-8s %7.1f %8.4f %8.4f %8.1f %8.1f %6.2f" % (r["g"],r["s"],r["dur"],r["hor"],r["ver"],r["f1"],r["f2"],r["r"]))
print()
print("%-10s %3s %10s %10s %9s %9s" % ("工况","n","水平RMS","垂直RMS","主频","高频能量"))
summ={}
for g,_ in GROUPS:
    v=[r for r in rows if r["g"]==g]
    if not v: continue
    d=dict(n=len(v), hor=float(np.mean([q["hor"] for q in v])), ver=float(np.mean([q["ver"] for q in v])),
           f=float(np.mean([q["f1"] for q in v])), ehi=float(np.mean([q["ehi"] for q in v])))
    summ[g]=d
    print("%-10s %3d %10.4f %10.4f %9.1f %10.3f" % (g,d["n"],d["hor"],d["ver"],d["f"],d["ehi"]))
json.dump(dict(rows=rows,summary=summ), open(r"D:\deepseek工作\proj03\results\vibration.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("\n写入 results/vibration.json")
