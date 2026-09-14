"""Metrics, summarizer and statistics.

metrics: balanced accuracy (primary), accuracy, Cohen's kappa, macro-F1, AUC (P300).
summarizer: outputs/<run_id>/**/result.json -> results/<run_id>/*.csv|md|png (per model, per subject,
paired tests, comparison against results/reference/). Sample standard deviation (n-1).
stats: paired Wilcoxon + Holm, Friedman + Nemenyi CD, within a single run_id only.
"""
