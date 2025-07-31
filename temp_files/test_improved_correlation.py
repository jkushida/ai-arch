#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改善後の安全率とコストの相関をテストするスクリプト
"""

import sys
import os

# FreeCAD環境の初期化
FREECAD_PATH = '/Applications/FreeCAD.app/Contents/Resources/lib'
if FREECAD_PATH not in sys.path:
    sys.path.append(FREECAD_PATH)

import random
import pandas as pd
import numpy as np

# generate_building_fem_analyzeモジュールの強制リロード
if 'generate_building_fem_analyze' in sys.modules:
    del sys.modules['generate_building_fem_analyze']

from generate_building_fem_analyze import evaluate_building_from_params

# テストサンプルを生成
samples = []
rng = random.Random(42)  # シード固定

print("安全率とコストの相関改善テスト")
print("=" * 60)

# 10サンプル生成（様々な安全率を実現するパラメータ）
for i in range(10):
    print(f"\nサンプル {i+1}/10:")
    
    # 安全率を変化させるため、構造部材サイズを系統的に変化
    # 小さい部材 → 低安全率、大きい部材 → 高安全率
    size_factor = 0.5 + i * 0.2  # 0.5 ~ 2.3
    
    bc = int(300 * size_factor)  # 150 ~ 690
    hc = int(400 * size_factor)  # 200 ~ 920
    tf = int(200 * size_factor)  # 100 ~ 460
    tr = int(150 * size_factor)  # 75 ~ 345
    tw_ext = int(200 * size_factor)  # 100 ~ 460
    
    # 材料選択（RC中心でテスト）
    material = 0  # コンクリート
    
    dv = {
        'Lx': 10.0,  # 固定
        'Ly': 10.0,  # 固定
        'H1': 3.0,   # 固定
        'H2': 3.0,   # 固定
        'tf': tf,
        'tr': tr,
        'bc': bc,
        'hc': hc,
        'tw_ext': tw_ext,
        'wall_tilt_angle': 0.0,  # 固定
        'window_ratio_2f': 0.3,  # 固定
        'roof_morph': 0.5,       # 固定
        'roof_shift': 0.0,       # 固定
        'balcony_depth': 1.5,    # 固定
        'material_columns': material,
        'material_floor1': material,
        'material_floor2': material,
        'material_roof': material,
        'material_walls': material,
        'material_balcony': material
    }
    
    output_path = f"test_correlation_{i+1}.FCStd"
    
    try:
        result = evaluate_building_from_params(dv, save_fcstd=False)
        
        if result.get('status') == 'Success':
            safety_factor = result.get('safety', {}).get('overall_safety_factor', 0.0)
            cost_per_sqm = result.get('economic', {}).get('cost_per_sqm', 0.0)
            seismic_grade = result.get('economic', {}).get('seismic_grade', '')
            
            print(f"  部材サイズ係数: {size_factor:.1f}")
            print(f"  柱サイズ: {bc}x{hc} mm")
            print(f"  安全率: {safety_factor:.2f}")
            print(f"  耐震グレード: {seismic_grade}")
            print(f"  コスト: {cost_per_sqm:,.0f} 円/m²")
            
            samples.append({
                'sample_id': i+1,
                'size_factor': size_factor,
                'bc': bc,
                'hc': hc,
                'tf': tf,
                'tr': tr,
                'avg_column_size': (bc + hc) / 2,
                'avg_slab_thickness': (tf + tr) / 2,
                'safety_factor': safety_factor,
                'cost_per_sqm': cost_per_sqm,
                'seismic_grade': seismic_grade
            })
    except Exception as e:
        print(f"  エラー: {e}")

# 結果をDataFrameに変換
if samples:
    df = pd.DataFrame(samples)
    
    # 相関分析
    print("\n" + "=" * 60)
    print("相関分析結果:")
    correlation = df['safety_factor'].corr(df['cost_per_sqm'])
    print(f"安全率とコストの相関係数: {correlation:.3f}")
    
    # 回帰分析
    from scipy import stats
    slope, intercept, r_value, p_value, std_err = stats.linregress(
        df['safety_factor'], df['cost_per_sqm']
    )
    print(f"決定係数 (R²): {r_value**2:.3f}")
    print(f"回帰直線の傾き: {slope:,.0f} 円/m²")
    print(f"p値: {p_value:.4f}")
    
    # 耐震グレード別の平均コスト
    print("\n耐震グレード別の平均コスト:")
    for grade in df['seismic_grade'].unique():
        grade_df = df[df['seismic_grade'] == grade]
        if len(grade_df) > 0:
            avg_cost = grade_df['cost_per_sqm'].mean()
            avg_safety = grade_df['safety_factor'].mean()
            print(f"  {grade}: {avg_cost:,.0f} 円/m² (平均安全率: {avg_safety:.2f})")
    
    # CSVに保存
    df.to_csv('test_improved_correlation.csv', index=False)
    print("\n結果をtest_improved_correlation.csvに保存しました")