# -*- coding: utf-8 -*-
"""五档正常 vs 五档胶带：60-260 Hz 逐峰列出，看 76 Hz 有没有能量。"""
import os, csv
import numpy as np
ROOT = r"D:\deepseek工作\proj03\data\振动"
def load(p):
    t,x,y,z=[],[],[],[]
    with open(p, encoding="utf-8-sig", newline="") as f:
        r=csv.reader(f); next(r)
        for row in r:
            if len(row)<4: continue
            try: t.append(float(row[0])); x.append(float(row[1])); y.append(float(row[2])); z.append(float(row[3]))
            except ValueError: continue
    return np.array(t),np.array(x),np.array(y),np.array(z)
for s in ("5档","5档1","5档2","5档带胶带","5档带胶带1","5档带胶带2"):
    t,x,y,z=load(os.path.join(ROOT,s,"Raw Data.csv"))
    fs=1.0/np.median(np.diff(t)); zd=z-z.mean()
    n=1
    while n<len(zd): n*=2
    Z=np.abs(np.fft.rfft(zd*np.hanning(len(zd)),n)); fr=np.fft.rfftfreq(n,1.0/fs)
    m=(fr>=20)&(fr<=320); f_,z_=fr[m],Z[m]; z_=z_/z_.max()
    # 局部极大
    pk=[]
    for i in range(1,len(z_)-1):
        if z_[i]>z_[i-1] and z_[i]>z_[i+1] and z_[i]>0.10:
            pk.append((f_[i], z_[i]))
    print("%-10s " % s + "  ".join("%.0f(%.2f)" % p for p in pk[:8]))
    for probe in (31.4, 62.8, 76.3, 94.2, 152.6, 228.9):
        i=np.argmin(np.abs(f_-probe))
        print("      %6.1f Hz -> %.3f" % (probe, z_[i]), end="")
    print()
