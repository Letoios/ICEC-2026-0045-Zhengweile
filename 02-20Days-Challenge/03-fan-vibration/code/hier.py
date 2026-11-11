# -*- coding: utf-8 -*-
"""分层判定（正确版）。"""
import csv
import numpy as np
rows=list(csv.DictReader(open(r"D:\deepseek工作\proj03\results\features.csv",encoding="utf-8-sig")))
COLS=["f0","e_mid","e_high","h2","h3","h4"]
X=np.array([[float(r[c]) for c in COLS] for r in rows])
y5=np.array([int(r["group"][1])-1 for r in rows])
num=np.array([int(r["file"].split("_")[1].split(".")[0]) for r in rows])
batch=np.array(["%s_%d"%(r["group"],n//5) for r,n in zip(rows,num)])

def cv(sub_idx, y, K, k=3):
    sub_idx=np.asarray(sub_idx); y=np.asarray(y)
    ok=tot=0; det=[]
    for g in sorted(set(batch[sub_idx])):
        pos=np.arange(len(sub_idx))
        ing=batch[sub_idx]==g; trn=~ing
        if ing.sum()==0 or len(set(y[trn]))<K: continue
        Gi=sub_idx[trn]
        mu,sd=X[Gi].mean(0),X[Gi].std(0)+1e-9
        A=(X[Gi]-mu)/sd; ytr=y[trn]
        for j in np.where(ing)[0]:
            b=(X[sub_idx[j]]-mu)/sd
            d=((A-b)**2).sum(1); nn=np.argsort(d)[:k]
            p=int(np.bincount(ytr[nn],minlength=K).argmax())
            ok+=int(p==y[j]); tot+=1
            if p!=y[j]: det.append((rows[sub_idx[j]]["file"],int(y[j]),p))
    return ok,tot,det

all_idx=np.arange(98)
o,t,_=cv(all_idx, np.where(y5<3,0,1), 2)
print("① 有没有故障（正常 vs 故障）    %d/%d = %.1f%%"%(o,t,100*o/t))
o,t,_=cv(all_idx, y5, 5)
print("④ 直接五分类（对照）            %d/%d = %.1f%%"%(o,t,100*o/t))
o,t,d=cv(all_idx, np.where(y5<3,0,y5-2), 3)
print("   直接三分类（对照）           %d/%d = %.1f%%"%(o,t,100*o/t))

fi=np.where(np.isin(y5,[3,4]))[0]
o,t,d=cv(fi, y5[fi]-3, 2)
print("② 故障里是哪一种（胶带/遮挡）  %d/%d = %.1f%%"%(o,t,100*o/t))
for x in d: print("      错:",x)

gi=np.where(np.isin(y5,[0,1,2]))[0]
o,t,d=cv(gi, y5[gi], 3)
print("③ 正常里是哪一档（1/3/5 档）  %d/%d = %.1f%%"%(o,t,100*o/t))
for x in d[:5]: print("     错:",x)


# ---- 落盘（供文档复核）----
import io, json
_res = {}
_a = np.arange(98)
o, t, _ = cv(_a, np.where(y5 < 3, 0, 1), 2)
_res["layer1_has_fault"] = {"ok": int(o), "tot": int(t), "pct": round(100.0 * o / t, 1)}
o, t, _ = cv(_a, y5, 5)
_res["direct_5class"] = {"ok": int(o), "tot": int(t), "pct": round(100.0 * o / t, 1)}
o, t, _ = cv(_a, np.where(y5 < 3, 0, y5 - 2), 3)
_res["direct_3class"] = {"ok": int(o), "tot": int(t), "pct": round(100.0 * o / t, 1)}
_fi = np.where(np.isin(y5, [3, 4]))[0]
o, t, _ = cv(_fi, y5[_fi] - 3, 2)
_res["layer2_which_fault"] = {"ok": int(o), "tot": int(t), "pct": round(100.0 * o / t, 1)}
_gi = np.where(np.isin(y5, [0, 1, 2]))[0]
o, t, _ = cv(_gi, y5[_gi], 3)
_res["layer3_which_gear"] = {"ok": int(o), "tot": int(t), "pct": round(100.0 * o / t, 1)}
_res["n_total"] = 98
json.dump(_res, io.open(r"D:\deepseek工作\proj03\results\hier.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("saved results/hier.json")
