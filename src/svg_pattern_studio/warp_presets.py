"""Convenient trapezoid geometry presets shared by both UI modes."""

WARP_PRESETS: dict[str, tuple[int, int, int, int]] = {
    '変形なし': (100, 100, 0, 0),
    '下へ広がる台形': (65, 135, 0, 0),
    '上へ広がる台形': (135, 65, 0, 0),
    '右に傾ける': (100, 100, -18, 18),
    '左に傾ける': (100, 100, 18, -18),
    '右下へ広がる': (75, 135, -5, 18),
    '左下へ広がる': (75, 135, 5, -18),
}
KEYS = ('warp_top', 'warp_bottom', 'warp_top_shift', 'warp_bottom_shift')


def warp_preset_name(layer: dict) -> str:
    values = tuple(int(layer.get(key, default)) for key, default in zip(KEYS, (100, 100, 0, 0)))
    return next((name for name, setting in WARP_PRESETS.items() if setting == values), '自由調整')


def apply_warp_preset(layer: dict, name: str) -> dict:
    if name == '自由調整':
        return dict(layer)
    result = dict(layer)
    result.update(zip(KEYS, WARP_PRESETS[name]))
    return result
