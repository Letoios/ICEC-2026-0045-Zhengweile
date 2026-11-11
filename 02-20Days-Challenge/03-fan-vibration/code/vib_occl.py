# -*- coding: utf-8 -*-
import os, csv
import numpy as np
ROOT = r"D:\deepseek工作\proj03\data\振动"
S = ["5档","5档1","5档2","半遮挡","半遮挡1","半遮挡2"]

def load(p):
    t,x,y,z=[],[],[],[]
    with open(p, encoding="utf-8-sig", newline="") as f:
        r=csv.reader(f); next(r)
        for row in r:
            if len(row)<4: continue
            try: t.append(float(row[0])); x.append(float(row[1])); y.append(float(row[2])); z.append(float(row[3]))
            except ValueError: continue
    return np.array(t),np.array(x),np.array(y),np.array(z)

def peaks(zd, fs, k=2):
    n=1
    while n<len(zd): n*=2
    w=np.hanning(len(zd)); Z=np.abs(np.fft.rfft(zd*w,n)); fr=np.fft.rfftfreq(n,1.0/fs)
    m=(fr>=15)&(fr<=500); f_,z_=fr[m],Z[m]
    idx=np.argsort(z_)[::-1]; out=[]
    for i in idx:
        if all(abs(f_[i]-q)>8 for q,_ in out): out.append((f_[i], z_[i]))
        if len(out)>=k: break
    return out

print("%-8s %7s %8s %8s %8s %8s   主峰/次峰" % ("样本","时长","水平RMS","垂直RMS","主频","高频能量"))
agg={}
for s in S:
    p=os.path.join(ROOT,s,"Raw Data.csv")
    if not os.path.exists(p): print("缺", s); continue
    t,x,y,z=load(p); fs=1.0/np.median(np.diff(t))
    xd,yd,zd=x-x.mean(),y-y.mean(),z-z.mean()
    h=np.hypot(xd,yd).std()
    pk=peaks(zd,fs)
    # 高频能量占比（>150 Hz）相对于 15-500
    n=1
    while n<len(zd): n*=2
    Z=np.abs(np.fft.rfft(zd*np.hanning(len(zd)),n)); fr=np.fft.rfftfreq(n,1.0/fs)
    band=(fr>=15)&(fr<=500); hi=(fr>150)&(fr<=500)
    e=float((Z[hi]**2).sum()/max((Z[band]**2).sum(),1e-12))
    print("%-8s %7.1f %8.4f %8.4f %8.1f %8.3f   %s" % (s, t[-1]-t[0], h, zd.std(), pk[0][0], e,
          "  ".join("%.1f(%.2f)" % (f,a/pk[0][1]) for f,a in pk)))
    agg.setdefault("5档" if s.startswith("5") else "半遮挡",[]).append((h, zd.std(), pk[0][0], e))
print()
print("%-8s %3s %10s %10s %9s %10s" % ("工况","n","水平RMS","垂直RMS","主频","高频能量"))
for k in ("5档","半遮挡"):
    v=agg.get(k,[])
    if not v: continue
    print("%-8s %3d %10.4f %10.4f %9.1f %10.4f" % (k,len(v),
        np.mean([q[0] for q in v]), np.mean([q[1] for q in v]),
        np.mean([q[2] for q in v]), np.mean([q[3] for q in v])))
