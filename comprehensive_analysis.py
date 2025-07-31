#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
production_freecad_random_fem_evaluation2.csv の包括的分析
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

print("=" * 80)
print("production_freecad_random_fem_evaluation2.csv の包括的分析")
print("=" * 80)

# 1. データ概要
print("\n【1. データ概要】")
print(f"総レコード数: {len(df)}")
print(f"成功レコード数: {len(df[df['evaluation_status'] == 'success'])}")
print(f"失敗レコード数: {len(df[df['evaluation_status'] != 'success'])}")
print(f"成功率: {len(df[df['evaluation_status'] == 'success']) / len(df) * 100:.1f}%")

# 成功データのみを分析対象とする
df_success = df[df['evaluation_status'] == 'success'].copy()

# 2. 基本統計量
print("\n【2. 主要指標の基本統計量】")
key_metrics = ['cost_per_sqm', 'co2_per_sqm', 'safety_factor', 'comfort_score', 'constructability_score']
stats_df = df_success[key_metrics].describe()
print(stats_df.round(2))

# 3. 材料分析
print("\n【3. 材料使用分析】")
material_cols = ['material_columns', 'material_floor1', 'material_floor2', 
                 'material_roof', 'material_walls', 'material_balcony']

# 材料タイプのカウント
for col in material_cols:
    print(f"\n{col}:")
    value_counts = df_success[col].value_counts().sort_index()
    for val, count in value_counts.items():
        material_name = {0: "コンクリート", 1: "木材", 2: "CLT"}.get(val, "不明")
        print(f"  {material_name} ({val}): {count}件 ({count/len(df_success)*100:.1f}%)")

# 材料の組み合わせ分析
df_success['total_wood'] = sum((df_success[col] >= 1).astype(int) for col in material_cols)
df_success['total_clt'] = sum((df_success[col] == 2).astype(int) for col in material_cols)

print("\n【4. 材料組み合わせパターン】")
print(f"全RC造（木材使用なし）: {len(df_success[df_success['total_wood'] == 0])}件")
print(f"全木造（RC使用なし）: {len(df_success[df_success['total_wood'] == 6])}件")
print(f"混合構造: {len(df_success[(df_success['total_wood'] > 0) & (df_success['total_wood'] < 6)])}件")
print(f"CLT使用建物: {len(df_success[df_success['total_clt'] > 0])}件")

# 5. 相関分析
print("\n【5. 主要指標間の相関】")
corr_matrix = df_success[key_metrics].corr()
print("\n相関行列:")
print(corr_matrix.round(3))

# 特に重要な相関
print("\n重要な相関関係:")
print(f"コストとCO2: {corr_matrix.loc['cost_per_sqm', 'co2_per_sqm']:.3f}")
print(f"コストと安全率: {corr_matrix.loc['cost_per_sqm', 'safety_factor']:.3f}")
print(f"安全率と施工性: {corr_matrix.loc['safety_factor', 'constructability_score']:.3f}")

# 6. 設計パラメータの分布
print("\n【6. 設計パラメータの分布】")
design_params = ['Lx', 'Ly', 'H1', 'H2', 'bc', 'hc', 'tf', 'tr']
for param in design_params:
    print(f"{param}: 平均 {df_success[param].mean():.2f}, 標準偏差 {df_success[param].std():.2f}")

# 7. 床面積と各指標の関係
print("\n【7. 床面積と各指標の関係】")
for metric in ['cost_per_sqm', 'co2_per_sqm', 'safety_factor']:
    corr = df_success['floor_area'].corr(df_success[metric])
    print(f"床面積と{metric}: 相関 {corr:.3f}")

# 8. 実行時間分析
print("\n【8. 実行時間分析】")
print(f"平均実行時間: {df_success['evaluation_time_s'].mean():.1f}秒")
print(f"最短実行時間: {df_success['evaluation_time_s'].min():.1f}秒")
print(f"最長実行時間: {df_success['evaluation_time_s'].max():.1f}秒")

# グラフ作成
fig = plt.figure(figsize=(16, 12))

# 1. コストとCO2の散布図（材料タイプで色分け）
ax1 = plt.subplot(3, 3, 1)
colors = df_success['total_wood'].map(lambda x: 'red' if x == 0 else ('green' if x >= 4 else 'orange'))
scatter = ax1.scatter(df_success['co2_per_sqm'], df_success['cost_per_sqm'], 
                     c=colors, alpha=0.6, s=100)
ax1.set_xlabel('CO2排出量 (kg-CO2/m²)')
ax1.set_ylabel('建設コスト (円/m²)')
ax1.set_title('CO2とコストの関係')
ax1.grid(True, alpha=0.3)

