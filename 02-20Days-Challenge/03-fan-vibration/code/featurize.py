# -*- coding: utf-8 -*-
"""批量提取特征 -> results/features.csv"""
import os, csv, json
import numpy as np, audio as A

def hps_f0(x, sr, lo=12.0, hi=120.0, k=8):
    fr, am = A.spectrum(x, sr, n=65536)
    p = am.mean(axis=0); df = fr[1]-fr[0]
    best, bestv = None, -1e18
    for i in range(int(lo/df), int(hi/df)):
        f0 = fr[i]; s = 0.0
        for kk in range(1, k+1):
            idx = int(round(kk*f0/df))
            if idx >= len(p): break
            s += (1.0/kk)*np.log(p[idx]+1e-12)
        if s > bestv: bestv, best = s, f0
    return float(best) / (2.0 if best > 55 else 1.0)

def harm_ratios(p, fr, f0):
    """h1..h4 相对 h1 的幅度；f0 附近取 ±3 bin 的最大值。"""
    df = fr[1]-fr[0]
    def amp(f):
        i = int(round(f/df)); lo, hi = max(0,i-3), min(len(p), i+4)
        return float(p[lo:hi].max()) if hi > lo else 1e-12
    h = [amp(k*f0) for k in range(1,5)]
    return [x/(h[0]+1e-12) for x in h[1:]]

mapping = json.load(open(r"D:\deepseek工作\proj03\results\file_map.json", encoding="utf-8"))
WAV = r"D:\deepseek工作\proj03\data\wav"
ROWS = []
for m in mapping:
    w = os.path.join(WAV, os.path.basename(m["path"]).replace(".mp3",".wav"))
    x, sr = A.read_wav(w); x = x[int(0.3*sr):-int(0.3*sr)]
    fr, am = A.spectrum(x, sr, n=16384)
    p = am.mean(axis=0)
    band = (fr>=20)&(fr<=8000); f_, a_ = fr[band], p[band]
    tot = a_.sum()+1e-20
    f0 = hps_f0(x, sr)
    h2,h3,h4 = harm_ratios(p, fr, f0)
    rms = float(np.sqrt((x**2).mean()))
    peak = float(np.abs(x).max())
    ROWS.append(dict(file=os.path.basename(m["path"]), group=m["group"], dur=m["dur"],
        f0=round(f0,2), rms=round(rms,5), crest=round(peak/(rms+1e-12),2),
        centroid=round(float((f_*a_).sum()/tot),1),
        e_low=round(float(a_[f_<500].sum()/tot),4),
        e_mid=round(float(a_[(f_>=500)&(f_<2000)].sum()/tot),4),
        e_high=round(float(a_[f_>=2000].sum()/tot),4),
        h2=round(h2,4), h3=round(h3,4), h4=round(h4,4)))
with open(r"D:\deepseek工作\proj03\results\features.csv","w",newline="",encoding="utf-8-sig") as f:
    wtr = csv.DictWriter(f, fieldnames=list(ROWS[0].keys())); wtr.writeheader(); wtr.writerows(ROWS)
print("features.csv  %d 行  %d 列" % (len(ROWS), len(ROWS[0])))
for g in ("C1","C2","C3","C4","C5"):
    s=[r for r in ROWS if r["group"]==g]
    print("  %s n=%2d  f0 %.1f  谱心 %.0f  高频 %.3f  h2 %.2f" % (
        g, len(s), np.median([r["f0"] for r in s]), np.median([r["centroid"] for r in s]),
        np.median([r["e_high"] for r in s]), np.median([r["h2"] for r in s])))
