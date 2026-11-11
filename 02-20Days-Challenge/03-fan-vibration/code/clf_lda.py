# -*- coding: utf-8 -*-
"""在同一批 8 维特征上比较三种分类器：最近质心 / Fisher-LDA / 类均衡最近质心。留一法。"""
import numpy as np, json
R = r"D:\deepseek工作\proj03\results"
X = np.load(R + r"\X_white.npy"); y5 = np.load(R + r"\y.npy")
fmap = json.load(open(R + r"\file_map.json", encoding="utf-8"))
G5 = ["C1","C2","C3","C4","C5"]
# 批次键：用 orig 前缀（同一批录制）
batch = np.array([m.get("idx", i) for i, m in enumerate(fmap)][:len(y5)])

def lda_fit(X, y, K):
    mu = X.mean(0)
    Sw = np.zeros((X.shape[1], X.shape[1])); Sb = np.zeros_like(Sw)
    for c in range(K):
        Xc = X[y == c]
        if len(Xc) == 0: continue
        mc = Xc.mean(0); d = Xc - mc
        Sw += d.T @ d
        n = len(Xc); dd = (mc - mu).reshape(-1, 1)
        Sb += n * (dd @ dd.T)
    Sw += np.eye(len(Sw)) * 1e-6 * np.trace(Sw)
    w, V = np.linalg.eigh(np.linalg.inv(Sw) @ Sb)
    idx = np.argsort(w)[::-1][:K-1]
    return V[:, idx]

def loo(X, y, K, mode):
    ok = 0; err = []
    for i in range(len(X)):
        tr = np.ones(len(X), bool); tr[i] = False
        Xtr, ytr = X[tr], y[tr]
        if mode == "lda":
            W = lda_fit(Xtr, ytr, K); A, B = Xtr @ W, X[i:i+1] @ W
        else:
            A, B = Xtr, X[i:i+1]
        cs = [A[ytr == c].mean(0) for c in range(K)]
        if mode == "bal":
            cnt = np.array([(ytr == c).sum() for c in range(K)], float)
            d = [np.linalg.norm(B[0]-cs[c]) * (len(ytr)/cnt[c])**0.5 for c in range(K)]
        else:
            d = [np.linalg.norm(B[0]-cs[c]) for c in range(K)]
        p = int(np.argmin(d))
        if p == y[i]: ok += 1
        else: err.append((fmap[i]["orig"], G5[y[i]], G5[p]))
    return ok, err

mu, sd = X.mean(0), X.std(0)+1e-9
Z = (X-mu)/sd
y3 = np.where(y5 < 3, 0, y5-2)

for K, yy, tag in ((5, y5, "五类"), (3, y3, "三类")):
    for mode, nm in (("cen","最近质心(现行)"), ("lda","Fisher-LDA"), ("bal","类均衡质心")):
        ok, err = loo(Z, yy, K, mode)
        print("%s %-14s %3d/%d = %5.1f%%" % (tag, nm, ok, len(Z), 100*ok/len(Z)))
    print()
