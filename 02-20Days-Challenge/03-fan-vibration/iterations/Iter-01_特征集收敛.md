# Iteration 01　特征从 8 个收敛到 6 个

## 变更前
`time_feats`（rms/peak/crest/skew/kurt/zcr）+ `freq_feats`（centroid/bandwidth/rolloff/flatness）
+ `harm_ratios`（f0/h2/h3/h4），共 8 个进分类。

## 变更后
`f0 + e_mid + e_high + h2 + h3 + h4`（6 个）。

## 依据
`code/ablate.py` 的逐特征消融（见 `process_logs/2026-11-09_提准三组实验.md`）：
- 删 `centroid`：五类 66.3 → 67.3
- 删 `e_low`：三类 90.8 → 92.9
- 删 `f0`：五类掉到 58.2（不能删）

## 为什么这两个可以删
它们主要编码「手机离声源多远」，属位置特征。同一工况下换个距离，这两个量变化比换工况还大。

## 影响
五类留一法 66.3 → 68.4；分组 CV 61.2（新增口径）。
