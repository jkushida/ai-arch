#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改善されたデータの詳細分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 日本語フォントの設定
plt.rcParams['font.family'] = 'Hiragino Sans'
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro', 'Yu Gothic', 'Meirio']
plt.rcParams['axes.unicode_minus'] = False

# データ読み込み
df = pd.read_csv('production_freecad_random_fem_evaluation2.csv')

print("=" * 80)
print("改善されたデータの分析結果")
print("=" * 80)

# 1. コストの改善状況
print("\n【1. コストの改善状況】")
print(f"平均コスト: {df['cost_per_sqm'].mean():,.0f} 円/m² (83万円/m²)")
print(f"中央値: {df['cost_per_sqm'].median():,.0f} 円/m²")
print(f"最大値: {df['cost_per_sqm'].max():,.0f} 円/m² (165万円/m²)")
print(f"最小値: {df['cost_per_sqm'].min():,.0f} 円/m²")

# 100万円/m²を超えるサンプル
high_cost = df[df['cost_per_sqm'] > 1000000]
print(f"\n100万円/m²を超えるサンプル: {len(high_cost)}件 ({len(high_cost)/len(df)*100:.1f}%)")

# 2. 安全率とコストの関係
print("\n【2. 安全率とコストの関係】")
corr = df['safety_factor'].corr(df['cost_per_sqm'])
print(f"相関係数: {corr:.3f}")

# 安全率別の平均コスト
df['safety_category'] = pd.cut(df['safety_factor'], 
                               bins=[0, 1.0, 1.5, 2.0, 2.5, 10],
                               labels=['危険(<1.0)', '境界(1.0-1.5)', '標準(1.5-2.0)', 
                                      '良好(2.0-2.5)', '過剰(>2.5)'])

print("\n安全率カテゴリ別の平均コスト:")
for cat in ['危険(<1.0)', '境界(1.0-1.5)', '標準(1.5-2.0)', '良好(2.0-2.5)', '過剰(>2.5)']:
    subset = df[df['safety_category'] == cat]
    if len(subset) > 0:
        print(f"  {cat}: {subset['cost_per_sqm'].mean():,.0f} 円/m² (n={len(subset)})")

# 3. 問題のあるサンプルの詳細
print("\n【3. 問題のあるサンプルの分析】")

# 高コストサンプル（130万円/m²以上）
very_high_cost = df[df['cost_per_sqm'] > 1300000]
if len(very_high_cost) > 0:
    print("\n■ 特に高コストのサンプル（130万円/m²以上）:")
    for idx, row in very_high_cost.iterrows():
        print(f"  sample{idx+1}: {row['cost_per_sqm']:,.0f} 円/m²")
        print(f"    柱: {row['bc']}×{row['hc']}mm, 安全率: {row['safety_factor']:.2f}")

# 低安全率サンプル
low_safety = df[df['safety_factor'] < 1.0]
print(f"\n■ 安全率1.0未満のサンプル: {len(low_safety)}件")
if len(low_safety) > 5:
    print("  （最初の5件を表示）")
    for i, (idx, row) in enumerate(low_safety.iterrows()):
        if i >= 5:
            break
        print(f"  sample{idx+1}: 安全率 {row['safety_factor']:.3f}, コスト {row['cost_per_sqm']:,.0f} 円/m²")

# 4. 材料構成の影響
print("\n【4. 材料構成とコストの関係】")
material_cols = ['material_columns', 'material_floor1', 'material_floor2', 
                'material_roof', 'material_walls', 'material_balcony']
df['wood_count'] = df[material_cols].sum(axis=1)

# 木材使用数別の平均コスト
print("\n木材使用数別の平均コスト:")
for count in sorted(df['wood_count'].unique()):
    subset = df[df['wood_count'] == count]
    print(f"  {count}箇所: {subset['cost_per_sqm'].mean():,.0f} 円/m² (n={len(subset)})")

# 5. 総合評価
print("\n【5. 総合評価】")

# 改善点
improvements = []
if df['cost_per_sqm'].mean() < 1000000:
    improvements.append("✅ 平均コストが100万円/m²未満に改善")
if df['cost_per_sqm'].max() < 2000000:
    improvements.append("✅ 最大コストが200万円/m²未満に改善")

# 残る問題点
issues = []
if len(df[df['safety_factor'] < 1.0]) > 5:
    issues.append("⚠️ 安全率1.0未満のサンプルが依然として多い")
if len(df[df['cost_per_sqm'] > 1300000]) > 0:
    issues.append("⚠️ 130万円/m²を超える高コストサンプルが存在")

print("\n改善された点:")
for imp in improvements:
    print(f"  {imp}")

print("\n残る問題点:")
for issue in issues:
    print(f"  {issue}")

# グラフ作成
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. コスト分布のヒストグラム
ax1 = axes[0, 0]
ax1.hist(df['cost_per_sqm']/10000, bins=20, edgecolor='black', alpha=0.7, color='blue')
ax1.axvline(x=100, color='red', linestyle='--', label='一般的な上限')
ax1.set_xlabel('コスト (万円/m²)')
ax1.set_ylabel('頻度')
ax1.set_title('改善後のコスト分布')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. 安全率 vs コスト
ax2 = axes[0, 1]
scatter = ax2.scatter(df['safety_factor'], df['cost_per_sqm']/10000, 
                     c=df['wood_count'], cmap='RdBu_r', alpha=0.6, s=100)
ax2.set_xlabel('安全率')
ax2.set_ylabel('コスト (万円/m²)')
ax2.set_title(f'安全率 vs コスト（相関: {corr:.3f}）')
ax2.axvline(x=1.0, color='red', linestyle='--', alpha=0.5, label='最低基準')
ax2.axvline(x=2.0, color='green', linestyle='--', alpha=0.5, label='推奨値')
ax2.legend()
ax2.grid(True, alpha=0.3)
plt.colorbar(scatter, ax=ax2, label='木材使用数')

# 3. 柱サイズとコストの関係
ax3 = axes[1, 0]
column_area = df['bc'] * df['hc'] / 1000  # 千mm²単位
ax3.scatter(column_area, df['cost_per_sqm']/10000, alpha=0.6)
ax3.set_xlabel('柱断面積 (千mm²)')
ax3.set_ylabel('コスト (万円/m²)')
ax3.set_title('柱断面積とコストの関係')
ax3.grid(True, alpha=0.3)

# 4. 安全率の分布
ax4 = axes[1, 1]
safety_counts = df['safety_category'].value_counts()
ax4.bar(range(len(safety_counts)), safety_counts.values)
ax4.set_xticks(range(len(safety_counts)))
ax4.set_xticklabels(safety_counts.index, rotation=45, ha='right')
ax4.set_ylabel('件数')
ax4.set_title('安全率カテゴリの分布')
ax4.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('improved_data_analysis.png', dpi=150, bbox_inches='tight')
print(f"\n✅ グラフを保存しました: improved_data_analysis.png")