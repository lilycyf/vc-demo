from __future__ import annotations

from vc_demo.official_k562.native_models import OfficialK562NativeModel


class GeneratedModel(OfficialK562NativeModel):
    implementation_blueprint = 'official_temperature_calibrated_head'
    native_variant = 'target_gene_head'

    def __init__(self, spec):
        super().__init__(spec, variant='target_gene_head')
