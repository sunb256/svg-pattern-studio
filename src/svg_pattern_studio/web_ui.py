"""Streamlit UI for composing browser-page backgrounds."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
import random

import streamlit as st
import streamlit.components.v1 as components

try:
    from .generator import FADES, KINDS, default_layer
    from .layer_tools import copy_layer, duplicate_layer, nudge_layer, layer_difference, layer_warp_difference
    from .warp_presets import WARP_PRESETS, apply_warp_preset, warp_preset_name
    from .preset_tools import apply_web_preset
    from .composition import (PATTERN_SETS, DEFAULT_PATTERN, palette_catalog,
                              apply_composition)
    from .web_background import default_web_theme, make_web_pack, web_css, web_preview_html, web_presets, web_svgs
except ImportError:
    from generator import FADES, KINDS, default_layer
    from layer_tools import copy_layer, duplicate_layer, nudge_layer, layer_difference, layer_warp_difference
    from warp_presets import WARP_PRESETS, apply_warp_preset, warp_preset_name
    from preset_tools import apply_web_preset
    from composition import (PATTERN_SETS, DEFAULT_PATTERN, palette_catalog,
                             apply_composition)
    from web_background import default_web_theme, make_web_pack, web_css, web_preview_html, web_presets, web_svgs

PATTERN_NAMES = {
    "Flowing waves": "流れる波線", "Curved grid": "曲線グリッド",
    "Organic contours": "等高線", "Triangle mesh": "三角形メッシュ",
    "Radiating arcs": "放射状の円弧", "Spirograph": "スピログラフ",
    "Perspective fan": "交差する扇状曲線", "Hexagon grid": "六角形グリッド",
    "Dot field": "ドット",
    "Diagonal stripes": "斜めストライプ", "Concentric rings": "同心リング",
    "Ribbon bands": "リボン束", "Diamond lattice": "ひし形格子",
    "Chevron field": "シェブロン", "Sunburst rays": "サンバースト",
    "Nested rectangles": "入れ子長方形", "Orbit ellipses": "軌道楕円",
    "Arc lattice": "円弧ラティス", "None": "なし", "To right": "右方向に消える",
    "To left": "左方向に消える", "To bottom": "下方向に消える",
    "To top": "上方向に消える", "Center focus": "周辺に消える",
}
BLEND_NAMES = {"normal": "通常", "screen": "スクリーン", "multiply": "乗算", "overlay": "オーバーレイ"}

POSITIONS = [
    ("left", "top"), ("center", "top"), ("right", "top"),
    ("left", "center"), ("center", "center"), ("right", "center"),
    ("left", "bottom"), ("center", "bottom"), ("right", "bottom"),
]
POSITION_LABELS = ["左上", "上中央", "右上", "中央左", "中央", "中央右", "左下", "下中央", "右下"]


def _place_layer(side: str, index: int, x: int, y: int) -> None:
    """Move the chosen pattern's center to a 3x3 canvas anchor."""
    conf = deepcopy(st.session_state.web_config)
    conf[side]["layers"][index]["x"] = x
    conf[side]["layers"][index]["y"] = y
    st.session_state.web_config = conf
    st.session_state.web_rev += 1


def _on_preset_change() -> None:
    """Streamlit runs on_change before rebuilding widget trees on a rerun.

    Replacing the entire theme here means the preview + sidebar editors get
    the same new configuration immediately, without a separate apply button.
    """
    apply_web_preset(st.session_state, st.session_state["web-selected-preset"])
    st.session_state["web-selection-mode"] = "legacy"


# A tiny self-contained Streamlit component: clicking the thumbnail itself
# sends an event back to Python. Thumbnails are shipped as static assets,
# so browsing the catalogue does not trigger 56 SVG renders on every rerun.
GALLERY_DIR = Path(__file__).resolve().parent / "assets" / "preset-gallery"
selectable_gallery = components.declare_component(
    "svg_pattern_selectable_gallery_v09", path=str(GALLERY_DIR)
)


