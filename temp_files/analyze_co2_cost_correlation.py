#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CO2排出量とコストの相関分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# 日本語フォントの設定
plt.rcParams['font.family'] = 'Hiragino Sans'
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro', 'Yu Gothic', 'Meirio']
plt.rcParams['axes.unicode_minus'] = False

# CSVファイルを読み込む
df = pd.read_csv('production_freecad_random_fem_evaluation2.csv')

# 成功したサンプルのみを抽出
df_success = df[df['evaluation_status'] == 'success'].copy()

print("=" * 60)
print("CO2排出量とコストの相関分析")
print("=" * 60)
print(f"総サンプル数: {len(df)}")
print(f"成功サンプル数: {len(df_success)}")
print()

# 全体の相関係数を計算
overall_corr = df_success['cost_per_sqm'].corr(df_success['co2_per_sqm'])
print(f"【全体の相関係数】")
print(f"  CO2とコストの相関: {overall_corr:.4f}")

# p値を計算
_, p_value = stats.pearsonr(df_success['cost_per_sqm'], df_success['co2_per_sqm'])
print(f"  p値: {p_value:.6f}")
if p_value < 0.05:
    print("  → 統計的に有意な相関あり")
else:
    print("  → 統計的に有意な相関なし")
print()

# 材料使用数を計算（木材の合計数）
df_success['wood_count'] = (
    df_success['material_columns'] + 
    df_success['material_floor1'] + 
    df_success['material_floor2'] + 
    df_success['material_roof'] + 
    df_success['material_walls'] + 
    df_success['material_balcony']
)

# 材料タイプで分類
df_concrete = df_success[df_success['wood_count'] == 0]
df_mixed = df_success[(df_success['wood_count'] >= 1) & (df_success['wood_count'] <= 5)]
df_wood = df_success[df_success['wood_count'] == 6]

print("【材料別の相関係数】")
if len(df_concrete) > 3:
    corr_concrete = df_concrete['cost_per_sqm'].corr(df_concrete['co2_per_sqm'])
    print(f"  コンクリート造 (n={len(df_concrete)}): {corr_concrete:.4f}")
else:
    print(f"  コンクリート造: サンプル数不足 (n={len(df_concrete)})")

if len(df_mixed) > 3:
    corr_mixed = df_mixed['cost_per_sqm'].corr(df_mixed['co2_per_sqm'])
    print(f"  混合構造 (n={len(df_mixed)}): {corr_mixed:.4f}")
else:
    print(f"  混合構造: サンプル数不足 (n={len(df_mixed)})")

if len(df_wood) > 3:
    corr_wood = df_wood['cost_per_sqm'].corr(df_wood['co2_per_sqm'])
    print(f"  木造 (n={len(df_wood)}): {corr_wood:.4f}")
else:
    print(f"  木造: サンプル数不足 (n={len(df_wood)})")
print()

# 基本統計量
print("【基本統計量】")
print("コスト (円/m²):")
print(f"  平均: {df_success['cost_per_sqm'].mean():,.0f}")
print(f"  標準偏差: {df_success['cost_per_sqm'].std():,.0f}")
print(f"  最小: {df_success['cost_per_sqm'].min():,.0f}")
print(f"  最大: {df_success['cost_per_sqm'].max():,.0f}")
print()

print("CO2排出量 (kg-CO2/m²):")
print(f"  平均: {df_success['co2_per_sqm'].mean():.1f}")
print(f"  標準偏差: {df_success['co2_per_sqm'].std():.1f}")
print(f"  最小: {df_success['co2_per_sqm'].min():.1f}")
print(f"  最大: {df_success['co2_per_sqm'].max():.1f}")
print()

# 散布図を作成
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

# 1. 全体の散布図（材料別色分け）
scatter = ax1.scatter(
    df_success['co2_per_sqm'], 
    df_success['cost_per_sqm'],
    c=df_success['wood_count'],
    cmap='RdYlBu_r',
    alpha=0.6,
    s=100
)
ax1.set_xlabel('CO2排出量 (kg-CO2/m²)')
ax1.set_ylabel('建設コスト (円/m²)')
ax1.set_title(f'CO2排出量 vs 建設コスト\n相関係数: {overall_corr:.3f}')
ax1.grid(True, alpha=0.3)

# カラーバー
cbar = plt.colorbar(scatter, ax=ax1)
cbar.set_label('木材使用数 (0:RC造, 6:木造)')

# 回帰直線を追加
z = np.polyfit(df_success['co2_per_sqm'], df_success['cost_per_sqm'], 1)
p = np.poly1d(z)
x_line = np.linspace(df_success['co2_per_sqm'].min(), df_success['co2_per_sqm'].max(), 100)
ax1.plot(x_line, p(x_line), "r--", alpha=0.8, linewidth=2, label=f'y = {z[0]:.0f}x + {z[1]:.0f}')
ax1.legend()

# 2. 材料別の散布図
ax2.scatter(df_concrete['co2_per_sqm'], df_concrete['cost_per_sqm'], 
           label=f'RC造 (n={len(df_concrete)})', alpha=0.6, s=100, color='red')
ax2.scatter(df_mixed['co2_per_sqm'], df_mixed['cost_per_sqm'], 
           label=f'混合構造 (n={len(df_mixed)})', alpha=0.6, s=100, color='green')
ax2.scatter(df_wood['co2_per_sqm'], df_wood['cost_per_sqm'], 
           label=f'木造 (n={len(df_wood)})', alpha=0.6, s=100, color='blue')

ax2.set_xlabel('CO2排出量 (kg-CO2/m²)')
ax2.set_ylabel('建設コスト (円/m²)')
ax2.set_title('材料別のCO2排出量 vs 建設コスト')
ax2.grid(True, alpha=0.3)
ax2.legend()

plt.tight_layout()
plt.savefig('co2_cost_correlation_analysis.png', dpi=150, bbox_inches='tight')
print(f"\n✅ グラフを保存しました: co2_cost_correlation_analysis.png")

# 相関の強さの解釈
print("\n【相関の解釈】")
abs_corr = abs(overall_corr)
if abs_corr >= 0.7:
    strength = "強い"
elif abs_corr >= 0.4:
    strength = "中程度の"
elif abs_corr >= 0.2:
    strength = "弱い"
else:
    strength = "ほとんどない"

if overall_corr > 0:
    direction = "正の"
else:
    direction = "負の"

print(f"CO2排出量とコストには{direction}{strength}相関があります。")

if overall_corr > 0.7:
    print("→ CO2排出量が多い建物ほど、建設コストも高くなる傾向が強いです。")
elif overall_corr > 0.4:
    print("→ CO2排出量と建設コストには一定の関連性がありますが、他の要因も影響しています。")
else:
    print("→ CO2排出量と建設コストの関係は弱く、他の要因が大きく影響しています。")