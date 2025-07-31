#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全率とCO2排出量の相関分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from scipy import stats
matplotlib.use('Agg')

# 日本語フォントの設定
plt.rcParams['font.family'] = 'Hiragino Sans'
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro', 'Yu Gothic', 'Meirio']
plt.rcParams['axes.unicode_minus'] = False

# CSVファイルの読み込み
csv_file = "/Users/kushida2/Library/CloudStorage/GoogleDrive-kushida2008@gmail.com/マイドライブ/2025code/CadProg/new3/production_freecad_random_fem_evaluation2.csv"
df = pd.read_csv(csv_file)

print("=== 安全率とCO2排出量の相関分析 ===\n")

# 基本統計
print("【基本統計】")
print(f"安全率 - 平均: {df['safety_factor'].mean():.3f}, 標準偏差: {df['safety_factor'].std():.3f}")
print(f"CO2排出量 - 平均: {df['co2_per_sqm'].mean():.1f}, 標準偏差: {df['co2_per_sqm'].std():.1f}")
print()

# 相関係数の計算
correlation = df['safety_factor'].corr(df['co2_per_sqm'])
print(f"【相関係数】")
print(f"ピアソン相関係数: {correlation:.4f}")

# スピアマンの順位相関係数も計算
spearman_corr = stats.spearmanr(df['safety_factor'], df['co2_per_sqm'])
print(f"スピアマン順位相関係数: {spearman_corr.correlation:.4f} (p値: {spearman_corr.pvalue:.4f})")
print()

# 材料別の分析
print("【材料組み合わせ別の平均値】")
# 全部材の材料を合計（0-6の範囲、6が全て木材）
material_columns = ['material_columns', 'material_floor1', 'material_floor2', 
                    'material_roof', 'material_walls', 'material_balcony']
df['wood_count'] = df[material_columns].sum(axis=1)

material_stats = df.groupby('wood_count')[['safety_factor', 'co2_per_sqm']].agg(['mean', 'count'])
print(material_stats)
print()

# 安全率の範囲別CO2排出量
print("【安全率の範囲別CO2排出量】")
safety_bins = [0, 1, 1.5, 2, 3, 6]
safety_labels = ['0-1', '1-1.5', '1.5-2', '2-3', '3+']
df['safety_range'] = pd.cut(df['safety_factor'], bins=safety_bins, labels=safety_labels)
range_stats = df.groupby('safety_range')[['co2_per_sqm']].agg(['mean', 'std', 'count'])
print(range_stats)
print()

# 可視化
fig, axes = plt.subplots(2, 2, figsize=(15, 12))
fig.suptitle('安全率とCO2排出量の相関分析', fontsize=16)

# 1. 散布図
ax1 = axes[0, 0]
scatter = ax1.scatter(df['safety_factor'], df['co2_per_sqm'], 
                      c=df['wood_count'], cmap='RdYlGn', alpha=0.6, s=50)
ax1.set_xlabel('安全率')
ax1.set_ylabel('CO2排出量 (kg-CO2/m²)')
ax1.set_title(f'安全率 vs CO2排出量\n相関係数: {correlation:.3f}')
ax1.grid(True, alpha=0.3)

# トレンドライン追加
z = np.polyfit(df['safety_factor'], df['co2_per_sqm'], 1)
p = np.poly1d(z)
ax1.plot(sorted(df['safety_factor']), p(sorted(df['safety_factor'])), 
         "r--", alpha=0.8, label=f'y={z[0]:.1f}x+{z[1]:.1f}')
ax1.legend()

# カラーバー追加
cbar = plt.colorbar(scatter, ax=ax1)
cbar.set_label('木材使用数', rotation=270, labelpad=20)

# 2. 材料別の箱ひげ図（CO2）
ax2 = axes[0, 1]
wood_groups = []
labels = []
for i in range(7):
    if len(df[df['wood_count'] == i]) > 0:
        wood_groups.append(df[df['wood_count'] == i]['co2_per_sqm'])
        labels.append(f'{i}')

ax2.boxplot(wood_groups, labels=labels)
ax2.set_xlabel('木材使用部位数')
ax2.set_ylabel('CO2排出量 (kg-CO2/m²)')
ax2.set_title('木材使用数別CO2排出量分布')
ax2.grid(True, alpha=0.3)

