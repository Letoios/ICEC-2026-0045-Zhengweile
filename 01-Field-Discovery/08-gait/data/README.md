# data/ · 原始 CSV 不在仓库里

## 一句话

**46 段原始 Phyphox CSV（128 个文件 / 86.9 MB）在提交系统的「第 4 步 · 大文件分片上传」包里；
仓库只保留由它们生成的派生结果 `../features_all.csv`。**

---

## 为什么搬出去

不是因为数据敏感，是因为体积。128 个 CSV 平均 680 KB，合计 86.9 MB，占了阶段一的一半以上。
提交页自检清单第 ② 条要求「大文件……切勿强塞进 GitHub，直接通过第 4 步分片上传」，
所以把这一整层原始波形搬出去，只留特征表。

---

## 仓库里保留了什么

| 文件 | 内容 | 能不能直接用 |
|---|---|---|
| `../features_all.csv` | **46 行 × 12 列**：`file / source / truth / pred / ok / dur / rms / cad / ac / diff / skew / crest / impulse` | ✅ 所有判定、所有图、`gait_classify.py --check` 的输入 |
| `../gait_classify.py` | 九条规则 + `--check` / `--all` | ✅ 跑 `--check` 直接输出「共 46 段，判对 46，判错 0」 |

---

## 必须说清的代价

**`features_all.csv` 是派生结果，不是原始数据。** 搬走原始 CSV 之后：

- ✅ 判定逻辑、阈值、余量表、所有结论 —— **仍然可复核**（输入是特征表）
- ❌ 从原始波形重算特征 —— **不能在仓库内完成**，要先恢复 CSV 再跑 `../featurize.py`

这是这次取舍里唯一真正损失的东西。所以这句话写在最前面，不藏在最后。

---

## 怎么补回来

1. 从提交系统第 4 步包里取出 `大文件包`（含 `MANIFEST.csv`）；
2. 把里面 `01-Field-Discovery/08-gait/data/` 的内容**按原相对路径覆盖**回本目录；
   每个样本目录应含 `Accelerometer.csv`、`Gravity.csv`、`meta/time.csv`；
3. 校验（在仓库根目录执行）：

```powershell
$rows = Import-Csv "大文件包\MANIFEST.csv" | Where-Object { $_.相对路径 -like "*08-gait/data*" }
$bad = 0
foreach ($r in $rows) {
    if (-not (Test-Path -LiteralPath $r.相对路径)) { $bad++; continue }
    if ((Get-FileHash -LiteralPath $r.相对路径 -Algorithm MD5).Hash -ne $r.MD5) { $bad++ }
}
"共 $($rows.Count) 个，异常 $bad 个"
```

期望：`共 128 个，异常 0 个`。

4. 恢复后重算特征：

```powershell
cd 01-Field-Discovery/08-gait
python featurize.py          # 重新生成 features_all.csv
python gait_classify.py --check   # 应为「共 46 段，判对 46，判错 0」
```

---

## 采样参数（供核对，不需要原始文件也能验证）

| 项 | 值 |
|---|---|
| 采样率 | 480 Hz（`Accelerometer.csv`） |
| 重力 | 200 Hz（`Gravity.csv`，独立文件，不用整段均值估） |
| 姿态 | 240 Hz（`Orientation.csv`） |
| 对齐 | **按时间列 `np.interp`**，不按行号 |
| 单段时长 | 17.9 – 51.2 s |
| 坐标约定 | 竖直 = 重力方向投影，去直流后取动态分量 |
