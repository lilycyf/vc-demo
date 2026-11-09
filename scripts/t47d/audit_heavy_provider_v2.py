"""Zero-fit heavy-source, runtime and registration audit; never initializes a Session."""
import argparse
import json
from pathlib import Path
import subprocess

import pandas as pd

from vc_demo.harness.research_contract import file_digest, freeze_record
from vc_demo.t47d_provider_v2.cell_sources import read_cells, verified_file
from vc_demo.t47d_provider_v2.registration import implementation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparation-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    p = json.loads((args.preparation_dir / 'preparation_manifest.json').read_text())
    c = json.loads(Path(p['development_contract']).read_text())
    cc = json.loads(verified_file(p['confirmation_contract']).read_text())
    gene_order = pd.read_csv(verified_file(p['development_inputs']['gene_order'])).gene_id.astype(str).tolist()
    observations = {}
    for scope, values in [('development', p['development_inputs']), ('confirmation', cc)]:
        expected = set(c['groups'] if scope == 'development' else cc['groups'])
        cells = read_cells(values['early_cells'], groups=expected)
        if set(cells.obs.clone_id) != expected or cells.var_names.tolist() != gene_order:
            raise ValueError('Heavy cells differ from fixed group/gene contract')
        observations[scope] = {'cells': cells.n_obs, 'genes': cells.n_vars,
            'groups': len(expected), 'days': sorted(int(x) for x in cells.obs.time_day.unique()),
            'obs_columns': list(cells.obs.columns), 'source_sha256': values['early_cells']['sha256']}
    events = pd.read_csv(verified_file(p['development_inputs']['training_events']))
    if not set(events.clone_id).issubset(c['groups']) or not set(events.time_day).issubset({1, 4, 8, 26}):
        raise ValueError('Training event table includes query groups or undeclared endpoints')
    configs = {kind: {'model': 'ridge', 'representation': kind} for kind in ('scvi', 'pseudotime', 'cellrank', 'distance')}
    configs.update(hazard={'model': 'hazard', 'representation': 'pca', 'hazard_max_fit_day': 26},
                   tracsed={'model': 'tracsed', 'representation': 'pathway'})
    preview = {}
    for name, config in configs.items():
        actual = implementation(config, p)
        preview[name] = {'source_files_bound': len(actual['recipe']['code_sha256']),
            'consumed_artifact_roles': sorted(actual['recipe']['artifact_sha256']),
            'environment': actual['recipe']['environment'], 'registered_only_not_fitted': True}
    notebook = verified_file(p['tracsed_notebook'])
    runtime = p['tensorflow_runtime']
    identity = json.loads(verified_file(runtime).read_text())
    code = 'import json,sys,importlib.metadata as m;print(json.dumps({"python_version":sys.version.split()[0],"packages":{p:m.version(p) for p in ["tensorflow","keras","numpy","pandas","scikit-learn","scipy"]}}))'
    actual = json.loads(subprocess.check_output([runtime['python'], '-c', code], text=True))
    if actual != identity:
        raise ValueError('Isolated TensorFlow runtime identity changed')
    result = {'kind': 'heavy_provider_source_preflight_only', 'models_fitted_on_real_data': 0,
        'scientific_run_started': False, 'session_initialized': False, 'early_cells': observations,
        'train_only_event_rows': len(events), 'confirmation_groups_in_training_events': 0,
        'author_notebook_sha256': file_digest(notebook), 'tensorflow_runtime': identity,
        'registration_preview': preview, 'historical_test_exposure_preserved': p['prior_test_exposure'],
        'gpu_formal_fit_or_real_scale_convergence_certified': False}
    freeze_record(args.output, result)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
