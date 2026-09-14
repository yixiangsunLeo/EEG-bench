---
title: "LEGACY — 前身项目 eeg-mi-online 的去向与可复用件"
tags:
  - "#modality/eeg"
created: "2026-09-13"
updated: "2026-09-13"
status: "active"
---

# LEGACY

## 1. 备份在哪

| 位置 | 内容 |
|:---|:---|
| `/share/home/yuan/SYX_backup_2026-09-13.tar.gz`（125 MB，15,589 条目） | 清理后的完整 `SYX/eeg-mi-online/`：全部代码、文档、git 历史、阶段结果表、`results_snapshot_2026-09-13/`（outputs 的非二进制结果层 383 MB） |
| 同名 `.sha256` | 校验值 |
| GitHub `stevencummings341-prog/EEG`（branch `main`） | 与备份时 HEAD `1e183c9` 一致 |
| `/share/workspace2/moto_imagination/{WBCIC_SHU,SHU}/processed/` | 两个自有数据集的 processed npz，**未删除，可直接用** |

已删除且不可恢复：41 G checkpoints、11 G `.npz` embeddings/predictions、日志、3C processed 数据（可重生成）。

取文件示例：

```bash
tar -xzf /share/home/yuan/SYX_backup_2026-09-13.tar.gz -C /tmp \
    SYX/eeg-mi-online/code/preprocessing/shu_mat.py
```

## 2. 值得移植的旧代码（tarball 内路径，前缀 `SYX/eeg-mi-online/`）

| 路径 | 用途 | 移植到 |
|:---|:---|:---|
| `code/preprocessing/shu_mat.py` + `scripts/preprocess_shu.py` | SHU 2022 `.mat` → npz（标签 {1,2}→{0,1}） | `src/eegbench/data/shu2022.py` |
| `code/preprocessing/wbci_3c_mat.py` + `scripts/preprocess_wbci_3c.py` | WBCIC-SHU 3C `.mat` → npz + manifest | `src/eegbench/data/wbcic_shu.py` |
| `code/datasets/` + `code/configs/datasets/*.yaml` | WBCIC 2C manifest 读取、通道数/采样率元数据 | 同上 |
| `code/training/e2e_trainer.py` | best/last checkpoint、断点续跑、`cell_signature` 守卫、test 不参与选择的守卫 | `src/eegbench/training/trainer.py`（重写，借模式不搬代码） |
| `code/experiments/cross_subject_protocols.py` | 被试级 LOSO / k-fold / holdout + 泄漏断言 | `src/eegbench/protocols/` |
| `code/summaries/cross_subject_bench.py` | 配对 Wilcoxon+Holm、Friedman+Nemenyi CD 图 | `src/eegbench/evaluation/stats.py` |
| `code/models/paper_baselines/` | EEGNet / EEGNeX / EEG-Deformer / ATCNet 的官方代码移植与出处说明 | 参考；本项目一律走 `third_party/` submodule |
| `scripts/slurm/submit_bench.sh`, `_common.sh` | 4 卡分组 + 48 h 自动重投链 | `scripts/slurm/` |

## 3. 旧结果在哪（只供回看，不进本项目结果）

- `docs/RESULTS_TRUTH.md`：WBCIC-SHU 3C 跨被试权威表（ATCNet / EEGNeX / EEG-Deformer / S4ERP / EEGNet / DualCD 系列）。
- `results_snapshot_2026-09-13/experiments/{wbci_shu,shu}/<run_id>/`：各 run 的 `tables/`、`cells/**/result.json`、`runs/*.csv`。
- `1_session_drift/ 2_baseline/ 4_experiments/`：Phase 0–2c 跨 session 研究结果与 AI 分析。

## 4. 从旧项目带过来的经验（已写进 AGENTS/ARCHITECTURE）

1. 训练配方会改变模型排名；跨 run 不比较。
2. 表格必须能从原始 `result.json` 重算；文档里的数字出过错。
3. test 集绝不参与模型选择，需要代码守卫而非口头约定。
4. SHU 2022 跨被试近 chance；WBCIC 2C 与 3C 是互斥被试队列。
5. 镜像文档越多越不同步。

## 5. 清理当天的异常

2026-09-13 清理期间 `SYX/ssvep_10hz/`（公开 Tsinghua SSVEP benchmark 数据 + 2 个绘图脚本 + 图/xlsx）与根目录一篇 PDF（Subject-Independent Deep Learning Framework for MI-EEG…）消失。本项目的删除命令未涉及它们（已在 `/tmp` 复刻目录回放验证），文件系统无快照。若需要，数据与论文均可公开重新下载。
