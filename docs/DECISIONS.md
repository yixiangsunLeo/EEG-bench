---
title: "DECISIONS — 决定记录"
tags:
  - "#modality/eeg"
  - "#pipeline/5_dl_model"
created: "2026-09-13"
updated: "2026-09-13"
status: "active"
---

# DECISIONS

> 每条：编号 — 日期 — 背景 — 决定 — 后果。影响结果口径的决定必须在这里有一条。待决策项见 `PLAN.md` §5。

## D-001 · 2026-09-13 · 新建独立仓库，不延续 eeg-mi-online
- 背景：旧项目的研究问题（跨 session 修复、S4/DINO 融合）已放弃；旧仓库 29 KB 的 AGENTS.md 与 5 份镜像文档积累了大量过期状态。
- 决定：新建 `eeg-fm-bench`，独立 git 仓库；旧项目整体打包备份 + GitHub 保留，可按 `LEGACY.md` 按需取回文件。
- 后果：旧代码不自动可用；WBCIC/SHU 的 loader 需要移植（约半天）。

## D-002 · 2026-09-13 · 代码放 `src/eegbench/` 包，配置放 `configs/`
- 背景：旧项目 `code/` 与 stdlib 同名、只能从仓库根 `from code.x import`；模型参数散在多处。
- 决定：标准 src 布局，`pip install -e .`；每模型一份 YAML，`roster.yaml` 是总表。
- 后果：任何目录都能 import；配置有单一来源。

## D-003 · 2026-09-13 · 只维护 4 个活文档
- 背景：旧项目要求每次改动同步 6 处文档，结果互相不一致，最终结果表要从原始 JSON 重算。
- 决定：`AGENTS.md`（规则）/ `progress.md`（流水）/ `docs/PLAN.md`（阶段与待决策）/ `docs/DECISIONS.md`（本文件）。不再维护 FILE_CATALOG、operation_log、STATUS。
- 后果：目录变化靠 git log；README 只在关键目录。

## D-004 · 2026-09-13 · canonical 数据层 + 模型侧 input adapter
- 背景：12 个 FM 的采样率、滤波、归一化、通道词表各不相同（论文 Table 4）；若把这些做进数据集，会出现 N×M 个预处理版本。
- 决定：数据集只产出一份原生采样率、未滤波的 canonical；每个模型在 YAML 里声明 `input_spec`，由 `transforms` 在线执行。
- 后果：公平性有保证；训练时多一点 CPU 开销（可缓存）。

## D-005 · 2026-09-13 · 官方代码以 git submodule 隔离，权重带 sha256 manifest
- 背景：旧项目把官方 Keras/PyTorch 代码 vendored 进仓库，难以追溯版本。
- 决定：`third_party/<name>` pin commit；不改上游，改动走 patch 或 adapter；`weights/MANIFEST.yaml` 记录 url/sha256/license。
- 后果：clone 需 `--recurse-submodules`；权重下载后 `cli doctor` 校验。

## D-006 · 2026-09-13 · 同时记录 final-epoch 与 best-val 指标
- 背景：论文报 final-epoch；我们的习惯是 best-val。两者差异可能改变排名（旧项目实测配方能改变模型排名）。
- 决定：`result.json` 两套都存，主表口径由 PLAN Q3 拍板后固定；预测文件两套都存。
- 后果：存储 ×2（小）；换口径无需重跑。

## D-007 · 2026-09-13 · 先 specialist 再 FM
- 背景：specialist 便宜，能先校准数据 canonical 化与 LOSO 划分是否与论文一致。
- 决定：P2（8 specialist）先于 P3（12 FM）。
- 后果：若 P2 的 BNCI 数字与论文差距无法解释，先修数据/协议再进 P3。

