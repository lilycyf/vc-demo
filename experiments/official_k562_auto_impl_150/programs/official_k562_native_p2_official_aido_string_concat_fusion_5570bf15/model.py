from __future__ import annotations

from vc_demo.official_k562.native_models import OfficialK562NativeModel


class GeneratedModel(OfficialK562NativeModel):
    implementation_blueprint = 'official_aido_string_concat_fusion'
    native_variant = 'aido_string_fusion'

    def __init__(self, spec):
        super().__init__(spec, variant='aido_string_fusion')
