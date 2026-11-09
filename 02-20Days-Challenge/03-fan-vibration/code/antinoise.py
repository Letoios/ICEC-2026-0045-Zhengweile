# -*- coding: utf-8 -*-
"""抗噪：每个 SNR 下重算全部特征，再做留一 kNN，输出准确率曲线。"""
import os, json
import numpy as np, audio as A

FEAT = ["f0","centroid","e_low","e_mid","e_high","h2","h3","h4"]
G5 = ["C1","C2","C3","C4","C5"]
CACHE = r"D:\deepseek工作\proj03\results\antinoise_feats.json"

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

mapping = json.load(open(r"D:\deepseek工作\proj03\results\file_map.json", encoding="utf-8"))
WAV = r"D:\deepseek工作\proj03\data\wav"
SNRS = [None, 30, 20, 15, 10, 5]
rng = np.random.default_rng(0)
buf = {}
for snr in SNRS:
    key = "clean" if snr is None else str(snr)
    if os.path.exists(CACHE):
        old = json.load(open(CACHE, encoding="utf-8"))
        if key in old: buf[key] = old[key]; print("缓存", key); continue
    feats = []
    for i, m in enumerate(mapping):
        w = os.path.join(WAV, os.path.basename(m["path"]).replace(".mp3",".wav"))
        x, sr = A.read_wav(w); x = x[int(0.3*sr):-int(0.3*sr)]; x = x - x.mean()
        if snr is not None:
            ps = (x**2).mean()
            n = rng.normal(size=len(x)); n = n/np.sqrt((n**2).mean())*np.sqrt(ps)/(10**(snr/20.0))
            x = x + n
        feats.append(feats_of(x, sr))
    buf[key] = feats
    json.dump(buf, open(CACHE,"w",encoding="utf-8"))
    print("算完", key, len(feats))

y5 = np.array([G5.index(m["group"]) for m in mapping])
y3 = np.array([0 if g in (0,1,2) else (1 if g==3 else 2) for g in y5])

def loo_knn(Xs, y, K, k=3):
    conf = np.zeros((K,K), int)
    for i in range(len(y)):
        d = ((Xs-Xs[i])**2).sum(1); d[i] = 1e18
        nn = np.argsort(d)[:k]
        conf[y[i], int(np.bincount(y[nn], minlength=K).argmax())] += 1
    return conf

out = {}
print()
print("%-7s %8s %8s" % ("SNR", "五分类", "三分类"))
for snr in SNRS:
    key = "clean" if snr is None else str(snr)
    X = np.array(buf[key], float)
    Xs = (X - X.mean(0))/(X.std(0)+1e-9)
    a5 = np.trace(loo_knn(Xs, y5, 5))/len(y5)
    a3 = np.trace(loo_knn(Xs, y3, 3))/len(y3)
    out[key] = [round(100*a5,1), round(100*a3,1)]
    print("%-7s %7.1f%% %7.1f%%" % ("clean" if snr is None else "%ddB"%snr, 100*a5, 100*a3))
json.dump(out, open(r"D:\deepseek工作\proj03\results\antinoise.json","w",encoding="utf-8"),
          ensure_ascii=False, indent=1)
