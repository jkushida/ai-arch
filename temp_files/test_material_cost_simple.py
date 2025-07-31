#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
材料コストの比較テスト（簡潔版）
"""

import sys
import os

# VERBOSEを無効化
os.environ['VERBOSE_OUTPUT'] = '0'

# キャッシュクリア
for m in list(sys.modules.keys()):
    if 'generate_building' in m:
        del sys.modules[m]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import generate_building_fem_analyze
generate_building_fem_analyze.VERBOSE_OUTPUT = False

from generate_building_fem_analyze import evaluate_building_from_params

# 同じ建物で材料だけ変えて比較
base_design = {
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
    "balcony_depth": 1.5,
}

# コンクリート造
concrete_design = {
    **base_design,
    "material_columns": 0,
    "material_floor1": 0,
    "material_floor2": 0,
    "material_roof": 0,
    "material_walls": 0,
    "material_balcony": 0,
}

# 木造
wood_design = {
    **base_design,
    "material_columns": 1,
    "material_floor1": 1,
    "material_floor2": 1,
    "material_roof": 1,
    "material_walls": 1,
    "material_balcony": 1,
}

print("=== 材料コスト比較テスト ===\n")
print("建物仕様: 10m×10m、2階建て")
print("材料単価: コンクリート 20,000円/m³、木材 15,000円/m³（修正後）\n")

# コンクリート造
print("【コンクリート造】")
result_c = evaluate_building_from_params(concrete_design, save_fcstd=False)
if result_c['status'] == 'Success':
    print(f"  コスト: {result_c['economic']['cost_per_sqm']:,.0f} 円/m²")
    print(f"  CO2: {result_c['environmental']['co2_per_sqm']:.1f} kg-CO2/m²")
    print(f"  安全率: {result_c['safety']['overall_safety_factor']:.2f}")

# 木造
print("\n【木造】")
result_w = evaluate_building_from_params(wood_design, save_fcstd=False)
if result_w['status'] == 'Success':
    print(f"  コスト: {result_w['economic']['cost_per_sqm']:,.0f} 円/m²")
    print(f"  CO2: {result_w['environmental']['co2_per_sqm']:.1f} kg-CO2/m²")
    print(f"  安全率: {result_w['safety']['overall_safety_factor']:.2f}")

# 比較
if result_c['status'] == 'Success' and result_w['status'] == 'Success':
    cost_ratio = result_w['economic']['cost_per_sqm'] / result_c['economic']['cost_per_sqm']
    co2_ratio = result_w['environmental']['co2_per_sqm'] / result_c['environmental']['co2_per_sqm']
    safety_ratio = result_w['safety']['overall_safety_factor'] / result_c['safety']['overall_safety_factor']
    
    print("\n【比較結果（木造/コンクリート）】")
    print(f"  コスト比: {cost_ratio:.2f}")
    print(f"  CO2比: {co2_ratio:.2f}")
    print(f"  安全率比: {safety_ratio:.2f}")
    
    print("\n【コスト差】")
    cost_diff = result_w['economic']['cost_per_sqm'] - result_c['economic']['cost_per_sqm']
    print(f"  木造 - コンクリート: {cost_diff:,.0f} 円/m²")
    if cost_diff < 0:
        print("  ✅ 木造の方が安い！")
        print(f"  削減率: {(1 - cost_ratio)*100:.1f}%")