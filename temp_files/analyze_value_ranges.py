#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
各指標の値域の自然性・現実性を分析
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
print("各指標の値域分析")
print("=" * 80)

# 1. 建設コスト (円/m²)
print("\n【1. 建設コスト (cost_per_sqm)】")
print(f"最小値: {df['cost_per_sqm'].min():,.0f} 円/m²")
print(f"最大値: {df['cost_per_sqm'].max():,.0f} 円/m²")
print(f"平均値: {df['cost_per_sqm'].mean():,.0f} 円/m²")
print(f"標準偏差: {df['cost_per_sqm'].std():,.0f} 円/m²")
print(f"値域: {df['cost_per_sqm'].min()/10000:.1f} ~ {df['cost_per_sqm'].max()/10000:.1f} 万円/m²")

print("\n■ 一般的な建築コストとの比較:")
print("  木造住宅: 20-40万円/m²")
print("  RC造住宅: 30-60万円/m²")
print("  高級住宅: 50-100万円/m²")
print("  超高級住宅: 100-200万円/m²")

if df['cost_per_sqm'].min() < 200000:
    print("  ⚠️ 最小値が非現実的に低い（20万円/m²未満）")
if df['cost_per_sqm'].max() > 2000000:
    print("  ⚠️ 最大値が非現実的に高い（200万円/m²超）")
elif df['cost_per_sqm'].max() > 1000000:
    print("  △ 最大値がやや高い（100万円/m²超）が、高級住宅として許容範囲")

print(f"\n判定: {'△ やや広い' if df['cost_per_sqm'].max() > 1000000 else '✅ 概ね自然'}")

# 2. CO2排出量 (kg-CO2/m²)
print("\n【2. CO2排出量 (co2_per_sqm)】")
print(f"最小値: {df['co2_per_sqm'].min():.1f} kg-CO2/m²")
print(f"最大値: {df['co2_per_sqm'].max():.1f} kg-CO2/m²")
print(f"平均値: {df['co2_per_sqm'].mean():.1f} kg-CO2/m²")
print(f"標準偏差: {df['co2_per_sqm'].std():.1f} kg-CO2/m²")

print("\n■ 一般的なCO2排出量との比較:")
print("  木造住宅: 300-600 kg-CO2/m²")
print("  RC造住宅: 800-1500 kg-CO2/m²")
print("  鉄骨造: 1000-1800 kg-CO2/m²")

if df['co2_per_sqm'].min() < 300:
    print("  ⚠️ 最小値が非現実的に低い（300 kg-CO2/m²未満）")
if df['co2_per_sqm'].max() > 2000:
    print("  ⚠️ 最大値が非現実的に高い（2000 kg-CO2/m²超）")

print(f"\n判定: {'⚠️ 最大値が高すぎる' if df['co2_per_sqm'].max() > 2000 else '✅ 概ね自然'}")

# 3. 快適性スコア (comfort_score)
print("\n【3. 快適性スコア (comfort_score)】")
print(f"最小値: {df['comfort_score'].min():.2f}")
print(f"最大値: {df['comfort_score'].max():.2f}")
print(f"平均値: {df['comfort_score'].mean():.2f}")
print(f"標準偏差: {df['comfort_score'].std():.2f}")

print("\n■ 一般的なスコア範囲（10点満点と仮定）:")
print("  劣悪: 0-3")
print("  不良: 3-5")
print("  標準: 5-7")
print("  良好: 7-8.5")
print("  優秀: 8.5-10")

if df['comfort_score'].min() < 0:
    print("  ⚠️ 負の値が存在")
if df['comfort_score'].max() > 10:
    print("  ⚠️ 10を超える値が存在")

print(f"\n判定: {'✅ 自然な範囲' if 0 <= df['comfort_score'].min() and df['comfort_score'].max() <= 10 else '⚠️ 範囲外の値あり'}")

# 4. 施工性スコア (constructability_score)
print("\n【4. 施工性スコア (constructability_score)】")
print(f"最小値: {df['constructability_score'].min():.2f}")
print(f"最大値: {df['constructability_score'].max():.2f}")
print(f"平均値: {df['constructability_score'].mean():.2f}")
print(f"標準偏差: {df['constructability_score'].std():.2f}")

print("\n■ 一般的なスコア範囲（10点満点と仮定）:")
print("  非常に困難: 0-3")
print("  困難: 3-5")
print("  標準: 5-7")
print("  容易: 7-8.5")
print("  非常に容易: 8.5-10")

print(f"\n判定: {'✅ 自然な範囲' if 0 <= df['constructability_score'].min() and df['constructability_score'].max() <= 10 else '⚠️ 範囲外の値あり'}")

# 5. 安全率 (safety_factor)
print("\n【5. 安全率 (safety_factor)】")
print(f"最小値: {df['safety_factor'].min():.2f}")
print(f"最大値: {df['safety_factor'].max():.2f}")
print(f"平均値: {df['safety_factor'].mean():.2f}")
print(f"標準偏差: {df['safety_factor'].std():.2f}")

print("\n■ 構造設計における一般的な安全率:")
print("  危険（不合格）: < 1.0")
print("  最低限: 1.0-1.5")
print("  標準: 1.5-2.5")
print("  安全: 2.5-3.0")
print("  過剰設計: > 3.0")

if df['safety_factor'].min() < 0.5:
    print("  ⚠️ 極端に低い値が存在（0.5未満）")
if df['safety_factor'].max() > 4.0:
    print("  ⚠️ 過剰に高い値が存在（4.0超）")

unsafe_ratio = len(df[df['safety_factor'] < 1.0]) / len(df) * 100
print(f"\n  安全率1.0未満: {unsafe_ratio:.1f}%")

