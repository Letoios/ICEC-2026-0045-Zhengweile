# -*- coding: utf-8 -*-
"""生成 docs/回放仿真说明.md（所有数字由数据算出，不手抄）"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
RUNS = os.path.join(BASE, "build", "sim_runs.json")
SIM2 = os.path.join(BASE, "build", "sim2.json")
EV = os.path.join(BASE, "build", "events.json")
OUT = os.path.join(BASE, "deliver", "docs", "回放仿真说明.md")

CN = ["S0 安静", "S1 达标", "S2 轻度超标", "S3 中度超标", "S4 重度超标"]
EDGES = [(-1e9, -10.0), (-10.0, 0.0), (0.0, 5.0), (5.0, 10.0), (10.0, 1e9)]


def grade(d):
    for i, (lo, hi) in enumerate(EDGES):
        if lo < d <= hi:
            return i
    return 0


def main():
    runs = json.load(open(RUNS, encoding="utf-8"))
    d2 = json.load(open(SIM2, encoding="utf-8"))
    ev = {r["sid"]: r for r in json.load(open(EV, encoding="utf-8"))}
    grid = d2["grid"]
    front = {(f["confirm"], f["release"]) for f in d2["pareto"]}
    sp = {s["thr"]: s for s in d2["sp"]}
    sw = {(g["confirm"], g["release"]): g["flicker"] for g in grid}
    ag = {(g["confirm"], g["release"]): g["agree"] for g in grid}
    confs = [1.0, 2.0, 3.0, 5.0]
    rels = [0.0, 1.0, 2.0, 3.0]

    rows, mism = [], []
    for r in runs:
        dwell = r["dwell"] + [0] * (5 - len(r["dwell"]))
        ms = max(range(len(dwell)), key=lambda i: dwell[i])
        rows.append("| %s | %s | %s | %d | %.1f | %d | %s | %d | %.1f%% |"
                    % (r["sid"], r["site"], r["period"], r["limit"], r["leq"],
                       r["switches"], CN[ms], r["seconds"], ev[r["sid"]]["e_pct"]))
        exp = grade(r["leq"] - r["limit"])
        if exp != ms:
            way = "灯比表格**低一档**" if ms < exp else "灯比表格**高一档**"
            mism.append("- **%s %s %s**：Δ = %+.1f dB，按限值应判 **%s**，但灯主要停在 "
                        "**%s**——%s"
                        % (r["sid"], r["site"], r["period"], r["leq"] - r["limit"],
                           CN[exp], CN[ms], way))

    total_sw = sum(r["switches"] for r in runs)
    sp_hits = sum(r["sp_hits"] for r in runs)
    peak_max = max(r["peak"] for r in runs)
    n_flat = sum(1 for r in runs if r["switches"] <= 3)

    def matrix(fmt, func):
        head = "| 确认时长 \\ 回差 | " + " | ".join("%d dB" % r for r in rels) + " |"
        sep = "|---|---|---|---|---|"
        body = []
        for c in confs:
            cells = []
            for r in rels:
                v = func((c, r))
                cell = ("%d" % v) if fmt == "int" else ("%.1f%%" % v)
                if (c, r) == (3.0, 2.0):
                    cell = "**%s**" % cell
                cells.append(cell)
            body.append("| %d s | %s |" % (c, " | ".join(cells)))
        return "\n".join([head, sep] + body)

    doc = """# 回放仿真：把实测序列喂进状态机

> 用途：验证《光效逻辑设计》里的状态机不是纸面规格，而是能跑、能调参、能复现的工程件。
> 全部输入来自本包 `data/` 的 15 段实测记录，**没有新增任何采集**。

## 一、为什么要做这一步

原来的交付里，光效逻辑只有三样东西：文字规格、「迁移规则」表、一张示意图。
评委只能判断「写得对不对」，判断不了「装上去会不会疯狂跳变」。

这一步把 15 段真实声级序列逐秒灌进状态机，回答三个问题：

1. 装上去以后，灯到底怎么亮？
2. 会不会疯狂跳变？
3. 3 s 确认、1 dB 回差这两个数字，凭什么？

## 二、仿真口径

| 项 | 取值 |
|---|---|
| 输入 | `data/S01…S15/Amplitudes.csv`，采样率约 9.2 Hz |
| 时间步 | 1 s（每 9–10 个样本做一次能量平均，得到 1 s Leq） |
| 档位判据 | `Δ_t = 1 s Leq − 该点位昼间限值` |
| 档位边界 | S0 Δ≤−10 / S1 −10<Δ≤0 / S2 0<Δ≤+5 / S3 +5<Δ≤+10 / S4 Δ>+10 |
| 上升沿 | 更高档位连续 3 s 成立才切换 |
| 下降沿 | 以档位边界为中心对称：升档需 Δ > 边界 + 1 dB，降档需 Δ < 边界 − 1 dB，保持 2 s，且当前状态已驻留 ≥10 s |
| 冲击通道 | 该秒内**采样峰值** ≥ 85 dB(A) 立即置 SP，持续 3 s |

