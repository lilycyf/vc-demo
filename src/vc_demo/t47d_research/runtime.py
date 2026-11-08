"""Versioned task-specific representation cache; historical caches stay unchanged."""
from functools import lru_cache
from pathlib import Path
import importlib.metadata

from vc_demo.harness.research_contract import digest, file_digest
from vc_demo.t47d_full import features
from vc_demo.t47d_full import models as model_api
from vc_demo.harness.research_contract import write_record

_original_identity = features.cache_identity
_original_builder = features.build_fold


@lru_cache(maxsize=1)
def source_identity():
    source = Path('data/t47d_lineage/prepared/qc_counts.h5ad')
    code = [Path(features.__file__), Path(__file__)]
    packages = {}
    for package in ('numpy', 'torch', 'scikit-learn', 'scanpy', 'scvi-tools', 'cellrank', 'pertpy', 'POT', 'jax', 'jaxlib', 'ott-jax'):
        try:
            packages[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            packages[package] = 'not_installed_in_this_environment'
    return {'source_sha256': file_digest(source), 'code_sha256': {str(p): file_digest(p) for p in code},
            'packages': packages, 'version': 'research-adapter-v3'}


def cache_identity(bundle, train_idx, seed, max_fit_day=4, fit_treatments=None, no_time_direction=False):
    _, payload = _original_identity(bundle, train_idx, seed, max_fit_day, fit_treatments, no_time_direction)
    payload.update(source_identity())
    payload['training_rows'] = sorted(bundle['meta'].iloc[train_idx].apply(
        lambda r: str(r.clone_id)+'::'+str(r.treatment), axis=1).tolist())
    return Path('data/t47d_lineage/research_fold_artifacts_v3')/digest(payload)[:24], payload


def build_fold(bundle, train_idx, seed, modules=('scvi','pseudotime','distance','cellrank'),
               max_fit_day=4, fit_treatments=None, no_time_direction=False):
    dest, _ = cache_identity(bundle,train_idx,seed,max_fit_day,fit_treatments,no_time_direction)
    receipt = dest/'content_receipt.json'
    arrays = dest/'features.npz'
    if arrays.is_file():
        if not receipt.is_file():
            import uuid
            dest.rename(dest.with_name(dest.name+'.interrupted-'+uuid.uuid4().hex[:8]))
        else:
            import json
            expected = json.loads(receipt.read_text())
            if file_digest(arrays) != expected['features_sha256'] or file_digest(dest/'manifest.json') != expected['manifest_sha256']:
                raise ValueError('Derived representation cache content changed; do not consume it')
    result = _original_builder(bundle,train_idx,seed,modules,max_fit_day,fit_treatments,no_time_direction)
    write_record(receipt,{'features_sha256':file_digest(arrays),
        'manifest_sha256':file_digest(dest/'manifest.json'),'validation':'content, code, vocabulary and training-row identities'})
    return result


def configure():
    features.cache_identity = cache_identity
    model_api.build_fold = build_fold
