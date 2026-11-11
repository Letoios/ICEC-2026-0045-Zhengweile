# -*- coding: utf-8 -*-
import os, csv
import numpy as np
ROOT = r"D:\deepseek工作\proj03\data\振动"
GROUPS = [("1档", ["1档","1档1","1档2"]), ("3档", ["3档","3档1","3档2"]), ("5档", ["5档","5档1","5档2"])]

def load(p):
    t,x,y,z=[],[],[],[]
    with open(p, encoding="utf-8-sig", newline="") as f:
        r=csv.reader(f); next(r)
        for row in r:
            if len(row)<4: continue
            try: t.append(float(row[0])); x.append(float(row[1])); y.append(float(row[2])); z.append(float(row[3]))
            except ValueError: continue
    return np.array(t),np.array(x),np.array(y),np.array(z)

def peaks(zd, fs, k=3):
    n=1
    while n < len(zd): n*=2
    w=np.hanning(len(zd)); Z=np.abs(np.fft.rfft(zd*w,n)); fr=np.fft.rfftfreq(n,1.0/fs)
    m=(fr>=15)&(fr<=500); f_,z_=fr[m],Z[m]
    idx=np.argsort(z_)[::-1]
    out=[]
    for i in idx:
        if all(abs(f_[i]-q)>8 for q,_ in out):
            out.append((f_[i], z_[i]))
        if len(out)>=k: break
    return out

print("%-6s %7s %8s %8s %8s   主峰（Hz, 相对幅度）" % ("样本","时长s","axRMS","ayRMS","azRMS"))
agg={}
for name, subs in GROUPS:
    for s in subs:
        p=os.path.join(ROOT,s,"Raw Data.csv")
        if not os.path.exists(p): continue
        t,x,y,z=load(p); fs=1.0/np.median(np.diff(t))
        xd,yd,zd=x-x.mean(),y-y.mean(),z-z.mean()
        pk=peaks(zd,fs)
        top=pk[0][1] if pk else 1.0
        print("%-6s %7.1f %8.4f %8.4f %8.4f   %s" % (s, t[-1]-t[0], xd.std(), yd.std(), zd.std(),
              "  ".join("%.1f (%.2f)" % (f, a/top) for f,a in pk)))
        agg.setdefault(name,[]).append((xd.std(), yd.std(), zd.std(), pk[0][0]))
print()
print("%-6s %3s %10s %9s %9s %10s" % ("档位","n","水平RMS","垂直RMS","主频Hz","折算rpm"))
for name,_ in GROUPS:
    v=agg.get(name,[])
    if not v: continue
    h=np.mean([np.hypot(q[0],q[1]) for q in v]); zz=np.mean([q[2] for q in v]); f=np.mean([q[3] for q in v])
    print("%-6s %3d %10.4f %9.4f %9.1f %10.0f" % (name,len(v),h,zz,f,f*60))
