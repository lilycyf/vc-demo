from __future__ import annotations

from torch import nn

from vc_demo.official_k562.native_models import OfficialK562NativeModel


class GeneratedModel(nn.Module):
    def __init__(self, spec):
        super().__init__()
        self.impl = OfficialK562NativeModel(spec, variant="target_gene_head")

    def forward(self, x):
        return self.impl(x)
