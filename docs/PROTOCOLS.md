---
title: "PROTOCOLS — 评测协议：论文口径、我们的映射、跨数据集候选"
tags:
  - "#modality/eeg"
  - "#pipeline/5_dl_model"
  - "#method/benchmark"
created: "2026-09-13"
updated: "2026-09-13"
status: "draft"
---

# PROTOCOLS

> §1 是论文事实；§2、§3 是**候选方案，未拍板**（对应 `PLAN.md` §5）。定了以后写进 `configs/protocols/*.yaml` 并记 `DECISIONS.md`。

## 1. 论文口径（EEG-FM-Compass §3.2–3.4，事实）

| 项 | 内容 |
|:---|:---|
| 场景 A：LOSO | 同任务、同设备下的跨被试；测试被试零校准。**MI/P300 的 5 个 BNCI 数据集：每被试只用单个 session 微调**；其余数据集用全部 trial。大数据集（TUAB、Sleep-EDFx）用 10 折被试划分 |
| 场景 B：within-subject few-shot | 目标被试少量标注微调、其余评测。MI：单 session 的 30%（每类 <30 trial）；BNCI2014009 单 session 10%；BNCI2014008 单 session 5%（Table 15） |
| 微调策略 | full-parameter fine-tuning vs linear probing（冻结 encoder，只训 head）；补充 LoRA 实验（CBraMod、Neuro-GPT） |
| 重复与报告点 | 3 个随机 seed 平均；**报告微调最后一个 epoch 的测试集指标** |
| 超参 | 每模型单独调，不共用一套 |
| 指标 | 分类主指标 **BCA**；MI 另报 Acc、Cohen's κ（Tables 16–21）；P300 另报 AUC（Tables 22–25） |
| 预处理 | 每个 FM 按自身规范（Table 4）：采样率 / 滤波 / 归一化 / 通道映射 / patch；specialist 用数据集原生 |
| EA | 只用于原实现含 EA 的 EEGPT、MIRepNet；其余不做（避免预训练/微调表征空间不匹配） |
| 特殊 | BNCI2014009 的 0.8 s epoch 前补 0.2 s 凑成 1 s，满足 FM 最短输入；BrainOmni 不支持双极 montage（CHB-MIT、Sleep-EDFx 排除） |
| 泄漏标注 | 下游数据集若在某 FM 预训练语料中，表中标 ‡，并给 leakage-aware 排名。**5 个 BNCI 数据集在 Table 2 无 ‡** |
| 硬件 | 24×A800 + 8×A100 |

## 2. 我们的 LOSO 映射（候选）

| 数据集 | 被试数 | 微调 session（论文口径） | 测试 | 备注 |
|:---|---:|:---|:---|:---|
| BNCI2014001 | 9 | 单 session（候选：`0train`） | 留出被试全部 session | 4 类 |
| BNCI2014004 | 9 | 单 session（候选：第 1 个） | 同上 | 3 双极通道，FM 通道映射是难点 |
| BNCI2015001 | 12 | 单 session | 同上 | 512 Hz，部分被试 3 session |
| BNCI2014009 | 10 | 单 session | 同上 | P300，不平衡 |
| BNCI2014008 | 8 | 单 session（只有 1 个） | 同上 | ALS 被试，35 字符 |
| WBCIC-SHU | 51（2C）/ 11（3C） | **待定 Q2**：ses-01 / 全部 | 留出被试 3 session | **待定 Q1**：2C / 3C |
| SHU 2022 | 25 | **待定 Q2**：ses-01 / 全部 | 留出被试 5 session | 跨被试近 chance（51.4–53.7%） |

- 验证集：从训练被试中按被试留出（不切 trial）；final-epoch 口径下验证集只用于监控与 best-val 副表。
- seeds：训练 seed `{0,1,2}`；LOSO 本身无划分随机性。
- 单 session 选择必须对所有模型一致，并写进 split JSON。

## 3. 跨数据集实验候选（P4，**未定**）

### 3.1 任务与标签空间

| 组 | 数据集 | 公共标签空间 | 通道 |
|:---|:---|:---|:---|
| MI-LR | BNCI2014004、WBCIC-SHU 2C、SHU 2022、BNCI2014001（取 L/R 子集） | left_hand / right_hand | 3 bipolar / 58 / 32 / 22 |
| MI-RF | BNCI2015001、BNCI2014001（取 right/feet 子集）、WBCIC-SHU 3C（取 right/feet） | right_hand / feet | 13 / 22 / 58 |
| P300 | BNCI2014009、BNCI2014008 | target / non-target | 16 / 8 |

### 3.2 划分方式候选

- **A. Leave-one-dataset-out（LODO，零样本）**：在同组其余数据集上微调，在留出数据集**全部被试**上测试。最严格，直接回答「换设备/换实验室还能不能用」。
- **B. LODO + 目标校准（few-shot）**：A 的基础上加目标数据集少量被试/少量 trial 微调（借用论文 few-shot 比例）。
- **C. 成对迁移矩阵**：每对 (源, 目标) 一格，得到 k×k 矩阵，可看不对称性（如 58ch→3ch vs 3ch→58ch）。
- 对照：每个目标数据集自身的 LOSO 数字（§2）= 「同分布上界」；chance = 下界。

### 3.3 异质性处理（论文 §2 Channel Unification 的 6 类策略 → 我们的三档）

| 档 | 做法 | 适用模型 | 代价 |
|:---|:---|:---|:---|
| U1 交集通道 | 所有数据集取公共电极（MI 至少 C3/Cz/C4；需处理 BNCI2014004 双极 vs 单极） | 全部 specialist + 固定 montage 的 FM | 丢空间信息 |
| U2 插值到模板 | MNE 球面样条插值到 10-20 19 ch（CBraMod/BENDR 词表）或各 FM 词表 | 需要固定词表的 FM（CBraMod 19、Neuro-GPT 22、TFM 16、BrainOmni 16…） | 插值伪迹；3 ch → 19 ch 不可信 |
| U3 FM 原生机制 | 坐标感知（LUNA、BrainOmni）/ 逐通道（BIOT、SingLEM、TFM）/ 可学习通道 embedding（LaBraM、EEGPT、CBraMod） | 对应 FM | 各 FM 行为不同，需逐个查官方实现 |

时间维：统一裁到公共窗口（候选 0–4 s post-cue；BNCI2014004 4.5 s、BNCI2015001 5 s 裁短）；采样率由各模型 `input_spec` 处理。

### 3.4 对齐与泄漏

- EA（论文 §4.3）：按被试或按 session 计算参考协方差；跨数据集时只能用**源/训练侧**统计量或目标侧无标签 trial（后者要单独标注为 test-time alignment）。
- 预训练泄漏：跨数据集结论也要给 leakage-aware 版本（当前 7 个数据集对 12 个 FM 均无 ‡，但拉代码后要按各 FM 预训练语料表再核一次 WBCIC/SHU）。

## 4. 指标与统计

- BCA（主）、Acc、κ、macro-F1；P300 加 AUC；全部 per-subject 记录再聚合，标准差 ÷(n−1)。
- 模型间：同 run 内配对 Wilcoxon（Holm 校正）+ Friedman/Nemenyi CD 图；与论文数字只做数值对照，不做检验（无 per-seed 原始值）。