def _render_theme_gallery(presets: dict) -> None:
    """Render clickable thumbnails and synchronize selection with the sidebar."""
    with st.expander(f"{len(presets)}種類の背景デザインを一覧表示・クリックして選択", expanded=False):
        selected = st.session_state.get("web-selected-preset", next(iter(presets)))
        entries = json.loads((GALLERY_DIR / "catalog.json").read_text(encoding="utf-8"))
        click = selectable_gallery(
            items=entries, selected=selected, default=None,
            key="web-theme-gallery", height=435,
        )
        if isinstance(click, dict):
            name = click.get("name")
            event_id = click.get("event_id")
            if (name in presets and event_id and
                    event_id != st.session_state.get("web-gallery-last-event")):
                st.session_state["web-gallery-last-event"] = event_id
                st.session_state["web-selected-preset"] = name
                apply_web_preset(st.session_state, name)
                st.session_state["web-selection-mode"] = "legacy"
                st.rerun()
        st.caption("以前のサンプルを読み込むと、そのデザインで編集できます。新しい3カラム選択を変更すると、組み合わせ式のデザインに切り替わります。")


def _on_warp_preset_change(side: str, index: int, key: str) -> None:
    name = st.session_state[key]
    if name == "自由調整":
        return
    conf = deepcopy(st.session_state.web_config)
    conf[side]["layers"][index] = apply_warp_preset(conf[side]["layers"][index], name)
    st.session_state.web_config = conf
    st.session_state.web_focus = (side, index)
    st.session_state.web_rev += 1


def _init() -> None:
    if "web_config" not in st.session_state:
        st.session_state.web_config = default_web_theme()
    if "web_rev" not in st.session_state:
        st.session_state.web_rev = 0
    if "web_focus" not in st.session_state:
        st.session_state.web_focus = None




def _init_quick_composition() -> None:
    """Seed independent controls exactly once per Streamlit session."""
    palettes = palette_catalog()
    if "web-compose-palette" not in st.session_state:
        st.session_state["web-compose-palette"] = next(iter(palettes))
    if "web-compose-pattern" not in st.session_state:
        st.session_state["web-compose-pattern"] = DEFAULT_PATTERN
    if "web-selection-mode" not in st.session_state:
        _apply_palette_and_pattern(reset_gradient=True)


def _apply_palette_and_pattern(*, reset_gradient: bool) -> None:
    apply_composition(
        st.session_state,
        palette_name=st.session_state["web-compose-palette"],
        pattern_name=st.session_state["web-compose-pattern"],
    )
    st.session_state["web-selection-mode"] = "compose"
    if not reset_gradient:
        return
    palette = palette_catalog()[st.session_state["web-compose-palette"]]
    conf = deepcopy(st.session_state.web_config)
    conf["bg_start"] = palette["bg_start"]
    conf["bg_end"] = palette["bg_end"]
    conf["angle"] = palette["angle"]
    st.session_state.web_config = conf


def _on_palette_change() -> None:
    _apply_palette_and_pattern(reset_gradient=True)


def _on_pattern_change() -> None:
    current = deepcopy(st.session_state.web_config)
    start = current.get("bg_start")
    end = current.get("bg_end")
    angle = current.get("angle")
    _apply_palette_and_pattern(reset_gradient=False)
    conf = deepcopy(st.session_state.web_config)
    conf["bg_start"] = start
    conf["bg_end"] = end
    conf["angle"] = angle
    st.session_state.web_config = conf


def _on_gradient_quick_change() -> None:
    conf = deepcopy(st.session_state.web_config)
    conf["bg_start"] = st.session_state["web-compose-bg-start"]
    conf["bg_end"] = st.session_state["web-compose-bg-end"]
    conf["angle"] = int(st.session_state["web-compose-angle"])
    st.session_state.web_config = conf
    st.session_state.web_rev += 1


def _sync_quick_gradient_from_config() -> None:
    st.session_state["web-compose-bg-start"] = st.session_state.web_config.get("bg_start", "#14246B")
    st.session_state["web-compose-bg-end"] = st.session_state.web_config.get("bg_end", "#206CA8")
    st.session_state["web-compose-angle"] = int(st.session_state.web_config.get("angle", 145))


