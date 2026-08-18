from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path
from typing import Any

import numpy as np
import requests
from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def clean_candidates(drug: str) -> list[str]:
    name = re.sub(r"^HY-[A-Za-z0-9]+-", "", drug).strip()
    base = re.sub(r"\s*\([^)]*\)", "", name).strip()
    candidates = [name, base]
    if "hydrochloride" in name.lower():
        candidates.append(re.sub("hydrochloride", "", base, flags=re.I).strip())
    return list(dict.fromkeys([c for c in candidates if c]))


def pubchem_lookup(name: str) -> dict[str, Any] | None:
    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{}/property/CanonicalSMILES,IsomericSMILES,InChIKey,MolecularFormula,MolecularWeight/JSON".format(requests.utils.quote(name))
    r = requests.get(url, timeout=30)
    if r.status_code != 200:
        return None
    props = r.json().get("PropertyTable", {}).get("Properties", [])
    if not props:
        return None
    out = props[0]
    out["query_name"] = name
    out["source_url"] = url
    return out


def fingerprint(smiles: str, n_bits: int) -> np.ndarray:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"RDKit cannot parse SMILES: {smiles}")
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=n_bits)
    arr = np.zeros((n_bits,), dtype=np.float32)
    AllChem.DataStructs.ConvertToNumpyArray(fp, arr)
    desc = np.array([
        Descriptors.MolWt(mol),
        Descriptors.MolLogP(mol),
        Descriptors.TPSA(mol),
        float(Descriptors.NumHDonors(mol)),
        float(Descriptors.NumHAcceptors(mol)),
        float(Descriptors.NumRotatableBonds(mol)),
    ], dtype=np.float32)
    desc = np.nan_to_num(desc)
    desc = desc / np.array([1000.0, 10.0, 300.0, 20.0, 30.0, 30.0], dtype=np.float32)
    return np.concatenate([arr, desc]).astype(np.float32)


def build(data_dir: Path, output: Path, summary: Path, n_bits: int) -> dict[str, Any]:
    manifest = read_json(data_dir / "manifest.json")
    drugs = [str(x) for x in manifest["perturbation_drugs"]]
    rows = []
    embeddings = []
    failures = []
    for drug in drugs:
        hit = None
        tried = []
        for name in clean_candidates(drug):
            tried.append(name)
            hit = pubchem_lookup(name)
            if hit:
                break
            time.sleep(0.2)
        if not hit:
            failures.append({"drug": drug, "queries": tried, "reason": "not found in PubChem PUG REST"})
            continue
        smiles = hit.get("CanonicalSMILES") or hit.get("IsomericSMILES") or hit.get("SMILES") or hit.get("ConnectivitySMILES")
        try:
            emb = fingerprint(str(smiles), n_bits)
        except Exception as exc:
            failures.append({"drug": drug, "queries": tried, "reason": repr(exc), "pubchem": hit})
            continue
        rows.append({"drug": drug, "queries": tried, "pubchem": hit, "smiles": smiles})
        embeddings.append(emb)
    if failures:
        raise SystemExit(json.dumps({"status": "blocked", "failures": failures}, indent=2))
    arr = np.vstack(embeddings).astype(np.float32)
    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output, drug_embeddings=arr, perturbation_drugs=np.array(drugs), source="PubChem PUG REST + RDKit Morgan fingerprint radius=2")
    report = {
        "format": "helf_drug_fingerprints.v1",
        "artifact_id": "chemical_encoder_checkpoint_or_drug_fingerprints",
        "output": str(output),
        "source": "PubChem PUG REST; RDKit Morgan fingerprint radius=2 plus normalized molecular descriptors",
        "n_drugs": len(drugs),
        "coverage": len(rows) / len(drugs),
        "embedding_shape": list(arr.shape),
        "rows": rows,
    }
    summary.parent.mkdir(parents=True, exist_ok=True)
    summary.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Build HELF drug fingerprint artifact from PubChem + RDKit.")
    parser.add_argument("--data-dir", type=Path, default=Path("data/cell_lines/aivc_helf_perturb_deg_cls"))
    parser.add_argument("--output", type=Path, default=Path("data/artifacts/helf/drug_embeddings.npz"))
    parser.add_argument("--summary", type=Path, default=Path("experiments/aivc_search_space_manifest_audit/helf_drug_fingerprint_artifact_summary.json"))
    parser.add_argument("--n-bits", type=int, default=2048)
    args = parser.parse_args()
    print(json.dumps(build(args.data_dir, args.output, args.summary, args.n_bits), indent=2))


if __name__ == "__main__":
    main()
