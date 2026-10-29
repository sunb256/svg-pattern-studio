"""Responsive Web background compositions.

Pure Python (standard library only); independent transparent top/bottom SVG strips
are combined with a CSS gradient. CSS is shared by browser preview and ZIP output.
"""

from __future__ import annotations

import base64
from copy import deepcopy
import io
import json
from html import escape
import re
import zipfile
from typing import Any

try:
    from .generator import default_layer, render_svg
except ImportError:  # Streamlit executes app.py as a script
    from generator import default_layer, render_svg

COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
ALIGNMENTS = {"left": "0%", "center": "50%", "right": "100%"}


def default_web_theme() -> dict[str, Any]:
    top_mesh = default_layer("Triangle mesh", 11) | {
        "color": "#A8DFFF", "opacity": .23, "density": 23,
        "width": .9, "scale": 1.15, "x": -10, "y": -9,
        "fade": "To right",
    }
    top_grid = default_layer("Curved grid", 30) | {
        "color": "#96C9F9", "opacity": .09, "density": 13,
        "fade": "To bottom", "x": 0, "y": -35,
    }
    bottom_wave = default_layer("Flowing waves", 41) | {
        "color": "#B8EAFF", "opacity": .27, "density": 19,
        "width": .95, "scale": 1.5, "y": 24,
        "fade": "To top", "rotation": -8,
    }
    bottom_grid = default_layer("Perspective fan", 65) | {
        "color": "#A7D5FC", "opacity": .15, "density": 18,
        "width": .8, "scale": 1.12, "y": 20,
        "fade": "To top", "rotation": 8,
    }
    return {
        "name": "ブルー・ネットワーク",
        "bg_start": "#14246B", "bg_end": "#206CA8", "angle": 145,
        "top": {
            "enabled": True, "width": 1600, "height": 480,
            "size": 115, "size_unit": "%", "align": "center", "inset": 0,
            "anchor_y": "top", "shift_x": 0, "edge_feather": 0, "vertical_feather": 28,
            "layers": [top_mesh, top_grid],
        },
        "bottom": {
            "enabled": True, "width": 1600, "height": 460,
            "size": 115, "size_unit": "%", "align": "center", "inset": 0,
            "anchor_y": "bottom", "shift_x": 0, "edge_feather": 0, "vertical_feather": 28,
            "layers": [bottom_wave, bottom_grid],
        },
    }


