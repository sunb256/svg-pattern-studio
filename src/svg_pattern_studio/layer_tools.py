"""Non-UI layer editing operations shared by both Streamlit editors.

Identical ``seed`` and ``kind`` deliberately preserve identical geometry.
Only the layer transforms/appearance change when making a shifted copy.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

MAX_LAYERS = 6


def _index(layers: list[dict[str, Any]], index: int) -> None:
    if index < 0 or index >= len(layers):
        raise IndexError("Layer index out of range")


def _bounded(value: int | float, lo: int, hi: int) -> int:
    return max(lo, min(hi, round(value)))


def duplicate_layer(
    layers: list[dict[str, Any]],
    source: int,
    *,
    shift_x: int = 0,
    shift_y: int = 0,
    rotation: int = 0,
    opacity_factor: float = 1.0,
    limit: int = MAX_LAYERS,
) -> list[dict[str, Any]]:
    """Insert an independent copy directly above source (same seed and kind)."""
    _index(layers, source)
    if len(layers) >= limit:
        raise ValueError(f"Cannot add more than {limit} layers")
    result = deepcopy(layers)
    duplicate = deepcopy(layers[source])
    duplicate["x"] = _bounded(duplicate["x"] + shift_x, -100, 100)
    duplicate["y"] = _bounded(duplicate["y"] + shift_y, -100, 100)
    duplicate["rotation"] = _bounded(duplicate["rotation"] + rotation, -180, 180)
    duplicate["opacity"] = min(1.0, max(0.0, duplicate["opacity"] * opacity_factor))
    result.insert(source + 1, duplicate)
    return result


def copy_layer(layers: list[dict[str, Any]], source: int, target: int) -> list[dict[str, Any]]:
    """Replace an existing target layer, leaving source untouched."""
    _index(layers, source)
    _index(layers, target)
    if source == target:
        raise ValueError("Source and target must differ")
    result = deepcopy(layers)
    result[target] = deepcopy(layers[source])
    return result


def nudge_layer(
    layers: list[dict[str, Any]], index: int, *,
    dx: int = 0, dy: int = 0, drotation: int = 0,
) -> list[dict[str, Any]]:
    """Adjust only placement, keeping geometry (and random seed) unchanged."""
    _index(layers, index)
    result = deepcopy(layers)
    item = result[index]
    item["x"] = _bounded(item["x"] + dx, -100, 100)
    item["y"] = _bounded(item["y"] + dy, -100, 100)
    item["rotation"] = _bounded(item["rotation"] + drotation, -180, 180)
    return result


def layer_difference(source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    """Summarize transform differences and whether both use the same geometry."""
    return {
        "dx": int(target["x"] - source["x"]),
        "dy": int(target["y"] - source["y"]),
        "drotation": int(target["rotation"] - source["rotation"]),
        "dscale": round((target["scale"] - source["scale"]) * 100),
        "same_geometry": all(source[field] == target[field]
                             for field in ("kind", "seed", "density")),
    }
