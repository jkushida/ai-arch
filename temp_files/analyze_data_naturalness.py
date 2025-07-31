#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
production_freecad_random_fem_evaluation2.csv の詳細分析
データの自然性・妥当性を検証
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

# データ読み込み
df = pd.read_csv('production_freecad_random_fem_evaluation2.csv')

print("=" * 80)
print("production_freecad_random_fem_evaluation2.csv の詳細分析")
print("=" * 80)

# 基本情報
print("\n【1. 基本情報】")
print(f"総サンプル数: {len(df)}")
print(f"成功サンプル数: {len(df[df['evaluation_status'] == 'success'])}")
print(f"カラム数: {len(df.columns)}")

# 建物サイズの分析
print("\n【2. 建物サイズの妥当性】")
print("\n■ 建物寸法 (m)")
print(f"  幅 (Lx): {df['Lx'].min():.2f} ~ {df['Lx'].max():.2f} m (平均: {df['Lx'].mean():.2f})")
print(f"  奥行 (Ly): {df['Ly'].min():.2f} ~ {df['Ly'].max():.2f} m (平均: {df['Ly'].mean():.2f})")
print(f"  1階高 (H1): {df['H1'].min():.2f} ~ {df['H1'].max():.2f} m (平均: {df['H1'].mean():.2f})")
print(f"  2階高 (H2): {df['H2'].min():.2f} ~ {df['H2'].max():.2f} m (平均: {df['H2'].mean():.2f})")
print(f"  床面積: {df['floor_area'].min():.1f} ~ {df['floor_area'].max():.1f} m² (平均: {df['floor_area'].mean():.1f})")

# 異常値チェック
if df['H1'].min() < 2.4 or df['H1'].max() > 4.0:
    print("  ⚠️ 1階高さに異常値の可能性あり（通常2.4-4.0m）")
if df['H2'].min() < 2.4 or df['H2'].max() > 4.0:
    print("  ⚠️ 2階高さに異常値の可能性あり（通常2.4-4.0m）")

# 構造部材サイズの分析
print("\n【3. 構造部材サイズの妥当性】")
print("\n■ 部材寸法 (mm)")
print(f"  床厚 (tf): {df['tf'].min()} ~ {df['tf'].max()} mm (平均: {df['tf'].mean():.0f})")
print(f"  屋根厚 (tr): {df['tr'].min()} ~ {df['tr'].max()} mm (平均: {df['tr'].mean():.0f})")
print(f"  柱幅 (bc): {df['bc'].min()} ~ {df['bc'].max()} mm (平均: {df['bc'].mean():.0f})")
print(f"  柱高 (hc): {df['hc'].min()} ~ {df['hc'].max()} mm (平均: {df['hc'].mean():.0f})")
print(f"  外壁厚 (tw_ext): {df['tw_ext'].min()} ~ {df['tw_ext'].max()} mm (平均: {df['tw_ext'].mean():.0f})")

# 異常値チェック
if df['bc'].max() > 1000:
    print("  ⚠️ 柱幅に1000mm以上の値あり - 非現実的に大きい可能性")
if df['hc'].max() > 1000:
    print("  ⚠️ 柱高に1000mm以上の値あり - 非現実的に大きい可能性")
if df['tf'].max() > 600:
    print("  ⚠️ 床厚に600mm以上の値あり - 非現実的に厚い可能性")

# コストの分析
print("\n【4. 建設コストの妥当性】")
cost_stats = df['cost_per_sqm'].describe()
print(f"\n■ コスト統計 (円/m²)")
print(f"  平均: {cost_stats['mean']:,.0f}")
print(f"  標準偏差: {cost_stats['std']:,.0f}")
print(f"  最小: {cost_stats['min']:,.0f}")
print(f"  25%: {cost_stats['25%']:,.0f}")
print(f"  中央値: {cost_stats['50%']:,.0f}")
print(f"  75%: {cost_stats['75%']:,.0f}")
print(f"  最大: {cost_stats['max']:,.0f}")

# 異常値の検出
q1 = cost_stats['25%']
q3 = cost_stats['75%']
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

