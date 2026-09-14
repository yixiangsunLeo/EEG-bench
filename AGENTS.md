---
title: "AGENTS.md — eeg-fm-bench 灵魂记忆"
tags:
  - "#modality/eeg"
  - "#pipeline/5_dl_model"
  - "#method/benchmark"
  - "#method/foundation_model"
created: "2026-09-13"
updated: "2026-09-13"
status: "active"
---

# AGENTS.md — 唯一权威规则文件

> 任何 Agent / 人进入本项目先读本文件（5 分钟）。本文件只放**长期有效的规则与契约**。
> 「现在做到哪了」看 `progress.md` 顶部一条；「计划与待决策」看 `docs/PLAN.md`；
> 「为什么这样定」看 `docs/DECISIONS.md`。**历史、结果数字、临时状态一律不写进本文件。**

## 1. 项目身份

| 维度 | 内容 |
|:---|:---|
| 项目 | **eeg-fm-bench**：EEG 基础模型（FM）与专用模型的统一 benchmark + 跨数据集泛化实验 |
| 参考论文 | EEG-FM-Compass（Liu et al., NSR 2026, arXiv:2601.17883v3）；PDF 在 `docs/papers/`；官方代码 https://github.com/Dingkun0817/EEG-FM-Benchmark |
| 第一目标 | 在 **7 个数据集**上复现论文 Table 2 的 **Cross-subject LOSO × Full fine-tuning** 口径：BNCI2014001 / BNCI2014004 / BNCI2015001 / BNCI2014009 / BNCI2014008 + WBCIC-SHU + SHU 2022 |
| 模型 | Table 2 全部 20 条：8 个 specialist（Traditional ML, EEGNet, ShallowConv, LMDA, CNN-T, Deformer, Conformer, TSception）+ 12 个 FM（BENDR, BIOT-6D, LaBraM, Neuro-GPT, EEGPT, CBraMod, TFM, BrainOmni-Tiny/Base, EEGMamba, SingLEM, LUNA-Base）。**只用作者官方代码与官方权重** |
| 第二目标 | 跨数据集实验（训练集/测试集来自不同数据集）。**协议未定**，候选方案见 `docs/PROTOCOLS.md` §3 |
| 论文对标数字 | `results/reference/eeg_fm_compass_table2_loso_fullft.csv`（从论文 Table 2 转录，别人的数字） |
| 前身 | `eeg-mi-online`（2026-06 ~ 08，跨 session / 跨被试 MI 研究）。已整体备份并删除，见 `docs/LEGACY.md` |

## 2. 设计原则（第一性原理）

1. **Canonical data layer**：每个数据集只做一次「raw → canonical」转换，落盘为版本化的
   `data/canonical/<dataset>/v<k>/`（`X[trials, ch, time] float32` 原生采样率 + 通道名 + 元数据 + 校验值）。
   训练代码**只读 canonical**，永不直接碰 raw。
2. **Model-side input adapter**：每个 FM 对采样率 / 滤波 / 归一化 / 通道词表 / patch 长度有各自要求
   （论文 Table 4）。这些属于**模型**而非数据集：`adapter(canonical_trial) -> model_input`，在模型 YAML 里声明。
   所有模型吃同一批 canonical trial，公平性由此保证。
3. **Protocol as data**：划分（LOSO / few-shot / cross-dataset）由确定性函数 `(dataset, protocol, seed) -> split.json`
   生成并带 hash；每个结果引用 split hash。换划分 = 换文件，不改代码。
4. **一个 trainer，配置驱动**：模型特有行为走 hook（自定义 loss / 冻结策略），不 fork trainer。
   微调模式 `full` / `linear_probe`（/ `lora` 预留）。每个 cell 只存 `best.pt` + `last.pt`，可断点续跑，
   `result.json` 是完成标记，`cell_signature` 守卫「换了配置却复用目录」。
5. **结果 = 原始 per-cell JSON + 保存的预测**；表格是派生物，由 summarizer 重算，**禁止手改数字**。
   同时记录 final-epoch（论文口径）与 best-val 两套指标，报告时再选。
6. **第三方代码隔离**：官方仓库以 git submodule 放 `third_party/<name>`，pin 到 commit；**不改上游文件**，
   必要修改放 `third_party/patches/` 或我们的 adapter 里。权重放外部 `weights/`，`MANIFEST.yaml` 记 URL+sha256+license。
7. **算力纪律**：重活走 Slurm；GPU 任务 CUDA 不可用必须 fail fast；先 smoke 再 full；job array 按 cell 并行。

## 3. 目录路由

