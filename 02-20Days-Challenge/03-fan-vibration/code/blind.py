# -*- coding: utf-8 -*-
"""盲测：判一段没见过的录音属于哪一类。用法: blind.py <wav 或 mp3 路径>"""
import os, sys, csv
import numpy as np, audio as A

FEAT = ["f0","centroid","e_low","e_mid","e_high","h2","h3","h4"]
G5 = ["C1 一档","C2 三档","C3 五档","C4 五档+贴胶带","C5 五档+半遮挡"]

def hps_f0(x, sr, lo=12.0, hi=120.0, k=8):
    fr, am = A.spectrum(x, sr, n=65536); p = am.mean(axis=0); df = fr[1]-fr[0]
    best, bestv = None, -1e18
    for i in range(int(lo/df), int(hi/df)):
        f0 = fr[i]; s = 0.0
        for kk in range(1, k+1):
            idx = int(round(kk*f0/df))
            if idx >= len(p): break
            s += (1.0/kk)*np.log(p[idx]+1e-12)
        if s > bestv: bestv, best = s, f0
    return float(best) / (2.0 if best > 55 else 1.0)

def feats_of(x, sr):
    fr, am = A.spectrum(x, sr, n=16384); p = am.mean(axis=0)
    band = (fr>=20)&(fr<=8000); f_, a_ = fr[band], p[band]
    tot = a_.sum()+1e-20
    f0 = hps_f0(x, sr); df = fr[1]-fr[0]
    def amp(f):
        i = int(round(f/df)); lo, hi = max(0,i-3), min(len(p), i+4)
        return float(p[lo:hi].max()) if hi > lo else 1e-12
    h = [amp(k*f0) for k in range(1,5)]
    return [f0, float((f_*a_).sum()/tot),
            float(a_[f_<500].sum()/tot), float(a_[(f_>=500)&(f_<2000)].sum()/tot),
            float(a_[f_>=2000].sum()/tot)] + [x/(h[0]+1e-12) for x in h[1:]]

def main(path):
    rows = list(csv.DictReader(open(r"D:\deepseek工作\proj03\results\features.csv", encoding="utf-8-sig")))
    X = np.array([[float(r[k]) for k in FEAT] for r in rows])
    y = np.array([int(r["group"][1]) - 1 for r in rows])
    mu, sd = X.mean(0), X.std(0) + 1e-9
    Xs = (X - mu) / sd

    if path.lower().endswith(".mp3"):
        import mp3read as M
        tmp = path + ".wav"; M.mp3_to_wav(path, tmp); path = tmp
    x, sr = A.read_wav(path)
    x = x[int(0.3*sr):-int(0.3*sr)]; x = x - x.mean()
    f = np.array(feats_of(x, sr)); fs = (f - mu) / sd

    d = ((Xs - fs)**2).sum(1)
    mu_k = np.array([Xs[y == k].mean(0) for k in range(5)])
    dk = ((mu_k - fs)**2).sum(1)
    order = np.argsort(dk)
    nn = np.argsort(d)[:3]
    pred = int(np.bincount(y[nn], minlength=5).argmax())

    print("文件      : %s" % os.path.basename(path))
    print("基频 f0   : %.1f Hz" % f[0])
    print("谱心      : %.0f Hz" % f[1])
    print("频段占比  : 低频 %.2f / 中频 %.2f / 高频 %.2f" % (f[2], f[3], f[4]))
    print("谐波比    : h2 %.2f  h3 %.2f  h4 %.2f" % (f[5], f[6], f[7]))
    print("判定      : %s" % G5[pred])
    others = [k for k in range(5) if k != pred]
    sec = min(others, key=lambda k: dk[k])
    print("依据      : 离 %s 类心 %.2f，离次近的 %s 类心 %.2f" % (
        G5[pred], dk[pred], G5[sec], dk[sec]))
    print("最近邻    : " + ", ".join("%s(%.2f)" % (G5[y[i]], d[i]) for i in nn))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python blind.py <wav|mp3>"); sys.exit(1)
    main(sys.argv[1])
