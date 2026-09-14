---
title: "eeg-fm-bench"
tags:
  - "#modality/eeg"
  - "#pipeline/5_dl_model"
  - "#method/benchmark"
created: "2026-09-13"
updated: "2026-09-13"
status: "active"
---

# eeg-fm-bench

EEG 基础模型（FM）× 专用模型的统一 benchmark 与跨数据集泛化实验。
参考 **EEG-FM-Compass**（Liu et al., NSR 2026, arXiv:2601.17883v3；官方代码
[Dingkun0817/EEG-FM-Benchmark](https://github.com/Dingkun0817/EEG-FM-Benchmark)）Table 2 的
Cross-subject LOSO × Full fine-tuning 口径。

- **数据集（7）**：BNCI2014001 / BNCI2014004 / BNCI2015001（MI），BNCI2014009 / BNCI2014008（P300），
  WBCIC-SHU（MI），SHU 2022（MI）。卡片见 `docs/DATASETS.md`。
- **模型（20）**：8 specialist + 12 FM，全部用作者官方代码与权重。名册见 `docs/MODELS.md` / `configs/models/roster.yaml`。
- **协议**：先复现论文 LOSO 口径，再做跨数据集；细节待定，见 `docs/PROTOCOLS.md`。
- **状态**：2026-09-13 建立骨架；代码与数据尚未拉取。看 `progress.md` 顶部。

## 目录

```text
eeg-fm-bench/
├── AGENTS.md            # 唯一权威规则（先读）
├── progress.md          # 流水日志，最新在上
├── docs/                # PLAN / ARCHITECTURE / PROTOCOLS / DATASETS / MODELS / DECISIONS / LEGACY / papers
├── configs/             # paths.example.yaml + datasets/ models/ protocols/ experiments/
├── src/eegbench/        # 唯一代码包：data transforms models protocols training evaluation cli
├── third_party/         # 官方模型代码（git submodule，pin commit）+ patches/
├── data/  weights/      # canonical 数据 / 预训练权重（gitignore，可 symlink 到外部盘）
├── outputs/ checkpoints/ logs/   # run 产物（gitignore）
├── results/             # 汇总表（git 跟踪）+ reference/ 论文数字
├── scripts/slurm/       # 提交模板
└── tests/
```

## 入口（规划中，尚未实现）

```bash
python -m eegbench.cli prepare   --dataset bnci2014001            # raw -> canonical
python -m eegbench.cli split     --protocol loso_single_session --dataset bnci2014001
python -m eegbench.cli train     --experiment configs/experiments/<name>.yaml [--cells ...]
python -m eegbench.cli summarize --experiment configs/experiments/<name>.yaml
```

环境：集群共享 conda `mi_torch_cu118`（不改）；FM 依赖冲突时另建环境，见 `environment.yml` 注释。
