#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
production_freecad_random_fem_evaluation2.csv の分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# 日本語フォントの設定
plt.rcParams['font.family'] = 'Hiragino Sans'
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro', 'Yu Gothic', 'Meirio']
plt.rcParams['axes.unicode_minus'] = False

# CSVファイルを読み込み
csv_path = '/Users/kushida2/Library/CloudStorage/GoogleDrive-kushida2008@gmail.com/マイドライブ/2025code/CadProg/new3/production_freecad_random_fem_evaluation2.csv'
df = pd.read_csv(csv_path)

print("=== CSVファイル分析 ===\n")
print(f"総レコード数: {len(df)}")

# 成功したサンプルのみを抽出
df_success = df[df['evaluation_status'] == 'success'].copy()
print(f"成功サンプル数: {len(df_success)}")
print(f"成功率: {len(df_success)/len(df)*100:.1f}%\n")

# 材料使用数を計算（木材の数）
material_cols = ['material_columns', 'material_floor1', 'material_floor2', 
                'material_roof', 'material_walls', 'material_balcony']
df_success['wood_count'] = df_success[material_cols].sum(axis=1)

# 材料構成による分類
df_success['material_type'] = df_success['wood_count'].apply(
    lambda x: 'コンクリート造' if x == 0 else '木造' if x == 6 else '混合構造'
)

print("=== 材料構成の分布 ===")
material_dist = df_success['material_type'].value_counts()
for mat_type, count in material_dist.items():
    print(f"{mat_type}: {count}件 ({count/len(df_success)*100:.1f}%)")

print("\n=== 安全率の統計 ===")
print(f"全体の平均安全率: {df_success['safety_factor'].mean():.2f}")
print(f"標準偏差: {df_success['safety_factor'].std():.2f}")
print(f"最小値: {df_success['safety_factor'].min():.2f}")
print(f"最大値: {df_success['safety_factor'].max():.2f}")

# 材料タイプ別の安全率
print("\n=== 材料タイプ別の安全率 ===")
for mat_type in ['コンクリート造', '木造', '混合構造']:
    subset = df_success[df_success['material_type'] == mat_type]
    if len(subset) > 0:
        print(f"\n{mat_type}:")
        print(f"  サンプル数: {len(subset)}")
        print(f"  平均安全率: {subset['safety_factor'].mean():.2f}")
        print(f"  標準偏差: {subset['safety_factor'].std():.2f}")
        print(f"  最小値: {subset['safety_factor'].min():.2f}")
        print(f"  最大値: {subset['safety_factor'].max():.2f}")

# 木造とコンクリート造の比較
concrete = df_success[df_success['material_type'] == 'コンクリート造']
wood = df_success[df_success['material_type'] == '木造']

if len(concrete) > 0 and len(wood) > 0:
    ratio = wood['safety_factor'].mean() / concrete['safety_factor'].mean()
    print(f"\n木造/コンクリート造の平均安全率比: {ratio:.2f}")

# コストとCO2の分析
print("\n=== コストとCO2排出量の統計 ===")
for mat_type in ['コンクリート造', '木造', '混合構造']:
    subset = df_success[df_success['material_type'] == mat_type]
    if len(subset) > 0:
        print(f"\n{mat_type}:")
        print(f"  平均コスト: {subset['cost_per_sqm'].mean():,.0f} 円/m²")
        print(f"  平均CO2: {subset['co2_per_sqm'].mean():.1f} kg-CO2/m²")

# 可視化
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. 安全率のヒストグラム（材料タイプ別）
ax1 = axes[0, 0]
for mat_type, color in zip(['コンクリート造', '木造', '混合構造'], ['blue', 'brown', 'green']):
    subset = df_success[df_success['material_type'] == mat_type]
    if len(subset) > 0:
        ax1.hist(subset['safety_factor'], bins=20, alpha=0.5, label=mat_type, color=color)