def web_presets() -> dict[str, dict[str, Any]]:
    ocean = default_web_theme()
    violet = deepcopy(ocean)
    violet.update(name="パープル・曲線", bg_start="#21143D", bg_end="#744A93", angle=130)
    violet["top"]["layers"] = [
        default_layer("Organic contours", 21) | {
            "color": "#F4BDFF", "opacity": .29, "density": 27,
            "scale": 1.3, "x": -30, "y": -45, "fade": "To right",
        },
        default_layer("Radiating arcs", 8) | {
            "color": "#A6B5FF", "opacity": .24, "density": 21,
            "scale": 1.2, "x": 30, "y": -15, "fade": "To bottom",
        },
    ]
    violet["bottom"]["layers"] = [
        default_layer("Flowing waves", 92) | {
            "color": "#E2A9FF", "opacity": .36, "density": 31,
            "rotation": 14, "scale": 1.3, "y": 12, "fade": "To top",
        },
        default_layer("Curved grid", 53) | {
            "color": "#A0B9FF", "opacity": .14, "density": 14,
            "scale": 1.3, "fade": "To top",
        },
    ]
    emerald = deepcopy(ocean)
    emerald.update(name="エメラルド・等高線", bg_start="#0A2A37", bg_end="#17797F", angle=125)
    emerald["top"]["layers"] = [
        default_layer("Hexagon grid", 10) | {
            "color": "#8EF3DF", "opacity": .28, "density": 19,
            "scale": 1.0, "fade": "To right", "x": -15,
        },
        default_layer("Dot field", 17) | {
            "color": "#B1FFED", "opacity": .18, "density": 24,
            "fade": "To bottom", "y": -5,
        },
    ]
    emerald["bottom"]["layers"] = [
        default_layer("Organic contours", 33) | {
            "color": "#A5F5DF", "opacity": .38, "density": 28,
            "scale": 1.55, "x": 30, "y": 60, "fade": "To top",
        },
    ]
    def layer(kind: str, seed: int, color: str, opacity: float, density: int, **kwargs: Any) -> dict[str, Any]:
        return default_layer(kind, seed) | {
            "color": color, "opacity": opacity, "density": density, **kwargs,
        }

    midnight = deepcopy(ocean)
    midnight.update(name="ネイビー・設計グリッド", bg_start="#08152C", bg_end="#214E75", angle=135)
    midnight["top"]["layers"] = [
        layer("Curved grid", 31, "#8DD4FC", .29, 24, fade="To bottom", scale=1.22, y=-23),
        layer("Dot field", 56, "#D1E9FF", .22, 23, fade="To right", scale=1.12),
    ]
    midnight["bottom"]["layers"] = [
        layer("Perspective fan", 32, "#7AC6F1", .30, 32, fade="To top", scale=1.36, y=18),
        layer("Flowing waves", 46, "#9BCEFB", .13, 14, fade="To top", rotation=-6),
    ]

    dunes = deepcopy(ocean)
    dunes.update(name="オレンジ・砂丘", bg_start="#4B263B", bg_end="#BA7153", angle=140)
    dunes["top"]["layers"] = [
        layer("Flowing waves", 63, "#FFD8A0", .33, 28, fade="To right", rotation=12, scale=1.15, y=-28),
        layer("Radiating arcs", 23, "#FFE7C0", .18, 22, fade="To bottom", scale=1.13, x=32, y=-20),
    ]
    dunes["bottom"]["layers"] = [
        layer("Organic contours", 25, "#FFE3C5", .34, 23, fade="To top", scale=1.68, y=48),
        layer("Flowing waves", 17, "#F9B887", .22, 19, fade="To top", y=26),
    ]

    aurora = deepcopy(ocean)
    aurora.update(name="ターコイズ・オーロラ", bg_start="#091D36", bg_end="#176D83", angle=120)
    aurora["top"]["layers"] = [
        layer("Radiating arcs", 44, "#8AFFE3", .41, 31, fade="To bottom", scale=1.53, x=-24, y=-35),
        layer("Flowing waves", 18, "#A2B9FF", .22, 25, fade="To right", rotation=-13, y=-19),
    ]
    aurora["bottom"]["layers"] = [
        layer("Curved grid", 37, "#91EFE0", .23, 25, fade="To top", scale=1.24, rotation=-9, y=20),
        layer("Flowing waves", 8, "#A9CAFF", .25, 30, fade="To top", rotation=13, y=25),
    ]

    coral = deepcopy(ocean)
    coral.update(name="コーラル・六角格子", bg_start="#351A47", bg_end="#A34C79", angle=150)
    coral["top"]["layers"] = [
        layer("Hexagon grid", 28, "#FFB8CF", .26, 20, fade="To right", scale=1.18, x=-15, y=-23),
        layer("Triangle mesh", 74, "#B6B9FF", .18, 18, fade="To bottom", scale=1.12, x=21),
    ]
    coral["bottom"]["layers"] = [
        layer("Flowing waves", 39, "#FFCDDB", .30, 27, fade="To top", scale=1.2, rotation=7, y=22),
        layer("Radiating arcs", 52, "#F1B0FF", .19, 23, fade="To top", scale=1.38, x=33, y=24),
    ]

    forest = deepcopy(ocean)
    forest.update(name="グリーン・幾何メッシュ", bg_start="#0B2831", bg_end="#386D59", angle=125)
    forest["top"]["layers"] = [
        layer("Triangle mesh", 25, "#A1F1CC", .30, 22, fade="To right", scale=1.13, x=-22, y=-19),
        layer("Dot field", 35, "#E0FFE0", .17, 19, fade="To bottom", scale=1.1),
    ]
    forest["bottom"]["layers"] = [
        layer("Perspective fan", 16, "#B1E5CF", .31, 34, fade="To top", scale=1.17, y=21),
        layer("Organic contours", 45, "#B6FFD7", .18, 16, fade="To top", x=32, y=31, scale=1.16),
    ]

    graphite = deepcopy(ocean)
    graphite.update(name="ダークグレー・ミニマル", bg_start="#121D2A", bg_end="#374B61", angle=160)
    graphite["top"]["layers"] = [
        layer("Hexagon grid", 17, "#C9D9E8", .16, 16, fade="To right", scale=1.2, y=-16),
        layer("Spirograph", 61, "#91C4E6", .15, 13, fade="To bottom", scale=.72, x=26, y=-24),
    ]
    graphite["bottom"]["layers"] = [
        layer("Flowing waves", 80, "#B7D9EE", .23, 16, fade="To top", scale=1.26, rotation=-3, y=20),
    ]

    # v0.7: nine additional compositions.  Some intentionally use the same
    # kind + seed twice with a small translation/rotation offset: this creates
    # the interlaced, echo-like lines that the layer-copy workflow encourages.
    copper = deepcopy(ocean)
    copper.update(name="カッパー・回路格子", bg_start="#201C32", bg_end="#845760", angle=133)
    copper["top"]["layers"] = [
        layer("Hexagon grid", 85, "#F5BA9C", .28, 20, fade="To right", x=-16, rotation=6),
        layer("Curved grid", 63, "#FFD5B1", .19, 24, fade="To bottom", y=-20, scale=1.2),
    ]
    copper["bottom"]["layers"] = [
        layer("Perspective fan", 47, "#EFB38D", .30, 30, fade="To top", y=27, rotation=-9),
        layer("Triangle mesh", 79, "#F8D4D1", .16, 16, fade="To top", x=22, y=18),
    ]

    glacier = deepcopy(ocean)
    glacier.update(name="アイスブルー・三角メッシュ", bg_start="#0D2545", bg_end="#4E92BD", angle=140)
    glacier["top"]["layers"] = [
        layer("Triangle mesh", 116, "#D8F7FF", .38, 25, fade="To right", x=-16, y=-22, scale=1.14),
        layer("Triangle mesh", 116, "#83D8F4", .15, 25, fade="To right", x=-10, y=-19, rotation=5, scale=1.14),
    ]
    glacier["bottom"]["layers"] = [
        layer("Organic contours", 78, "#C6EEFA", .30, 23, fade="To top", scale=1.38, x=25, y=37),
        layer("Dot field", 39, "#FFFFFF", .16, 25, fade="To top", y=12),
    ]

    orbit = deepcopy(ocean)
    orbit.update(name="ブラック・軌道", bg_start="#0C1025", bg_end="#37446D", angle=158)
    orbit["top"]["layers"] = [
        layer("Spirograph", 72, "#A7B8FF", .29, 29, fade="To right", scale=1.16, x=-29, y=-30),
        layer("Radiating arcs", 88, "#A8E9FF", .16, 25, fade="To bottom", x=27, y=-19),
    ]
    orbit["bottom"]["layers"] = [
        layer("Radiating arcs", 31, "#A6B5FF", .24, 28, fade="To top", scale=1.30, x=30, y=30),
        layer("Flowing waves", 13, "#9CCDEE", .14, 17, fade="To top", rotation=-11, y=21),
    ]

    sakura = deepcopy(ocean)
    sakura.update(name="ピンク・ウェーブ", bg_start="#3B284A", bg_end="#BD83A5", angle=125)
    sakura["top"]["layers"] = [
        layer("Organic contours", 119, "#FFE0E7", .29, 29, fade="To right", scale=1.38, x=-32, y=-26),
        layer("Dot field", 54, "#F8D7F0", .23, 24, fade="To bottom", y=-18),
    ]
    sakura["bottom"]["layers"] = [
        layer("Flowing waves", 71, "#FFD8E5", .34, 25, fade="To top", rotation=-6, y=27),
        layer("Flowing waves", 71, "#C9CDFF", .17, 25, fade="To top", rotation=-1, x=7, y=30),
    ]

    electric = deepcopy(ocean)
    electric.update(name="コバルト・曲線グリッド", bg_start="#0F173D", bg_end="#3057B2", angle=148)
    electric["top"]["layers"] = [
        layer("Curved grid", 107, "#76ECFF", .33, 25, fade="To right", rotation=9, x=-12, y=-22),
        layer("Radiating arcs", 52, "#AFC3FF", .20, 18, fade="To bottom", x=24, y=-12, scale=1.2),
    ]
    electric["bottom"]["layers"] = [
        layer("Perspective fan", 29, "#72DFFF", .37, 37, fade="To top", rotation=-12, y=22),
        layer("Curved grid", 107, "#ABB5FF", .13, 25, fade="To top", rotation=15, x=-3, y=26),
    ]

    sandstone = deepcopy(ocean)
    sandstone.update(name="ベージュ・等高線", bg_start="#39303D", bg_end="#A78C75", angle=137)
    sandstone["top"]["layers"] = [
        layer("Organic contours", 106, "#F8DEB9", .38, 32, fade="To right", scale=1.4, x=-28, y=-22),
        layer("Hexagon grid", 77, "#EFD9BB", .16, 15, fade="To bottom", scale=1.12, rotation=5),
    ]
    sandstone["bottom"]["layers"] = [
        layer("Triangle mesh", 93, "#FFF0D6", .19, 18, fade="To top", y=26),
        layer("Flowing waves", 62, "#F5C9AB", .29, 24, fade="To top", rotation=8, y=30),
    ]

    interference = deepcopy(ocean)
    interference.update(name="ティール・干渉波", bg_start="#072D39", bg_end="#138494", angle=124)
    interference["top"]["layers"] = [
        layer("Flowing waves", 112, "#A4FFF1", .33, 32, fade="To right", rotation=7, x=-8, y=-20),
        layer("Flowing waves", 112, "#B0DAFF", .19, 32, fade="To right", rotation=12, x=0, y=-19),
    ]
    interference["bottom"]["layers"] = [
        layer("Curved grid", 32, "#9BEADD", .22, 23, fade="To top", y=25, rotation=-6),
        layer("Radiating arcs", 67, "#6BCBE4", .20, 20, fade="To top", x=31, y=33),
    ]

    cobalt = deepcopy(ocean)
    cobalt.update(name="ブルー・星座メッシュ", bg_start="#111C52", bg_end="#2659A0", angle=132)
    cobalt["top"]["layers"] = [
        layer("Dot field", 64, "#E7F3FF", .33, 29, fade="To right", x=-18, y=-16),
        layer("Triangle mesh", 47, "#8AC7FF", .24, 20, fade="To bottom", x=-24, y=-18),
    ]
    cobalt["bottom"]["layers"] = [
        layer("Spirograph", 28, "#B1B9FF", .22, 24, fade="To top", scale=1.08, x=25, y=35),
        layer("Perspective fan", 51, "#B4E8FF", .24, 31, fade="To top", y=24),
    ]

    rose = deepcopy(ocean)
    rose.update(name="ローズ・交差グリッド", bg_start="#40263F", bg_end="#AA6078", angle=156)
    rose["top"]["layers"] = [
        layer("Curved grid", 121, "#FFD5C6", .27, 24, fade="To right", scale=1.16, rotation=-9, y=-20),
        layer("Flowing waves", 49, "#F4B6E3", .19, 24, fade="To bottom", rotation=13, x=5, y=-16),
    ]
    rose["bottom"]["layers"] = [
        layer("Hexagon grid", 17, "#EFC9FF", .22, 19, fade="To top", y=23),
        layer("Organic contours", 65, "#FFD6B7", .31, 26, fade="To top", scale=1.55, x=26, y=36),
    ]

    # v0.8: four distinct grayscale tones plus six contrasting palettes.
    # Each preset uses different shapes and/or staggered duplicate layers,
    # rather than merely recoloring the previous eighteen themes.
    light_gray = deepcopy(ocean)
    light_gray.update(name="ライトグレー・細密グリッド", bg_start="#F0F2F4", bg_end="#B6BDC7", angle=134)
    light_gray["top"]["layers"] = [
        layer("Curved grid", 132, "#536679", .34, 24, fade="To right", x=-16, y=-22, rotation=3, scale=1.16),
        layer("Curved grid", 132, "#88939D", .22, 24, fade="To right", x=-9, y=-21, rotation=7, scale=1.16),
    ]
    light_gray["bottom"]["layers"] = [
        layer("Hexagon grid", 84, "#52616C", .26, 18, fade="To top", scale=1.12, y=35),
        layer("Flowing waves", 19, "#76889A", .35, 17, fade="To top", rotation=-10, y=25),
    ]

    silver = deepcopy(ocean)
    silver.update(name="シルバー・流線", bg_start="#B9C7D0", bg_end="#6D8190", angle=159)
    silver["top"]["layers"] = [
        layer("Flowing waves", 138, "#F9FEFF", .68, 27, fade="To right", rotation=12, y=-20, scale=1.20),
        layer("Flowing waves", 138, "#445567", .24, 27, fade="To right", rotation=17, x=7, y=-16, scale=1.20),
    ]
    silver["bottom"]["layers"] = [
        layer("Radiating arcs", 35, "#ECF6FC", .48, 24, fade="To top", x=24, scale=1.35, y=30),
        layer("Dot field", 89, "#F5FFFF", .23, 15, fade="To top", y=21),
    ]

    charcoal = deepcopy(ocean)
    charcoal.update(name="チャコール・軌道", bg_start="#121416", bg_end="#3C434B", angle=150)
    charcoal["top"]["layers"] = [
        layer("Spirograph", 73, "#E6ECF2", .34, 31, fade="To right", x=-26, y=-22, scale=1.24),
        layer("Spirograph", 73, "#748797", .22, 31, fade="To right", x=-20, y=-20, rotation=8, scale=1.24),
    ]
    charcoal["bottom"]["layers"] = [
        layer("Organic contours", 40, "#B6C0C8", .36, 26, fade="To top", x=29, y=33, scale=1.42),
        layer("Perspective fan", 18, "#C3D1D9", .21, 22, fade="To top", rotation=6, y=21),
    ]

    warm_gray = deepcopy(ocean)
    warm_gray.update(name="ウォームグレー・等高線", bg_start="#595451", bg_end="#AEA49A", angle=118)
    warm_gray["top"]["layers"] = [
        layer("Organic contours", 128, "#F7EDE1", .43, 29, fade="To right", x=-31, y=-27, scale=1.49),
        layer("Triangle mesh", 66, "#E4D4C3", .18, 14, fade="To bottom", x=15, rotation=-8),
    ]
    warm_gray["bottom"]["layers"] = [
        layer("Organic contours", 22, "#F7E9D7", .34, 23, fade="To top", rotation=8, y=35, scale=1.34),
        layer("Curved grid", 71, "#E5D0B8", .18, 12, fade="To top", rotation=-6, y=15),
    ]

    yellow = deepcopy(ocean)
    yellow.update(name="イエロー・放射線", bg_start="#625111", bg_end="#DBB938", angle=132)
    yellow["top"]["layers"] = [
        layer("Radiating arcs", 136, "#FFF7BA", .49, 34, fade="To right", x=-23, y=-26, scale=1.55),
        layer("Dot field", 21, "#F9E58F", .24, 22, fade="To bottom", x=6),
    ]
    yellow["bottom"]["layers"] = [
        layer("Perspective fan", 94, "#FFF6C8", .42, 37, fade="To top", rotation=-9, y=22, scale=1.28),
        layer("Flowing waves", 57, "#FFE58C", .23, 18, fade="To top", rotation=5, y=28),
    ]

    orange = deepcopy(ocean)
    orange.update(name="オレンジ・干渉波", bg_start="#792E1D", bg_end="#E38635", angle=157)
    orange["top"]["layers"] = [
        layer("Flowing waves", 127, "#FFDAB4", .39, 33, fade="To right", rotation=-11, x=-14, y=-24),
        layer("Flowing waves", 127, "#FFF0CA", .23, 33, fade="To right", rotation=-6, x=-6, y=-21),
    ]
    orange["bottom"]["layers"] = [
        layer("Curved grid", 97, "#FFE3BE", .27, 25, fade="To top", rotation=6, y=30),
        layer("Hexagon grid", 61, "#FFCC9D", .19, 17, fade="To top", x=21, y=28),
    ]

    red = deepcopy(ocean)
    red.update(name="レッド・三角メッシュ", bg_start="#481720", bg_end="#AD293D", angle=140)
    red["top"]["layers"] = [
        layer("Triangle mesh", 144, "#FFD0D3", .37, 27, fade="To right", x=-22, y=-17, scale=1.17),
        layer("Triangle mesh", 144, "#FF859B", .15, 27, fade="To right", x=-18, y=-15, rotation=5, scale=1.17),
    ]
    red["bottom"]["layers"] = [
        layer("Hexagon grid", 40, "#FFB9BB", .31, 18, fade="To top", y=28, rotation=7),
        layer("Flowing waves", 30, "#FDD4DE", .21, 23, fade="To top", rotation=-12, y=33),
    ]

    lime = deepcopy(ocean)
    lime.update(name="ライム・交差グリッド", bg_start="#19472C", bg_end="#84B646", angle=144)
    lime["top"]["layers"] = [
        layer("Curved grid", 145, "#DDFF9C", .46, 28, fade="To right", rotation=11, x=-14, y=-22),
        layer("Hexagon grid", 83, "#A9EB87", .22, 16, fade="To bottom", y=-5, scale=1.11),
    ]
    lime["bottom"]["layers"] = [
        layer("Perspective fan", 91, "#E8FFC4", .39, 30, fade="To top", rotation=13, y=25),
        layer("Curved grid", 145, "#BCF48B", .19, 28, fade="To top", rotation=16, x=-7, y=27),
    ]

    sky = deepcopy(ocean)
    sky.update(name="スカイブルー・曲線ストライプ", bg_start="#4B9CCB", bg_end="#B3E1EC", angle=128)
    sky["top"]["layers"] = [
        layer("Flowing waves", 147, "#FFFFFF", .60, 34, fade="To right", rotation=-10, x=-9, y=-19),
        layer("Radiating arcs", 55, "#DDF8FF", .29, 19, fade="To bottom", x=28, y=-14, scale=1.27),
    ]
    sky["bottom"]["layers"] = [
        layer("Organic contours", 69, "#E3FAFF", .42, 25, fade="To top", y=37, scale=1.42),
        layer("Dot field", 131, "#FFFFFF", .33, 23, fade="To top", x=10, y=22),
    ]

    ivory = deepcopy(ocean)
    ivory.update(name="アイボリー・ドット", bg_start="#FCF5E4", bg_end="#D0C5A8", angle=165)
    ivory["top"]["layers"] = [
        layer("Dot field", 112, "#786C55", .48, 30, fade="To right", y=-20),
        layer("Hexagon grid", 116, "#92826A", .27, 19, fade="To bottom", x=-13, y=-21),
    ]
    ivory["bottom"]["layers"] = [
        layer("Organic contours", 78, "#786A55", .34, 23, fade="To top", y=31, scale=1.40),
        layer("Dot field", 112, "#B69A65", .31, 24, fade="To top", x=8, y=18),
    ]

    themes = (
        ocean, violet, emerald, midnight, dunes, aurora, coral, forest, graphite,
        copper, glacier, orbit, sakura, electric, sandstone, interference, cobalt, rose,
        light_gray, silver, charcoal, warm_gray, yellow, orange, red, lime, sky, ivory,
    )
    try:
        from .more_presets import additional_presets
    except ImportError:
        from more_presets import additional_presets
    presets = {theme["name"]: theme for theme in themes}
    presets.update(additional_presets(ocean))
    return _upgrade_presets(presets)




