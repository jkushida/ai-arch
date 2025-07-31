#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PSO2.pyを小規模で実行して現実的な設定をテスト
"""

import os
import sys
import time
import pandas as pd
import numpy as np

print("=" * 60)
print("PSO2.py 現実的設定テスト")
print("=" * 60)

# 設定の変更内容を表示
print("\n【最適化設定】")
print("- 粒子数: 10")
print("- 世代数: 10")
print("- 目的: コスト最小化（安全率2.0以上）")

print("\n【材料特性の変更】")
print("1. 木材のCO2: -50 → 50 kg-CO2/m³")
print("2. 施工費係数: 最大2.5 → 最大1.35")
print("3. 材料選択: 全RC 20%、全木造 20%、混合 60%")
print("4. 木造の応答係数: 7.5 → 4.0")

# PSO2.pyのパラメータを環境変数で上書き
os.environ['PSO_N_PARTICLES'] = '10'
os.environ['PSO_N_ITERATIONS'] = '10'

# PSO2.pyを実行
print("\n実行開始...")
start_time = time.time()

# モジュールをリロード
if 'PSO2' in sys.modules:
    del sys.modules['PSO2']

# PSO2.pyを実行
exec(open('PSO2.py').read())

# 結果を分析
elapsed = time.time() - start_time
print(f"\n実行時間: {elapsed:.1f}秒")

# CSVファイルを読み込んで分析
try:
    df = pd.read_csv('pso_optimization_history.csv')
    
    print("\n【最適化結果】")
    print(f"評価回数: {len(df)}")
    
    # 最良解
    best_idx = df['fitness'].idxmin()
    best = df.iloc[best_idx]
    
    print(f"\n最良解:")
    print(f"  コスト: {best['cost_per_sqm']:,.0f} 円/m²")
    print(f"  CO2: {best['co2_per_sqm']:.0f} kg-CO2/m²")
    print(f"  安全率: {best['safety_factor']:.2f}")
    
    # 材料構成
    materials = ['material_columns', 'material_floor1', 'material_floor2', 
                 'material_roof', 'material_walls', 'material_balcony']
    wood_count = sum(best[mat] for mat in materials)
    print(f"  材料: {'全RC' if wood_count == 0 else '全木造' if wood_count == 6 else '混合構造'}")
    
    # 成功率
    success_df = df[df['evaluation_status'] == 'Success']
    print(f"\n成功率: {len(success_df)}/{len(df)} ({len(success_df)/len(df)*100:.1f}%)")
    
    # CO2とコストの相関
    if len(success_df) > 3:
        corr = success_df['cost_per_sqm'].corr(success_df['co2_per_sqm'])
        print(f"\nCO2-コスト相関: {corr:.3f}")
    
except Exception as e:
    print(f"\n結果分析エラー: {e}")

print("=" * 60)