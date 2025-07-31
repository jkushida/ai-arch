#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
過剰カテゴリサンプルの詳細分析
"""

import pandas as pd
import numpy as np

# CSVファイルを読み込む
df = pd.read_csv('production_freecad_random_fem_evaluation2.csv')

print("=" * 80)
print("過剰カテゴリサンプルの詳細分析")
print("=" * 80)

# 過剰カテゴリのサンプル（安全率 > 3.0）
excessive_samples = df[df['safety_factor'] > 3.0]
print(f"\n過剰カテゴリのサンプル数: {len(excessive_samples)}")

# sample21とsample37の詳細
sample21 = df.iloc[20]  # 0-indexed なので行22は20
sample37 = df.iloc[36]  # 行38は36

print("\n【Sample21の詳細】")
print(f"安全率: {sample21['safety_factor']:.3f}")
print(f"コスト: {sample21['cost_per_sqm']:,.0f} 円/m²")
print(f"材料: 木造中心")
print(f"構造サイズ:")
print(f"  柱: {sample21['bc']} x {sample21['hc']} mm")
print(f"  床版厚: {sample21['tf']} mm")
print(f"  屋根版厚: {sample21['tr']} mm")
print(f"  外壁厚: {sample21['tw_ext']} mm")
print(f"床面積: {sample21['floor_area']:.1f} m²")
print(f"建物サイズ: {sample21['Lx']:.1f} x {sample21['Ly']:.1f} m")
print(f"階高: H1={sample21['H1']:.1f}m, H2={sample21['H2']:.1f}m")

print("\n【Sample37の詳細】")
print(f"安全率: {sample37['safety_factor']:.3f}")
print(f"コスト: {sample37['cost_per_sqm']:,.0f} 円/m²")
print(f"材料: RC中心")
print(f"構造サイズ:")
print(f"  柱: {sample37['bc']} x {sample37['hc']} mm")
print(f"  床版厚: {sample37['tf']} mm")
print(f"  屋根版厚: {sample37['tr']} mm")
print(f"  外壁厚: {sample37['tw_ext']} mm")
print(f"床面積: {sample37['floor_area']:.1f} m²")
print(f"建物サイズ: {sample37['Lx']:.1f} x {sample37['Ly']:.1f} m")
print(f"階高: H1={sample37['H1']:.1f}m, H2={sample37['H2']:.1f}m")

# 構造体積の比較
vol_21 = (sample21['bc'] * sample21['hc'] * (sample21['H1'] + sample21['H2']) * 1000 * 4 +  # 柱
          sample21['tf'] * sample21['floor_area'] * 1000 * 1000 +  # 床版
          sample21['tr'] * sample21['floor_area'] * 1000 * 500)    # 屋根版（半分）
vol_37 = (sample37['bc'] * sample37['hc'] * (sample37['H1'] + sample37['H2']) * 1000 * 4 +  # 柱
          sample37['tf'] * sample37['floor_area'] * 1000 * 1000 +  # 床版
          sample37['tr'] * sample37['floor_area'] * 1000 * 500)    # 屋根版（半分）

print(f"\n【構造体積の推定】")
print(f"Sample21: {vol_21/1e9:.3f} m³")
print(f"Sample37: {vol_37/1e9:.3f} m³")

# 高安全率サンプル（2.5以上）との比較
high_safety = df[df['safety_factor'] >= 2.5]
print(f"\n【高安全率サンプル（安全率≥2.5）の統計】")
print(f"サンプル数: {len(high_safety)}")

# 材料別の平均
for mat in [0, 1, 2]:
    mat_name = ['コンクリート', '木材', 'CLT'][mat]
    mat_df = high_safety[high_safety['material_columns'] == mat]
    if len(mat_df) > 0:
        print(f"\n{mat_name} (n={len(mat_df)}):")
        print(f"  平均安全率: {mat_df['safety_factor'].mean():.3f}")
        print(f"  平均コスト: {mat_df['cost_per_sqm'].mean():,.0f} 円/m²")
        print(f"  平均柱サイズ: {mat_df['bc'].mean():.0f} x {mat_df['hc'].mean():.0f} mm")

# 構造サイズとコストの関係
print("\n【構造サイズ分析】")
print("高安全率サンプルの柱断面積とコストの関係:")
high_safety['column_area'] = high_safety['bc'] * high_safety['hc']
for index, row in high_safety.iterrows():
    print(f"  安全率{row['safety_factor']:.2f}: 柱{row['bc']}x{row['hc']}mm (面積{row['column_area']:,}mm²), コスト{row['cost_per_sqm']:,.0f}円/m²")

# 問題の特定
print("\n【問題の特定】")
print("Sample21が異常に低コストな理由:")
print("1. 低天井設計（H1=2.68m, H2=2.61m）で構造体積が小さい")
print("2. 木造のため材料単価が低い")
print("3. 現在のコスト計算が構造体積を適切に反映していない可能性")
print("4. 高強度を実現するための特殊工法のコストが計上されていない")

print("\n" + "=" * 80)