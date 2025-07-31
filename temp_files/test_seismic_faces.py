#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地震荷重の面選択をデバッグ
"""

import sys
import os

# キャッシュクリア
for m in list(sys.modules.keys()):
    if 'generate_building' in m:
        del sys.modules[m]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# VERBOSE出力を有効化
os.environ['VERBOSE_OUTPUT'] = '1'

import generate_building_fem_analyze
generate_building_fem_analyze.VERBOSE_OUTPUT = True

from generate_building_fem_analyze import evaluate_building_from_params

# シンプルなテストケース
design_vars = {
    "Lx": 8.0,
    "Ly": 8.0,
    "H1": 3.0,
    "H2": 3.0,
    "tf": 250,
    "tr": 200,
    "bc": 400,
    "hc": 400,
    "tw_ext": 200,
    "wall_tilt_angle": 0.0,
    "window_ratio_2f": 0.3,
    "roof_morph": 0.5,
    "roof_shift": 0.0,
    "balcony_depth": 0.0,
    "material_columns": 1,  # 木造
    "material_floor1": 1,
    "material_floor2": 1,
    "material_roof": 1,
    "material_walls": 1,
    "material_balcony": 1,
}

print("\n【木造での地震荷重面選択テスト】")
result = evaluate_building_from_params(design_vars, save_fcstd=True)