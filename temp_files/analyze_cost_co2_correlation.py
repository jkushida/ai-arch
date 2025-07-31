#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
コストとCO2排出量の相関分析
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

print("=== コストとCO2排出量の相関分析 ===\n")

# 基本統計
print("【基本統計】")
print(f"建設コスト - 平均: {df['cost_per_sqm'].mean():,.0f} 円/m², 標準偏差: {df['cost_per_sqm'].std():,.0f}")
print(f"CO2排出量 - 平均: {df['co2_per_sqm'].mean():.1f} kg-CO2/m², 標準偏差: {df['co2_per_sqm'].std():.1f}")
print()

# 相関係数の計算
correlation = df['cost_per_sqm'].corr(df['co2_per_sqm'])
print(f"【相関係数】")
print(f"ピアソン相関係数: {correlation:.4f}")

# スピアマンの順位相関係数も計算
spearman_corr = stats.spearmanr(df['cost_per_sqm'], df['co2_per_sqm'])
print(f"スピアマン順位相関係数: {spearman_corr.correlation:.4f} (p値: {spearman_corr.pvalue:.4f})")
print()

# 材料別の分析
print("【材料組み合わせ別の平均値】")
# 全部材の材料を合計（0-6の範囲、6が全て木材）
material_columns = ['material_columns', 'material_floor1', 'material_floor2', 
                    'material_roof', 'material_walls', 'material_balcony']
df['wood_count'] = df[material_columns].sum(axis=1)

material_stats = df.groupby('wood_count')[['cost_per_sqm', 'co2_per_sqm']].agg(['mean', 'count'])
print(material_stats)
print()

# コストの範囲別CO2排出量
print("【コスト範囲別CO2排出量】")
cost_bins = [0, 500000, 700000, 900000, 1200000, 2000000]
cost_labels = ['〜50万', '50-70万', '70-90万', '90-120万', '120万〜']
df['cost_range'] = pd.cut(df['cost_per_sqm'], bins=cost_bins, labels=cost_labels)
range_stats = df.groupby('cost_range')[['co2_per_sqm']].agg(['mean', 'std', 'count'])
print(range_stats)
print()

# 可視化
fig, axes = plt.subplots(2, 3, figsize=(18, 12))
fig.suptitle('コストとCO2排出量の相関分析', fontsize=16)

# 1. 散布図（材料数で色分け）
ax1 = axes[0, 0]
scatter = ax1.scatter(df['cost_per_sqm']/10000, df['co2_per_sqm'], 
                      c=df['wood_count'], cmap='RdYlGn', alpha=0.6, s=50)
ax1.set_xlabel('建設コスト (万円/m²)')
ax1.set_ylabel('CO2排出量 (kg-CO2/m²)')
ax1.set_title(f'コスト vs CO2排出量\n相関係数: {correlation:.3f}')
ax1.grid(True, alpha=0.3)

# トレンドライン追加
z = np.polyfit(df['cost_per_sqm'], df['co2_per_sqm'], 1)
p = np.poly1d(z)
ax1.plot(sorted(df['cost_per_sqm']/10000), p(sorted(df['cost_per_sqm']))/1, 
         "r--", alpha=0.8, label=f'回帰直線')
ax1.legend()

# カラーバー追加
cbar = plt.colorbar(scatter, ax=ax1)
cbar.set_label('木材使用数', rotation=270, labelpad=20)

# 2. 材料数別の箱ひげ図（コスト）
ax2 = axes[0, 1]
wood_groups_cost = []
labels = []
for i in range(7):
    if len(df[df['wood_count'] == i]) > 0:
        wood_groups_cost.append(df[df['wood_count'] == i]['cost_per_sqm']/10000)
        labels.append(f'{i}')

ax2.boxplot(wood_groups_cost, labels=labels)
ax2.set_xlabel('木材使用部位数')
ax2.set_ylabel('建設コスト (万円/m²)')
ax2.set_title('木材使用数別コスト分布')
ax2.grid(True, alpha=0.3)

# 3. 材料数別の箱ひげ図（CO2）
ax3 = axes[0, 2]
wood_groups_co2 = []
for i in range(7):
    if len(df[df['wood_count'] == i]) > 0:
        wood_groups_co2.append(df[df['wood_count'] == i]['co2_per_sqm'])

ax3.boxplot(wood_groups_co2, labels=labels)
ax3.set_xlabel('木材使用部位数')
ax3.set_ylabel('CO2排出量 (kg-CO2/m²)')
ax3.set_title('木材使用数別CO2排出量分布')
ax3.grid(True, alpha=0.3)

# 4. コスト範囲別CO2排出量
ax4 = axes[1, 0]
x_pos = range(len(cost_labels))
means = range_stats['co2_per_sqm']['mean'].values
stds = range_stats['co2_per_sqm']['std'].values
counts = range_stats['co2_per_sqm']['count'].values

bars = ax4.bar(x_pos, means, yerr=stds, capsize=5, alpha=0.7)
ax4.set_xticks(x_pos)
ax4.set_xticklabels(cost_labels, rotation=45)
ax4.set_xlabel('コスト範囲')
ax4.set_ylabel('平均CO2排出量 (kg-CO2/m²)')
ax4.set_title('コスト範囲別の平均CO2排出量')
ax4.grid(True, alpha=0.3)

# 各バーの上にサンプル数を表示
for i, (bar, count) in enumerate(zip(bars, counts)):
    if not np.isnan(count):
        ax4.text(bar.get_x() + bar.get_width()/2., bar.get_height() + (stds[i] if not np.isnan(stds[i]) else 0) + 20,
                 f'n={int(count)}', ha='center', va='bottom')

