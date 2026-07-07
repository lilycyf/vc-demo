from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
from typing import Any

import h5py
import numpy as np
import torch
from safetensors.torch import load_file, save_file


REPO_ROOT = Path(__file__).resolve().parents[1]
MODELGENERATOR_AIDO = Path("/workspace/_external/ModelGenerator/huggingface/aido.cell/aido_cell")
AIDO_DIR = Path("/home/Models/AIDO.Cell-100M")
STRING_DIR = Path("/home/Models/STRING_GNN")
AIDO_EMBEDDING_H5AD = REPO_ROOT / "data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad"
GNN_EMBEDDING_H5AD = REPO_ROOT / "data/artifacts/official_k562/GNN_Simple_Official_D256.h5ad"
STRING_EDGE_TSV = REPO_ROOT / "data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt"


TOKENIZER_SOURCE = r'''
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import torch
from transformers.tokenization_utils_base import BatchEncoding
from transformers.tokenization_utils import PreTrainedTokenizer


class CellFoundationTokenizer(PreTrainedTokenizer):
    """Compatibility tokenizer for public VCHarness AIDO.Cell nodes.

    AIDO.Cell official examples consume fixed-length expression tensors rather
    than natural-language tokens. Public VCHarness nodes nevertheless call
    AutoTokenizer and pass dictionaries like:

        {"gene_ids": ["ENSG..."], "expression": [1.0]}

    This tokenizer maps Ensembl IDs or symbols into the AIDO 19,264-gene order,
    fills absent genes with the configured pad value, and appends the two depth
    tokens expected by CellFoundationModel.
    """

    model_input_names = ["input_ids", "attention_mask"]

    def __init__(
        self,
        gene_map_file: str = "gene_id_to_aido_index.json",
        model_gene_count: int = 19264,
        pad_value: float = -2.0,
        missing_value: float = 0.0,
        depth_value: float = 5.0,
        **kwargs: Any,
    ) -> None:
        kwargs.pop("model_max_length", None)
        self.model_gene_count = int(model_gene_count)
        self.pad_value = float(pad_value)
        self.missing_value = float(missing_value)
        self.depth_value = float(depth_value)
        self.gene_map_file = gene_map_file
        base = Path(kwargs.get("name_or_path", "") or ".")
        candidates = [base / gene_map_file, Path(gene_map_file)]
        mapping_path = next((p for p in candidates if p.exists()), None)
        if mapping_path is None:
            self.gene_to_index: dict[str, int] = {}
        else:
            self.gene_to_index = {str(k): int(v) for k, v in json.loads(mapping_path.read_text()).items()}
        super().__init__(model_max_length=model_gene_count + 2, **kwargs)

    @property
    def vocab_size(self) -> int:
        return self.model_gene_count + 2

    def get_vocab(self) -> dict[str, int]:
        return dict(self.gene_to_index)


    def _tokenize(self, text: str, **kwargs: Any) -> list[str]:
        return [text]

    def _convert_token_to_id(self, token: str) -> int:
        return int(self.gene_to_index.get(str(token), 0))

    def _convert_id_to_token(self, index: int) -> str:
        return str(index)

    def save_vocabulary(self, save_directory: str, filename_prefix: str | None = None):
        out = Path(save_directory) / ((filename_prefix or "") + self.gene_map_file)
        out.write_text(json.dumps(self.gene_to_index, indent=2) + "\n")
        return (str(out),)

    def __call__(self, inputs, return_tensors: str | None = None, **kwargs: Any) -> BatchEncoding:
        if isinstance(inputs, dict):
            rows = [inputs]
        else:
            rows = list(inputs)
        batch = []
        masks = []
        for row in rows:
            x = torch.full((self.model_gene_count + 2,), self.pad_value, dtype=torch.float32)
            mask = torch.zeros((self.model_gene_count + 2,), dtype=torch.float32)
            gene_ids = row.get("gene_ids", []) or []
            expr = row.get("expression", []) or []
            for gene_id, value in zip(gene_ids, expr):
                idx = self.gene_to_index.get(str(gene_id))
                if idx is None or idx < 0 or idx >= self.model_gene_count:
                    continue
                x[idx] = float(value)
                mask[idx] = 1.0
            x[self.model_gene_count :] = self.depth_value
            mask[self.model_gene_count :] = 1.0
            batch.append(x)
            masks.append(mask)
        encoded = BatchEncoding({"input_ids": torch.stack(batch), "attention_mask": torch.stack(masks)})
        if return_tensors in {None, "pt"}:
            return encoded
        raise ValueError(f"unsupported return_tensors={return_tensors!r}; only 'pt' is supported")
'''


