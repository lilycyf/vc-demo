from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np


def post_tsv(url: str, params: dict[str, object], timeout: int = 180) -> list[dict[str, str]]:
    data = urlencode(params).encode()
    req = Request(url, data=data, method="POST")
    with urlopen(req, timeout=timeout) as resp:
        text = resp.read().decode("utf-8")
    if not text.strip():
        return []
    return list(csv.DictReader(text.splitlines(), delimiter="\t"))


def get_string_version() -> dict[str, str]:
    with urlopen("https://string-db.org/api/json/version", timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload[0]


def load_gene_sets(data_dir: Path) -> tuple[list[str], list[str]]:
    perturbations: set[str] = set()
    target_genes: list[str] | None = None
    for split in ["train.npz", "val.npz", "test.npz"]:
        with np.load(data_dir / split, allow_pickle=True) as z:
            perturbations.update(str(x) for x in z["perturbations"].tolist())
            tg = [str(x) for x in z["target_genes"].tolist()]
            if target_genes is None:
                target_genes = tg
            elif target_genes != tg:
                raise ValueError(f"target_genes differ in {split}")
    return sorted(perturbations), list(target_genes or [])


def write_tsv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "source_gene",
        "target_gene",
        "score",
        "source",
        "evidence/version",
        "source_string_id",
        "target_string_id",
        "source_string_name",
        "target_string_name",
        "nscore",
        "fscore",
        "pscore",
        "ascore",
        "escore",
        "dscore",
        "tscore",
    ]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a K562-aligned STRING/PPI induced subgraph artifact.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/cell_lines/k562_concat_esm2_gene_embedding"))
    parser.add_argument("--output", type=Path, default=Path("data/artifacts/string/k562_target_graph_edges.tsv"))
    parser.add_argument("--summary", type=Path, default=Path("experiments/k562_string_graph_artifact_summary.json"))
    parser.add_argument("--species", type=int, default=9606)
    parser.add_argument("--score-threshold", type=float, default=0.4)
    parser.add_argument("--caller-identity", default="vc-demo-k562-string-artifact")
    args = parser.parse_args()

    perturbation_genes, target_genes = load_gene_sets(args.data_dir)
    all_genes = sorted(set(perturbation_genes) | set(target_genes))
    version = get_string_version()
    stable = version.get("stable_address") or "https://string-db.org"
    api_base = stable.rstrip("/") + "/api/tsv"

    mapping_rows = post_tsv(
        api_base + "/get_string_ids",
        {
            "identifiers": "\r".join(all_genes),
            "species": args.species,
            "caller_identity": args.caller_identity,
        },
    )
    string_to_dataset: dict[str, set[str]] = defaultdict(set)
    dataset_to_string: dict[str, str] = {}
    mapped_preferred: dict[str, str] = {}
    for row in mapping_rows:
        query_index = int(row["queryIndex"])
        gene = all_genes[query_index]
        sid = row["stringId"]
        dataset_to_string[gene] = sid
        string_to_dataset[sid].add(gene)
        mapped_preferred[gene] = row.get("preferredName", "")

    string_ids = sorted(set(dataset_to_string.values()))
    network_rows = post_tsv(
        api_base + "/network",
        {
            "identifiers": "\r".join(string_ids),
            "species": args.species,
            "required_score": 0,
            "caller_identity": args.caller_identity,
        },
        timeout=300,
    )

    out_rows: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    raw_edge_count = 0
    for row in network_rows:
        a = row.get("stringId_A", "")
        b = row.get("stringId_B", "")
        if a not in string_to_dataset or b not in string_to_dataset:
            continue
        raw_edge_count += 1
        score = float(row.get("score", 0.0))
        if score < args.score_threshold:
            continue
        for ga in string_to_dataset[a]:
            for gb in string_to_dataset[b]:
                if ga == gb:
                    continue
                left, right = sorted((ga, gb))
                key = (left, right)
                if key in seen:
                    continue
                seen.add(key)
                out_rows.append(
                    {
                        "source_gene": left,
                        "target_gene": right,
                        "score": f"{score:.6f}",
                        "source": "STRING official network API",
                        "evidence/version": f"STRING v{version.get('string_version','unknown')}; stable={stable}; required_score_api=0; retained_score_threshold={args.score_threshold}",
                        "source_string_id": dataset_to_string[left],
                        "target_string_id": dataset_to_string[right],
                        "source_string_name": mapped_preferred.get(left, ""),
                        "target_string_name": mapped_preferred.get(right, ""),
                        "nscore": row.get("nscore", ""),
                        "fscore": row.get("fscore", ""),
                        "pscore": row.get("pscore", ""),
                        "ascore": row.get("ascore", ""),
                        "escore": row.get("escore", ""),
                        "dscore": row.get("dscore", ""),
                        "tscore": row.get("tscore", ""),
                    }
                )

    out_rows.sort(key=lambda r: (str(r["source_gene"]), str(r["target_gene"])))
    write_tsv(args.output, out_rows)

    graph_nodes = {str(r["source_gene"]) for r in out_rows} | {str(r["target_gene"]) for r in out_rows}
    pert_graph = sorted(set(perturbation_genes) & graph_nodes)
    target_graph = sorted(set(target_genes) & graph_nodes)
    summary = {
        "artifact": "string_k562_gene_graph",
        "output": str(args.output),
        "source_url": api_base + "/network",
        "mapping_url": api_base + "/get_string_ids",
        "source": "STRING official network API",
        "version": version,
        "species": args.species,
        "data_dir": str(args.data_dir),
        "filtering_rule": "Map K562 perturbation and target gene symbols to STRING protein IDs, query the official STRING v12.0 network API for the union, keep induced-subgraph edges where both endpoints map back to K562 genes and combined score >= 0.4.",
        "score_threshold": args.score_threshold,
        "n_perturbation_genes": len(perturbation_genes),
        "n_target_genes": len(target_genes),
        "n_union_genes": len(all_genes),
        "mapped_gene_count": len(dataset_to_string),
        "unmapped_gene_count": len(all_genes) - len(dataset_to_string),
        "unmapped_genes": sorted(set(all_genes) - set(dataset_to_string)),
        "raw_edge_count": raw_edge_count,
        "filtered_edge_count": len(out_rows),
        "node_count": len(graph_nodes),
        "perturbation_gene_graph_coverage": len(pert_graph) / len(perturbation_genes),
        "target_gene_graph_coverage": len(target_graph) / len(target_genes),
        "covered_perturbation_genes": pert_graph,
        "covered_target_genes_count": len(target_graph),
        "missing_perturbation_genes": sorted(set(perturbation_genes) - graph_nodes),
        "missing_target_genes": sorted(set(target_genes) - graph_nodes),
        "columns": [
            "source_gene",
            "target_gene",
            "score",
            "source",
            "evidence/version",
            "source_string_id",
            "target_string_id",
            "source_string_name",
            "target_string_name",
            "nscore",
            "fscore",
            "pscore",
            "ascore",
            "escore",
            "dscore",
            "tscore",
        ],
    }
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ["output", "source_url", "raw_edge_count", "filtered_edge_count", "node_count", "perturbation_gene_graph_coverage", "target_gene_graph_coverage", "unmapped_gene_count"]}, indent=2))


if __name__ == "__main__":
    main()
