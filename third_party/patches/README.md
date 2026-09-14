# third_party/patches/

Unified diffs against pinned upstream commits, one file per submodule (`<name>.patch`), each with a header
comment stating what it changes and why. Applied by `eegbench doctor --apply-patches`. Prefer adapter-level
monkeypatching in `src/eegbench/models/<key>/adapter.py`; use a patch only when unavoidable.
