#!/usr/bin/env python3
"""Download the five BNCI datasets used in the benchmark via MOABB into the shared raw root
(`raw_root` in configs/paths.local.yaml -> MOABB creates `<raw_root>/MNE-bnci-data/...`).

    conda run -n eegbench python scripts/download_bnci.py            # all five
    conda run -n eegbench python scripts/download_bnci.py --only bnci2014004 bnci2014008
    conda run -n eegbench python scripts/download_bnci.py --check     # list what is on disk, no network

Raw files only; no epoching or filtering happens here (that is `eegbench prepare`, P1).
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

DATASETS = {  # eegbench key -> MOABB class name
    "bnci2014001": "BNCI2014_001",
    "bnci2014004": "BNCI2014_004",
    "bnci2015001": "BNCI2015_001",
    "bnci2014009": "BNCI2014_009",
    "bnci2014008": "BNCI2014_008",
}


def raw_root() -> Path:
    cfg = ROOT / "configs" / "paths.local.yaml"
    if not cfg.exists():
        sys.exit("configs/paths.local.yaml missing (copy paths.example.yaml and fill it)")
    paths = yaml.safe_load(cfg.read_text())
    return Path(paths.get("mne_data") or paths["raw_root"])


def on_disk(root: Path) -> None:
    # moabb 1.5 mirrors the URL path: <root>/MNE-bnci-data/~bci/database/<collection>/<file>.mat
    base = root / "MNE-bnci-data"
    if not base.exists():
        print(f"(nothing under {base})")
        return
    by_dir: dict[str, list[Path]] = {}
    for f in base.rglob("*"):
        if f.is_file() and not f.name.startswith("tmp"):
            by_dir.setdefault(f.parent.name, []).append(f)
    for d in sorted(by_dir):
        files = by_dir[d]
        print(f"  {d:12s} {len(files):4d} files  {sum(f.stat().st_size for f in files)/1e6:8.1f} MB  "
              f"[{', '.join(sorted(f.name for f in files))[:90]}{'…' if len(files) > 6 else ''}]")


def enumerate_files(keys, mds, root: Path) -> list[tuple[str, str, Path]]:
    """Ask MOABB itself for every (dataset_key, url, destination) it would download — no network, no files written.

    `moabb.datasets.download.data_dl` computes the destination and then calls pooch `retrieve`; we swap `retrieve`
    for a recorder for the duration of the enumeration so MOABB's own URL/path logic is used verbatim.
    """
    from moabb.datasets import download as dl

    os.environ["MNE_DATASETS_BNCI_PATH"] = str(root)
    os.environ["MNE_DATA"] = str(root)
    recorded: list[tuple[str, str, Path]] = []
    current = {"key": None}

    def recorder(url, known_hash, fname=None, path=None, **kwargs):  # noqa: ARG001
        dest = Path(path) / fname
        recorded.append((current["key"], url, dest))
        return str(dest)

    real = dl.retrieve
    dl.retrieve = recorder
    try:
        for key in keys:
            current["key"] = key
            ds = getattr(mds, DATASETS[key])()
            for s in ds.subject_list:
                ds.data_path(s, path=str(root), force_update=False, update_path=False)
    finally:
        dl.retrieve = real
    # de-duplicate, keep order
    seen, out = set(), []
    for item in recorded:
        if item[2] not in seen:
            seen.add(item[2]); out.append(item)
    return out


def curl_one(url: str, dest: Path, stage_dir: Path) -> tuple[Path, bool, str]:
    if dest.is_file():
        return dest, True, "exists"
    stage_dir.mkdir(parents=True, exist_ok=True)
    part = stage_dir / (dest.name + ".part")
    cmd = ["curl", "-k", "-L", "--fail", "--silent", "--show-error", "-C", "-",
           "--retry", "60", "--retry-all-errors", "--retry-delay", "5", "--retry-max-time", "0",
           "--speed-time", "120", "--speed-limit", "1000",   # give up (then retry) if < 1 KB/s for 2 min
           "-o", str(part), url]
    for attempt in range(1, 61):
        r = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if r.returncode == 0:
            dest.parent.mkdir(parents=True, exist_ok=True)
            tmp = dest.with_suffix(dest.suffix + ".tmp")
            shutil.copy2(part, tmp)
            tmp.rename(dest)
            part.unlink(missing_ok=True)
            return dest, True, f"downloaded ({dest.stat().st_size/1e6:.1f} MB, attempt {attempt})"
        if r.returncode == 33:           # HTTP range not supported for a fresh restart edge case
            part.unlink(missing_ok=True)
    return dest, False, f"curl failed after retries: {r.stderr.strip()[-200:]}"


def curl_mode(keys, mds, root: Path, stage_root: Path, n_parallel: int) -> list[str]:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    files = enumerate_files(keys, mds, root)
    todo = [f for f in files if not f[2].is_file()]
    print(f"MOABB enumerated {len(files)} files for {keys}; {len(files)-len(todo)} already present, {len(todo)} to fetch "
          f"({n_parallel} parallel curl streams, resumable)")
    for key, url, dest in todo:
        print(f"  {key:12s} {url}  ->  {dest.relative_to(root)}")
    failed_keys: set[str] = set()
    with ThreadPoolExecutor(max_workers=n_parallel) as ex:
        futs = {ex.submit(curl_one, url, dest, stage_root / "curl_parts"): key for key, url, dest in todo}
        for fut in as_completed(futs):
            dest, ok, msg = fut.result()
            print(f"  {'ok  ' if ok else 'FAIL'} {dest.name:12s} {msg}", flush=True)
            if not ok:
                failed_keys.add(futs[fut])
    return sorted(failed_keys)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--staging", default=None,
                    help="download into this local dir first (pooch on NFS is ~10x slower), then rsync into raw_root")
    ap.add_argument("--finalize", action="store_true",
                    help="write the persistent MNE config (MNE_DATA / MNE_DATASETS_BNCI_PATH) to raw_root; run once, after all downloads")
    ap.add_argument("--curl", type=int, default=0, metavar="N",
                    help="resumable mode: let MOABB enumerate (url, destination) pairs, then fetch them with N parallel "
                         "`curl -C - --retry` streams (the TU Graz server drops connections after ~13 min; pooch cannot resume)")
    args = ap.parse_args()

    root = raw_root()
    root.mkdir(parents=True, exist_ok=True)
    if args.check:
        print(f"raw_root = {root}")
        on_disk(root)
        return 0
    if args.finalize:
        import mne
        mne.set_config("MNE_DATA", str(root), set_env=True)
        mne.set_config("MNE_DATASETS_BNCI_PATH", str(root), set_env=True)
        print(f"persistent MNE config -> {root}")
        return 0
    dl_root = Path(args.staging) if args.staging else root
    dl_root.mkdir(parents=True, exist_ok=True)
    # Process-local only (mne.get_config reads os.environ first). Never write the shared ~/.mne config here:
    # parallel per-dataset processes would redirect each other mid-download.
    os.environ["MNE_DATA"] = str(dl_root)
    os.environ["MNE_DATASETS_BNCI_PATH"] = str(dl_root)
    print(f"download root = {dl_root}   final root = {root}")
    if dl_root != root and (root / "MNE-bnci-data").exists():
        # seed the staging dir with files already downloaded, so pooch skips them instead of re-downloading
        (dl_root / "MNE-bnci-data").mkdir(parents=True, exist_ok=True)
        subprocess.run(["rsync", "-a", f"{root / 'MNE-bnci-data'}/", f"{dl_root / 'MNE-bnci-data'}/"], check=True)

    import mne
    import moabb
    from moabb import datasets as mds
    from moabb.datasets import bnci as moabb_bnci

    mne.set_log_level("WARNING")
    print(f"moabb {moabb.__version__} | mne {mne.__version__}")

    # MOABB >= 1.5 already points the BNCI datasets at the TU Graz origin server (bnci/base.py: BNCI_URL =
    # https://lampx.tugraz.at/~bci/database/), which is reachable from this cluster. We do NOT override it;
    # `bnci_url` in paths.local.yaml is only honoured if set explicitly (kept for machines where the default fails).
    paths = yaml.safe_load((ROOT / "configs" / "paths.local.yaml").read_text())
    base = getattr(moabb_bnci, "base", None)
    default_url = getattr(base, "BNCI_URL", "?") if base is not None else "?"
    print(f"MOABB BNCI_URL (default, unchanged) = {default_url}")
    if paths.get("bnci_url"):
        print(f"WARNING: overriding BNCI_URL -> {paths['bnci_url']} (bnci_url set in paths.local.yaml)")
        base.BNCI_URL = paths["bnci_url"]

    failed = []
    keys = args.only or list(DATASETS)
    if args.curl:
        failed += curl_mode(keys, mds, root, dl_root, args.curl)
        print("\non disk (final root):")
        on_disk(root)
        return 1 if failed else 0

    for key in keys:
        cls = getattr(mds, DATASETS[key])
        ds = cls()
        print(f"[{key}] {DATASETS[key]}: subjects={ds.subject_list} sessions/subject={ds.n_sessions}")
        try:
            ds.download(subject_list=ds.subject_list, path=str(dl_root), force_update=False, verbose="WARNING")
            print("  done")
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED: {type(e).__name__}: {e}")
            failed.append(key)

    if dl_root != root:
        src, dst = dl_root / "MNE-bnci-data", root / "MNE-bnci-data"
        dst.mkdir(parents=True, exist_ok=True)
        print(f"\nrsync {src}/ -> {dst}/")
        r = subprocess.run(["rsync", "-a", "--remove-source-files", f"{src}/", f"{dst}/"])
        if r.returncode != 0:
            failed.append("rsync")
    print("\non disk (final root):")
    on_disk(root)
    print("\nNOTE: run `--finalize` once all datasets are complete to point the persistent MNE config at the final root.")
    if failed:
        print("FAILED:", failed)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
