---
title: "progress.md — 流水日志"
tags:
  - "#modality/eeg"
  - "#pipeline/5_dl_model"
created: "2026-09-13"
updated: "2026-09-13"
status: "active"
---

# progress.md

> 最新在上。每条：日期 — 做了什么 — 产物在哪 — 下一步。只记事实，不记推测。

## 2026-09-14 — P0 基建：官方代码、权重、环境、BNCI 数据

**做了什么**

1. **代码**：`third_party/eeg_fm_benchmark`（论文官方 pipeline，commit `680b12b`）+ 17 个官方仓库全部以
   submodule 拉取并 pin（`--depth 1`），清单与 commit 见 `third_party/README.md`。发现 benchmark 仓库已
   vendored 全部 20 个模型的实现、MOABB 数据脚本、以及 BNCI2014004 / BNCI2015001 的逐模型超参 JSON（`config/`）。
2. **权重**：`scripts/download_weights.py` 收齐 12 个 FM 的 checkpoint 到 `weights/`（1.7 GB，文件名与
   benchmark `models/pretrained_models/` 一致），sha256 写入 `weights/MANIFEST.yaml`。来源：GitHub release（BENDR）、
   官方仓库内置（BIOT、LaBraM、SingLEM、TFM）、Hugging Face 经 `hf-mirror.com`（Neuro-GPT、CBraMod、EEGMamba、
   BrainOmni ×3、LUNA）。**EEGPT 用 HF 第三方转换件**（figshare 私链需浏览器），D-011；`scripts/convert_eegpt_safetensors.py`
   负责还原成 `eegpt.ckpt` 并支持与官方文件比对。
3. **环境**：`scripts/setup_env.sh` 建 conda `eegbench`（py3.10 + torch 2.7.1+cu128 + benchmark requirements），D-009。
4. **数据**：`configs/paths.local.yaml` 已写，`MNE_DATA=/share/workspace2/moto_imagination`（与 WBCIC_SHU、SHU 并列），
   canonical 输出 `.../eegbench_canonical/`，D-012。`scripts/download_bnci.py` 用 MOABB 1.5.0 自带的数据集类下载 5 套 BNCI，
   **未覆盖任何 URL**：moabb 1.5.0 的 `bnci/base.py` 默认主机已是 TU Graz `https://lampx.tugraz.at/~bci/database/`（可达）。
   pooch 直写 NFS 只有 ~30 KB/s，改为 `--staging /tmp/...` 本地暂存 + 五路并行 + rsync 到最终位置（布局由 MOABB 生成）。
   链路约 280 KB/s，预计 1–2 小时。
5. 网络事实：huggingface.co、drive.google.com、bnci-horizon-2020.eu、figshare（JS 质询）不可达；GitHub、hf-mirror.com、
   lampx.tugraz.at 可达。
6. **SingLEM 权重修正（D-013）**：benchmark 读的 `singlem_pretrained.pt` 是 SingLEM 原始发布件，2026-07-31 上游改版后
   被删并换成重训版。已从子模块 git 历史取回（`05abe21:weights/singlem_pretrained.pt`，sha256 与 blob 一致），子模块 pin 到 `05abe21`。
7. **环境事实**：torch 2.7.1+cu128 + benchmark requirements 全部装好；`torcheeg`（LUNA 需要、上游 requirements 漏列）以
   `--no-deps` 安装以避开其 `scipy<=1.10.1` 的 pin；mamba-ssm 的 GitHub 预编译 wheel 需 glibc≥2.32（集群 2.28）→ 用
   `scripts/slurm/build_mamba.sbatch` 在 GPU 节点从官方源码编译。

**验证**（GPU 节点 gpu02，RTX 4090 D；Slurm 62567 / 62578 / 62590）：CUDA 可用；导入检查 25/25 通过（含 deepspeed、
mamba_ssm）；`scripts/smoke_models.py --device cuda` **19/19 深度模型带官方权重 forward 通过**，CSP_LDA / Xdawn_LDA 可导入
——即 Table 2 的 20 条全部可运行。参数量与 Table 52 一致或差异可解释（EEGPT `target_encoder` 25.3 M ↔ 25 M；BrainOmni
含 tokenizer；Conformer 的 LazyLinear 头随输入长度变）。
**数据**：BNCI 五套 82 个 `.mat`（3.4 GB）全部落在 `/share/workspace2/moto_imagination/MNE-bnci-data/`，`scripts/verify_bnci.py`
用 MOABB loader 核对：被试数 / 通道数 / 采样率全部与 Table 14 一致，Table 14 的试次数恰等于官方脚本所取单 session 的试次
（详见 `docs/DATASETS.md` §2.5）。pooch 单流约 30 KB/s 且连接 ~13 分钟被掐断，最终改为 MOABB 枚举文件清单 + `curl -C -` 六路续传
（聚合 ~8 MB/s）。`~/.mne` 持久配置尚未写（`python scripts/download_bnci.py --finalize`，一条命令，留给用户）。

**P0 完成。下一步**：用户拍板 PLAN §5（Q1–Q5、Q7–Q11，Q6 已定）→ P1 写 `eegbench prepare`（MOABB → canonical；
WBCIC/SHU processed npz → canonical）与 LOSO split。

## 2026-09-13 — 推倒重来：备份旧项目、建立 eeg-fm-bench 骨架

**做了什么**

1. 旧项目 `eeg-mi-online` 清理后整体打包：`/share/home/yuan/SYX_backup_2026-09-13.tar.gz`
   （125 MB，15,589 条目，sha256 见同名 `.sha256`）。打包前删除了 41 G 权重、14 G outputs、
   日志与旧 backup 权重；`outputs/` 的非二进制结果层（CSV/JSON/PNG，383 MB）保留在包内
   `SYX/eeg-mi-online/results_snapshot_2026-09-13/`。GitHub `stevencummings341-prog/EEG` 与本地 HEAD 一致。
2. 确认备份后删除 `SYX/eeg-mi-online/` 全部内容。
3. 新建 `SYX/eeg-fm-bench/`：目录骨架、`AGENTS.md`（重写，只留规则）、`CLAUDE.md`、`.cursor/rules/`、
   `docs/{PLAN,ARCHITECTURE,PROTOCOLS,DATASETS,MODELS,DECISIONS,LEGACY}.md`、7 个数据集卡片 YAML、
   模型名册 `configs/models/roster.yaml`、论文 Table 2 转录 `results/reference/eeg_fm_compass_table2_loso_fullft.csv`、
   `pyproject.toml` / `.gitignore` / `environment.yml`。参考论文 PDF 移入 `docs/papers/`。
4. `git init`（branch `main`）并 stage 全部 54 个文件；**首个 commit 未做**——本机没有 git 全局身份，
   需用户执行 `git -c user.name=... -c user.email=... commit -m "Bootstrap eeg-fm-bench"`（或先 `git config user.*`）。
5. **未做**：未拉取任何官方代码、未下载数据集与权重、未写任何实现代码（只有包骨架与契约文档）。

**异常记录**：清理过程中 `SYX/ssvep_10hz/` 与根目录一篇 PDF 消失，本项目的删除命令未涉及它们
（已用复刻目录回放验证）；无文件系统快照可恢复。SSVEP 材料为公开 Tsinghua benchmark 数据 + 两个绘图脚本。

**下一步**：按 `docs/PLAN.md` P0 → 用户拍板 `docs/PLAN.md` §5 的待决策项；然后拉取
EEG-FM-Benchmark 代码、建环境、把 7 个数据集转成 canonical。