# 2. 安全率のヒストグラム
ax2 = plt.subplot(3, 3, 2)
ax2.hist(df_success['safety_factor'], bins=15, edgecolor='black', alpha=0.7)
ax2.axvline(x=2.0, color='red', linestyle='--', label='推奨値')
ax2.set_xlabel('安全率')
ax2.set_ylabel('頻度')
ax2.set_title('安全率の分布')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. 材料使用の棒グラフ
ax3 = plt.subplot(3, 3, 3)
material_usage = pd.DataFrame()
for col in material_cols:
    material_usage[col.replace('material_', '')] = df_success[col].value_counts().sort_index()
material_usage = material_usage.T
material_usage.plot(kind='bar', ax=ax3, color=['gray', 'brown', 'purple'])
ax3.set_xlabel('部材')
ax3.set_ylabel('使用件数')
ax3.set_title('部材別材料使用状況')
ax3.legend(['コンクリート', '木材', 'CLT'])
plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45)

# 4. 快適性スコアの箱ひげ図
ax4 = plt.subplot(3, 3, 4)
df_success['material_category'] = df_success['total_wood'].apply(
    lambda x: 'RC造' if x == 0 else ('木造' if x >= 4 else '混合'))
df_success.boxplot(column='comfort_score', by='material_category', ax=ax4)
ax4.set_xlabel('材料タイプ')
ax4.set_ylabel('快適性スコア')
ax4.set_title('材料タイプ別快適性')

# 5. 施工性スコアの箱ひげ図
ax5 = plt.subplot(3, 3, 5)
df_success.boxplot(column='constructability_score', by='material_category', ax=ax5)
ax5.set_xlabel('材料タイプ')
ax5.set_ylabel('施工性スコア')
ax5.set_title('材料タイプ別施工性')

# 6. 床面積とコストの関係
ax6 = plt.subplot(3, 3, 6)
ax6.scatter(df_success['floor_area'], df_success['cost_per_sqm'], alpha=0.6)
ax6.set_xlabel('床面積 (m²)')
ax6.set_ylabel('単位コスト (円/m²)')
ax6.set_title('床面積と単位コストの関係')
ax6.grid(True, alpha=0.3)

# 7. 相関行列のヒートマップ
ax7 = plt.subplot(3, 3, 7)
sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0, 
            square=True, ax=ax7, fmt='.2f')
ax7.set_title('主要指標の相関行列')

# 8. 設計パターンの円グラフ
ax8 = plt.subplot(3, 3, 8)
pattern_counts = df_success['design_pattern'].value_counts().head(5)
ax8.pie(pattern_counts.values, labels=pattern_counts.index, autopct='%1.1f%%')
ax8.set_title('上位5設計パターン')

# 9. 実行時間のヒストグラム
ax9 = plt.subplot(3, 3, 9)
ax9.hist(df_success['evaluation_time_s'], bins=20, edgecolor='black', alpha=0.7)
ax9.set_xlabel('実行時間 (秒)')
ax9.set_ylabel('頻度')
ax9.set_title('評価実行時間の分布')
ax9.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('comprehensive_analysis.png', dpi=150, bbox_inches='tight')
print(f"\n✅ グラフを保存しました: comprehensive_analysis.png")

# 9. まとめと洞察
print("\n【9. 主な洞察】")
print("1. 材料選択:")
print(f"   - CLTオプションの導入により材料の多様性が向上")
print(f"   - 全体の{len(df_success[df_success['total_clt'] > 0])/len(df_success)*100:.0f}%がCLTを使用")

print("\n2. コスト構造:")
avg_cost_by_material = df_success.groupby('material_category')['cost_per_sqm'].mean()
for mat, cost in avg_cost_by_material.items():
    print(f"   - {mat}: 平均 {cost:,.0f} 円/m²")

print("\n3. 環境性能:")
avg_co2_by_material = df_success.groupby('material_category')['co2_per_sqm'].mean()
for mat, co2 in avg_co2_by_material.items():
    print(f"   - {mat}: 平均 {co2:.0f} kg-CO2/m²")

print("\n4. 安全性:")
safety_by_material = df_success.groupby('material_category')['safety_factor'].mean()
for mat, safety in safety_by_material.items():
    print(f"   - {mat}: 平均安全率 {safety:.2f}")

# 相関係数の追加表示
cost_co2_corr = df_success['cost_per_sqm'].corr(df_success['co2_per_sqm'])
cost_safety_corr = df_success['cost_per_sqm'].corr(df_success['safety_factor'])

print("\n✅ 分析完了")
print(f"📈 コストとCO2の相関係数: {cost_co2_corr:.3f}")
print(f"📈 コストと安全性の相関係数: {cost_safety_corr:.3f}")

print("\n" + "=" * 80)