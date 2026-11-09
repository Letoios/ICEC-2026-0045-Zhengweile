# -*- coding: utf-8 -*-
"""抗噪复测：与 featurize.py 完全同一套算法（不同 FFT 长度），分组交叉验证。"""
import os, json, re
import numpy as np
import audio as A

FEAT = ["f0", "e_mid", "e_high", "h2", "h3", "h4"]
G5 = ["C1", "C2", "C3", "C4", "C5"]


def hps_f0(x, sr, lo=12.0, hi=120.0, k=8):
    fr, am = A.spectrum(x, sr, n=65536)
    p = am.mean(axis=0); df = fr[1] - fr[0]
    best, bestv = None, -1e18
    for i in range(int(lo / df), int(hi / df)):
        f0 = fr[i]; s = 0.0
        for kk in range(1, k + 1):
            idx = int(round(kk * f0 / df))
            if idx >= len(p): break
            s += (1.0 / kk) * np.log(p[idx] + 1e-12)
        if s > bestv: bestv, best = s, f0
    return float(best) / (2.0 if best > 55 else 1.0)


def harm(p, fr, f0):
    df = fr[1] - fr[0]
    def amp(f):
        i = int(round(f / df)); lo, hi = max(0, i - 3), min(len(p), i + 4)
        return float(p[lo:hi].max()) if hi > lo else 1e-12
    h = [amp(k * f0) for k in range(1, 5)]
    return [v / (h[0] + 1e-12) for v in h[1:]]


def feats(x, sr):
    fr, am = A.spectrum(x, sr, n=16384); p = am.mean(axis=0)
    band = (fr >= 20) & (fr <= 8000); f_, a_ = fr[band], p[band]; tot = a_.sum() + 1e-20
    f0 = hps_f0(x, sr)
    h2, h3, h4 = harm(p, fr, f0)
    return [f0, float(a_[(f_ >= 500) & (f_ < 2000)].sum() / tot),
            float(a_[f_ >= 2000].sum() / tot), h2, h3, h4]


MP = json.load(open(r"D:\deepseek工作\proj03\results\file_map.json", encoding="utf-8"))
WAV = r"D:\deepseek工作\proj03\data\wav"


def build(snr, seed=7):
    X, y, b = [], [], []
    rng = np.random.default_rng(seed)
    for m in MP:
        fn = os.path.basename(m["path"])
        w = os.path.join(WAV, fn.replace(".mp3", ".wav"))
        x, sr = A.read_wav(w); x = x[int(0.3 * sr):-int(0.3 * sr)]
        if snr is not None:
            nz = rng.normal(0, 1, len(x))
            x = x + nz / (np.std(nz) + 1e-12) * (np.sqrt(np.mean(x ** 2)) / (10 ** (snr / 20.0)))
        X.append(feats(x, sr)); y.append(G5.index(m["group"]))
        i = int(re.search(r"_(\d+)\.", fn).group(1))
        b.append("%s_%d" % (m["group"], i // 5))
    return np.array(X), np.array(y), np.array(b)


def knn(Xtr, ytr, Xte, K, k=3):
    mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
    A_ = (Xtr - mu) / sd; B_ = (Xte - mu) / sd
    out = []
    for q in B_:
        d = ((A_ - q) ** 2).sum(1); nn = np.argsort(d)[:k]
        out.append(int(np.bincount(ytr[nn], minlength=K).argmax()))
    return np.array(out)


res = {}
for snr in (None, 30, 20, 15, 10, 5):
    X, y5, b = build(snr)
    y3 = np.array([0 if v < 3 else v - 2 for v in y5])
    row = []
    for y, K in ((y5, 5), (y3, 3)):
        ok = tot = 0
        for g in sorted(set(b)):
            te = b == g; tr = ~te
            if len(set(y[tr])) < K: continue
            p = knn(X[tr], y[tr], X[te], K)
            ok += int((p == y[te]).sum()); tot += int(te.sum())
        row.append(round(100.0 * ok / max(1, tot), 1))
    res["clean" if snr is None else str(snr)] = row
    print("算完 %-5s  五类 %.1f%%  三类 %.1f%%" % ("clean" if snr is None else snr, row[0], row[1]), flush=True)

json.dump(res, open(r"D:\deepseek工作\proj03\results\antinoise.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=2)
print("saved")
