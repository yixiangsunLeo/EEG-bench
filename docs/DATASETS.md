---
title: "DATASETS — 7 个数据集卡片"
tags:
  - "#modality/eeg"
  - "#pipeline/1_data"
created: "2026-09-13"
updated: "2026-09-13"
status: "active"
---

# DATASETS

> 机器可读版在 `configs/datasets/*.yaml`。BNCI 五个的数字来自论文 Table 14 与 A3；两个自有数据集来自旧项目已核实事实。
> 拉数据后若与 MOABB 实际不符，以实际为准并更新两处。

## 1. 总表

| key | 名称 | 范式 | 被试 | 通道 | 采样率 | trial 长度 | trial 总数 | 类别 | 来源 |
|:---|:---|:---|---:|---:|---:|---:|---:|:---|:---|
| `bnci2014001` | BNCI2014001（BCI Comp. IV 2a） | MI | 9 | 22 | 250 | 4 s | 2,592 | left_hand / right_hand / feet / tongue | MOABB `BNCI2014_001` |
| `bnci2014004` | BNCI2014004（BCI Comp. IV 2b） | MI | 9 | 3（双极 C3/Cz/C4） | 250 | 4.5 s | 1,400 | left_hand / right_hand | MOABB `BNCI2014_004` |
| `bnci2015001` | BNCI2015001 | MI | 12 | 13 | 512 | 5 s | 2,400 | right_hand / feet | MOABB `BNCI2015_001` |
| `bnci2014009` | BNCI2014009 | P300 | 10 | 16 | 256 | 0.8 s（补到 1 s） | 5,760 | target / non-target | MOABB `BNCI2014_009` |
| `bnci2014008` | BNCI2014008（ALS） | P300 | 8 | 8 | 256 | 1 s | 33,600 | target / non-target | MOABB `BNCI2014_008` |
| `wbcic_shu` | WBCIC-SHU 2025（Yang et al., Sci Data 12:488） | MI | 2C 51 / 3C 11 | 58 | 250 | 4 s | 2C 见 manifest / 3C 9,899 | 2C: left/right；3C: left/right/feet | 外部盘 processed npz |
| `shu2022` | SHU 2022（Ma et al., Sci Data 2022） | MI | 25 | 32 | 250 | 4 s | ≈11,988（125 session × 90–100） | left_hand / right_hand | 外部盘 processed npz |

## 2. 各数据集细节

### bnci2014001
- 2 session（MOABB 命名 `0train` / `1test`），每 session 6 run × 48 = 288 trial。4 类平衡。
- 论文 LOSO：每被试单 session 微调。

### bnci2014004
- 5 session：前 2 个无反馈筛查，后 3 个有反馈；每类 120 trial/被试。3 个双极通道。
- **FM 通道映射难点**：多数 FM 词表是单极 10-20 名；双极 `C3-?` 如何映射需看官方 benchmark 实现。

### bnci2015001
- 右手 vs 双脚持续 MI；512 Hz、13 电极、0.5–100 Hz 带通 + 50 Hz 陷波（数据集自带）。部分被试 3 个 session。

### bnci2014009
- 6×6 矩阵拼写 P300，10 名健康被试，16 通道（Fz, FCz, Cz, CPz, Pz, Oz, F3, F4, C3, C4, CP3, CP4, P3, P4, PO7, PO8），0.1–20 Hz。4 session × 3 run。
- 严重不平衡（target : non-target ≈ 1 : 5），BCA 与 AUC 都要。论文把 0.8 s epoch 前补 0.2 s。

### bnci2014008
- 8 名 ALS 被试，8 通道（Fz, Cz, Pz, Oz, P3, P4, PO7, PO8），0.1–30 Hz，7 run × 5 字符 = 35 trial，展开为 33,600 个 flash epoch。单 session。