# 5. 2次元ヒストグラム（密度表示）
ax5 = axes[1, 1]
h = ax5.hist2d(df['cost_per_sqm']/10000, df['co2_per_sqm'], bins=[20, 20], cmap='YlOrRd')
ax5.set_xlabel('建設コスト (万円/m²)')
ax5.set_ylabel('CO2排出量 (kg-CO2/m²)')
ax5.set_title('コストとCO2排出量の密度分布')
plt.colorbar(h[3], ax=ax5, label='サンプル数')

# 6. 材料タイプ別の散布図
ax6 = axes[1, 2]
material_types = {
    'RC中心': df['wood_count'] <= 1,
    '混合構造': (df['wood_count'] > 1) & (df['wood_count'] < 5),
    '木造中心': df['wood_count'] >= 5
}

colors = ['blue', 'green', 'brown']
for i, (label, mask) in enumerate(material_types.items()):
    subset = df[mask]
    ax6.scatter(subset['cost_per_sqm']/10000, subset['co2_per_sqm'], 
                label=label, alpha=0.6, s=30, c=colors[i])

ax6.set_xlabel('建設コスト (万円/m²)')
ax6.set_ylabel('CO2排出量 (kg-CO2/m²)')
ax6.set_title('材料タイプ別の分布')
ax6.legend()
ax6.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('cost_co2_correlation_analysis.png', dpi=150, bbox_inches='tight')
print("グラフを cost_co2_correlation_analysis.png に保存しました。")

# 追加の詳細分析図
plt.figure(figsize=(14, 8))

plt.subplot(1, 2, 1)
# コストとCO2の関係を四分割で分析
median_cost = df['cost_per_sqm'].median()
median_co2 = df['co2_per_sqm'].median()

# 四分割
quadrants = {
    '低コスト・低CO2': (df['cost_per_sqm'] <= median_cost) & (df['co2_per_sqm'] <= median_co2),
    '低コスト・高CO2': (df['cost_per_sqm'] <= median_cost) & (df['co2_per_sqm'] > median_co2),
    '高コスト・低CO2': (df['cost_per_sqm'] > median_cost) & (df['co2_per_sqm'] <= median_co2),
    '高コスト・高CO2': (df['cost_per_sqm'] > median_cost) & (df['co2_per_sqm'] > median_co2)
}

colors_quad = ['green', 'orange', 'blue', 'red']
for i, (label, mask) in enumerate(quadrants.items()):
    subset = df[mask]
    plt.scatter(subset['cost_per_sqm']/10000, subset['co2_per_sqm'], 
                label=f'{label} (n={len(subset)})', alpha=0.6, s=50, c=colors_quad[i])

plt.axvline(x=median_cost/10000, color='gray', linestyle='--', alpha=0.5)
plt.axhline(y=median_co2, color='gray', linestyle='--', alpha=0.5)
plt.xlabel('建設コスト (万円/m²)')
plt.ylabel('CO2排出量 (kg-CO2/m²)')
plt.title('コストとCO2の四分割分析')
plt.legend(loc='upper left', bbox_to_anchor=(0, 0.95))
plt.grid(True, alpha=0.3)

plt.subplot(1, 2, 2)
# 各象限の材料使用パターン
quad_wood_stats = {}
for label, mask in quadrants.items():
    subset = df[mask]
    avg_wood = subset['wood_count'].mean()
    quad_wood_stats[label] = avg_wood

x_pos = range(len(quad_wood_stats))
values = list(quad_wood_stats.values())
plt.bar(x_pos, values, color=colors_quad, alpha=0.7)
plt.xticks(x_pos, quad_wood_stats.keys(), rotation=45, ha='right')
plt.ylabel('平均木材使用部位数')
plt.title('各象限の平均木材使用数')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('cost_co2_quadrant_analysis.png', dpi=150, bbox_inches='tight')
print("四分割分析図を cost_co2_quadrant_analysis.png に保存しました。")

# 回帰分析の詳細
print("\n【回帰分析の詳細】")
slope, intercept, r_value, p_value, std_err = stats.linregress(df['cost_per_sqm'], df['co2_per_sqm'])
print(f"回帰直線: CO2 = {slope:.6f} × コスト + {intercept:.2f}")
print(f"決定係数 (R²): {r_value**2:.4f}")
print(f"p値: {p_value:.4e}")
print(f"標準誤差: {std_err:.6f}")

# コストとCO2の関係における材料の影響
print("\n【材料による影響分析】")
for material_type, mask in material_types.items():
    subset = df[mask]
    print(f"\n{material_type} (n={len(subset)}):")
    print(f"  平均コスト: {subset['cost_per_sqm'].mean():,.0f} 円/m²")
    print(f"  平均CO2: {subset['co2_per_sqm'].mean():.1f} kg-CO2/m²")
    if len(subset) > 10:
        corr = subset['cost_per_sqm'].corr(subset['co2_per_sqm'])
        print(f"  相関係数: {corr:.3f}")

# 最適なバランスのサンプル抽出
print("\n【低コスト・低CO2の優良サンプル（上位10件）】")
# コストとCO2を正規化して合計スコアを計算
df['cost_normalized'] = (df['cost_per_sqm'] - df['cost_per_sqm'].min()) / (df['cost_per_sqm'].max() - df['cost_per_sqm'].min())
df['co2_normalized'] = (df['co2_per_sqm'] - df['co2_per_sqm'].min()) / (df['co2_per_sqm'].max() - df['co2_per_sqm'].min())
df['eco_score'] = df['cost_normalized'] + df['co2_normalized']

best_samples = df.nsmallest(10, 'eco_score')[['cost_per_sqm', 'co2_per_sqm', 'wood_count', 'safety_factor', 'comfort_score']]
print(best_samples.to_string())

print("\n分析完了！")