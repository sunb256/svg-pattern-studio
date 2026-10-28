"""Streamlit UI for composing browser-page backgrounds."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import random

import streamlit as st
import streamlit.components.v1 as components

try:
    from .generator import FADES, KINDS, default_layer
    from .layer_tools import copy_layer, duplicate_layer, nudge_layer, layer_difference
    from .preset_tools import apply_web_preset
    from .web_background import default_web_theme, make_web_pack, web_css, web_preview_html, web_presets, web_svgs
except ImportError:
    from generator import FADES, KINDS, default_layer
    from layer_tools import copy_layer, duplicate_layer, nudge_layer, layer_difference
    from preset_tools import apply_web_preset
    from web_background import default_web_theme, make_web_pack, web_css, web_preview_html, web_presets, web_svgs

PATTERN_NAMES = {
    "Flowing waves": "流れる波線", "Curved grid": "曲線グリッド",
    "Organic contours": "等高線", "Triangle mesh": "三角形メッシュ",
    "Radiating arcs": "放射状の円弧", "Spirograph": "スピログラフ",
    "Perspective fan": "交差する扇状曲線", "Hexagon grid": "六角形グリッド",
    "Dot field": "ドット", "None": "なし", "To right": "右方向に消える",
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


def _init() -> None:
    if "web_config" not in st.session_state:
        st.session_state.web_config = default_web_theme()
    if "web_rev" not in st.session_state:
        st.session_state.web_rev = 0
    if "web_focus" not in st.session_state:
        st.session_state.web_focus = None


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

    st.markdown("**2. 横幅・線切れ対策**")
    width_mode = (
        "固定幅" if zone["size_unit"] == "px" else
        "画面幅に合わせる" if zone["size"] == 100 else
        "画面より広く" if zone["size"] == 115 else "カスタム"
    )
    sizing = st.radio(
        "横幅の指定", ["画面幅に合わせる", "画面より広く", "固定幅", "カスタム"],
        index=["画面幅に合わせる", "画面より広く", "固定幅", "カスタム"].index(width_mode),
        key=f"{key}-width-mode",
        help="おすすめは画面幅以上。線は移動・回転後の表示範囲まで生成され、画面端で自然に消えます。",
    )
    if sizing == "画面幅に合わせる":
        zone["size_unit"], zone["size"] = "%", 100
    elif sizing == "画面より広く":
        zone["size_unit"], zone["size"] = "%", 115
    elif sizing == "固定幅":
        if zone["size_unit"] != "px":
            zone["size"] = 1200
        zone["size_unit"] = "px"
        zone["size"] = int(st.number_input(
            "表示幅 (px)", 100, 4000, int(zone["size"]), 50, key=f"{key}-pixel-width",
        ))
    else:
        unit = st.selectbox(
            "単位", ["%", "px"], index=["%", "px"].index(zone["size_unit"]),
            key=f"{key}-custom-unit",
        )
        old_size = int(zone["size"])
        if unit != zone["size_unit"]:
            old_size = 100 if unit == "%" else 1200
        zone["size_unit"] = unit
        zone["size"] = int(st.number_input(
            "表示幅", min_value=10 if unit == "%" else 100,
            max_value=250 if unit == "%" else 4000, value=old_size,
            step=5 if unit == "%" else 50, key=f"{key}-custom-size-{unit}",
        ))
    if ((zone["size_unit"] == "%" and zone["size"] < 100)
            or zone["size_unit"] == "px"):
        st.info("固定幅や100%未満では、画像そのものの端がページ内に見える場合があります。"
                "ページ全体を途切れず覆うには「画面幅に合わせる」か「画面より広く」を選択してください。")
    zone["edge_feather"] = st.slider(
        "Webページの左右端を自然に消す (%)", 0, 40, int(zone.get("edge_feather", 10)), 1,
        key=f"{key}-edge-feather",
        help="SVGを115%に拡大しても、実際に表示される画面の端を基準にフェードします。",
    )
    zone["vertical_feather"] = st.slider(
        "模様の上下境界をなめらかに消す (%)", 0, 50,
        int(zone.get("vertical_feather", 28)), 1, key=f"{key}-vertical-feather",
        help="上部SVGなら下辺、下部SVGなら上辺から自然に消すため、画像の境界が横線になりません。",
    )
    with st.expander("SVGキャンバスの縦横比（通常は変更不要）", expanded=False):
        a, b = st.columns(2)
        zone["width"] = int(a.number_input("SVG横幅 (px)", 200, 6000, int(zone["width"]), 50, key=f"{key}-w"))
        zone["height"] = int(b.number_input("SVG高さ (px)", 200, 6000, int(zone["height"]), 50, key=f"{key}-h"))

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
    st.title("SVG Pattern Studio — Web背景モード")
    presets = web_presets()
    st.caption(f"{len(presets)}種類のデザイン例。色名＋模様名で選べます。選択すると即時に切り替わります。")
    with st.expander(f"{len(presets)}種類の背景デザインを一覧表示", expanded=False):
        gallery = Path(__file__).resolve().parent / "assets" / "design-gallery.png"
        if gallery.is_file():
            st.image(str(gallery), use_column_width=True)
        st.caption("サイドバーの「デザイン例」を変更すると即時に反映します。現在の調整内容は置き換わります。")

    config = deepcopy(st.session_state.web_config)
    revision = st.session_state.web_rev
    with st.sidebar:
        st.subheader("Web背景の設定")
        st.selectbox(
            "デザイン例", list(presets), key="web-selected-preset",
            on_change=_on_preset_change,
            help="選択を変更すると即座にテーマが切り替わります。未保存の調整は上書きされます。",
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
            "作業エリアの高さ", options=[480, 560, 640, 720], value=560,
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
            st.subheader("Webページのライブプレビュー")
            html = web_preview_html(config, viewport_width=viewport, page_height=height, fit=fit)
            components.html(html, height=work_height - 75 if keep_preview else 640, scrolling=False)
            st.caption(f"ページ {viewport} × {height}px。模様の配置は書き出しCSSと同じ設定です。")

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
