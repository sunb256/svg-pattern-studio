"""Standalone theme selection logic; kept separate from Streamlit widgets."""
from __future__ import annotations

from copy import deepcopy
from typing import Any, MutableMapping

try:
    from .web_background import web_presets
except ImportError:
    from web_background import web_presets


def apply_web_preset(state: MutableMapping[str, Any], name: str) -> None:
    """Atomically switch themes and invalidate obsolete editor/undo widget state.

    The dropdown's Streamlit on_change callback runs this *before* new editors
    are rendered, so the live preview and editor settings update together.
    """
    state["web_config"] = deepcopy(web_presets()[name])
    state["web_rev"] = int(state.get("web_rev", 0)) + 1
    state["web_focus"] = None
    for side in ("top", "bottom"):
        state.pop(f"web-undo-{side}", None)