print(f"\n判定: {'⚠️ 危険な建物が多い' if unsafe_ratio > 10 else '△ やや問題あり'}")

# 6. 総合評価
print("\n【6. 総合評価】")

natural_indicators = []
unnatural_indicators = []

# コスト
if df['cost_per_sqm'].min() >= 300000 and df['cost_per_sqm'].max() <= 2000000:
    natural_indicators.append("建設コスト")
else:
    unnatural_indicators.append("建設コスト（値域: 42-165万円/m²）")

# CO2
if df['co2_per_sqm'].min() >= 300 and df['co2_per_sqm'].max() <= 2000:
    natural_indicators.append("CO2排出量")
else:
    unnatural_indicators.append(f"CO2排出量（最大値: {df['co2_per_sqm'].max():.0f} kg-CO2/m²）")

# 快適性
if 0 <= df['comfort_score'].min() and df['comfort_score'].max() <= 10:
    natural_indicators.append("快適性スコア")
else:
    unnatural_indicators.append("快適性スコア")

# 施工性
if 0 <= df['constructability_score'].min() and df['constructability_score'].max() <= 10:
    natural_indicators.append("施工性スコア")
else:
    unnatural_indicators.append("施工性スコア")

# 安全率
if df['safety_factor'].min() >= 0.5 and df['safety_factor'].max() <= 4.0 and unsafe_ratio <= 10:
    natural_indicators.append("安全率")
else:
    unnatural_indicators.append(f"安全率（最小値: {df['safety_factor'].min():.2f}, 危険率: {unsafe_ratio:.1f}%）")

print("\n✅ 自然な値域の指標:")
for ind in natural_indicators:
    print(f"  - {ind}")

print("\n⚠️ 不自然な値域の指標:")
for ind in unnatural_indicators:
    print(f"  - {ind}")

# グラフ作成
fig, axes = plt.subplots(2, 3, figsize=(15, 10))

# 1. コスト分布
ax1 = axes[0, 0]
ax1.hist(df['cost_per_sqm']/10000, bins=20, edgecolor='black', alpha=0.7)
ax1.axvline(x=30, color='green', linestyle='--', label='一般的下限')
ax1.axvline(x=100, color='orange', linestyle='--', label='高級住宅上限')
ax1.axvline(x=200, color='red', linestyle='--', label='超高級上限')
ax1.set_xlabel('コスト (万円/m²)')
ax1.set_ylabel('頻度')
ax1.set_title('建設コストの分布')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. CO2分布
ax2 = axes[0, 1]
ax2.hist(df['co2_per_sqm'], bins=20, edgecolor='black', alpha=0.7)
ax2.axvline(x=600, color='green', linestyle='--', label='木造上限')
ax2.axvline(x=1500, color='orange', linestyle='--', label='RC造上限')
ax2.axvline(x=2000, color='red', linestyle='--', label='現実的上限')
ax2.set_xlabel('CO2排出量 (kg-CO2/m²)')
ax2.set_ylabel('頻度')
ax2.set_title('CO2排出量の分布')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. 快適性スコア分布
ax3 = axes[0, 2]
ax3.hist(df['comfort_score'], bins=20, edgecolor='black', alpha=0.7)
ax3.axvline(x=5, color='orange', linestyle='--', label='標準下限')
ax3.axvline(x=7, color='green', linestyle='--', label='良好下限')
ax3.set_xlabel('快適性スコア')
ax3.set_ylabel('頻度')
ax3.set_title('快適性スコアの分布')
ax3.set_xlim(0, 10)
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4. 施工性スコア分布
ax4 = axes[1, 0]
ax4.hist(df['constructability_score'], bins=20, edgecolor='black', alpha=0.7)
ax4.axvline(x=5, color='orange', linestyle='--', label='標準下限')
ax4.axvline(x=7, color='green', linestyle='--', label='容易下限')
ax4.set_xlabel('施工性スコア')
ax4.set_ylabel('頻度')
ax4.set_title('施工性スコアの分布')
ax4.set_xlim(0, 10)
ax4.legend()
ax4.grid(True, alpha=0.3)

# 5. 安全率分布
ax5 = axes[1, 1]
ax5.hist(df['safety_factor'], bins=20, edgecolor='black', alpha=0.7)
ax5.axvline(x=1.0, color='red', linestyle='--', label='最低基準')
ax5.axvline(x=1.5, color='orange', linestyle='--', label='標準下限')
ax5.axvline(x=2.5, color='green', linestyle='--', label='標準上限')
ax5.set_xlabel('安全率')
ax5.set_ylabel('頻度')
ax5.set_title('安全率の分布')
ax5.legend()
ax5.grid(True, alpha=0.3)

# 6. 各指標の箱ひげ図
ax6 = axes[1, 2]
# 正規化して比較
normalized_data = [
    df['cost_per_sqm'] / 1000000,  # 百万円単位
    df['co2_per_sqm'] / 1000,      # トン単位
    df['comfort_score'] / 10,       # 0-1に正規化
    df['constructability_score'] / 10,  # 0-1に正規化
    df['safety_factor'] / 3         # 3で割って正規化
]
ax6.boxplot(normalized_data, labels=['コスト\n(百万円/m²)', 'CO2\n(t-CO2/m²)', 
                                     '快適性\n(0-1)', '施工性\n(0-1)', '安全率\n(/3)'])
ax6.set_ylabel('正規化値')
ax6.set_title('各指標の正規化分布比較')
ax6.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('value_range_analysis.png', dpi=150, bbox_inches='tight')
print(f"\n✅ グラフを保存しました: value_range_analysis.png")