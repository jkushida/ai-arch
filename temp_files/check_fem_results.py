#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FEM解析結果の詳細確認
"""

import sys
import os

# キャッシュクリア
for m in list(sys.modules.keys()):
    if 'generate_building_fem_analyze' in m:
        del sys.modules[m]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# VERBOSE出力を有効化
os.environ['VERBOSE_OUTPUT'] = '1'

from generate_building_fem_analyze import evaluate_building_from_params

# テストケース（test_seismic_load.pyと同じ設定）
design_vars = {
    "Lx": 10.0,
    "Ly": 10.0,
    "H1": 3.0,
    "H2": 3.0,
    "tf": 300,
    "tr": 250,
    "bc": 500,
    "hc": 500,
    "tw_ext": 250,
    "wall_tilt_angle": 0.0,
    "window_ratio_2f": 0.3,
    "roof_morph": 0.5,
    "roof_shift": 0.0,
    "balcony_depth": 2.0,
    # すべてコンクリート
    "material_columns": 0,
    "material_floor1": 0,
    "material_floor2": 0,
    "material_roof": 0,
    "material_walls": 0,
    "material_balcony": 0,
}

print("\n" + "="*60)
print("コンクリート造の詳細")
print("="*60)

result_concrete = evaluate_building_from_params(design_vars, save_fcstd=False)

if result_concrete['status'] == 'Success':
    print(f"\n【結果】")
    print(f"安全率: {result_concrete['safety']['overall_safety_factor']:.2f}")
    print(f"最大応力: {result_concrete['safety'].get('max_stress', 0):.2f} MPa")
    print(f"最大変位: {result_concrete['safety'].get('max_displacement', 0):.2f} mm")
    
    # FEM結果の詳細
    fem = result_concrete.get('raw_fem_results', {})
    if fem:
        print(f"\n【FEM結果詳細】")
        print(f"平均応力: {fem.get('avg_stress', 0):.2f} MPa")
        print(f"平均変位: {fem.get('avg_displacement', 0):.2f} mm")

# 木造
design_vars.update({
    "material_columns": 1,
    "material_floor1": 1,
    "material_floor2": 1,
    "material_roof": 1,
    "material_walls": 1,
    "material_balcony": 1,
})

print("\n" + "="*60)
print("木造の詳細")
print("="*60)

result_wood = evaluate_building_from_params(design_vars, save_fcstd=False)

if result_wood['status'] == 'Success':
    print(f"\n【結果】")
    print(f"安全率: {result_wood['safety']['overall_safety_factor']:.2f}")
    print(f"最大応力: {result_wood['safety'].get('max_stress', 0):.2f} MPa")
    print(f"最大変位: {result_wood['safety'].get('max_displacement', 0):.2f} mm")
    
    # FEM結果の詳細
    fem = result_wood.get('raw_fem_results', {})
    if fem:
        print(f"\n【FEM結果詳細】")
        print(f"平均応力: {fem.get('avg_stress', 0):.2f} MPa")
        print(f"平均変位: {fem.get('avg_displacement', 0):.2f} mm")

# 比較
if result_concrete['status'] == 'Success' and result_wood['status'] == 'Success':
    print("\n" + "="*60)
    print("比較結果")
    print("="*60)
    
    c_safety = result_concrete['safety']['overall_safety_factor']
    w_safety = result_wood['safety']['overall_safety_factor']
    c_stress = result_concrete['safety'].get('max_stress', 0)
    w_stress = result_wood['safety'].get('max_stress', 0)
    c_disp = result_concrete['safety'].get('max_displacement', 0)
    w_disp = result_wood['safety'].get('max_displacement', 0)
    
    print(f"安全率比（木造/コンクリート）: {w_safety/c_safety:.2f}")
    print(f"応力比（木造/コンクリート）: {w_stress/c_stress:.2f}")
    print(f"変位比（木造/コンクリート）: {w_disp/c_disp:.2f}")
    
    print(f"\n【解釈】")
    if w_stress/c_stress > 0.9 and w_stress/c_stress < 1.1:
        print("⚠️ FEM解析で応力がほぼ同じ → 材料特性が反映されていない可能性")
    if w_disp/c_disp > 1.5:
        print("✅ 木造の変位が大きい → ヤング率の違いが反映されている")
    else:
        print("⚠️ 変位の差が小さい → ヤング率の違いが十分反映されていない")