#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快適性スコアの範囲をテストするスクリプト
"""

import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
sys.path.append('.')
from generate_building_fem_analyze import calculate_comfort_score

# ランダムな建物パラメータを生成してテスト
np.random.seed(42)
n_samples = 100

results = []

for i in range(n_samples):
    # ランダムなパラメータを生成
    building_info = {
        'H1_mm': np.random.uniform(2400, 4000),
        'H2_mm': np.random.uniform(2400, 4000),
        'Lx_mm': np.random.uniform(5000, 15000),
        'Ly_mm': np.random.uniform(5000, 15000),
        'window_ratio_2f': np.random.uniform(0.05, 0.9),
        'floor_opening_ratio': np.random.uniform(0.3, 0.9),
        'bc_mm': np.random.uniform(200, 1200),
        'tw_ext_mm': np.random.uniform(80, 500),
        'wall_tilt_angle': np.random.uniform(0, 40),
        'roof_morph': np.random.uniform(0.1, 0.9),
        'has_balcony': np.random.choice([True, False]),
        'balcony_depth': np.random.uniform(0.5, 4.0) if np.random.random() > 0.5 else 0,
        'span_length': np.random.uniform(5.0, 15.0)
    }
    
    fem_results = {
        'max_displacement': np.random.uniform(5.0, 50.0)
    }
    
    # 快適性スコアを計算
    result = calculate_comfort_score(fem_results, building_info)
    comfort_score = result['comfort_score']
    
    results.append({
        'sample': i+1,
        'comfort_score': comfort_score,
        'avg_height': (building_info['H1_mm'] + building_info['H2_mm']) / 2000,
        'avg_span': (building_info['Lx_mm'] + building_info['Ly_mm']) / 2000,
        'window_ratio': building_info['window_ratio_2f'],
        'bc': building_info['bc_mm']
    })

# DataFrameに変換
df = pd.DataFrame(results)

# 統計情報を表示
print("\n========== 快適性スコアの統計情報 ==========")
print(f"サンプル数: {len(df)}")
print(f"最小値: {df['comfort_score'].min():.2f}")
print(f"最大値: {df['comfort_score'].max():.2f}")
print(f"平均値: {df['comfort_score'].mean():.2f}")
print(f"標準偏差: {df['comfort_score'].std():.2f}")
print(f"25%点: {df['comfort_score'].quantile(0.25):.2f}")
print(f"50%点（中央値）: {df['comfort_score'].quantile(0.50):.2f}")
print(f"75%点: {df['comfort_score'].quantile(0.75):.2f}")

# 分布の可視化
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 1. ヒストグラム
ax = axes[0, 0]
ax.hist(df['comfort_score'], bins=20, edgecolor='black', alpha=0.7)
ax.set_xlabel('快適性スコア')
ax.set_ylabel('頻度')
ax.set_title('快適性スコアの分布')
ax.axvline(x=3, color='red', linestyle='--', label='目標最小値(3)')
ax.axvline(x=8, color='red', linestyle='--', label='目標最大値(8)')
ax.legend()
ax.grid(True, alpha=0.3)

# 2. 天井高との関係
ax = axes[0, 1]
scatter = ax.scatter(df['avg_height'], df['comfort_score'], 
                    c=df['comfort_score'], cmap='RdYlGn', alpha=0.6)
ax.set_xlabel('平均天井高 (m)')
ax.set_ylabel('快適性スコア')
ax.set_title('天井高と快適性スコアの関係')
ax.grid(True, alpha=0.3)
plt.colorbar(scatter, ax=ax, label='快適性スコア')

# 3. スパンとの関係
ax = axes[1, 0]
scatter = ax.scatter(df['avg_span'], df['comfort_score'], 
                    c=df['comfort_score'], cmap='RdYlGn', alpha=0.6)
ax.set_xlabel('平均スパン (m)')
ax.set_ylabel('快適性スコア')
ax.set_title('スパンと快適性スコアの関係')
ax.grid(True, alpha=0.3)
plt.colorbar(scatter, ax=ax, label='快適性スコア')

# 4. 窓開口率との関係
ax = axes[1, 1]
scatter = ax.scatter(df['window_ratio'], df['comfort_score'], 
                    c=df['comfort_score'], cmap='RdYlGn', alpha=0.6)
ax.set_xlabel('窓開口率')
ax.set_ylabel('快適性スコア')
ax.set_title('窓開口率と快適性スコアの関係')
ax.grid(True, alpha=0.3)
plt.colorbar(scatter, ax=ax, label='快適性スコア')

plt.tight_layout()
plt.savefig('comfort_score_distribution_test.png', dpi=150)
print("\n✅ グラフを保存しました: comfort_score_distribution_test.png")

# 範囲の確認
score_range = df['comfort_score'].max() - df['comfort_score'].min()
print(f"\n実際の範囲幅: {score_range:.2f}")
print(f"目標範囲幅: 5.00 (3-8)")

if df['comfort_score'].min() < 3.5 and df['comfort_score'].max() > 7.5:
    print("\n✅ 目標範囲（3-8）をほぼカバーしています！")
else:
    print(f"\n⚠️ 目標範囲（3-8）に対して、実際は {df['comfort_score'].min():.2f} - {df['comfort_score'].max():.2f} です")