"""Export T47D v2 contracts only. Never starts a Session, fit or search."""
import argparse
import json

from vc_demo.t47d_provider_v2.data import prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared', required=True)
    parser.add_argument('--pathways', required=True)
    parser.add_argument('--historical-run', required=True)
    parser.add_argument('--baseline-tree', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args()
    manifest = prepare(args.prepared, args.pathways, args.historical_run, args.baseline_tree, args.output_dir)
    print(json.dumps({'counts': manifest['counts'], 'dataset_sha256': manifest['dataset_sha256'],
                      'models_fitted': 0, 'scientific_run_started': False}, indent=2))


if __name__ == '__main__':
    main()
