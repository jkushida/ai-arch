#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終確認テスト - 木造とコンクリート造の安全率比較
"""

import sys
import os

# モジュールキャッシュをクリア
modules_to_remove = [m for m in sys.modules if 'generate_building_fem_analyze' in m]
for m in modules_to_remove:
    del sys.modules[m]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# VERBOSE出力を有効化
os.environ['VERBOSE_OUTPUT'] = '1'

from generate_building_fem_analyze import evaluate_building_from_params

# シンプルなテストケース
design_vars_base = {
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
}

# コンクリート造
print("\n" + "="*60)
print("テスト1: コンクリート造")
print("="*60)
design_vars_concrete = design_vars_base.copy()
design_vars_concrete.update({
    "material_columns": 0,
    "material_floor1": 0,
    "material_floor2": 0,
    "material_roof": 0,
    "material_walls": 0,
    "material_balcony": 0,
})

result_concrete = evaluate_building_from_params(design_vars_concrete, save_fcstd=False)

# 木造
print("\n" + "="*60)
print("テスト2: 木造")
print("="*60)
design_vars_wood = design_vars_base.copy()
design_vars_wood.update({
    "material_columns": 1,
    "material_floor1": 1,
    "material_floor2": 1,
    "material_roof": 1,
    "material_walls": 1,
    "material_balcony": 1,
})

result_wood = evaluate_building_from_params(design_vars_wood, save_fcstd=False)

# 結果サマリー
print("\n" + "="*60)
print("結果サマリー")
print("="*60)

if result_concrete['status'] == 'Success':
    print(f"コンクリート造:")
    print(f"  安全率: {result_concrete['safety']['overall_safety_factor']:.2f}")
    print(f"  最大応力: {result_concrete['safety'].get('max_stress', 0):.2f} MPa")
    print(f"  最大変位: {result_concrete['safety'].get('max_displacement', 0):.2f} mm")

if result_wood['status'] == 'Success':
    print(f"\n木造:")
    print(f"  安全率: {result_wood['safety']['overall_safety_factor']:.2f}")
    print(f"  最大応力: {result_wood['safety'].get('max_stress', 0):.2f} MPa")
    print(f"  最大変位: {result_wood['safety'].get('max_displacement', 0):.2f} mm")

if result_concrete['status'] == 'Success' and result_wood['status'] == 'Success':
    safety_ratio = result_wood['safety']['overall_safety_factor'] / result_concrete['safety']['overall_safety_factor']
    print(f"\n安全率比（木造/コンクリート）: {safety_ratio:.2f}")
    
    if safety_ratio < 1.0:
        print("✅ 成功！木造の安全率がコンクリート造より低くなりました。")
    else:
        print("❌ 木造の安全率が依然として高いです。")