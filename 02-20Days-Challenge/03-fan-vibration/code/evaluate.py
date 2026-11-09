# -*- coding: utf-8 -*-
"""最终评估：两套交叉验证口径 × 两种分类粒度，输出 clf_report.json。

口径说明：
- 留一法（LOO）：每次留一段。同一批次的其他段仍在训练集，会高估。
- 分组交叉验证（GroupCV）：每次留一整个批次（同一次录音的连续 5 段）。
  这是诚实口径 —— 模拟「换一次录音环境」。
"""
import csv, json
import numpy as np

FEAT = ["f0", "e_mid", "e_high", "h2", "h3", "h4"]   # 贪心选择后的 6 个
G5 = ["C1", "C2", "C3", "C4", "C5"]
G3 = ["正常", "失衡", "遮挡"]
rows = list(csv.DictReader(open(r"D:\deepseek工作\proj03\results\features.csv", encoding="utf-8-sig")))
X = np.array([[float(r[k]) for k in FEAT] for r in rows])
y5 = np.array([G5.index(r["group"]) for r in rows])
y3 = np.array([0 if r["group"] in ("C1", "C2", "C3") else (1 if r["group"] == "C4" else 2) for r in rows])
num = np.array([int(r["file"].split("_")[1].split(".")[0]) for r in rows])
batch = np.array(["%s_%d" % (r["group"], n // 5) for r, n in zip(rows, num)])


def knn_pred(Xtr, ytr, Xte, K, k=3):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    A_ = (Xtr - mu) / sd; B_ = (Xte - mu) / sd
    out = []
    for b in B_:
        d = ((A_ - b) ** 2).sum(1)
        nn = np.argsort(d)[:k]
        out.append(int(np.bincount(ytr[nn], minlength=K).argmax()))
    return np.array(out)


def loo_conf(y, K):
    conf = np.zeros((K, K), int)
    for i in range(len(y)):
        m = np.ones(len(y), bool); m[i] = False
        conf[y[i], knn_pred(X[m], y[m], X[i:i+1], K)[0]] += 1
    return conf


def group_conf(y, K):
    conf = np.zeros((K, K), int)
    for g in sorted(set(batch)):
        te = batch == g; tr = ~te
        if len(set(y[tr])) < K:
            continue
        p = knn_pred(X[tr], y[tr], X[te], K)
        for t, q in zip(y[te], p):
            conf[t, q] += 1
    return conf


rep = {"features": FEAT, "n": len(rows), "n_batch": len(set(batch))}
for tag, y, K, names in (("five", y5, 5, G5), ("three", y3, 3, G3)):
    c1, c2 = loo_conf(y, K), group_conf(y, K)
    rep[tag] = {
        "names": names,
        "loo_conf": c1.tolist(), "loo_acc": float(np.trace(c1)) / max(1, c1.sum()),
        "group_conf": c2.tolist(), "group_acc": float(np.trace(c2)) / max(1, c2.sum()),
        "group_n": int(c2.sum()),
    }

json.dump(rep, open(r"D:\deepseek工作\proj03\results\clf_report.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)

print("特征：", " + ".join(FEAT))
print("样本 %d 段 / 批次 %d 个\n" % (len(rows), len(set(batch))))
for tag in ("five", "three"):
    r = rep[tag]
    print("%-6s 留一法 %.1f%%   分组交叉验证 %.1f%%（n=%d）" % (
        "五类" if tag == "five" else "三类",
        100 * r["loo_acc"], 100 * r["group_acc"], r["group_n"]))
print()
for tag in ("five", "three"):
    r = rep[tag]; nm = r["names"]; c = np.array(r["group_conf"])
    print("【%s】分组交叉验证混淆矩阵（行=真值 列=预测）" % ("五类" if tag == "five" else "三类"))
    print("        " + "".join("%8s" % x for x in nm))
    for i, lab in enumerate(nm):
        print("%-8s" % lab + "".join("%8d" % v for v in c[i]))
    print()
