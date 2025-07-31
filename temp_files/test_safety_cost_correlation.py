#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全率とコストの相関を確認するテストスクリプト
"""

import sys
import os

# FreeCAD環境の初期化
FREECAD_PATH = '/Applications/FreeCAD.app/Contents/Resources/lib'
if FREECAD_PATH not in sys.path:
    sys.path.append(FREECAD_PATH)

# generate_building_fem_analyzeモジュールの強制リロード
if 'generate_building_fem_analyze' in sys.modules:
    del sys.modules['generate_building_fem_analyze']

import random
import json
import pandas as pd
import time
from generate_building_fem_analyze import create_building_and_analyze

# サンプルデータを生成
samples = []
rng = random.Random(12345)  # シード固定

print("安全率とコストの相関テスト")
print("=" * 60)

# 10サンプル生成
for i in range(10):
    print(f"\nサンプル {i+1}/10:")
    
    # パラメータ生成（構造部材サイズを変化させる）
    bc = rng.randint(400, 1000)  # 柱幅を広範囲に
    hc = rng.randint(400, 1000)  # 柱高さを広範囲に
    tf = rng.randint(200, 600)   # スラブ厚を変化
    tr = rng.randint(200, 600)
    tw_ext = rng.randint(300, 500)
    
    dv = {
        'Lx': rng.uniform(8.0, 12.0),
        'Ly': rng.uniform(8.0, 12.0),
        'H1': rng.uniform(2.8, 3.5),
        'H2': rng.uniform(2.6, 3.2),
        'tf': tf,
        'tr': tr,
        'bc': bc,
        'hc': hc,
        'tw_ext': tw_ext,
        'wall_tilt_angle': rng.uniform(-30, 30),
        'window_ratio_2f': rng.uniform(0.1, 0.7),
        'roof_morph': rng.uniform(0.0, 0.9),
        'roof_shift': rng.uniform(-0.4, 0.4),
        'balcony_depth': rng.uniform(1.0, 3.5),
        # 材料は固定（コンクリート）で比較
        'material_columns': 0,
        'material_floor1': 0,
        'material_floor2': 0,
        'material_roof': 0,
        'material_walls': 0,
        'material_balcony': 0
    }
    
    output_path = f"test_safety_cost_{i+1}.FCStd"
    
    try:
        result = create_building_and_analyze(dv, output_path, evaluate_fem=True)
        
        if result['evaluation_status'] == 'success':
            print(f"  柱サイズ: {bc}x{hc} mm")
            print(f"  スラブ厚: {tf}/{tr} mm")
            print(f"  安全率: {result['safety_factor']:.2f}")
            print(f"  コスト: {result['cost_per_sqm']:,.0f} 円/m²")
            
            samples.append({
                'sample_id': i+1,
                'bc': bc,
                'hc': hc,
                'tf': tf,
                'tr': tr,
                'avg_column_size': (bc + hc) / 2,
                'avg_slab_thickness': (tf + tr) / 2,
                'safety_factor': result['safety_factor'],
                'cost_per_sqm': result['cost_per_sqm'],
                'total_cost': result['total_cost']
            })
    except Exception as e:
        print(f"  エラー: {e}")

# 結果をDataFrameに変換
if samples:
    df = pd.DataFrame(samples)
    
    # 相関分析
    print("\n" + "=" * 60)
    print("相関分析結果:")
    print(f"安全率とコストの相関係数: {df['safety_factor'].corr(df['cost_per_sqm']):.3f}")
    print(f"柱サイズとコストの相関係数: {df['avg_column_size'].corr(df['cost_per_sqm']):.3f}")
    print(f"スラブ厚とコストの相関係数: {df['avg_slab_thickness'].corr(df['cost_per_sqm']):.3f}")
    print(f"柱サイズと安全率の相関係数: {df['avg_column_size'].corr(df['safety_factor']):.3f}")
    
    # CSVに保存
    df.to_csv('test_safety_cost_correlation.csv', index=False)
    print("\n結果をtest_safety_cost_correlation.csvに保存しました")