STRING_CONFIG_SOURCE = r'''
from __future__ import annotations

from transformers.configuration_utils import PretrainedConfig


class StringGNNCompatConfig(PretrainedConfig):
    model_type = "string_gnn_compat"

    def __init__(
        self,
        hidden_size: int = 256,
        node_embeddings_file: str = "node_embeddings.pt",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.hidden_size = hidden_size
        self.node_embeddings_file = node_embeddings_file
'''


STRING_MODEL_SOURCE = r'''
from __future__ import annotations

from pathlib import Path

import torch
from torch import nn
from transformers.modeling_outputs import BaseModelOutput
from transformers.modeling_utils import PreTrainedModel

from .configuration_string_gnn_compat import StringGNNCompatConfig


class StringGNNCompatModel(PreTrainedModel):
    """Frozen STRING_GNN compatibility model.

    The public genbio-ai/STRING_GNN Hugging Face repo currently exposes no
    model weights. This class returns the official public GNN Simple D=256
    node embeddings from node_embeddings.pt so public VCHarness nodes can use
    their expected AutoModel call path for frozen embedding extraction.
    """

    config_class = StringGNNCompatConfig
    base_model_prefix = "string_gnn"

    def __init__(self, config: StringGNNCompatConfig):
        super().__init__(config)
        path = Path(config.name_or_path or ".") / config.node_embeddings_file
        if not path.exists():
            path = Path(config.node_embeddings_file)
        embeddings = torch.load(path, map_location="cpu")
        self.register_buffer("node_embeddings", embeddings.float(), persistent=False)
        self.anchor = nn.Parameter(torch.zeros(1), requires_grad=False)

    def forward(self, edge_index=None, edge_weight=None, output_hidden_states: bool = False, **kwargs):
        hidden = self.node_embeddings.to(device=self.anchor.device)
        return BaseModelOutput(last_hidden_state=hidden)
'''


def _decode(values: np.ndarray) -> list[str]:
    return [v.decode("utf-8") if isinstance(v, (bytes, bytearray)) else str(v) for v in values]


def _obs_values(f: h5py.File, key: str) -> list[str]:
    obj = f["obs"][key]
    if isinstance(obj, h5py.Group):
        cats = _decode(obj["categories"][()])
        codes = obj["codes"][()]
        return [cats[int(code)] if int(code) >= 0 else "" for code in codes]
    return _decode(obj[()])


def _read_h5ad_x_dense(path: Path) -> np.ndarray:
    with h5py.File(path, "r") as f:
        x = f["X"]
        if hasattr(x, "shape"):
            return np.asarray(x[()], dtype="float32")
        encoding = x.attrs.get("encoding-type", "")
        if isinstance(encoding, bytes):
            encoding = encoding.decode("utf-8")
        shape = tuple(int(v) for v in x.attrs["shape"])
        data = np.asarray(x["data"][()], dtype="float32")
        indices = x["indices"][()]
        indptr = x["indptr"][()]
        dense = np.zeros(shape, dtype="float32")
        if encoding == "csr_matrix":
            for row in range(shape[0]):
                start, end = int(indptr[row]), int(indptr[row + 1])
                dense[row, indices[start:end]] = data[start:end]
        elif encoding == "csc_matrix":
            for col in range(shape[1]):
                start, end = int(indptr[col]), int(indptr[col + 1])
                dense[indices[start:end], col] = data[start:end]
        else:
            raise ValueError(f"unsupported X encoding for {path}: {encoding!r}")
        return dense


