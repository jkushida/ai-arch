#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gbest_generate_building.py
==========================
pso_gbest_history.csv の最新行（gbest）を用いて FEM解析を実行し，
結果を test_results.csv に test_generate_building.py と同じ列名・列順で出力するスクリプト
"""

import sys
import os
import csv
from datetime import datetime
import time
import glob
import pandas as pd

# 現在のディレクトリのみをPythonパスに追加（親ディレクトリは追加しない）
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# VERBOSE出力を有効化してデバッグ
os.environ['VERBOSE_OUTPUT'] = 'True'

# モジュールをインポート
from generate_building_fem_analyze import evaluate_building_from_params

# タイムスタンプ付きファイル名を使用するかどうか
USE_TIMESTAMP_FOR_FCSTD = True  # FCStdファイルにもタイムスタンプを付ける

# === CSVから最新のgbest情報を読み込み ===
csv_path = os.path.join(current_dir, "pso_output/csv/pso_gbest_history.csv")

if not os.path.exists(csv_path):
    print(f"\n❌ CSVファイルが見つかりません: {csv_path}")
    sys.exit(1)

df = pd.read_csv(csv_path)

if df.empty:
    print(f"\n❌ エラー: CSVファイルが空です。PSO 実行後にデータが生成されているか確認してください: {csv_path}")
    sys.exit(1)

try:
    latest_gbest = df.iloc[-1]  # 最後の行を取得
except IndexError as e:
    print(f"\n❌ エラー: CSVファイルから最新行を取得できません。内容を確認してください: {csv_path}")
    print(f"詳細: {e}")
    sys.exit(1)

print("\n=== 最新のgbest情報 ===")
print(latest_gbest)

# --- evaluate_building_from_params に渡す辞書を作成 ---
test_params = latest_gbest.to_dict()

# 材料パラメータをintにキャスト（0/1）
material_keys = [
    'material_columns', 'material_floor1', 'material_floor2',
    'material_roof', 'material_walls', 'material_balcony'
]
for key in material_keys:
    if key in test_params:
        test_params[key] = int(test_params[key])

print("\n=== 建物評価テスト実行開始 ===")

# 入力パラメータの表示
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
        fcstd_filename = f"gbest_building_{timestamp}.FCStd"
    else:
        fcstd_filename = "gbest_building.FCStd"
    
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
        safety = results['safety']
        print(f"  安全率: {safety['overall_safety_factor']:.3f}")
        print(f"  最大変位: {safety['max_displacement_mm']:.3f} mm")
        
        # 経済性
        economic = results['economic']
        print(f"  建設コスト: {economic['cost_per_sqm']:,.0f} 円/㎡")
        print(f"  総工費: {economic['total_cost']:,.0f} 円")
        
        # 環境性
        environmental = results['environmental']
        print(f"  CO2排出量: {environmental['co2_per_sqm']:.1f} kg-CO2/㎡")
        
        # 快適性
        comfort = results['comfort']
        print(f"  快適性スコア: {comfort['comfort_score']:.2f}/10")
        
        # 施工性
        constructability = results['constructability']
        print(f"  施工性スコア: {constructability['constructability_score']:.2f}/10")
        
        # CSV出力（test_generate_building.py と同じ日本語列名で統一）
        headers_jp = [
            "タイムスタンプ", "建物幅[m]", "建物奥行[m]", "1階高さ[m]", "2階高さ[m]",
            "床スラブ厚[mm]", "屋根スラブ厚[mm]", "柱幅[mm]", "柱高さ[mm]", "外壁厚[mm]",
            "壁傾斜角[度]", "2階窓面積比", "屋根形態", "屋根シフト", "バルコニー奥行[m]",
            "柱材料(0:ｺﾝｸﾘｰﾄ,1:木材)", "1階床材料(0:ｺﾝｸﾘｰﾄ,1:木材)", "2階床材料(0:ｺﾝｸﾘｰﾄ,1:木材)",
            "屋根材料(0:ｺﾝｸﾘｰﾄ,1:木材)", "外壁材料(0:ｺﾝｸﾘｰﾄ,1:木材)", "バルコニー材料(0:ｺﾝｸﾘｰﾄ,1:木材)",
            "建設コスト[円/m²]", "CO2排出量[kg-CO2/m²]", "快適性スコア", "施工性スコア",
            "安全率", "総工費[円]", "床面積[m²]", "評価ステータス", "評価時間[秒]", "FreeCADファイルパス"
        ]

        values = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            test_params['Lx'], test_params['Ly'], test_params['H1'], test_params['H2'],
            test_params['tf'], test_params['tr'], test_params['bc'], test_params['hc'], test_params['tw_ext'],
            test_params['wall_tilt_angle'], test_params['window_ratio_2f'], test_params['roof_morph'], test_params['roof_shift'], test_params['balcony_depth'],
            test_params['material_columns'], test_params['material_floor1'], test_params['material_floor2'],
            test_params['material_roof'], test_params['material_walls'], test_params['material_balcony'],
            economic['cost_per_sqm'], environmental['co2_per_sqm'], comfort['comfort_score'], constructability['constructability_score'],
            safety['overall_safety_factor'], economic['total_cost'], test_params['Lx'] * test_params['Ly'],
            results['status'], round(evaluation_time, 1), fcstd_filename
        ]

        csv_filename = "test_results.csv"
        file_exists = os.path.exists(csv_filename)

        with open(csv_filename, 'a', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
            if not file_exists:
                writer.writerow(headers_jp)
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
    base_name = os.path.splitext(fcstd_filename)[0]
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
