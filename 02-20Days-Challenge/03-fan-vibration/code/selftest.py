# -*- coding: utf-8 -*-
"""项目三 · 自检：在没有真实录音之前，先用合成信号把整条流水线跑通。

合成五类「风扇」信号：
  C1 正常·低速   f0=25 Hz，谐波 1/k
  C2 正常·高速   f0=45 Hz
  C3 扇叶失衡    f0 被 fr 调幅 → f0±fr 边带
  C4 风道遮挡    f0 变弱 + 宽带底噪抬高
  C5 轴承异响    f0 + 3.5 kHz 窄带，被 BPFO≈6.3·f0 周期性冲击调制

自检判据：特征表能看出四条物理差别 + 最近质心分类 5/5。
"""
import os
import numpy as np
import audio as A
import features as F

SR = 44100
DUR = 3.0
rng = np.random.default_rng(7)


def fan(f0, amp=0.12, nh=6):
    t = np.arange(int(SR * DUR)) / SR
    s = np.zeros_like(t)
    for k in range(1, nh + 1):
        s += (amp / k) * np.sin(2 * np.pi * k * f0 * t + rng.uniform(0, 6.28))
    return t, s


def c1():
    return fan(25.0)


def c2():
    return fan(45.0)


def c3():
    """失衡：转频 fr 对 f0 做幅度调制，边带比会明显抬高。"""
    t, s = fan(25.0)
    fr = 4.0                                   # 每转一次的摆动
    s = s * (1.0 + 0.45 * np.sin(2 * np.pi * fr * t))
    return t, s


def c4():
    """遮挡：基频被闷住，宽带噪声抬高。"""
    t, s = fan(25.0, amp=0.05)
    s = s + 0.030 * rng.standard_normal(len(t))
    return t, s


def c5():
    """轴承：高频窄带 + 周期性冲击（包络谱会出峰）。"""
    t, s = fan(25.0, amp=0.10)
    bpfo = 6.3 * 25.0
    env = (np.sin(2 * np.pi * bpfo * t) > 0.98).astype(float)
    k = np.ones(int(0.0008 * SR)) / 0.0008        # 短促冲击的包络
    bursts = np.convolve(env, k, mode="same")
    s = s + 0.20 * bursts * np.sin(2 * np.pi * 3500.0 * t)
    return t, s


CASES = [("C1", c1), ("C2", c2), ("C3", c3), ("C4", c4), ("C5", c5)]


def main():
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "_selftest")
    out = os.path.abspath(out)
    os.makedirs(out, exist_ok=True)

    rows = []
    for name, fn in CASES:
        for rep in range(2):                       # 每类两段，模拟重复采集
            t, s = fn()
            s = s + 0.004 * rng.standard_normal(len(s))
            s = s / max(1e-9, np.max(np.abs(s))) * 0.85
            p = os.path.join(out, "%s_%d.wav" % (name, rep + 1))
            A.write_wav(p, s, SR)
            rows.append((name, F.extract(p)))

    print("合成样本 %d 段 → %s\n" % (len(rows), out))
    hdr = ("样本", "f0", "rms", "crest", "kurt", "centroid", "flatness", "sb1", "e_high", "env_crest")
    print("%-8s %7s %7s %7s %8s %9s %9s %7s %8s %10s" % hdr)
    for name, f in rows:
        print("%-8s %7.1f %7.3f %7.1f %8.2f %9.0f %9.4f %7.3f %8.4f %10.2f" % (
            name, f["f0"], f["rms"], f["crest"], f["kurt"],
            f["centroid"], f["flatness"], f["sb1"], f["e_high"], f["env_crest"]))

    # 最近质心（留一法）：只用特征的 z 分数，不调参
    keys = ["f0", "rms", "crest", "kurt", "centroid", "flatness", "sb1", "e_high", "env_crest"]
    X = np.array([[f[k] for k in keys] for _, f in rows], float)
    y = np.array([n for n, _ in rows])
    mu, sd = X.mean(0), X.std(0) + 1e-12
    Z = (X - mu) / sd

    ok = 0
    for i in range(len(rows)):
        m = np.arange(len(rows)) != i
        cent = {c: Z[m][y[m] == c].mean(0) for c in sorted(set(y[m]))}
        d = {c: float(np.linalg.norm(Z[i] - v)) for c, v in cent.items()}
        pred = min(d, key=d.get)
        hit = pred == y[i]
        ok += hit
        if not hit:
            print("  错：%s 判成 %s" % (y[i], pred))
    print("\n最近质心留一法：%d / %d" % (ok, len(rows)))
    print("结论：%s" % ("五类可分，流水线跑通" if ok == len(rows) else "仍有混淆，看上面的错分"))


if __name__ == "__main__":
    main()
