# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import audio as A
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



