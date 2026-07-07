#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


def read_text(path: Path, limit: int | None = None) -> str:
    text = path.read_text(errors='replace')
    if limit is not None:
        return text[:limit]
    return text


def literal_constants(py_path: Path) -> dict[str, Any]:
    constants: dict[str, Any] = {}
    try:
        tree = ast.parse(py_path.read_text(errors='replace'))
    except SyntaxError:
        return constants
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    try:
                        constants[target.id] = ast.literal_eval(node.value)
                    except Exception:
                        constants[target.id] = ast.unparse(node.value) if hasattr(ast, 'unparse') else '<expr>'
    return constants


def regex_hits(files: list[Path], patterns: dict[str, str]) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {name: [] for name in patterns}
    compiled = {name: re.compile(pattern, re.I) for name, pattern in patterns.items()}
    for path in files:
        rel = str(path)
        for lineno, line in enumerate(path.read_text(errors='replace').splitlines(), 1):
            for name, rx in compiled.items():
                if rx.search(line):
                    out[name].append({'file': rel, 'line': lineno, 'text': line.strip()[:240]})
    return out


def summarize_current_manifest(repo: Path, rel_path: str) -> dict[str, Any]:
    path = repo / rel_path
    if not path.exists():
        return {'path': rel_path, 'exists': False}
    data = json.loads(path.read_text())
    keys = [
        'cell_line', 'task', 'source', 'n_classes', 'class_names', 'n_perturbations',
        'n_features', 'n_target_genes', 'target_gene_selection', 'label_rule',
        'split_sizes', 'feature_set', 'feature_description', 'label_counts'
    ]
    return {'path': rel_path, 'exists': True, **{k: data.get(k) for k in keys if k in data}}


def score_from_memory(text: str) -> float | None:
    pats = [
        r'Test F1[:=]\s*\*?\*?([0-9]+\.[0-9]+)',
        r'Test/f1:\s*([0-9]+\.[0-9]+)',
        r'Test F1=([0-9]+\.[0-9]+)',
        r'test/f1\s*=\s*([0-9]+\.[0-9]+)',
    ]
    vals: list[float] = []
    for pat in pats:
        vals.extend(float(x) for x in re.findall(pat, text, flags=re.I))
    return max(vals) if vals else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--vcharness-dir', default='/workspace/_external/VCHarness/K562_cls')
    parser.add_argument('--repo-root', default='.')
    parser.add_argument('--out-json', default='experiments/k562_official_task_reconstruction/official_k562_audit.json')
    args = parser.parse_args()

    base = Path(args.vcharness_dir)
    repo = Path(args.repo_root)
    mcts_path = base / 'mcts_data.json'
    if not mcts_path.exists():
        raise FileNotFoundError(mcts_path)

    mcts = json.loads(mcts_path.read_text())
    memory_files = sorted((base / 'memory').glob('*.md'))
    code_files = sorted((base / 'static').glob('*_code.py'))
    best_node = mcts.get('global_best_node')
    best_memory = base / 'memory' / f'{best_node}.md'
    best_code = base / 'static' / f'{best_node}_code.py'

    code_constants = [literal_constants(p) for p in code_files]
    constant_values: dict[str, Counter] = {}
    for constants in code_constants:
        for key, value in constants.items():
            if key in {'N_GENES', 'N_CLASSES', 'AIDO_GENES', 'AIDO_MODEL_DIR', 'STRING_MODEL_DIR', 'CLASS_FREQ', 'TRAIN_TSV', 'VAL_TSV', 'TEST_TSV'}:
                constant_values.setdefault(key, Counter()).update([repr(value)])

    all_files = memory_files + code_files
    patterns = {
        'target_gene_count_6640': r'6640|6,640',
        'training_samples_1388': r'1388|1,388',
        'perturbation_count_1542': r'1542|1,542',
        'aido': r'AIDO|AIDO\.Cell',
        'scfoundation': r'scFoundation',
        'string_gnn': r'STRING_GNN|STRING',
        'data_files': r'train\.tsv|val\.tsv|test\.tsv|TRAIN_TSV|VAL_TSV|TEST_TSV',
        'class_frequency': r'CLASS_FREQ|0\.0429|0\.9251|0\.0320',
        'metric': r'per-gene|macro|val/f1|val_f1|test/f1|Test F1',
    }
    hits = regex_hits(all_files, patterns)

    model_terms = Counter()
    for path in memory_files:
        text = path.read_text(errors='replace')
        for term in ['AIDO.Cell-100M', 'AIDO.Cell-10M', 'scFoundation', 'STRING_GNN', 'LoRA', 'NeighborhoodAttention', 'GenePriorBias', 'GatedFusion', 'SWA', 'bilinear', 'Muon', 'AdamW']:
            if re.search(re.escape(term), text, flags=re.I):
                model_terms[term] += 1

    node_scores = []
    for path in memory_files:
        text = path.read_text(errors='replace')
        score = score_from_memory(text)
        if score is not None:
            node_scores.append({'node': path.stem, 'score': score})
    node_scores.sort(key=lambda x: x['score'], reverse=True)

    out = {
        'official_vcharness_dir': str(base),
        'mcts_metadata': {k: mcts.get(k) for k in ['best_score', 'best_score_display', 'min_score', 'max_score', 'score_direction', 'current_step', 'exploration_c', 'total_nodes', 'draft_nodes', 'improvement_nodes', 'global_best_node']},
        'file_counts': {'memory_md': len(memory_files), 'code_py': len(code_files), 'curve_png': len(list((base / 'static').glob('*_curve.png')))},
        'constant_value_counts': {k: dict(v.most_common(10)) for k, v in sorted(constant_values.items())},
        'regex_evidence': {k: v[:20] for k, v in hits.items()},
        'regex_evidence_counts': {k: len(v) for k, v in hits.items()},
        'model_term_counts_in_memory': dict(model_terms.most_common()),
        'top_scores_from_memory': node_scores[:20],
        'best_node': {
            'id': best_node,
            'memory_path': str(best_memory),
            'code_path': str(best_code),
            'memory_excerpt': read_text(best_memory, 2200) if best_memory.exists() else None,
            'code_header_excerpt': read_text(best_code, 2600) if best_code.exists() else None,
            'constants': literal_constants(best_code) if best_code.exists() else {},
        },
        'current_repo': {
            'k562_concat': summarize_current_manifest(repo, 'data/cell_lines/k562_concat/manifest.json'),
            'k562_concat_esm2_gene_embedding': summarize_current_manifest(repo, 'data/cell_lines/k562_concat_esm2_gene_embedding/manifest.json'),
        },
        'inferred_alignment_gaps': [
            'Official visible K562 code uses N_GENES=6640; current repo K562 manifests use n_target_genes=1000.',
            'Official memory repeatedly cites 1,388 training samples; current repo uses train/val/test perturbation rows 73/16/16.',
            'Official best node uses AIDO.Cell-100M and STRING_GNN model directories; current repo has ESM2/STRING/Reactome artifacts but no AIDO.Cell checkpoint or official STRING_GNN checkpoint.',
            'Official code expects train.tsv/val.tsv/test.tsv with labels per perturbation row; public VCHarness tree inspected here does not include those TSV data files.',
            'Official metric implementation is per-gene macro F1 over 3 classes and 6,640 genes; current repo reports Macro-F1 on a 1,000-gene local label universe.',
        ],
    }

    out_path = repo / args.out_json
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps({'wrote': str(out_path), 'best_node': best_node, 'memory_files': len(memory_files), 'code_files': len(code_files)}, indent=2))


if __name__ == '__main__':
    main()
