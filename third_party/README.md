# third_party/

Official repositories as **git submodules pinned to a commit** (added 2026-09-14 with `--depth 1`; use
`git submodule update --init --depth 1` when cloning). Nothing here is edited.

| submodule | upstream | pinned | used by | notes |
|:---|:---|:---|:---|:---|
| `eeg_fm_benchmark` | https://github.com/Dingkun0817/EEG-FM-Benchmark | `680b12b` (2026-08-11) | all | Paper's own pipeline: `models/{DL,FM,ML}` (all 20 Table-2 models vendored), `datasets/*/Preprocess_Dataset.py` (MOABB), `run_finetuning.py`, per-dataset hyperparameter JSONs in `config/` (only BNCI2014004 / BNCI2015001 shipped). Expects weights under `models/pretrained_models/` — we keep them in `weights/` with identical relative names |
| `eegnet_arl` | https://github.com/vlawhern/arl-eegmodels | `4a512e5` | eegnet | Keras reference; benchmark has a PyTorch port |
| `braindecode` | https://github.com/braindecode/braindecode | `adaa63a` | shallowconv | `ShallowFBCSPNet` reference |
| `eeg_deformer` | https://github.com/yi-ding-cs/EEG-Deformer | `47df1c4` | deformer | |
| `eeg_conformer` | https://github.com/eeyhsong/EEG-Conformer | `9ae149b` | conformer | |
| `lmda` | https://github.com/MiaoZhengQing/LMDA-Code | `c54f209` | lmda | |
| `tsception` | https://github.com/yi-ding-cs/TSception | `9efd666` | tsception | |
| `labram` | https://github.com/935963004/LaBraM | `c431221` | labram | bundles `checkpoints/labram-base.pth` (96.6 MB) + `vqnsp.pth` |
| `bendr` | https://github.com/SPOClab-ca/BENDR | `ac918ab` | bendr | weights = GitHub release `v0.1-alpha` (`encoder.pt`, `contextualizer.pt`) |
| `neurogpt` | https://github.com/wenhui0206/NeuroGPT | `230571d` | neuro_gpt | weights on HF `wenhuic/Neuro-GPT` |
| `brainomni` | https://github.com/OpenTSLab/BrainOmni | `340d6b5` | brainomni_tiny/base | weights on HF `OpenTSLab/BrainOmni` (tiny / base / braintokenizer) |
| `biofoundation_luna` | https://github.com/pulp-bio/BioFoundation | `f7e9437` | luna_base | weights on HF `PulpBio/LUNA` (CC BY-ND 4.0) |
| `eegmamba` | https://github.com/wjq-learning/EEGMamba | `dbc83fa` | eegmamba | weights on HF `weighting666/EEGMamba`; needs `mamba-ssm` |
| `singlem` | https://github.com/ttlabtuat/SingLEM | **`05abe21`** (2025-10-03, last pre-revision; full history fetched) | singlem | Pinned to the paper-era release: it carries `weights/singlem_pretrained.pt` that the benchmark loads. The 2026-07-31 revision (`4d95929` → HEAD `6db5b5a`) deleted it and shipped *retrained* checkpoints (`SingLEM/checkpoints/*.pt`, different bytes) — see D-013. Revised corpus notes list `WBCIC_MI_23` — check overlap with WBCIC-SHU |
| `tfm_tokenizer` | https://github.com/Jathurshan0330/TFM-Tokenizer | `2d6da48` | tfm | bundles `pretrained_weigths/multiple_dataset_settings/{Pretrained_tfm_tokenizer_2x2x8,MTP_Pretrained_tfm_encoder_64x4}` |
| `cbramod` | https://github.com/wjq-learning/CBraMod | `b9e9610` | cbramod | weights on HF `weighting666/CBraMod` |
| `eegpt` | https://github.com/BINE022/EEGPT | `a0e0a8f` | eegpt | official weights only on a figshare private link (browser-only) — see `weights/README.md` |
| `biot` | https://github.com/ycq091044/BIOT | `d138e32` | biot_6d (+1D/2D) | bundles `pretrained-models/*.ckpt` |

Not added: `CNN-Transformer` (no upstream repo listed by the benchmark; implemented in `eeg_fm_benchmark/models/DL/CNNTransformer`),
`FBCNet` / `MSCFormer` (in the benchmark repo but not in Table 2), `MIRepNet` (optional, PLAN.md).

Rules

- Never modify upstream files. Needed changes go to `patches/<name>.patch` (with rationale) or into
  `src/eegbench/models/<key>/adapter.py`.
- `python -m eegbench.cli doctor` (planned) checks that pinned commits are checked out.
- Upstream licenses apply; keep each repo's LICENSE in place. LUNA weights are CC BY-ND 4.0 (no derivatives redistribution).
