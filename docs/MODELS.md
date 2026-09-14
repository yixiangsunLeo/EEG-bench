---
title: "MODELS — 20 个模型名册"
tags:
  - "#modality/eeg"
  - "#pipeline/5_dl_model"
  - "#method/foundation_model"
created: "2026-09-13"
updated: "2026-09-13"
status: "active"
---

# MODELS

> 机器可读版在 `configs/models/roster.yaml`；每个模型接入时再建 `configs/models/<key>.yaml`。
> 参数量与总排名来自论文 Table 52（13 数据集 × LOSO+few-shot 的平均名次）；输入规范来自 Table 4。
> 官方仓库与 pin 的 commit 见 `third_party/README.md`（2026-09-14 已全部拉取）；权重来源与 sha256 见 `weights/MANIFEST.yaml` / `weights/README.md`。
> **实现以 `third_party/eeg_fm_benchmark/models/{DL,FM,ML}` 为准**（论文作者 vendored 的版本，D-010）；各官方仓库作 provenance 对照。

## 1. Specialist（从零训练，用数据集原生输入）

| key | 名称 | 类型 | 参数量 | 论文总排名 | 备注 |
|:---|:---|:---|---:|---:|:---|
| `traditional_ml` | Traditional ML | 范式专用 ML | – | 11 | MI：CSP+LDA；P300：xDAWN+LDA。无 seed 方差 |
| `eegnet` | EEGNet | CNN | 2 K | 2 | |
| `shallowconv` | ShallowConvNet | CNN | 36 K | 4 | |
| `lmda` | LMDA-Net | CNN | 3 K | 6 | |
| `tsception` | TSception | CNN | 9 K | 8 | |
| `cnn_t` | CNN-Transformer | CNN+Transformer | 2.8 M | 14 | |
| `deformer` | EEG-Deformer | CNN+Transformer | 0.8 M | 5 | |
| `conformer` | EEG Conformer | CNN+Transformer | 0.16 M | 3 | |

## 2. Foundation models（官方权重 + 微调）

| key | 名称 | 预训练目标 | 参数量 | 总排名 | 重采样 | 滤波 | 归一化 | 通道映射 | patch / stride | EA | 备注 |
|:---|:---|:---|---:|---:|---:|:---|:---|:---|:---|:---:|:---|
| `bendr` | BENDR | Embedded tokens | 4.0 M | 12 | 256 | ≤120 Hz | →[-1,1] | 19 | 375 ms / 375 ms | – | 预训练 TUEG；下游曾用 BCIC-IV-2a（非预训练） |
| `biot_6d` | BIOT-6D | Embedded tokens | 3.2 M | 13 | 200 | – | x / P95(\|x\|) | 16（逐通道） | 1 s / 0.5 s | – | 另有 1D/2D 变体；预训练含 CHB-MIT、TUAB |
| `labram` | LaBraM | Codebook index | 5.8 M | 9 | 200 | 0.1–75 Hz + 50 Hz notch | →[-1,1] | 可学习通道 embedding | 1 s / 1 s | – | |
| `neuro_gpt` | Neuro-GPT | Embedded tokens | 0.16 M | 7 | 250 | 0.5–100 Hz + 60 Hz notch | z-score | 22 | 2 s / 1.8 s | – | 预训练含 TUAB |
| `eegpt` | EEGPT | Raw signals | 25 M | 15 | 256 | ≤38 / ≤30 / ≤120 Hz（按任务） | **EA** / CAR / z-score | 可学习通道 embedding | 250 ms / 250 ms | ✓ | 论文中 linear probing 有时优于 full-FT |
| `cbramod` | CBraMod | Raw signals | 4.0 M | **1** | 200 | 0.3–75 Hz + 60 Hz notch | →[-1,1] | 19 | 1 s / 1 s | – | 论文总排名第一；预训练含 TUAB |
| `tfm` | TFM（TFM-Tokenizer） | Codebook index | 1.9 M | 20 | 200 | 0.1–75 Hz + 50 Hz notch | – | 16（逐通道） | 1 s / 0.5 s | – | 预训练含 CHB-MIT、TUAB |
| `brainomni_tiny` | BrainOmni-Tiny | Codebook index | 8.4 M | 16 | 256 | 0.1–96 Hz + 50/60 Hz notch | z-score | 16 / 坐标感知 | 2 s / 1 s | – | 不支持双极 montage |
| `brainomni_base` | BrainOmni-Base | Codebook index | 33 M | 17 | 同上 | 同上 | 同上 | 同上 | 同上 | – | 同上 |
| `eegmamba` | EEGMamba | Raw signals | 3.3 M | 10 | 200 | 0.3–75 Hz + 50/60 Hz notch | →[-1,1] | – | 1 s / 1 s | – | 依赖 mamba-ssm，环境风险最高；预训练含 TUAB |
| `singlem` | SingLEM | Raw + frequency | 3.3 M | 19 | 128 | 0.5–50 Hz + 50 Hz notch | →(-1,1) | 1（单通道） | 1 s / 0.75 s | – | |
| `luna_base` | LUNA-Base | Embedded tokens | 7.0 M | 18 | 256 | 0.1–75 Hz + 50/60 Hz notch | z-score | 坐标感知 / 统一潜空间 | L=40 | – | TUAB 最强，其他范式弱；预训练含 TUAB |

可选：`mirepnet`（MI 专用 FM，250 Hz、8–32 Hz、zero-mean + EA、45 ch）——论文放在补充材料，MI 上表现最好；是否纳入待定。

## 3. 接入清单（每个模型）

1. ~~`third_party/<name>` submodule + pin commit；`weights/MANIFEST.yaml` 加条目并校验 sha256~~ ✅ 2026-09-14（全部 20 条）。
2. `src/eegbench/models/<key>/adapter.py`：包装 `eeg_fm_benchmark/models/**/Loader_<Model>.py`（把
   `utils.utils.get_pretrained_models_path` 重定向到 `weights/`）、声明 `input_spec`、实现 `trainable_parameters(mode)`。
3. `configs/models/<key>.yaml`：`input_spec` + 官方微调超参（lr / batch / epochs / optimizer）+ 出处。
4. `tests/models/test_<key>.py`：随机张量 forward 形状正确；`linear_probe` 模式下 encoder 参数 `requires_grad=False`。
5. 在 `docs/MODELS.md` 本表补「官方仓库 + commit」列。

## 4. 论文数字（对标用）

`results/reference/eeg_fm_compass_table2_loso_fullft.csv`：Table 2「Cross-subject (LOSO) — Full fine-tuning」全部 20 行 × 7 列
（含我们不做的 CHB-MIT、TUAB 两列，仅供完整性）。‡ = 该数据集在该 FM 预训练语料中。
