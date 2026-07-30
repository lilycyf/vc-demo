from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import torch
from safetensors.torch import save_file
from torch import nn
import torch.nn.functional as F


@dataclass
class TrainConfig:
    graph_tsv: str
    teacher_h5ad: str
    output_dir: str
    export_dir: str
    hidden_dim: int = 512
    output_dim: int = 256
    layers: int = 3
    dropout: float = 0.10
    lr: float = 0.002
    weight_decay: float = 1e-4
    epochs: int = 100
    patience: int = 20
    seeds: tuple[int, ...] = (3, 7, 11)
    smoothness_weight: float = 0.01
    smooth_edges: int = 100000
    train_fraction: float = 0.80
    val_fraction: float = 0.10
    device: str = "cuda"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(values: list[str]) -> str:
    h = hashlib.sha256()
    for value in values:
        h.update(value.encode())
        h.update(b"\n")
    return h.hexdigest()


def read_h5ad_embedding(path: Path) -> tuple[list[str], torch.Tensor]:
    with h5py.File(path, "r") as f:
        node_names = [x.decode() if isinstance(x, bytes) else str(x) for x in f["obs/ensembl_gene_id"][:]]
        x = f["X"]
        if isinstance(x, h5py.Dataset):
            arr = np.asarray(x[:], dtype=np.float32)
        else:
            data = x["data"][:]
            indices = x["indices"][:]
            indptr = x["indptr"][:]
            n_rows = len(indptr) - 1
            n_cols = len(f["var/var_id"][:])
            arr = np.zeros((n_rows, n_cols), dtype=np.float32)
            for row in range(n_rows):
                start, end = int(indptr[row]), int(indptr[row + 1])
                arr[row, indices[start:end]] = data[start:end]
    if arr.shape[0] != len(node_names):
        raise ValueError(f"node count mismatch: X={arr.shape}, obs={len(node_names)}")
    return node_names, torch.from_numpy(arr)


def read_edges(path: Path, node_to_idx: dict[str, int]) -> tuple[torch.Tensor, torch.Tensor, dict[str, Any]]:
    src: list[int] = []
    dst: list[int] = []
    weight: list[float] = []
    raw = 0
    kept = 0
    with path.open() as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            raw += 1
            a = row.get("protein1")
            b = row.get("protein2")
            if a not in node_to_idx or b not in node_to_idx:
                continue
            score = float(row.get("combined_score", 0.0)) / 1000.0
            if score <= 0:
                continue
            ia = node_to_idx[a]
            ib = node_to_idx[b]
            src.extend([ia, ib])
            dst.extend([ib, ia])
            weight.extend([score, score])
            kept += 1
    edge_index = torch.tensor([src, dst], dtype=torch.long)
    edge_weight = torch.tensor(weight, dtype=torch.float32)
    stats = {
        "raw_edges": raw,
        "kept_undirected_pairs": kept,
        "directed_edges": int(edge_index.shape[1]),
        "node_coverage": len(set(src).union(dst)) / max(1, len(node_to_idx)),
    }
    return edge_index, edge_weight, stats


def normalized_edge_weight(edge_index: torch.Tensor, edge_weight: torch.Tensor, n_nodes: int) -> torch.Tensor:
    dst = edge_index[1]
    denom = torch.zeros(n_nodes, dtype=torch.float32)
    denom.index_add_(0, dst.cpu(), edge_weight.cpu())
    return edge_weight.cpu() / denom[dst.cpu()].clamp_min(1e-8)


def deterministic_split(node_names: list[str], train_fraction: float, val_fraction: float) -> dict[str, list[int]]:
    buckets = [(hashlib.sha256(name.encode()).hexdigest(), i) for i, name in enumerate(node_names)]
    order = [i for _, i in sorted(buckets)]
    n = len(order)
    n_train = int(n * train_fraction)
    n_val = int(n * val_fraction)
    return {"train": order[:n_train], "val": order[n_train:n_train + n_val], "test": order[n_train + n_val:]}


class GraphSageLayer(nn.Module):
    def __init__(self, dim_in: int, dim_out: int, dropout: float) -> None:
        super().__init__()
        self.self_proj = nn.Linear(dim_in, dim_out)
        self.neigh_proj = nn.Linear(dim_in, dim_out)
        self.norm = nn.LayerNorm(dim_out)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x: torch.Tensor, edge_index: torch.Tensor, edge_weight: torch.Tensor) -> torch.Tensor:
        src, dst = edge_index
        neigh = torch.zeros_like(x)
        neigh.index_add_(0, dst, x[src] * edge_weight.unsqueeze(-1))
        z = self.self_proj(x) + self.neigh_proj(neigh)
        return self.dropout(F.gelu(self.norm(z)))