ax1.set_xlabel('安全率')
ax1.set_ylabel('頻度')
ax1.set_title('材料タイプ別の安全率分布')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. 安全率の箱ひげ図
ax2 = axes[0, 1]
material_types = []
safety_factors = []
for mat_type in ['コンクリート造', '木造', '混合構造']:
    subset = df_success[df_success['material_type'] == mat_type]
    if len(subset) > 0:
        material_types.append(mat_type)
        safety_factors.append(subset['safety_factor'].values)

if safety_factors:
    ax2.boxplot(safety_factors, labels=material_types)
    ax2.set_ylabel('安全率')
    ax2.set_title('材料タイプ別の安全率分布（箱ひげ図）')
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=2.0, color='red', linestyle='--', label='推奨安全率')
    ax2.legend()

# 3. コスト vs 安全率（材料タイプ別）
ax3 = axes[1, 0]
colors = {'コンクリート造': 'blue', '木造': 'brown', '混合構造': 'green'}
for mat_type in colors:
    subset = df_success[df_success['material_type'] == mat_type]
    if len(subset) > 0:
        ax3.scatter(subset['safety_factor'], subset['cost_per_sqm'], 
                   alpha=0.6, label=mat_type, color=colors[mat_type])
ax3.set_xlabel('安全率')
ax3.set_ylabel('コスト (円/m²)')
ax3.set_title('安全率 vs コスト')
ax3.legend()
ax3.grid(True, alpha=0.3)
ax3.axvline(x=2.0, color='red', linestyle='--', alpha=0.5)

# 4. CO2 vs 安全率（材料タイプ別）
ax4 = axes[1, 1]
for mat_type in colors:
    subset = df_success[df_success['material_type'] == mat_type]
    if len(subset) > 0:
        ax4.scatter(subset['safety_factor'], subset['co2_per_sqm'], 
                   alpha=0.6, label=mat_type, color=colors[mat_type])
ax4.set_xlabel('安全率')
ax4.set_ylabel('CO2排出量 (kg-CO2/m²)')
ax4.set_title('安全率 vs CO2排出量')
ax4.legend()
ax4.grid(True, alpha=0.3)
ax4.axvline(x=2.0, color='red', linestyle='--', alpha=0.5)

plt.tight_layout()
plt.savefig('safety_material_analysis.png', dpi=150, bbox_inches='tight')
print("\n✅ グラフを保存しました: safety_material_analysis.png")

# 詳細な統計情報
print("\n=== 柱材料による影響分析 ===")
concrete_columns = df_success[df_success['material_columns'] == 0]
wood_columns = df_success[df_success['material_columns'] == 1]

print(f"コンクリート柱: {len(concrete_columns)}件, 平均安全率: {concrete_columns['safety_factor'].mean():.2f}")
print(f"木造柱: {len(wood_columns)}件, 平均安全率: {wood_columns['safety_factor'].mean():.2f}")

if len(concrete_columns) > 0 and len(wood_columns) > 0:
    ratio = wood_columns['safety_factor'].mean() / concrete_columns['safety_factor'].mean()
    print(f"柱材料による安全率比（木造/コンクリート）: {ratio:.2f}")

# 安全率2.0以上のサンプル
safe_samples = df_success[df_success['safety_factor'] >= 2.0]
print(f"\n安全率2.0以上のサンプル: {len(safe_samples)}件 ({len(safe_samples)/len(df_success)*100:.1f}%)")

# 材料タイプ別の安全率2.0以上の割合
print("\n=== 材料タイプ別の安全率2.0以上の割合 ===")
for mat_type in ['コンクリート造', '木造', '混合構造']:
    subset = df_success[df_success['material_type'] == mat_type]
    if len(subset) > 0:
        safe_count = len(subset[subset['safety_factor'] >= 2.0])
        print(f"{mat_type}: {safe_count}/{len(subset)} ({safe_count/len(subset)*100:.1f}%)")