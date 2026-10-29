"""Run: uv run --with streamlit streamlit run app.py"""

from __future__ import annotations

import base64
from copy import deepcopy
import io
import json
import random
import zipfile

import streamlit as st
import streamlit.components.v1 as components

from generator import FADES, KINDS, PRESETS, default_layer, preset_layers, render_svg
try:
    from .layer_tools import copy_layer, duplicate_layer, nudge_layer, layer_difference, layer_warp_difference
    from .warp_presets import WARP_PRESETS, apply_warp_preset, warp_preset_name
except ImportError:
    from layer_tools import copy_layer, duplicate_layer, nudge_layer, layer_difference, layer_warp_difference
    from warp_presets import WARP_PRESETS, apply_warp_preset, warp_preset_name


SIZES = {
    "Desktop 16:9 (1600×900)": (1600, 900),
    "Wide 21:9 (1680×720)": (1680, 720),
    "Portrait (900×1600)": (900, 1600),
    "Square (1080×1080)": (1080, 1080),
    "Decoration strip (1600×450)": (1600, 450),
    "Custom": None,
}
JAPANESE = {
    "Flowing waves": "流れる波線",
    "Curved grid": "曲線グリッド",
    "Organic contours": "有機的な等高線",
    "Triangle mesh": "三角形ネットワーク",
    "Radiating arcs": "放射状の円弧",
    "Spirograph": "スピログラフ",
    "Perspective fan": "扇状に交差する曲線",
    "Hexagon grid": "六角形グリッド",
    "Dot field": "ドットの配置",
    "None": "なし",
    "To right": "右方向に消える",
    "To left": "左方向に消える",
    "To bottom": "下方向に消える",
    "To top": "上方向に消える",
    "Center focus": "周辺に向けて消える",
}
BLENDS = {"normal": "通常", "screen": "スクリーン（明るく交差）", "multiply": "乗算（暗く交差）", "overlay": "オーバーレイ"}


def init_state() -> None:
    if "layers" not in st.session_state:
        st.session_state.layers = preset_layers("Deep ocean")
    if "layer_revision" not in st.session_state:
        st.session_state.layer_revision = 0
    if "layer_focus" not in st.session_state:
        st.session_state.layer_focus = None
    if "bg_start" not in st.session_state:
        st.session_state.bg_start = PRESETS["Deep ocean"]["bg_start"]
    if "bg_end" not in st.session_state:
        st.session_state.bg_end = PRESETS["Deep ocean"]["bg_end"]
    if "glow" not in st.session_state:
        st.session_state.glow = PRESETS["Deep ocean"]["glow"]


def _on_classic_preset_change() -> None:
    """Switch the normal SVG mode as soon as the selection changes."""
    name = st.session_state["classic-selected-preset"]
    config = PRESETS[name]
    st.session_state.bg_start = config["bg_start"]
    st.session_state.bg_end = config["bg_end"]
    st.session_state.glow = config["glow"]
    st.session_state.layers = preset_layers(name)
    st.session_state.layer_revision += 1
    st.session_state.layer_focus = None


def change_layers(layers: list[dict]) -> None:
    st.session_state.layers = layers
    st.session_state.layer_revision += 1
    st.rerun()