### wbcic_shu（自有）
- 原始：BIDS，`/share/workspace2/moto_imagination/WBCIC_SHU/`（`sourcedata/2C dataset`、`derivatives/{2C,3C} dataset_processeddata`），raw 59 ch @1000 Hz。
- 已处理（可直接用）：`.../WBCIC_SHU/processed/eog_ecg_clean/processed_manifest.csv`，`X [trials, 58, 1000]`（250 Hz × 4 s），标签 {0,1}；148 session ok / 5 failed。
- **2C（subjects 1–51）与 3C（subjects 52–62）是互斥被试队列，不是子集**；Figshare 写的 "52 subjects" 有误，以 51 为准。3 session/被试。
- 3C 的 processed npz 之前放在旧项目 `outputs/processed/wbci_shu_3c_mat_clean/`（已删）；需重新生成，旧脚本见 `LEGACY.md`（约 7 分钟）。
- 文献对标：EDAPT（J Neural Eng 2026）零样本跨被试 EEGNet 0.81 / DeepConvNet 0.85（59 ch / 1000 Hz 原始数据，2 折被试划分）——口径不同，仅作参考。
- MOABB 中疑有对应条目（`Yang2025`），待核；若有，优先走 MOABB 以统一口径。

### shu2022（自有）
- 原始：作者发布的 per-session `.mat`（已带通/陷波/4 s 切段），`/share/workspace2/moto_imagination/SHU/`。
- 已处理（可直接用）：`.../SHU/processed/npz_clean/processed_manifest.csv`，`X [trials, 32, 1000]`，`y ∈ {0,1}`，125 session 全 ok，每 session 90–100 trial，类别不保证 50/50。
- 5 session/被试。跨被试解码接近 chance（chance band 51.4–53.7%），1–2 pp 差异按噪声处理。
- SHU 2022 论文自身跨 session 数字（≈53.7%）用的是 ses-01 训练 + 1500 epoch，与我们口径不可比。

## 2.5 BNCI 五套下载与核对（2026-09-14，事实）

- 位置：`/share/workspace2/moto_imagination/MNE-bnci-data/~bci/database/{001-2014,004-2014,001-2015,009-2014,008-2014}/`，
  82 个 `.mat`，3.4 GB；文件清单与路径由 moabb 1.5.0 自身枚举（`scripts/download_bnci.py --curl`），主机为 MOABB 默认的
  TU Graz 源站。`scripts/verify_bnci.py` 用 MOABB loader 读取全部被试后与 Table 14 对比：

| key | 被试 | EEG 通道 | fs | moabb 1.5.0 的 session 名（每 session 试次） | Table 14 试次 | 对应关系 |
|:---|---:|---:|---:|:---|---:|:---|
| bnci2014001 | 9 ✓ | 22 ✓ | 250 ✓ | `0train` 2592 / `1test` 2592 | 2,592 | = `0train`（官方脚本所取） |
| bnci2014004 | 9 ✓ | 3 ✓ | 250 ✓ | `0train` 1120 / `1train` 1120 / `2train` 1440 / `3test` 1400 / `4test` 1440 | 1,400 | = `3test`（官方脚本所取，唯一吻合的 session） |
| bnci2015001 | 12 ✓ | 13 ✓ | 512 ✓ | `0A` 2400 / `1B` 2400 / `2C` 800 | 2,400 | = 第 1 个 session（`0A`） |
| bnci2014009 | 10 ✓ | 16 ✓ | 256 ✓ | `0` 5760 / `1` 5760 / `2` 5760 | 5,760 | = 第 1 个 session（`0`） |
| bnci2014008 | 8 ✓ | 8 ✓ | 256 ✓ | `0` 33600 | 33,600 | 唯一 session |

- **MOABB 版本问题（待确认）**：官方 `Preprocess_Dataset.py` 对 2015001 / 2014009 / 2014008 按 `sessions == '0train'` 过滤，
  但 moabb 1.5.0 下这三套的 session 名是 `0A` / `0` / `0`，该过滤会得到空集——作者用的 MOABB 版本命名不同（未 pin）。
  语义上 Table 14 的数字都对应"第 1 个 session"，但按哪个版本/怎样映射需拍板（PLAN Q10）。

## 3. canonical 化要点

- 五个 BNCI：用 MOABB 下载 + 取 epoch（不做 MOABB 的默认滤波，保留原生采样率），再写 canonical；记录 MOABB 版本。
- 两个自有：从外部 processed npz 直接转 canonical，补齐 10-20 通道名（WBCIC 58 ch、SHU 32 ch 的通道表要从原始数据集文档取），记录来源 manifest sha256。
- 通道名统一到 10-20 标准名；双极通道 `A-B` 形式并标 `montage: bipolar`。
- 单位统一 µV；不在 canonical 层滤波/重采样。
