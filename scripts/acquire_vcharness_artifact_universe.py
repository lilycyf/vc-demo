# Source-backed acquisition sweep for the VCHarness-style artifact universe.
#
# This script downloads or audits only public/source-backed artifacts. It writes
# manifests and reports to experiments/string_net_artifact_project and stores
# large files under /workspace/models, /workspace/vc-demo/data, or
# /workspace/_external. Do not commit those large artifact directories.

from __future__ import annotations

import hashlib
import json
import subprocess
import time
import urllib.request
from pathlib import Path

ROOT = Path("/workspace/vc-demo")
RUN = ROOT / "experiments/string_net_artifact_project"
MANIFEST = RUN / "artifact_acquisition_sweep_manifest.json"
REPORT = RUN / "ARTIFACT_ACQUISITION_SWEEP_REPORT.zh.md"
MODELS = Path("/workspace/models")
EXTERNAL = Path("/workspace/_external")

RUN.mkdir(parents=True, exist_ok=True)
MODELS.mkdir(parents=True, exist_ok=True)
EXTERNAL.mkdir(parents=True, exist_ok=True)

items: list[dict] = []


def run(cmd: list[str], *, cwd: Path = ROOT, timeout: int | None = None) -> dict:
    t0 = time.time()
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "seconds": round(time.time() - t0, 3),
        "stdout_tail": proc.stdout[-4000:],
        "stderr_tail": proc.stderr[-4000:],
    }


def sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_info(path: Path) -> dict:
    if not path.exists():
        return {"path": str(path), "exists": False}
    if path.is_file():
        return {
            "path": str(path),
            "exists": True,
            "kind": "file",
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    files = [p for p in path.rglob("*") if p.is_file()]
    return {
        "path": str(path),
        "exists": True,
        "kind": "dir",
        "file_count": len(files),
        "bytes": sum(p.stat().st_size for p in files),
    }


def add_item(**kw) -> None:
    items.append(kw)
    MANIFEST.write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "items": items,
            },
            indent=2,
        )
        + "\n"
    )


def hf_model_api(repo_id: str) -> dict:
    url = "https://huggingface.co/api/models/" + repo_id
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            return {"ok": True, "status": response.status, "json": json.load(response)}
    except Exception as exc:
        return {"ok": False, "error": repr(exc)}


if Path("/home/Models").exists() and not Path("/home/Models").is_symlink():
    pass
elif not Path("/home/Models").exists():
    Path("/home/Models").symlink_to(MODELS)

for repo_id, url, dest in [
    ("public_vcharness_repo", "https://github.com/genbio-ai/VCHarness.git", EXTERNAL / "VCHarness"),
    ("public_modelgenerator_repo", "https://github.com/genbio-ai/ModelGenerator.git", EXTERNAL / "ModelGenerator"),
]:
    if dest.exists():
        rec = run(["git", "pull", "--ff-only"], cwd=dest)
        status = "present_updated_or_checked"
    else:
        rec = run(["git", "clone", url, str(dest)], cwd=EXTERNAL)
        status = "present" if rec["returncode"] == 0 else "blocked_or_failed"
    add_item(
        id=repo_id,
        type="source_code_repo",
        status=status,
        source=url,
        local_path=str(dest),
        command=rec,
        file_info=file_info(dest),
    )

known = [
    (
        "official_essential_deg_with_split_h5ad",
        "essential/essential_deg_with_split.h5ad",
        ROOT / "data/artifacts/official_k562/essential_deg_with_split.h5ad",
        "official task h5ad",
    ),
    (
        "official_k562_aido_cell_100m_embedding_h5ad",
        "gene_embeddings/AIDOcell_100M_essential_K-562_2025_11_26_(D=640).h5ad",
        ROOT / "data/artifacts/official_k562/AIDOcell_100M_essential_K562_D640.h5ad",
        "AIDO.Cell-100M cached K562 embedding",
    ),
    (
        "official_gnn_simple_embedding_h5ad",
        "gene_embeddings/GNN_Simple_Official_(D=256).h5ad",
        ROOT / "data/artifacts/official_k562/GNN_Simple_Official_D256.h5ad",
        "GNN Simple official D256 embedding",
    ),
    (
        "official_string_gnn_keep20_graph",
        "gnn/9606.protein.links.ensembl_900_keep20_adaptive.txt",
        ROOT / "data/artifacts/official_k562/9606.protein.links.ensembl_900_keep20_adaptive.txt",
        "STRING keep20 graph source",
    ),
    (
        "esm2_gene_embedding_h5ad",
        "gene_embeddings/ESM2_(D=1280).h5ad",
        ROOT / "data/artifacts/gene_embeddings/ESM2_D1280.h5ad",
        "ESM2 gene embedding D1280",
    ),
]

