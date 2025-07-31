#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終的な改善結果の分析
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

print("=" * 80)
print("最終的な改善結果の分析")
print("=" * 80)

# 基本統計
print(f"\n総サンプル数: {len(df)}")
print(f"成功サンプル数: {len(df[df['evaluation_status'] == 'success'])}")

# 1. コストの分析
print("\n【1. 建設コスト】")
cost_stats = df['cost_per_sqm'].describe()
print(f"平均: {cost_stats['mean']:,.0f} 円/m² ({cost_stats['mean']/10000:.1f}万円/m²)")
print(f"標準偏差: {cost_stats['std']:,.0f} 円/m²")
print(f"最小: {cost_stats['min']:,.0f} 円/m²")
print(f"最大: {cost_stats['max']:,.0f} 円/m²")

# 100万円/m²を超えるサンプル
high_cost = df[df['cost_per_sqm'] > 1000000]
print(f"\n100万円/m²超: {len(high_cost)}件 ({len(high_cost)/len(df)*100:.1f}%)")
if len(high_cost) > 0:
    print("  高コストサンプル:")
    for idx, row in high_cost.iterrows():
        print(f"    sample{idx+1}: {row['cost_per_sqm']:,.0f} 円/m²")

# コストの妥当性判定
if cost_stats['mean'] < 1000000 and cost_stats['max'] < 2000000:
    print("✅ コストは概ね妥当な範囲")
else:
    print("⚠️ コストに問題あり")

# 2. CO2排出量の分析
print("\n【2. CO2排出量】")
co2_stats = df['co2_per_sqm'].describe()
print(f"平均: {co2_stats['mean']:.1f} kg-CO2/m²")
print(f"標準偏差: {co2_stats['std']:.1f} kg-CO2/m²")
print(f"最小: {co2_stats['min']:.1f} kg-CO2/m²")
print(f"最大: {co2_stats['max']:.1f} kg-CO2/m²")

# 2000を超えるサンプル
high_co2 = df[df['co2_per_sqm'] > 2000]
print(f"\n2000 kg-CO2/m²超: {len(high_co2)}件")
if len(high_co2) > 0:
    for idx, row in high_co2.iterrows():
        print(f"  sample{idx+1}: {row['co2_per_sqm']:.1f} kg-CO2/m²")

# CO2上限制限の確認
if co2_stats['max'] <= 2000:
    print("✅ CO2排出量は2000以下に制限されています")
else:
    print("⚠️ CO2排出量の上限制限が機能していない可能性")

# 3. 快適性・施工性スコア
print("\n【3. 快適性・施工性スコア】")
print(f"快適性平均: {df['comfort_score'].mean():.2f} (範囲: {df['comfort_score'].min():.2f} ~ {df['comfort_score'].max():.2f})")
print(f"施工性平均: {df['constructability_score'].mean():.2f} (範囲: {df['constructability_score'].min():.2f} ~ {df['constructability_score'].max():.2f})")

# スコアの妥当性
if 0 <= df['comfort_score'].min() and df['comfort_score'].max() <= 10:
    print("✅ 快適性スコアは妥当な範囲")
else:
    print("⚠️ 快適性スコアに範囲外の値")

if 0 <= df['constructability_score'].min() and df['constructability_score'].max() <= 10:
    print("✅ 施工性スコアは妥当な範囲")
else:
    print("⚠️ 施工性スコアに範囲外の値")

# 4. 安全率の分析
print("\n【4. 安全率】")
safety_stats = df['safety_factor'].describe()
print(f"平均: {safety_stats['mean']:.2f}")
print(f"標準偏差: {safety_stats['std']:.2f}")
print(f"最小: {safety_stats['min']:.2f}")
print(f"最大: {safety_stats['max']:.2f}")

# 危険なサンプル
unsafe = df[df['safety_factor'] < 1.0]
print(f"\n安全率1.0未満: {len(unsafe)}件 ({len(unsafe)/len(df)*100:.1f}%)")
if len(unsafe) > 0 and len(unsafe) <= 5:
    for idx, row in unsafe.iterrows():
        print(f"  sample{idx+1}: 安全率 {row['safety_factor']:.3f}")

# 5. 材料構成の分析
print("\n【5. 材料構成】")
material_cols = ['material_columns', 'material_floor1', 'material_floor2', 
                'material_roof', 'material_walls', 'material_balcony']
df['wood_count'] = df[material_cols].sum(axis=1)

