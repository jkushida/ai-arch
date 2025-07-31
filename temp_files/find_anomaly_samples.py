#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全率>3.0でコストが異常に低いサンプルを特定
"""

import pandas as pd
import numpy as np

# CSVファイルを読み込む
df = pd.read_csv('production_freecad_random_fem_evaluation2.csv')

print("=" * 80)
print("安全率>3.0でコストが異常に低いサンプルの調査")
print("=" * 80)

# 安全率>3.0のサンプルを抽出
high_safety = df[df['safety_factor'] > 3.0]
print(f"\n安全率>3.0のサンプル数: {len(high_safety)}")

# その中でコスト<2,000,000円/m²のサンプル
anomaly_samples = high_safety[high_safety['cost_per_sqm'] < 2000000]
print(f"その中でコスト<2,000,000円/m²のサンプル数: {len(anomaly_samples)}")

if len(anomaly_samples) > 0:
    print("\n【異常サンプルの詳細】")
    for idx, row in anomaly_samples.iterrows():
        print(f"\n--- Sample {idx+1} (行{idx+2}) ---")
        print(f"安全率: {row['safety_factor']:.3f}")
        print(f"コスト: {row['cost_per_sqm']:,.0f} 円/m²")
        print(f"材料: {row['design_pattern']}")
        print(f"構造パラメータ:")
        print(f"  柱: {row['bc']}x{row['hc']}mm (面積: {row['bc']*row['hc']:,}mm²)")
        print(f"  床版厚: {row['tf']}mm")
        print(f"  屋根版厚: {row['tr']}mm")
        print(f"  外壁厚: {row['tw_ext']}mm")
        print(f"  階高: H1={row['H1']}m, H2={row['H2']}m")
        print(f"  建物サイズ: {row['Lx']}x{row['Ly']}m")
        print(f"  床面積: {row['floor_area']:.1f}m²")
        print(f"  材料詳細:")
        print(f"    柱: {['RC', '木材', 'CLT'][int(row['material_columns'])]}")
        print(f"    床: {['RC', '木材', 'CLT'][int(row['material_floor1'])]}")
        print(f"    屋根: {['RC', '木材', 'CLT'][int(row['material_roof'])]}")

# 正常な高安全率サンプルとの比較
normal_high_safety = high_safety[high_safety['cost_per_sqm'] >= 2000000]
if len(normal_high_safety) > 0:
    print(f"\n\n【正常な高安全率サンプル（コスト≥2,000,000円/m²）の統計】")
    print(f"サンプル数: {len(normal_high_safety)}")
    print(f"平均安全率: {normal_high_safety['safety_factor'].mean():.3f}")
    print(f"平均コスト: {normal_high_safety['cost_per_sqm'].mean():,.0f} 円/m²")
    print(f"平均柱断面積: {(normal_high_safety['bc'] * normal_high_safety['hc']).mean():,.0f} mm²")

# 柱断面積とコストの関係を確認
print("\n\n【全サンプルの柱断面積分析】")
df['column_area'] = df['bc'] * df['hc']

# 柱断面積の範囲別にグループ化
area_ranges = [(0, 300000), (300000, 500000), (500000, 700000), (700000, 1000000)]
for low, high in area_ranges:
    group = df[(df['column_area'] >= low) & (df['column_area'] < high)]
    if len(group) > 0:
        print(f"\n柱断面積 {low/1000:.0f}k-{high/1000:.0f}k mm²:")
        print(f"  サンプル数: {len(group)}")
        print(f"  平均安全率: {group['safety_factor'].mean():.3f}")
        print(f"  平均コスト: {group['cost_per_sqm'].mean():,.0f} 円/m²")
        # 安全率>3のサンプルがあるか
        high_safety_group = group[group['safety_factor'] > 3.0]
        if len(high_safety_group) > 0:
            print(f"  安全率>3.0のサンプル: {len(high_safety_group)}件")
            print(f"    最低コスト: {high_safety_group['cost_per_sqm'].min():,.0f} 円/m²")
            print(f"    最高コスト: {high_safety_group['cost_per_sqm'].max():,.0f} 円/m²")

print("\n" + "=" * 80)