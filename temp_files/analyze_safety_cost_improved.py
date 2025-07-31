#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改善後の安全率とコストの相関を分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# 日本語フォントの設定
plt.rcParams['font.family'] = 'Hiragino Sans'
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro']
plt.rcParams['axes.unicode_minus'] = False

# CSVファイルを読み込む
df = pd.read_csv('production_freecad_random_fem_evaluation2.csv')

# 成功データのみを分析対象とする
df_success = df[df['evaluation_status'] == 'success'].copy()

print("=" * 80)
print("改善後の安全率とコストの相関分析")
print("=" * 80)

# 1. 基本統計
print(f"\n総サンプル数: {len(df_success)}")

# 2. 柱サイズと安全率・コストの関係
df_success['avg_column_size'] = (df_success['bc'] + df_success['hc']) / 2
df_success['avg_slab_thickness'] = (df_success['tf'] + df_success['tr']) / 2

# 3. 相関分析
print("\n【相関分析】")
print(f"安全率とコストの相関: {df_success['safety_factor'].corr(df_success['cost_per_sqm']):.3f}")
print(f"柱サイズとコストの相関: {df_success['avg_column_size'].corr(df_success['cost_per_sqm']):.3f}")
print(f"柱サイズと安全率の相関: {df_success['avg_column_size'].corr(df_success['safety_factor']):.3f}")
print(f"スラブ厚とコストの相関: {df_success['avg_slab_thickness'].corr(df_success['cost_per_sqm']):.3f}")

# 4. 材料別の分析
df_success['material_type'] = df_success.apply(
    lambda row: 'RC造' if row['material_columns'] == 0 else 
                ('CLT造' if row['material_columns'] == 2 else '木造'), axis=1)

print("\n【材料別平均値】")
for mat_type in ['RC造', '木造', 'CLT造']:
    mat_df = df_success[df_success['material_type'] == mat_type]
    if len(mat_df) > 0:
        print(f"\n{mat_type}:")
        print(f"  サンプル数: {len(mat_df)}")
        print(f"  平均コスト: {mat_df['cost_per_sqm'].mean():,.0f} 円/m²")
        print(f"  平均安全率: {mat_df['safety_factor'].mean():.2f}")
        print(f"  平均柱サイズ: {mat_df['avg_column_size'].mean():.0f} mm")

# グラフ作成
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. 安全率 vs コスト（改善後）
ax1 = axes[0, 0]
colors = {'RC造': 'red', '木造': 'green', 'CLT造': 'purple'}
for mat_type, color in colors.items():
    mat_df = df_success[df_success['material_type'] == mat_type]
    if len(mat_df) > 0:
        ax1.scatter(mat_df['safety_factor'], mat_df['cost_per_sqm'], 
                   color=color, alpha=0.6, label=mat_type, s=100)

# 回帰直線を追加
x = df_success['safety_factor']
y = df_success['cost_per_sqm']
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
ax1.plot(x, slope*x + intercept, 'b--', alpha=0.8, 
         label=f'回帰直線 (R²={r_value**2:.3f})')

ax1.set_xlabel('安全率')
ax1.set_ylabel('建設コスト (円/m²)')
ax1.set_title(f'安全率 vs 建設コスト (相関: {x.corr(y):.3f})')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. 柱サイズ vs コスト
ax2 = axes[0, 1]
ax2.scatter(df_success['avg_column_size'], df_success['cost_per_sqm'], 
           alpha=0.6, s=100)
ax2.set_xlabel('平均柱サイズ (mm)')
ax2.set_ylabel('建設コスト (円/m²)')
ax2.set_title(f"柱サイズ vs コスト (相関: {df_success['avg_column_size'].corr(df_success['cost_per_sqm']):.3f})")
ax2.grid(True, alpha=0.3)

# 3. 柱サイズ vs 安全率
ax3 = axes[1, 0]
ax3.scatter(df_success['avg_column_size'], df_success['safety_factor'], 
           alpha=0.6, s=100)
ax3.set_xlabel('平均柱サイズ (mm)')
ax3.set_ylabel('安全率')
ax3.set_title(f"柱サイズ vs 安全率 (相関: {df_success['avg_column_size'].corr(df_success['safety_factor']):.3f})")
ax3.grid(True, alpha=0.3)

# 4. 安全率区間別のコスト分布
ax4 = axes[1, 1]
df_success['safety_category'] = pd.cut(df_success['safety_factor'], 
                                      bins=[0, 1.0, 1.5, 2.0, 10], 
                                      labels=['1.0未満', '1.0-1.5', '1.5-2.0', '2.0以上'])
df_success.boxplot(column='cost_per_sqm', by='safety_category', ax=ax4)
ax4.set_xlabel('安全率区間')
ax4.set_ylabel('建設コスト (円/m²)')
ax4.set_title('安全率区間別のコスト分布')
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('safety_cost_improved_analysis.png', dpi=150, bbox_inches='tight')
print(f"\n✅ グラフを保存しました: safety_cost_improved_analysis.png")

# 詳細統計
print("\n【安全率区間別の詳細】")
for category in ['1.0未満', '1.0-1.5', '1.5-2.0', '2.0以上']:
    cat_df = df_success[df_success['safety_category'] == category]
    if len(cat_df) > 0:
        print(f"\n{category}:")
        print(f"  サンプル数: {len(cat_df)}")
        print(f"  平均コスト: {cat_df['cost_per_sqm'].mean():,.0f} 円/m²")
        print(f"  平均柱サイズ: {cat_df['avg_column_size'].mean():.0f} mm")
        print(f"  平均スラブ厚: {cat_df['avg_slab_thickness'].mean():.0f} mm")