"""Additional visually distinct background presets for SVG Pattern Studio 0.9.

Each composition has its own palette, two shape families at the top and bottom,
and varied spacing, orientation and occasionally an offset echo of a shape.
This module deliberately contains no Streamlit dependency.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

try:
    from .generator import default_layer
except ImportError:
    from generator import default_layer

# theme name, gradient start/end, pattern colors, two top shapes, two bottom shapes
# Keep names color-first for easy browsing.
RECIPES = [
    ("ミント・波紋", "#D4F6E7", "#62CDB0", "#218A79", "#E6FFF8", "Organic contours", "Radiating arcs", "Flowing waves", "Dot field"),
    ("セージ・幾何格子", "#DCE4D2", "#839C87", "#345E53", "#F8FFF1", "Hexagon grid", "Curved grid", "Organic contours", "Triangle mesh"),
    ("オリーブ・等高線", "#343D21", "#8C9850", "#DDE6A4", "#F9F2C6", "Organic contours", "Dot field", "Perspective fan", "Flowing waves"),
    ("シアン・星座", "#06283F", "#1686B2", "#96F4FF", "#E9FFFF", "Triangle mesh", "Dot field", "Spirograph", "Radiating arcs"),
    ("アクア・流線", "#E4FFFF", "#55B4C1", "#16778B", "#E5FFFF", "Flowing waves", "Curved grid", "Perspective fan", "Dot field"),
    ("インディゴ・軌道", "#151945", "#5454A2", "#BDC6FF", "#C7F0FF", "Spirograph", "Radiating arcs", "Curved grid", "Flowing waves"),
    ("ラベンダー・交差曲線", "#DFD9F8", "#9489CB", "#69559A", "#FFFFFF", "Curved grid", "Flowing waves", "Organic contours", "Perspective fan"),
    ("ライラック・網目", "#362348", "#9375B8", "#E5C9FF", "#C7E1FF", "Triangle mesh", "Hexagon grid", "Flowing waves", "Dot field"),
    ("ワインレッド・波紋", "#36162E", "#8C355C", "#FFD3DD", "#F1AED0", "Organic contours", "Radiating arcs", "Flowing waves", "Spirograph"),
    ("バーガンディ・蜂の巣", "#581C2A", "#AE5660", "#FFBCB5", "#FFF1D9", "Hexagon grid", "Triangle mesh", "Curved grid", "Dot field"),
    ("サーモン・流線", "#FFE4D9", "#ED8D7B", "#B24651", "#FFFAE8", "Flowing waves", "Perspective fan", "Organic contours", "Dot field"),
    ("ピーチ・散点", "#FFF2DE", "#F0B68C", "#A96861", "#FFF9F2", "Dot field", "Radiating arcs", "Flowing waves", "Hexagon grid"),
    ("テラコッタ・地形線", "#6F342D", "#C6795A", "#FFE1B0", "#FFF1DA", "Organic contours", "Curved grid", "Hexagon grid", "Perspective fan"),
    ("ブロンズ・放射線", "#392C23", "#AA7242", "#FCD69B", "#F6E5CD", "Radiating arcs", "Spirograph", "Perspective fan", "Triangle mesh"),
    ("ゴールド・細密格子", "#FBF0CF", "#D1A83E", "#8C641F", "#FFF9EB", "Curved grid", "Hexagon grid", "Triangle mesh", "Flowing waves"),
    ("アンバー・交差波", "#5D330B", "#DB961B", "#FFE0A2", "#FFF6DC", "Flowing waves", "Curved grid", "Perspective fan", "Organic contours"),
    ("クリーム・波紋", "#FFFDF2", "#E7D5B5", "#84745D", "#FFFFFF", "Organic contours", "Radiating arcs", "Flowing waves", "Dot field"),
    ("ホワイト・曲線", "#FFFFFF", "#D7E2EB", "#526B87", "#FFFFFF", "Flowing waves", "Spirograph", "Curved grid", "Hexagon grid"),
    ("スレートグレー・網目", "#29343D", "#667989", "#D1E2EF", "#E8F6FA", "Triangle mesh", "Hexagon grid", "Perspective fan", "Flowing waves"),
    ("スモークグレー・線束", "#D3D3D5", "#6E717D", "#383D4F", "#F6F6FA", "Perspective fan", "Flowing waves", "Radiating arcs", "Dot field"),
    ("ブルーグレー・流線", "#E0E9EC", "#728FA6", "#375B79", "#FFFFFF", "Flowing waves", "Organic contours", "Curved grid", "Spirograph"),
    ("ペールグレー・六角格子", "#F5F4F2", "#BEC4C7", "#61676B", "#FFFFFF", "Hexagon grid", "Dot field", "Triangle mesh", "Organic contours"),
    ("ブラック・幾何交差", "#05060A", "#282E35", "#ABBFCB", "#6BB9D2", "Curved grid", "Triangle mesh", "Spirograph", "Perspective fan"),
    ("フォレスト・曲線迷路", "#071F20", "#2C5C47", "#9FE2B4", "#B9F2E1", "Curved grid", "Hexagon grid", "Organic contours", "Flowing waves"),
    ("モスグリーン・等高線", "#4B5542", "#9BB78E", "#F0FFE5", "#D7F5B9", "Organic contours", "Triangle mesh", "Dot field", "Radiating arcs"),
    ("ミッドナイトブルー・干渉波", "#060E28", "#182D70", "#79BFFF", "#B5D6FF", "Flowing waves", "Flowing waves", "Curved grid", "Perspective fan"),
    ("フューシャ・スパイラル", "#3B104B", "#BA3C9F", "#FFAFED", "#DDBFFF", "Spirograph", "Radiating arcs", "Flowing waves", "Organic contours"),
    ("ローズゴールド・格子", "#F8E0D7", "#B98079", "#804853", "#FFF1DC", "Hexagon grid", "Curved grid", "Flowing waves", "Triangle mesh"),
]


def additional_presets(base: dict[str, Any]) -> dict[str, dict[str, Any]]:
    """Generate deterministic presets; return fresh and independent dictionaries."""
    themes: dict[str, dict[str, Any]] = {}
    for i, (name, c1, c2, ink, glint, tk1, tk2, bk1, bk2) in enumerate(RECIPES):
        config = deepcopy(base)
        config.update(name=name, bg_start=c1, bg_end=c2, angle=110+(i * 17) % 70)
        seed = 210 + i * 13
        # Distinct placement, angle and densities between themes. Match the seed
        # when copying a shape: the line geometry is preserved for echo effects.
        def shape(kind: str, n: int, col: str, alpha: float, density: int,
                  *, x: int, y: int, rotation: int, fade: str, scale: float) -> dict[str, Any]:
            return default_layer(kind, n) | {
                "color": col, "opacity": alpha, "density": density,
                "width": .75 + (i % 3) * .08,
                "scale": scale, "x": x, "y": y,
                "rotation": rotation, "fade": fade,
            }

        config["top"]["layers"] = [
            shape(tk1, seed, ink, .28 + (i % 3) * .07, 20 + (i % 5) * 3,
                  x=-27+(i % 5)*4, y=-23, rotation=-10+(i % 5)*5,
                  fade="To right", scale=1.15+(i % 4)*.08),
            shape(tk2, seed if tk1 == tk2 else seed+1, glint, .19+(i % 4)*.03, 17+(i % 6)*2,
                  x=11+(i % 5)*6, y=-14-(i % 3)*5, rotation=8-(i % 4)*4,
                  fade="To bottom", scale=1.12+(i % 3)*.10),
        ]
        config["bottom"]["layers"] = [
            shape(bk1, seed+2, glint, .25+(i % 4)*.05, 24+(i % 5)*3,
                  x=12+(i % 6)*4, y=27+(i % 4)*4, rotation=-13+(i % 6)*5,
                  fade="To top", scale=1.24+(i % 3)*.09),
            shape(bk2, seed+3, ink, .16+(i % 3)*.035, 15+(i % 7)*2,
                  x=-7+(i % 5)*3, y=23+(i % 3)*5, rotation=9-(i % 5)*4,
                  fade="To top", scale=1.12+(i % 4)*.08),
        ]
        themes[name] = config
    return themes
