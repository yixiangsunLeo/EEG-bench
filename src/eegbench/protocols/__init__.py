"""Deterministic split generators: (dataset, protocol, seed) -> split.json with sha256 hash.

Planned protocols (configs/protocols/): loso_single_session, loso_all_sessions, few_shot_within,
cross_dataset_lodo, cross_dataset_pairwise. Every generator must pass the leakage assertions
(subject-disjoint train/val/test; dataset-disjoint for cross-dataset protocols) in tests/protocols/.
"""