# v0.13: expanded pattern family and automatic perspective styling.
EXTRA_THEME_KINDS = [
    "Diagonal stripes", "Concentric rings", "Ribbon bands",
    "Diamond lattice", "Chevron field", "Sunburst rays",
    "Nested rectangles", "Orbit ellipses", "Arc lattice",
]


def _apply_trapezoid_signature(layer: dict[str, Any], *, side: str, theme_index: int, layer_index: int) -> dict[str, Any]:
    out = dict(layer)
    if side == "top":
        out["warp_top"] = 56 + ((theme_index * 7 + layer_index * 9) % 24)
        out["warp_bottom"] = 118 + ((theme_index * 5 + layer_index * 7) % 24)
        out["warp_top_shift"] = -18 + ((theme_index * 5 + layer_index * 11) % 22)
        out["warp_bottom_shift"] = -10 + ((theme_index * 9 + layer_index * 7) % 20)
    else:
        out["warp_top"] = 62 + ((theme_index * 6 + layer_index * 7) % 28)
        out["warp_bottom"] = 120 + ((theme_index * 8 + layer_index * 5) % 26)
        out["warp_top_shift"] = -14 + ((theme_index * 4 + layer_index * 9) % 18)
        out["warp_bottom_shift"] = -8 + ((theme_index * 6 + layer_index * 13) % 16)
    # Strengthen the perspective a little for line-driven families.
    if out.get("kind") in {"Flowing waves", "Curved grid", "Perspective fan", "Ribbon bands", "Arc lattice", "Diagonal stripes"}:
        out["warp_top"] = max(42, int(out["warp_top"] * 0.92))
        out["warp_bottom"] = min(160, int(out["warp_bottom"] * 1.05))
    return out


