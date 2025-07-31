#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
サンプル95のパラメータでFEM解析をテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generate_building_fem_analyze import evaluate_building_from_params
import time

def test_sample95():
    # サンプル95のパラメータ
    params = {
        'Lx': 10.11,
        'Ly': 9.73,
        'H1': 3.26,
        'H2': 2.85,
        'tf': 285,
        'tr': 242,
        'bc': 826,
        'hc': 655,
        'tw_ext': 150,  # デフォルト値
        'wall_tilt_angle': 0.0,  # デフォルト値
        'window_ratio_2f': 0.0,  # デフォルト値
        'roof_morph': 0.0,  # デフォルト値
        'roof_shift': 0.0,  # デフォルト値
        'balcony_depth': 0.0,  # デフォルト値
        'floors': 2
    }
    
    print("=== サンプル95のテスト開始 ===")
    print(f"パラメータ: {params}")
    
    # 詳細ログを有効化
    os.environ['FEM_DETAILED_LOG'] = '1'
    os.environ['FEM_SAMPLE_ID'] = '[サンプル95]'
    
    start_time = time.time()
    try:
        print(f"FEM解析開始: {time.strftime('%H:%M:%S')}")
        result = evaluate_building_from_params(params, save_fcstd=True, fcstd_path="test_sample95.FCStd")
        elapsed = time.time() - start_time
        
        print(f"\n=== 解析成功 ===")
        print(f"経過時間: {elapsed:.1f}秒")
        print(f"安全率: {result['safety']['overall_safety_factor']:.3f}")
        print(f"最大変位: {result['raw_fem_results']['max_displacement']:.3f} mm")
        print(f"最大応力: {result['raw_fem_results']['max_stress']:.3f} MPa")
        
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n=== エラー発生 ===")
        print(f"経過時間: {elapsed:.1f}秒")
        print(f"エラー: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        os.environ.pop('FEM_DETAILED_LOG', None)
        os.environ.pop('FEM_SAMPLE_ID', None)

if __name__ == "__main__":
    test_sample95()