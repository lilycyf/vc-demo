from __future__ import annotations

from vc_demo.official_k562.native_models import OfficialK562NativeModel


class GeneratedModel(OfficialK562NativeModel):
    implementation_blueprint = 'official_target_graph_conditioned_head'
    native_variant = 'string_gnn_attention'

    def __init__(self, spec):
        super().__init__(spec, variant='string_gnn_attention')
