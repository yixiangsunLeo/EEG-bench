---
title: "PLAN — 目标、范围、阶段、待决策"
tags:
  - "#modality/eeg"
  - "#pipeline/5_dl_model"
  - "#method/benchmark"
created: "2026-09-13"
updated: "2026-09-13"
status: "active"
---

# PLAN

> 活文档：阶段状态、范围、待决策清单变了就改。规则在 `AGENTS.md`，决定在 `DECISIONS.md`。

## 1. 目标

1. **Benchmark 复现**：在 7 个数据集 × 20 个模型上跑 EEG-FM-Compass Table 2 的
   「Cross-subject (LOSO) — Full fine-tuning」口径，得到可与论文 5 个 BNCI 列直接对照的数字，
   并把 WBCIC-SHU、SHU 2022 两列补上（论文没有）。
2. **跨数据集实验**：在上述数据集之间做训练/测试来自不同数据集的泛化实验。协议未定（§5）。

## 2. 范围

| 维度 | 在范围内 | 明确不做 |
|:---|:---|:---|
| 数据集 | BNCI2014001 / 004 / 2015001（MI）；BNCI2014009 / 008（P300）；WBCIC-SHU；SHU 2022 | CHB-MIT、TUAB、Sleep-EDFx、SEED 等其余 6 个论文数据集 |
| 模型 | Table 2 全部 20 条（8 specialist + 12 FM） | 自研模型、重新预训练 FM |
| 场景 | LOSO × full-FT（主）；LOSO × linear probing（次）；跨数据集 | within-subject few-shot（可选，排在最后） |
| 代码 | 官方仓库 + 我们的薄 adapter | 修改上游模型数学 |

## 3. 阶段

| 阶段 | 内容 | 完成判据 | 状态 |
|:---|:---|:---|:---|
| **P0 基建** | 目录骨架、规则文档、数据/模型卡片 ✅；EEG-FM-Benchmark + 17 个官方仓库 submodule 并 pin ✅；12 个 FM 权重 + sha256 manifest ✅（EEGPT 为镜像转换件 D-011；SingLEM 取论文时期原件 D-013）；conda 环境 `eegbench` ✅（D-009，GPU 节点导入检查全绿）；**20/20 模型带官方权重在 GPU 上 forward 通过** ✅；5 个 BNCI 数据集 82 文件下载并与 Table 14 核对一致 ✅（D-012） | 全部达成 | **✅ 完成 2026-09-14**（遗留待确认项见 §5 Q8–Q11） |
| **P1 数据** | 5 个 BNCI 经 MOABB 下载 → canonical；WBCIC-SHU、SHU 2022 从外部 processed npz → canonical（移植旧 loader，见 `LEGACY.md`）；生成 LOSO split 并 hash | 7 个 `data/canonical/*/v1/` 各带 manifest 与校验；split JSON 通过无泄漏测试 | pending |
| **P2 specialist benchmark** | 8 个 specialist × 7 数据集 × LOSO × 3 seeds | 5 个 BNCI 列与论文差距在可解释范围；summarizer 出表 | pending |
| **P3 FM benchmark** | 12 个 FM × 7 数据集 × full-FT（+ linear probing） | 同上；含 `weights` 校验、adapter 测试 | pending |
| **P4 跨数据集** | 按 §5 拍板的协议跑 | 协议写入 `PROTOCOLS.md` 并有 DECISIONS 记录后才开跑 | blocked：协议未定 |
| **P5 分析** | 与论文对照、排名、统计检验、报告 | `results/` 有完整表与 `REPORT.md` | pending |

顺序：P0 → P1 → P2 → P3 → P4 → P5。P2 先于 P3 是因为 specialist 便宜、能先校准数据与协议是否与论文一致。

## 4. 与论文对齐的不可变项 vs 我们的自由度

