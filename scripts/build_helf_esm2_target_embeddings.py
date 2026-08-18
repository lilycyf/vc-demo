from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import numpy as np
import requests
import torch
from transformers import AutoModel, AutoTokenizer


def load_target_genes(data_dir: Path) -> list[str]:
    train = np.load(data_dir / "train.npz", allow_pickle=True)
    return [str(x) for x in train["target_genes"]]


def download_uniprot_human_tsv(cache_path: Path) -> list[dict[str, str]]:
    """Download/cache human UniProt sequences for local gene-symbol lookup."""
    if not cache_path.exists() or cache_path.stat().st_size == 0:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        url = "https://rest.uniprot.org/uniprotkb/stream"
        params = {
            "query": "organism_id:9606",
            "format": "tsv",
            "fields": "accession,gene_primary,gene_names,protein_name,sequence,reviewed",
        }
        with requests.get(url, params=params, stream=True, timeout=120) as response:
            response.raise_for_status()
            with cache_path.open("wb") as fh:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        fh.write(chunk)
    rows: list[dict[str, str]] = []
    header: list[str] | None = None
    for line in cache_path.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        parts = line.split("\t")
        if header is None:
            header = parts
            continue
        row = {header[i]: parts[i] if i < len(parts) else "" for i in range(len(header))}
        if row.get("Sequence"):
            rows.append(row)
    return rows


def build_gene_index(rows: list[dict[str, str]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for row in rows:
        names: list[str] = []
        primary = row.get("Gene Names (primary)", "").strip()
        if primary:
            names.append(primary)
        names.extend(row.get("Gene Names", "").replace(";", " ").split())
        for name in names:
            key = name.upper()
            current = index.get(key)
            candidate = {
                "gene": name,
                "accession": row.get("Entry"),
                "entry_type": row.get("Reviewed", ""),
                "protein_name": row.get("Protein names"),
                "sequence": row.get("Sequence"),
            }
            if current is None or (candidate["entry_type"] == "reviewed" and current.get("entry_type") != "reviewed"):
                index[key] = candidate
    return index

def mean_pool(outputs: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    token_embeddings = outputs[:, 1:-1]
    token_mask = mask[:, 1:-1].unsqueeze(-1).to(token_embeddings.dtype)
    return (token_embeddings * token_mask).sum(dim=1) / token_mask.sum(dim=1).clamp_min(1.0)


def build(data_dir: Path, output: Path, summary: Path, model_name: str, batch_size: int, uniprot_cache: Path, device_arg: str) -> dict[str, Any]:
    os.environ.setdefault("HF_HOME", "/workspace/.cache/huggingface")
    genes = load_target_genes(data_dir)
    uniprot_rows = download_uniprot_human_tsv(uniprot_cache)
    gene_index = build_gene_index(uniprot_rows)
    seq_rows = []
    missing = []
    for gene in genes:
        hit = gene_index.get(str(gene).upper())
        if hit:
            row = dict(hit)
            row["gene"] = gene
            row["query_source"] = str(uniprot_cache)
            seq_rows.append(row)
        else:
            missing.append(gene)
            seq_rows.append({"gene": gene, "sequence": None, "query_source": str(uniprot_cache)})
    print(json.dumps({"stage": "sequence_alignment", "targets": len(genes), "covered": len(genes) - len(missing), "missing": len(missing), "cache": str(uniprot_cache)}, indent=2), flush=True)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModel.from_pretrained(model_name)
    if device_arg == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device = device_arg
    print(json.dumps({"stage": "model_loaded", "model_name": model_name, "device": device}, indent=2), flush=True)
    model.to(device).eval()
    hidden = int(model.config.hidden_size)
    embeddings = np.zeros((len(genes), hidden), dtype=np.float32)
    covered_indices = [i for i, row in enumerate(seq_rows) if row.get("sequence")]
    with torch.no_grad():
        for start in range(0, len(covered_indices), batch_size):
            idxs = covered_indices[start:start + batch_size]
            if start % max(batch_size * 10, 1) == 0:
                print(json.dumps({"stage": "embedding_batch", "done": start, "total": len(covered_indices)}, indent=2), flush=True)
            seqs = [str(seq_rows[i]["sequence"]) for i in idxs]
            encoded = tokenizer(seqs, return_tensors="pt", padding=True, truncation=True, max_length=1024)
            encoded = {k: v.to(device) for k, v in encoded.items()}
            out = model(**encoded).last_hidden_state
            pooled = mean_pool(out, encoded["attention_mask"]).cpu().float().numpy()
            embeddings[idxs] = pooled
    output.parent.mkdir(parents=True, exist_ok=True)
    coverage_mask = np.array([bool(row.get("sequence")) for row in seq_rows], dtype=bool)
    np.savez_compressed(output, target_gene_embeddings=embeddings, target_genes=np.array(genes), coverage_mask=coverage_mask, model_name=model_name, source="UniProt REST + HuggingFace ESM2 mean-pooled protein embeddings")
    report = {
        "format": "helf_esm2_target_gene_embeddings.v1",
        "artifact_id": "esm2_gene_or_protein_embeddings",
        "output": str(output),
        "model_name": model_name,
        "source": "Cached UniProt human protein TSV + HuggingFace ESM2 mean-pooled protein embeddings",
        "uniprot_cache": str(uniprot_cache),
        "n_targets": len(genes),
        "covered_targets": int(coverage_mask.sum()),
        "coverage": float(coverage_mask.mean()),
        "embedding_shape": list(embeddings.shape),
        "device": device,
        "missing_target_genes": missing,
        "sequence_rows": [{k: v for k, v in row.items() if k != "sequence"} for row in seq_rows],
    }
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build HELF target-gene ESM2 embedding artifact from UniProt sequences.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/cell_lines/aivc_helf_perturb_deg_cls"))
    parser.add_argument("--output", type=Path, default=Path("data/artifacts/helf/esm2_gene_embeddings.npz"))
    parser.add_argument("--summary", type=Path, default=Path("experiments/aivc_search_space_manifest_audit/helf_esm2_target_embedding_artifact_summary.json"))
    parser.add_argument("--model-name", default="facebook/esm2_t33_650M_UR50D")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--uniprot-cache", type=Path, default=Path("data/artifacts/helf/uniprot_human_sequences.tsv"))
    parser.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto")
    args = parser.parse_args()
    print(json.dumps(build(args.data_dir, args.output, args.summary, args.model_name, args.batch_size, args.uniprot_cache, args.device), indent=2))


if __name__ == "__main__":
    main()