def _step_composition(key: str, names: list[str], delta: int, mode: str) -> None:
    current = st.session_state[key]
    st.session_state[key] = names[(names.index(current) + delta) % len(names)]
    if mode == "palette":
        _on_palette_change()
    else:
        _on_pattern_change()




def _randomize_composition() -> None:
    palettes = list(palette_catalog())
    patterns = list(PATTERN_SETS)
    current = (st.session_state.get("web-compose-palette"), st.session_state.get("web-compose-pattern"))
    # Try several times to avoid repeating the same combination.
    for _ in range(12):
        palette = random.choice(palettes)
        pattern = random.choice(patterns)
        if (palette, pattern) != current:
            break
    st.session_state["web-compose-palette"] = palette
    st.session_state["web-compose-pattern"] = pattern
    _apply_palette_and_pattern(reset_gradient=True)

def _render_quick_composition() -> None:
    """Three selectors: palette, pattern set, and gradient fine tuning."""
    palettes = palette_catalog()
    _sync_quick_gradient_from_config()
    left, center, right = st.columns([1, 1.15, 1], gap="medium")
    with left:
        st.markdown("**色合い**")
        chosen = st.selectbox(
            "色合いを選択", list(palettes), key="web-compose-palette",
            on_change=_on_palette_change,
            label_visibility="collapsed",
        )
        palette = palettes[chosen]
        start, end = palette["bg_start"], palette["bg_end"]
        st.markdown(
            f'<div role="img" aria-label="{chosen}の配色" style="height:38px;'
            f'border-radius:8px;border:1px solid #8885;'
            f'background:linear-gradient(120deg,{start},{end})"></div>',
            unsafe_allow_html=True,
        )
        prev, nex = st.columns(2)
        prev.button("◀ 前の色", key="compose-prev-palette", use_container_width=True,
                    on_click=_step_composition, args=("web-compose-palette", list(palettes), -1, "palette"))
        nex.button("次の色 ▶", key="compose-next-palette", use_container_width=True,
                   on_click=_step_composition, args=("web-compose-palette", list(palettes), 1, "palette"))
    with center:
        st.markdown("**パターンセット**")
        selected = st.selectbox(
            "パターンセットを選択", list(PATTERN_SETS), key="web-compose-pattern",
            on_change=_on_pattern_change,
            label_visibility="collapsed",
        )
        top_kind, top_count = PATTERN_SETS[selected]["top"]
        bottom_kind, bottom_count = PATTERN_SETS[selected]["bottom"]
        top_label = PATTERN_NAMES[top_kind] + (" ×2" if top_count == 2 else "")
        bottom_label = PATTERN_NAMES[bottom_kind] + (" ×2" if bottom_count == 2 else "")
        st.caption(f"上：{top_label}")
        st.caption(f"下：{bottom_label}")
        prev, nex = st.columns(2)
        prev.button("◀ 前の模様", key="compose-prev-pattern", use_container_width=True,
                    on_click=_step_composition, args=("web-compose-pattern", list(PATTERN_SETS), -1, "pattern"))
        nex.button("次の模様 ▶", key="compose-next-pattern", use_container_width=True,
                   on_click=_step_composition, args=("web-compose-pattern", list(PATTERN_SETS), 1, "pattern"))
    with right:
        st.markdown("**グラデーション調整**")
        c1, c2 = st.columns(2)
        c1.color_picker("開始色", key="web-compose-bg-start", label_visibility="collapsed", on_change=_on_gradient_quick_change)
        c2.color_picker("終了色", key="web-compose-bg-end", label_visibility="collapsed", on_change=_on_gradient_quick_change)
        st.slider("角度", 0, 360, key="web-compose-angle", step=5, on_change=_on_gradient_quick_change)
        r1, r2 = st.columns(2)
        if r1.button("色を入れ替え", key="compose-swap-gradient", use_container_width=True):
            start = st.session_state["web-compose-bg-start"]
            end = st.session_state["web-compose-bg-end"]
            st.session_state["web-compose-bg-start"] = end
            st.session_state["web-compose-bg-end"] = start
            _on_gradient_quick_change()
            st.rerun()
        if r2.button("配色に戻す", key="compose-reset-gradient", use_container_width=True):
            palette = palettes[st.session_state["web-compose-palette"]]
            st.session_state["web-compose-bg-start"] = palette["bg_start"]
            st.session_state["web-compose-bg-end"] = palette["bg_end"]
            st.session_state["web-compose-angle"] = int(palette["angle"])
            _on_gradient_quick_change()
            st.rerun()
        st.button("ランダム", key="compose-random", use_container_width=True, on_click=_randomize_composition,
                  help="色合いとパターンセットの組み合わせをランダムに切り替えます。")
    if st.session_state.get("web-selection-mode") == "legacy":
        st.caption("以前のデザイン例を編集中です。上の選択肢を変更すると、新しい組み合わせ式のデザインへ切り替わります。")

