"""Unified model interface and adapters over official code in third_party/.

Contract (docs/ARCHITECTURE.md §3.2):

    class EEGModel(nn.Module):
        input_spec: InputSpec                       # declared in configs/models/<key>.yaml
        def forward(self, x, meta) -> logits        # [B, n_classes]
        def trainable_parameters(self, mode)        # "full" | "linear_probe" | "lora"

One sub-package per model key (see configs/models/roster.yaml): `<key>/adapter.py` loads the official
encoder + verified weights, builds the classification head, and declares `input_spec`.
Upstream code is never modified; patches go to third_party/patches/.
Planned modules: base.py, registry.py, heads.py, <key>/adapter.py.
"""