def make_pack(width: int, height: int, layers: list[dict], bg_start: str, bg_end: str, glow: int) -> bytes:
    def make(layers_: list[dict], transparent: bool) -> str:
        return render_svg(width, height, layers_, bg_start=bg_start, bg_end=bg_end,
                          glow=glow, transparent=transparent)

    manifest = {
        "name": "Custom geometric theme",
        "background": "composite.svg",
        "overlay": "overlay.svg",
        "bg_start": bg_start,
        "bg_end": bg_end,
        "layers": layers,
        "size": {"width": width, "height": height},
        "note": "Use overlay.svg on a CSS background gradient when page height varies.",
    }
    css = f"""/* Fixed image, scales without losing quality; may crop at other aspect ratios. */
.page-background {{
  min-height: 100vh;
  background: url('/themes/composite.svg') center / cover no-repeat;
}}

/* For pages of variable height: gradient is independent of the transparent decoration. */
.page-background-flexible {{
  min-height: 100vh;
  background-image: url('/themes/overlay.svg'), linear-gradient(145deg, {bg_start}, {bg_end});
  background-position: center top, center;
  background-size: 100% auto, cover;
  background-repeat: no-repeat;
}}
"""
    bio = io.BytesIO()
    with zipfile.ZipFile(bio, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("composite.svg", make(layers, False))
        z.writestr("overlay.svg", make(layers, True))
        for i, layer in enumerate(layers, start=1):
            if layer.get("enabled", True):
                z.writestr(f"layers/layer-{i:02d}.svg", make([layer], True))
        z.writestr("theme.json", json.dumps(manifest, indent=2, ensure_ascii=False))
        z.writestr("example.css", css)
    return bio.getvalue()


def _on_classic_warp_change(index: int, key: str) -> None:
    name = st.session_state[key]
    if name == "自由調整":
        return
    layers = deepcopy(st.session_state.layers)
    layers[index] = apply_warp_preset(layers[index], name)
    st.session_state.layers = layers
    st.session_state.layer_focus = index
    st.session_state.layer_revision += 1


def render_classic_mode() -> None:
    init_state()
    st.title("SVG Pattern Studio")
    st.caption("9種類の幾何学・曲線パターンを重ねて、SVG背景を作成するローカルツール。変更すると即座にプレビューへ反映されます。")

    with st.sidebar:
        st.subheader("キャンバスと色")
        st.selectbox(
            "デザイン例", list(PRESETS), index=0, key="classic-selected-preset",
            on_change=_on_classic_preset_change,
            help="選択したデザインがすぐプレビューに反映され、未保存の調整は置き換わります。",
        )

        if st.button("模様のランダム値を変える", use_container_width=True):
            layers = [layer | {"seed": random.SystemRandom().randint(0, 99999)}
                      for layer in st.session_state.layers]
            change_layers(layers)

        size_name = st.selectbox("キャンバス比率", list(SIZES))
        if SIZES[size_name] is None:
            c1, c2 = st.columns(2)
            width = int(c1.number_input("幅", 200, 6000, 1600, 50))
            height = int(c2.number_input("高さ", 200, 6000, 900, 50))
        else:
            width, height = SIZES[size_name]
        transparent = st.toggle("背景を透明にする", value=False,
                                help="模様だけのSVGとして出力。ページの上や下などに重ねたいときに便利です。")
        c1, c2 = st.columns(2)
        bg_start = c1.color_picker("背景色 1", key="bg_start")
        bg_end = c2.color_picker("背景色 2", key="bg_end")
        glow = st.slider("背景の柔らかな光", 0, 100, key="glow")
        st.divider()
        st.caption("生成したSVGは編集可能なベクター画像です。複数レイヤーは下から上へ順番に重なります。")

    edit, preview = st.columns([1.0, 1.35], gap="large")
    with edit:
        h, plus, minus = st.columns([4, 1.3, 1.3], vertical_alignment="center")
        h.subheader("パターンのレイヤー")
        if plus.button("＋ 追加", disabled=len(st.session_state.layers) >= 6,
                       help="最大6レイヤー"):
            change_layers(st.session_state.layers + [default_layer("Organic contours", len(st.session_state.layers)*23+9)])
        if minus.button("－ 削除", disabled=len(st.session_state.layers) <= 1,
                        help="最後のレイヤーを削除"):
            change_layers(st.session_state.layers[:-1])

        with st.expander("レイヤー間でコピー（例: 1 → 2）", expanded=False):
            st.caption("コピー先の設定をすべて上書きします。seedを共有するので形は同じです。")
            if len(st.session_state.layers) > 1:
                c1, c2 = st.columns(2)
                src = c1.selectbox("コピー元", range(len(st.session_state.layers)),
                                   format_func=lambda idx: f"レイヤー {idx+1}", key="classic-copy-from")
                targets = [j for j in range(len(st.session_state.layers)) if j != src]
                dst = c2.selectbox("コピー先", targets, format_func=lambda idx: f"レイヤー {idx+1}",
                                   key="classic-copy-to")
                if st.button(f"{src+1} → {dst+1} にコピー", key="classic-copy-button"):
                    st.session_state.layer_focus = dst
                    change_layers(copy_layer(st.session_state.layers, src, dst))
            else:
                st.caption("先にレイヤーを追加してください。")
        edited_layers = []
        rev = st.session_state.layer_revision
        for i, layer in enumerate(st.session_state.layers):
            prefix = f"layer-{rev}-{i}"
            with st.expander(f"{i+1}. {JAPANESE.get(layer['kind'],layer['kind'])}",
                             expanded=(st.session_state.layer_focus == i if st.session_state.layer_focus is not None else i < 2)):
                enabled = st.checkbox("このレイヤーを表示", value=layer.get("enabled",True), key=f"{prefix}-enable")
                kind = st.selectbox("模様", KINDS,
                                    index=KINDS.index(layer["kind"]),
                                    format_func=lambda k: JAPANESE[k], key=f"{prefix}-kind")
                color_col, blend_col = st.columns([.7,1.3], vertical_alignment="bottom")
                color = color_col.color_picker("線の色", layer["color"], key=f"{prefix}-color")
                blend = blend_col.selectbox("重ね合わせ", list(BLENDS),
                                           index=list(BLENDS).index(layer.get("blend","normal")),
                                           format_func=lambda k: BLENDS[k], key=f"{prefix}-blend")
                c1,c2 = st.columns(2)
                opacity = c1.slider("透明度（表示の濃さ）", 0, 100, int(layer["opacity"]*100), 1, key=f"{prefix}-opacity")
                density = c2.slider("線や図形の数", 5, 55, int(layer["density"]), 1, key=f"{prefix}-density")
                c1,c2 = st.columns(2)
                linewidth = c1.slider("線の太さ", .3, 4.0, float(layer["width"]), .1, key=f"{prefix}-width")
                scale = c2.slider("模様の拡大率", 30, 200, int(float(layer["scale"])*100), 5, key=f"{prefix}-scale")
                c1,c2 = st.columns(2)
                x = c1.slider("左右位置 (%)", -100, 100, int(layer["x"]), 5, key=f"{prefix}-x")
                y = c2.slider("上下位置 (%)", -100, 100, int(layer["y"]), 5, key=f"{prefix}-y")
                rotation = st.slider("回転 (°)", -180, 180, int(layer["rotation"]), 5, key=f"{prefix}-rot")
                with st.popover("台形変形・傾き（遠近感）", use_container_width=True):
                    st.caption("変形パターンの選択で即時反映。スライダーでさらに微調整できます。")
                    shape_names = list(WARP_PRESETS) + ["自由調整"]
                    st.selectbox("変形パターン", shape_names,
                                 index=shape_names.index(warp_preset_name(layer)),
                                 key=f"{prefix}-warp-shape", on_change=_on_classic_warp_change,
                                 args=(i, f"{prefix}-warp-shape"))
                    cc1, cc2 = st.columns(2)
                    warp_top = cc1.slider("上辺の幅 (%)", 40, 160, int(layer.get("warp_top", 100)), 2, key=f"{prefix}-warp-top")
                    warp_bottom = cc2.slider("下辺の幅 (%)", 40, 160, int(layer.get("warp_bottom", 100)), 2, key=f"{prefix}-warp-bottom")
                    cc3, cc4 = st.columns(2)
                    warp_top_shift = cc3.slider("上辺の横ずれ (%)", -50, 50, int(layer.get("warp_top_shift", 0)), 1, key=f"{prefix}-warp-top-shift")
                    warp_bottom_shift = cc4.slider("下辺の横ずれ (%)", -50, 50, int(layer.get("warp_bottom_shift", 0)), 1, key=f"{prefix}-warp-bottom-shift")
                fade = st.selectbox("フェード方向", FADES, index=FADES.index(layer["fade"]),
                                    format_func=lambda k: JAPANESE[k], key=f"{prefix}-fade")
                seed = int(st.number_input("形のランダム値（seed）", 0, 99999,
                                           int(layer["seed"]), 1, key=f"{prefix}-seed"))
                a, b = st.columns(2)
                can_duplicate = len(st.session_state.layers) < 6
                if a.button("⧉ 完全複製", disabled=not can_duplicate,
                            key=f"{prefix}-duplicate", use_container_width=True):
                    st.session_state.layer_focus = i + 1
                    change_layers(duplicate_layer(st.session_state.layers, i))
                if b.button("⧉ 少しずらして複製", disabled=not can_duplicate,
                            key=f"{prefix}-offset-duplicate", use_container_width=True,
                            help="右8%、回転+5°、濃さ80%。同じseedでコピー"):
                    st.session_state.layer_focus = i + 1
                    change_layers(duplicate_layer(st.session_state.layers, i,
                                                  shift_x=8, rotation=5, opacity_factor=.8))
                with st.popover("矢印・回転で微調整", use_container_width=True):
                    shift = st.select_slider("移動量 (%)", [1, 2, 3, 5, 10], value=3,
                                             key=f"{prefix}-shift-step")
                    turn = st.select_slider("回転量 (°)", [1, 2, 3, 5, 10], value=3,
                                            key=f"{prefix}-turn-step")
                    up = st.columns([1,1,1])
                    if up[1].button("↑", key=f"{prefix}-up-2", use_container_width=True):
                        st.session_state.layer_focus = i
                        change_layers(nudge_layer(st.session_state.layers, i, dy=-shift))
                    mid = st.columns(3)
                    if mid[0].button("←", key=f"{prefix}-left-2", use_container_width=True):
                        st.session_state.layer_focus = i
                        change_layers(nudge_layer(st.session_state.layers, i, dx=-shift))
                    if mid[2].button("→", key=f"{prefix}-right-2", use_container_width=True):
                        st.session_state.layer_focus = i
                        change_layers(nudge_layer(st.session_state.layers, i, dx=shift))
                    down = st.columns([1,1,1])
                    if down[1].button("↓", key=f"{prefix}-down-2", use_container_width=True):
                        st.session_state.layer_focus = i
                        change_layers(nudge_layer(st.session_state.layers, i, dy=shift))
                    rot = st.columns(2)
                    if rot[0].button(f"↶ -{turn}°", key=f"{prefix}-rot-l", use_container_width=True):
                        st.session_state.layer_focus = i
                        change_layers(nudge_layer(st.session_state.layers, i, drotation=-turn))
                    if rot[1].button(f"↷ +{turn}°", key=f"{prefix}-rot-r", use_container_width=True):
                        st.session_state.layer_focus = i
                        change_layers(nudge_layer(st.session_state.layers, i, drotation=turn))
                if len(st.session_state.layers) >= 2:
                    with st.popover("ほかのレイヤーとの差分を見る", use_container_width=True):
                        others = [j for j in range(len(st.session_state.layers)) if j != i]
                        reference_i = st.selectbox("比較元", others,
                                                    format_func=lambda j: f"レイヤー {j+1}",
                                                    key=f"{prefix}-compare")
                        reference = st.session_state.layers[reference_i]
                        current = dict(layer, x=x, y=y, rotation=rotation, scale=scale/100,
                                       seed=seed, kind=kind, density=density)
                        diff = layer_difference(reference, current)
                        st.write(f"左右 {diff['dx']:+d}% / 上下 {diff['dy']:+d}% / "
                                 f"角度 {diff['drotation']:+d}° / 拡大率 {diff['dscale']:+d}%")
                        warp_diff = layer_warp_difference(reference, current | {
                            "warp_top": warp_top, "warp_bottom": warp_bottom,
                            "warp_top_shift": warp_top_shift, "warp_bottom_shift": warp_bottom_shift,
                        })
                        st.caption(f"台形差：上辺 {warp_diff['dwarp_top']:+d}% / 下辺 {warp_diff['dwarp_bottom']:+d}% / "
                                   f"上辺ずれ {warp_diff['dwarp_top_shift']:+d}% / 下辺ずれ {warp_diff['dwarp_bottom_shift']:+d}%")
                        st.caption("同じ形を維持" if diff["same_geometry"] else "模様の種類・seed・密度が異なります")
                move_left, move_right = st.columns(2)
                if move_left.button("↑ 手前へ（順序変更）", key=f"{prefix}-up", disabled=i==len(st.session_state.layers)-1,
                                    use_container_width=True):
                    new = st.session_state.layers.copy()
                    new[i],new[i+1]=new[i+1],new[i]
                    change_layers(new)
                if move_right.button("↓ 奥へ（順序変更）", key=f"{prefix}-down", disabled=i==0,
                                     use_container_width=True):
                    new = st.session_state.layers.copy()
                    new[i],new[i-1]=new[i-1],new[i]
                    change_layers(new)
                edited_layers.append({
                    "enabled": enabled, "kind": kind, "color": color, "opacity": opacity/100,
                    "blend": blend, "density": density, "width": linewidth, "scale": scale/100,
                    "x": x, "y": y, "rotation": rotation, "fade": fade, "seed": seed,
                    "warp_top": warp_top, "warp_bottom": warp_bottom,
                    "warp_top_shift": warp_top_shift, "warp_bottom_shift": warp_bottom_shift,
                })
        st.session_state.layers = edited_layers

    with preview:
        st.subheader("ライブプレビュー")
        svg = render_svg(width, height, edited_layers, bg_start=bg_start, bg_end=bg_end,
                         glow=glow, transparent=transparent)
        encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
        preview_html = f"""<!DOCTYPE html><html><head><style>
            html,body {{margin:0; padding:0; background:#f0f2f5; height:100%;}}
            .stage {{height:505px; display:flex; align-items:center; justify-content:center;
              background-color:#e5e9ee;
              background-image:linear-gradient(45deg,#d5dae1 25%, transparent 25%),
              linear-gradient(-45deg,#d5dae1 25%,transparent 25%),
              linear-gradient(45deg,transparent 75%,#d5dae1 75%),
              linear-gradient(-45deg,transparent 75%,#d5dae1 75%);
              background-size:20px 20px; background-position:0 0,0 10px,10px -10px,-10px 0px;}}
            img {{display:block; max-width:100%; max-height:485px; width:auto; height:auto;
               box-shadow:0 8px 24px #0b152435; object-fit:contain;}}
            </style></head><body><div class="stage">
            <img alt="SVG pattern preview" width="{width}" height="{height}"
            src="data:image/svg+xml;base64,{encoded}"/></div></body></html>"""
        components.html(preview_html, height=510, scrolling=False)
        st.caption(f"出力サイズ {width} × {height} ／ {len([l for l in edited_layers if l['enabled']])} レイヤー ／ SVGは拡大しても線が粗くなりません。")
        st.subheader("エクスポート")
        c1,c2 = st.columns(2)
        c1.download_button("SVGを保存", svg.encode("utf-8"),
                           file_name="geometric-background.svg", mime="image/svg+xml", use_container_width=True,
                           type="primary")
        package = make_pack(width, height, edited_layers, bg_start, bg_end, glow)
        c2.download_button("一式をZIPで保存", package, file_name="svg-theme-pack.zip",
                           mime="application/zip", use_container_width=True)
        st.info("ZIPには、背景付きSVG・透明SVG・レイヤーごとのSVG・theme.json・CSS例を収録しています。ページの高さが変わる場合は、透明SVGとCSSグラデーションの組み合わせが便利です。")
        st.code("""/* React / CSS の例 */
    .page {
      min-height: 100vh;
      background: url('/themes/overlay.svg') center top / 100% auto no-repeat,
                  linear-gradient(145deg, var(--bg-start), var(--bg-end));
    }""", language="css")
