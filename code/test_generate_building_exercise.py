#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_generate_building_exercise.py
===================================
演習用の建物評価テストスクリプト
単一変数実験と変数ペア実験をサポート
結果をtest_results.csvに追記形式で保存
"""

import sys
import os
import csv
from datetime import datetime
import time
import glob
import argparse
import itertools

# 現在のディレクトリのみをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# VERBOSE出力を無効化（大量実験のため）
os.environ['VERBOSE_OUTPUT'] = 'False'

# モジュールをインポート
from generate_building_fem_analyze import evaluate_building_from_params

# ベースライン（デフォルト）パラメータ
baseline_params = {
    # 建物寸法
    'Lx': 8.0,           # 建物幅 [m]
    'Ly': 8.0,           # 建物奥行 [m]
    'H1': 3.0,           # 1階高さ [m]
    'H2': 3.0,           # 2階高さ [m]
    
    # 構造部材寸法
    'tf': 250,           # 床スラブ厚 [mm]
    'tr': 200,           # 屋根スラブ厚 [mm]
    'bc': 400,           # 柱幅 [mm]
    'hc': 400,           # 柱高さ [mm]
    'tw_ext': 150,       # 外壁厚 [mm]
    
    # その他の設計パラメータ
    'wall_tilt_angle': 0,       # 壁傾斜角（垂直）
    'window_ratio_2f': 0.4,      # 2階窓面積比
    'roof_morph': 0.5,           # 屋根形態（標準）
    'roof_shift': 0.5,           # 屋根シフト（対称）
    'balcony_depth': 1.5,        # バルコニー奥行
    
    # 材料パラメータ（0:コンクリート, 1:木材）
    'material_columns': 0,       # 柱材料
    'material_floor1': 0,        # 1階床材料
    'material_floor2': 0,        # 2階床材料
    'material_roof': 0,          # 屋根材料
    'material_walls': 0,         # 外壁材料
    'material_balcony': 0        # バルコニー材料
}

def run_single_experiment(params, experiment_name=""):
    """単一実験を実行して結果を返す"""
    try:
        # タイムスタンプ生成
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # FCStdファイル名
        if experiment_name:
            fcstd_filename = f"test_{experiment_name}_{timestamp}.FCStd"
        else:
            fcstd_filename = f"test_{timestamp}.FCStd"
        
        # 実行時間計測開始
        start_time = time.time()
        
        # 評価関数を実行
        results = evaluate_building_from_params(
            params,
            save_fcstd=True,
            fcstd_path=fcstd_filename
        )
        
        # 実行時間計測終了
        evaluation_time = time.time() - start_time
        
        # 結果を辞書形式で返す
        if results['status'] == 'Success':
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'fcstd_path': fcstd_filename,
                'params': params,
                'safety_factor': results['safety']['overall_safety_factor'],
                'cost_per_sqm': results['economic']['cost_per_sqm'],
                'total_cost': results['economic']['total_cost'],
                'co2_per_sqm': results['environmental']['co2_per_sqm'],
                'comfort_score': results['comfort']['comfort_score'],
                'constructability_score': results['constructability']['constructability_score'],
                'floor_area': params['Lx'] * params['Ly'],
                'evaluation_status': 'Success',
                'evaluation_time_s': round(evaluation_time, 1)
            }
        else:
            return {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'fcstd_path': fcstd_filename,
                'params': params,
                'safety_factor': None,
                'cost_per_sqm': None,
                'total_cost': None,
                'co2_per_sqm': None,
                'comfort_score': None,
                'constructability_score': None,
                'floor_area': params['Lx'] * params['Ly'],
                'evaluation_status': f"Failed: {results.get('message', 'Unknown error')}",
                'evaluation_time_s': round(evaluation_time, 1)
            }
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

def save_to_csv(result, csv_filename="test_results.csv"):
    """結果をCSVファイルに保存（タイムスタンプの次にFCStdパス）"""
    if not result:
        return
    
    # パラメータ説明の定義
    param_descriptions = {
        'Lx': '建物幅[m]',
        'Ly': '建物奥行[m]',
        'H1': '1階高さ[m]',
        'H2': '2階高さ[m]',
        'tf': '床スラブ厚[mm]',
        'tr': '屋根スラブ厚[mm]',
        'bc': '柱幅[mm]',
        'hc': '柱高さ[mm]',
        'tw_ext': '外壁厚[mm]',
        'wall_tilt_angle': '壁傾斜角[度]',
        'window_ratio_2f': '2階窓面積比',
        'roof_morph': '屋根形態',
        'roof_shift': '屋根シフト',
        'balcony_depth': 'バルコニー奥行[m]',
        'material_columns': '柱材料(0:ｺﾝｸﾘｰﾄ,1:木材)',
        'material_floor1': '1階床材料(0:ｺﾝｸﾘｰﾄ,1:木材)',
        'material_floor2': '2階床材料(0:ｺﾝｸﾘｰﾄ,1:木材)',
        'material_roof': '屋根材料(0:ｺﾝｸﾘｰﾄ,1:木材)',
        'material_walls': '外壁材料(0:ｺﾝｸﾘｰﾄ,1:木材)',
        'material_balcony': 'バルコニー材料(0:ｺﾝｸﾘｰﾄ,1:木材)'
    }
    
    result_descriptions = {
        'timestamp': 'タイムスタンプ',
        'fcstd_path': 'FreeCADファイルパス',
        'cost_per_sqm': '建設コスト[円/m²]',
        'co2_per_sqm': 'CO2排出量[kg-CO2/m²]',
        'comfort_score': '快適性スコア',
        'constructability_score': '施工性スコア',
        'safety_factor': '安全率',
        'total_cost': '総工費[円]',
        'floor_area': '床面積[m²]',
        'evaluation_status': '評価ステータス',
        'evaluation_time_s': '評価時間[秒]'
    }
    
    # ヘッダー行の作成
    headers = []
    descriptions = []
    values = []
    
    # タイムスタンプを最初に
    headers.append('timestamp')
    descriptions.append(result_descriptions['timestamp'])
    values.append(result['timestamp'])
    
    # FCStdパスを2番目に
    headers.append('fcstd_path')
    descriptions.append(result_descriptions['fcstd_path'])
    values.append(result['fcstd_path'])
    
    # 設計変数を追加（パラメータの順番通り）
    param_order = ['Lx', 'Ly', 'H1', 'H2', 'tf', 'tr', 'bc', 'hc', 'tw_ext',
                   'wall_tilt_angle', 'window_ratio_2f', 'roof_morph', 'roof_shift', 'balcony_depth',
                   'material_columns', 'material_floor1', 'material_floor2', 'material_roof',
                   'material_walls', 'material_balcony']
    
    for key in param_order:
        headers.append(key)
        descriptions.append(param_descriptions.get(key, key))
        values.append(result['params'].get(key, ''))
    
    # 評価結果を追加
    result_keys = ['cost_per_sqm', 'co2_per_sqm', 'comfort_score', 
                   'constructability_score', 'safety_factor', 'total_cost',
                   'floor_area', 'evaluation_status', 'evaluation_time_s']
    
    for key in result_keys:
        headers.append(key)
        descriptions.append(result_descriptions.get(key, key))
        values.append(result.get(key, ''))
    
    # CSVファイルに書き込み
    file_exists = os.path.exists(csv_filename)
    with open(csv_filename, 'a', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        
        # ファイルが新規作成の場合のみヘッダーを書き込む
        if not file_exists:
            writer.writerow(descriptions)  # 日本語説明行
            writer.writerow(headers)       # 英語変数名行
        
        # 値の行を追加
        writer.writerow(values)

def single_variable_experiment(variable_name, test_values, csv_filename="test_results.csv"):
    """Step 1: 単一変数実験"""
    print(f"\n=== 単一変数実験: {variable_name} ===")
    print(f"テスト値: {test_values}")
    
    results = []
    for i, value in enumerate(test_values):
        print(f"\n実験 {i+1}/{len(test_values)}: {variable_name} = {value}")
        
        # ベースラインパラメータをコピー
        params = baseline_params.copy()
        params[variable_name] = value
        
        # 実験実行
        result = run_single_experiment(params, f"{variable_name}_{value}")
        
        if result:
            save_to_csv(result, csv_filename)
            results.append(result)
            print(f"  ✅ 安全率: {result['safety_factor']:.3f}, "
                  f"コスト: {result['cost_per_sqm']:,.0f} 円/m², "
                  f"CO2: {result['co2_per_sqm']:.1f} kg/m²")
        else:
            print(f"  ❌ 実験失敗")
    
    return results

def variable_pair_experiment(var1_name, var1_values, var2_name, var2_values, csv_filename="test_results.csv"):
    """Step 2: 変数ペア実験"""
    print(f"\n=== 変数ペア実験: {var1_name} × {var2_name} ===")
    print(f"{var1_name}: {var1_values}")
    print(f"{var2_name}: {var2_values}")
    
    results = []
    total = len(var1_values) * len(var2_values)
    count = 0
    
    for val1 in var1_values:
        for val2 in var2_values:
            count += 1
            print(f"\n実験 {count}/{total}: {var1_name}={val1}, {var2_name}={val2}")
            
            # ベースラインパラメータをコピー
            params = baseline_params.copy()
            params[var1_name] = val1
            params[var2_name] = val2
            
            # 実験実行
            result = run_single_experiment(params, f"{var1_name}{val1}_{var2_name}{val2}")
            
            if result:
                save_to_csv(result, csv_filename)
                results.append(result)
                print(f"  ✅ 安全率: {result['safety_factor']:.3f}, "
                      f"コスト: {result['cost_per_sqm']:,.0f} 円/m²")
            else:
                print(f"  ❌ 実験失敗")
    
    return results

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='建物評価演習実験スクリプト')
    parser.add_argument('--mode', type=str, default='demo',
                        choices=['demo', 'single', 'pair', 'all'],
                        help='実行モード: demo(デモ), single(単一変数), pair(変数ペア), all(全実験)')
    parser.add_argument('--variable', type=str, default='Lx',
                        help='単一変数実験で変更する変数名')
    parser.add_argument('--values', type=str, default='6,8,10,12,14',
                        help='テスト値（カンマ区切り）')
    parser.add_argument('--var1', type=str, default='Lx',
                        help='変数ペア実験の変数1')
    parser.add_argument('--var1_values', type=str, default='6,8,10',
                        help='変数1のテスト値')
    parser.add_argument('--var2', type=str, default='Ly',
                        help='変数ペア実験の変数2')
    parser.add_argument('--var2_values', type=str, default='6,8,10',
                        help='変数2のテスト値')
    parser.add_argument('--csv', type=str, default='test_results.csv',
                        help='出力CSVファイル名')
    
    args = parser.parse_args()
    
    print("=== 建物評価演習実験 開始 ===")
    print(f"出力CSVファイル: {args.csv}")
    
    if args.mode == 'demo':
        # デモモード：ベースラインの1サンプルのみ実行
        print("\n=== デモモード：ベースライン評価 ===")
        result = run_single_experiment(baseline_params, "baseline")
        if result:
            save_to_csv(result, args.csv)
            print(f"\n✅ 結果を {args.csv} に保存しました")
    
    elif args.mode == 'single':
        # 単一変数実験
        values = [float(v) if '.' in v else int(v) for v in args.values.split(',')]
        single_variable_experiment(args.variable, values, args.csv)
    
    elif args.mode == 'pair':
        # 変数ペア実験
        var1_values = [float(v) if '.' in v else int(v) for v in args.var1_values.split(',')]
        var2_values = [float(v) if '.' in v else int(v) for v in args.var2_values.split(',')]
        variable_pair_experiment(args.var1, var1_values, args.var2, var2_values, args.csv)
    
    elif args.mode == 'all':
        # 演習Step1の全実験を実行
        print("\n=== 演習Step1: 全単一変数実験を実行 ===")
        
        experiments = [
            ('Lx', [6, 8, 10, 12, 14]),
            ('bc', [200, 300, 400, 500, 600]),
            ('tf', [150, 200, 250, 300, 350]),
            ('H1', [2.5, 2.8, 3.0, 3.3, 3.6]),
            ('wall_tilt_angle', [-20, -10, 0, 10, 20]),
            ('roof_morph', [0, 0.25, 0.5, 0.75, 1.0]),
            ('window_ratio_2f', [0.2, 0.3, 0.4, 0.5, 0.6]),
            ('material_columns', [0, 0.25, 0.5, 0.75, 1.0])
        ]
        
        for var_name, test_values in experiments:
            single_variable_experiment(var_name, test_values, args.csv)
    
    print("\n=== 実験完了 ===")
    print(f"結果は {args.csv} に保存されました")

if __name__ == "__main__":
    main()