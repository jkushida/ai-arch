#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_generate_building.py
========================
generate_building_fem_analyze.pyのテスト用スクリプト
設計変数と結果をCSVファイルに出力
"""

import sys
import os
import csv
from datetime import datetime
import time
import glob

# 現在のディレクトリのみをPythonパスに追加（親ディレクトリは追加しない）
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# VERBOSE出力を有効化してデバッグ
os.environ['VERBOSE_OUTPUT'] = 'True'

# モジュールをインポート
from generate_building_fem_analyze import evaluate_building_from_params

# タイムスタンプ付きファイル名を使用するかどうか
USE_TIMESTAMP = False  # True: タイムスタンプ付き, False: 固定ファイル名
USE_TIMESTAMP_FOR_FCSTD = True  # FCStdファイルにもタイムスタンプを付ける


# テスト用パラメータ
default_params = {
    # 建物寸法
    'Lx': 10.0,           # 建物幅 [m]
    'Ly': 9.0,           # 建物奥行 [m]
    'H1': 3.0,           # 1階高さ [m]
    'H2': 2.8,           # 2階高さ [m]
    
    # 構造部材寸法
    'tf': 400,           # 床スラブ厚 [mm]
    'tr': 450,           # 屋根スラブ厚 [mm]
    'bc': 500,           # 柱幅 [mm]
    'hc': 600,           # 柱高さ [mm]
    'tw_ext': 450,       # 外壁厚 [mm]
    
    # その他の設計パラメータ
    'wall_tilt_angle': -25,      # 壁傾斜角
    'window_ratio_2f': 0.7,      # 2階窓面積比
    'roof_morph': 0.9,           # 屋根形態
    'roof_shift': 0.7,           # 屋根シフト
    'balcony_depth': 1.8         # バルコニー奥行
}

# 材料パラメータ（0:コンクリート, 1:木材）
material_params = {
    'material_columns': 0,      # 柱材料
    'material_floor1': 0,       # 1階床材料
    'material_floor2': 0,       # 2階床材料
    'material_roof': 0,         # 屋根材料
    'material_walls': 1,        # 外壁材料
    'material_balcony': 0       # バルコニー材料
}




print("=== 建物評価テスト実行開始 ===")

# パラメータを結合
test_params = {**default_params, **material_params}

# 1サンプルのみ実行
print("\n入力パラメータ:")
for key, value in test_params.items():
    if key.startswith('material_'):
        material = '木材' if value == 1 else 'コンクリート'
        print(f"  {key}: {value} ({material})")
    else:
        print(f"  {key}: {value}")

print("\n解析実行中...")

# 実行時間計測開始
start_time = time.time()

try:
    # FCStdファイル名の生成
    if USE_TIMESTAMP_FOR_FCSTD:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        fcstd_filename = f"test_building_{timestamp}.FCStd"
    else:
        fcstd_filename = "test_building.FCStd"
    
    # 評価関数を実行
    results = evaluate_building_from_params(
        test_params,
        save_fcstd=True,
        fcstd_path=fcstd_filename
    )
    
    # 実行時間計測終了
    evaluation_time = time.time() - start_time
    
    # 結果を表示
    if results['status'] == 'Success':
        print("\n=== 解析結果 ===")
        
        # 安全性
        print("\n【安全性】")
        safety = results['safety']
        print(f"  安全率: {safety['overall_safety_factor']:.3f}")
        print(f"  最大変位: {safety['max_displacement_mm']:.3f} mm")
        if safety.get('max_stress_mpa') is not None:
            print(f"  最大応力: {safety['max_stress_mpa']:.3f} MPa")
        
        # 経済性
        print("\n【経済性】")
        economic = results['economic']
        print(f"  建設コスト: {economic['cost_per_sqm']:,.0f} 円/㎡")
        print(f"  総工費: {economic['total_cost']:,.0f} 円")
        
        # 環境性
        print("\n【環境性】")
        environmental = results['environmental']
        print(f"  CO2排出量: {environmental['co2_per_sqm']:.1f} kg-CO2/㎡")
        print(f"  最適化ポテンシャル: {environmental['optimization_potential']*100:.1f}%")
        
        # 快適性
        print("\n【快適性】")
        comfort = results['comfort']
        print(f"  快適性スコア: {comfort['comfort_score']:.2f}/10")
        print(f"    空間の広がり: {comfort['spaciousness_score']:.2f}")
        print(f"    採光・眺望: {comfort['lighting_score']:.2f}")
        print(f"    開放感: {comfort['piloti_openness_score']:.2f}")
        print(f"    プライバシー: {comfort['privacy_score']:.2f}")
        
        # 施工性
        print("\n【施工性】")
        constructability = results['constructability']
        print(f"  施工性スコア: {constructability['constructability_score']:.2f}/10")
        
        # 総合評価（存在する場合のみ表示）
        if 'overall_score' in results:
            print("\n【総合評価】")
            print(f"  総合スコア: {results['overall_score']:.2f}")
        
        # CSV出力
        if USE_TIMESTAMP:
            csv_filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        else:
            csv_filename = "test_results.csv"
        
        # CSVファイルに書き込み（追記モード）
        file_exists = os.path.exists(csv_filename)
        with open(csv_filename, 'a', newline='', encoding='utf-8-sig') as csvfile:
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
            'cost_per_sqm': '建設コスト[円/m²]',
            'co2_per_sqm': 'CO2排出量[kg-CO2/m²]',
            'comfort_score': '快適性スコア',
            'constructability_score': '施工性スコア',
            'safety_factor': '安全率',
            'total_cost': '総工費[円]',
            'floor_area': '床面積[m²]',
            'evaluation_status': '評価ステータス',
            'evaluation_time_s': '評価時間[秒]',
            'fcstd_path': 'FreeCADファイルパス'
            }
            
            # ヘッダー行の作成
            headers = []
            descriptions = []
            values = []
            
            # タイムスタンプを最初に追加
            headers.append('timestamp')
            descriptions.append(result_descriptions.get('timestamp', 'タイムスタンプ'))
            values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            # FCStdファイルパスを2番目に追加
            headers.append('fcstd_path')
            descriptions.append(result_descriptions.get('fcstd_path', 'FreeCADファイルパス'))
            values.append(fcstd_filename)
            
            # 設計変数を追加（順番を固定）
            param_order = ['Lx', 'Ly', 'H1', 'H2', 'tf', 'tr', 'bc', 'hc', 'tw_ext',
                           'wall_tilt_angle', 'window_ratio_2f', 'roof_morph', 'roof_shift', 'balcony_depth',
                           'material_columns', 'material_floor1', 'material_floor2', 'material_roof',
                           'material_walls', 'material_balcony']
            
            for key in param_order:
                headers.append(key)
                descriptions.append(param_descriptions.get(key, key))
                values.append(test_params.get(key, ''))
            
            # 評価結果を追加（fcstd_pathは既に追加済みなので除外）
            result_keys = [
            "cost_per_sqm",
            "co2_per_sqm",
            "comfort_score",
            "constructability_score",
            "safety_factor",
            "total_cost",
            "floor_area",
            "evaluation_status",
            "evaluation_time_s"
            ]
            
            headers.extend(result_keys)
            for key in result_keys:
                descriptions.append(result_descriptions.get(key, key))
            
            # 床面積を計算
            floor_area = test_params['Lx'] * test_params['Ly']
            
            values.extend([
            economic['cost_per_sqm'],
            environmental['co2_per_sqm'],
            comfort['comfort_score'],
            constructability['constructability_score'],
            safety['overall_safety_factor'],
            economic['total_cost'],
            floor_area,
            results['status'],  # evaluation_status
            round(evaluation_time, 1)  # evaluation_time_s (小数点以下第1位まで)
            ])
            
            # CSVライター
            writer = csv.writer(csvfile)
            
            # ファイルが新規作成の場合のみヘッダーを書き込む
            if not file_exists:
                # 日本語説明行
                writer.writerow(descriptions)
                # 英語変数名行
                writer.writerow(headers)
            
            # 値の行を追加
            writer.writerow(values)
        
        print(f"\n✅ 結果をCSVファイルに保存しました: {csv_filename}")
        
    else:
        print(f"\n❌ 解析失敗: {results.get('message', 'Unknown error')}")

except Exception as e:
    print(f"\n❌ エラーが発生しました: {e}")
    import traceback
    traceback.print_exc()

# この実行で生成された.FCBakファイルのみを削除
if 'fcstd_filename' in locals() and fcstd_filename:
    # FCStdファイル名から拡張子を除いた部分を取得
    base_name = os.path.splitext(fcstd_filename)[0]
    # 対応する.FCBakファイルを検索
    fcbak_pattern = f"{base_name}.*.FCBak"
    fcbak_files = glob.glob(fcbak_pattern)
    
    if fcbak_files:
        print(f"\n🗑️ 生成された.FCBakファイルを削除中...")
        for fcbak in fcbak_files:
            try:
                os.remove(fcbak)
                print(f"   削除: {fcbak}")
            except Exception as e:
                print(f"   削除エラー: {fcbak} - {e}")
        print(f"✅ {len(fcbak_files)}個の.FCBakファイルを削除しました")

print("\n=== テスト完了 ===")