def _refresh_theme(theme: dict[str, Any], idx: int) -> dict[str, Any]:
    cfg = deepcopy(theme)
    cfg["top"]["vertical_feather"] = 30
    cfg["bottom"]["vertical_feather"] = 32
    cfg["top"]["edge_feather"] = 0
    cfg["bottom"]["edge_feather"] = 0
    # Vary the strip heights slightly so the new pattern families have room.
    cfg["top"]["height"] = 460 + (idx % 3) * 20
    cfg["bottom"]["height"] = 430 + ((idx + 1) % 3) * 24
    for side in ("top", "bottom"):
        layers = cfg[side].get("layers", [])
        for li, layer in enumerate(layers):
            # Reconsider the pattern family: every theme receives at least one
            # of the new pattern kinds, often two, while preserving its palette.
            if li == 1 or (li == 0 and idx % 5 == (0 if side == "top" else 2)):
                layer["kind"] = EXTRA_THEME_KINDS[(idx * 2 + li + (0 if side == "top" else 3)) % len(EXTRA_THEME_KINDS)]
                layer["density"] = max(14, int(layer.get("density", 20)) + (idx + li) % 8)
                layer["scale"] = round(float(layer.get("scale", 1.0)) * (1.06 + ((idx + li) % 3) * 0.04), 3)
                layer["rotation"] = int(layer.get("rotation", 0)) + ((idx * 9 + li * 13) % 24 - 12)
            else:
                layer["density"] = min(55, max(10, int(layer.get("density", 20)) + (idx + li) % 4))
                layer["scale"] = round(float(layer.get("scale", 1.0)) * (1.03 + ((idx + li) % 2) * 0.03), 3)
            if li == 0:
                layer["blend"] = "screen"
            elif idx % 4 == 0:
                layer["blend"] = "overlay"
            layer.update(_apply_trapezoid_signature(layer, side=side, theme_index=idx, layer_index=li))
    return cfg


