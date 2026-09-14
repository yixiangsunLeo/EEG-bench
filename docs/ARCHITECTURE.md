---
title: "ARCHITECTURE — 目录、数据流、契约"
tags:
  - "#modality/eeg"
  - "#pipeline/5_dl_model"
created: "2026-09-13"
updated: "2026-09-13"
status: "active"
---

# ARCHITECTURE

## 1. 数据流

```text
raw (外部盘, 只读)                       官方仓库 third_party/<model> (只读)
      │ prepare (一次, 版本化)                       │ 我们的薄 adapter
      ▼                                             ▼
data/canonical/<dataset>/v<k>/  ──►  transforms  ──►  models/<model>  ──►  logits
  X[trials,ch,time] @native fs        (按模型 YAML                           │
  + channels + meta + sha256           input_spec 执行)                      ▼
      │                                                  outputs/<run_id>/<cell>/result.json + predictions.npz
      │ split (确定性, hash)                                                │
      ▼                                                                      ▼ summarize
outputs/<run_id>/splits/<dataset>__<protocol>__seed<k>.json         results/<run_id>/*.csv|md|png
```

关键分界：**数据集只负责给出 canonical trial；模型负责把 canonical trial 变成自己要的输入。**

## 2. 包分层 `src/eegbench/`

| 子包 | 职责 | 不做什么 |
|:---|:---|:---|
| `data/` | 数据集注册表；`prepare_<dataset>()`：raw/MOABB → canonical；canonical 读写与校验 | 不做滤波/重采样（那是模型侧） |
| `transforms/` | 纯函数：resample、bandpass/notch、channel select/map/interpolate、z-score / minmax / percentile、EA、patchify | 不持有状态（EA 的参考矩阵由调用方按划分算好传入） |
| `models/` | `base.py` 统一接口；`registry.py` 按 key 构建；`<model>/adapter.py` 包装 `third_party/<model>`，声明 `input_spec` 并实现 head | 不复制上游模型代码 |
| `protocols/` | split 生成器：`loso_single_session`、`loso_all_sessions`、`few_shot_within`、`cross_dataset_*`；hash；泄漏断言 | 不读模型 |
| `training/` | 唯一 trainer：full / linear_probe（/ lora）；best+last checkpoint；resume；cell_signature；final-epoch 与 best-val 双记录 | 不含模型特有 loss（走 hook） |
| `evaluation/` | 指标（BCA/Acc/κ/F1/AUC）；summarizer：`result.json` → 表；统计检验（配对 Wilcoxon+Holm、Friedman+Nemenyi） | 不手写数字 |
| `cli.py` | `prepare / split / train / summarize / doctor` | 业务逻辑不写在 cli |

## 3. 契约

### 3.1 canonical 数据 `data/canonical/<dataset>/v<k>/`

```text
manifest.json     # dataset key, version, sfreq, channel_names(10-20 名), class_names, units(µV), sha256 per file, 生成命令+git commit
sub-<id>/ses-<id>.npz   # X float32 [n_trials, n_ch, n_times] (原生 fs, 未滤波或只保留数据集自带滤波), y int64 [n_trials], trial_meta (run/onset 等)
```

- 通道名统一为 10-20 标准名；双极通道写作 `C3-Cz` 形式并在 manifest 标 `montage: bipolar`。
- 版本号只在转换逻辑变化时递增；旧版本目录不删。
- 两个自有数据集（WBCIC-SHU、SHU 2022）从外部 processed npz 转换而来，转换脚本必须记录来源 manifest 的 sha256。

### 3.2 模型接口 `models/base.py`

```python
class EEGModel(nn.Module):
    input_spec: InputSpec      # sfreq, band, notch, norm, channel_policy, window_s, patch_s ...（来自模型 YAML）
    def forward(self, x: Tensor, meta: BatchMeta) -> Tensor: ...   # logits [B, n_classes]
    def trainable_parameters(self, mode: Literal["full","linear_probe","lora"]) -> Iterable[Parameter]: ...
    # 可选 hook：compute_loss(...) / on_after_step(...)
```

- adapter 负责：加载官方权重（校验 sha256）→ 构造 head → 声明 `input_spec`。
- `InputSpec` 由 `transforms` 解释执行；同一模型在所有数据集上 `input_spec` 相同（否则记 DECISIONS）。

### 3.3 split JSON

```json
{"dataset":"bnci2014001","protocol":"loso_single_session","seed":0,"canonical_version":"v1",
 "folds":[{"fold":0,"test_subjects":["01"],"train_subjects":[...],"val_subjects":[...],
           "train_sessions":{"02":["0train"]},"test_sessions":{"01":["0train","1test"]}}],
 "hash":"sha256:..."}
```

- 泄漏断言：`test ∩ (train ∪ val) = ∅`（按被试）；跨数据集协议再加「数据集级」断言。

### 3.4 result.json（每 cell 一份，是完成标记）

```json
{"run_id":"...","cell":"<dataset>__<model>__<protocol>__fold<k>__seed<s>","split_hash":"...",
 "canonical_version":"v1","model_config_hash":"...","git_commit":"...","env_fingerprint":{...},
 "final_epoch":{"bca":..,"acc":..,"kappa":..,"macro_f1":..,"auc":..},
 "best_val":{"epoch":..,"bca":..,...},"n_epochs":..,"wall_time_s":..,"hardware":"..."}
```

`predictions.npz`：per-trial `y_true / y_pred / proba / trial_id` 两套（final、best）。

### 3.5 命名

- `run_id`：`<experiment>_v<k>`，如 `bench_loso_mi_v1`；已完成的 run 只读。
- cell：`<dataset>__<model>__<protocol>__fold<k>__seed<s>`；checkpoints 同名目录下 `best.pt` / `last.pt`。
- 模型 key：小写 snake_case，与 `configs/models/roster.yaml` 一致（如 `cbramod`、`brainomni_base`）。

## 4. 第三方代码与权重

- `third_party/<name>`：git submodule，pin commit；`third_party/README.md` 记来源与 commit。
- 上游需要改动时：优先在 adapter 里 monkeypatch；不行则 `third_party/patches/<name>.patch` + 说明。
- `weights/MANIFEST.yaml`：`{model_key: {file, url, sha256, license, source_commit}}`；`cli doctor` 校验。

## 5. 为什么这样设计（对旧项目的修正）

- 旧项目结果表分散在 `outputs/`、阶段目录、多份 md，最后不得不从 `result.json` 重算权威表 → 现在 **表只由 summarizer 生成**。
- 旧项目 5 份镜像文档（FILE_CATALOG / operation_log / STATUS / ARCHITECTURE / progress）互相不同步 → 现在只有 4 个活文档。
- 旧项目 `code/` 目录名与 stdlib 冲突、模型配置散在多处 → `src/eegbench` 包 + 每模型一份 YAML。
- 旧项目发现「换配方会改变模型排名」→ 现在配方、split、canonical 版本全部进 `result.json`，跨 run 不比较。