def _change_zone(side: str, op: str, index: int = -1, *, target: int = -1,
                 dx: int = 0, dy: int = 0, drotation: int = 0) -> None:
    """Apply an atomic layer operation, invalidating Streamlit widget keys.

    Keeping the seed when duplicating makes the underlying lines match exactly;
    the new copy can then be moved/rotated without regenerating the pattern.
    """
    conf = deepcopy(st.session_state.web_config)
    arr = conf[side]["layers"]
    focus = None
    if op == "add" and len(arr) < 6:
        arr.append(default_layer("Flowing waves" if side == "bottom" else "Triangle mesh", 73 + len(arr) * 7))
        focus = len(arr) - 1
    elif op == "duplicate" and len(arr) < 6:
        conf[side]["layers"] = duplicate_layer(arr, index)
        focus = index + 1
    elif op == "offset_duplicate" and len(arr) < 6:
        conf[side]["layers"] = duplicate_layer(arr, index, shift_x=8,
                                                  rotation=5, opacity_factor=.8)
        focus = index + 1
    elif op == "copy":
        conf[side]["layers"] = copy_layer(arr, index, target)
        focus = target
    elif op == "nudge":
        conf[side]["layers"] = nudge_layer(arr, index, dx=dx, dy=dy,
                                             drotation=drotation)
        focus = index
    elif op == "remove" and arr:
        arr.pop(index)
    elif op == "up" and index < len(arr) - 1:
        arr[index], arr[index + 1] = arr[index + 1], arr[index]
        focus = index + 1
    elif op == "down" and index > 0:
        arr[index], arr[index - 1] = arr[index - 1], arr[index]
        focus = index - 1
    else:
        return
    st.session_state[f"web-undo-{side}"] = deepcopy(st.session_state.web_config[side]["layers"])
    st.session_state.web_config = conf
    st.session_state.web_focus = (side, focus) if focus is not None else None
    st.session_state.web_rev += 1
    st.rerun()


def _undo_zone(side: str) -> None:
    key = f"web-undo-{side}"
    if key not in st.session_state:
        return
    conf = deepcopy(st.session_state.web_config)
    conf[side]["layers"] = st.session_state.pop(key)
    st.session_state.web_config = conf
    st.session_state.web_focus = None
    st.session_state.web_rev += 1
    st.rerun()


