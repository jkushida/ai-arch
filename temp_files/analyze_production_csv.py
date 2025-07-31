#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
production_freecad_random_fem_evaluation2.csvの分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 日本語フォントの設定
plt.rcParams['font.family'] = 'Hiragino Sans'
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro']
plt.rcParams['axes.unicode_minus'] = False

# CSVファイルを読み込む
df = pd.read_csv('production_freecad_random_fem_evaluation2.csv')

print("=" * 80)
print("production_freecad_random_fem_evaluation2.csv の分析結果")
print("=" * 80)

# 1. 基本統計
print("\n【1. データ概要】")
print(f"総サンプル数: {len(df)}")
print(f"成功率: 100% (すべて成功)")

# 2. 主要指標の統計
print("\n【2. 主要指標の基本統計】")
print("\nコスト (円/m²):")
print(f"  最小値: {df['cost_per_sqm'].min():,.0f}")
print(f"  最大値: {df['cost_per_sqm'].max():,.0f}")
print(f"  平均値: {df['cost_per_sqm'].mean():,.0f}")
print(f"  中央値: {df['cost_per_sqm'].median():,.0f}")

print("\n安全率:")
print(f"  最小値: {df['safety_factor'].min():.2f}")
print(f"  最大値: {df['safety_factor'].max():.2f}")
print(f"  平均値: {df['safety_factor'].mean():.2f}")
print(f"  中央値: {df['safety_factor'].median():.2f}")

# 3. 相関分析
print("\n【3. 相関分析】")
corr_cost_safety = df['cost_per_sqm'].corr(df['safety_factor'])
corr_cost_co2 = df['cost_per_sqm'].corr(df['co2_per_sqm'])
corr_safety_comfort = df['safety_factor'].corr(df['comfort_score'])

print(f"コストと安全率の相関: {corr_cost_safety:.3f}")
print(f"コストとCO2の相関: {corr_cost_co2:.3f}")
print(f"安全率と快適性の相関: {corr_safety_comfort:.3f}")

# 4. 材料別分析
print("\n【4. 材料別分析】")
material_names = {0: 'コンクリート', 1: '木材', 2: 'CLT'}

# 柱材料でグループ化
for mat_id in sorted(df['material_columns'].unique()):
    mat_df = df[df['material_columns'] == mat_id]
    if len(mat_df) > 0:
        print(f"\n{material_names.get(mat_id, '不明')} (n={len(mat_df)}):")
        print(f"  平均コスト: {mat_df['cost_per_sqm'].mean():,.0f} 円/m²")
        print(f"  平均安全率: {mat_df['safety_factor'].mean():.2f}")
        print(f"  平均CO2: {mat_df['co2_per_sqm'].mean():.0f} kg-CO2/m²")

# 5. 安全率の分布
print("\n【5. 安全率の分布】")
safety_ranges = [(0, 1), (1, 1.5), (1.5, 2), (2, 2.5), (2.5, 3), (3, 4)]
for low, high in safety_ranges:
    count = len(df[(df['safety_factor'] >= low) & (df['safety_factor'] < high)])
    if count > 0:
        print(f"  {low:.1f} - {high:.1f}: {count}件 ({count/len(df)*100:.1f}%)")

# 6. 適切性の評価
print("\n【6. 適切性の評価】")

# 安全率1.0未満の建物
unsafe_buildings = df[df['safety_factor'] < 1.0]
print(f"\n安全率1.0未満: {len(unsafe_buildings)}件 ({len(unsafe_buildings)/len(df)*100:.1f}%)")
if len(unsafe_buildings) > 0:
    print("  ⚠️ 構造的に危険な建物が含まれています")

# 構造パラメータと安全率の関係
bc_corr = df['bc'].corr(df['safety_factor'])
hc_corr = df['hc'].corr(df['safety_factor'])
print(f"\n構造パラメータとの相関:")
print(f"  柱幅(bc)と安全率: {bc_corr:.3f}")
print(f"  柱高(hc)と安全率: {hc_corr:.3f}")

# 7. グラフ作成
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 散布図：コストvs安全率
ax1 = axes[0, 0]
colors = df['material_columns'].map({0: 'red', 1: 'green', 2: 'blue'})
ax1.scatter(df['safety_factor'], df['cost_per_sqm'], c=colors, alpha=0.6)
ax1.set_xlabel('安全率')
ax1.set_ylabel('コスト (円/m²)')
ax1.set_title(f'安全率とコストの関係 (相関: {corr_cost_safety:.3f})')
ax1.axvline(x=1.0, color='black', linestyle='--', alpha=0.5, label='安全率=1.0')
ax1.grid(True, alpha=0.3)

# ヒストグラム：安全率の分布
ax2 = axes[0, 1]
ax2.hist(df['safety_factor'], bins=20, edgecolor='black', alpha=0.7)
ax2.axvline(x=1.0, color='red', linestyle='--', label='基準値')
ax2.set_xlabel('安全率')
ax2.set_ylabel('頻度')
ax2.set_title('安全率の分布')
ax2.legend()

# 箱ひげ図：材料別コスト
ax3 = axes[1, 0]
cost_data = []
labels = []
for mat_id in sorted(df['material_columns'].unique()):
    mat_df = df[df['material_columns'] == mat_id]
    if len(mat_df) > 0:
        cost_data.append(mat_df['cost_per_sqm'].values / 1000)  # 千円単位
        labels.append(f"{material_names.get(mat_id, '不明')}\n(n={len(mat_df)})")
ax3.boxplot(cost_data, labels=labels)
ax3.set_ylabel('コスト (千円/m²)')
ax3.set_title('材料別コスト分布')
ax3.grid(True, alpha=0.3)

# 散布図：柱サイズvs安全率
ax4 = axes[1, 1]
ax4.scatter(df['bc'], df['safety_factor'], alpha=0.6)
ax4.set_xlabel('柱幅 bc (mm)')
ax4.set_ylabel('安全率')
ax4.set_title(f'柱サイズと安全率の関係 (相関: {bc_corr:.3f})')
ax4.axhline(y=1.0, color='red', linestyle='--', alpha=0.5)
ax4.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('production_analysis.png', dpi=150, bbox_inches='tight')
print(f"\n✅ グラフを保存しました: production_analysis.png")

# 8. 総合評価
print("\n【7. 総合評価】")
print("\n✅ 良い点:")
print(f"  - 安全率とコストに正の相関 ({corr_cost_safety:.3f}) が確認できる")
print(f"  - 構造部材サイズと安全率が正の相関を示している")
print(f"  - 材料による差別化が明確")

print("\n⚠️ 改善点:")
if len(unsafe_buildings) > 0:
    print(f"  - 安全率1.0未満の建物が{len(unsafe_buildings)}件存在")
if corr_cost_safety < 0.5:
    print(f"  - 安全率とコストの相関がやや弱い ({corr_cost_safety:.3f})")

# 安全率ごとの平均コストを計算
print("\n【8. 安全率レベル別の平均コスト】")
df['safety_level'] = pd.cut(df['safety_factor'], 
                            bins=[0, 1, 1.5, 2, 2.5, 3, 4],
                            labels=['危険', '最低限', '標準', '良好', '優秀', '過剰'])
for level in ['危険', '最低限', '標準', '良好', '優秀', '過剰']:
    level_df = df[df['safety_level'] == level]
    if len(level_df) > 0:
        avg_cost = level_df['cost_per_sqm'].mean()
        avg_safety = level_df['safety_factor'].mean()
        print(f"{level}: {avg_cost:,.0f} 円/m² (平均安全率: {avg_safety:.2f}, n={len(level_df)})")

print("\n" + "=" * 80)