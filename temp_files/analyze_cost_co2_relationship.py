#!/usr/bin/env python3
"""コストとCO2の関係を分析"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import seaborn as sns

# 日本語フォント設定
plt.rcParams['font.sans-serif'] = ['Hiragino Sans GB', 'Arial Unicode MS', 'MS Gothic']
plt.rcParams['axes.unicode_minus'] = False

# データ読み込み
df = pd.read_csv('production_freecad_random_fem_evaluation.csv')

# 基本統計
print("=== 基本統計 ===")
print(f"サンプル数: {len(df)}")
print(f"\nコスト（円/㎡）:")
print(f"  平均: {df['cost_per_sqm'].mean():,.0f}")
print(f"  標準偏差: {df['cost_per_sqm'].std():,.0f}")
print(f"  最小: {df['cost_per_sqm'].min():,.0f}")
print(f"  最大: {df['cost_per_sqm'].max():,.0f}")

print(f"\nCO2排出量（kg-CO2/㎡）:")
print(f"  平均: {df['co2_per_sqm'].mean():.1f}")
print(f"  標準偏差: {df['co2_per_sqm'].std():.1f}")
print(f"  最小: {df['co2_per_sqm'].min():.1f}")
print(f"  最大: {df['co2_per_sqm'].max():.1f}")

# 相関分析
correlation = df['cost_per_sqm'].corr(df['co2_per_sqm'])
print(f"\n相関係数: {correlation:.3f}")

# 線形回帰
slope, intercept, r_value, p_value, std_err = stats.linregress(df['cost_per_sqm'], df['co2_per_sqm'])
print(f"\n線形回帰:")
print(f"  決定係数 R²: {r_value**2:.3f}")
print(f"  p値: {p_value:.4f}")

# 散布図作成
plt.figure(figsize=(12, 8))

# メインの散布図
plt.subplot(2, 2, 1)
plt.scatter(df['cost_per_sqm']/10000, df['co2_per_sqm'], alpha=0.6, s=100)
plt.xlabel('建設コスト（万円/㎡）')
plt.ylabel('CO2排出量（kg-CO2/㎡）')
plt.title(f'建設コストとCO2排出量の関係\n相関係数: {correlation:.3f}')
plt.grid(True, alpha=0.3)

# 回帰直線を追加
x_line = np.array([df['cost_per_sqm'].min(), df['cost_per_sqm'].max()])
y_line = slope * x_line + intercept
plt.plot(x_line/10000, y_line, 'r--', alpha=0.8, label=f'回帰直線 (R²={r_value**2:.3f})')
plt.legend()

# 安全率で色分け
plt.subplot(2, 2, 2)
scatter = plt.scatter(df['cost_per_sqm']/10000, df['co2_per_sqm'], 
                     c=df['safety_factor'], cmap='viridis', 
                     alpha=0.6, s=100)
plt.colorbar(scatter, label='安全率')
plt.xlabel('建設コスト（万円/㎡）')
plt.ylabel('CO2排出量（kg-CO2/㎡）')
plt.title('安全率による色分け')
plt.grid(True, alpha=0.3)

# ヒストグラム（コスト）
plt.subplot(2, 2, 3)
plt.hist(df['cost_per_sqm']/10000, bins=10, alpha=0.7, edgecolor='black')
plt.xlabel('建設コスト（万円/㎡）')
plt.ylabel('頻度')
plt.title('建設コストの分布')
plt.grid(True, alpha=0.3, axis='y')

# ヒストグラム（CO2）
plt.subplot(2, 2, 4)
plt.hist(df['co2_per_sqm'], bins=10, alpha=0.7, edgecolor='black', color='green')
plt.xlabel('CO2排出量（kg-CO2/㎡）')
plt.ylabel('頻度')
plt.title('CO2排出量の分布')
plt.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig('cost_co2_relationship.png', dpi=300, bbox_inches='tight')
plt.show()

# 材料使用量との関係分析
print("\n=== 材料パターンとの関係 ===")
# 木材使用率を計算（2階床と壁が木材）
df['wood_ratio'] = (df['material_floor2'] + df['material_walls']) / 6 * 100
print(f"木材使用率: {df['wood_ratio'].mean():.1f}%（全サンプル同じ）")

# 構造パラメータとの相関
print("\n=== 構造パラメータとの相関 ===")
params = ['bc', 'hc', 'tf', 'tr', 'tw_ext', 'wall_tilt_angle']
for param in params:
    corr_cost = df[param].corr(df['cost_per_sqm'])
    corr_co2 = df[param].corr(df['co2_per_sqm'])
    print(f"{param}:")
    print(f"  コストとの相関: {corr_cost:.3f}")
    print(f"  CO2との相関: {corr_co2:.3f}")

# 相関行列のヒートマップ
plt.figure(figsize=(10, 8))
corr_cols = ['cost_per_sqm', 'co2_per_sqm', 'safety_factor', 'comfort_score', 
             'constructability_score', 'bc', 'hc', 'tf', 'tr', 'tw_ext']
corr_matrix = df[corr_cols].corr()
sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0,
            square=True, linewidths=1)
plt.title('各指標の相関行列')
plt.tight_layout()
plt.savefig('correlation_heatmap.png', dpi=300, bbox_inches='tight')
plt.show()