from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

REQUIRED_MODULE_IDS = {
    'aido_dna', 'aido_dna2', 'aido_cell_3m', 'aido_cell_10m', 'aido_cell_100m',
    'aido_protein', 'aido_protein_16b', 'proteinrag_16b_struct',
    'esm2_35m', 'esm2_150m', 'esm2_650m', 'esm2_3b',
    'string_gnn_model_dir', 'string_ppi_graph', 'string_spectral', 'string_seq', 'string_wavegc', 'string_net', 'gnn_simple_official_d256',
    'scfoundation', 'scgpt', 'geneformer', 'transcriptformer', 'scprint',
    'genept_all', 'genept_bp', 'genept_cc', 'genept_mf', 'genept_ncbi', 'genept_n_plus_u',
    'depmap', 'genotypevae', 'positional_3m', 'positional_10m', 'positional_100m',
    'alphagenome', 'reactome_pathway_memberships', 'regulatory_network_prior',
    'scratch_baseline', 'public_vcharness_static_tree',
}


def load_json(path: Path) -> dict:
    with path.open() as handle:
        return json.load(handle)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    universe_path = root / 'configs' / 'vcharness_paper_model_universe.json'
    k562_path = root / 'configs' / 'official_k562_paper_scale_search_space.json'
    universe = load_json(universe_path)
    k562 = load_json(k562_path)
    modules = universe.get('modules', [])
    ids = {item.get('id') for item in modules}
    missing = sorted(REQUIRED_MODULE_IDS - ids)
    extra = sorted(ids - REQUIRED_MODULE_IDS)
    duplicates = sorted([mid for mid, count in Counter(item.get('id') for item in modules).items() if count > 1])
    bad_entries = [item.get('id', '<missing-id>') for item in modules if not all(item.get(field) for field in ['id', 'family', 'paper_presence', 'artifact_status', 'strict_use_rule'])]
    errors: list[str] = []
    if missing:
        errors.append(f'missing required paper modules: {missing}')
    if duplicates:
        errors.append(f'duplicate module ids: {duplicates}')
    if bad_entries:
        errors.append(f'module entries missing required fields: {bad_entries}')
    if k562.get('paper_model_universe_manifest') != 'configs/vcharness_paper_model_universe.json':
        errors.append('official K562 search space does not point to configs/vcharness_paper_model_universe.json')
    coverage = k562.get('coverage_requirement', {})
    if not coverage.get('cannot_be_smaller_than_paper'):
        errors.append('official K562 coverage requirement does not set cannot_be_smaller_than_paper=true')
    print(json.dumps({
        'universe_manifest': str(universe_path.relative_to(root)),
        'k562_search_space': str(k562_path.relative_to(root)),
        'module_count': len(modules),
        'required_module_count': len(REQUIRED_MODULE_IDS),
        'missing_required_modules': missing,
        'extra_modules': extra,
        'status_counts': dict(sorted(Counter(item.get('artifact_status', 'unknown') for item in modules).items())),
        'family_counts': dict(sorted(Counter(item.get('family', 'unknown') for item in modules).items())),
        'k562_references_universe': k562.get('paper_model_universe_manifest') == 'configs/vcharness_paper_model_universe.json',
        'errors': errors,
    }, indent=2))
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
