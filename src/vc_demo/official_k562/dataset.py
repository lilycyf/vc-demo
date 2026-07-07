from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import h5py
import numpy as np
import torch
from torch.utils.data import Dataset

Split = Literal["train", "val", "test"]


@dataclass(frozen=True)
class OfficialK562TSVSpec:
    data_dir: str
    embedding_h5ad: str | None = None
    embedding_h5ads: tuple[str, ...] = ()
    n_classes: int = 3


def _decode(values: np.ndarray) -> list[str]:
    return [v.decode("utf-8") if isinstance(v, (bytes, bytearray)) else str(v) for v in values]


def _read_h5ad_x(f) -> np.ndarray:
    x = f["X"]
    if hasattr(x, "shape"):
        return np.asarray(x[()], dtype="float32")
    encoding = x.attrs.get("encoding-type", "")
    if isinstance(encoding, bytes):
        encoding = encoding.decode("utf-8")
    if encoding in {"csr_matrix", "csc_matrix"}:
        shape = tuple(int(v) for v in x.attrs["shape"])
        data = np.asarray(x["data"][()], dtype="float32")
        indices = x["indices"][()]
        indptr = x["indptr"][()]
        dense = np.zeros(shape, dtype="float32")
        if encoding == "csr_matrix":
            for row in range(shape[0]):
                start, end = int(indptr[row]), int(indptr[row + 1])
                dense[row, indices[start:end]] = data[start:end]
        else:
            for col in range(shape[1]):
                start, end = int(indptr[col]), int(indptr[col + 1])
                dense[indices[start:end], col] = data[start:end]
        return dense
    raise ValueError(f"unsupported h5ad X encoding: {encoding!r}")


def _obs_values(f, candidates: list[str]) -> list[str] | None:
    if "obs" not in f:
        return None
    obs = f["obs"]
    for key in candidates:
        if key not in obs:
            continue
        obj = obs[key]
        if isinstance(obj, h5py.Group):
            cats = _decode(obj["categories"][()])
            codes = obj["codes"][()]
            return [cats[int(code)] if int(code) >= 0 else "" for code in codes]
        return _decode(obj[()])
    index_key = obs.attrs.get("_index")
    if isinstance(index_key, bytes):
        index_key = index_key.decode("utf-8")
    if index_key and index_key in obs:
        return _decode(obs[index_key][()])
    return None


def _load_embedding_table(path: str | None) -> tuple[dict[str, int], torch.Tensor] | None:
    if not path:
        return None
    h5ad = Path(path)
    if not h5ad.exists():
        raise FileNotFoundError(h5ad)
    with h5py.File(h5ad, "r") as f:
        if "X" not in f:
            raise ValueError(f"{h5ad} has no X matrix")
        x = _read_h5ad_x(f)
        ids = _obs_values(f, ["gene_id", "ensembl_gene_id", "_index"])
        if ids is None:
            raise ValueError(f"{h5ad} does not expose obs/gene_id, obs/ensembl_gene_id, or obs index for alignment")
    id_to_idx = {gene_id: i for i, gene_id in enumerate(ids) if gene_id}
    return id_to_idx, torch.from_numpy(x)


class OfficialK562TSVDataset(Dataset):
    """Official Essential K562 DEG TSV dataset.

    The TSV contract mirrors the public VCHarness node code: columns are
    pert_id, symbol, and label. Labels are JSON arrays with raw DEG classes
    -1/0/1 and are remapped to 0/1/2 for torch cross entropy.
    """

    def __init__(self, split: Split, spec: OfficialK562TSVSpec) -> None:
        self.data_dir = Path(spec.data_dir)
        self.tsv_path = self.data_dir / f"{split}.tsv"
        if not self.tsv_path.exists():
            raise FileNotFoundError(self.tsv_path)
        self.pert_ids: list[str] = []
        self.symbols: list[str] = []
        labels: list[list[int]] = []
        with self.tsv_path.open(newline="") as f:
            reader = csv.DictReader(f, delimiter="\t")
            for row in reader:
                self.pert_ids.append(row["pert_id"])
                self.symbols.append(row["symbol"])
                labels.append([int(x) + 1 for x in json.loads(row["label"])])
        self.labels = torch.tensor(labels, dtype=torch.long)
        embedding_paths = tuple(spec.embedding_h5ads) or ((spec.embedding_h5ad,) if spec.embedding_h5ad else ())
        if not embedding_paths:
            self.features = torch.eye(len(self.pert_ids), dtype=torch.float32)
            self.embedding_coverage = 0.0
            self.embedding_coverages = {}
        else:
            feature_blocks: list[torch.Tensor] = []
            coverages: dict[str, float] = {}
            for embedding_path in embedding_paths:
                table = _load_embedding_table(embedding_path)
                if table is None:
                    continue
                id_to_idx, embeddings = table
                rows = []
                matched = 0
                for pert_id in self.pert_ids:
                    idx = id_to_idx.get(pert_id)
                    if idx is None:
                        rows.append(torch.zeros(embeddings.shape[1], dtype=torch.float32))
                    else:
                        matched += 1
                        rows.append(embeddings[idx])
                feature_blocks.append(torch.stack(rows))
                coverages[str(embedding_path)] = matched / max(len(self.pert_ids), 1)
            if not feature_blocks:
                raise ValueError("no usable official K562 embedding tables were loaded")
            self.features = torch.cat(feature_blocks, dim=1) if len(feature_blocks) > 1 else feature_blocks[0]
            self.embedding_coverages = coverages
            self.embedding_coverage = min(coverages.values()) if coverages else 0.0

    def __len__(self) -> int:
        return len(self.pert_ids)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        return {"x": self.features[idx], "y": self.labels[idx]}
