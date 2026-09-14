#!/usr/bin/env python3
"""Download / collect the pretrained FM weights expected by third_party/eeg_fm_benchmark and record them
in weights/MANIFEST.yaml (file, url, sha256, size, license, source_commit, downloaded).

    python scripts/download_weights.py            # fetch everything missing, verify, update manifest
    python scripts/download_weights.py --verify   # only re-hash existing files against the manifest
    python scripts/download_weights.py --only cbramod luna_base

Target paths mirror `models/pretrained_models/` of the benchmark (see its utils/utils.py:get_pretrained_models_path)
so our adapters can redirect that function to `weights/` without renaming anything.

Network notes (cluster, 2026-09-14): huggingface.co and Google Drive are unreachable; the public mirror
https://hf-mirror.com serves the same files (`<repo>/resolve/main/<path>`); GitHub is reachable.
Only stdlib is used so the script runs in the base interpreter (needs `curl` on PATH).
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = ROOT / "weights"
MANIFEST = WEIGHTS / "MANIFEST.yaml"
TP = ROOT / "third_party"
HF = os.environ.get("HF_ENDPOINT", "https://hf-mirror.com").rstrip("/")


def hf(repo: str, path: str) -> str:
    return f"{HF}/{repo}/resolve/main/{path}"


# model_key -> list of artifacts. Each artifact: target (relative to weights/), source (url or local Path),
# plus provenance. `submodule` names the third_party checkout whose commit is recorded as source_commit.
SOURCES: dict[str, dict] = {
    "bendr": {
        "submodule": "bendr", "license": "see upstream repo (SPOClab-ca/BENDR)",
        "artifacts": [
            {"target": "encoder.pt",
             "source": "https://github.com/SPOClab-ca/BENDR/releases/download/v0.1-alpha/encoder.pt"},
            # contextualizer is not used by the benchmark loader; kept for completeness of the official release.
            {"target": "contextualizer.pt", "optional": True,
             "source": "https://github.com/SPOClab-ca/BENDR/releases/download/v0.1-alpha/contextualizer.pt"},
        ],
    },
    "biot_6d": {
        "submodule": "biot", "license": "see upstream repo (ycq091044/BIOT)",
        "artifacts": [
            {"target": "EEG-six-datasets-18-channels.ckpt",
             "source": TP / "biot/pretrained-models/EEG-six-datasets-18-channels.ckpt"},
            {"target": "EEG-PREST-16-channels.ckpt", "optional": True,
             "source": TP / "biot/pretrained-models/EEG-PREST-16-channels.ckpt"},
            {"target": "EEG-SHHS+PREST-18-channels.ckpt", "optional": True,
             "source": TP / "biot/pretrained-models/EEG-SHHS+PREST-18-channels.ckpt"},
        ],
    },
    "labram": {
        "submodule": "labram", "license": "see upstream repo (935963004/LaBraM)",
        "artifacts": [
            {"target": "labram-base.pth", "source": TP / "labram/checkpoints/labram-base.pth"},
        ],
    },
    "neuro_gpt": {
        "submodule": "neurogpt", "license": "see HF model card wenhuic/Neuro-GPT",
        "artifacts": [
            {"target": "neurogpt.bin", "source": hf("wenhuic/Neuro-GPT", "pretrained_model/pytorch_model.bin")},
        ],
    },
    "eegpt": {
        "submodule": "eegpt", "license": "see upstream repo (BINE022/EEGPT)",
        # Official file `eegpt_mcae_58chs_4s_large4E.ckpt` is only on a figshare private link that needs a browser
        # (JS challenge; API rejects the token). `eeg-telecom-paris/eegpt-large-official` is a weights-only
        # safetensors conversion with the identical module structure (encoder/predictor/reconstructor/
        # target_encoder, 413 tensors, 58ch/256Hz/4s/patch64/embed512x4). Converted back to the Lightning
        # `{"state_dict": ...}` layout by scripts/convert_eegpt_safetensors.py -> eegpt.ckpt.
        # PROVENANCE: third-party conversion, not byte-verified against figshare. See weights/README.md.
        "artifacts": [
            {"target": "eegpt_large_official.safetensors",
             "source": hf("eeg-telecom-paris/eegpt-large-official", "weights.safetensors")},
            {"target": "eegpt_large_official.model_cfg.yaml",
             "source": hf("eeg-telecom-paris/eegpt-large-official", "model_cfg.yaml")},
            # produced locally from the safetensors above; recorded (hashed) here, not downloaded
            {"target": "eegpt.ckpt", "derived": "scripts/convert_eegpt_safetensors.py"},
        ],
    },
    "cbramod": {
        "submodule": "cbramod", "license": "see HF model card weighting666/CBraMod",
        "artifacts": [
            {"target": "CBraMod.pth", "source": hf("weighting666/CBraMod", "pretrained_weights.pth")},
        ],
    },
    "tfm": {
        "submodule": "tfm_tokenizer", "license": "see upstream repo (Jathurshan0330/TFM-Tokenizer)",
        # bundled in the official repo (multiple-dataset setting), exact filenames the benchmark loader expects
        "artifacts": [
            {"target": "tfm_tokenizer_last.pth",
             "source": TP / "tfm_tokenizer/pretrained_weigths/multiple_dataset_settings/"
                            "Pretrained_tfm_tokenizer_2x2x8/tfm_tokenizer_last.pth"},
            {"target": "tfm_encoder_mtp_last.pth",
             "source": TP / "tfm_tokenizer/pretrained_weigths/multiple_dataset_settings/"
                            "MTP_Pretrained_tfm_encoder_64x4/tfm_encoder_mtp_last.pth"},
        ],
    },
    "brainomni_tiny": {
        "submodule": "brainomni", "license": "see HF model card OpenTSLab/BrainOmni",
        "artifacts": [
            {"target": "BrainOmni/tiny/BrainOmni.pt", "source": hf("OpenTSLab/BrainOmni", "tiny/BrainOmni.pt")},
            {"target": "BrainOmni/tiny/model_cfg.json", "source": hf("OpenTSLab/BrainOmni", "tiny/model_cfg.json")},
            {"target": "BrainOmni/braintokenizer/BrainTokenizer.pt",
             "source": hf("OpenTSLab/BrainOmni", "braintokenizer/BrainTokenizer.pt")},
            {"target": "BrainOmni/braintokenizer/model_cfg.json",
             "source": hf("OpenTSLab/BrainOmni", "braintokenizer/model_cfg.json")},
        ],
    },
    "brainomni_base": {
        "submodule": "brainomni", "license": "see HF model card OpenTSLab/BrainOmni",
        "artifacts": [
            {"target": "BrainOmni/base/BrainOmni.pt", "source": hf("OpenTSLab/BrainOmni", "base/BrainOmni.pt")},
            {"target": "BrainOmni/base/model_cfg.json", "source": hf("OpenTSLab/BrainOmni", "base/model_cfg.json")},
        ],
    },
    "eegmamba": {
        "submodule": "eegmamba", "license": "see HF model card weighting666/EEGMamba",
        "artifacts": [
            {"target": "EEGMamba.pth", "source": hf("weighting666/EEGMamba", "pretrained_EEGMamba.pth")},
        ],
    },
    "singlem": {
        "submodule": "singlem", "license": "see upstream repo (ttlabtuat/SingLEM)",
        # The benchmark (2026-06..08) loads `singlem_pretrained.pt`, the ORIGINAL SingLEM release checkpoint
        # (repo path weights/singlem_pretrained.pt, 2025-08-20 .. 2026-07-31). The upstream revision on 2026-07-31
        # ("Update revised manuscript release", 4d95929) deleted it and shipped RETRAINED checkpoints under
        # SingLEM/checkpoints/ (different bytes: 13,162,319 vs 13,177,518). To match the paper we take the file from
        # git history at the last pre-revision commit and pin the submodule there (D-013).
        "artifacts": [
            {"target": "singlem_pretrained.pt",
             "source": {"git": ("singlem", "05abe21", "weights/singlem_pretrained.pt")}},
            # retrained primary checkpoint of the 2026-07-31 revision, kept only for a later "revised SingLEM" comparison
            {"target": "singlem_downstream_excluded_rev2026-07-31.pt", "optional": True,
             "source": {"git": ("singlem", "6db5b5a", "SingLEM/checkpoints/singlem_downstream_excluded.pt")}},
        ],
    },
    "luna_base": {
        "submodule": "biofoundation_luna", "license": "CC BY-ND 4.0 (PulpBio HF model cards)",
        "artifacts": [
            {"target": "LUNA_base.safetensors", "source": hf("PulpBio/LUNA", "LUNA_base.safetensors")},
            {"target": "LUNA_config.json", "source": hf("PulpBio/LUNA", "config.json"), "optional": True},
        ],
    },
}


def sha256(path: Path, bufsize: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(bufsize):
            h.update(chunk)
    return h.hexdigest()


def submodule_commit(name: str) -> str | None:
    d = TP / name
    if not d.exists():
        return None
    try:
        return subprocess.check_output(["git", "-C", str(d), "rev-parse", "HEAD"], text=True).strip()
    except Exception:  # noqa: BLE001
        return None


def fetch(source, target: Path) -> bool:
    target.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(source, dict) and "git" in source:
        # extract a blob from a submodule's history: {"git": (submodule, commit, path)}
        sub, commit, path = source["git"]
        with target.open("wb") as f:
            r = subprocess.run(["git", "-C", str(TP / sub), "show", f"{commit}:{path}"], stdout=f, stderr=subprocess.PIPE)
        if r.returncode != 0:
            target.unlink(missing_ok=True)
            print(f"  GIT SHOW FAILED {sub}@{commit}:{path}\n  {r.stderr.decode(errors='replace').strip()[-300:]}")
            return False
        return True
    if isinstance(source, Path):
        if not source.exists():
            print(f"  MISSING local source {source}")
            return False
        shutil.copy2(source, target)
        return True
    tmp = target.with_suffix(target.suffix + ".part")
    cmd = ["curl", "-L", "--fail", "--retry", "3", "--retry-delay", "5", "-C", "-", "-o", str(tmp), source]
    r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        print(f"  DOWNLOAD FAILED ({r.returncode}) {source}\n  {r.stderr.strip()[-300:]}")
        return False
    tmp.rename(target)
    return True


def load_manifest() -> dict:
    import yaml  # base anaconda has PyYAML; the eegbench env too

    if MANIFEST.exists():
        data = yaml.safe_load(MANIFEST.read_text()) or {}
        return {k: v for k, v in data.items() if isinstance(v, dict)}
    return {}


def dump_manifest(entries: dict) -> None:
    import yaml

    header = (
        "# Pretrained weights manifest — generated/updated by scripts/download_weights.py.\n"
        "# Paths are relative to weights/ and mirror the benchmark's models/pretrained_models/ layout.\n"
        "# `eegbench doctor` re-hashes every file. Never edit sha256 by hand.\n\n"
    )
    ordered = {k: entries[k] for k in SOURCES if k in entries}
    ordered.update({k: v for k, v in entries.items() if k not in ordered})
    MANIFEST.write_text(header + yaml.safe_dump(ordered, sort_keys=False, allow_unicode=True))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None, help="model keys to process")
    ap.add_argument("--verify", action="store_true", help="only verify existing files against manifest")
    args = ap.parse_args()

    manifest = load_manifest()
    keys = args.only or list(SOURCES)
    today = dt.date.today().isoformat()
    failures: list[str] = []

    for key in keys:
        spec = SOURCES[key]
        entry = manifest.get(key) or {"artifacts": []}
        recorded = {a["file"]: a for a in entry.get("artifacts", [])}
        new_artifacts = []
        print(f"[{key}]")
        for art in spec["artifacts"]:
            target = WEIGHTS / art["target"]
            if args.verify:
                if target.exists() and art["target"] in recorded:
                    ok = sha256(target) == recorded[art["target"]]["sha256"]
                    print(f"  {'ok  ' if ok else 'BAD '} {art['target']}")
                    if not ok:
                        failures.append(f"{key}:{art['target']}")
                else:
                    print(f"  absent {art['target']}")
                continue
            if not target.exists():
                if "derived" in art:
                    print(f"  MISSING derived {art['target']} — run `python {art['derived']}` first")
                    failures.append(f"{key}:{art['target']}")
                    continue
                print(f"  fetching {art['target']} <- {art['source']}")
                if not fetch(art["source"], target):
                    if not art.get("optional"):
                        failures.append(f"{key}:{art['target']}")
                    continue
            digest = sha256(target)
            src = art.get("source")
            if "derived" in art:
                url = f"derived:{art['derived']}"
            elif isinstance(src, dict) and "git" in src:
                url = "git:third_party/{}@{}:{}".format(*src["git"])
            elif isinstance(src, Path):
                url = f"local:{src.relative_to(ROOT)}"
            else:
                url = str(src)
            new_artifacts.append({
                "file": art["target"],
                "url": url,
                "sha256": digest,
                "size_bytes": target.stat().st_size,
                "optional": bool(art.get("optional", False)),
                "downloaded": recorded.get(art["target"], {}).get("downloaded", today),
            })
            print(f"  ok  {art['target']}  {target.stat().st_size/1e6:.1f} MB  sha256={digest[:12]}…")
        if not args.verify:
            manifest[key] = {
                "license": spec["license"],
                "source_commit": submodule_commit(spec["submodule"]),
                "artifacts": new_artifacts or entry.get("artifacts", []),
                "status": "complete" if new_artifacts and not any(f.startswith(key + ":") for f in failures)
                else ("pending" if not spec["artifacts"] else "incomplete"),
            }
    if not args.verify:
        dump_manifest(manifest)
        print(f"\nmanifest -> {MANIFEST.relative_to(ROOT)}")
    if failures:
        print("FAILURES:", failures)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
