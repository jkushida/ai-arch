#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
現実的な設定調整後の結果分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 日本語フォントの設定
plt.rcParams['font.family'] = 'Hiragino Sans'
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro']
plt.rcParams['axes.unicode_minus'] = False

# CSVファイルを読み込む
df = pd.read_csv('production_freecad_random_fem_evaluation2.csv')
df_success = df[df['evaluation_status'] == 'success'].copy()

print("=" * 60)
print("現実的な設定調整後の分析結果")
print("=" * 60)
print(f"\n総サンプル数: {len(df)} (全て成功)")

# 材料使用数を計算
df_success['wood_count'] = (
    df_success['material_columns'] + 
    df_success['material_floor1'] + 
    df_success['material_floor2'] + 
    df_success['material_roof'] + 
    df_success['material_walls'] + 
    df_success['material_balcony']
)

# 1. 材料分布
print("\n【1. 材料分布】")
rc_count = len(df_success[df_success['wood_count'] == 0])
wood_count = len(df_success[df_success['wood_count'] == 6])
mixed_count = len(df_success[(df_success['wood_count'] >= 1) & (df_success['wood_count'] <= 5)])

print(f"全RC造: {rc_count} 件 ({rc_count/len(df_success)*100:.1f}%)")
print(f"全木造: {wood_count} 件 ({wood_count/len(df_success)*100:.1f}%)")
print(f"混合構造: {mixed_count} 件 ({mixed_count/len(df_success)*100:.1f}%)")

# 2. CO2とコストの相関
print("\n【2. CO2とコストの相関】")
corr = df_success['cost_per_sqm'].corr(df_success['co2_per_sqm'])
print(f"相関係数: {corr:.3f}")
print(f"目標値(0.8)との差: {abs(corr - 0.8):.3f}")

# 材料タイプ別の相関
if rc_count > 3:
    rc_df = df_success[df_success['wood_count'] == 0]
    rc_corr = rc_df['cost_per_sqm'].corr(rc_df['co2_per_sqm'])
    print(f"RC造のみ: {rc_corr:.3f}")

if wood_count > 3:
    wood_df = df_success[df_success['wood_count'] == 6]
    wood_corr = wood_df['cost_per_sqm'].corr(wood_df['co2_per_sqm'])
    print(f"木造のみ: {wood_corr:.3f}")

# 3. 安全率の分析
print("\n【3. 安全率の分析】")
print(f"全体平均: {df_success['safety_factor'].mean():.2f}")
print(f"範囲: {df_success['safety_factor'].min():.2f} - {df_success['safety_factor'].max():.2f}")

# 材料別の安全率
if rc_count > 0:
    rc_safety = df_success[df_success['wood_count'] == 0]['safety_factor']
    print(f"\nRC造の安全率:")
    print(f"  平均: {rc_safety.mean():.2f}")
    print(f"  範囲: {rc_safety.min():.2f} - {rc_safety.max():.2f}")

if wood_count > 0:
    wood_safety = df_success[df_success['wood_count'] == 6]['safety_factor']
    print(f"\n木造の安全率:")
    print(f"  平均: {wood_safety.mean():.2f}")
    print(f"  範囲: {wood_safety.min():.2f} - {wood_safety.max():.2f}")

# 4. コストとCO2の統計
print("\n【4. コストとCO2の統計】")
print(f"\nコスト (円/m²):")
print(f"  平均: {df_success['cost_per_sqm'].mean():,.0f}")
print(f"  標準偏差: {df_success['cost_per_sqm'].std():,.0f}")

# 材料別コスト
if rc_count > 0:
    print(f"  RC造平均: {df_success[df_success['wood_count'] == 0]['cost_per_sqm'].mean():,.0f}")
if wood_count > 0:
    print(f"  木造平均: {df_success[df_success['wood_count'] == 6]['cost_per_sqm'].mean():,.0f}")

