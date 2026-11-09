# -*- coding: utf-8 -*-
"""谱白化版特征：先用宽带平滑谱做分母，抹掉整体倾斜，留下峰结构。"""
import os, json, csv
import numpy as np, audio as A

def smooth_baseline(p, k=161):
    """滑动中值 = 宽带包络（比谐波宽得多）。"""
    from numpy.lib.stride_tricks import sliding_window_view
    pad = k // 2
    q = np.pad(p, pad, mode="edge")
    w = sliding_window_view(q, k)
    return np.median(w, axis=1)

def hps_f0(p, fr, lo=12.0, hi=120.0, k=8):
    df = fr[1]-fr[0]
    best, bestv = None, -1e18
    for i in range(int(lo/df), int(hi/df)):
        f0 = fr[i]; s = 0.0
        for kk in range(1, k+1):
            idx = int(round(kk*f0/df))
            if idx >= len(p): break
            s += (1.0/kk)*np.log(p[idx]+1e-12)
        if s > bestv: bestv, best = s, f0
    return float(best) / (2.0 if best > 55 else 1.0)

def feats(path):
    x, sr = A.read_wav(path) if path.lower().endswith(".wav") else (None, None)
    x = x[int(0.3*sr):-int(0.3*sr)]; x = x - x.mean()
    fr, am = A.spectrum(x, sr, n=16384); p = am.mean(axis=0)
    w = p / (smooth_baseline(p) + 1e-12)          # 白化
    band = (fr>=20)&(fr<=8000)
    f_, w_ = fr[band], w[band]
    tot = w_.sum()+1e-20
    f0 = hps_f0(p, fr); df = fr[1]-fr[0]
    def amp(f):
        i = int(round(f/df)); lo, hi = max(0,i-3), min(len(p), i+4)
        return float(w[lo:hi].max()) if hi > lo else 1e-12
    h = [amp(k*f0) for k in range(1,5)]
    pf = p[band]; ptot = pf.sum()+1e-20
    return [f0, float((f_*w_).sum()/tot),
            float(w_[f_<500].sum()/tot), float(w_[(f_>=500)&(f_<2000)].sum()/tot),
            float(w_[f_>=2000].sum()/tot)] + [x/(h[0]+1e-12) for x in h[1:]]

mapping = json.load(open(r"D:\deepseek工作\proj03\results\file_map.json", encoding="utf-8"))
WAV = r"D:\deepseek工作\proj03\data\wav"
X, y = [], []
for m in mapping:
    X.append(feats(os.path.join(WAV, os.path.basename(m["path"]).replace(".mp3",".wav"))))
    y.append(int(m["group"][1])-1)
X = np.array(X); y = np.array(y)
np.save(r"D:\deepseek工作\proj03\results\X_white.npy", X)
np.save(r"D:\deepseek工作\proj03\results\y.npy", y)

mu, sd = X.mean(0), X.std(0)+1e-9
Xs = (X-mu)/sd
def loo(Xs, y, K, k=3):
    conf = np.zeros((K,K), int)
    for i in range(len(y)):
        d = ((Xs-Xs[i])**2).sum(1); d[i]=1e18
        nn = np.argsort(d)[:k]
        conf[y[i], int(np.bincount(y[nn], minlength=K).argmax())] += 1
    return conf
c5 = loo(Xs, y, 5); y3 = np.array([0 if v<3 else v-2 for v in y])
c3 = loo(Xs, y3, 3)
print("白化特征  五分类 LOO %.1f%%   三分类 LOO %.1f%%" % (100*np.trace(c5)/len(y), 100*np.trace(c3)/len(y)))

print()
print("五段盲测（白化特征）：")
names = ["C1 一档","C2 三档","C3 五档","C4 贴胶带","C5 半遮挡"]
truth = {1:"C4",2:"C2",3:"C1",4:"C5",5:"C3"}
for n in range(1,6):
    f = np.array(feats(r"D:\deepseek工作\proj03\data\blind\b%d.wav" % n))
    fs = (f-mu)/sd
    d = ((Xs-fs)**2).sum(1)
    nn = np.argsort(d)[:3]
    pred = int(np.bincount(y[nn], minlength=5).argmax())
    ok = "✓" if truth[n][0] == "C%d" % (pred+1) else "✗"
    print("  b%d  f0 %5.1f  谱心 %4.0f  判 %-8s 真值 %s  %s" % (
        n, f[0], f[1], names[pred], truth[n], ok))
