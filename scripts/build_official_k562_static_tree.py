from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

BEST_PATH_DEFAULT = "node2-1-1-1-1-1"
NODE_RE = re.compile(r"^(node[0-9](?:-[0-9]+)*)_code\.py$")


def parent_for(node_id: str) -> str:
    if "-" not in node_id:
        return ""
    return node_id.rsplit("-", 1)[0]


def classify_node(path: Path) -> tuple[str, str]:
    text = path.read_text(errors="replace")[:20000]
    lowered = text.lower()
    uses_aido = "aido" in lowered or "cell-100m" in lowered or "cellfoundation" in lowered
    uses_string = "string_gnn" in lowered or "string" in lowered or "graph" in lowered
    uses_lora = "lora" in lowered or "peft" in lowered or "adapter" in lowered
    uses_attention = "attention" in lowered or "multihead" in lowered or "attn" in lowered
    if uses_aido and uses_string:
        family = "aido_string_fusion"
        blueprint = "official_aido_string_fusion"
    elif uses_aido and uses_lora:
        family = "aido_lora_adapter"
        blueprint = "official_aido_lora_adapter"
    elif uses_string or uses_attention:
        family = "string_gnn_attention"
        blueprint = "official_string_gnn_attention"
    else:
        family = "official_training_or_head_variant"
        blueprint = "official_target_gene_head"
    return family, blueprint


def gap_type(blueprint: str, node_id: str, best_path: str) -> str:
    if node_id == best_path:
        return "wrapped_only"
    if blueprint in {"official_aido_lora_adapter", "official_string_gnn_attention", "official_aido_string_fusion", "official_target_gene_head"}:
        return "native_equivalent"
    return "not_mapped"


def build_tree(static_dir: Path, best_path: str) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    for code_path in sorted(static_dir.glob("node*_code.py")):
        match = NODE_RE.match(code_path.name)
        if not match:
            continue
        node_id = match.group(1)
        curve = static_dir / f"{node_id}_curve.png"
        family, blueprint = classify_node(code_path)
        nodes[node_id] = {
            "id": node_id,
            "parent": parent_for(node_id),
            "children": [],
            "code_path": str(code_path),
            "curve_path": str(curve) if curve.exists() else "",
            "runnable": code_path.exists(),
            "model_family": family,
            "local_equivalent_blueprint": blueprint,
            "gap_type": gap_type(blueprint, node_id, best_path),
            "required_artifacts": ["official_essential_deg_with_split_h5ad", "official_aido_cell_100m_model_dir", "official_string_gnn_model_dir"],
        }
    for node_id, node in nodes.items():
        parent = node["parent"]
        if parent in nodes:
            nodes[parent].setdefault("children", []).append(node_id)
    roots = sorted([node_id for node_id, node in nodes.items() if not node["parent"] or node["parent"] not in nodes])
    best_lineage: list[str] = []
    current = best_path
    while current:
        if current in nodes:
            best_lineage.append(current)
        current = parent_for(current)
    best_lineage.reverse()
    deepest = sorted(nodes, key=lambda n: (n.count("-"), n))[-1] if nodes else ""
    family_mapping: dict[str, Any] = {}
    for node_id, node in nodes.items():
        family = node["model_family"]
        row = family_mapping.setdefault(family, {"node_count": 0, "nodes": [], "local_equivalent_blueprints": sorted(set())})
        row["node_count"] += 1
        row["nodes"].append(node_id)
    for row in family_mapping.values():
        blueprints = sorted({nodes[node_id]["local_equivalent_blueprint"] for node_id in row["nodes"]})
        row["local_equivalent_blueprints"] = blueprints
        row["nodes"] = sorted(row["nodes"], key=lambda n: (n.count("-"), n))
    return {"format": "official_k562_static_tree.v1", "static_dir": str(static_dir), "node_count": len(nodes), "root_nodes": roots, "best_path": best_path, "best_lineage": best_lineage, "deepest_node_hint": deepest, "family_mapping": family_mapping, "nodes": nodes}


def write_catalog(tree: dict[str, Any], path: Path) -> None:
    lines = ["# Official K562 Public Static Tree Catalog", "", f"- Static dir: `{tree['static_dir']}`", f"- Node count: {tree['node_count']}", f"- Best path default: `{tree['best_path']}`", f"- Deepest node hint: `{tree['deepest_node_hint']}`", "", "## Best Path", ""]
    for node_id in tree.get("best_lineage", []):
        node = tree["nodes"][node_id]
        lines.append(f"- `{node_id}` family={node['model_family']} blueprint={node['local_equivalent_blueprint']} gap={node['gap_type']}")
    lines.extend(["", "## Nodes", "", "| Node | Parent | Children | Family | Local blueprint | Gap | Runnable |", "|---|---|---:|---|---|---|---:|"])
    for node_id in sorted(tree["nodes"], key=lambda n: (n.split('-')[0], n.count('-'), n)):
        node = tree["nodes"][node_id]
        lines.append(f"| `{node_id}` | `{node['parent']}` | {len(node['children'])} | {node['model_family']} | {node['local_equivalent_blueprint']} | {node['gap_type']} | {str(node['runnable']).lower()} |")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a benchmark scaffold from public VCHarness K562 static node files.")
    parser.add_argument("--static-dir", type=Path, default=Path("/workspace/_external/VCHarness/K562_cls/static"))
    parser.add_argument("--output-json", type=Path, default=Path("experiments/official_k562_alignment/official_k562_static_tree.json"))
    parser.add_argument("--output-md", type=Path, default=Path("experiments/official_k562_alignment/official_k562_node_catalog.md"))
    parser.add_argument("--best-path-json", type=Path, default=Path("experiments/official_k562_alignment/official_k562_best_path.json"))
    parser.add_argument("--family-mapping-json", type=Path, default=Path("experiments/official_k562_alignment/official_k562_family_mapping.json"))
    parser.add_argument("--best-path", default=BEST_PATH_DEFAULT)
    args = parser.parse_args()
    tree = build_tree(args.static_dir, args.best_path)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(tree, indent=2) + "\n", encoding="utf-8")
    write_catalog(tree, args.output_md)
    best = {"best_path": args.best_path, "best_lineage": tree.get("best_lineage", []), "nodes": [tree["nodes"][n] for n in tree.get("best_lineage", [])]}
    args.best_path_json.parent.mkdir(parents=True, exist_ok=True)
    args.best_path_json.write_text(json.dumps(best, indent=2) + "\n", encoding="utf-8")
    args.family_mapping_json.parent.mkdir(parents=True, exist_ok=True)
    args.family_mapping_json.write_text(json.dumps(tree.get("family_mapping", {}), indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"tree": str(args.output_json), "catalog": str(args.output_md), "best_path": str(args.best_path_json), "family_mapping": str(args.family_mapping_json), "node_count": tree["node_count"]}, indent=2))


if __name__ == "__main__":
    main()