for artifact_id, hf_path, output, desc in known:
    rec = run(
        ["python", "scripts/download_foundation_artifact.py", "--path", hf_path, "--output", str(output)],
        cwd=ROOT,
        timeout=3600,
    )
    add_item(
        id=artifact_id,
        type="public_hf_dataset_file",
        description=desc,
        source=f"huggingface:genbio-ai/foundation-models-perturbation/{hf_path}",
        local_path=str(output),
        status="present" if output.exists() else "failed",
        command=rec,
        file_info=file_info(output),
    )

derived_commands = [
    ("official_k562_task_contract", ["python", "scripts/build_official_k562_task.py", "build"]),
    ("official_k562_task_validate", ["python", "scripts/build_official_k562_task.py", "validate"]),
    (
        "class_distribution",
        [
            "python",
            "scripts/build_official_k562_class_distribution.py",
            "--train-tsv",
            "data/cell_lines/official_k562_cls/train.tsv",
            "--output",
            "data/artifacts/official_k562/class_distribution_train.json",
        ],
    ),
    (
        "pathway_membership_matrix",
        [
            "python",
            "scripts/build_k562_pathway_membership.py",
            "--data-dir",
            "data/cell_lines/official_k562_cls",
            "--output",
            "data/artifacts/pathways/k562_target_pathway_membership.npz",
            "--summary",
            str(RUN / "k562_pathway_membership_artifact_summary.json"),
        ],
    ),
]

for artifact_id, cmd in derived_commands:
    rec = run(cmd, cwd=ROOT, timeout=3600)
    add_item(
        id=artifact_id,
        type="derived_artifact_or_audit",
        status="present_or_completed" if rec["returncode"] == 0 else "failed_or_requires_review",
        command=rec,
    )

aido_dir = Path("/home/Models/AIDO.Cell-100M")
aido_manifest = RUN / "aido_cell_100m_model_dir_manifest.json"
rec = run(
    [
        "python",
        "scripts/download_hf_model_snapshot.py",
        "--repo-id",
        "genbio-ai/AIDO.Cell-100M",
        "--output-dir",
        str(aido_dir),
        "--include",
        "config.json",
        "generation_config.json",
        "model.safetensors",
        "README.md",
        "LICENSE",
        "--manifest",
        str(aido_manifest),
    ],
    cwd=ROOT,
    timeout=7200,
)
add_item(
    id="official_aido_cell_100m_model_dir",
    type="public_hf_model_snapshot",
    status="present_with_runtime_compatibility_to_verify" if aido_dir.exists() else "failed",
    source="huggingface:model/genbio-ai/AIDO.Cell-100M",
    local_path=str(aido_dir),
    command=rec,
    file_info=file_info(aido_dir),
    manifest_path=str(aido_manifest),
)

for artifact_id, repo_id, expected in [
    (
        "official_string_gnn_model_dir",
        "genbio-ai/STRING_GNN",
        ["config.json", "model.safetensors", "pytorch_model.bin", "graph_data.pt", "node_names.json"],
    ),
    ("scfoundation_candidate_xcompass", "xCompass-AI/scFoundation", ["config.json", "pytorch_model.bin", "model.safetensors"]),
    ("scgpt_candidate_bowang", "bowang-lab/scGPT", ["config.json", "pytorch_model.bin", "model.safetensors"]),
    ("geneformer_candidate_ctheodoris", "ctheodoris/Geneformer", ["config.json", "pytorch_model.bin", "model.safetensors"]),
]:
    info = hf_model_api(repo_id)
    siblings = []
    if info.get("ok"):
        siblings = [s.get("rfilename") for s in info.get("json", {}).get("siblings", [])]
    missing = [name for name in expected if name not in siblings]
    status = (
        "present_public_checkpoint_repo"
        if info.get("ok") and any(name in siblings for name in ["model.safetensors", "pytorch_model.bin"])
        else "blocked_unavailable_or_not_direct_checkpoint"
    )
    add_item(
        id=artifact_id,
        type="public_model_probe",
        source=f"huggingface:model/{repo_id}",
        status=status,
        expected_files=expected,
        available_files=siblings[:200],
        missing_expected_files=missing,
        raw_ok=info.get("ok"),
        gated=(info.get("json") or {}).get("gated") if info.get("ok") else None,
        private=(info.get("json") or {}).get("private") if info.get("ok") else None,
    )

prep_rec = run(
    ["python", "scripts/prepare_official_k562_missing_files.py", "--output", str(RUN / "missing_files_preparation.json")],
    cwd=ROOT,
    timeout=3600,
)
add_item(
    id="official_public_node_compatibility_preparation",
    type="compatibility_reconstruction",
    status="completed" if prep_rec["returncode"] == 0 else "failed_or_partial",
    caveat=(
        "STRING_GNN compatibility reconstruction is not the original checkpoint; "
        "AIDO compatibility patches use public ModelGenerator source and AIDO checkpoint."
    ),
    command=prep_rec,
    file_info_aido=file_info(Path("/home/Models/AIDO.Cell-100M")),
    file_info_string=file_info(Path("/home/Models/STRING_GNN")),
)

