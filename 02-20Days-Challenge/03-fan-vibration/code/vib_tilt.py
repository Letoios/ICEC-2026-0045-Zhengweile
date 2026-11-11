# -*- coding: utf-8 -*-
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
print("%-12s %7s %7s %7s %7s %7s" % ("样本","gx","gy","gz","|g|","倾角°"))
for s in S:
    p=os.path.join(ROOT,s,"Raw Data.csv")
    if not os.path.exists(p): continue
    t,x,y,z=load(p); mx,my,mz=x.mean(),y.mean(),z.mean()
    g=np.sqrt(mx**2+my**2+mz**2)
    print("%-12s %7.3f %7.3f %7.3f %7.3f %7.1f" % (s,mx,my,mz,g,np.degrees(np.arccos(min(1,mz/g)))))
