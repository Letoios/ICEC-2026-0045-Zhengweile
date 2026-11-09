# -*- coding: utf-8 -*-
"""多窗口投票：把一段切成若干 3 s 窗，逐窗提特征、逐窗判，再投票。"""
import os, json
import numpy as np, audio as A

def hps_f0(p, fr, lo=12.0, hi=120.0, k=8):
    df = fr[1]-fr[0]; best, bestv = None, -1e18
    for i in range(int(lo/df), int(hi/df)):
        f0 = fr[i]; s = 0.0
        for kk in range(1, k+1):
            idx = int(round(kk*f0/df))
            if idx >= len(p): break
            s += (1.0/kk)*np.log(p[idx]+1e-12)
        if s > bestv: bestv, best = s, f0
    return float(best)/(2.0 if best > 55 else 1.0)

def feats_of(x, sr):
    fr, am = A.spectrum(x, sr, n=8192); p = am.mean(axis=0)
    band = (fr>=20)&(fr<=8000); f_, a_ = fr[band], p[band]; tot = a_.sum()+1e-20
    f0 = hps_f0(p, fr); df = fr[1]-fr[0]
    def amp(f):
        i=int(round(f/df)); lo,hi=max(0,i-3),min(len(p),i+4)
        return float(p[lo:hi].max()) if hi>lo else 1e-12
    h=[amp(k*f0) for k in range(1,5)]
    return [f0, float((f_*a_).sum()/tot), float(a_[f_<500].sum()/tot),
            float(a_[(f_>=500)&(f_<2000)].sum()/tot), float(a_[f_>=2000].sum()/tot)] + \
           [q/(h[0]+1e-12) for q in h[1:]]

def windows(x, sr, win=3.0, hop=1.5):
    n, h = int(win*sr), int(hop*sr)
    if len(x) <= n: return [x]
    return [x[i:i+n] for i in range(0, len(x)-n+1, h)]

mapping = json.load(open(r"D:\deepseek工作\proj03\results\file_map.json", encoding="utf-8"))
WAV = r"D:\deepseek工作\proj03\data\wav"
G5 = ["C1","C2","C3","C4","C5"]
Xf, yf, fid = [], [], []
for k, m in enumerate(mapping):
    p = os.path.join(WAV, os.path.basename(m["path"]).replace(".mp3",".wav"))
    x, sr = A.read_wav(p); x = x[int(0.3*sr):-int(0.3*sr)]; x = x - x.mean()
    for w in windows(x, sr):
        Xf.append(feats_of(w, sr)); yf.append(G5.index(m["group"])); fid.append(k)
Xf = np.array(Xf); yf = np.array(yf); fid = np.array(fid)
mu, sd = Xf.mean(0), Xf.std(0)+1e-9
Xs = (Xf-mu)/sd

# 文件级留一：留出的文件所有窗都不参与训练
files = np.unique(fid)
ok5 = ok3 = 0
y3f = np.where(yf < 3, 0, yf-2)
for k in files:
    tr = fid != k; te = fid == k
    for K, yy, cnt in ((5, yf, "5"), (3, y3f, "3")):
        mu_k = np.array([Xs[tr & (yy==c)].mean(0) for c in range(K)])
        votes = []
        for i in np.where(te)[0]:
            d = ((mu_k - Xs[i])**2).sum(1)
            votes.append(int(d.argmin()))
        pred = int(np.bincount(votes, minlength=K).argmax())
        true = int(yy[te][0])
        if cnt == "5": ok5 += (pred == true)
        else: ok3 += (pred == true)
n = len(files)
print("多窗口投票（3 s 窗 / 1.5 s 步，文件级留一）")
print("  五分类 %d/%d = %.1f%%" % (ok5, n, 100*ok5/n))
print("  三分类 %d/%d = %.1f%%" % (ok3, n, 100*ok3/n))
print()
print("（对照：单窗整段特征 五类 66.3%% / 三类 91.6%%）")
np.save(r"D:\deepseek工作\proj03\results\Xwin.npy", Xs)
np.save(r"D:\deepseek工作\proj03\results\ywin.npy", yf)
np.save(r"D:\deepseek工作\proj03\results\fwin.npy", fid)
print("窗数统计：平均每段 %.1f 个窗，共 %d 个" % (len(Xs)/n, len(Xs)))
