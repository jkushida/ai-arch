#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
材料構成の詳細分析
"""

import pandas as pd
import numpy as np

# CSVファイルを読み込み
csv_path = '/Users/kushida2/Library/CloudStorage/GoogleDrive-kushida2008@gmail.com/マイドライブ/2025code/CadProg/new3/production_freecad_random_fem_evaluation2.csv'
df = pd.read_csv(csv_path)

# 成功したサンプルのみ
df_success = df[df['evaluation_status'] == 'success'].copy()

print("=== 材料構成の詳細分析 ===\n")

# 各材料の使用状況
material_cols = ['material_columns', 'material_floor1', 'material_floor2', 
                'material_roof', 'material_walls', 'material_balcony']

print("材料別の木材使用率:")
for col in material_cols:
    wood_count = df_success[col].sum()
    wood_rate = wood_count / len(df_success) * 100
    print(f"  {col}: {wood_count}/{len(df_success)} ({wood_rate:.1f}%)")

# 木材使用数の分布
df_success['wood_count'] = df_success[material_cols].sum(axis=1)
print("\n木材使用数の分布:")
wood_dist = df_success['wood_count'].value_counts().sort_index()
for count, freq in wood_dist.items():
    print(f"  {count}部材: {freq}件")

# 全コンクリート vs 全木造
all_concrete = df_success[df_success['wood_count'] == 0]
all_wood = df_success[df_success['wood_count'] == 6]

print(f"\n全コンクリート造: {len(all_concrete)}件")
print(f"全木造: {len(all_wood)}件")
print(f"混合構造: {len(df_success) - len(all_concrete) - len(all_wood)}件")

# 安全率との相関
print("\n木材使用数と安全率の相関:")
correlation = df_success['wood_count'].corr(df_success['safety_factor'])
print(f"相関係数: {correlation:.3f}")

# 木材使用数別の平均安全率
print("\n木材使用数別の平均安全率:")
for count in sorted(df_success['wood_count'].unique()):
    subset = df_success[df_success['wood_count'] == count]
    avg_safety = subset['safety_factor'].mean()
    print(f"  {count}部材: {avg_safety:.2f} (n={len(subset)})")

# 柱が木造の場合の詳細
print("\n=== 柱材料による詳細分析 ===")
wood_columns = df_success[df_success['material_columns'] == 1]
concrete_columns = df_success[df_success['material_columns'] == 0]

print(f"\n木造柱のサンプル:")
for idx, row in wood_columns.iterrows():
    print(f"  サンプル{idx+1}: 安全率={row['safety_factor']:.2f}, "
          f"木材数={row['wood_count']}, コスト={row['cost_per_sqm']:,.0f}円/m²")

print(f"\nコンクリート柱のサンプル（上位5件）:")
for idx, row in concrete_columns.nlargest(5, 'safety_factor').iterrows():
    print(f"  サンプル{idx+1}: 安全率={row['safety_factor']:.2f}, "
          f"木材数={row['wood_count']}, コスト={row['cost_per_sqm']:,.0f}円/m²")

# 最も安全率が高いサンプル
print("\n=== 安全率上位サンプル ===")
top_samples = df_success.nlargest(5, 'safety_factor')
for idx, row in top_samples.iterrows():
    print(f"\nサンプル{idx+1}:")
    print(f"  安全率: {row['safety_factor']:.2f}")
    print(f"  材料構成: ", end="")
    for col in material_cols:
        mat = "木" if row[col] == 1 else "コ"
        print(f"{col.split('_')[1]}={mat}, ", end="")
    print(f"\n  コスト: {row['cost_per_sqm']:,.0f} 円/m²")
    print(f"  CO2: {row['co2_per_sqm']:.1f} kg-CO2/m²")