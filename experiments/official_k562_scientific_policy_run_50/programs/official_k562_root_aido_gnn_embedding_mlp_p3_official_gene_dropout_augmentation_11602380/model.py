from __future__ import annotations

from vc_demo.official_k562.native_models import OfficialK562NativeModel


class GeneratedModel(OfficialK562NativeModel):
    def __init__(self, spec) -> None:
        super().__init__(spec, variant='gene_dropout_augmentation')
