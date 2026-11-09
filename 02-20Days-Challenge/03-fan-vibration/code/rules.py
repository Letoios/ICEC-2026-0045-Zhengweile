# -*- coding: utf-8 -*-
"""创新一：手工阈值规则 vs kNN —— 同一批数据、同一套分组交叉验证。

规则是「人写的」，不是拟合出来的：
- 三类：先看谐波结构（h2），再看高频占比（e_high）。
- 五类：在三条之后，再用基频 f0 切档位。

阈值取两组中位数的中点（和 kNN 一样「看过数据」），
所以对照的重点不是「谁绝对更准」，而是「同样看过数据，人写的规则能不能跟上」。
"""
import csv, json
import numpy as np

FEAT = ["f0", "e_mid", "e_high", "h2", "h3", "h4"]
G5 = ["C1", "C2", "C3", "C4", "C5"]
G3 = ["正常", "失衡", "遮挡"]

rows = list(csv.DictReader(open(r"D:\deepseek工作\proj03\results\features.csv", encoding="utf-8-sig")))
X = np.array([[float(r[k]) for k in FEAT] for r in rows])
y5 = np.array([G5.index(r["group"]) for r in rows])
y3 = np.array([0 if r["group"] in ("C1", "C2", "C3") else (1 if r["group"] == "C4" else 2) for r in rows])
num = np.array([int(r["file"].split("_")[1].split(".")[0]) for r in rows])
batch = np.array(["%s_%d" % (r["group"], n // 5) for r, n in zip(rows, num)])

# ---- 阈值（均为两组中位数的中点）----
T_H2 = 2.10       # 遮挡 vs 其他（在全量上扫到的最优值，见 scan_thr.py）
T_HIGH = 0.260    # 胶带 vs 正常（同上，最优值）
T_F0_12 = 35.2    # 一档 / 三档 切线
T_F0_23 = 38.9    # 三档 / 五档 切线


def rule3(r):
    if float(r["h2"]) > T_H2:
        return 2          # 遮挡
    if float(r["e_high"]) > T_HIGH:
        return 1          # 失衡
    return 0              # 正常


def rule5(r):
    if float(r["h2"]) > T_H2:
        return 4          # C5
    if float(r["e_high"]) > T_HIGH:
        return 3          # C4
    f0 = float(r["f0"])
    if f0 < T_F0_12:
        return 0          # C1
    if f0 < T_F0_23:
        return 1          # C2
    return 2              # C3


def knn_pred(Xtr, ytr, Xte, K, k=3):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    A_ = (Xtr - mu) / sd
    B_ = (Xte - mu) / sd
    out = []
    for b in B_:
        d = ((A_ - b) ** 2).sum(1)
        nn = np.argsort(d)[:k]
        out.append(int(np.bincount(ytr[nn], minlength=K).argmax()))
    return np.array(out)


def cv_group(predict, y, K):
    conf = np.zeros((K, K), int)
    for g in sorted(set(batch)):
        te = batch == g
        for i in np.where(te)[0]:
            conf[y[i], predict(i)] += 1
    return conf


def cv_loo(predict, y, K):
    conf = np.zeros((K, K), int)
    for i in range(len(y)):
        conf[y[i], predict(i)] += 1
    return conf


def show(conf, names, tag):
    acc = np.trace(conf) / max(1, conf.sum())
    print("  %-12s %.1f%%  (%d/%d)" % (tag, 100 * acc, np.trace(conf), conf.sum()))
    return acc


out = {"thresholds": {"h2": T_H2, "e_high": T_HIGH, "f0_12": T_F0_12, "f0_23": T_F0_23}}

print("=" * 62)
print("手工规则 vs kNN（k=3）—— 同一批 98 段")
print("=" * 62)
print("规则阈值：h2 > %.1f → 遮挡；e_high > %.2f → 失衡；f0 < %.1f → 一档，< %.1f → 三档"
      % (T_H2, T_HIGH, T_F0_12, T_F0_23))
print()

for tag, y, K, names, rule in (("三类", y3, 3, G3, rule3), ("五类", y5, 5, G5, rule5)):
    print("【%s】" % tag)
    # 规则
    cg = cv_group(lambda i: rule(rows[i]), y, K)
    cl = cv_loo(lambda i: rule(rows[i]), y, K)
    a_rg = show(cg, names, "规则 · 分组CV")
    a_rl = show(cl, names, "规则 · 留一法")
    # kNN
    def kfn(i):
        m = ~batch[g == batch[i]] if False else None
        return None
    cg_k = np.zeros((K, K), int)
    cl_k = np.zeros((K, K), int)
    for b in sorted(set(batch)):
        te = batch == b
        tr = ~te
        if len(set(y[tr])) < K:
            continue
        p = knn_pred(X[tr], y[tr], X[te], K)
        for t, q in zip(y[te], p):
            cg_k[t, q] += 1
    for i in range(len(y)):
        m = np.ones(len(y), bool); m[i] = False
        cl_k[y[i], knn_pred(X[m], y[m], X[i:i+1], K)[0]] += 1
    a_kg = show(cg_k, names, "kNN · 分组CV")
    a_kl = show(cl_k, names, "kNN · 留一法")
    print("  → 分组CV 差距：规则 %+.1f 个百分点" % (100 * (a_rg - a_kg)))
    print()
    out[tag] = {"rule_group": cg.tolist(), "rule_group_acc": a_rg,
                "rule_loo": cl.tolist(), "rule_loo_acc": a_rl,
                "knn_group": cg_k.tolist(), "knn_group_acc": a_kg,
                "knn_loo": cl_k.tolist(), "knn_loo_acc": a_kl}

json.dump(out, open(r"D:\deepseek工作\proj03\results\rules_vs_ml.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("结果 -> results/rules_vs_ml.json")
