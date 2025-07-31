#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
柱材料によるコスト分析
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

# 成功したサンプルのみ
df_success = df[df['evaluation_status'] == 'success'].copy()

print("=== 柱材料によるコスト分析 ===\n")

# 柱材料別の基本統計
concrete_columns = df_success[df_success['material_columns'] == 0]
wood_columns = df_success[df_success['material_columns'] == 1]

print("【コンクリート柱】")
print(f"サンプル数: {len(concrete_columns)}")
print(f"平均コスト: {concrete_columns['cost_per_sqm'].mean():,.0f} 円/m²")
print(f"標準偏差: {concrete_columns['cost_per_sqm'].std():,.0f} 円/m²")
print(f"最小値: {concrete_columns['cost_per_sqm'].min():,.0f} 円/m²")
print(f"最大値: {concrete_columns['cost_per_sqm'].max():,.0f} 円/m²")

print("\n【木造柱】")
print(f"サンプル数: {len(wood_columns)}")
print(f"平均コスト: {wood_columns['cost_per_sqm'].mean():,.0f} 円/m²")
print(f"標準偏差: {wood_columns['cost_per_sqm'].std():,.0f} 円/m²")
print(f"最小値: {wood_columns['cost_per_sqm'].min():,.0f} 円/m²")
print(f"最大値: {wood_columns['cost_per_sqm'].max():,.0f} 円/m²")

# コスト差
cost_diff = wood_columns['cost_per_sqm'].mean() - concrete_columns['cost_per_sqm'].mean()
cost_ratio = wood_columns['cost_per_sqm'].mean() / concrete_columns['cost_per_sqm'].mean()

print(f"\n【コスト比較】")
print(f"平均コスト差（木造 - コンクリート）: {cost_diff:,.0f} 円/m²")
print(f"コスト比（木造/コンクリート）: {cost_ratio:.2f}")

# 柱サイズも考慮した分析
print("\n=== 柱サイズ別の分析 ===")
print("\n【コンクリート柱の詳細】")
for idx, row in concrete_columns.iterrows():
    print(f"サンプル{idx+1}: bc={row['bc']}mm, hc={row['hc']}mm, "
          f"コスト={row['cost_per_sqm']:,.0f}円/m², 安全率={row['safety_factor']:.2f}")

print("\n【木造柱の詳細】")
for idx, row in wood_columns.iterrows():
    print(f"サンプル{idx+1}: bc={row['bc']}mm, hc={row['hc']}mm, "
          f"コスト={row['cost_per_sqm']:,.0f}円/m², 安全率={row['safety_factor']:.2f}")

# 柱断面積との相関
df_success['column_area'] = df_success['bc'] * df_success['hc'] / 1000000  # m²
concrete_columns = df_success[df_success['material_columns'] == 0]  # 再取得
wood_columns = df_success[df_success['material_columns'] == 1]      # 再取得
concrete_area_avg = concrete_columns['column_area'].mean()
wood_area_avg = wood_columns['column_area'].mean()

print(f"\n【平均柱断面積】")
print(f"コンクリート柱: {concrete_area_avg:.3f} m²")
print(f"木造柱: {wood_area_avg:.3f} m²")
print(f"断面積比（木造/コンクリート）: {wood_area_avg/concrete_area_avg:.2f}")

# CO2排出量の比較
print("\n=== CO2排出量の比較 ===")
print(f"コンクリート柱 平均CO2: {concrete_columns['co2_per_sqm'].mean():.1f} kg-CO2/m²")
print(f"木造柱 平均CO2: {wood_columns['co2_per_sqm'].mean():.1f} kg-CO2/m²")
co2_diff = wood_columns['co2_per_sqm'].mean() - concrete_columns['co2_per_sqm'].mean()
print(f"CO2差（木造 - コンクリート）: {co2_diff:.1f} kg-CO2/m²")

# 可視化
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. コストの箱ひげ図
ax1 = axes[0, 0]
data_cost = [concrete_columns['cost_per_sqm'].values, wood_columns['cost_per_sqm'].values]
ax1.boxplot(data_cost, tick_labels=['コンクリート柱', '木造柱'])
ax1.set_ylabel('コスト (円/m²)')
ax1.set_title('柱材料別のコスト分布')
ax1.grid(True, alpha=0.3)

# 2. 安全率 vs コスト
ax2 = axes[0, 1]
ax2.scatter(concrete_columns['safety_factor'], concrete_columns['cost_per_sqm'], 
           label='コンクリート柱', alpha=0.7, s=100, color='blue')
ax2.scatter(wood_columns['safety_factor'], wood_columns['cost_per_sqm'], 
           label='木造柱', alpha=0.7, s=100, color='brown')
ax2.set_xlabel('安全率')
ax2.set_ylabel('コスト (円/m²)')
ax2.set_title('安全率 vs コスト')
ax2.legend()
ax2.grid(True, alpha=0.3)
ax2.axvline(x=2.0, color='red', linestyle='--', alpha=0.5, label='推奨安全率')

# 3. 柱断面積 vs コスト
ax3 = axes[1, 0]
ax3.scatter(concrete_columns['column_area'], concrete_columns['cost_per_sqm'], 
           label='コンクリート柱', alpha=0.7, s=100, color='blue')
ax3.scatter(wood_columns['column_area'], wood_columns['cost_per_sqm'], 
           label='木造柱', alpha=0.7, s=100, color='brown')
ax3.set_xlabel('柱断面積 (m²)')
ax3.set_ylabel('コスト (円/m²)')
ax3.set_title('柱断面積 vs コスト')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4. CO2の箱ひげ図
ax4 = axes[1, 1]
data_co2 = [concrete_columns['co2_per_sqm'].values, wood_columns['co2_per_sqm'].values]
ax4.boxplot(data_co2, tick_labels=['コンクリート柱', '木造柱'])
ax4.set_ylabel('CO2排出量 (kg-CO2/m²)')
ax4.set_title('柱材料別のCO2排出量分布')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('column_cost_analysis.png', dpi=150, bbox_inches='tight')
print("\n✅ グラフを保存しました: column_cost_analysis.png")

# 材料単価の確認
print("\n=== 材料単価の設定値（参考） ===")
print("generate_building_fem_analyze.pyより：")
print("  コンクリート: 20,000 円/m³")
print("  木材: 50,000 円/m³")
print("  ※木材の方が単価は高いが、密度が低いため総重量が減少")