## D-009 · 2026-09-14 · 单一环境 `eegbench`：Python 3.10 + torch 2.7.1+cu128
- 背景：论文仓库一份 `requirements.txt` 覆盖全部 20 个模型（含 mamba-ssm、deepspeed、linear-attention-transformer 等），说明作者用单一环境跑通；集群驱动 CUDA 12.8；用户 pip 缓存里已有为 torch 2.7.1+cu128 编好的 `mamba_ssm-2.3.1` wheel，登录节点无 GPU 无法编译。
- 决定：先建单一 conda 环境 `eegbench`（`scripts/setup_env.sh`），torch 选 cu128（匹配驱动 CUDA 12.8）；共享环境 `mi_torch_cu118` 不动。若某模型依赖冲突，再为其单建 `envs/<key>.yml`（PLAN Q6 由此收敛为「单 env 优先，冲突再拆」）。
- 实施记录（2026-09-14）：① 缓存里的 mamba wheel 实为 GitHub 预编译件，需 glibc≥2.32，集群 RHEL 8 只有 2.28 → mamba-ssm 2.3.1 与 causal-conv1d 1.7.0（Mamba 快速路径断言需要；EEGMamba README 指向 Mamba 官方安装说明）在 GPU 节点用 `module gcc/13.4.0 + cuda/12.8` 从官方源码编译（系统 gcc 8.5 编译失败），见 `scripts/slurm/build_mamba.sbatch`；② LUNA loader 依赖 `torcheeg`（上游 requirements 漏列），其 `scipy<=1.10.1` pin 与 mne/moabb 冲突，故 `--no-deps` 安装并单独补齐其余依赖，LUNA 只用到其中一个常量；③ moabb 解析为 1.5.0（满足 `>=1.0`），但其 session 命名与官方数据脚本的过滤字符串不一致（PLAN Q10）。
- 后果：EEGMamba 的 CUDA kernel 只能在 GPU 节点验证；CPU 上 forward 不可用。`pip check` 留有 torcheeg/scipy 一条名义冲突。

## D-010 · 2026-09-14 · 官方代码以 EEG-FM-Benchmark 为主实现，各官方仓库作 provenance
- 背景：论文仓库已 vendored 全部模型代码并提供统一 `run_finetuning.py`；各官方仓库主要提供权重与对照。
- 决定：`third_party/eeg_fm_benchmark` 是模型实现的第一来源（我们的 adapter 包装它的 `models/{DL,FM,ML}` loader）；17 个官方仓库作为 submodule 保留，用于权重来源、版本核对与差异审查。CNN-Transformer 无官方仓库，只有 benchmark 内实现。
- 后果：复现口径与论文一致；若 benchmark 的 vendored 代码与官方仓库有差异，以论文数字对应的 benchmark 版本为准并记录。

## D-011 · 2026-09-14 · EEGPT 权重暂用 HF 第三方转换件
- 背景：官方 `eegpt_mcae_58chs_4s_large4E.ckpt` 只在 figshare 私有链接（需浏览器，API 拒绝 token），集群无法脚本下载；`eeg-telecom-paris/eegpt-large-official` 是模块结构完全一致的 weights-only safetensors。
- 决定：先用转换件（`scripts/convert_eegpt_safetensors.py` → `eegpt.ckpt`），MANIFEST 标注 provenance；用户从浏览器取得官方文件后用 `--compare` 做逐张量比对。比对通过前 EEGPT 数字带脚注。
- 后果：EEGPT 是 12 个 FM 里唯一未经官方字节校验的权重。

## D-012 · 2026-09-14 · 数据集统一放在 `/share/workspace2/moto_imagination/`
- 背景：两个自有数据集已在该目录；用户要求新数据集与之放一起。
- 决定：`MNE_DATA=/share/workspace2/moto_imagination`（MOABB 会在其下建 `MNE-bnci-data/`）；canonical 输出到同目录 `eegbench_canonical/`，项目内 `data/` 只放 symlink。`configs/paths.local.yaml` 已写。下载完全走 MOABB 1.5.0 的数据集类与其默认主机（TU Graz），不覆盖 URL；仅为规避 NFS 小块写慢而先落本地 `/tmp` 再 rsync。
- 后果：项目目录不含数据；换机只改 `paths.local.yaml`。

## D-013 · 2026-09-14 · SingLEM 用论文时期的原始 checkpoint，子模块 pin 到改版前
- 背景：benchmark loader 读 `singlem_pretrained.pt`。SingLEM 官方仓库 2026-07-31 改版（commit `4d95929`）删除了该文件并发布**重训**的三个 checkpoint（`singlem_downstream_excluded.pt` 等，字节数不同：13,162,319 vs 13,177,518）。论文实验（2026-01 ~ 08）用的是旧文件。
- 决定：从 git 历史取回 `05abe21:weights/singlem_pretrained.pt`（sha256 `0e492189…`，与 blob 逐字节一致）作为 `weights/singlem_pretrained.pt`；`third_party/singlem` pin 到改版前最后一个 commit `05abe21`（2025-10-03）。重训版另存为 `singlem_downstream_excluded_rev2026-07-31.pt`（可选，仅供日后对比）。
- 后果：SingLEM 数字与论文可比；若日后要评估"新版 SingLEM"，需作为独立条目而非替换。

## D-008 · 2026-09-13 · 跨数据集协议未定前不开跑 P4
- 背景：通道统一策略与标签空间决定了哪些模型能参加，随意开跑会产生不可比数字。
- 决定：P4 blocked，直到 PLAN Q1/Q4/Q5 有答案并写入 `configs/protocols/`。
- 后果：P4 至少在 P2 之后。