for artifact_id, cmd in [
    (
        "official_model_dir_validation",
        ["python", "scripts/validate_official_model_dirs.py", "--output", str(RUN / "model_dir_validation.json")],
    ),
    ("artifact_registry_audit_k562", ["python", "-m", "vc_demo.harness.artifact_registry", "--cell-line", "K562"]),
]:
    rec = run(cmd, cwd=ROOT, timeout=1200)
    add_item(id=artifact_id, type="validation", status="completed" if rec["returncode"] == 0 else "failed", command=rec)

disk = run(["bash", "-lc", "du -sh /workspace/models /workspace/vc-demo/data /workspace/_external 2>/dev/null || true; df -h /workspace"], cwd=ROOT)
add_item(id="disk_usage_after_acquisition", type="disk_audit", status="completed", command=disk)

by_id = {item["id"]: item for item in items}
lines: list[str] = []
lines.append("# Artifact Acquisition Sweep Report（中文）")
lines.append("")
lines.append(
    "本报告记录在 RunPod network volume `string-net-artifacts` 上执行的模型/数据 artifact 下载、验证与 blocker 审计。"
    "大文件保存在 `/workspace` 或 `/home/Models -> /workspace/models`，不会提交到 GitHub。"
)
lines.append("")
lines.append("## 总结")
lines.append("")
for status in sorted({item.get("status", "") for item in items}):
    lines.append(f"- `{status}`: {sum(1 for item in items if item.get('status') == status)}")
lines.append("")
lines.append("## 已可直接使用或已下载/构建")
lines.append("")
for artifact_id in [
    "official_essential_deg_with_split_h5ad",
    "official_k562_aido_cell_100m_embedding_h5ad",
    "official_gnn_simple_embedding_h5ad",
    "official_string_gnn_keep20_graph",
    "esm2_gene_embedding_h5ad",
    "official_k562_task_contract",
    "class_distribution",
    "pathway_membership_matrix",
    "official_aido_cell_100m_model_dir",
    "public_vcharness_repo",
    "public_modelgenerator_repo",
]:
    item = by_id.get(artifact_id)
    if not item:
        continue
    info = item.get("file_info") or {}
    size = info.get("bytes") or info.get("file_count") or ""
    lines.append(
        f"- `{artifact_id}`: `{item.get('status')}`; source: {item.get('source', 'derived')}; "
        f"path: `{item.get('local_path', '见 command/output')}`; size/file_count: `{size}`"
    )
lines.append("")
lines.append("## 不能作为原文同款直接使用的模块")
lines.append("")
lines.append(
    "- `official_string_gnn_model_dir`: HF repo `genbio-ai/STRING_GNN` 可访问，但公开 tree 不含 "
    "`config.json`、权重、`graph_data.pt`、`node_names.json`。因此不能声明为 VCHarness 原文同款 checkpoint。"
    "可以用公开 graph + GNN_Simple embedding 做 compatibility reconstruction 或重新训练。"
)
lines.append(
    "- `scfoundation_cell_embeddings`: 需要 row-aligned K562/scRNA cell embeddings 或明确 checkpoint + normalization + "
    "gene vocabulary + row order 编码流程。公开 checkpoint即使存在，也不能直接等同于本任务 row-aligned artifact；需要单独构建并验证。"
)
lines.append(
    "- `single_cell_foundation_model_artifact/scGPT`: 需要公开 checkpoint、基因词表、输入标准化、row order 映射和无泄漏编码流程。"
    "没有这些不能直接标为 present。"
)
lines.append(
    "- `regulatory_network_artifact`: 需要先定义网络来源、边语义、版本、阈值和 K562 target/perturbation gene 对齐；"
    "不能默认把任意调控网络当作 artifact。"
)
lines.append("")
lines.append("## 重建/训练建议")
lines.append("")
lines.append(
    "- 最适合作为独立训练案例的是 `STRING_GNN`：公开数据最完整，已有 STRING keep20 graph + GNN_Simple D256 embedding "
    "可作教师/初始化/对齐目标；目标产物是 `/home/Models/STRING_GNN` 兼容目录，包含 `config.json`、`modeling_*.py`、"
    "`graph_data.pt`、`node_names.json`、`model.safetensors` 或 `pytorch_model.bin`。"
)
lines.append(
    "- 预计资源：原型/兼容重建 1-3 小时；论文级可审计训练 0.5-2 天，取决于是否训练 GNN encoder、是否多 seed、"
    "是否做 downstream K562 validation。当前 RTX PRO 6000 96GB VRAM 足够。"
)
lines.append(
    "- 成果保存：大模型保存在 `/workspace/models/STRING_GNN`；训练中间产物保存在 `/workspace/artifacts/string_gnn_rebuild`；"
    "GitHub 只保存 manifest、脚本、README、checksum、训练配置和小型报告。"
)
lines.append("")
lines.append("## 机器可读 manifest")
lines.append("")
lines.append(f"- `{MANIFEST}`")
REPORT.write_text("\n".join(lines) + "\n")
print(json.dumps({"manifest": str(MANIFEST), "report": str(REPORT), "items": len(items)}, indent=2))