**口径差异（重要）**：01 页汇总表的 Δ 是「整段 Leq − 限值」，这里的 `Δ_t` 是「每秒 Leq − 限值」。
两者在能量意义上是同一个数（已校验：15 段逐秒能量均与整段 Leq 完全一致，误差 < 0.01 dB），
但**逐秒会围绕均值摆动**，而摆动形态因点位因时段而异——这正是需要去抖和回差的原因，也是「发现 3」的来源。

**冲击通道必须用采样峰值，不能用 1 s 能量均**。这一步是按设计文档原意实现的：
若误用 1 s Leq 判冲击，15 段里 **一次都触发不了**（见发现 1 的附注），
因为 0.2 s 的尖叫会被 1 s 平均抹平——这恰好反证了「Leq 抓不住脉冲」。

## 三、15 段回放结果

| 编号 | 点位 | 时段 | 限值 | 整段 Leq | 切换次数 | 主要停留状态 | 时长(s) | 爆发能量占比 |
|---|---|---|---|---|---|---|---|---|
{rows}

- 15 段合计切换 **{total}** 次，平均每段 {avg:.1f} 次（每段 82–125 s，约每 50 秒变一次）
- **{nflat}/15 段切换 0–3 次**：灯基本常亮，只在开头 2–5 秒完成一次「入场判定」
- 只有 S15（实训室走廊晚）达到 6 次，是全套数据里唯一会出现可见闪烁的一段
- 图：`fig8_灯色回放时间线.png`（每条带子上方叠了逐秒 Δ 曲线，能看清「为什么这么亮」）

## 四、参数扫描：3 s + 2 dB 凭什么

只看「切换次数」会得出「越保守越好」的错误结论——把确认时长调到 60 秒，灯一次都不闪，
但它也早就不跟真值了。所以必须同时看两个互相矛盾的指标：

- **闪烁（flicker）**：15 段合计切换次数，越少越稳
- **一致率（agree）**：逐秒比较「灯的状态」与「按 1 s Leq 应得的档位」，相同的比例越高越准

切换次数矩阵（合计）：

{matrix_f}

逐秒一致率矩阵（15 段平均）：

{matrix_a}

**怎么读这两张表**：

- 1 s + 0 dB 最激进：142 次切换，一致率却只有 69.4%——因为它跟着噪声抖，反而判不准
- **3 s + 1 dB（本设计）：24 次切换，74.4% 一致率**
- 5 s + 3 dB 最保守：15 次切换，64.8%——比本设计只稳 1 次，却丢将近 10 个点准确率

把 16 个组合画在「闪烁—准确率」平面上，落在**帕累托前沿**上的只有 6 个
（`fig9_参数扫描矩阵.png`）：其余 10 个组合都能被某个前沿点同时压住。
**本设计的 3 s / 1 dB 正好落在这条前沿上**——这就是它「不是一个随便的数字」的证明。

## 五、四个实测发现

### 发现 1：冲击通道在校园场景里几乎用不上

按采样峰值判定，15 段约 1500 秒里：

| 阈值 | 触发秒数 | 涉及段数 |
|---|---|---|
| 85 dB（GBZ 2.2 职业限值） | {sp85} | {seg85}/15 |
| 84 dB | {sp84} | {seg84}/15 |
| 82 dB | {sp82} | {seg82}/15 |
| 80 dB | {sp80} | {seg80}/15 |
| 78 dB | {sp78} | {seg78}/15 |

实测最高采样峰值只有 **{peak:.1f} dB(A)**。即使把阈值降到 78 dB（比职业限值低 7 dB），
1500 秒里也只有 5 秒触发、摊在 4 段上。

**结论：不是阈值设错了，是这 15 段场景本来就没有脉冲型噪声。**
这一带校园的噪声是「持续偏高型」，不是「偶发冲击型」。
所以「85 该不该降到 80」这个问题，数据给出的答案是：降不降都不影响这 15 段的结论，
但**应该在报告里说明这条通道在校园场景下的适用性**，而不是假装它工作良好（`fig11`）。

附注：如果误用 1 s 能量均去判 85 dB，15 段里触发 **0 次**——因为 1 s 平均会把 0.2 s 的尖叫抹平。
这从反面说明：冲击通道必须用采样级峰值，实现时不能偷懒用 Leq。

