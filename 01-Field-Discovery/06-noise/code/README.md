# 课题 06　生成脚本说明

## 先看这条：这些脚本在本包里能直接跑

`code/` 下每个脚本都按**双布局**解析路径：脚本位于本包的 `code/` 里时，数据取本包 `data/`、中间件取本包 `results/`、图与文档写回本包 `figs/`、`docs/`、`数据/`；脚本仍放在作者工作区（`D:\deepseek工作\noise06`）时，中间件沿用工作区的 `build/`。同一份代码两条路都能走，不用改任何常量。

| 能在包内直接跑（只读本包 `data/` + `results/`） | 需要原始采集目录（`D:\分贝项目`，无法随包提供） |
|---|---|
| `recompute.py` 复核 15 组指标 | `extract.py`：原始 zip → `stats.json` |
| `robust.py` → `figrobust.py` 稳健性分析 + fig13/fig14 | `meta.py`：设备型号、校准偏移、双源 |
| `gum.py` 不确定度预算 | `evidence.py`：采集证明 CSV、SHA256 |
| `sim.py` → `events.py` → `sim2.py` → `sim3.py` → `sim4.py` → `figsim.py` → `figacc.py` → `gen_simdoc.py`（回放仿真 + fig8–fig12 + 本文档） | |
| `figs.py`（fig1–fig6）、`figmap.py`（fig7） | |
| `build_xlsx.py` 重建 `数据/*.xlsx`（需 openpyxl） | |

生成图所需的中间件（`stats.json`、`meta.json`、`sim_runs/sim_sweep/sim2–4.json`、`events.json`、`robust.json`、`gum.json`）全部随包放在 `results/`，底图 `campus_map.jpg` 放在 `data/`。

**已实测**（2026-11-01，Python 3.12 + Pillow 12.3 + openpyxl 3.1.5）：在包内重跑上面整条流水线，`figs/` 下 14 张图与随包版本**逐字节一致**（SHA256 相同），`数据/*.xlsx` 用同一串脚本重建后，15 组指标与判定结果完全一致（xlsx 是 zip 容器，字节比较无意义）。也就是说这些图确实是这串脚本从 `data/` 算出来的，不是手画的。

---

这个目录是这个交付包里**每一个数字、每一张图**的来源。分两类：

| 文件 | 作用 | 能否直接跑 |
|---|---|---|
| `recompute.py` | **独立复核**：只读本包的 `data/`，重算全部 15 组指标并与 `meta.txt` 对账 | ✅ 可直接跑，不依赖任何外部数据 |
| `extract.py` | 从原始包（zip / 导出文件夹）提取 15 组指标 → `stats.json` | ⚠ 需要原始数据目录 |
| `meta.py` | 提取设备型号、校准偏移、双源对照 → `meta.json` | ⚠ 需要原始数据目录 |
| `build_xlsx.py` | 生成 `数据/*.xlsx` 五个 sheet | ⚠ 读 `stats.json` |
| `figs.py` | 生成 `figs/fig1`–`fig6` | ⚠ 读 `stats.json`、`meta.json` |
| `figmap.py` | 生成 `figs/fig7_噪声地图.png`（校园平面图打点） | ⚠ 需要 `campus_map.jpg` |
| `evidence.py` | 生成 `证据包/` 里的采集证明 CSV、SHA256、日志骨架 | ⚠ 需要原始数据目录 |

---

## 一、想验证「这些数是不是真的」，只跑这一个

```bash
cd code
python recompute.py
```

输出会打印 15 行指标，并在末尾给出**与 `data/Sxx/meta.txt` 记录的最大偏差**（当前为 0.005 dB，来自四舍五入）。
如果这个脚本在你机器上跑出来的结果与 Excel 的「01 十五组汇总」一致，就说明交付里的每个数都能从原始序列独立复现。

加 `--csv` 会同时写出 `recompute.csv`，方便逐行对照。

它只依赖 Python 标准库，不需要 numpy / pandas / openpyxl。

---

## 二、想从原始数据完整重跑，按这个顺序

```bash
python extract.py        # → build/stats.json      （15 组指标）
python meta.py           # → build/meta.json       （设备、校准偏移、双源）
python build_xlsx.py     # → 数据/*.xlsx
python figs.py           # → figs/fig1–fig6
python figmap.py         # → figs/fig7（需要 build/campus_map.jpg）
python evidence.py       # → 证据包/（采集证明、SHA256、日志骨架）
```