| 路径 | 放什么 | 规则 |
|:---|:---|:---|
| `src/eegbench/` | 唯一代码包（`data / transforms / models / protocols / training / evaluation / cli`） | 分层职责见 `docs/ARCHITECTURE.md`；人工入口只有 `python -m eegbench.cli ...` |
| `configs/` | `paths.local.yaml`（本机，gitignore）+ `datasets/ models/ protocols/ experiments/` | 所有可运行配置都在这里；Python 里不许写绝对路径 |
| `third_party/` | 官方模型代码（submodule）+ `patches/` | 只读上游；见 `third_party/README.md` |
| `data/` | canonical 数据（或指向外部盘的 symlink） | gitignore；raw 永不进项目 |
| `weights/` | 预训练权重 + `MANIFEST.yaml` | gitignore；下载后必须校验 sha256 |
| `outputs/ checkpoints/ logs/` | run 产物 | gitignore；已完成 run 只读，复跑必须新 `run_id` |
| `results/` | 人读的汇总表（summarizer 生成）+ `reference/` 论文数字 | git 跟踪；只放 CSV/MD/PNG |
| `docs/` | PLAN / ARCHITECTURE / PROTOCOLS / DATASETS / MODELS / DECISIONS / LEGACY / papers | 见 §6 |
| `scripts/` | Slurm 模板、一次性脚本 | 能进 `cli` 的功能不要留在 scripts |
| `tests/` | pytest；contract 测试优先（adapter 输入输出形状、split 无泄漏、resume 幂等） | 新 adapter / 新协议必须带测试 |

## 4. 硬边界

1. 只在本仓库根目录内写文件；外部 raw 目录**只读**（禁止改名/删除/写入）。
2. 外部路径只出现在 `configs/paths.local.yaml`（gitignore）；仓库里只有 `paths.example.yaml`。
3. 不编造结果；未落盘的东西只能写 planned/pending，不能写 done。
4. 不覆盖已完成的 run；不删 `checkpoints/outputs` 里别人的产物，除非用户明确要求。
5. 第三方上游代码不改；官方权重不重训不微调后冒充官方。
6. 登录节点不跑训练/预处理重活。

## 5. 实验规则

1. 按**被试**划分，绝不按 trial 泄漏；验证集只从训练被试里切；测试被试的数据不参与任何模型选择。
2. 论文口径 = LOSO、MI/P300 数据集每被试只用**单个 session** 微调、3 个 seed、final-epoch 测试指标、
   每模型单独调超参、主指标 BCA。**复现时先按论文口径，偏离必须写进 `docs/DECISIONS.md`。**
3. 归一化 / 对齐（z-score、EA…）只用训练侧统计量或 per-trial fit-free 方式；EA 只给原实现用 EA 的模型（EEGPT、MIRepNet）。
4. 每个 cell 记录：seed、split hash、canonical 数据版本、模型 YAML、训练配方、git commit、环境指纹、硬件。
5. 指标：BCA（主）、Accuracy、Cohen's κ、macro-F1；P300 加 AUC。标准差用样本标准差（÷n−1）。
6. 跨模型比较只在同一 `run_id`（同划分、同 canonical 版本）内进行。

## 6. 文档纪律（只维护 4 个活文档）

| 文档 | 何时改 |
|:---|:---|
| `AGENTS.md` | **规则或契约**变了才改；不记状态 |
| `progress.md` | 每次实质动作追加一条（最新在上，含日期）；这是唯一的流水 |
| `docs/PLAN.md` | 阶段状态、范围、待决策清单变了就改 |
| `docs/DECISIONS.md` | 每个影响结果口径的决定：一条编号记录（背景 / 决定 / 后果） |

其余 `docs/*.md` 是参考卡片，按需更新。**不再维护** FILE_CATALOG / operation_log / STATUS 之类的镜像文档
——目录变化看 `git log`，状态看 `progress.md`。README 只在根目录与 `src/ configs/ third_party/ data/ weights/ results/ scripts/ tests/`。

根目录与 `docs/` 下的 Markdown 带 YAML frontmatter（title / tags / created / updated / status）；目录级 README 不强制。文件名无空格、snake_case；CSV 表头英文 snake_case。

## 7. 禁止事项

- 不把历史叙事、结果数字、临时 TODO 堆进本文件。
- 不为了「跑通」改 FM 的输入规范（采样率 / 通道 / 归一化）而不记录；那会让数字与论文不可比。
- 不在协议未定前把任何跨数据集数字写成结论。
- 不引入第二个 trainer / 第二套结果格式。

## 8. 交接信息

- 前身项目备份：`/share/home/yuan/SYX_backup_2026-09-13.tar.gz`（sha256 见同名 `.sha256`），GitHub `stevencummings341-prog/EEG`（main，已同步）。可复用的旧代码路径见 `docs/LEGACY.md`。
- 两个自有数据集的 processed npz 仍在外部盘（`/share/workspace2/moto_imagination/{WBCIC_SHU,SHU}/processed/`），未受清理影响；见 `docs/DATASETS.md`。
- 集群：Slurm，GPU 分区 gpu2node / gpu3node，conda 环境 `mi_torch_cu118`（共享，勿改）；FM 各自依赖冲突时另建环境，记录在 `environment.yml` 注释与 `docs/DECISIONS.md`。
