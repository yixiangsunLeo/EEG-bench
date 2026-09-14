#!/usr/bin/env python3
"""Verify downloaded BNCI datasets against the paper's Table 14 using MOABB's own loaders (no filtering).

For each dataset whose files are all present: load every subject with `dataset.get_data()`, count sessions / runs /
channels / sampling rate / trials (events), and compare with configs/datasets/<key>.yaml (Table 14 facts).

    conda run -n eegbench python scripts/verify_bnci.py                 # all complete datasets
    conda run -n eegbench python scripts/verify_bnci.py --only bnci2014008
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from download_bnci import DATASETS, enumerate_files, raw_root  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()

    root = raw_root()
    os.environ["MNE_DATA"] = str(root)
    os.environ["MNE_DATASETS_BNCI_PATH"] = str(root)
    import mne
    from moabb import datasets as mds

    mne.set_log_level("ERROR")
    keys = args.only or list(DATASETS)
    files = enumerate_files(keys, mds, root)
    problems = []
    for key in keys:
        card = yaml.safe_load((ROOT / "configs" / "datasets" / f"{key}.yaml").read_text())
        mine = [f for f in files if f[0] == key]
        missing = [f[2].name for f in mine if not f[2].is_file()]
        if missing:
            print(f"[{key}] INCOMPLETE: {len(missing)}/{len(mine)} files missing -> skipped")
            continue
        ds = getattr(mds, DATASETS[key])()
        data = ds.get_data()  # {subject: {session: {run: Raw}}}
        n_subj = len(data)
        sessions = sorted({s for subj in data.values() for s in subj})
        n_trials, chans, sfreqs = 0, set(), set()
        per_session: dict[str, int] = {}
        for subj in data.values():
            for sess, runs in subj.items():
                for raw in runs.values():
                    ev = mne.find_events(raw, stim_channel="stim", verbose=False) if "stim" in raw.ch_names else None
                    n = len(ev) if ev is not None else len(mne.events_from_annotations(raw, verbose=False)[0])
                    # keep only event codes that map to the dataset's classes
                    if ev is not None:
                        codes = set(ds.event_id.values())
                        n = int(sum(1 for e in ev if e[2] in codes))
                    n_trials += n
                    per_session[sess] = per_session.get(sess, 0) + n
                    chans.add(len([c for c in raw.ch_names if c.lower() != "stim" and raw.get_channel_types([c])[0] == "eeg"]))
                    sfreqs.add(float(raw.info["sfreq"]))
        exp_subj, exp_ch, exp_fs, exp_trials = card["n_subjects"], card["n_channels"], card["sfreq_native"], card["n_trials_total"]
        ok_subj, ok_ch, ok_fs = n_subj == exp_subj, chans == {exp_ch}, sfreqs == {float(exp_fs)}
        print(f"[{key}] subjects {n_subj} (card {exp_subj}) {'ok' if ok_subj else 'MISMATCH'} | "
              f"eeg channels {sorted(chans)} (card {exp_ch}) {'ok' if ok_ch else 'MISMATCH'} | "
              f"sfreq {sorted(sfreqs)} (card {exp_fs}) {'ok' if ok_fs else 'MISMATCH'}")
        print(f"          sessions {sessions}; trials per session {per_session}; total {n_trials} (Table 14: {exp_trials})")
        if not (ok_subj and ok_ch and ok_fs):
            problems.append(key)
    if problems:
        print("MISMATCHES:", problems)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