class PublicStringGNN(nn.Module):
    def __init__(self, n_nodes: int, hidden_dim: int, output_dim: int, layers: int, dropout: float) -> None:
        super().__init__()
        self.node_features = nn.Embedding(n_nodes, hidden_dim)
        nn.init.normal_(self.node_features.weight, std=0.02)
        self.layers = nn.ModuleList(GraphSageLayer(hidden_dim, hidden_dim, dropout) for _ in range(layers))
        self.output = nn.Sequential(nn.LayerNorm(hidden_dim), nn.Linear(hidden_dim, output_dim))

    def forward(self, edge_index: torch.Tensor, edge_weight: torch.Tensor) -> torch.Tensor:
        x = self.node_features.weight
        for layer in self.layers:
            x = x + layer(x, edge_index, edge_weight)
        return self.output(x)


def evaluate(pred: torch.Tensor, target: torch.Tensor, idx: torch.Tensor) -> dict[str, float]:
    p = pred[idx]
    t = target[idx]
    return {
        "mse": F.mse_loss(p, t).item(),
        "cosine": F.cosine_similarity(p, t, dim=-1).mean().item(),
    }


def reconstruction_loss(pred: torch.Tensor, target: torch.Tensor, idx: torch.Tensor) -> tuple[torch.Tensor, dict[str, float]]:
    p = pred[idx]
    t = target[idx]
    mse = F.mse_loss(p, t)
    cos = 1.0 - F.cosine_similarity(p, t, dim=-1).mean()
    return mse + cos, {"mse": float(mse.detach().cpu()), "cosine_loss": float(cos.detach().cpu())}


def neighbor_preservation(pred: torch.Tensor, target: torch.Tensor, sample_idx: torch.Tensor, k: int = 10) -> dict[str, float]:
    p = F.normalize(pred, dim=-1)
    t = F.normalize(target, dim=-1)
    sim_p = p[sample_idx] @ p.T
    sim_t = t[sample_idx] @ t.T
    pred_top = sim_p.topk(k + 1, dim=-1).indices[:, 1:]
    true_top = sim_t.topk(k + 1, dim=-1).indices[:, 1:]
    overlaps = []
    for a, b in zip(pred_top.cpu().tolist(), true_top.cpu().tolist()):
        overlaps.append(len(set(a).intersection(b)) / k)
    return {f"top{k}_overlap": float(np.mean(overlaps)), "sample_size": int(len(overlaps))}