outliers = df[(df['cost_per_sqm'] < lower_bound) | (df['cost_per_sqm'] > upper_bound)]
if len(outliers) > 0:
    print(f"\n  ⚠️ コストの外れ値: {len(outliers)}件")
    for idx, row in outliers.iterrows():
        print(f"    - sample{idx+1}: {row['cost_per_sqm']:,.0f} 円/m²")

# 一般的な基準との比較
print("\n■ 一般的な建築コストとの比較:")
print("  - 木造住宅: 20-40万円/m²")
print("  - RC造住宅: 30-60万円/m²")
print("  - 高級住宅: 50-100万円/m²")

if df['cost_per_sqm'].min() < 200000:
    print("  ⚠️ 20万円/m²未満のサンプルあり - 非現実的に安い")
if df['cost_per_sqm'].max() > 3000000:
    print("  ⚠️ 300万円/m²超のサンプルあり - 非現実的に高い")

# 安全率の分析
print("\n【5. 安全率の妥当性】")
safety_stats = df['safety_factor'].describe()
print(f"\n■ 安全率統計")
print(f"  平均: {safety_stats['mean']:.2f}")
print(f"  標準偏差: {safety_stats['std']:.2f}")
print(f"  最小: {safety_stats['min']:.2f}")
print(f"  最大: {safety_stats['max']:.2f}")

# 安全率の分布
unsafe = len(df[df['safety_factor'] < 1.0])
marginal = len(df[(df['safety_factor'] >= 1.0) & (df['safety_factor'] < 1.5)])
safe = len(df[(df['safety_factor'] >= 1.5) & (df['safety_factor'] < 2.5)])
oversafe = len(df[df['safety_factor'] >= 2.5])

print(f"\n■ 安全率の分布:")
print(f"  危険 (<1.0): {unsafe}件 ({unsafe/len(df)*100:.1f}%)")
print(f"  境界 (1.0-1.5): {marginal}件 ({marginal/len(df)*100:.1f}%)")
print(f"  適正 (1.5-2.5): {safe}件 ({safe/len(df)*100:.1f}%)")
print(f"  過剰 (≥2.5): {oversafe}件 ({oversafe/len(df)*100:.1f}%)")

# CO2排出量の分析
print("\n【6. CO2排出量の妥当性】")
co2_stats = df['co2_per_sqm'].describe()
print(f"\n■ CO2排出量統計 (kg-CO2/m²)")
print(f"  平均: {co2_stats['mean']:.1f}")
print(f"  標準偏差: {co2_stats['std']:.1f}")
print(f"  最小: {co2_stats['min']:.1f}")
print(f"  最大: {co2_stats['max']:.1f}")

print("\n■ 一般的なCO2排出量との比較:")
print("  - 木造住宅: 300-600 kg-CO2/m²")
print("  - RC造住宅: 800-1500 kg-CO2/m²")

# 材料構成の分析
print("\n【7. 材料構成の分析】")
material_cols = ['material_columns', 'material_floor1', 'material_floor2', 
                'material_roof', 'material_walls', 'material_balcony']
df['wood_count'] = df[material_cols].sum(axis=1)

material_dist = df['wood_count'].value_counts().sort_index()
print("\n■ 木材使用数の分布:")
for count, freq in material_dist.items():
    material_type = "RC造" if count == 0 else "木造" if count == 6 else "混合構造"
    print(f"  {count}箇所 ({material_type}): {freq}件")

# 相関分析
print("\n【8. 主要指標間の相関】")
correlations = df[['cost_per_sqm', 'co2_per_sqm', 'safety_factor', 'bc', 'hc', 'floor_area']].corr()

print("\n■ 重要な相関関係:")
print(f"  コスト vs 安全率: {correlations.loc['cost_per_sqm', 'safety_factor']:.3f}")
print(f"  コスト vs CO2: {correlations.loc['cost_per_sqm', 'co2_per_sqm']:.3f}")
print(f"  安全率 vs 柱幅: {correlations.loc['safety_factor', 'bc']:.3f}")
print(f"  安全率 vs 柱高: {correlations.loc['safety_factor', 'hc']:.3f}")

