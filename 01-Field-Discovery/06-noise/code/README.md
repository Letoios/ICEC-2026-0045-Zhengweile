# 课题 06　生成脚本说明

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
