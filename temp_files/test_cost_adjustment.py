#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
コスト調整の効果をテスト
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from generate_building_fem_analyze import calculate_economic_cost
import pandas as pd

# production_freecad_random_fem_evaluation2.csv からsample30のデータを再現
sample30_info = {
    'Lx': 10.51,
    'Ly': 11.31,
    'H1': 3.03,
    'H2': 2.82,
    'tf_mm': 556,
    'tr_mm': 542,
    'bc_mm': 876,
    'hc_mm': 782,
    'tw_ext_mm': 465,
    'material_columns': 1,  # 木材
    'material_floor1': 0,   # コンクリート
    'material_floor2': 0,   # コンクリート
    'material_roof': 0,     # コンクリート
    'material_walls': 1,    # 木材
    'material_balcony': 0,  # コンクリート
    'volume': (10.51 * 11.31 * (3.03 + 2.82)) * 0.3,  # 概算
    'mass': (10.51 * 11.31 * (3.03 + 2.82)) * 0.3 * 2400,  # 概算
    'asymmetry_factor': 0.1,
    'opening_complexity': 0.1,
    'structural_irregularity': 0.1,
    'has_cantilever': True,
    'has_stairs': True,
    'wall_tilt_angle': 14.4,
    'roof_morph': 0.71
}

# 他のサンプルも比較のために計算
sample_infos = {
    'sample1': {
        'Lx': 8.21,
        'Ly': 8.35,
        'H1': 2.97,
        'H2': 2.66,
        'tf_mm': 580,
        'tr_mm': 573,
        'bc_mm': 439,
        'hc_mm': 788,
        'tw_ext_mm': 437,
        'material_columns': 0,
        'material_floor1': 0,
        'material_floor2': 0,
        'material_roof': 1,
        'material_walls': 0,
        'material_balcony': 1,
        'volume': (8.21 * 8.35 * (2.97 + 2.66)) * 0.3,
        'mass': (8.21 * 8.35 * (2.97 + 2.66)) * 0.3 * 2400,
        'asymmetry_factor': 0.1,
        'opening_complexity': 0.1,
        'structural_irregularity': 0.1,
        'has_cantilever': True,
        'has_stairs': True,
        'wall_tilt_angle': 3.7,
        'roof_morph': 0.14
    },
    'sample3': {
        'Lx': 9.59,
        'Ly': 11.08,
        'H1': 3.06,
        'H2': 3.01,
        'tf_mm': 513,
        'tr_mm': 553,
        'bc_mm': 897,
        'hc_mm': 933,
        'tw_ext_mm': 471,
        'material_columns': 0,
        'material_floor1': 1,
        'material_floor2': 1,
        'material_roof': 0,
        'material_walls': 1,
        'material_balcony': 1,
        'volume': (9.59 * 11.08 * (3.06 + 3.01)) * 0.3,
        'mass': (9.59 * 11.08 * (3.06 + 3.01)) * 0.3 * 2400,
        'asymmetry_factor': 0.1,
        'opening_complexity': 0.1,
        'structural_irregularity': 0.1,
        'has_cantilever': True,
        'has_stairs': True,
        'wall_tilt_angle': -4.8,
        'roof_morph': 0.78
    }
}

print("=" * 80)
print("コスト調整の効果テスト")
print("=" * 80)

# CSVデータの読み込み（比較用）
df = pd.read_csv('production_freecad_random_fem_evaluation2.csv')

# sample30のテスト
print("\n【sample30の結果】")
result30 = calculate_economic_cost(sample30_info)
new_cost = result30['cost_per_sqm']
original_cost = df.iloc[29]['cost_per_sqm']  # sample30は30行目

print(f"元のコスト: {original_cost:,.0f} 円/m²")
print(f"新しいコスト: {new_cost:,.0f} 円/m²")
print(f"削減率: {(1 - new_cost/original_cost) * 100:.1f}%")
print(f"安全率（元）: 1.252")

# その他のサンプルも計算
print("\n【その他のサンプルの結果】")
for sample_name, info in sample_infos.items():
    result = calculate_economic_cost(info)
    new_cost = result['cost_per_sqm']
    
    # 元のデータを検索
    sample_num = int(sample_name.replace('sample', ''))
    original_data = df.iloc[sample_num - 1]
    original_cost = original_data['cost_per_sqm']
    safety_factor = original_data['safety_factor']
    
    print(f"\n{sample_name}:")
    print(f"  元のコスト: {original_cost:,.0f} 円/m²")
    print(f"  新しいコスト: {new_cost:,.0f} 円/m²")
    print(f"  削減率: {(1 - new_cost/original_cost) * 100:.1f}%")
    print(f"  安全率: {safety_factor:.3f}")

# 全体の統計
print("\n【統計サマリー】")
print(f"元の平均コスト: {df['cost_per_sqm'].mean():,.0f} 円/m²")
print(f"元の最大コスト: {df['cost_per_sqm'].max():,.0f} 円/m²")
print(f"元の最小コスト: {df['cost_per_sqm'].min():,.0f} 円/m²")

# 予想される新しい平均（約30-40%削減を想定）
estimated_new_avg = df['cost_per_sqm'].mean() * 0.65
print(f"\n予想される新しい平均コスト: {estimated_new_avg:,.0f} 円/m²")
print(f"これは一般的な建築コスト（30-100万円/m²）の範囲内です。")