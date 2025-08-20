"""
range_presets.py

設計変数の定義域（上下限）を固定・狭域化するためのプリセット集。

使い方:
- `pso_config.py` で RANGE_PRESET を設定（例: 'small_footprint_low_height'）
- 本ファイルの `PRESET_NAME_TO_RANGE_OVERRIDES` で定義された上書きを適用
- (min, max) が同値なら固定値として扱われる

注意:
- ここでの範囲はベースの `variable_ranges` を超えないことを推奨
- 超える場合は `pso_config.py` 側でベース範囲にクランプされる
"""
from __future__ import annotations

# 各プリセットは { 変数名: (下限, 上限) } の辞書
PRESET_NAME_TO_RANGE_OVERRIDES = {
    # 変更なし
    "default": {},

    # 小さめの平面・低めの階高にフォーカス（狭域化）
    "small_footprint_low_height": {
        "Lx": (8.0, 10.0),
        "Ly": (6.0, 8.0),
        "H1": (2.6, 3.0),
        "H2": (2.6, 3.0),
        "window_ratio_2f": (0.2, 0.6),
        "wall_tilt_angle": (-10.0, 10.0),
    },

    # 柱断面を500mm角に固定して他の変数で最適化（固定値）
    "lock_columns_500mm": {
        "bc": (500, 500),
        "hc": (500, 500),
    },

    # 快適性寄りの外形: 天井高と窓比率を高めに（狭域化）
    "comfort_focused_envelope": {
        "H1": (3.0, 3.5),
        "H2": (3.0, 3.2),
        "window_ratio_2f": (0.4, 0.8),
        "wall_tilt_angle": (-10.0, 10.0),
    },

    # 低炭素: 木材固定（離散）
    "low_carbon_timber_all": {
        "material_columns": (1, 1),
        "material_floor1": (1, 1),
        "material_floor2": (1, 1),
        "material_roof": (1, 1),
        "material_walls": (1, 1),
        "material_balcony": (1, 1),
    },

    # ハイブリッド: 柱RC、他は木材
    "hybrid_columns_rc_others_timber": {
        "material_columns": (0, 0),
        "material_floor1": (1, 1),
        "material_floor2": (1, 1),
        "material_roof": (1, 1),
        "material_walls": (1, 1),
        "material_balcony": (1, 1),
    },

    # 軽量化: スラブ・外壁を薄めに（狭域化）
    "lightweight_thin_slabs": {
        "tf": (350, 450),
        "tr": (350, 450),
        "tw_ext": (300, 400),
    },
}