**需要改的一行**：每个脚本开头都有一个绝对路径常量（`ROOT` 指向原始数据目录、`OUT_DIR` 指向输出目录），
改成你自己机器上的路径即可。原始数据的目录结构是：

```
<ROOT>/
├── 早图书馆/
├── 早食堂/
├── …
└── 晚上图书馆/
    └── 晚图书馆2026-10-25 19-11-41/    ← 这一组是未压缩的导出文件夹（PLK110），见 ANOMALIES A-01
```

每个文件夹里是 Phyphox「声音振幅」导出的 zip，或解压后的同结构目录。

**依赖**：`build_xlsx.py` 需要 `openpyxl`，`figs.py` / `figmap.py` 需要 `Pillow`，
字体用 Windows 自带的 `微软雅黑`（`C:\Windows\Fonts\msyh.ttc`）。

---

## 三、几个容易踩的点（写在这里省得你重新发现）

1. **`Amplitudes.csv` 里有 `-∞` 和 `NaN` 行**。Phyphox 在声级为 0 时写 `-∞`，个别段末尾会写 `NaN`，
   两者都必须跳过，否则 `Leq` 会算成 `nan`。
2. **采样率不是 20 Hz，是约 9.2 Hz**。早期版本误标为 20 Hz，已按实测改正（15 段 758~1152 个样本，对应 82~125 s）。
3. **重力方向必须按时间插值，不能按行号对齐**。加速度 480 Hz、重力 200 Hz，行号对不上。
4. **晚上图书馆那一组的 zip 不是本人数据**（同学用 PKG110 录的重复件），
   本人的是未压缩文件夹，脚本里用 `SOURCE_OVERRIDE` 显式指定——这是 ANOMALIES A-01 的处理方式。

## 回放仿真（创新五）

| 文件 | 作用 | 输入 | 输出 |
|---|---|---|---|
| `sim.py` | 把 `data/` 里的 15 段序列逐秒灌进光效状态机，统计切换次数与驻留 | `data/` | `build/sim_runs.json`、`build/sim_sweep.json` |
| `sim2.py` | 逐秒一致率、闪烁-准确率帕累托前沿、冲击阈值敏感性 | `data/` + `sim.py` 的函数 | `build/sim2.json` |
| `sim3.py` | 三处改动的消融：换基准 / 对称回差 / 3 s 输入 | `data/` | `build/sim3.json` |
| `sim4.py` | 保持时长 × 最短驻留扫描 | `data/` | `build/sim4.json` |
| `figacc.py` | fig12 准确率提升路径 | `build/sim3.json` + `sim4.json` | `figs/fig12` |
| `events.py` | 事件归因：高于本段 L90+10 dB 的样本占总能量多少 | `data/` | `build/events.json` |
| `figsim.py` | 画 fig8 灯色时间线、fig9 参数扫描矩阵、fig10 能量构成 | 上面两个 json | `figs/fig8–10` |
| `gen_simdoc.py` | 生成 `docs/回放仿真说明.md`（表格由数据算出，不手抄） | 上面三个 json | 该 md |

运行顺序：

```
python sim.py
python events.py
python sim2.py
python sim3.py
python sim4.py
python figsim.py
python figacc.py
python gen_simdoc.py
```

注意：这四个脚本假设工作目录是包根（与 `data/`、`build/` 同级），
`build/` 不存在时先建。

### 稳健性分析（结果 13 / 14）

| 脚本 | 作用 | 输入 | 输出 |
|---|---|---|---|
| `robust.py` | bootstrap 置信区间、翻转率、整体偏移扫描、时长收敛 | 本包 `data/`、`results/stats.json` | `results/robust.json` + 屏幕表格 |
| `figrobust.py` | 画两张图 | `results/robust.json` | `figs/fig13_判定误差棒.png`、`figs/fig14_时长收敛.png` |

运行顺序：`robust.py` → `figrobust.py`。`robust.py` 只依赖标准库，`results/stats.json` 已随包提供（由 `extract.py` 生成）；若只想复核数字，直接看 `results/robust_输出.txt` 与 `results/robust.json` 即可。