def train_one_seed(cfg: TrainConfig, node_names: list[str], teacher_cpu: torch.Tensor, edge_index_cpu: torch.Tensor, edge_weight_cpu: torch.Tensor, split: dict[str, list[int]], seed: int) -> dict[str, Any]:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    device = torch.device(cfg.device if cfg.device == "cuda" and torch.cuda.is_available() else "cpu")
    teacher = teacher_cpu.to(device)
    edge_index = edge_index_cpu.to(device)
    edge_weight = edge_weight_cpu.to(device)
    train_idx = torch.tensor(split["train"], dtype=torch.long, device=device)
    val_idx = torch.tensor(split["val"], dtype=torch.long, device=device)
    test_idx = torch.tensor(split["test"], dtype=torch.long, device=device)
    model = PublicStringGNN(len(node_names), cfg.hidden_dim, cfg.output_dim, cfg.layers, cfg.dropout).to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    smooth_src = smooth_dst = None
    if cfg.smoothness_weight > 0 and edge_index.shape[1] > 0:
        generator = torch.Generator(device="cpu").manual_seed(seed + 9001)
        n_edges = min(cfg.smooth_edges, edge_index.shape[1])
        choice = torch.randperm(edge_index.shape[1], generator=generator)[:n_edges].to(device)
        smooth_src = edge_index[0, choice]
        smooth_dst = edge_index[1, choice]
    best_record: dict[str, Any] | None = None
    best_state: dict[str, torch.Tensor] | None = None
    history: list[dict[str, Any]] = []
    patience_left = cfg.patience
    t0 = time.time()
    for epoch in range(1, cfg.epochs + 1):
        model.train()
        opt.zero_grad(set_to_none=True)
        pred = model(edge_index, edge_weight)
        loss, parts = reconstruction_loss(pred, teacher, train_idx)
        if smooth_src is not None and smooth_dst is not None:
            smooth = F.mse_loss(pred[smooth_src], pred[smooth_dst])
            loss = loss + cfg.smoothness_weight * smooth
            parts["smoothness"] = float(smooth.detach().cpu())
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        model.eval()
        with torch.no_grad():
            pred = model(edge_index, edge_weight)
            rec = {
                "epoch": epoch,
                "loss": float(loss.detach().cpu()),
                "train": evaluate(pred, teacher, train_idx),
                "val": evaluate(pred, teacher, val_idx),
                "test": evaluate(pred, teacher, test_idx),
                "parts": parts,
            }
        history.append(rec)
        if best_record is None or rec["val"]["cosine"] > best_record["val"]["cosine"]:
            best_record = rec
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
            patience_left = cfg.patience
        else:
            patience_left -= 1
        if epoch == 1 or epoch % 10 == 0 or epoch == cfg.epochs:
            print(json.dumps({"seed": seed, "epoch": epoch, "val_cosine": rec["val"]["cosine"], "best_val_cosine": best_record["val"]["cosine"]}), flush=True)
        if patience_left <= 0:
            break
    assert best_record is not None and best_state is not None
    model.load_state_dict(best_state)
    model.eval()
    with torch.no_grad():
        best_pred = model(edge_index, edge_weight).detach().cpu()
    sample = torch.tensor(split["test"][: min(1024, len(split["test"]))], dtype=torch.long)
    best_metrics = {
        "train": evaluate(best_pred, teacher_cpu, torch.tensor(split["train"])),
        "val": evaluate(best_pred, teacher_cpu, torch.tensor(split["val"])),
        "test": evaluate(best_pred, teacher_cpu, torch.tensor(split["test"])),
        "neighbor_preservation": neighbor_preservation(best_pred, teacher_cpu, sample, k=10),
    }
    seed_dir = Path(cfg.output_dir) / f"seed_{seed}"
    seed_dir.mkdir(parents=True, exist_ok=True)
    torch.save(best_state, seed_dir / "best_model.pt")
    torch.save(best_pred, seed_dir / "node_embeddings.pt")
    result = {
        "seed": seed,
        "best_epoch": best_record["epoch"],
        "best_metrics": best_metrics,
        "history": history,
        "seconds": round(time.time() - t0, 3),
        "state_path": str(seed_dir / "best_model.pt"),
        "embedding_path": str(seed_dir / "node_embeddings.pt"),
    }
    (seed_dir / "metrics.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def write_export_model(export_dir: Path, node_names: list[str], graph_data: dict[str, Any], embedding: torch.Tensor, provenance: dict[str, Any]) -> None:
    export_dir.mkdir(parents=True, exist_ok=True)
    (export_dir / "node_names.json").write_text(json.dumps(node_names, indent=2) + "\n")
    torch.save(graph_data, export_dir / "graph_data.pt")
    save_file({"node_embeddings": embedding.contiguous()}, str(export_dir / "model.safetensors"))
    config = {
        "model_type": "string_gnn_public_rebuild",
        "hidden_size": int(embedding.shape[1]),
        "num_nodes": int(embedding.shape[0]),
        "architectures": ["StringGNNPublicRebuildModel"],
        "auto_map": {
            "AutoConfig": "configuration_string_gnn_rebuild.StringGNNPublicRebuildConfig",
            "AutoModel": "modeling_string_gnn_rebuild.StringGNNPublicRebuildModel",
        },
        "provenance": provenance,
    }
    (export_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    (export_dir / "configuration_string_gnn_rebuild.py").write_text('''from __future__ import annotations\n\nfrom transformers import PretrainedConfig\n\n\nclass StringGNNPublicRebuildConfig(PretrainedConfig):\n    model_type = "string_gnn_public_rebuild"\n\n    def __init__(self, hidden_size=256, num_nodes=0, provenance=None, **kwargs):\n        super().__init__(**kwargs)\n        self.hidden_size = hidden_size\n        self.num_nodes = num_nodes\n        self.provenance = provenance or {}\n''')
    (export_dir / "modeling_string_gnn_rebuild.py").write_text('''from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch
from safetensors.torch import load_file

from .configuration_string_gnn_rebuild import StringGNNPublicRebuildConfig


@dataclass
class StringGNNPublicRebuildOutput:
    last_hidden_state: torch.Tensor


class StringGNNPublicRebuildModel(torch.nn.Module):
    config_class = StringGNNPublicRebuildConfig
    generate = None
    prepare_inputs_for_generation = None
    _reorder_cache = None

    def __init__(self, config: StringGNNPublicRebuildConfig):
        super().__init__()
        self.config = config
        self.node_embeddings = torch.nn.Parameter(torch.zeros(int(config.num_nodes), int(config.hidden_size)), requires_grad=False)

    @classmethod
    def from_pretrained(cls, pretrained_model_name_or_path, *model_args, config=None, **kwargs):
        if config is None:
            from transformers import AutoConfig
            config = AutoConfig.from_pretrained(pretrained_model_name_or_path, trust_remote_code=True)
        model = cls(config)
        tensors = load_file(str(Path(pretrained_model_name_or_path) / "model.safetensors"))
        with torch.no_grad():
            model.node_embeddings.copy_(tensors["node_embeddings"])
        return model

    def forward(self, node_indices: Optional[torch.Tensor] = None, **kwargs):
        embeddings = self.node_embeddings
        if node_indices is not None:
            embeddings = embeddings[node_indices]
        return StringGNNPublicRebuildOutput(last_hidden_state=embeddings)
''')
    (export_dir / "README.md").write_text("# STRING_GNN Public Rebuild v1\n\nSource-backed public rebuild trained from public STRING graph and GNN Simple D256 teacher embeddings. This is not the unpublished GenBio/VCHarness original STRING_GNN checkpoint.\n")


def export_best(cfg: TrainConfig, node_names: list[str], edge_index: torch.Tensor, edge_weight: torch.Tensor, graph_stats: dict[str, Any], results: list[dict[str, Any]]) -> dict[str, Any]:
    best = max(results, key=lambda r: r["best_metrics"]["val"]["cosine"])
    embedding = torch.load(best["embedding_path"], map_location="cpu")
    graph_data = {"edge_index": edge_index.cpu(), "edge_weight": edge_weight.cpu(), "node_names": node_names, "graph_stats": graph_stats}
    provenance = {
        "artifact_id": "STRING_GNN_PublicRebuild_v1",
        "not_original_genbio_checkpoint": True,
        "teacher_h5ad": cfg.teacher_h5ad,
        "graph_tsv": cfg.graph_tsv,
        "best_seed": best["seed"],
        "best_epoch": best["best_epoch"],
        "node_order_sha256": sha256_text(node_names),
    }
    export_dir = Path(cfg.export_dir)
    write_export_model(export_dir, node_names, graph_data, embedding, provenance)
    return {"export_dir": str(export_dir), "best_seed": best["seed"], "best_val_cosine": best["best_metrics"]["val"]["cosine"], "embedding_shape": list(embedding.shape)}


def auto_model_smoke(export_dir: Path) -> dict[str, Any]:
    from transformers import AutoModel
    model = AutoModel.from_pretrained(str(export_dir), trust_remote_code=True)
    out = model()
    return {"status": "ok", "class": model.__class__.__name__, "last_hidden_state_shape": list(out.last_hidden_state.shape)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a public STRING_GNN rebuild from public STRING graph and GNN Simple teacher embeddings.")
    parser.add_argument("--graph-tsv", default="data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt")
    parser.add_argument("--teacher-h5ad", default="data/artifacts/official_k562/GNN_Simple_Official_D256.h5ad")
    parser.add_argument("--output-dir", default="/workspace/artifacts/string_gnn_rebuild_v1")
    parser.add_argument("--export-dir", default="/workspace/models/STRING_GNN_PublicRebuild_v1")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--patience", type=int, default=20)
    parser.add_argument("--hidden-dim", type=int, default=512)
    parser.add_argument("--layers", type=int, default=3)
    parser.add_argument("--dropout", type=float, default=0.10)
    parser.add_argument("--lr", type=float, default=0.002)
    parser.add_argument("--weight-decay", type=float, default=1e-4)
    parser.add_argument("--smoothness-weight", type=float, default=0.01)
    parser.add_argument("--smooth-edges", type=int, default=100000)
    parser.add_argument("--seeds", type=int, nargs="+", default=[3, 7, 11])
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--symlink", default="/home/Models/STRING_GNN_PUBLIC_REBUILD")
    args = parser.parse_args()
    cfg = TrainConfig(graph_tsv=args.graph_tsv, teacher_h5ad=args.teacher_h5ad, output_dir=args.output_dir, export_dir=args.export_dir, hidden_dim=args.hidden_dim, layers=args.layers, dropout=args.dropout, lr=args.lr, weight_decay=args.weight_decay, epochs=args.epochs, patience=args.patience, seeds=tuple(args.seeds), smoothness_weight=args.smoothness_weight, smooth_edges=args.smooth_edges, device=args.device)
    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    node_names, teacher = read_h5ad_embedding(Path(cfg.teacher_h5ad))
    edge_index, raw_edge_weight, graph_stats = read_edges(Path(cfg.graph_tsv), {name: i for i, name in enumerate(node_names)})
    edge_weight = normalized_edge_weight(edge_index, raw_edge_weight, len(node_names))
    split = deterministic_split(node_names, cfg.train_fraction, cfg.val_fraction)
    data_manifest = {
        "node_count": len(node_names),
        "teacher_shape": list(teacher.shape),
        "teacher_sha256": sha256_file(Path(cfg.teacher_h5ad)),
        "graph_sha256": sha256_file(Path(cfg.graph_tsv)),
        "node_order_sha256": sha256_text(node_names),
        "graph_stats": graph_stats,
        "split_counts": {k: len(v) for k, v in split.items()},
        "torch_version": torch.__version__,
        "cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "config": asdict(cfg),
    }
    (out_dir / "data_manifest.json").write_text(json.dumps(data_manifest, indent=2) + "\n")
    results = [train_one_seed(cfg, node_names, teacher, edge_index, edge_weight, split, seed) for seed in cfg.seeds]
    export = export_best(cfg, node_names, edge_index, edge_weight, graph_stats, results)
    smoke = auto_model_smoke(Path(cfg.export_dir))
    if args.symlink:
        symlink = Path(args.symlink)
        symlink.parent.mkdir(parents=True, exist_ok=True)
        if symlink.exists() or symlink.is_symlink():
            symlink.unlink()
        symlink.symlink_to(Path(cfg.export_dir))
    aggregate = {
        "status": "completed",
        "seconds": round(time.time() - t0, 3),
        "data_manifest": data_manifest,
        "seed_results": results,
        "export": export,
        "auto_model_smoke": smoke,
        "symlink": args.symlink,
        "caveat": "This is a public rebuild trained from public graph and teacher embeddings, not the unpublished GenBio/VCHarness original STRING_GNN checkpoint.",
    }
    (out_dir / "rebuild_manifest.json").write_text(json.dumps(aggregate, indent=2) + "\n")
    repo_exp = Path("experiments/string_gnn_public_rebuild_v1")
    repo_exp.mkdir(parents=True, exist_ok=True)
    small = {k: v for k, v in aggregate.items() if k != "seed_results"}
    small["seed_summaries"] = [{"seed": r["seed"], "best_epoch": r["best_epoch"], "best_metrics": r["best_metrics"], "seconds": r["seconds"]} for r in results]
    (repo_exp / "rebuild_manifest.json").write_text(json.dumps(small, indent=2) + "\n")
    lines = ["# STRING_GNN Public Rebuild v1 Report", "", aggregate["caveat"], "", "## Export", "", f"- Export dir: `{cfg.export_dir}`", f"- AutoModel smoke: `{smoke}`", f"- Best seed: `{export['best_seed']}`", f"- Best val cosine: `{export['best_val_cosine']:.6f}`", "", "## Seed Results", ""]
    for r in results:
        m = r["best_metrics"]
        lines.append(f"- seed {r['seed']}: epoch {r['best_epoch']}, val cosine {m['val']['cosine']:.6f}, val MSE {m['val']['mse']:.6f}, test cosine {m['test']['cosine']:.6f}, top10 overlap {m['neighbor_preservation']['top10_overlap']:.4f}")
    lines.extend(["", "## Provenance", "", f"- Teacher: `{cfg.teacher_h5ad}`", f"- Graph: `{cfg.graph_tsv}`", f"- Node order sha256: `{data_manifest['node_order_sha256']}`", f"- Graph sha256: `{data_manifest['graph_sha256']}`", f"- Teacher sha256: `{data_manifest['teacher_sha256']}`"])
    (repo_exp / "final_rebuild_report.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({"status": "completed", "export": export, "smoke": smoke}, indent=2))


if __name__ == "__main__":
    main()
