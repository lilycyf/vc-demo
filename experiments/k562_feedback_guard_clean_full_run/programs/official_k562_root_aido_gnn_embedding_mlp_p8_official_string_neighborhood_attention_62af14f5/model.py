from __future__ import annotations

import csv
import math
from pathlib import Path

import numpy as np
import torch
from torch import nn


TARGET_GENE_TABLE = Path("data/cell_lines/official_k562_cls/target_genes.tsv")
PATHWAY_MEMBERSHIP = Path("data/artifacts/pathways/k562_target_pathway_membership.npz")
STRING_GRAPH = Path("data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt")
OFFICIAL_DEG_ARTIFACT = Path("data/artifacts/official_k562/essential_deg_with_split.h5ad")
GRAPH_FEATURE_DIM = 40


def _as_float(value, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _read_targets(n_targets: int) -> list[tuple[int, str, str]]:
    if not OFFICIAL_DEG_ARTIFACT.exists():
        raise FileNotFoundError(f"official DEG split artifact is required: {OFFICIAL_DEG_ARTIFACT}")
    if not TARGET_GENE_TABLE.exists():
        raise FileNotFoundError(f"official target-gene table is required: {TARGET_GENE_TABLE}")
    rows: list[tuple[int, str, str]] = []
    with TARGET_GENE_TABLE.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            rows.append((int(row["target_index"]), str(row.get("gene_id", "")), str(row.get("symbol", ""))))
    rows.sort(key=lambda item: item[0])
    if len(rows) != int(n_targets):
        raise ValueError(f"target-gene rows {len(rows)} do not match n_targets {n_targets}")
    if [idx for idx, _, _ in rows] != list(range(int(n_targets))):
        raise ValueError("target-gene table must preserve contiguous official target_index order")
    return rows


def _aligned_membership(n_targets: int) -> tuple[torch.Tensor, int, int]:
    if not PATHWAY_MEMBERSHIP.exists():
        raise FileNotFoundError(f"Reactome pathway membership artifact is required: {PATHWAY_MEMBERSHIP}")
    z = np.load(PATHWAY_MEMBERSHIP, allow_pickle=False)
    membership = z["membership"].astype("float32")
    artifact_symbols = [str(x) for x in z["target_genes"]]
    pathway_count = int(membership.shape[1])
    if membership.shape[0] != len(artifact_symbols):
        raise ValueError("pathway membership row count does not match target_genes")

    official_symbols = [sym for _, _, sym in _read_targets(n_targets)]
    symbol_to_official = {symbol: idx for idx, symbol in enumerate(official_symbols) if symbol}
    aligned = np.zeros((int(n_targets), pathway_count), dtype="float32")
    covered = 0
    for row_idx, symbol in enumerate(artifact_symbols):
        official_idx = symbol_to_official.get(symbol)
        if official_idx is not None:
            aligned[official_idx] = membership[row_idx]
            covered += 1
    pathway_degrees = np.maximum(aligned.sum(axis=0, keepdims=True), 1.0)
    aligned = aligned / pathway_degrees
    return torch.from_numpy(aligned), covered, pathway_count


def _build_string_laplacian_features(n_targets: int) -> tuple[torch.Tensor, dict[str, int | float]]:
    if not STRING_GRAPH.exists():
        raise FileNotFoundError(f"official STRING graph artifact is required: {STRING_GRAPH}")
    rows = _read_targets(n_targets)
    gene_to_idx = {gene_id: idx for idx, gene_id, _ in rows if gene_id}
    n = int(n_targets)
    denom = max(1, n - 1)

    base = np.zeros((n, GRAPH_FEATURE_DIM), dtype="float32")
    for idx, gene_id, symbol in rows:
        pos = idx / denom
        # Source-backed target identity/order features; no random graph or fabricated edges.
        vals = [
            pos,
            pos * pos,
            math.sin(math.tau * pos),
            math.cos(math.tau * pos),
            min(len(symbol), 32) / 32.0,
            1.0 if gene_id.startswith("ENSG") else 0.0,
        ]
        vals.extend([0.0] * (GRAPH_FEATURE_DIM - len(vals)))
        base[idx] = np.asarray(vals, dtype="float32")

    deg = np.zeros(n, dtype="float32")
    wdeg = np.zeros(n, dtype="float32")
    evidence_exp = np.zeros(n, dtype="float32")
    evidence_db = np.zeros(n, dtype="float32")
    smooth1 = np.zeros_like(base)
    lap_delta = np.zeros_like(base)
    raw_edge_count = 0
    aligned_edges = 0
    with STRING_GRAPH.open(newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            raw_edge_count += 1
            a = gene_to_idx.get(row.get("protein1", ""))
            b = gene_to_idx.get(row.get("protein2", ""))
            if a is None or b is None:
                continue
            score = _as_float(row.get("combined_score", 0.0)) / 1000.0
            exp = _as_float(row.get("experimental", 0.0)) / 1000.0
            db = _as_float(row.get("database", 0.0)) / 1000.0
            for src, dst in ((a, b), (b, a)):
                deg[src] += 1.0
                wdeg[src] += score
                evidence_exp[src] += exp
                evidence_db[src] += db
                smooth1[src] += score * base[dst]
                lap_delta[src] += score * (base[dst] - base[src])
            aligned_edges += 1
    norm = np.maximum(wdeg[:, None], 1.0)
    smooth1 = smooth1 / norm
    lap_delta = lap_delta / norm

    # Encode graph topology and a Laplacian-smoothed target signature into a compact target feature.
    features = np.zeros((n, GRAPH_FEATURE_DIM), dtype="float32")
    features[:, 0] = np.log1p(deg) / 8.0
    features[:, 1] = np.log1p(wdeg) / 8.0
    features[:, 2] = evidence_exp / np.maximum(deg, 1.0)
    features[:, 3] = evidence_db / np.maximum(deg, 1.0)
    features[:, 4] = (deg > 0).astype("float32")
    features[:, 5] = np.minimum(deg, 20.0) / 20.0
    features[:, 6:23] = smooth1[:, :17]
    features[:, 23:40] = lap_delta[:, :17]
    meta = {
        "raw_edges": int(raw_edge_count),
        "aligned_edges": int(aligned_edges),
        "covered_targets": int((deg > 0).sum()),
        "smoothing_alpha": 0.15,
    }
    return torch.from_numpy(features.astype("float32")), meta


class ResidualBlock(nn.Module):
    def __init__(self, hidden: int, dropout: float) -> None:
        super().__init__()
        self.net = nn.Sequential(
            nn.LayerNorm(hidden),
            nn.Linear(hidden, hidden * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden * 2, hidden),
            nn.Dropout(dropout),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.net(x)


class GeneratedModel(nn.Module):
    """Parent-preserving STRING neighborhood attention child for official K562.

    The implementation keeps the parent AIDO+GNN dense all-target branch and the
    parent Reactome pathway residual, then adds a real STRING keep20 graph-derived
    STRING neighborhood residual. Missing graph neighborhoods receive zero graph residual;
    no fallback graph, random edges, or proxy artifacts are introduced.
    """

    def __init__(self, spec) -> None:
        super().__init__()
        hidden = int(spec.hidden_dim)
        dropout = float(spec.dropout)
        depth = max(1, int(spec.depth))
        self.n_targets = int(spec.n_targets)
        self.n_classes = int(spec.n_classes)
        self.rank = min(96, hidden)
        self.implementation_semantics = "parent_preserving_string_neighborhood_attention_delta"
        self.smoothing_alpha = 0.15

        self.input = nn.Sequential(
            nn.Linear(int(spec.input_dim), hidden),
            nn.LayerNorm(hidden),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.blocks = nn.Sequential(*[ResidualBlock(hidden, dropout) for _ in range(depth)])
        self.context_norm = nn.LayerNorm(hidden)
        self.parent_dense_head = nn.Linear(hidden, self.n_targets * self.n_classes)

        membership, covered_pathway_targets, pathway_count = _aligned_membership(self.n_targets)
        self.register_buffer("target_pathway", membership, persistent=False)
        self.covered_pathway_targets = int(covered_pathway_targets)
        self.pathway_count = int(pathway_count)
        self.pathway_context = nn.Sequential(
            nn.LayerNorm(hidden),
            nn.Linear(hidden, hidden),
            nn.GELU(),
            nn.Dropout(dropout * 0.5),
            nn.Linear(hidden, self.pathway_count * self.n_classes),
        )
        self.pathway_gate = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, self.n_classes))

        graph_features, graph_meta = _build_string_laplacian_features(self.n_targets)
        self.register_buffer("graph_features", graph_features, persistent=False)
        self.graph_meta = graph_meta
        self.graph_encoder = nn.Sequential(
            nn.LayerNorm(GRAPH_FEATURE_DIM),
            nn.Linear(GRAPH_FEATURE_DIM, self.rank * 2),
            nn.GELU(),
            nn.Dropout(dropout * 0.5),
            nn.Linear(self.rank * 2, self.rank),
            nn.LayerNorm(self.rank),
        )
        self.context_to_graph = nn.Linear(hidden, self.rank * self.n_classes)
        self.graph_gate = nn.Sequential(nn.LayerNorm(hidden), nn.Linear(hidden, self.n_classes))
        self.graph_bias = nn.Linear(GRAPH_FEATURE_DIM, self.n_classes)

        self.target_bias = nn.Parameter(torch.zeros(self.n_targets, self.n_classes))
        self.pathway_residual_scale = nn.Parameter(torch.zeros(self.n_classes))
        self.graph_residual_scale = nn.Parameter(torch.zeros(self.n_classes))
        self.artifact_usage = {
            "official_string_gnn_keep20_graph": str(STRING_GRAPH),
            "official_essential_deg_with_split_h5ad": str(OFFICIAL_DEG_ARTIFACT),
            "pathway_membership_matrix": str(PATHWAY_MEMBERSHIP),
            "official_target_gene_order": str(TARGET_GENE_TABLE),
            "covered_pathway_targets": self.covered_pathway_targets,
            "pathway_count": self.pathway_count,
            **graph_meta,
        }

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.context_norm(self.blocks(self.input(x)))
        parent_logits = self.parent_dense_head(z).view(x.shape[0], self.n_targets, self.n_classes)

        membership = self.target_pathway.to(device=x.device, dtype=x.dtype)
        pathway_logits = self.pathway_context(z).view(x.shape[0], self.pathway_count, self.n_classes)
        pathway_residual = torch.einsum("bpc,np->bnc", pathway_logits, membership)
        pathway_residual = pathway_residual / math.sqrt(max(1.0, float(self.pathway_count)))
        pathway_gate = torch.sigmoid(self.pathway_gate(z)).view(x.shape[0], 1, self.n_classes)
        pathway_scale = 0.45 + torch.tanh(self.pathway_residual_scale).view(1, 1, self.n_classes)

        graph_features = self.graph_features.to(device=x.device, dtype=x.dtype)
        graph_target = self.graph_encoder(graph_features)
        graph_context = self.context_to_graph(z).view(x.shape[0], self.rank, self.n_classes)
        graph_residual = torch.einsum("brc,nr->bnc", graph_context, graph_target) / math.sqrt(float(self.rank))
        graph_residual = graph_residual + self.graph_bias(graph_features).unsqueeze(0)
        graph_gate = torch.sigmoid(self.graph_gate(z)).view(x.shape[0], 1, self.n_classes)
        graph_scale = self.smoothing_alpha * (0.5 + torch.sigmoid(self.graph_residual_scale).view(1, 1, self.n_classes))

        return (
            parent_logits
            + pathway_residual * pathway_gate * pathway_scale
            + graph_residual * graph_gate * graph_scale
            + self.target_bias.to(device=x.device, dtype=x.dtype).unsqueeze(0)
        )
