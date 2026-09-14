# src/

Single package `eegbench` (src layout; `pip install -e .`). Layer responsibilities are in each sub-package's
`__init__.py` docstring and in `docs/ARCHITECTURE.md` §2. Human entry point: `python -m eegbench.cli`.
No absolute paths, no dataset-specific branches inside models, no model-specific branches inside the trainer.