def _zone_editor(side: str, zone: dict, revision: int) -> dict:
    title = "上部装飾" if side == "top" else "下部装飾"
    key = f"web-{revision}-{side}"
    st.caption(f"{title} — 透過SVGを独立生成。最大6レイヤーを重ねられます。")
    zone["enabled"] = st.toggle("この装飾を使用する", value=bool(zone["enabled"]), key=f"{key}-enabled")
    st.markdown("**1. ページ内の配置**")
    selected_position = (zone["align"], zone.get("anchor_y", side))
    zone["align"], zone["anchor_y"] = st.selectbox(
        "模様全体をどこに表示するか", POSITIONS,
        index=POSITIONS.index(selected_position),
        format_func=lambda pos: POSITION_LABELS[POSITIONS.index(pos)],
        key=f"{key}-position",
        help="左上・中央・右下などを選ぶだけで配置できます。",
    )
    a, b = st.columns(2)
    zone["shift_x"] = int(a.slider(
        "横方向の微調整 (px)", -500, 500, int(zone.get("shift_x", 0)), 10,
        key=f"{key}-shift-x",
    ))
    zone["inset"] = int(b.slider(
        "縦方向の余白 (px)", 0, 500, int(zone["inset"]), 10,
        key=f"{key}-inset",
        help="上配置なら下方向、下配置なら上方向、中央なら下方向に動きます。",
    ))

    # Web背景では表示幅を画面より少し広い115%に固定します。
    # 固定pxや100%未満は画像の境界がページ内に現れるため、UIから除外します。
    zone["size_unit"], zone["size"] = "%", 115
    st.markdown("**2. フェード**")
    zone["edge_feather"] = st.slider(
        "左右端のフェード (%)", 0, 40, int(zone.get("edge_feather", 0)), 1,
        key=f"{key}-edge-feather",
        help="Webページの左右端を基準に、模様を徐々に透明にします。0%で無効です。",
    )
    zone["vertical_feather"] = st.slider(
        "上下端のフェード (%)", 0, 50,
        int(zone.get("vertical_feather", 28)), 1, key=f"{key}-vertical-feather",
        help="上部装飾は下端、下部装飾は上端を徐々に透明にします。0%で無効です。",
    )

    st.markdown("**3. 模様のレイヤー**")

    a, b = st.columns([1, 2], vertical_alignment="center")
    if a.button("＋ レイヤー追加", key=f"{key}-add", disabled=len(zone["layers"])>=6):
        _change_zone(side, "add")
    b.caption("下のレイヤーから順に合成されます。")
    with st.expander("レイヤー間でコピー（例: 1 → 2）", expanded=False):
        st.caption("コピー元を既存レイヤーへ上書きします。元の模様・ランダム値・色・位置まで同じになります。")
        if len(zone["layers"]) >= 2:
            c1, c2 = st.columns(2)
            source = c1.selectbox("コピー元", range(len(zone["layers"])),
                                   format_func=lambda i: f"レイヤー {i+1}",
                                   key=f"{key}-copy-source")
            targets = [i for i in range(len(zone["layers"])) if i != source]
            target = c2.selectbox("コピー先（上書き）", targets,
                                   format_func=lambda i: f"レイヤー {i+1}",
                                   key=f"{key}-copy-target")
            if st.button(f"{source+1} → {target+1} にコピー", key=f"{key}-copy-button",
                         use_container_width=True):
                _change_zone(side, "copy", source, target=target)
        else:
            st.caption("コピー先が必要です。先にレイヤーを追加してください。")
    if st.button("↶ 直前のレイヤー操作を取り消す", key=f"{key}-undo",
                 disabled=f"web-undo-{side}" not in st.session_state,
                 use_container_width=True):
        _undo_zone(side)
    edited = []
    for i, layer in enumerate(zone["layers"]):
        lk = f"{key}-layer-{i}"
        label = PATTERN_NAMES.get(layer["kind"], layer["kind"])
        focus = st.session_state.web_focus
        expanded = (focus == (side, i)) if focus is not None and focus[0] == side else i == 0
        with st.expander(f"{i+1}. {label}", expanded=expanded):
            layer = deepcopy(layer)
            layer["enabled"] = st.checkbox("表示", value=bool(layer.get("enabled", True)), key=f"{lk}-enabled")
            layer["kind"] = st.selectbox("模様の種類", KINDS, index=KINDS.index(layer["kind"]),
                                         format_func=lambda x: PATTERN_NAMES[x], key=f"{lk}-kind")
            a, b = st.columns(2)
            layer["color"] = a.color_picker("線の色", value=layer["color"], key=f"{lk}-color")
            layer["blend"] = b.selectbox("交差・合成", list(BLEND_NAMES),
                                    index=list(BLEND_NAMES).index(layer.get("blend", "normal")),
                                    format_func=lambda x: BLEND_NAMES[x], key=f"{lk}-blend")
            a, b = st.columns(2)
            layer["opacity"] = a.slider("濃さ (%)", 0, 100, int(float(layer["opacity"])*100), 1,
                                         key=f"{lk}-opacity") / 100
            layer["density"] = b.slider("線・図形の数", 5, 55, int(layer["density"]), 1,
                                          key=f"{lk}-density")
            a, b = st.columns(2)
            layer["width"] = a.slider("線幅", .3, 4.0, float(layer["width"]), .05, key=f"{lk}-width")
            layer["scale"] = b.slider("拡大率 (%)", 30, 200, int(float(layer["scale"])*100), 1,
                                       key=f"{lk}-scale") / 100
            with st.popover("模様を9方向から配置", use_container_width=True):
                st.caption("この模様を左右上下にワンクリックで移動します。続けて下のスライダーで微調整できます。")
                labels = (("↖ 左上", "↑ 上", "↗ 右上"),
                          ("← 左", "● 中央", "→ 右"),
                          ("↙ 左下", "↓ 下", "↘ 右下"))
                for row_index in range(3):
                    cols = st.columns(3)
                    for col_index in range(3):
                        cols[col_index].button(
                            labels[row_index][col_index],
                            key=f"{lk}-pos-{row_index}-{col_index}",
                            on_click=_place_layer,
                            args=(side, i, (col_index - 1) * 40, (row_index - 1) * 40),
                            use_container_width=True,
                        )
            a, b = st.columns(2)
            layer["x"] = a.slider("左右移動 (%)", -100, 100, int(layer["x"]), 1, key=f"{lk}-x")
            layer["y"] = b.slider("上下移動 (%)", -100, 100, int(layer["y"]), 1, key=f"{lk}-y")
            layer["rotation"] = st.slider("回転角度", -180, 180, int(layer["rotation"]), 1,
                                           key=f"{lk}-rotation")
            with st.popover("台形変形・傾き（遠近感）", use_container_width=True):
                st.caption("形を選ぶだけでも変形できます。複製レイヤーごとに違う角度を指定できます。")
                shape_names = list(WARP_PRESETS) + ["自由調整"]
                st.selectbox("変形パターン", shape_names,
                             index=shape_names.index(warp_preset_name(layer)),
                             key=f"{lk}-warp-shape", on_change=_on_warp_preset_change,
                             args=(side, i, f"{lk}-warp-shape"))
                cc1, cc2 = st.columns(2)
                layer["warp_top"] = cc1.slider("上辺の幅 (%)", 40, 160, int(layer.get("warp_top", 100)), 2, key=f"{lk}-warp-top")
                layer["warp_bottom"] = cc2.slider("下辺の幅 (%)", 40, 160, int(layer.get("warp_bottom", 100)), 2, key=f"{lk}-warp-bottom")
                cc3, cc4 = st.columns(2)
                layer["warp_top_shift"] = cc3.slider("上辺の横ずれ (%)", -50, 50, int(layer.get("warp_top_shift", 0)), 1, key=f"{lk}-warp-top-shift")
                layer["warp_bottom_shift"] = cc4.slider("下辺の横ずれ (%)", -50, 50, int(layer.get("warp_bottom_shift", 0)), 1, key=f"{lk}-warp-bottom-shift")
                st.caption("例：上辺70%・下辺130%で下に広がる台形。複製後に差をつけると立体的な交差模様になります。")
            layer["fade"] = st.selectbox("消え方", FADES, index=FADES.index(layer["fade"]),
                                         format_func=lambda x: PATTERN_NAMES[x], key=f"{lk}-fade")
            layer["seed"] = int(st.number_input("ランダム値 (seed)", 0, 99999,
                                                 int(layer["seed"]), 1, key=f"{lk}-seed"))
            st.markdown("**複製・微調整**")
            a, b = st.columns(2)
            can_duplicate = len(zone["layers"]) < 6
            if a.button("⧉ 完全複製", key=f"{lk}-duplicate", disabled=not can_duplicate,
                        use_container_width=True, help="同じseedで真上に新しいレイヤーを追加"):
                _change_zone(side, "duplicate", i)
            if b.button("⧉ 少しずらして複製", key=f"{lk}-offset-duplicate",
                        disabled=not can_duplicate, use_container_width=True,
                        help="右8%、回転+5°、濃さ80%で複製。seedは維持"):
                _change_zone(side, "offset_duplicate", i)
            with st.popover("矢印と角度で微調整", use_container_width=True):
                st.caption("同じ模様のまま位置や角度だけ調整します。ランダム値は変更しません。")
                step = st.select_slider("移動量 (%)", [1, 2, 3, 5, 10], value=3,
                                        key=f"{lk}-nudge-step")
                turn = st.select_slider("回転量 (°)", [1, 2, 3, 5, 10], value=3,
                                        key=f"{lk}-turn-step")
                north = st.columns([1, 1, 1])
                if north[1].button("↑", key=f"{lk}-nudge-up", use_container_width=True):
                    _change_zone(side, "nudge", i, dy=-step)
                middle = st.columns(3)
                if middle[0].button("←", key=f"{lk}-nudge-left", use_container_width=True):
                    _change_zone(side, "nudge", i, dx=-step)
                if middle[2].button("→", key=f"{lk}-nudge-right", use_container_width=True):
                    _change_zone(side, "nudge", i, dx=step)
                south = st.columns([1, 1, 1])
                if south[1].button("↓", key=f"{lk}-nudge-down", use_container_width=True):
                    _change_zone(side, "nudge", i, dy=step)
                turns = st.columns(2)
                if turns[0].button(f"↶ -{turn}°", key=f"{lk}-turn-left", use_container_width=True):
                    _change_zone(side, "nudge", i, drotation=-turn)
                if turns[1].button(f"↷ +{turn}°", key=f"{lk}-turn-right", use_container_width=True):
                    _change_zone(side, "nudge", i, drotation=turn)
            if len(zone["layers"]) >= 2:
                with st.popover("ほかのレイヤーとの差分を見る", use_container_width=True):
                    peers = [j for j in range(len(zone["layers"])) if j != i]
                    source_i = st.selectbox("比較元", peers,
                                            format_func=lambda j: f"レイヤー {j+1}",
                                            key=f"{lk}-compare")
                    peer = edited[source_i] if source_i < len(edited) else zone["layers"][source_i]
                    diff = layer_difference(peer, layer)
                    st.caption(f"レイヤー{source_i+1} → レイヤー{i+1}")
                    st.write(f"左右 {diff['dx']:+d}% / 上下 {diff['dy']:+d}% / "
                             f"角度 {diff['drotation']:+d}° / 拡大率 {diff['dscale']:+d}%")
                    warp_diff = layer_warp_difference(peer, layer)
                    st.caption(f"台形差：上辺 {warp_diff['dwarp_top']:+d}% / 下辺 {warp_diff['dwarp_bottom']:+d}% / "
                               f"上辺ずれ {warp_diff['dwarp_top_shift']:+d}% / 下辺ずれ {warp_diff['dwarp_bottom_shift']:+d}%")
                    st.caption("同じ形を維持" if diff["same_geometry"] else "模様の種類・seed・密度が異なります")
            a, b, c = st.columns(3)
            if a.button("↑ 手前", key=f"{lk}-up", disabled=i==len(zone["layers"])-1,
                        use_container_width=True):
                _change_zone(side, "up", i)
            if b.button("↓ 奥", key=f"{lk}-down", disabled=i==0, use_container_width=True):
                _change_zone(side, "down", i)
            if c.button("削除", key=f"{lk}-remove", use_container_width=True):
                _change_zone(side, "remove", i)
            edited.append(layer)
    zone["layers"] = edited
    return zone


