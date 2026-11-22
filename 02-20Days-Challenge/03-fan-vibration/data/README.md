# data/ · 这个目录里有什么、缺什么、怎么补

## 一句话

**代码、特征表、结果、图都在仓库里；原始音视频不在仓库里，在提交系统的「第 4 步 · 大文件分片上传」包里。**

---

## 仓库里保留了什么（约 13 MB）

| 路径 | 内容 | 能不能直接用 |
|---|---|---|
| `features.csv` | 98 段 × 6 特征（f0 / centroid / e_low / e_mid / e_high / h2 / h3 / h4） | ✅ 全部下游实验的输入 |
| `vibration.json` | 15 组振动的水平/垂直 RMS 与主峰 | ✅ |
| `raw/` 下的 `.csv` | 逐段的导出特征（不含波形） | ✅ |
| `照片/` 6 张 | 带时间地点水印的现场照 | ✅ |
| `盲测视频.mp4` | 演示视频 | ❌ **已移出**（28.6 MB，超 25 MB 限制） |
| `wav/`、`原样导出_wav32/`、`blind/`、`未使用/` | 原始音频 | ❌ **已移出**（共 219 个，218 MB，属「WAV 音频集」） |

---

## 搬出清单（共 220 个文件 / 246.6 MB）

| 原因 | 路径 | 数量 | 体积 |
|---|---|---|---|
| WAV 音频集 | `data/wav/`、`data/原样导出_wav32/` | 138 | 179.3 MB |
| 音频集（mp3） | `data/blind/`、`data/未使用/` 等 | 81 | 38.7 MB |
| 演示视频 >25MB | `data/盲测视频.mp4` | 1 | 28.6 MB |

**依据**：提交页自检清单第 ② 条——「超过 25MB 的演示视频（MP4/MOV）、200+ 原图包、WAV 音频集或模型权重，切勿强塞进 GitHub，直接通过第 4 步『大文件分片上传』直传校内门户服务器」。

---

## 怎么补回来

1. 从提交系统的第 4 步包里取出 `大文件包`（含 `MANIFEST.csv`）；
2. 把里面 `02-20Days-Challenge/03-fan-vibration/data/` 的内容**按原相对路径覆盖**回本目录；
3. 校验（在仓库根目录执行）：

```powershell
$rows = Import-Csv "大文件包\MANIFEST.csv" | Where-Object { $_.相对路径 -like "*03-fan-vibration/data*" }
$bad = 0
foreach ($r in $rows) {
    if (-not (Test-Path -LiteralPath $r.相对路径)) { $bad++; continue }
    if ((Get-FileHash -LiteralPath $r.相对路径 -Algorithm MD5).Hash -ne $r.MD5) { $bad++ }
}
"共 $($rows.Count) 个，异常 $bad 个"
```

---

## 搬走之后，还有哪些结论可以当场复核

**不需要音频就能复核的部分（全部）**：
- 三类 90.8% / 五类 61.2% / 分层 90.8·100·43.1 —— 输入是 `features.csv`，`code/hier.py` 直接跑
- 振动通道全部结论 —— 输入是 `vibration.json`
- 11 张图 —— 输入是上面两者

**需要音频才能复核的部分**：
- 从 mp3/wav 重新提取特征（`code/featurize.py`）
- 频谱瀑布图（`figs/fig09_频谱瀑布.png`）的原始 STFT

也就是说：**下游结论全部可复算，上游特征提取需要大文件包**。
