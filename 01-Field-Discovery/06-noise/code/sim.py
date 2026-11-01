# -*- coding: utf-8 -*-
"""课题06 光效逻辑离线回放仿真

把 15 段真实声级序列逐秒灌进《光效逻辑设计》里的状态机，
看灯到底会怎么亮。顺便做参数扫描，回答「3 s 确认 / 2 dB 回差凭什么是这个数」。

输出：
  build/sim_runs.json       每段的状态时间线、切换次数、各态驻留
  build/sim_sweep.json      参数扫描矩阵
"""
import json
import math
import os

BASE = os.path.dirname(os.path.abspath(__file__))
STATS = os.path.join(BASE, "build", "stats.json")
DATA = os.path.join(BASE, "deliver", "data")

CONFIRM_S = 3.0
RELEASE_DB = 1.0
HOLD_S = 2.0
MIN_DWELL_S = 10.0
SP_LMAX = 85.0

EDGES = [(-1e9, -10.0), (-10.0, 0.0), (0.0, 5.0), (5.0, 10.0), (10.0, 1e9)]
NAMES = ["S0", "S1", "S2", "S3", "S4"]


def grade(delta):
    for i, (lo, hi) in enumerate(EDGES):
        if lo < delta <= hi:
            return i
    return 0


def read_db(path):
    vals = []
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for i, line in enumerate(f):
            if i == 0:
                continue
            parts = line.strip().split(",")
            if len(parts) < 2:
                continue
            try:
                v = float(parts[1])
            except ValueError:
                continue
            if v > 0:
                vals.append(v)
    return vals


def simulate(vals, fs, limit, confirm_s=CONFIRM_S, release_db=RELEASE_DB,
             hold_s=HOLD_S, min_dwell=MIN_DWELL_S, sp_lmax=SP_LMAX):
    n = max(1, int(round(fs)))
    frames, peaks = [], []
    for i in range(0, len(vals) - n + 1, n):
        seg = vals[i:i + n]
        frames.append(10 * math.log10(sum(10 ** (v / 10.0) for v in seg) / len(seg)))
        peaks.append(max(seg))

    states, switches, dwell, sp_hits = [], 0, [], 0
    cur, since = 0, 0.0
    cand, cand_run, low_run = None, 0, 0
    for f, pk in zip(frames, peaks):
        d = f - limit
        g = grade(d)
        if pk >= sp_lmax:
            sp_hits += 1
        if g > cur:
            # 对称回差：升档必须越过「边界 + RELEASE_DB」，与降档的「边界 − RELEASE_DB」对称。
            # 只写 d > 边界（单边）会让平衡点整体下移，出现「表判中度、灯停轻度」。
            if d <= EDGES[cur][1] + release_db:
                cand, cand_run = None, 0
            elif cand == g:
                cand_run += 1
            else:
                cand, cand_run = g, 1
            if cand_run >= confirm_s:
                cur, since, cand, cand_run, low_run = g, 0, None, 0, 0
                switches += 1
        else:
            cand, cand_run = None, 0
        if g < cur:
            lo, _ = EDGES[cur]
            low_run = low_run + 1 if d < lo - release_db else 0
            if low_run >= hold_s and since >= min_dwell:
                cur, since, low_run = g, 0, 0
                switches += 1
        else:
            low_run = 0
        states.append(cur)
        since += 1
        if len(dwell) <= cur:
            dwell.extend([0] * (cur + 1 - len(dwell)))
        dwell[cur] += 1
    return states, switches, dwell, sp_hits, [round(f - limit, 1) for f in frames]


def load_index():
    stats = json.load(open(STATS, encoding="utf-8"))
    idx = []
    for d in sorted(os.listdir(DATA)):
        if not d.startswith("S"):
            continue
        sid, per, loc = d.split("_")
        rec = next(r for r in stats if r["per"] == per and r["loc"] == loc)
        vals = read_db(os.path.join(DATA, d, "Amplitudes.csv"))
        fs = rec["n"] / rec["dur"]
        idx.append({"sid": sid, "dir": d, "per": per, "loc": loc,
                    "limit": rec["limit"], "leq": rec["leq"],
                    "peak": rec["peak"], "fs": fs, "vals": vals})
    return idx


def main():
    idx = load_index()
    runs = []
    for r in idx:
        states, sw, dwell, sp, deltas = simulate(r["vals"], r["fs"], r["limit"])
        runs.append({"sid": r["sid"], "site": r["loc"], "period": r["per"],
                     "limit": r["limit"], "leq": r["leq"], "peak": r["peak"],
                     "fs": round(r["fs"], 2), "seconds": len(states),
                     "states": states, "switches": sw, "dwell": dwell,
                     "sp_hits": sp, "deltas": deltas})
        print("%s %-6s %-2s fs %.2f  限值 %2d  Leq %5.1f  切换 %2d 次  %s"
              % (r["sid"], r["loc"], r["per"], r["fs"], r["limit"], r["leq"], sw,
                 " ".join("%s:%ds" % (NAMES[i], v) for i, v in enumerate(dwell))))

    sweep = []
    for confirm in (1.0, 2.0, 3.0, 5.0):
        for rel in (0.0, 1.0, 2.0, 3.0):
            tot = 0
            for r in idx:
                _, sw, _, _, _ = simulate(r["vals"], r["fs"], r["limit"],
                                       confirm_s=confirm, release_db=rel)
                tot += sw
            sweep.append({"confirm": confirm, "release": rel, "switches": tot})
            print("confirm %.0fs  release %.0fdB  → 总切换 %3d" % (confirm, rel, tot))

    json.dump(runs, open(os.path.join(BASE, "build", "sim_runs.json"), "w",
                         encoding="utf-8"), ensure_ascii=False)
    json.dump(sweep, open(os.path.join(BASE, "build", "sim_sweep.json"), "w",
                          encoding="utf-8"), ensure_ascii=False)
    print("\nsaved sim_runs.json / sim_sweep.json")


if __name__ == "__main__":
    main()