def prepare_aido_dir(aido_dir: Path, source_dir: Path, aido_embedding_h5ad: Path) -> dict[str, Any]:
    aido_dir.mkdir(parents=True, exist_ok=True)
    copied = []
    for rel in ["models/configuration_cellfoundation.py", "models/modeling_cellfoundation.py"]:
        src = source_dir / rel
        dst = aido_dir / Path(rel).name
        shutil.copy2(src, dst)
        if dst.name == "modeling_cellfoundation.py":
            text = dst.read_text()
            text = text.replace(
                "            encoder_input += position_emb.transpose(0, 1)",
                "            encoder_input = encoder_input + position_emb.transpose(0, 1)",
            )
            text = text.replace("    base_model_prefix = \"bert\"", "    base_model_prefix = \"\"")
            anchor = "\n\n@add_start_docstrings(\n    \"\"\"\n    CellFoundation Model with two heads"
            alias = (
                "\n\n    @property\n"
                "    def bert(self):\n"
                "        # Compatibility alias for public VCHarness nodes that expect\n"
                "        # AutoModel(AIDO).bert.gene_embedding. ModelGenerator exposes\n"
                "        # gene_embedding directly on CellFoundationModel.\n"
                "        return self\n"
            )
            if alias.strip() not in text:
                text = text.replace(anchor, alias + anchor, 1)
            dst.write_text(text)
        copied.append(str(dst))
    gene_list_src = source_dir / "models/gene_lists/OS_scRNA_gene_index.19264.tsv"
    gene_list_dst = aido_dir / "OS_scRNA_gene_index.19264.tsv"
    shutil.copy2(gene_list_src, gene_list_dst)
    copied.append(str(gene_list_dst))
    tokenizer_path = aido_dir / "tokenization_cellfoundation.py"
    tokenizer_path.write_text(TOKENIZER_SOURCE.strip() + "\n")
    copied.append(str(tokenizer_path))

    with h5py.File(aido_embedding_h5ad, "r") as f:
        ensembl = _obs_values(f, "ensembl_gene_id")
        symbol = _obs_values(f, "symbol")
    gene_to_idx: dict[str, int] = {}
    for idx, (ensg, sym) in enumerate(zip(ensembl, symbol)):
        if ensg:
            gene_to_idx[ensg] = idx
        if sym:
            gene_to_idx[sym] = idx
    gene_map_path = aido_dir / "gene_id_to_aido_index.json"
    gene_map_path.write_text(json.dumps(gene_to_idx, indent=2) + "\n")
    copied.append(str(gene_map_path))

    config_path = aido_dir / "config.json"
    config = json.loads(config_path.read_text())
    auto_map = config.get("auto_map", {})
    auto_map.update(
        {
            "AutoConfig": "configuration_cellfoundation.CellFoundationConfig",
            "AutoModel": "modeling_cellfoundation.CellFoundationModel",
            "AutoModelForMaskedLM": "modeling_cellfoundation.CellFoundationForMaskedLM",
            "AutoTokenizer": ["tokenization_cellfoundation.CellFoundationTokenizer", None],
        }
    )
    config["auto_map"] = auto_map
    config_path.write_text(json.dumps(config, indent=2) + "\n")

    # AutoModel loads CellFoundationModel directly, whose keys do not include
    # the original checkpoint's bert prefix. Preserve the original file and
    # write an AutoModel-compatible safetensors file with stripped keys.
    weights_path = aido_dir / "model.safetensors"
    original_weights_path = aido_dir / "model.original_with_bert_prefix.safetensors"
    if weights_path.exists():
        if not original_weights_path.exists():
            weights_path.rename(original_weights_path)
        raw = load_file(str(original_weights_path))
        converted = {}
        for key, value in raw.items():
            if key.startswith("bert."):
                converted[key[len("bert."):]] = value
            elif key.startswith("cls."):
                continue
            else:
                converted[key] = value
        save_file(converted, str(weights_path), metadata={"format": "pt"})
        copied.append(str(weights_path))

    tokenizer_config = {
        "tokenizer_class": "CellFoundationTokenizer",
        "auto_map": {"AutoTokenizer": ["tokenization_cellfoundation.CellFoundationTokenizer", None]},
        "model_max_length": 19266,
        "model_gene_count": 19264,
        "gene_map_file": "gene_id_to_aido_index.json",
        "pad_value": -2.0,
        "missing_value": 0.0,
        "depth_value": 5.0,
    }
    (aido_dir / "tokenizer_config.json").write_text(json.dumps(tokenizer_config, indent=2) + "\n")
    copied.append(str(aido_dir / "tokenizer_config.json"))

    return {"aido_dir": str(aido_dir), "copied_or_written": copied, "gene_map_entries": len(gene_to_idx)}