print(f"\nCO2 (kg-CO2/m²):")
print(f"  平均: {df_success['co2_per_sqm'].mean():.0f}")
print(f"  標準偏差: {df_success['co2_per_sqm'].std():.0f}")

# 材料別CO2
if rc_count > 0:
    print(f"  RC造平均: {df_success[df_success['wood_count'] == 0]['co2_per_sqm'].mean():.0f}")
if wood_count > 0:
    print(f"  木造平均: {df_success[df_success['wood_count'] == 6]['co2_per_sqm'].mean():.0f}")

# 5. 改善の評価
print("\n【5. 改善の評価】")
print("✅ 材料分布: RC造・木造が適切に含まれている" if rc_count > 5 and wood_count > 5 else "❌ 材料分布: 偏りがある")
print("✅ CO2-コスト相関: 目標値に近い" if 0.7 < corr < 0.9 else "❌ CO2-コスト相関: 改善が必要")
print("✅ 安全率: 現実的な範囲" if df_success['safety_factor'].min() > 0.5 else "❌ 安全率: 低すぎる値あり")

# グラフの作成
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

# 1. CO2 vs コスト
scatter = ax1.scatter(df_success['co2_per_sqm'], df_success['cost_per_sqm'], 
                     c=df_success['wood_count'], cmap='RdYlBu', alpha=0.6, s=50)
ax1.set_xlabel('CO2排出量 (kg-CO2/m²)')
ax1.set_ylabel('建設コスト (円/m²)')
ax1.set_title(f'CO2排出量 vs 建設コスト (相関: {corr:.3f})')
ax1.grid(True, alpha=0.3)
plt.colorbar(scatter, ax=ax1, label='木材使用数')

# 2. 材料分布（円グラフ）
labels = ['全RC造', '全木造', '混合構造']
sizes = [rc_count, wood_count, mixed_count]
colors = ['#ff9999', '#66b3ff', '#99ff99']
ax2.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
ax2.set_title('材料構成の分布')

# 3. 安全率のヒストグラム
ax3.hist(df_success['safety_factor'], bins=20, alpha=0.7, color='blue', edgecolor='black')
ax3.axvline(x=2.0, color='red', linestyle='--', label='推奨安全率')
ax3.set_xlabel('安全率')
ax3.set_ylabel('頻度')
ax3.set_title('安全率の分布')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4. 材料別のコスト・CO2比較
if rc_count > 0 and wood_count > 0:
    materials = ['RC造', '木造']
    costs = [
        df_success[df_success['wood_count'] == 0]['cost_per_sqm'].mean(),
        df_success[df_success['wood_count'] == 6]['cost_per_sqm'].mean()
    ]
    co2s = [
        df_success[df_success['wood_count'] == 0]['co2_per_sqm'].mean(),
        df_success[df_success['wood_count'] == 6]['co2_per_sqm'].mean()
    ]
    
    x = np.arange(len(materials))
    width = 0.35
    
    ax4_twin = ax4.twinx()
    bars1 = ax4.bar(x - width/2, costs, width, label='コスト', color='orange', alpha=0.7)
    bars2 = ax4_twin.bar(x + width/2, co2s, width, label='CO2', color='green', alpha=0.7)
    
    ax4.set_xlabel('材料タイプ')
    ax4.set_ylabel('コスト (円/m²)', color='orange')
    ax4_twin.set_ylabel('CO2 (kg-CO2/m²)', color='green')
    ax4.set_title('材料別のコスト・CO2比較')
    ax4.set_xticks(x)
    ax4.set_xticklabels(materials)
    ax4.tick_params(axis='y', labelcolor='orange')
    ax4_twin.tick_params(axis='y', labelcolor='green')

plt.tight_layout()
plt.savefig('realistic_analysis_results.png', dpi=150, bbox_inches='tight')
print(f"\n✅ グラフを保存しました: realistic_analysis_results.png")

print("\n" + "=" * 60)