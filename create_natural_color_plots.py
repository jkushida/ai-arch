#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
各指標の散布図を材料の自然な色（木材=茶色、コンクリート=灰色）で作成
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap

# 日本語フォントの設定
plt.rcParams['font.family'] = 'Hiragino Sans'
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro', 'Yu Gothic', 'Meirio']
plt.rcParams['axes.unicode_minus'] = False

# データ読み込み
df = pd.read_csv('production_freecad_random_fem_evaluation2.csv')

# 材料使用数を計算（木材の合計数）
material_cols = ['material_columns', 'material_floor1', 'material_floor2', 
                'material_roof', 'material_walls', 'material_balcony']
df['wood_count'] = df[material_cols].sum(axis=1)
df['wood_ratio'] = df['wood_count'] / 6.0  # 0〜1に正規化

# カスタムカラーマップを作成（コンクリート=灰色 → 木材=茶色）
colors = [
    (0.7, 0.7, 0.7),    # 灰色（コンクリート）
    (0.6, 0.5, 0.4),    # 中間色1
    (0.5, 0.35, 0.25),  # 中間色2
    (0.4, 0.25, 0.15)   # 茶色（木材）
]
n_bins = 100
cm = LinearSegmentedColormap.from_list('concrete_to_wood', colors, N=n_bins)

# グラフ作成
fig, axes = plt.subplots(2, 2, figsize=(14, 12))

# 共通の設定
scatter_params = {
    'cmap': cm,
    'alpha': 0.7,
    's': 100,
    'edgecolors': 'white',
    'linewidth': 0.5
}

# 1. 建設コスト vs 安全率
ax1 = axes[0, 0]
scatter1 = ax1.scatter(df['safety_factor'], df['cost_per_sqm'], 
                       c=df['wood_ratio'], **scatter_params)
ax1.set_xlabel('安全率', fontsize=12)
ax1.set_ylabel('建設コスト (円/m²)', fontsize=12)
ax1.set_title('建設コスト (円/m²) vs 安全率', fontsize=14)
ax1.axvline(x=2.0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='推奨安全率')
ax1.grid(True, alpha=0.3)
ax1.legend()

# Y軸を科学的記数法で表示
ax1.ticklabel_format(style='scientific', axis='y', scilimits=(0,0))
ax1.yaxis.get_offset_text().set_fontsize(10)

# 2. CO2排出量 vs 安全率
ax2 = axes[0, 1]
scatter2 = ax2.scatter(df['safety_factor'], df['co2_per_sqm'], 
                       c=df['wood_ratio'], **scatter_params)
ax2.set_xlabel('安全率', fontsize=12)
ax2.set_ylabel('CO2排出量 (kg-CO2/m²)', fontsize=12)
ax2.set_title('CO2排出量 (kg-CO2/m²) vs 安全率', fontsize=14)
ax2.axvline(x=2.0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='推奨安全率')
ax2.grid(True, alpha=0.3)
ax2.legend()

# 3. 快適性スコア vs 安全率
ax3 = axes[1, 0]
scatter3 = ax3.scatter(df['safety_factor'], df['comfort_score'], 
                       c=df['wood_ratio'], **scatter_params)
ax3.set_xlabel('安全率', fontsize=12)
ax3.set_ylabel('快適性スコア', fontsize=12)
ax3.set_title('快適性スコア vs 安全率', fontsize=14)
ax3.axvline(x=2.0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='推奨安全率')
ax3.grid(True, alpha=0.3)
ax3.legend()

# 4. 施工性スコア vs 安全率
ax4 = axes[1, 1]
scatter4 = ax4.scatter(df['safety_factor'], df['constructability_score'], 
                       c=df['wood_ratio'], **scatter_params)
ax4.set_xlabel('安全率', fontsize=12)
ax4.set_ylabel('施工性スコア', fontsize=12)
ax4.set_title('施工性スコア vs 安全率', fontsize=14)
ax4.axvline(x=2.0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='推奨安全率')
ax4.grid(True, alpha=0.3)
ax4.legend()

# カラーバーを追加（右側に配置）
cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
cbar = plt.colorbar(scatter1, cax=cbar_ax)
cbar.set_label('材料構成', fontsize=12, labelpad=10)
cbar.set_ticks([0, 0.5, 1])
cbar.set_ticklabels(['コンクリート造\n（灰色）', '混合構造', '木造\n（茶色）'])

# レイアウト調整
plt.subplots_adjust(right=0.9)
plt.tight_layout()

# 保存
output_filename = 'natural_color_scatter_plots.png'
plt.savefig(output_filename, dpi=150, bbox_inches='tight')
print(f"✅ グラフを保存しました: {output_filename}")

# 統計情報を出力
print("\n【材料構成別の統計】")
for mat_type, (min_ratio, max_ratio) in [
    ('コンクリート造寄り', (0, 0.33)),
    ('混合構造', (0.33, 0.67)),
    ('木造寄り', (0.67, 1.0))
]:
    subset = df[(df['wood_ratio'] >= min_ratio) & (df['wood_ratio'] <= max_ratio)]
    if len(subset) > 0:
        print(f"\n{mat_type} (n={len(subset)}):")
        print(f"  平均安全率: {subset['safety_factor'].mean():.2f}")
        print(f"  平均コスト: {subset['cost_per_sqm'].mean():,.0f} 円/m²")
        print(f"  平均CO2: {subset['co2_per_sqm'].mean():.1f} kg-CO2/m²")
        print(f"  平均快適性: {subset['comfort_score'].mean():.2f}")
        print(f"  平均施工性: {subset['constructability_score'].mean():.2f}")

# plt.show()  # 非表示にして処理を高速化