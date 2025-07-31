#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sample30の詳細分析
"""

import pandas as pd
import numpy as np

# CSVファイルを読み込む
df = pd.read_csv('production_freecad_random_fem_evaluation2.csv')

# sample30のデータを取得（インデックスは29）
sample30 = df.iloc[29]

print("=" * 60)
print("sample30の詳細分析")
print("=" * 60)

print("\n【建物基本情報】")
print(f"床面積: {sample30['floor_area']:.1f} m²")
print(f"幅(Lx): {sample30['Lx']:.2f} m")
print(f"奥行(Ly): {sample30['Ly']:.2f} m")
print(f"1階高(H1): {sample30['H1']:.2f} m")
print(f"2階高(H2): {sample30['H2']:.2f} m")

print("\n【構造部材情報】")
print(f"柱幅(bc): {sample30['bc']} mm")
print(f"柱高(hc): {sample30['hc']} mm")
print(f"床厚(tf): {sample30['tf']} mm")
print(f"屋根厚(tr): {sample30['tr']} mm")
print(f"外壁厚(tw_ext): {sample30['tw_ext']} mm")

print("\n【材料構成】")
material_cols = ['material_columns', 'material_floor1', 'material_floor2', 
                'material_roof', 'material_walls', 'material_balcony']
materials = {col: sample30[col] for col in material_cols}
print("材料タイプ (0:コンクリート, 1:木材, 2:CLT):")
for part, mat in materials.items():
    part_name = part.replace('material_', '')
    print(f"  {part_name}: {int(mat)}")

print("\n【評価結果】")
print(f"建設コスト: {sample30['cost_per_sqm']:,.0f} 円/m² (289万円/m²)")
print(f"総コスト: {sample30['total_cost']:,.0f} 円")
print(f"安全率: {sample30['safety_factor']:.3f}")
print(f"CO2排出量: {sample30['co2_per_sqm']:.1f} kg-CO2/m²")

# 他のサンプルとの比較
print("\n【他サンプルとの比較】")
print(f"平均コスト: {df['cost_per_sqm'].mean():,.0f} 円/m²")
print(f"sample30のコスト倍率: {sample30['cost_per_sqm'] / df['cost_per_sqm'].mean():.2f}倍")

# 類似の安全率を持つサンプルとの比較
similar_safety = df[(df['safety_factor'] >= 1.0) & (df['safety_factor'] <= 1.5)]
print(f"\n安全率1.0-1.5の平均コスト: {similar_safety['cost_per_sqm'].mean():,.0f} 円/m²")
print(f"sample30の倍率: {sample30['cost_per_sqm'] / similar_safety['cost_per_sqm'].mean():.2f}倍")

# 柱サイズの影響を分析
print("\n【柱サイズの影響】")
avg_bc = df['bc'].mean()
avg_hc = df['hc'].mean()
print(f"平均柱幅: {avg_bc:.0f} mm")
print(f"平均柱高: {avg_hc:.0f} mm")
print(f"sample30の柱幅比: {sample30['bc'] / avg_bc:.2f}倍")
print(f"sample30の柱高比: {sample30['hc'] / avg_hc:.2f}倍")

# 断面積の比較
sample30_area = sample30['bc'] * sample30['hc']
avg_area = avg_bc * avg_hc
print(f"\n柱断面積:")
print(f"  平均: {avg_area:,.0f} mm²")
print(f"  sample30: {sample30_area:,.0f} mm²")
print(f"  比率: {sample30_area / avg_area:.2f}倍")

print("\n【問題の原因】")
print("柱断面積が平均の1.77倍と大きく、")
print("対数的増加でも依然としてコストへの影響が大きいと考えられます。")