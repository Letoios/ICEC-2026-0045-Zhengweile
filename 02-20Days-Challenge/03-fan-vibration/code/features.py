# -*- coding: utf-8 -*-
"""项目三 · 特征提取（时域 + 频域 + 边带 / 包络）

五类工况的物理差别：
  C1/C2 档位不同     → 基频 f0 不同、总能量不同
  C3 扇叶失衡        → 出现 f0±fr 边带（调幅），边带比升高
  C4 风道遮挡        → 宽带噪声抬高、谱平坦度升高、基频信噪比下降
  C5 轴承异响        → 2–8 kHz 窄带 + 包络谱出周期性冲击
所以特征要能分别指向这四条。
"""
import numpy as np
import audio as A



def estimate_f0(freqs, amp, lo=15.0, hi=120.0, kmax=6, step=0.02):
    """谐波梳估基频：让 k*f0 (k=1..kmax) 尽量都落在强峰上。

    为什么不用 argmax：风扇有叶片通过频率、倍频、结构共振，
    单个最高峰不一定是转频；而且短录音的 FFT 分辨率只有几 Hz，
    argmax 会落在相邻 bin 上，二档三档就分不开了。
    谐波梳同时看 6 个谐波，抗单峰误判，分辨率可到 step（0.02 Hz）。
    """
    if len(amp) == 0:
        return 0.0, 0.0
    cand = np.arange(lo, hi, step)
    sc = np.zeros_like(cand)
    w = np.zeros_like(cand)
    for k in range(1, kmax + 1):
        fk = cand * k
        ok = fk <= freqs[-1]
        sc[ok] += np.interp(fk[ok], freqs, amp) / k      # 高次谐波权重降低
        w[ok] += 1.0 / k
    sc = sc / np.maximum(w, 1e-9)
    j = int(np.argmax(sc))
    return float(cand[j]), float(20 * np.log10(max(sc[j], 1e-12)))


def time_feats(x):
    rms = float(np.sqrt(np.mean(x ** 2)))
    peak = float(np.max(np.abs(x))) if len(x) else 0.0
    crest = peak / rms if rms > 1e-9 else 0.0
    z = (x - x.mean()) / (x.std() + 1e-12)
    skew = float(np.mean(z ** 3))
    kurt = float(np.mean(z ** 4))
    zcr = float(np.mean(np.abs(np.diff(np.signbit(x).astype(np.int8)))))
    return dict(rms=rms, peak=peak, crest=crest, skew=skew, kurt=kurt, zcr=zcr)


def freq_feats(freqs, amp):
    p = amp ** 2 + 1e-20
    tot = float(p.sum())
    cen = float((freqs * p).sum() / tot)
    bw = float(np.sqrt((((freqs - cen) ** 2) * p).sum() / tot))
    cum = np.cumsum(p)
    roll = float(freqs[int(np.searchsorted(cum, 0.85 * cum[-1]))])
    flat = float(np.exp(np.mean(np.log(p + 1e-20))) / (np.mean(p) + 1e-20))
    return dict(centroid=cen, bandwidth=bw, rolloff=roll, flatness=flat)


def sideband_feats(freqs, amp, f0, fr, k=1):
    """边带比：f0±k·fr 处能量 / f0 处能量。失衡会让它明显抬高。"""
    if f0 <= 0:
        return dict(sb1=0.0, sb2=0.0, harm=0.0)
    def at(f, w=3.0):
        return A.band_energy(freqs, amp, max(0.0, f - w), f + w)
    base = at(f0) + 1e-20
    sb1 = (at(f0 - k * fr) + at(f0 + k * fr)) / base
    sb2 = (at(f0 - 2 * k * fr) + at(f0 + 2 * k * fr)) / base
    # 谐波能量占比：2f0..5f0 之和 / f0
    harm = sum(at(m * f0) for m in (2, 3, 4, 5)) / base
    return dict(sb1=float(sb1), sb2=float(sb2), harm=float(harm))


def env_feats(x, sr):
    """包络谱的「冲击性」：最大值 / 中位数（轴承爆点时远大于 1）。"""
    ef, es = A.envelope_spectrum(x, sr)
    if len(es) == 0 or es.max() <= 0:
        return dict(env_crest=0.0, env_peak_hz=0.0)
    return dict(env_crest=float(es.max() / (np.median(es) + 1e-12)),
                env_peak_hz=float(ef[int(np.argmax(es))]))


def extract(path, f0_range=(20.0, 120.0)):
    """一段 WAV → 一个特征字典。f0 先在 20–120 Hz 找（风扇转速 1200–7200 rpm）。"""
    x, sr = A.read_wav(path)
    if len(x) == 0:
        raise ValueError("空文件：" + path)
    # 去掉首尾 0.2 s，避免按键/放下的瞬态
    cut = int(0.2 * sr)
    if len(x) > 3 * cut:
        x = x[cut:-cut]

    tf = time_feats(x)
    # 频谱分辨率 = sr/n。n 取到 65536，0.7 Hz/bin；录音越长越准
    n = 8192
    while n < 65536 and n * 4 <= len(x):
        n *= 2
    freqs1, amp1 = A.spectrum(x, sr, n=n)
    mean_amp = amp1.mean(axis=0) if amp1.shape[0] else np.zeros_like(freqs1)
    ff = freq_feats(freqs1, mean_amp)

    f0, a0 = estimate_f0(freqs1, mean_amp, f0_range[0], f0_range[1])
    sf = sideband_feats(freqs1, mean_amp, f0, f0)   # fr≈f0（单叶片主导时近似）

    # 四个频段的能量占比：低频主体 / 中频 / 高频（遮挡与轴承都看这里）
    tot = float((mean_amp ** 2).sum()) + 1e-20
    e_low = A.band_energy(freqs1, mean_amp, 20, 500) / tot
    e_mid = A.band_energy(freqs1, mean_amp, 500, 2000) / tot
    e_high = A.band_energy(freqs1, mean_amp, 2000, 8000) / tot

    ev = env_feats(x, sr)

    f = dict(file=path, sr=sr, dur=round(len(x) / sr, 2), f0=round(f0, 2), f0_rpm=round(f0 * 60, 0), a0=a0,
             e_low=e_low, e_mid=e_mid, e_high=e_high)
    f.update({k: round(v, 6) for k, v in tf.items()})
    f.update({k: round(v, 4) for k, v in ff.items()})
    f.update({k: round(v, 5) for k, v in sf.items()})
    f.update({k: round(v, 4) for k, v in ev.items()})
    return f


FIELDS = ["file", "dur", "f0", "rms", "crest", "skew", "kurt",
          "centroid", "bandwidth", "flatness", "sb1", "sb2", "harm",
          "e_low", "e_mid", "e_high", "env_crest", "env_peak_hz"]
