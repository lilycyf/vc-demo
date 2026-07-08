from __future__ import annotations

from vc_demo.official_k562.native_models import OfficialK562NativeModel


class GeneratedModel(OfficialK562NativeModel):
    """Reactome/pathway pooling node using the acquired K562 membership artifact."""

    def __init__(self, spec):
        super().__init__(spec, variant="pathway_pooling_reactome")