def _upgrade_presets(presets: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    upgraded: dict[str, dict[str, Any]] = {}
    echo_indices = {11, 19, 27, 35, 43, 51}
    for idx, name in enumerate(list(presets.keys())):
        cfg = _refresh_theme(presets[name], idx)
        if idx in echo_indices:
            side = "bottom" if idx % 2 else "top"
            layers = cfg[side].get("layers", [])
            if len(layers) >= 2:
                src = dict(layers[0])
                layers[1].update({
                    "kind": src["kind"],
                    "seed": src["seed"],
                    "x": int(src.get("x", 0)) + 8,
                    "y": int(src.get("y", 0)) + 4,
                    "rotation": int(src.get("rotation", 0)) + 6,
                    "opacity": round(max(0.12, float(src.get("opacity", 0.3)) * 0.72), 3),
                    "scale": round(float(src.get("scale", 1.0)) * 1.03, 3),
                    "blend": "overlay",
                })
                layers[1].update(_apply_trapezoid_signature(layers[1], side=side, theme_index=idx, layer_index=1))
        upgraded[name] = cfg
    return upgraded

def suggested_text_color(config: dict[str, Any]) -> str:
    """Readable preview text for pale and dark gradients (based on top color)."""
    color = config["bg_start"].lstrip("#")
    rgb = [int(color[i:i+2], 16) / 255 for i in (0, 2, 4)]
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
    luminance = sum(v * w for v, w in zip(linear, (.2126, .7152, .0722)))
    return "#172333" if luminance > .43 else "#F8FBFF"


def _validate(config: dict[str, Any]) -> None:
    for key in ("bg_start", "bg_end"):
        if not COLOR_RE.fullmatch(config[key]):
            raise ValueError(f"Invalid color in {key}")
    if not 0 <= config["angle"] <= 360:
        raise ValueError("Gradient angle must be between 0 and 360")
    for side in ("top", "bottom"):
        item = config[side]
        if not 200 <= item["width"] <= 6000 or not 200 <= item["height"] <= 6000:
            raise ValueError(f"Invalid dimensions for {side}")
        if item["align"] not in ALIGNMENTS or item["size_unit"] not in ("px", "%"):
            raise ValueError(f"Invalid placement for {side}")
        if item["size_unit"] == "px" and not 100 <= item["size"] <= 4000:
            raise ValueError(f"Invalid pixel size for {side}")
        if item["size_unit"] == "%" and not 10 <= item["size"] <= 250:
            raise ValueError(f"Invalid percentage size for {side}")
        if not 0 <= item["inset"] <= 500:
            raise ValueError(f"Invalid inset for {side}")
        if item.get("anchor_y", side) not in ("top", "center", "bottom"):
            raise ValueError(f"Invalid vertical anchor for {side}")
        if not -500 <= item.get("shift_x", 0) <= 500:
            raise ValueError(f"Invalid horizontal shift for {side}")
        if not 0 <= item.get("edge_feather", 0) <= 40:
            raise ValueError(f"Invalid edge feather for {side}")
        if not 0 <= item.get("vertical_feather", 28) <= 50:
            raise ValueError(f"Invalid vertical feather for {side}")
        if len(item["layers"]) > 6:
            raise ValueError(f"Too many layers for {side}")


def web_svgs(config: dict[str, Any]) -> dict[str, str]:
    """Return independent transparent SVGs with different native dimensions."""
    _validate(config)
    return {
        f"{side}.svg": render_svg(
            config[side]["width"], config[side]["height"],
            config[side]["layers"], transparent=True,
            # Edge blending happens in CSS *after* background-size cropping.
            # Fading inside the SVG gets cropped at 115%, creating new hard ends.
            edge_feather=0, seamless=True,
            vertical_anchor=config[side].get("anchor_y", side),
            vertical_feather=int(config[side].get("vertical_feather", 28)),
        )
        for side in ("top", "bottom")
    }


def web_css(
    config: dict[str, Any],
    *,
    urls: dict[str, str] | None = None,
    selector: str = ".page-background",
) -> str:
    """Export/preview CSS generator, preserving the same layer positions and sizes.

    Note: URLs must be generated internally or otherwise trusted; they are CSS URL tokens.
    """
    _validate(config)
    if urls is None:
        urls = {"top": "/themes/top.svg", "bottom": "/themes/bottom.svg"}
    # The color gradient is the element background; two independent pseudo-
    # elements carry decoration masks. This ensures the feather is based on
    # *actual page width* after 115% scaling, rather than on the SVG source.
    rules = [f"""{selector} {{
  position: relative;
  isolation: isolate;
  min-height: 100vh;
  background: linear-gradient({config['angle']}deg, {config['bg_start']}, {config['bg_end']});
}}"""]
    for side, pseudo in (("top", "before"), ("bottom", "after")):
        item = config[side]
        if not item["enabled"]:
            rules.append(f"{selector}::{pseudo} {{ content: none; }}")
            continue
        anchor = item.get("anchor_y", side)
        inset = item["inset"]
        y = (
            f'{inset}px' if anchor == "top"
            else f'calc(50% + {inset}px)' if anchor == "center"
            else f'calc(100% - {inset}px)'
        )
        shift = item.get("shift_x", 0)
        x = ALIGNMENTS[item["align"]]
        if shift > 0:
            x = f'calc({x} + {shift}px)'
        elif shift < 0:
            x = f'calc({x} - {abs(shift)}px)'
        feather = int(item.get("edge_feather", 0))
        mask = (
            f"linear-gradient(to right, transparent 0%, #000 {feather}%, "
            f"#000 {100-feather}%, transparent 100%)"
            if feather else "none"
        )
        rules.append(f"""{selector}::{pseudo} {{
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  background-image: url("{urls[side]}");
  background-position: {x} {y};
  background-size: {item['size']}{item['size_unit']} auto;
  background-repeat: no-repeat;
  -webkit-mask-image: {mask};
  mask-image: {mask};
}}""")
    return "\n".join(rules) + "\n"



def _embedded_svg_urls(images: dict[str, str]) -> dict[str, str]:
    """Make a standalone preview work without a local server or asset paths."""
    return {
        side: "data:image/svg+xml;base64," + base64.b64encode(
            images[f"{side}.svg"].encode("utf-8")
        ).decode("ascii")
        for side in ("top", "bottom")
    }


def standalone_preview_html(
    config: dict[str, Any], *,
    urls: dict[str, str] | None = None,
    initial_height: int = 1600,
) -> str:
    """The actual export preview.html, with optional embedded SVG asset URLs.

    `urls=None` creates the portable ZIP version with sibling top.svg / bottom.svg.
    Data URLs create an independent HTML document suitable for a browser Blob tab.
    """
    resolved_urls = urls if urls is not None else {
        "top": "./top.svg", "bottom": "./bottom.svg",
    }
    if not 400 <= initial_height <= 6000:
        raise ValueError("Invalid standalone preview height")
    css = web_css(config, urls=resolved_urls)
    name = escape(str(config["name"]))
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>preview.html — {name}</title>
<style>html,body {{ margin:0; font-family:system-ui,sans-serif; }}
{css}
.demo {{ min-height:{initial_height}px; padding:40px 6%; box-sizing:border-box;
  color:{suggested_text_color(config)}; }}
.controls {{ position:fixed; z-index:10; bottom:12px; right:12px; padding:10px 14px;
background:#16203bcc; color:white; border-radius:12px; }}
.controls input {{ width:100px; }}
</style></head><body>
<div class="page-background demo" id="page"><h1>{name}</h1>
<p>上部・下部の透明SVGをCSSグラデーションと合成しています。</p></div>
<div class="controls"><label>ページ高さ (px): <input type="number" min="400" max="6000"
value="{initial_height}" id="height"></label></div>
<script>const field=document.getElementById('height');
field.oninput=()=>{{const v=Number(field.value);if(v>=400&&v<=6000)
document.getElementById('page').style.minHeight=v+'px';}};</script></body></html>"""


def web_preview_html(
    config: dict[str, Any], *, viewport_width: int = 1280,
    page_height: int = 1500, fit: str = "whole",
) -> str:
    """Live iframe: click the page to open current standalone preview in a new tab.

    The new tab uses a self-contained HTML Blob with inline SVG data URLs.
    No server-side files, temporary local paths, or downloads are required.
    The ZIP's preview.html is built by the same standalone_preview_html function.
    """
    if not (320 <= viewport_width <= 2500 and 400 <= page_height <= 6000):
        raise ValueError("Invalid preview dimensions")
    if fit not in ("whole", "width"):
        raise ValueError("Invalid preview fit")
    images = web_svgs(config)
    urls = _embedded_svg_urls(images)
    css = web_css(config, urls=urls)
    # Keep every byte of the HTML isolated from the outer iframe script. In
    # particular, a literal </script> inside a JS string would close the script.
    standalone = standalone_preview_html(config, urls=urls, initial_height=page_height)
    encoded_standalone = base64.b64encode(standalone.encode("utf-8")).decode("ascii")
    return f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
* {{ box-sizing: border-box; }}
html, body {{ padding:0; margin:0; font-family:system-ui,sans-serif; }}
body {{ background:#EDF0F5; }}
.stage {{ width:100%; padding:12px; height:100vh; overflow:auto; text-align:center; }}
.open-preview {{ display:inline-block; vertical-align:top; color:inherit; text-decoration:none; cursor:zoom-in; }}
.open-preview:focus-visible {{ outline:3px solid #1476e0; outline-offset:3px; }}
.viewport {{ position:relative; margin:0 auto; box-shadow: 0 8px 28px #10162e38; }}
.viewport::after {{ content:"クリックで別タブに表示"; position:absolute; top:12px; right:12px;
  padding:5px 9px; background:#10162ed8; color:#fff; border-radius:6px;
  font:12px system-ui,sans-serif; opacity:0; pointer-events:none; transition:opacity .14s; }}
.open-preview:hover .viewport::after, .open-preview:focus-visible .viewport::after {{ opacity:1; }}
.page-background {{ width:{viewport_width}px; height:{page_height}px; overflow:hidden; text-align:left;
  transform-origin:top left; color:{suggested_text_color(config)}; }}
{css}
.preview-copy {{ padding:40px 6%; }}
.preview-copy h1 {{ margin:0 0 12px; font-size:28px; line-height:1.25; }}
.preview-copy p {{ margin:0; font-size:14px; opacity:.85; }}
</style></head>
<body><div class="stage" id="stage">
<a class="open-preview" id="openPreview" target="_blank" rel="noopener"
   aria-label="現在の設定をpreview.htmlとして別タブに開く">
<div class="viewport" id="frame">
<div class="page-background" id="page"><div class="preview-copy">
<h1>Web background preview</h1><p>{viewport_width} × {page_height}px — 上部と下部のSVGを独立配置</p>
</div></div></div></a></div>
<script>
const stage = document.getElementById('stage');
const frame = document.getElementById('frame');
const page = document.getElementById('page');
const pageWidth = {viewport_width};
const pageHeight = {page_height};
function resizePreview() {{
  const maxWidth = Math.max(100, stage.clientWidth - 28);
  const scale = {('Math.min(1, maxWidth / pageWidth, Math.max(100, stage.clientHeight - 32) / pageHeight)' if fit == 'whole' else 'Math.min(1, maxWidth / pageWidth)')};
  page.style.transform = `scale(${{scale}})`;
  frame.style.width = (pageWidth * scale) + 'px';
  frame.style.height = (pageHeight * scale) + 'px';
}}
resizePreview();
window.addEventListener('resize', resizePreview);
new ResizeObserver(resizePreview).observe(stage);
// Base64 isolates the standalone HTML from the outer script and preserves Unicode.
const standaloneBase64 = '{encoded_standalone}';
const bytes = Uint8Array.from(atob(standaloneBase64), c => c.charCodeAt(0));
const previewHtml = new TextDecoder('utf-8').decode(bytes);
const previewUrl = URL.createObjectURL(new Blob([previewHtml], {{type:'text/html;charset=utf-8'}}));
document.getElementById('openPreview').href = previewUrl;
window.addEventListener('pagehide', () => URL.revokeObjectURL(previewUrl), {{once:true}});
</script></body></html>"""


def make_web_pack(config: dict[str, Any]) -> bytes:
    images = web_svgs(config)
    css = web_css(config)
    manifest = deepcopy(config)
    manifest["format"] = "svg-pattern-studio-web-v3"
    manifest["suggested_text_color"] = suggested_text_color(config)
    manifest["files"] = {"top": "top.svg", "bottom": "bottom.svg", "css": "example.css"}
    # Same HTML template as the click-to-open preview, but relative asset URLs
    # so the exported ZIP stays small and can be opened entirely offline.
    html = standalone_preview_html(config)
    b = io.BytesIO()
    with zipfile.ZipFile(b, "w", zipfile.ZIP_DEFLATED) as z:
        for filename, svg in images.items():
            z.writestr(filename, svg)
        z.writestr("example.css", css)
        z.writestr("preview.html", html)
        z.writestr("theme.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        z.writestr("README.txt", "Copy top.svg and bottom.svg to React public/themes/.\n"
                                    "Copy all .page-background rules from example.css, including ::before/::after.\n"
                                    "preview.html can be opened directly in a browser.\n")
    return b.getvalue()
