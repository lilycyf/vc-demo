"""Register explicit T47D analysis plans without a Session or model fits."""
import argparse
import json
from pathlib import Path

from vc_demo.harness.research_contract import freeze_record
from vc_demo.t47d_provider_v2.analysis_registration import register_analyses


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task-spec', type=Path, required=True)
    parser.add_argument('--preparation-dir', type=Path, required=True)
    parser.add_argument('--plans', type=Path, required=True)
    parser.add_argument('--contracts-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = register_analyses(json.loads(args.task_spec.read_text()),
        json.loads((args.preparation_dir / 'preparation_manifest.json').read_text()),
        json.loads(args.plans.read_text()), args.contracts_dir)
    from vc_demo.harness.research_v2.postselection import validate_plans
    validate_plans(result)
    freeze_record(args.output, result)
    print(json.dumps({'registered_analyses': sorted(result['analyses']), 'models_fitted': 0,
        'session_initialized': False, 'scientific_run_started': False}, indent=2))


if __name__ == '__main__':
    main()
