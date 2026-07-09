from __future__ import annotations

from pathlib import Path
from typing import Any

PROXY_MARKERS = (
    "OfficialK562NativeModel",
    "native_public_best_reimplementation",
    "implementation_agent_official_native_proxy",
    "native custom_program proxy",
    "compact native",
    "compact proxy",
    "executable proxy",
)


def model_source_violations(model_path: Path) -> list[str]:
    if not model_path.exists():
        return [f"missing_model_source:{model_path}"]
    text = model_path.read_text(encoding="utf-8", errors="ignore")
    return [f"proxy_marker:{marker}" for marker in PROXY_MARKERS if marker in text]


def config_proxy_violations(config: dict[str, Any]) -> list[str]:
    model = dict(config.get("model", {}) or {})
    violations: list[str] = []
    blueprint = str(model.get("program_blueprint", ""))
    custom_path = str(model.get("custom_model_path", ""))
    note = str(config.get("proposal_note", ""))
    if blueprint == "official_native_public_best_reimplementation":
        violations.append("proxy_blueprint:official_native_public_best_reimplementation")
    if custom_path.endswith("src/vc_demo/official_k562/native_public_best.py") or custom_path.endswith("official_k562/native_public_best.py"):
        violations.append("proxy_model_path:native_public_best.py")
    lowered_note = note.lower()
    if "proxy" in lowered_note or "compact reimplementation" in lowered_note:
        violations.append("proxy_proposal_note")
    return violations


def assert_no_formal_proxy(config: dict[str, Any], model_path: Path | None = None, *, context: str = "formal official K562 run") -> None:
    violations = config_proxy_violations(config)
    if model_path is not None:
        violations.extend(model_source_violations(model_path))
    if violations:
        raise RuntimeError(
            f"{context} forbids compact native/proxy implementations. "
            "Use the external public static benchmark or implement the full artifact-backed blueprint instead. "
            f"Violations: {', '.join(sorted(set(violations)))}"
        )
