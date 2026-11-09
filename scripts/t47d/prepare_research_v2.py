"""Export source-backed contracts only; never starts a Session, fit or search."""
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
    parser.add_argument('--heavy-sources', action='store_true', help='Export split-separated early raw cells and train-only event outcomes; zero model fits')
    parser.add_argument('--tracsed-notebook', help='Pinned author source notebook, required with --tensorflow-python')
    parser.add_argument('--tensorflow-python', help='Isolated TensorFlow runtime, required with --tracsed-notebook')
    args = parser.parse_args()
    manifest = prepare(args.prepared, args.pathways, args.historical_run, args.baseline_tree, args.output_dir,
        heavy_sources=args.heavy_sources, tracsed_notebook=args.tracsed_notebook, tensorflow_python=args.tensorflow_python)
    print(json.dumps({'counts': manifest['counts'], 'heavy_source_counts': manifest.get('heavy_source_counts'),
        'dataset_sha256': manifest['dataset_sha256'], 'models_fitted': 0, 'scientific_run_started': False}, indent=2))


if __name__ == '__main__':
    main()
