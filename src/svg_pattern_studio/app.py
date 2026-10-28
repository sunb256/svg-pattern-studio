"""Launch with: uv run streamlit run src/svg_pattern_studio/app.py"""

import streamlit as st

st.set_page_config(page_title="SVG Pattern Studio", layout="wide", page_icon="✳")
mode = st.sidebar.radio(
    "編集モード", ["Web背景モード", "通常のSVGモード"], key="studio_mode"
)
st.sidebar.divider()

if mode == "通常のSVGモード":
    from classic_ui import render_classic_mode
    render_classic_mode()
else:
    from web_ui import render_web_mode
    render_web_mode()
