#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テスト用サンプルを生成して相関を確認
"""

import sys
import os

# FreeCAD環境の初期化
FREECAD_PATH = '/Applications/FreeCAD.app/Contents/Resources/lib'
if FREECAD_PATH not in sys.path:
    sys.path.append(FREECAD_PATH)

import pandas as pd
import numpy as np
import random

# generate_building_fem_analyzeモジュールの強制リロード
if 'generate_building_fem_analyze' in sys.modules:
    del sys.modules['generate_building_fem_analyze']

from generate_building_fem_analyze import evaluate_building_from_params

print("テストサンプル生成開始")
print("=" * 60)

# CSV列定義
columns = [
    'Lx', 'Ly', 'H1', 'H2', 'tf', 'tr', 'bc', 'hc', 'tw_ext',
    'wall_tilt_angle', 'window_ratio_2f', 'roof_morph', 'roof_shift', 'balcony_depth',
    'material_columns', 'material_floor1', 'material_floor2', 
    'material_roof', 'material_walls', 'material_balcony',
    'cost_per_sqm', 'co2_per_sqm', 'comfort_score', 'constructability_score',
    'safety_factor', 'total_cost', 'floor_area', 'design_pattern',
    'evaluation_status', 'evaluation_time_s', 'fcstd_path'
]

results = []
rng = random.Random(42)

# 10サンプル生成（構造サイズを系統的に変化）
for i in range(10):
    # 構造サイズを段階的に変化
    size_factor = 0.6 + i * 0.1  # 0.6 ~ 1.5
    
    dv = {
        'Lx': 10.0,
        'Ly': 10.0,
        'H1': 3.0,
        'H2': 3.0,
        'tf': int(300 * size_factor),
        'tr': int(300 * size_factor),
        'bc': int(600 * size_factor),
        'hc': int(600 * size_factor),
        'tw_ext': int(300 * size_factor),
        'wall_tilt_angle': 0.0,
        'window_ratio_2f': 0.3,
        'roof_morph': 0.5,
        'roof_shift': 0.0,
        'balcony_depth': 1.5,
        'material_columns': rng.choice([0, 1, 2]),  # ランダムな材料
        'material_floor1': 0,
        'material_floor2': 0,
        'material_roof': 0,
        'material_walls': 0,
        'material_balcony': 0
    }
    
    print(f"\nサンプル {i+1}/10:")
    print(f"  サイズ係数: {size_factor:.1f}")
    print(f"  柱サイズ: {dv['bc']}x{dv['hc']} mm")
    print(f"  材料: {['コンクリート', '木材', 'CLT'][dv['material_columns']]}")
    
    start_time = pd.Timestamp.now()
    
    try:
        result = evaluate_building_from_params(dv, save_fcstd=False)
        
        end_time = pd.Timestamp.now()
        eval_time = (end_time - start_time).total_seconds()
        
        if result.get('status') == 'Success':
            row = {**dv}
            row['cost_per_sqm'] = result.get('economic', {}).get('cost_per_sqm', 0.0)
            row['co2_per_sqm'] = result.get('environmental', {}).get('co2_per_sqm', 0.0)
            row['comfort_score'] = result.get('comfort', {}).get('overall_comfort_score', 0.0)
            row['constructability_score'] = result.get('constructability', {}).get('overall_score', 0.0)
            row['safety_factor'] = result.get('safety', {}).get('overall_safety_factor', 0.0)
            row['total_cost'] = result.get('economic', {}).get('total_construction_cost', 0.0)
            row['floor_area'] = result.get('building_info', {}).get('floor_area', 0.0)
            row['design_pattern'] = result.get('building_info', {}).get('design_pattern', '')
            row['evaluation_status'] = 'success'
            row['evaluation_time_s'] = eval_time
            row['fcstd_path'] = f'test_sample_{i+1}.FCStd'
            
            results.append(row)
            
            print(f"  ✅ 成功: 安全率={row['safety_factor']:.2f}, コスト={row['cost_per_sqm']:,.0f} 円/m²")
        else:
            print(f"  ❌ 失敗: {result.get('message', 'Unknown error')}")
            
    except Exception as e:
        print(f"  ❌ エラー: {e}")

# CSV保存
if results:
    df = pd.DataFrame(results, columns=columns)
    df.to_csv('test_samples.csv', index=False)
    print(f"\n結果をtest_samples.csvに保存しました")
    
    # 相関計算
    if len(df) > 1:
        corr = df['safety_factor'].corr(df['cost_per_sqm'])
        print(f"\n📊 安全率とコストの相関係数: {corr:.3f}")
        
        # 材料別の平均
        for mat in df['material_columns'].unique():
            mat_df = df[df['material_columns'] == mat]
            if len(mat_df) > 0:
                mat_name = ['コンクリート', '木材', 'CLT'][mat]
                avg_cost = mat_df['cost_per_sqm'].mean()
                avg_safety = mat_df['safety_factor'].mean()
                print(f"\n{mat_name}:")
                print(f"  平均コスト: {avg_cost:,.0f} 円/m²")
                print(f"  平均安全率: {avg_safety:.2f}")
else:
    print("\n有効な結果がありません")

print("\n" + "=" * 60)