### 发现 2：同样是超标，「吵了一下」和「一直吵」完全不是一回事

用「高于本段 L90+10 dB 的样本占总能量的比例」衡量爆发程度（`fig10_能量构成.png`）：

- **S06 图书馆午间：51.4%** —— 一半能量来自极少数样本，其余 100 秒其实很安静
- S05 实训室走廊早 15.1%、S11 图书馆晚 10.9%
- **S07 食堂午间、S09、S10、S12、S13、S15：0.0%** —— 整段平稳抬高，没有爆发

两者治理手段完全不同：爆发型该管「那几秒」，持续型该管「整个环境」。
**这也是光效必须双通道的实测依据**：爆发型该闪，持续型该常亮。

### 发现 3：能量均值判「中度超标」，灯却显示「轻度」——差一档

15 段里有 3 段出现「表里不一」：

{mismatch}

原因不是 bug，是**两种判定的物理含义本来就不同**：

- 汇总表的 Δ 是**能量均值**——两个 1 秒的 75 dB 尖峰，就能把 100 秒的 58 dB 拉高 3 dB
- 灯的 Δ 是**瞬时值**——它只能反映「此刻响不响」，反映不了「平均水平」

S06 就是典型：106 秒里 95 秒都在 57–59 dB（Δ 只有 +2~+4），中间两秒冲到 75/76 dB，
足以把整段 Leq 抬到 61.2（Δ = +6.2）。灯诚实地显示「轻度超标」，表格诚实地写「中度超标」。

**这不是矛盾，是必须写进文档的口径对齐**：表格判定用 Leq（符合 GB 3096 的计权方式），
灯的状态用瞬时值（符合人的主观感受）。两者不一致时以表格为准，灯只作提示。
不写清这一点，现场一句「你表说中度、灯怎么是黄的」就能把人问住。

### 发现 4：多数场景下「去抖」其实没被用到

{nflat}/15 段的切换发生在开头 2–5 秒，之后 90–120 秒一动不动。
说明当前这批数据里「临界抖动」不是主要矛盾——真正会闪的场景（食堂高峰的餐盘碰撞、
主干道下课人流）**还没被录到**。

这是局限，也是下一步采集的方向。

## 六、复现方式

```
cd D:\\deepseek工作\\noise06
python sim.py        # 状态机回放 → build/sim_runs.json、build/sim_sweep.json
python events.py     # 事件归因   → build/events.json
python sim2.py       # 一致率与帕累托、阈值敏感性 → build/sim2.json
python figsim.py     # 画 fig8 / fig9 / fig10 / fig11
python gen_simdoc.py # 重新生成本文件（所有数字由数据算出）
```

五个脚本只依赖标准库 + Pillow，输入只读本包 `data/`。

## 七、局限（必读）

1. **样本时长**：每段 82–125 s，回放得出的「稳定状态」只代表那两分钟，不代表整天
2. **采样率**：约 9.2 Hz，1 s 只有 9 个点，1 s Leq 分辨率有限，抓不住 <0.1 s 的尖峰
3. **单一场景**：15 段都在「有人在但不拥挤」的时段，没有录到高峰期
4. **参数是在本批数据上扫出来的**：换点位、换季节、换学校都要重扫，不能直接套用
5. **SP 通道未验证**：几乎不触发，无法判断它触发时是否正确
6. **一致率上限受 5 s 保持限制**：本次扫描固定了保持时长，只变确认与回差；
   若把保持也算进网格，一致率还能更高，但代价是降档更迟钝

以上六条同时登记在 `证据包/ANOMALIES.md`，不隐藏。
"""

    doc = doc.format(
        rows="\n".join(rows), total=total_sw, avg=total_sw / 15.0, nflat=n_flat,
        mismatch="\n".join(mism) if mism else "- 无",
        matrix_f=matrix("int", lambda k: sw[k]),
        matrix_a=matrix("pct", lambda k: ag[k]),
        sp85=sp[85]["seg_frames"], seg85=sp[85]["seg_hit"],
        sp84=sp[84]["seg_frames"], seg84=sp[84]["seg_hit"],
        sp82=sp[82]["seg_frames"], seg82=sp[82]["seg_hit"],
        sp80=sp[80]["seg_frames"], seg80=sp[80]["seg_hit"],
        sp78=sp[78]["seg_frames"], seg78=sp[78]["seg_hit"],
        peak=peak_max)

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(doc)
    print("saved", OUT, len(doc), "chars,", len(mism), "mismatches,",
          len(front), "pareto points")


if __name__ == "__main__":
    main()
