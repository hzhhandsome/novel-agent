from __future__ import annotations

import math
from typing import Any


def estimate_model_usage(
    node: str,
    route: str,
    model_config: dict,
    input_text: str,
    output_text: str,
    duration_ms: int,
    input_cost_per_1k: float,
    output_cost_per_1k: float,
) -> dict[str, Any]:
    input_tokens = estimate_tokens(input_text)
    output_tokens = estimate_tokens(output_text)
    estimated_cost = (input_tokens / 1000 * input_cost_per_1k) + (output_tokens / 1000 * output_cost_per_1k)
    return {
        "node": node,
        "route": route,
        "model_config": model_config,
        "estimated_input_tokens": input_tokens,
        "estimated_output_tokens": output_tokens,
        "duration_ms": duration_ms,
        "estimated_cost": round(estimated_cost, 8),
    }


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 2))


def aggregate_model_usage(snapshots: list[dict | None]) -> dict[str, Any]:
    calls = []
    for snapshot in snapshots:
        if not snapshot:
            continue
        for key, value in snapshot.items():
            if key.endswith("_model_usage") and isinstance(value, dict):
                calls.append(value)

    return {
        "estimated_input_tokens": sum(int(item.get("estimated_input_tokens") or 0) for item in calls),
        "estimated_output_tokens": sum(int(item.get("estimated_output_tokens") or 0) for item in calls),
        "duration_ms": sum(int(item.get("duration_ms") or 0) for item in calls),
        "estimated_cost": round(sum(float(item.get("estimated_cost") or 0) for item in calls), 8),
        "calls": calls,
    }