| 项 | 论文做法（§3.2–3.4） | 我们 |
|:---|:---|:---|
| 划分 | LOSO；MI/P300 BNCI 数据集**每被试只用单个 session**微调 | 复现时相同；WBCIC/SHU 选哪个 session 待定 |
| 重复 | 3 个随机 seed | 相同 |
| 报告点 | **final-epoch** 测试集指标 | 记录 final-epoch 与 best-val 两套，主表用 final-epoch |
| 超参 | 每模型单独调 | 直接沿用官方仓库配置；调参前必须记 DECISIONS |
| 主指标 | BCA；MI 加 Acc/κ；P300 加 AUC | 相同 |
| EA | 只给 EEGPT、MIRepNet | 相同 |
| 预处理 | 每 FM 按自己 Table 4 规范 | 相同，写在模型 YAML 的 `input_spec` |
| 硬件 | A800/A100 | 4090D 集群；batch 需按显存调整时记 DECISIONS |

## 5. 待决策（需用户拍板，未定前不产出被当作结果的数字）

| # | 问题 | 候选 | 影响 |
|:---|:---|:---|:---|
| Q1 | WBCIC-SHU 用 2C（51 人，L/R）还是 3C（11 人，L/R/feet）或两者 | 2C 与 BNCI2014004/SHU 标签空间一致，利于跨数据集；3C 与 BNCI2014001 子集一致 | 数据集数与跨数据集设计 |
| Q2 | WBCIC / SHU 的「单 session」微调选哪个 session | 第一 session（与论文对 BNCI 的常规一致）/ 全部 session | 与论文口径可比性 |
| Q3 | 模型选择依据 | final-epoch（论文）/ best-val | 主表口径 |
| Q4 | 跨数据集协议 | 见 `PROTOCOLS.md` §3 的 A/B/C 三类候选 | P4 全部设计 |
| Q5 | 通道统一策略（跨数据集必需） | 交集通道 / 插值到模板 / 依赖 FM 自带的通道机制 | 哪些模型能进跨数据集实验 |
| Q6 | 环境策略 | ~~单一 env / 每 FM 一 env~~ → **已定 D-009**：单一 `eegbench`（torch 2.7.1+cu128），冲突再拆 | — |
| Q7 | few-shot 场景是否做 | 做 / 不做 | 算力 |
| **Q8** | **LOSO full-FT 的逐模型超参**：官方仓库只发了 BNCI2014004 / 2015001 两套 `config/*.json`，其中 `Cross`（LOSO）条目仅 EEGMamba、LUNA 有 `full`，其余全是 Few-shot 或 head_only；另 3 个 BNCI 与我们 2 个数据集完全没有。README 明说"每个数据集×模型需自行搜索" | (a) 向作者要 Table 2 的 LOSO 配置（GitHub issue / 邮件 liudingkun@hust.edu.cn）；(b) 用 README 参考命令 + Few-shot JSON 作起点自行搜索并记 DECISIONS；(c) 两者并行 | 数字是否可与论文对照 |
| **Q9** | WBCIC-SHU / SHU 2022 的"单 session"取哪个 | 论文对 BNCI 的做法：4 套取第 1 个 session，BNCI2014004 取第 4 个（`3test`，带反馈，Table 14 的 1,400 只与它吻合）；没有可套用的规则 | 与 Q2 合并 |
| **Q10** | **MOABB 版本 / session 命名**：官方脚本用 `'0train'` 过滤 2015001 / 2014009 / 2014008，但 moabb 1.5.0 的命名是 `0A` / `0` / `0`（过滤得空集）；作者未 pin MOABB 版本 | (a) 问作者用的 moabb 版本并 pin；(b) 按"第 1 个 session"语义做映射并记 DECISIONS（Table 14 数字支持该语义） | P1 canonical 化的正确性 |
| **Q11** | EEGPT 官方权重比对：需你在浏览器打开 https://figshare.com/s/e37df4f8a907a866df4b 下载 `eegpt_mcae_58chs_4s_large4E.ckpt` 传到集群，我跑 `scripts/convert_eegpt_safetensors.py --compare` | 做 / 暂缓（EEGPT 数字带脚注） | EEGPT 是否可信 |

## 6. 风险

- 12 个 FM 的依赖互相冲突（mamba-ssm、特定 torch 版本）；权重下载渠道不稳定。
- BNCI2014008 P300 高度不平衡（33,600 trials），BCA 与 AUC 必须都算。
- FM 通道词表（19 ch 10-20、22 ch、16 ch）与 BNCI2014004 的 3 个双极通道不兼容——论文能跑说明官方 benchmark 有处理方式，拉代码后先查。
- SHU 2022 跨被试近 chance（旧项目实测），结果解读要标 chance band。