# 評価時間の分析
print("\n【9. 計算時間の妥当性】")
time_stats = df['evaluation_time_s'].describe()
print(f"\n■ 評価時間統計 (秒)")
print(f"  平均: {time_stats['mean']:.1f}")
print(f"  最小: {time_stats['min']:.1f}")
print(f"  最大: {time_stats['max']:.1f}")

# 総合評価
print("\n【10. 総合評価】")
issues = []

# コストの問題
if df['cost_per_sqm'].max() > 2000000:
    issues.append("極端に高いコスト（200万円/m²超）のサンプルが存在")

# 安全率の問題
if unsafe > 0:
    issues.append(f"安全率1.0未満の危険なサンプルが{unsafe}件存在")

# 構造部材の問題
if df['bc'].max() > 1000 or df['hc'].max() > 1000:
    issues.append("非現実的に大きな柱サイズ（1000mm超）が存在")

# CO2の問題
if df['co2_per_sqm'].max() > 2500:
    issues.append("非現実的に高いCO2排出量（2500 kg-CO2/m²超）が存在")

if issues:
    print("\n⚠️ 検出された問題:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\n✅ データは概ね妥当な範囲内にあります")

# 改善提案
print("\n【11. 改善提案】")
if df['cost_per_sqm'].max() > 2000000:
    print("  1. コスト計算式の見直し（特に大断面部材の場合）")
if unsafe > 0:
    print("  2. 構造設計パラメータの調整範囲の見直し")
if df['bc'].max() > 1000:
    print("  3. 柱サイズの上限設定（例: 800mm以下）")

# グラフ作成
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# 1. コストのヒストグラム
ax1 = axes[0, 0]
ax1.hist(df['cost_per_sqm']/10000, bins=20, edgecolor='black', alpha=0.7)
ax1.set_xlabel('コスト (万円/m²)')
ax1.set_ylabel('頻度')
ax1.set_title('建設コストの分布')
ax1.axvline(x=30, color='red', linestyle='--', label='一般的な下限')
ax1.axvline(x=100, color='red', linestyle='--', label='一般的な上限')
ax1.legend()

# 2. 安全率のヒストグラム
ax2 = axes[0, 1]
ax2.hist(df['safety_factor'], bins=20, edgecolor='black', alpha=0.7)
ax2.set_xlabel('安全率')
ax2.set_ylabel('頻度')
ax2.set_title('安全率の分布')
ax2.axvline(x=1.0, color='red', linestyle='--', label='最低基準')
ax2.axvline(x=2.0, color='green', linestyle='--', label='推奨値')
ax2.legend()

# 3. 柱サイズの散布図
ax3 = axes[0, 2]
ax3.scatter(df['bc'], df['hc'], alpha=0.6)
ax3.set_xlabel('柱幅 bc (mm)')
ax3.set_ylabel('柱高 hc (mm)')
ax3.set_title('柱断面サイズの分布')
ax3.grid(True, alpha=0.3)

# 4. コスト vs 安全率
ax4 = axes[1, 0]
ax4.scatter(df['safety_factor'], df['cost_per_sqm']/10000, alpha=0.6)
ax4.set_xlabel('安全率')
ax4.set_ylabel('コスト (万円/m²)')
ax4.set_title('安全率とコストの関係')
ax4.grid(True, alpha=0.3)

# 5. CO2のヒストグラム
ax5 = axes[1, 1]
ax5.hist(df['co2_per_sqm'], bins=20, edgecolor='black', alpha=0.7)
ax5.set_xlabel('CO2排出量 (kg-CO2/m²)')
ax5.set_ylabel('頻度')
ax5.set_title('CO2排出量の分布')

# 6. 材料構成の円グラフ
ax6 = axes[1, 2]
material_types = []
for count in df['wood_count']:
    if count == 0:
        material_types.append('RC造')
    elif count == 6:
        material_types.append('木造')
    else:
        material_types.append('混合構造')
material_counts = pd.Series(material_types).value_counts()
ax6.pie(material_counts.values, labels=material_counts.index, autopct='%1.1f%%')
ax6.set_title('材料構成の割合')

plt.tight_layout()
plt.savefig('data_naturalness_analysis.png', dpi=150, bbox_inches='tight')
print(f"\n✅ 分析グラフを保存しました: data_naturalness_analysis.png")

print("\n" + "=" * 80)