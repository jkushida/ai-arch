#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地震荷重デバッグテスト（VERBOSE版）
"""

import sys
import os

# モジュールキャッシュをクリア
if 'generate_building_fem_analyze' in sys.modules:
    del sys.modules['generate_building_fem_analyze']

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# VERBOSE出力を有効化
os.environ['VERBOSE_OUTPUT'] = '1'

# グローバル変数として設定
import generate_building_fem_analyze
generate_building_fem_analyze.VERBOSE_OUTPUT = True

from generate_building_fem_analyze import evaluate_building_from_params

# 最小限のテストケース
design_vars = {
    "Lx": 6.0,
    "Ly": 6.0,
    "H1": 3.0,
    "H2": 3.0,
    "tf": 200,
    "tr": 150,
    "bc": 400,
    "hc": 400,
    "tw_ext": 200,
    "wall_tilt_angle": 0.0,
    "window_ratio_2f": 0.2,
    "roof_morph": 0.5,
    "roof_shift": 0.0,
    "balcony_depth": 0.0,
    "material_columns": 0,  # コンクリート
    "material_floor1": 0,
    "material_floor2": 0,
    "material_roof": 0,
    "material_walls": 0,
    "material_balcony": 0,
}

print("\n========== コンクリート造テスト (VERBOSE) ==========")
result_concrete = evaluate_building_from_params(design_vars, save_fcstd=False)

if result_concrete['status'] == 'Success':
    print(f"\n✅ コンクリート造 - 安全率: {result_concrete['safety']['overall_safety_factor']:.2f}")
    print(f"   最大応力: {result_concrete['safety'].get('max_stress', 0):.2f} MPa")
    print(f"   最大変位: {result_concrete['safety'].get('max_displacement', 0):.2f} mm")