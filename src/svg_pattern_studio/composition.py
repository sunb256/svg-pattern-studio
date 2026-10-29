"""Independent palette × pattern-set composition.

A pattern set now chooses exactly one motif for the top and one motif for the
bottom. Each side may optionally render a second *echo* of the same motif,
slightly shifted / rotated, but different motifs are never mixed within one
side. This keeps the concept simple and matches the UI wording.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, MutableMapping

try:
    from .generator import default_layer
    from .web_background import default_web_theme, web_presets
except ImportError:
    from generator import default_layer
    from web_background import default_web_theme, web_presets

# name -> top(kind,count), bottom(kind,count)
PATTERN_SETS: dict[str, dict[str, tuple[str, int]]] = {
    "星座ネットワーク": {"top": ("Triangle mesh", 2), "bottom": ("Perspective fan", 2)},
    "波線とドット": {"top": ("Flowing waves", 2), "bottom": ("Dot field", 2)},
    "曲線と六角形": {"top": ("Curved grid", 1), "bottom": ("Hexagon grid", 2)},
    "等高線とひし形": {"top": ("Organic contours", 1), "bottom": ("Diamond lattice", 2)},
    "放射アークと軌道": {"top": ("Radiating arcs", 2), "bottom": ("Orbit ellipses", 1)},
    "スパイログラフとリング": {"top": ("Spirograph", 1), "bottom": ("Concentric rings", 1)},
    "遠近パースとシェブロン": {"top": ("Perspective fan", 1), "bottom": ("Chevron field", 2)},
    "六角形と波線": {"top": ("Hexagon grid", 2), "bottom": ("Flowing waves", 1)},
    "ドットと入れ子長方形": {"top": ("Dot field", 1), "bottom": ("Nested rectangles", 2)},
    "斜めストライプと円弧": {"top": ("Diagonal stripes", 2), "bottom": ("Arc lattice", 1)},
    "同心リングとリボン": {"top": ("Concentric rings", 1), "bottom": ("Ribbon bands", 2)},
    "リボンと三角形": {"top": ("Ribbon bands", 2), "bottom": ("Triangle mesh", 2)},
    "ひし形格子と放射線": {"top": ("Diamond lattice", 2), "bottom": ("Sunburst rays", 1)},
    "シェブロンと曲線": {"top": ("Chevron field", 1), "bottom": ("Curved grid", 2)},
    "サンバーストと等高線": {"top": ("Sunburst rays", 1), "bottom": ("Organic contours", 1)},
    "入れ子長方形と斜め線": {"top": ("Nested rectangles", 1), "bottom": ("Diagonal stripes", 2)},
    "軌道楕円とスパイラル": {"top": ("Orbit ellipses", 2), "bottom": ("Spirograph", 1)},
    "円弧ラティスと六角形": {"top": ("Arc lattice", 1), "bottom": ("Hexagon grid", 2)},
}

DEFAULT_PATTERN = "星座ネットワーク"


def palette_catalog() -> dict[str, dict[str, Any]]:
    presets = web_presets()
    counts: dict[str, int] = {}
    for name in presets:
        prefix = name.split("・", 1)[0]
        counts[prefix] = counts.get(prefix, 0) + 1
    palettes = {}
    for name, config in presets.items():
        prefix, suffix = (name.split("・", 1) + [""])[:2]
        label = f"{prefix}（{suffix}）" if counts[prefix] > 1 else prefix
        colors: dict[str, list[str]] = {}
        for side in ("top", "bottom"):
            layers = config[side]["layers"]
            colors[side] = [x["color"] for x in layers] or ["#B3DFFF"]
        palettes[label] = {
            "bg_start": config["bg_start"],
            "bg_end": config["bg_end"],
            "angle": config["angle"],
            "colors": colors,
            "source": name,
        }
    return palettes


def _layer(kind: str, *, side: str, pattern_index: int, color: str) -> dict[str, Any]:
    seed = 131 + pattern_index * 113 + (0 if side == "top" else 37)
    layer = default_layer(kind, seed)
    top = side == "top"
    layer.update({
        "color": color,
        "opacity": .28 if top else .31,
        "density": 20 + (pattern_index % 13),
        "width": .85 + .1 * (pattern_index % 3),
        "scale": round(1.08 + .07 * ((pattern_index) % 4), 2),
        "x": -16 + (pattern_index * 3) % 12 if top else 12 + (pattern_index * 2) % 14,
        "y": -24 if top else 23,
        "rotation": (-12 if top else 8) + (pattern_index * 5) % 18 - 9,
        "fade": "To right" if top else "To top",
        "blend": "normal",
        "warp_top": 65 + (pattern_index * 3) % 18,
        "warp_bottom": 122 + (pattern_index * 7) % 25,
        "warp_top_shift": -14 + (pattern_index * 3) % 15,
        "warp_bottom_shift": -8 + (pattern_index * 5) % 18,
    })
    return layer


def _echo(layer: dict[str, Any], *, side: str, color: str | None = None) -> dict[str, Any]:
    copy = deepcopy(layer)
    copy.update({
        "x": int(layer["x"]) + (7 if side == "top" else -8),
        "y": int(layer["y"]) + (4 if side == "top" else -4),
        "rotation": int(layer["rotation"]) + (8 if side == "top" else -8),
        "scale": round(float(layer["scale"]) * 1.03, 3),
        "opacity": round(float(layer["opacity"]) * .7, 3),
        "warp_top": max(40, int(layer["warp_top"]) - 7),
        "warp_bottom": min(160, int(layer["warp_bottom"]) + 9),
        "warp_top_shift": int(layer["warp_top_shift"]) + 4,
        "warp_bottom_shift": int(layer["warp_bottom_shift"]) - 4,
        "blend": "screen",
    })
    if color:
        copy["color"] = color
    return copy


def compose_theme(palette_name: str, pattern_name: str) -> dict[str, Any]:
    palettes = palette_catalog()
    if palette_name not in palettes:
        raise ValueError(f"Unknown palette: {palette_name}")
    if pattern_name not in PATTERN_SETS:
        raise ValueError(f"Unknown pattern set: {pattern_name}")
    p = palettes[palette_name]
    index = list(PATTERN_SETS).index(pattern_name)
    config = deepcopy(default_web_theme())
    config.update({
        "name": f"{palette_name}・{pattern_name}",
        "bg_start": p["bg_start"], "bg_end": p["bg_end"], "angle": p["angle"],
    })
    for side in ("top", "bottom"):
        kind, count = PATTERN_SETS[pattern_name][side]
        inks = p["colors"][side]
        base = _layer(kind, side=side, pattern_index=index, color=inks[0])
        layers = [base]
        if count == 2:
            echo_color = inks[1 % len(inks)] if len(inks) > 1 else None
            layers.append(_echo(base, side=side, color=echo_color))
        config[side]["layers"] = layers
        config[side]["vertical_feather"] = 30 if side == "top" else 32
        config[side]["edge_feather"] = 0
        config[side]["size"] = 115
        config[side]["size_unit"] = "%"
    return config


def apply_composition(state: MutableMapping[str, Any], *, palette_name: str, pattern_name: str) -> None:
    state["web_config"] = compose_theme(palette_name, pattern_name)
    state["web_rev"] = int(state.get("web_rev", 0)) + 1
    state["web_focus"] = None
    for side in ("top", "bottom"):
        state.pop(f"web-undo-{side}", None)
