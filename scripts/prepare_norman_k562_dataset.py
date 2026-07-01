
from __future__ import annotations

import argparse
import json
from pathlib import Path

import anndata as ad
import numpy as np
from scipy import sparse


def mean_rows(x, mask):
    block = x[mask]
    if sparse.issparse(block):
        return np.asarray(block.mean(axis=0)).ravel().astype('float32')
    return np.asarray(block, dtype='float32').mean(axis=0)


def main() -> None:
    parser = argparse.ArgumentParser(description='Prepare Norman/Weissman 2019 K562 Perturb-seq data for vc-demo real_npz loader.')
    parser.add_argument('--h5ad', type=Path, default=Path('data/raw/scperturb/NormanWeissman2019_filtered.h5ad'))
    parser.add_argument('--data-dir', type=Path, default=Path('data/cell_lines/k562'))
    parser.add_argument('--n-target-genes', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=17)
    args = parser.parse_args()

    args.data_dir.mkdir(parents=True, exist_ok=True)
    adata = ad.read_h5ad(args.h5ad, backed='r')
    obs0 = adata.obs.copy()
    var = adata.var.copy()

    var_rank = var.copy()
    var_rank['ncounts'] = var_rank.get('ncounts', 0).astype(float)
    var_rank['ncells'] = var_rank.get('ncells', 0).astype(float)
    var_rank = var_rank[(var_rank['ncounts'] > 0) & (var_rank['ncells'] >= 25)]
    target_genes = var_rank.sort_values(['ncells', 'ncounts'], ascending=False).head(args.n_target_genes).index.to_numpy()

    print(f'loading {len(target_genes)} target genes from {adata.n_obs} cells')
    sub = adata[:, target_genes].to_memory()
    adata.file.close()
    x = sub.X.tocsr() if sparse.issparse(sub.X) else np.asarray(sub.X, dtype='float32')
    obs = sub.obs.copy()

    keep = np.ones(len(obs), dtype=bool)
    if 'good_coverage' in obs:
        keep &= obs['good_coverage'].astype(bool).to_numpy()
    if 'cell_line' in obs:
        keep &= obs['cell_line'].astype(str).str.upper().eq('K562').to_numpy()

    perturbation = obs['perturbation'].astype(str).to_numpy()
    nperts = obs['nperts'].astype(int).to_numpy()
    control_mask = keep & (perturbation == 'control')
    single_mask = keep & (perturbation != 'control') & (nperts == 1)

    unique, counts = np.unique(perturbation[single_mask], return_counts=True)
    perturbations = sorted(unique[counts >= 25].tolist())
    if len(perturbations) < 10:
        raise RuntimeError(f'not enough perturbations with >=25 cells: {len(perturbations)}')

    control_mean = mean_rows(x, control_mask)
    n = len(perturbations)
    features = np.eye(n, dtype='float32')
    labels = np.empty((n, len(target_genes)), dtype='int64')
    deltas = np.empty((n, len(target_genes)), dtype='float32')
    cell_counts = {}

    for i, pert in enumerate(perturbations):
        mask = single_mask & (perturbation == pert)
        delta = mean_rows(x, mask) - control_mean
        lo, hi = np.quantile(delta, [0.05, 0.95])
        row = np.ones(delta.shape, dtype='int64')
        row[delta <= lo] = 0
        row[delta >= hi] = 2
        labels[i] = row
        deltas[i] = delta.astype('float32')
        cell_counts[pert] = int(mask.sum())

    rng = np.random.default_rng(args.seed)
    order = rng.permutation(n)
    train_end = int(0.70 * n)
    val_end = int(0.85 * n)
    splits = {'train': order[:train_end], 'val': order[train_end:val_end], 'test': order[val_end:]}

    pert_arr = np.asarray(perturbations, dtype='U64')
    gene_arr = np.asarray(target_genes, dtype='U64')
    for split, idx in splits.items():
        np.savez_compressed(
            args.data_dir / f'{split}.npz',
            features=features[idx].astype('float32'),
            labels=labels[idx].astype('int64'),
            perturbations=pert_arr[idx],
            target_genes=gene_arr,
            delta_mean=deltas[idx].astype('float32'),
        )

    label_counts = {str(k): int(v) for k, v in zip(*np.unique(labels, return_counts=True))}
    manifest = {
        'format': 'npz',
        'cell_line': 'K562',
        'task': 'CRISPR_KO_DEG_classification',
        'source': {
            'name': 'NormanWeissman2019_filtered.h5ad from scPerturb Zenodo record 7041849',
            'url': 'https://zenodo.org/records/7041849',
            'doi': '10.5281/zenodo.7041849',
            'h5ad_file': str(args.h5ad),
        },
        'feature_key': 'features',
        'label_key': 'labels',
        'n_classes': 3,
        'class_names': ['down', 'unchanged', 'up'],
        'files': {'train': 'train.npz', 'val': 'val.npz', 'test': 'test.npz'},
        'n_perturbations': int(n),
        'n_features': int(features.shape[1]),
        'n_target_genes': int(labels.shape[1]),
        'target_gene_selection': f'top {len(target_genes)} genes by ncells then ncounts among expressed genes',
        'label_rule': 'per perturbation, delta vs control mean expression; <=5th percentile down, >=95th percentile up, otherwise unchanged',
        'min_cells_per_perturbation': 25,
        'control_cells': int(control_mask.sum()),
        'label_counts': label_counts,
        'split_sizes': {k: int(len(v)) for k, v in splits.items()},
        'cell_counts_by_perturbation': cell_counts,
    }
    (args.data_dir / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

    summary = {
        'data_dir': str(args.data_dir),
        'n_perturbations': int(n),
        'n_features': int(features.shape[1]),
        'n_target_genes': int(labels.shape[1]),
        'split_sizes': manifest['split_sizes'],
        'label_counts': label_counts,
        'first_perturbations': perturbations[:10],
        'first_target_genes': target_genes[:10].tolist(),
    }
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