def render_web_mode() -> None:
    _init()
    _init_quick_composition()
    st.title("SVG Pattern Studio — Web背景モード")
    _render_quick_composition()
    presets = web_presets()
    # Keep the previous 56 clickable designs, without crowding the three-column UI.
    _render_theme_gallery(presets)

    config = deepcopy(st.session_state.web_config)
    revision = st.session_state.web_rev
    with st.sidebar:
        st.subheader("Web背景の設定")
        with st.expander("以前のデザイン例（56種類）", expanded=False):
            st.selectbox(
                "デザイン例", list(presets), key="web-selected-preset",
                on_change=_on_preset_change,
                help="従来のサンプルを読み込みます。現在の調整は置き換わります。",
            )
        if st.button("模様のランダム値を変更", key="web-randomize", use_container_width=True):
            fresh = deepcopy(st.session_state.web_config)
            for side in ("top", "bottom"):
                for layer in fresh[side]["layers"]:
                    layer["seed"] = random.SystemRandom().randint(0, 99999)
            st.session_state.web_config = fresh
            st.session_state.web_rev += 1
            st.rerun()
        config["name"] = st.text_input("テーマ名", config["name"], key=f"web-{revision}-name")
        a, b = st.columns(2)
        config["bg_start"] = a.color_picker("背景色 1", config["bg_start"], key=f"web-{revision}-start")
        config["bg_end"] = b.color_picker("背景色 2", config["bg_end"], key=f"web-{revision}-end")
        config["angle"] = st.slider("グラデーション角度", 0, 360, int(config["angle"]), 5,
                                     key=f"web-{revision}-angle")
        st.divider()
        st.subheader("ページプレビュー")
        viewport = st.selectbox("表示幅", [375, 768, 1280, 1920], index=2,
                                format_func=lambda x: f"{x}px" + ("（スマホ）" if x == 375 else ""),
                                key="web-preview-width")
        height = st.selectbox("ページ高さ", [800, 1400, 2500, 4000], index=1,
                              format_func=lambda x: f"{x}px", key="web-preview-height")
        fit = st.radio("プレビュー表示", ["whole", "width"], horizontal=True,
                        format_func=lambda x: "全体を表示" if x == "whole" else "幅に合わせてスクロール",
                        key="web-preview-fit")
        st.divider()
        st.subheader("作業画面")
        keep_preview = st.toggle(
            "ライブプレビューを固定", value=True, key="web-preview-pinned",
            help="設定欄だけをスクロールし、右側のプレビューを見ながら調整します。",
        )
        work_height = st.select_slider(
            "作業エリアの高さ", options=[480, 560, 640, 720], value=720,
            format_func=lambda n: f"{n}px", key="web-work-area-height",
        ) if keep_preview else 640

    # Avoid document scrolling during editing: only the settings panel scrolls.
    # This is more predictable than making a tall iframe position:fixed.
    edit, preview = st.columns([1, 1.3], gap="large")
    with edit:
        if keep_preview:
            st.caption("設定欄をスクロールしても、右側のプレビューは固定されます。")
            editor_root = st.container(height=work_height - 48, border=True)
        else:
            editor_root = st.container(border=False)
        with editor_root:
            top_tab, bottom_tab = st.tabs(["上部SVG", "下部SVG"])
            with top_tab:
                config["top"] = _zone_editor("top", config["top"], revision)
            with bottom_tab:
                config["bottom"] = _zone_editor("bottom", config["bottom"], revision)

    # Store actual widget state, not just defaults, for subsequent add/delete/reorder operations.
    st.session_state.web_config = deepcopy(config)
    with preview:
        with st.container(border=False):
            html = web_preview_html(config, viewport_width=viewport, page_height=height, fit=fit)
            components.html(html, height=work_height - 75 if keep_preview else 640, scrolling=False)
            st.caption(f"ページ {viewport} × {height}px。プレビューをクリックすると、現在の設定を preview.html として別タブで開きます。")

    # Keep export actions outside the preview column, so it is short enough to
    # remain in the viewport while the user works through the long layer editor.
    with st.expander("SVG・CSSの書き出し", expanded=False):
        svgs = web_svgs(config)
        a, b, c = st.columns(3)
        a.download_button("上部SVGを保存", svgs["top.svg"], "top.svg", "image/svg+xml",
                          key="web-top-download", use_container_width=True)
        b.download_button("下部SVGを保存", svgs["bottom.svg"], "bottom.svg", "image/svg+xml",
                          key="web-bottom-download", use_container_width=True)
        c.download_button("Web背景一式をZIPで保存", make_web_pack(config),
                          file_name="web-background-theme.zip", mime="application/zip",
                          key="web-pack-download", type="primary", use_container_width=True)
        st.caption("ZIP: top.svg / bottom.svg / example.css / theme.json / preview.html")
        with st.expander("React / CSS への組み込み例", expanded=False):
            st.code(web_css(config), language="css")
            st.code('<div className="page-background">{children}</div>', language="tsx")
            st.caption("SVGはReactのpublic/themes/に配置します。CSSのURLはデフォルトで /themes/ です。")
