#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
現実的な設定のテスト（10サンプル）
"""

import pandas as pd
import numpy as np
import subprocess
import time

print("=" * 60)
print("現実的な設定のテスト実行")
print("=" * 60)

# 設定の変更内容を表示
print("\n【変更内容】")
print("1. 木材のCO2: -50 → 50 kg-CO2/m³")
print("2. 施工費係数: 最大2.5 → 最大1.35")
print("3. 材料選択: 全RC 20%、全木造 20%、混合 60%")
print("4. 木造の応答係数: 7.5 → 4.0")
print()

# 10サンプルでテスト実行
print("10サンプルでテスト実行中...")
start_time = time.time()

# simple_random_batch2.pyを10サンプルで実行
import os
import sys

# N_SAMPLESを一時的に10に変更
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 環境変数でサンプル数を指定
os.environ['TEST_N_SAMPLES'] = '10'

# simple_random_batch2.pyを直接実行
exec(open('simple_random_batch2.py').read())

# 結果を分析
print("\n" + "=" * 60)
print("結果分析")
print("=" * 60)

# CSVファイルを読み込む
df = pd.read_csv('production_freecad_random_fem_evaluation2.csv')
df_success = df[df['evaluation_status'] == 'success']

if len(df_success) > 0:
    # 基本統計
    print(f"\n成功サンプル数: {len(df_success)}/{len(df)}")
    
    # 材料分布
    wood_count = df_success['material_columns'] + df_success['material_floor1'] + \
                 df_success['material_floor2'] + df_success['material_roof'] + \
                 df_success['material_walls'] + df_success['material_balcony']
    
    print("\n【材料分布】")
    print(f"全RC造: {len(df_success[wood_count == 0])} 件")
    print(f"混合構造: {len(df_success[(wood_count >= 1) & (wood_count <= 5)])} 件")
    print(f"全木造: {len(df_success[wood_count == 6])} 件")
    
    # CO2とコストの相関
    corr = df_success['cost_per_sqm'].corr(df_success['co2_per_sqm'])
    print(f"\n【CO2-コスト相関】")
    print(f"相関係数: {corr:.3f}")
    
    # 安全率の分布
    print(f"\n【安全率】")
    print(f"平均: {df_success['safety_factor'].mean():.2f}")
    print(f"最小: {df_success['safety_factor'].min():.2f}")
    print(f"最大: {df_success['safety_factor'].max():.2f}")
    
    # 材料別の安全率
    rc_df = df_success[wood_count == 0]
    wood_df = df_success[wood_count == 6]
    
    if len(rc_df) > 0:
        print(f"\nRC造の平均安全率: {rc_df['safety_factor'].mean():.2f}")
    if len(wood_df) > 0:
        print(f"木造の平均安全率: {wood_df['safety_factor'].mean():.2f}")
    
    # コストとCO2の範囲
    print(f"\n【コスト (円/m²)】")
    print(f"平均: {df_success['cost_per_sqm'].mean():,.0f}")
    print(f"範囲: {df_success['cost_per_sqm'].min():,.0f} - {df_success['cost_per_sqm'].max():,.0f}")
    
    print(f"\n【CO2 (kg-CO2/m²)】")
    print(f"平均: {df_success['co2_per_sqm'].mean():.0f}")
    print(f"範囲: {df_success['co2_per_sqm'].min():.0f} - {df_success['co2_per_sqm'].max():.0f}")

elapsed = time.time() - start_time
print(f"\n実行時間: {elapsed:.1f}秒")
print("=" * 60)