# 3. 安全率の範囲別CO2排出量
ax3 = axes[1, 0]
x_pos = range(len(safety_labels))
means = range_stats['co2_per_sqm']['mean'].values
stds = range_stats['co2_per_sqm']['std'].values
counts = range_stats['co2_per_sqm']['count'].values

bars = ax3.bar(x_pos, means, yerr=stds, capsize=5, alpha=0.7)
ax3.set_xticks(x_pos)
ax3.set_xticklabels(safety_labels)
ax3.set_xlabel('安全率の範囲')
ax3.set_ylabel('平均CO2排出量 (kg-CO2/m²)')
ax3.set_title('安全率範囲別の平均CO2排出量')
ax3.grid(True, alpha=0.3)

# 各バーの上にサンプル数を表示
for i, (bar, count) in enumerate(zip(bars, counts)):
    ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height() + stds[i] + 20,
             f'n={int(count)}', ha='center', va='bottom')

# 4. 2次元ヒストグラム（密度表示）
ax4 = axes[1, 1]
h = ax4.hist2d(df['safety_factor'], df['co2_per_sqm'], bins=[20, 20], cmap='YlOrRd')
ax4.set_xlabel('安全率')
ax4.set_ylabel('CO2排出量 (kg-CO2/m²)')
ax4.set_title('安全率とCO2排出量の密度分布')
plt.colorbar(h[3], ax=ax4, label='サンプル数')

plt.tight_layout()
plt.savefig('safety_co2_correlation_analysis.png', dpi=150, bbox_inches='tight')
print("グラフを safety_co2_correlation_analysis.png に保存しました。")

# 追加の詳細分析図
plt.figure(figsize=(12, 8))

# 材料タイプ別の散布図
material_types = {
    'RC中心': df['wood_count'] <= 1,
    '混合構造': (df['wood_count'] > 1) & (df['wood_count'] < 5),
    '木造中心': df['wood_count'] >= 5
}

colors = ['blue', 'green', 'brown']
for i, (label, mask) in enumerate(material_types.items()):
    subset = df[mask]
    plt.scatter(subset['safety_factor'], subset['co2_per_sqm'], 
                label=label, alpha=0.6, s=30, c=colors[i])

plt.xlabel('安全率')
plt.ylabel('CO2排出量 (kg-CO2/m²)')
plt.title('材料タイプ別の安全率とCO2排出量の関係')
plt.legend()
plt.grid(True, alpha=0.3)

# 推奨範囲を表示
plt.axvline(x=2.0, color='red', linestyle='--', alpha=0.5, label='推奨安全率')
plt.axhline(y=2000, color='red', linestyle='--', alpha=0.5, label='CO2上限')

plt.tight_layout()
plt.savefig('safety_co2_by_material_type.png', dpi=150)
print("材料タイプ別分析図を safety_co2_by_material_type.png に保存しました。")

# 回帰分析の詳細
print("\n【回帰分析の詳細】")
slope, intercept, r_value, p_value, std_err = stats.linregress(df['safety_factor'], df['co2_per_sqm'])
print(f"回帰直線: CO2 = {slope:.2f} × 安全率 + {intercept:.2f}")
print(f"決定係数 (R²): {r_value**2:.4f}")
print(f"p値: {p_value:.4e}")
print(f"標準誤差: {std_err:.2f}")

# 安全率が高い/低いサンプルの特徴
print("\n【安全率による特徴分析】")
low_safety = df[df['safety_factor'] < 1.0]
high_safety = df[df['safety_factor'] > 2.5]

print(f"\n安全率 < 1.0 のサンプル（n={len(low_safety)}）:")
print(f"  平均CO2: {low_safety['co2_per_sqm'].mean():.1f} kg-CO2/m²")
print(f"  木材使用率: {low_safety['wood_count'].mean():.1f} 部位")

print(f"\n安全率 > 2.5 のサンプル（n={len(high_safety)}）:")
print(f"  平均CO2: {high_safety['co2_per_sqm'].mean():.1f} kg-CO2/m²")
print(f"  木材使用率: {high_safety['wood_count'].mean():.1f} 部位")

print("\n分析完了！")