#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
production_freecad_random_fem_evaluation2.csvの統計分析
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

# CSVファイルの読み込み
csv_file = "/Users/kushida2/Library/CloudStorage/GoogleDrive-kushida2008@gmail.com/マイドライブ/2025code/CadProg/new3/production_freecad_random_fem_evaluation2.csv"
df = pd.read_csv(csv_file)

print("=== production_freecad_random_fem_evaluation2.csv 分析レポート ===\n")

# 基本情報
print(f"データ数: {len(df)} 件")
print(f"カラム数: {len(df.columns)} 個\n")

# 主要指標の統計情報
print("【主要指標の統計情報】")
print("-" * 80)

# 数値データの統計
stats_columns = ['comfort_score', 'safety_factor', 'cost_per_sqm', 'co2_per_sqm', 'constructability_score']
stats_df = df[stats_columns].describe()
print(stats_df)
print()

# 快適性スコアの詳細分析
print("【快適性スコアの詳細分析】")
print(f"最小値: {df['comfort_score'].min():.3f}")
print(f"最大値: {df['comfort_score'].max():.3f}")
print(f"範囲: {df['comfort_score'].max() - df['comfort_score'].min():.3f}")
print(f"標準偏差: {df['comfort_score'].std():.3f}")
print(f"変動係数: {df['comfort_score'].std() / df['comfort_score'].mean():.3f}")
print()

# 安全率の分析
print("【安全率の分析】")
safety_over_5 = len(df[df['safety_factor'] > 5])
print(f"安全率 > 5 のサンプル数: {safety_over_5} 件 ({safety_over_5/len(df)*100:.1f}%)")
print(f"安全率の最大値: {df['safety_factor'].max():.3f}")
print()

# 材料選択の分析
print("【材料選択パターンの分析】")
material_columns = ['material_columns', 'material_floor1', 'material_floor2', 
                    'material_roof', 'material_walls', 'material_balcony']

for col in material_columns:
    wood_count = len(df[df[col] == 1])
    concrete_count = len(df[df[col] == 0])
    print(f"{col}: 木材={wood_count}件({wood_count/len(df)*100:.1f}%), "
          f"コンクリート={concrete_count}件({concrete_count/len(df)*100:.1f}%)")
print()

# 材料の組み合わせパターン
print("【材料組み合わせの上位パターン】")
material_pattern = df[material_columns].value_counts().head(10)
print(material_pattern)
print()

# 相関分析
print("【主要指標間の相関係数】")
correlation_cols = ['comfort_score', 'safety_factor', 'cost_per_sqm', 'co2_per_sqm', 'constructability_score']
corr_matrix = df[correlation_cols].corr()
print(corr_matrix)
print()

# 可視化
fig, axes = plt.subplots(2, 3, figsize=(15, 10))
fig.suptitle('production_freecad_random_fem_evaluation2.csv データ分析', fontsize=16)

# 1. 快適性スコアのヒストグラム
ax1 = axes[0, 0]
ax1.hist(df['comfort_score'], bins=30, edgecolor='black', alpha=0.7)
ax1.set_xlabel('快適性スコア')
ax1.set_ylabel('頻度')
ax1.set_title('快適性スコアの分布')
ax1.grid(True, alpha=0.3)

# 2. 安全率のヒストグラム
ax2 = axes[0, 1]
ax2.hist(df['safety_factor'], bins=30, edgecolor='black', alpha=0.7)
ax2.set_xlabel('安全率')
ax2.set_ylabel('頻度')
ax2.set_title('安全率の分布')
ax2.axvline(x=5, color='r', linestyle='--', label='上限目標(5)')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. コストのヒストグラム
ax3 = axes[0, 2]
ax3.hist(df['cost_per_sqm'], bins=30, edgecolor='black', alpha=0.7)
ax3.set_xlabel('建設コスト (円/m²)')
ax3.set_ylabel('頻度')
ax3.set_title('建設コストの分布')
ax3.grid(True, alpha=0.3)

# 4. 快適性スコア vs 安全率
ax4 = axes[1, 0]
ax4.scatter(df['safety_factor'], df['comfort_score'], alpha=0.5)
ax4.set_xlabel('安全率')
ax4.set_ylabel('快適性スコア')
ax4.set_title('安全率 vs 快適性スコア')
ax4.grid(True, alpha=0.3)

# 5. 快適性スコア vs コスト
ax5 = axes[1, 1]
ax5.scatter(df['cost_per_sqm'], df['comfort_score'], alpha=0.5)
ax5.set_xlabel('建設コスト (円/m²)')
ax5.set_ylabel('快適性スコア')
ax5.set_title('建設コスト vs 快適性スコア')
ax5.grid(True, alpha=0.3)

# 6. 材料選択の積み上げ棒グラフ
ax6 = axes[1, 2]
material_counts = []
for col in material_columns:
    wood_ratio = len(df[df[col] == 1]) / len(df) * 100
    material_counts.append(wood_ratio)

x = range(len(material_columns))
ax6.bar(x, material_counts)
ax6.set_xticks(x)
ax6.set_xticklabels([col.replace('material_', '') for col in material_columns], rotation=45)
ax6.set_ylabel('木材使用率 (%)')
ax6.set_title('部位別木材使用率')
ax6.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('production_data_analysis.png', dpi=150, bbox_inches='tight')
print("グラフを production_data_analysis.png に保存しました。")

# 快適性スコアの詳細な分布図
plt.figure(figsize=(12, 6))

plt.subplot(1, 2, 1)
plt.hist(df['comfort_score'], bins=50, edgecolor='black', alpha=0.7, density=True)
plt.xlabel('快適性スコア')
plt.ylabel('確率密度')
plt.title('快適性スコアの詳細分布')
plt.grid(True, alpha=0.3)

# 正規分布でフィッティング
from scipy import stats
mu, std = stats.norm.fit(df['comfort_score'])
x = np.linspace(df['comfort_score'].min(), df['comfort_score'].max(), 100)
plt.plot(x, stats.norm.pdf(x, mu, std), 'r-', lw=2, label=f'正規分布\n(μ={mu:.2f}, σ={std:.2f})')
plt.legend()

plt.subplot(1, 2, 2)
plt.boxplot([df['comfort_score'], df['safety_factor'], df['constructability_score']], 
            labels=['快適性', '安全率', '施工性'])
plt.ylabel('スコア')
plt.title('各評価指標の箱ひげ図')
plt.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('comfort_score_detailed_analysis.png', dpi=150)
print("快適性スコアの詳細分析図を comfort_score_detailed_analysis.png に保存しました。")

print("\n分析完了！")