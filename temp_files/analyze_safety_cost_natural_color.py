#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全率とコストの散布図を材料の自然な色で表示
木材が多いほど茶色、少ないほど灰色
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

# CSVファイルを読み込む
csv_path = 'production_freecad_random_fem_evaluation2.csv'
df = pd.read_csv(csv_path)

# 成功したサンプルのみを抽出
df_success = df[df['evaluation_status'] == 'success'].copy()

print("=" * 60)
print("安全率とコストの分析（材料の自然な色表示）")
print("=" * 60)
print(f"総サンプル数: {len(df)}")
print(f"成功サンプル数: {len(df_success)}")
print()

# 材料使用数を計算（木材の合計数）
material_cols = ['material_columns', 'material_floor1', 'material_floor2', 
                'material_roof', 'material_walls', 'material_balcony']
df_success['wood_count'] = df_success[material_cols].sum(axis=1)

# 木材比率を計算（0〜1）
df_success['wood_ratio'] = df_success['wood_count'] / 6.0

# カスタムカラーマップを作成
# コンクリート（灰色）から木材（茶色）へのグラデーション
colors = [
    (0.7, 0.7, 0.7),  # 灰色（コンクリート）
    (0.55, 0.4, 0.3),  # 中間色
    (0.4, 0.25, 0.15)  # 茶色（木材）
]
n_bins = 100
cmap_name = 'concrete_to_wood'
cm = LinearSegmentedColormap.from_list(cmap_name, colors, N=n_bins)

# 散布図を作成
fig, ax = plt.subplots(figsize=(10, 8))

# 散布図（材料比率で色分け）
scatter = ax.scatter(
    df_success['safety_factor'], 
    df_success['cost_per_sqm'] / 1e7,  # 億円/m²単位に変換
    c=df_success['wood_ratio'],
    cmap=cm,
    alpha=0.7,
    s=100,
    edgecolors='white',
    linewidth=0.5
)

# 軸の設定
ax.set_xlabel('安全率', fontsize=14)
ax.set_ylabel('建設コスト (円/m²)', fontsize=14)
ax.set_title('建設コスト (円/m²) vs 安全率', fontsize=16)

# Y軸の表示を調整（1e7表記を使用）
ax.text(-0.05, 1.02, '1e7', transform=ax.transAxes, fontsize=12, color='red')

# 推奨安全率の線
ax.axvline(x=2.0, color='red', linestyle='--', linewidth=2, alpha=0.7, label='推奨安全率')

# グリッド
ax.grid(True, alpha=0.3)

# カラーバー
cbar = plt.colorbar(scatter, ax=ax, pad=0.02)
cbar.set_label('材料構成', fontsize=12, labelpad=10)

# カラーバーのティック位置とラベルを設定
cbar.set_ticks([0, 0.5, 1])
cbar.set_ticklabels(['コンクリート造\n（灰色）', '混合構造', '木造\n（茶色）'])

# 凡例
ax.legend(loc='upper left', fontsize=12)

# レイアウト調整
plt.tight_layout()

# 保存
output_filename = 'safety_cost_natural_color.png'
plt.savefig(output_filename, dpi=150, bbox_inches='tight')
print(f"\n✅ グラフを保存しました: {output_filename}")

# 統計情報を出力
print("\n【材料タイプ別の統計】")
for mat_type, (min_ratio, max_ratio) in [
    ('コンクリート造', (0, 0.1)),
    ('混合構造', (0.1, 0.9)),
    ('木造', (0.9, 1.0))
]:
    subset = df_success[(df_success['wood_ratio'] >= min_ratio) & (df_success['wood_ratio'] <= max_ratio)]
    if len(subset) > 0:
        print(f"\n{mat_type} (n={len(subset)}):")
        print(f"  平均安全率: {subset['safety_factor'].mean():.2f}")
        print(f"  平均コスト: {subset['cost_per_sqm'].mean():,.0f} 円/m²")
        print(f"  平均CO2: {subset['co2_per_sqm'].mean():.1f} kg-CO2/m²")

# 相関係数
corr = df_success['safety_factor'].corr(df_success['cost_per_sqm'])
print(f"\n安全率とコストの相関係数: {corr:.3f}")

# 材料比率と安全率の関係
wood_safety_corr = df_success['wood_ratio'].corr(df_success['safety_factor'])
print(f"木材比率と安全率の相関係数: {wood_safety_corr:.3f}")

plt.show()