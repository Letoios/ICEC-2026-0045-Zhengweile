# -*- coding: utf-8 -*-
"""嵌套验证：每个留出批次内部重做一次特征选择，避免「在同一 CV 上挑特征」的乐观偏差。"""
import csv
import io, time
import numpy as np
rows=list(csv.DictReader(open(r"D:\deepseek工作\proj03\results\features.csv",encoding="utf-8-sig")))
ALL=["f0","rms","crest","centroid","e_low","e_mid","e_high","h2","h3","h4"]
Xall=np.array([[float(r[c]) for c in ALL] for r in rows])
y5=np.array([int(r["group"][1])-1 for r in rows]); y3=np.array([0 if v<3 else v-2 for v in y5])
num=np.array([int(r["file"].split("_")[1].split(".")[0]) for r in rows])
batch=np.array(["%s_%d"%(r["group"],n//5) for r,n in zip(rows,num)])
groups=sorted(set(batch)); COL={c:i for i,c in enumerate(ALL)}

def score(cols,K,y,tr,bs):
    """在训练批次 bs 上做分组 CV，返回加权准确率。"""
    X=Xall[:,[COL[c] for c in cols]]; ok=tot=0
    for g in bs:
        te=batch==g; trn=tr&(~te)
        if te.sum()==0 or len(set(y[trn]))<K: continue
        mu,sd=X[trn].mean(0),X[trn].std(0)+1e-9
        A=(X[trn]-mu)/sd
        for i in np.where(te)[0]:
            d=((A-(X[i]-mu)/sd)**2).sum(1); nn=np.argsort(d)[:3]
            p=int(np.bincount(y[np.where(trn)[0][nn]],minlength=K).argmax())
            ok+=int(p==y[i]); tot+=1
    return ok, tot

def greedy(K,y,bs):
    sel=[]; rest=ALL[:]
    for _ in range(6):
        best=None
        for c in rest:
            ok,tot=score(sel+[c],K,y,None,bs) if False else (None,None)
            # 训练侧 CV 用全训练集的批次
            o,t=score_batch(sel+[c],K,y,bs)
            v=o/max(t,1)
            if best is None or v>best[0]: best=(v,c)
        if best is None: break
        sel.append(best[1]); rest.remove(best[1])
    return sel

def score_batch(cols,K,y,bs):
    X=Xall[:,[COL[c] for c in cols]]; ok=tot=0
    for g in bs:
        te=batch==g; trn=np.isin(batch,[b for b in bs if b!=g])
        if te.sum()==0 or len(set(y[trn]))<K: continue
        mu,sd=X[trn].mean(0),X[trn].std(0)+1e-9
        A=(X[trn]-mu)/sd; ytr=y[trn]
        for i in np.where(te)[0]:
            d=((A-(X[i]-mu)/sd)**2).sum(1); nn=np.argsort(d)[:3]
            p=int(np.bincount(ytr[nn],minlength=K).argmax())
            ok+=int(p==y[i]); tot+=1
    return ok,tot

t0=time.time()
for K,y,tag in ((5,y5,"五类"),(3,y3,"三类")):
    ok=tot=0; picks={}
    for g in groups:
        te=batch==g; tr=np.ones(len(y),bool); tr[te]=False
        trbs=[b for b in groups if b!=g]
        if te.sum()==0 or len(set(y[tr]))<K: continue
        sel=greedy(K,y,trbs)
        picks[g]="+".join(sel)
        X=Xall[:,[COL[c] for c in sel]]
        mu,sd=X[tr].mean(0),X[tr].std(0)+1e-9
        A=(X[tr]-mu)/sd; ytr=y[tr]
        for i in np.where(te)[0]:
            d=((A-(X[i]-mu)/sd)**2).sum(1); nn=np.argsort(d)[:3]
            p=int(np.bincount(ytr[nn],minlength=K).argmax())
            ok+=int(p==y[i]); tot+=1
    print("%s 嵌套特征选择（每组独立选）: %d/%d = %.1f%%  用时 %.0fs" % (tag,ok,tot,100.0*ok/tot,time.time()-t0))
    import json
    _f = r"D:\deepseek工作\proj03\results\clf_nested.json"
    try:
        _d = json.load(io.open(_f, encoding="utf-8"))
    except Exception:
        _d = {}
    _d["nested_%dclass" % K] = {"ok": int(ok), "tot": int(tot), "pct": round(100.0 * ok / tot, 1)}
    json.dump(_d, io.open(_f, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    from collections import Counter
    c=Counter(picks.values())
    for k,v in c.most_common(3): print("     选中 %d 次: %s" % (v,k))
