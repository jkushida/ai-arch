#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地震荷重デバッグテスト
"""

import sys
import os

# モジュールキャッシュをクリア
if 'generate_building_fem_analyze' in sys.modules:
    del sys.modules['generate_building_fem_analyze']

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 最小限のVERBOSE出力
os.environ['VERBOSE_OUTPUT'] = '0'

from generate_building_fem_analyze import evaluate_building_from_params

# 最小限のテストケース
design_vars = {
    "Lx": 8.0,
    "Ly": 8.0,
    "H1": 3.0,
    "H2": 3.0,
    "tf": 200,
    "tr": 150,
    "bc": 400,
    "hc": 400,
    "tw_ext": 200,
    "wall_tilt_angle": 0.0,
    "window_ratio_2f": 0.3,
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

print("\n========== コンクリート造テスト ==========")
result_concrete = evaluate_building_from_params(design_vars, save_fcstd=False)

if result_concrete['status'] == 'Success':
    print(f"\n✅ コンクリート造 - 安全率: {result_concrete['safety']['overall_safety_factor']:.2f}")
    print(f"   最大応力: {result_concrete['safety'].get('max_stress', 0):.2f} MPa")
    print(f"   最大変位: {result_concrete['safety'].get('max_displacement', 0):.2f} mm")

# 木造に変更
design_vars.update({
    "material_columns": 1,  # 木材
    "material_floor1": 1,
    "material_floor2": 1,
    "material_roof": 1,
    "material_walls": 1,
    "material_balcony": 1,
})

print("\n========== 木造テスト ==========")
result_wood = evaluate_building_from_params(design_vars, save_fcstd=False)

if result_wood['status'] == 'Success':
    print(f"\n✅ 木造 - 安全率: {result_wood['safety']['overall_safety_factor']:.2f}")
    print(f"   最大応力: {result_wood['safety'].get('max_stress', 0):.2f} MPa")
    print(f"   最大変位: {result_wood['safety'].get('max_displacement', 0):.2f} mm")

# 比較
if result_concrete['status'] == 'Success' and result_wood['status'] == 'Success':
    safety_ratio = result_wood['safety']['overall_safety_factor'] / result_concrete['safety']['overall_safety_factor']
    print(f"\n📊 安全率比（木造/コンクリート）: {safety_ratio:.2f}")
    
    if safety_ratio >= 1.0:
        print("❌ 木造の安全率が依然として高い！")
    else:
        print("✅ 木造の安全率が低くなりました！")