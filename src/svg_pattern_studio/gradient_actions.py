"""Gradient button actions independent of Streamlit widgets.

Call these *inside* Streamlit on_click callbacks, before the new widget tree is
rendered. Mutating a color picker's session-state key after the widget has
already been instantiated during the same run raises StreamlitAPIException.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, MutableMapping, Mapping

BG_START = "web-compose-bg-start"
BG_END = "web-compose-bg-end"
BG_ANGLE = "web-compose-angle"
PALETTE = "web-compose-palette"


def _apply_gradient(state: MutableMapping[str, Any], start: str, end: str, angle: int) -> None:
    """Update the controls and exported theme from one source of truth."""
    config = deepcopy(state["web_config"])
    config.update(bg_start=start, bg_end=end, angle=int(angle))
    state[BG_START] = start
    state[BG_END] = end
    state[BG_ANGLE] = int(angle)
    state["web_config"] = config
    state["web_rev"] = int(state.get("web_rev", 0)) + 1


def swap_gradient(state: MutableMapping[str, Any]) -> None:
    """Exchange two background colors while preserving gradient angle."""
    _apply_gradient(state, state[BG_END], state[BG_START], int(state[BG_ANGLE]))


def restore_palette_gradient(
    state: MutableMapping[str, Any], palettes: Mapping[str, Mapping[str, Any]]
) -> None:
    """Restore the selected palette's two base colors and standard angle."""
    palette = palettes[state[PALETTE]]
    _apply_gradient(state, palette["bg_start"], palette["bg_end"], int(palette["angle"]))