wood_dist = df['wood_count'].value_counts().sort_index()
print("木材使用数の分布:")
for count, freq in wood_dist.items():
    print(f"  {count}箇所: {freq}件")

# 6. 総合評価
print("\n【6. 総合評価】")

issues = []
improvements = []

# コスト
if cost_stats['mean'] < 1000000:
    improvements.append("平均コストが100万円/m²未満")
if cost_stats['max'] < 2000000:
    improvements.append("最大コストが200万円/m²未満")
elif cost_stats['max'] > 2000000:
    issues.append("200万円/m²を超える高コストサンプルが存在")

# CO2
if co2_stats['max'] <= 2000:
    improvements.append("CO2排出量が2000 kg-CO2/m²以下に制限")
else:
    issues.append(f"CO2排出量が2000を超過（最大: {co2_stats['max']:.1f}）")

# 安全率
if len(unsafe) == 0:
    improvements.append("すべてのサンプルが安全率1.0以上")
elif len(unsafe) / len(df) < 0.1:
    issues.append(f"安全率1.0未満が{len(unsafe)}件存在（許容範囲内）")
else:
    issues.append(f"安全率1.0未満が{len(unsafe)}件（{len(unsafe)/len(df)*100:.1f}%）と多い")

print("\n✅ 改善された点:")
for imp in improvements:
    print(f"  - {imp}")

if issues:
    print("\n⚠️ 残る問題点:")
    for issue in issues:
        print(f"  - {issue}")
else:
    print("\n✅ すべての指標が妥当な範囲内です")

# グラフ作成
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. コスト分布
ax1 = axes[0, 0]
ax1.hist(df['cost_per_sqm']/10000, bins=20, edgecolor='black', alpha=0.7, color='blue')
ax1.axvline(x=100, color='red', linestyle='--', label='高級住宅上限')
ax1.set_xlabel('コスト (万円/m²)')
ax1.set_ylabel('頻度')
ax1.set_title('建設コストの分布')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. CO2分布
ax2 = axes[0, 1]
ax2.hist(df['co2_per_sqm'], bins=20, edgecolor='black', alpha=0.7, color='green')
ax2.axvline(x=2000, color='red', linestyle='--', label='上限値')
ax2.set_xlabel('CO2排出量 (kg-CO2/m²)')
ax2.set_ylabel('頻度')
ax2.set_title('CO2排出量の分布')
ax2.legend()
ax2.grid(True, alpha=0.3)

# 3. 安全率分布
ax3 = axes[1, 0]
ax3.hist(df['safety_factor'], bins=20, edgecolor='black', alpha=0.7, color='orange')
ax3.axvline(x=1.0, color='red', linestyle='--', label='最低基準')
ax3.axvline(x=2.0, color='green', linestyle='--', label='推奨値')
ax3.set_xlabel('安全率')
ax3.set_ylabel('頻度')
ax3.set_title('安全率の分布')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4. 各指標の相関
ax4 = axes[1, 1]

# カスタムカラーマップを作成（7段階：青灰色→赤）
from matplotlib.colors import ListedColormap
colors = [
    (112/255, 128/255, 144/255),  # 0: 青灰色（コンクリート）
    (132/255, 112/255, 132/255),  # 1: 青紫灰
    (152/255, 96/255, 120/255),   # 2: 紫赤
    (172/255, 80/255, 108/255),   # 3: 赤紫
    (192/255, 64/255, 96/255),    # 4: 深紅
    (212/255, 48/255, 84/255),    # 5: 赤
    (232/255, 32/255, 72/255)     # 6: 鮮やかな赤（木材）
]
cm = ListedColormap(colors, name='blue_gray_to_red')

scatter = ax4.scatter(df['safety_factor'], df['cost_per_sqm']/10000, 
                     c=df['wood_count'], cmap=cm, alpha=0.6, s=100)
ax4.set_xlabel('安全率')
ax4.set_ylabel('コスト (万円/m²)')
ax4.set_title('安全率 vs コスト（材料別）')
ax4.grid(True, alpha=0.3)
cbar = plt.colorbar(scatter, ax=ax4, label='木材使用数')
cbar.set_ticks([0, 1, 2, 3, 4, 5, 6])
cbar.set_ticklabels(['0\n(青灰)', '1', '2', '3', '4', '5', '6\n(赤)'])

plt.tight_layout()
plt.savefig('final_analysis_results.png', dpi=150, bbox_inches='tight')
print(f"\n✅ グラフを保存しました: final_analysis_results.png")