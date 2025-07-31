#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全性（安全率）と建設コストの関係分析
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# 日本語フォントの設定
plt.rcParams['font.family'] = 'Hiragino Sans'
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro']
plt.rcParams['axes.unicode_minus'] = False

# CSVファイルを読み込む
df = pd.read_csv('production_freecad_random_fem_evaluation2.csv')
df_success = df[df['evaluation_status'] == 'success'].copy()

print("=" * 60)
print("安全性（安全率）と建設コストの関係分析")
print("=" * 60)

# 基本統計
print(f"\nサンプル数: {len(df_success)}")
print(f"\n【基本統計】")
print(f"安全率: 平均 {df_success['safety_factor'].mean():.2f}, "
      f"範囲 {df_success['safety_factor'].min():.2f} - {df_success['safety_factor'].max():.2f}")
print(f"コスト: 平均 {df_success['cost_per_sqm'].mean():,.0f} 円/m², "
      f"範囲 {df_success['cost_per_sqm'].min():,.0f} - {df_success['cost_per_sqm'].max():,.0f} 円/m²")

# 相関分析
corr = df_success['safety_factor'].corr(df_success['cost_per_sqm'])
print(f"\n【相関分析】")
print(f"安全率とコストの相関係数: {corr:.3f}")

# 回帰分析
slope, intercept, r_value, p_value, std_err = stats.linregress(
    df_success['safety_factor'], df_success['cost_per_sqm'])
print(f"\n【回帰分析】")
print(f"回帰式: コスト = {intercept:,.0f} + {slope:,.0f} × 安全率")
print(f"決定係数 R²: {r_value**2:.3f}")
print(f"p値: {p_value:.4f}")

# 安全率区間ごとの分析
print(f"\n【安全率区間別の平均コスト】")
bins = [0, 1.0, 1.5, 2.0, 3.0, 5.0]
labels = ['1.0未満', '1.0-1.5', '1.5-2.0', '2.0-3.0', '3.0以上']
df_success['safety_category'] = pd.cut(df_success['safety_factor'], bins=bins, labels=labels)

for category in labels:
    cat_data = df_success[df_success['safety_category'] == category]
    if len(cat_data) > 0:
        print(f"{category}: {len(cat_data)}件, "
              f"平均コスト {cat_data['cost_per_sqm'].mean():,.0f} 円/m²")

# 材料タイプの追加
clt_cols = ['material_columns', 'material_floor1', 'material_floor2', 
            'material_roof', 'material_walls', 'material_balcony']
df_success['wood_count'] = sum((df_success[col] >= 1).astype(int) for col in clt_cols)
df_success['material_type'] = df_success['wood_count'].apply(
    lambda x: 'RC造' if x == 0 else ('木造中心' if x >= 4 else '混合構造'))

# 材料タイプ別の相関
print(f"\n【材料タイプ別の相関】")
for mat_type in df_success['material_type'].unique():
    mat_data = df_success[df_success['material_type'] == mat_type]
    if len(mat_data) >= 3:
        mat_corr = mat_data['safety_factor'].corr(mat_data['cost_per_sqm'])
        print(f"{mat_type}: {len(mat_data)}件, 相関 {mat_corr:.3f}")

# グラフ作成
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

# 1. 散布図：安全率 vs コスト
colors = {'RC造': 'red', '混合構造': 'orange', '木造中心': 'green'}
for mat_type, color in colors.items():
    mat_data = df_success[df_success['material_type'] == mat_type]
    ax1.scatter(mat_data['safety_factor'], mat_data['cost_per_sqm'], 
               label=mat_type, alpha=0.6, s=80, c=color)

# 回帰直線
x_range = np.array([df_success['safety_factor'].min(), df_success['safety_factor'].max()])
y_pred = intercept + slope * x_range
ax1.plot(x_range, y_pred, 'b--', label=f'回帰直線 (R²={r_value**2:.3f})')

ax1.set_xlabel('安全率')
ax1.set_ylabel('建設コスト (円/m²)')
ax1.set_title(f'安全率 vs 建設コスト (相関: {corr:.3f})')
ax1.legend()
ax1.grid(True, alpha=0.3)

# 2. 箱ひげ図：安全率区間別コスト
category_data = []
category_labels = []
for category in labels:
    cat_data = df_success[df_success['safety_category'] == category]['cost_per_sqm']
    if len(cat_data) > 0:
        category_data.append(cat_data)
        category_labels.append(f"{category}\n(n={len(cat_data)})")

if category_data:
    ax2.boxplot(category_data, labels=category_labels)
    ax2.set_xlabel('安全率区間')
    ax2.set_ylabel('建設コスト (円/m²)')
    ax2.set_title('安全率区間別のコスト分布')
    ax2.grid(True, alpha=0.3)

# 3. 構造部材サイズと安全率の関係
ax3.scatter(df_success['bc'] + df_success['hc'], df_success['safety_factor'], 
           alpha=0.6, s=50)
ax3.set_xlabel('柱断面積の指標 (bc + hc) [mm]')
ax3.set_ylabel('安全率')
ax3.set_title('構造部材サイズと安全率の関係')
ax3.grid(True, alpha=0.3)

# 部材サイズとコストの相関も計算
size_index = df_success['bc'] + df_success['hc']
size_corr = size_index.corr(df_success['safety_factor'])
ax3.text(0.05, 0.95, f'相関: {size_corr:.3f}', transform=ax3.transAxes, 
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

# 4. コスト構成要素の分析
# 部材サイズとコストの関係
ax4.scatter(df_success['bc'] + df_success['hc'], df_success['cost_per_sqm'], 
           alpha=0.6, s=50)
ax4.set_xlabel('柱断面積の指標 (bc + hc) [mm]')
ax4.set_ylabel('建設コスト (円/m²)')
ax4.set_title('構造部材サイズとコストの関係')
ax4.grid(True, alpha=0.3)

size_cost_corr = size_index.corr(df_success['cost_per_sqm'])
ax4.text(0.05, 0.95, f'相関: {size_cost_corr:.3f}', transform=ax4.transAxes, 
         verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
plt.savefig('safety_cost_relationship.png', dpi=150, bbox_inches='tight')
print(f"\n✅ グラフを保存しました: safety_cost_relationship.png")

# 結論
print("\n【分析結果のまとめ】")
if corr > 0.3:
    print("✅ 安全率とコストには正の相関があり、現実的な傾向を示しています")
    print(f"  （安全率が1増加すると、コストは約{slope:,.0f}円/m²増加）")
elif corr > 0:
    print("△ 安全率とコストには弱い正の相関がありますが、関係性は明確ではありません")
else:
    print("❌ 安全率とコストに正の相関が見られず、非現実的な傾向です")

# 材料による影響
print("\n【材料タイプの影響】")
rc_data = df_success[df_success['material_type'] == 'RC造']
wood_data = df_success[df_success['material_type'] == '木造中心']
if len(rc_data) > 0 and len(wood_data) > 0:
    print(f"RC造: 平均安全率 {rc_data['safety_factor'].mean():.2f}, "
          f"平均コスト {rc_data['cost_per_sqm'].mean():,.0f} 円/m²")
    print(f"木造: 平均安全率 {wood_data['safety_factor'].mean():.2f}, "
          f"平均コスト {wood_data['cost_per_sqm'].mean():,.0f} 円/m²")

print("\n" + "=" * 60)