"""Command-line entry point: ``python -m eegbench.cli <command>``.

Planned commands (not implemented yet):

    prepare    --dataset <key>                      raw / MOABB -> canonical (versioned)
    split      --protocol <key> --dataset <key>     write split.json + hash
    train      --experiment <yaml> [--cells ...]    run / resume cells
    summarize  --experiment <yaml>                  result.json -> results/<run_id>/
    doctor                                          check paths.local.yaml, weights sha256, submodules, CUDA
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    sys.stderr.write(
        "eegbench.cli: skeleton only (2026-09-13). Commands prepare/split/train/summarize/doctor "
        "are planned; see docs/PLAN.md P0.\n"
    )
    return 2 if argv else 0


if __name__ == "__main__":
    raise SystemExit(main())
