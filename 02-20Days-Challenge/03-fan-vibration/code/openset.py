# -*- coding: utf-8 -*-
"""创新二：开集检测 —— 留一个工况不参与训练，看它能不能被识别成「未知故障」。

做法（每次留出一类）：
1. 用其余 4 类训练；
2. 算每个样本到训练集的 kNN 距离（标准化特征空间里最近 3 个点的平均距离）；
3. 门槛取「训练集自身留一距离的 95 分位」；
4. 被留出那一类里，距离超过门槛的比例 = 拒识率（越高越好）；
   训练集自身被拒的比例 = 误拒率（应接近 5%，是门槛定义决定的）。

为什么要留出：现实里故障是长尾的，「没见过的故障」比「见过的」多。
一个只会五选一的分类器，遇到新故障一定会硬判成某一类，且很自信 —— 这是危险的。
"""
import csv, json
import numpy as np

FEAT = ["f0", "e_mid", "e_high", "h2", "h3", "h4"]
G5 = ["C1", "C2", "C3", "C4", "C5"]

rows = list(csv.DictReader(open(r"D:\deepseek工作\proj03\results\features.csv", encoding="utf-8-sig")))
X = np.array([[float(r[k]) for k in FEAT] for r in rows])
g = np.array([r["group"] for r in rows])

K = 3           # kNN 的 k
PCT = 95        # 门槛分位数


def knn_dist(Xtr, Xte, k=K):
    """每个测试样本到训练集最近 k 个点的平均欧氏距离。"""
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    A_ = (Xtr - mu) / sd
    B_ = (Xte - mu) / sd
    out = []
    for b in B_:
        d = np.sqrt(((A_ - b) ** 2).sum(1))
        out.append(float(np.sort(d)[:k].mean()))
    return np.array(out)


def loo_dist(Xtr, k=K):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    A_ = (Xtr - mu) / sd
    out = []
    for i in range(len(A_)):
        d = np.sqrt(((A_ - A_[i]) ** 2).sum(1))
        d[i] = 1e18
        out.append(float(np.sort(d)[:k].mean()))
    return np.array(out)


res = {"feat": FEAT, "k": K, "pct": PCT, "classes": {}}
print("=" * 64)
print("开集检测：留出一整个工况，看它能不能被认成「未知」")
print("=" * 64)
print("%-8s %8s %8s %8s %8s" % ("留出类", "门槛", "拒识率", "误拒率", "训练样本"))
for c in G5:
    te = g == c
    tr = ~te
    d_tr = loo_dist(X[tr])
    thr = float(np.percentile(d_tr, PCT))
    d_te = knn_dist(X[tr], X[te])
    rej = float((d_te > thr).mean())
    frr = float((d_tr > thr).mean())
    res["classes"][c] = {"thr": thr, "reject": rej, "frr": frr,
                         "n_tr": int(tr.sum()), "n_te": int(te.sum()),
                         "d_te": [round(float(v), 3) for v in d_te],
                         "thr_p": thr}
    print("%-8s %8.2f %7.0f%% %7.0f%% %8d" % (c, thr, 100 * rej, 100 * frr, tr.sum()))

# 对照：如果不用开集，硬判成四类之一，会判成什么
print()
print("对照：硬判（强制归到 4 个已知类之一）时，被留出类会被判成什么：")
for c in G5:
    te = g == c
    tr = ~te
    labels = sorted(set(g[tr]))
    mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-9
    A_ = (X[tr] - mu) / sd
    votes = []
    for b in (X[te] - mu) / sd:
        d = ((A_ - b) ** 2).sum(1)
        nn = np.argsort(d)[:K]
        votes.append(labels[int(np.bincount(
            [labels.index(v) for v in g[tr][nn]], minlength=len(labels)).argmax())])
    uniq, cnt = np.unique(votes, return_counts=True)
    top = ", ".join("%s×%d" % (u, n) for u, n in sorted(zip(uniq, cnt), key=lambda z: -z[1]))
    res["classes"][c]["hard_vote"] = {str(u): int(n) for u, n in zip(uniq, cnt)}
    print("  留出 %-3s → %s" % (c, top))

json.dump(res, open(r"D:\deepseek工作\proj03\results\openset.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print()
print("结果 -> results/openset.json")
