#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
減衰特性による応答増幅効果のテスト
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

# VERBOSEを直接設定
import generate_building_fem_analyze
generate_building_fem_analyze.VERBOSE_OUTPUT = True

from generate_building_fem_analyze import evaluate_building_from_params

# テストケース
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
    "material_columns": 0,  # コンクリート
    "material_floor1": 0,
    "material_floor2": 0,
    "material_roof": 0,
    "material_walls": 0,
    "material_balcony": 0,
}

print("\n【コンクリート造】")
result_c = evaluate_building_from_params(design_vars, save_fcstd=False)

# 木造
design_vars.update({
    "material_columns": 1,
    "material_floor1": 1,
    "material_floor2": 1,
    "material_roof": 1,
    "material_walls": 1,
    "material_balcony": 1,
})

print("\n【木造】")
result_w = evaluate_building_from_params(design_vars, save_fcstd=False)

# 結果サマリー
print("\n" + "="*60)
print("減衰特性考慮後の結果")
print("="*60)

if result_c['status'] == 'Success' and result_w['status'] == 'Success':
    c_safety = result_c['safety']['overall_safety_factor']
    w_safety = result_w['safety']['overall_safety_factor']
    
    print(f"\nコンクリート造:")
    print(f"  安全率: {c_safety:.2f}")
    print(f"  最大応力: {result_c['safety'].get('max_stress', 0):.1f} MPa")
    print(f"  最大変位: {result_c['safety'].get('max_displacement', 0):.1f} mm")
    
    print(f"\n木造:")
    print(f"  安全率: {w_safety:.2f}")
    print(f"  最大応力: {result_w['safety'].get('max_stress', 0):.1f} MPa")
    print(f"  最大変位: {result_w['safety'].get('max_displacement', 0):.1f} mm")
    
    print(f"\n安全率比（木造/コンクリート）: {w_safety/c_safety:.2f}")
    
    if w_safety < c_safety:
        print("\n✅ 成功！減衰特性の考慮により木造の安全率が低くなりました。")
    else:
        print("\n❌ まだ改善が必要です。")
else:
    print("エラーが発生しました")