def prepare_string_dir(string_dir: Path, gnn_h5ad: Path, edge_tsv: Path) -> dict[str, Any]:
    string_dir.mkdir(parents=True, exist_ok=True)
    embeddings = _read_h5ad_x_dense(gnn_h5ad)
    with h5py.File(gnn_h5ad, "r") as f:
        node_names = _obs_values(f, "ensembl_gene_id")
    if embeddings.shape[0] != len(node_names):
        raise ValueError("GNN embedding rows do not match node names")
    if embeddings.shape[1] != 256:
        raise ValueError(f"expected 256-dim GNN embeddings, got {embeddings.shape}")
    torch.save(torch.from_numpy(embeddings), string_dir / "node_embeddings.pt")
    (string_dir / "node_names.json").write_text(json.dumps(node_names, indent=2) + "\n")

    id_to_idx = {name: idx for idx, name in enumerate(node_names)}
    src_idx: list[int] = []
    dst_idx: list[int] = []
    weights: list[float] = []
    raw_edges = 0
    kept_edges = 0
    with edge_tsv.open(newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            raw_edges += 1
            s = row.get("protein1") or row.get("source_gene") or ""
            t = row.get("protein2") or row.get("target_gene") or ""
            if s not in id_to_idx or t not in id_to_idx:
                continue
            score_raw = row.get("combined_score") or row.get("score") or "0"
            score = float(score_raw)
            if score > 1.0:
                score = score / 1000.0
            i, j = id_to_idx[s], id_to_idx[t]
            src_idx.extend([i, j])
            dst_idx.extend([j, i])
            weights.extend([score, score])
            kept_edges += 1
    graph = {
        "edge_index": torch.tensor([src_idx, dst_idx], dtype=torch.long),
        "edge_weight": torch.tensor(weights, dtype=torch.float32),
    }
    torch.save(graph, string_dir / "graph_data.pt")

    config = {
        "model_type": "string_gnn_compat",
        "architectures": ["StringGNNCompatModel"],
        "hidden_size": 256,
        "node_embeddings_file": "node_embeddings.pt",
        "auto_map": {
            "AutoConfig": "configuration_string_gnn_compat.StringGNNCompatConfig",
            "AutoModel": "modeling_string_gnn_compat.StringGNNCompatModel",
        },
    }
    (string_dir / "config.json").write_text(json.dumps(config, indent=2) + "\n")
    (string_dir / "configuration_string_gnn_compat.py").write_text(STRING_CONFIG_SOURCE.strip() + "\n")
    (string_dir / "modeling_string_gnn_compat.py").write_text(STRING_MODEL_SOURCE.strip() + "\n")
    torch.save({"anchor": torch.zeros(1)}, string_dir / "pytorch_model.bin")
    (string_dir / "README.md").write_text(
        "# STRING_GNN compatibility directory\n\n"
        "This directory is reconstructed from public GenBio artifacts: "
        "GNN_Simple_Official_D256.h5ad and 9606.protein.links.ensembl_900_keep20_adaptive.txt. "
        "It is not a downloaded genbio-ai/STRING_GNN weight snapshot, because that public HF repo "
        "currently exposes no model weights.\n"
    )

    return {
        "string_dir": str(string_dir),
        "node_count": len(node_names),
        "embedding_shape": list(embeddings.shape),
        "raw_edges": raw_edges,
        "kept_undirected_pairs": kept_edges,
        "edge_index_shape": list(graph["edge_index"].shape),
        "source_embedding_h5ad": str(gnn_h5ad),
        "source_edge_tsv": str(edge_tsv),
    }


def smoke_test(aido_dir: Path, string_dir: Path) -> dict[str, Any]:
    result: dict[str, Any] = {}
    from transformers import AutoConfig, AutoModel, AutoTokenizer

    try:
        cfg = AutoConfig.from_pretrained(str(aido_dir), trust_remote_code=True)
        result["aido_auto_config"] = {"ok": True, "class": cfg.__class__.__name__}
    except Exception as exc:
        result["aido_auto_config"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    try:
        tok = AutoTokenizer.from_pretrained(str(aido_dir), trust_remote_code=True)
        encoded = tok([{"gene_ids": ["ENSG00000141510"], "expression": [1.0]}], return_tensors="pt")
        result["aido_auto_tokenizer"] = {
            "ok": True,
            "class": tok.__class__.__name__,
            "input_shape": list(encoded["input_ids"].shape),
            "attention_shape": list(encoded["attention_mask"].shape),
        }
    except Exception as exc:
        result["aido_auto_tokenizer"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    try:
        model = AutoModel.from_pretrained(str(aido_dir), trust_remote_code=True)
        result["aido_auto_model"] = {"ok": True, "class": model.__class__.__name__}
        del model
    except Exception as exc:
        result["aido_auto_model"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    try:
        model = AutoModel.from_pretrained(str(string_dir), trust_remote_code=True)
        graph = torch.load(string_dir / "graph_data.pt", map_location="cpu")
        out = model(edge_index=graph["edge_index"], edge_weight=graph["edge_weight"])
        result["string_auto_model"] = {
            "ok": True,
            "class": model.__class__.__name__,
            "last_hidden_state_shape": list(out.last_hidden_state.shape),
        }
    except Exception as exc:
        result["string_auto_model"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    result["status"] = "ok" if all(v.get("ok", True) for v in result.values() if isinstance(v, dict)) else "blocked"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare missing local compatibility files for the official K562 best-node path.")
    parser.add_argument("--aido-dir", type=Path, default=AIDO_DIR)
    parser.add_argument("--string-dir", type=Path, default=STRING_DIR)
    parser.add_argument("--modelgenerator-aido", type=Path, default=MODELGENERATOR_AIDO)
    parser.add_argument("--aido-embedding-h5ad", type=Path, default=AIDO_EMBEDDING_H5AD)
    parser.add_argument("--gnn-embedding-h5ad", type=Path, default=GNN_EMBEDDING_H5AD)
    parser.add_argument("--string-edge-tsv", type=Path, default=STRING_EDGE_TSV)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = {
        "aido": prepare_aido_dir(args.aido_dir, args.modelgenerator_aido, args.aido_embedding_h5ad),
        "string_gnn": prepare_string_dir(args.string_dir, args.gnn_embedding_h5ad, args.string_edge_tsv),
    }
    report["smoke_test"] = smoke_test(args.aido_dir, args.string_dir)
    report["status"] = "ok" if report["smoke_test"].get("status") == "ok" else "blocked"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
