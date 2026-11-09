# -*- coding: utf-8 -*-
"""项目三 · 音频与频谱基础库（只依赖 numpy + 标准库 wave）

为什么不用 soundfile / librosa：
  本机没有 pip 安装权限，且 /wav 是未压缩 PCM，标准库 `wave` 足够。
  所有算法自己写，正好满足「时域/频域特征提取代码」这一交付项。

约定：
  - 读进来统一成 float64，范围 [-1, 1)，单声道
  - 分帧默认 2048 点、汉宁窗、50% 重叠
"""
import os
import wave
import numpy as np


# ---------------------------------------------------------------- 读 WAV
def read_wav(path):
    """读 PCM WAV → (samples float64, sample_rate)。多声道自动混成单声道。"""
    with wave.open(path, "rb") as w:
        nch = w.getnchannels()
        sw = w.getsampwidth()
        sr = w.getframerate()
        n = w.getnframes()
        raw = w.readframes(n)

    if sw == 2:
        x = np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
    elif sw == 3:
        b = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 3)
        v = (b[:, 0].astype(np.int32)
             | (b[:, 1].astype(np.int32) << 8)
             | (b[:, 2].astype(np.int32) << 16))
        v = np.where(v >= 1 << 23, v - (1 << 24), v)
        x = v.astype(np.float64) / float(1 << 23)
    elif sw == 4:
        x = np.frombuffer(raw, dtype="<i4").astype(np.float64) / float(1 << 31)
    elif sw == 1:
        x = (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128.0) / 128.0
    else:
        raise ValueError("不支持的位深：%d 字节" % sw)

    if nch > 1:
        x = x.reshape(-1, nch).mean(axis=1)
    return x, sr


def write_wav(path, x, sr):
    """把 float64 写成 16 bit 单声道 WAV（自检与导出用）。"""
    y = np.clip(x, -1.0, 1.0)
    pcm = (y * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


# ---------------------------------------------------------------- 分帧 / 谱
def frame(x, n=2048, hop=None):
    """切成 (帧数, n) 的二维数组，尾部不足的丢掉。"""
    hop = hop or n // 2
    if len(x) < n:
        return np.zeros((0, n))
    k = 1 + (len(x) - n) // hop
    idx = np.arange(n)[None, :] + hop * np.arange(k)[:, None]
    return x[idx]


def hann(n):
    return 0.5 - 0.5 * np.cos(2.0 * np.pi * np.arange(n) / (n - 1))


def spectrum(x, sr, n=2048, hop=None):
    """返回 (频率轴 freqs[0..n/2], 单边幅度谱矩阵 amps[帧, n/2+1])。"""
    fr = frame(x, n, hop)
    if fr.shape[0] == 0:
        return np.zeros(n // 2 + 1), np.zeros((0, n // 2 + 1))
    w = hann(n)
    win = fr * w[None, :]
    spec = np.fft.rfft(win, axis=1)
    amp = np.abs(spec) * 2.0 / w.sum()          # 单边幅度谱，正弦峰值≈真实幅值
    freqs = np.fft.rfftfreq(n, 1.0 / sr)
    return freqs, amp


def welch(x, sr, n=4096):
    """平均功率谱（各帧幅度谱平方的均值），用于画稳态谱。"""
    freqs, amp = spectrum(x, sr, n=n, hop=n // 2)
    if amp.shape[0] == 0:
        return freqs, np.zeros_like(freqs)
    return freqs, (amp ** 2).mean(axis=0)


def envelope_spectrum(x, sr, band=(1500.0, 8000.0), n=2048):
    """包络谱：带通 → 整流 → 去直流 → FFT。轴承类故障在包络谱上出特征频率。"""
    freqs, amp = spectrum(x, sr, n=n, hop=n // 4)
    if amp.shape[0] == 0:
        return np.zeros(512), np.zeros(512)
    sel = (freqs >= band[0]) & (freqs <= band[1])
    # 反变换太重，这里用「带内能量随时间的起伏」当包络（复数谱求和后取模）
    env = np.abs((amp[:, sel] * np.exp(1j * np.zeros(int(sel.sum())))).sum(axis=1))
    env = env - env.mean()
    if len(env) < 8:
        return np.zeros(8), np.zeros(8)
    w = hann(len(env))
    spec = np.abs(np.fft.rfft(env * w))
    ef = np.fft.rfftfreq(len(env), 1.0 / (sr / (n // 4)))
    return ef, spec


# ---------------------------------------------------------------- 小工具
def db(x):
    return 20.0 * np.log10(np.maximum(np.asarray(x, float), 1e-12))


def band_energy(freqs, amp, lo, hi):
    sel = (freqs >= lo) & (freqs < hi)
    if not sel.any():
        return 0.0
    return float(np.sum(amp[sel] ** 2))


def find_peak(freqs, amp, lo=20.0, hi=500.0):
    """在 [lo, hi] 内找最强峰，返回 (频率, 幅度)。风扇基频就在这一段。"""
    sel = (freqs >= lo) & (freqs <= hi)
    if not sel.any():
        return 0.0, 0.0
    i = int(np.argmax(amp[sel]))
    return float(freqs[sel][i]), float(amp[sel][i])


def list_wavs(folder):
    out = []
    for r, _, fs in os.walk(folder):
        for f in fs:
            if f.lower().endswith(".wav"):
                out.append(os.path.join(r, f))
    return sorted(out)
