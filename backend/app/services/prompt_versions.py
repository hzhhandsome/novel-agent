from __future__ import annotations

import hashlib
from typing import Any

CONTEXT_BUILDER_VERSION = "context_builder@2026-07-20.v1"

PROMPT_TEMPLATE_VERSIONS = {
    "build_prompt_package": "build_prompt_package@2026-07-20.v1",
    "generate_prose": "generate_prose@2026-07-20.v1",
    "audit_prose": "audit_prose@2026-07-20.v1",
    "summarize_chapter": "summarize_chapter@2026-07-20.v1",
    "judge_foreshadowing": "judge_foreshadowing@2026-07-20.v1",
    "judge_character_period": "judge_character_period@2026-07-20.v1",
    "propose_future_plan_updates": "propose_future_plan_updates@2026-07-20.v1",
    "builtin_eval": "builtin_eval@2026-07-20.v1",
    "llm_judge_eval": "llm_judge_eval@2026-07-20.v1",
}


def prompt_metadata(node: str, prompt_text: str) -> dict[str, str]:
    return {
        "prompt_template": node,
        "prompt_version": PROMPT_TEMPLATE_VERSIONS.get(node, f"{node}@unversioned"),
        "prompt_hash": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
        "context_builder_version": CONTEXT_BUILDER_VERSION,
    }


def collect_prompt_versions(step_snapshots: list[dict[str, Any] | None]) -> dict[str, Any]:
    versions: dict[str, dict[str, str]] = {}
    for snapshot in step_snapshots:
        if not snapshot:
            continue
        for key, value in snapshot.items():
            if key == "prompt_metadata" and isinstance(value, dict):
                _add_prompt_version(versions, str(value.get("prompt_template") or "unknown"), value)
            if key.endswith("_prompt_metadata") and isinstance(value, dict):
                _add_prompt_version(versions, key[: -len("_prompt_metadata")], value)
    return {
        "context_builder_version": CONTEXT_BUILDER_VERSION,
        "nodes": versions,
    }


def _add_prompt_version(target: dict[str, dict[str, str]], node: str, value: dict[str, Any]) -> None:
    target[node] = {
        "prompt_template": str(value.get("prompt_template") or node),
        "prompt_version": str(value.get("prompt_version") or ""),
        "prompt_hash": str(value.get("prompt_hash") or ""),
        "context_builder_version": str(value.get("context_builder_version") or CONTEXT_BUILDER_VERSION),
    }
