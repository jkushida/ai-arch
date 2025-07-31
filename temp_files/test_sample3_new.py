#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sample3の対数的コスト計算テスト
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_building_fem_analyze import evaluate_building_from_params

# sample3のパラメータ
params = {
    'Lx': 9.59,
    'Ly': 11.08,
    'H1': 3.06,
    'H2': 3.01,
    'tf': 513,
    'tr': 553,
    'bc': 897,
    'hc': 933,
    'tw_ext': 471,
    'wall_tilt_angle': -4.8,
    'window_ratio_2f': 0.41,
    'roof_morph': 0.78,
    'roof_shift': 0.15,
    'balcony_depth': 2.8,
    'material_columns': 0,
    'material_floor1': 1,
    'material_floor2': 1,
    'material_roof': 0,
    'material_walls': 1,
    'material_balcony': 1
}

print("Sample3の対数的コスト計算テスト")
print("=" * 60)

# 評価実行
result = evaluate_building_from_params(params, save_fcstd=False)

if result['status'] == 'Success':
    print(f"✅ 評価成功")
    print(f"コスト: {result['economic']['cost_per_sqm']:,.0f} 円/m²")
    print(f"安全率: {result['safety']['overall_safety_factor']:.2f}")
    print(f"CO2: {result['environmental']['co2_per_sqm']:.1f} kg-CO2/m²")
    print(f"快適性: {result['comfort']['comfort_score']:.1f}")
    print(f"施工性: {result['constructability']['constructability_score']:.1f}")
else:
    print(f"❌ 評価失敗: {result.get('message', 'Unknown error')}")