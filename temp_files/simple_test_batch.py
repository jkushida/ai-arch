#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
シンプルなテストバッチ（1サンプルのみ）
"""

import sys
import os

# FreeCAD環境の初期化
FREECAD_PATH = '/Applications/FreeCAD.app/Contents/Resources/lib'
if FREECAD_PATH not in sys.path:
    sys.path.append(FREECAD_PATH)

import pandas as pd
import numpy as np

# generate_building_fem_analyzeモジュールの強制リロード
if 'generate_building_fem_analyze' in sys.modules:
    del sys.modules['generate_building_fem_analyze']

from generate_building_fem_analyze import evaluate_building_from_params

print("シンプルテストバッチ開始")
print("=" * 60)

# CSV初期化
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

# 1サンプルのみテスト
dv = {
    'Lx': 10.0,
    'Ly': 10.0,
    'H1': 3.0,
    'H2': 3.0,
    'tf': 400,
    'tr': 400,
    'bc': 800,
    'hc': 800,
    'tw_ext': 400,
    'wall_tilt_angle': 0.0,
    'window_ratio_2f': 0.3,
    'roof_morph': 0.5,
    'roof_shift': 0.0,
    'balcony_depth': 1.5,
    'material_columns': 0,  # コンクリート
    'material_floor1': 0,
    'material_floor2': 0,
    'material_roof': 0,
    'material_walls': 0,
    'material_balcony': 0
}

print(f"\nテストパラメータ:")
print(f"  建物サイズ: {dv['Lx']}m x {dv['Ly']}m")
print(f"  柱サイズ: {dv['bc']}mm x {dv['hc']}mm")

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
        row['fcstd_path'] = ''
        
        results.append(row)
        
        print(f"\n✅ 評価成功:")
        print(f"  安全率: {row['safety_factor']:.2f}")
        print(f"  コスト: {row['cost_per_sqm']:,.0f} 円/m²")
        print(f"  評価時間: {eval_time:.1f}秒")
    else:
        print(f"\n❌ 評価失敗: {result.get('message', 'Unknown error')}")
        
except Exception as e:
    print(f"\n❌ エラー発生: {e}")
    import traceback
    traceback.print_exc()

# CSV保存
if results:
    df = pd.DataFrame(results, columns=columns)
    df.to_csv('test_result.csv', index=False)
    print(f"\n結果をtest_result.csvに保存しました")
    
    # 相関計算
    if len(df) > 1:
        corr = df['safety_factor'].corr(df['cost_per_sqm'])
        print(f"\n📊 安全率とコストの相関係数: {corr:.3f}")
else:
    print("\n有効な結果がありません")

print("\n" + "=" * 60)