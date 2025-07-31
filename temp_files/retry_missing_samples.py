#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
retry_missing_samples.py
========================
simple_random_batch2.pyで作成できなかったサンプルを再試行するスクリプト

Usage:
    python retry_missing_samples.py [missing_samples.txt]
    
    または、missing_samples.txtがデフォルトで読み込まれます
"""

import sys
import os

# 現在のディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# simple_random_batch2の設定を流用
from simple_random_batch2 import (
    PARAM_RANGES, MATERIAL_PARAMS, EVALUATION_TIMEOUT,
    _generate_random_design_vector, _classify, _cleanup_freecad_memory,
    _next_fcstd_name, _timeout_handler, TimeoutError, _HAS_SIGALRM,
    VERBOSE_OUTPUT
)

import csv
import time
import signal
import random

# 引数からファイルパスを取得
if len(sys.argv) > 1:
    missing_samples_file = sys.argv[1]
else:
    missing_samples_file = os.path.join(current_dir, "missing_samples.txt")

# 欠番リストを読み込み
if not os.path.exists(missing_samples_file):
    print(f"❌ ファイルが見つかりません: {missing_samples_file}")
    print("   simple_random_batch2.py を実行して、missing_samples.txt を生成してください。")
    sys.exit(1)

missing_samples = []
with open(missing_samples_file, 'r') as f:
    for line in f:
        try:
            sample_num = int(line.strip())
            missing_samples.append(sample_num)
        except:
            pass

if not missing_samples:
    print("✅ 再試行するサンプルがありません。")
    sys.exit(0)

print("="*80)
print(f"🔧 欠番サンプル再試行スクリプト")
print(f"📋 対象サンプル: {missing_samples} (計{len(missing_samples)}個)")
print("="*80)

# fcstd_outputsディレクトリの確認
fcstd_output_dir = os.path.join(current_dir, "fcstd_outputs")
if not os.path.exists(fcstd_output_dir):
    os.makedirs(fcstd_output_dir, exist_ok=True)

# CSVファイルパス（追記モード）
csv_path = os.path.join(current_dir, "production_freecad_random_fem_evaluation2.csv")

# ヘッダー定義
header = [
    "Lx", "Ly", "H1", "H2", "tf", "tr", "bc", "hc", "tw_ext",
    "wall_tilt_angle", "window_ratio_2f", "roof_morph", "roof_shift", "balcony_depth",
    "material_columns", "material_floor1", "material_floor2", "material_roof", "material_walls", "material_balcony",
    "cost_per_sqm", "co2_per_sqm", "comfort_score", "constructability_score",
    "safety_factor", "total_cost", "floor_area", "design_pattern", "evaluation_status",
    "evaluation_time_s", "fcstd_path",
]

# CSVファイルが存在しない場合はヘッダーを書き込む
write_header = not os.path.exists(csv_path)

# モジュールをインポート
try:
    # モジュールをリロードして最新の変更を反映
    if 'generate_building_fem_analyze' in sys.modules:
        del sys.modules['generate_building_fem_analyze']
    
    from generate_building_fem_analyze import evaluate_building_from_params
    print("✅ generate_building_fem_analyze インポート成功")
except ImportError as e:
    print(f"❌ モジュールインポートエラー: {e}")
    sys.exit(1)

# 乱数生成器の準備
base_seed = 99999  # 異なるシードを使用
rng = random.Random(base_seed)

# 統計情報
n_ok = n_fail = n_timeout = 0
t0_all = time.time()
created_samples = []

# CSV開始
with open(csv_path, 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    if write_header:
        writer.writerow(header)
    
    # 各欠番サンプルを処理
    for i, sample_num in enumerate(missing_samples):
        print(f"\n{'='*60}")
        print(f"🔄 サンプル {sample_num} ({i+1}/{len(missing_samples)})")
        
        # 最大20回試行
        max_attempts = 20
        attempt_count = 0
        success = False
        
        while attempt_count < max_attempts and not success:
            attempt_count += 1
            
            # ランダムパラメータを生成
            dv = {}
            # 実数値パラメータ
            dv["Lx"] = round(rng.uniform(*PARAM_RANGES["Lx"]), 2)
            dv["Ly"] = round(rng.uniform(*PARAM_RANGES["Ly"]), 2)
            dv["H1"] = round(rng.uniform(*PARAM_RANGES["H1"]), 2)
            dv["H2"] = round(rng.uniform(*PARAM_RANGES["H2"]), 2)
            
            # 整数値パラメータ
            dv["tf"] = rng.randint(*PARAM_RANGES["tf"])
            dv["tr"] = rng.randint(*PARAM_RANGES["tr"])
            dv["bc"] = rng.randint(*PARAM_RANGES["bc"])
            dv["hc"] = rng.randint(*PARAM_RANGES["hc"])
            dv["tw_ext"] = rng.randint(*PARAM_RANGES["tw_ext"])
            
            # その他のパラメータ
            dv["wall_tilt_angle"] = round(rng.uniform(*PARAM_RANGES["wall_tilt_angle"]), 1)
            dv["window_ratio_2f"] = round(rng.uniform(*PARAM_RANGES["window_ratio_2f"]), 2)
            dv["roof_morph"] = round(rng.uniform(*PARAM_RANGES["roof_morph"]), 2)
            dv["roof_shift"] = round(rng.uniform(*PARAM_RANGES["roof_shift"]), 2)
            dv["balcony_depth"] = round(rng.uniform(*PARAM_RANGES["balcony_depth"]), 1)
            
            # 材料パラメータ
            for mat_param in MATERIAL_PARAMS:
                dv[mat_param] = rng.choice([0, 1])
            
            print(f"\n   試行 {attempt_count}/{max_attempts}")
            print(f"   パラメータ: Lx={dv['Lx']}, Ly={dv['Ly']}, tf={dv['tf']}mm, bc={dv['bc']}mm")
            
            t0 = time.time()
            fcstd_path = os.path.join(fcstd_output_dir, f"sample{sample_num}.FCStd")
            
            # 環境変数設定
            os.environ['FEM_DETAILED_LOG'] = '1'
            os.environ['FEM_SAMPLE_ID'] = f"[サンプル{sample_num}]"
            
            try:
                # タイムアウト処理
                if _HAS_SIGALRM:
                    signal.signal(signal.SIGALRM, _timeout_handler)
                    signal.alarm(EVALUATION_TIMEOUT)
                
                res = evaluate_building_from_params(dv, save_fcstd=True, fcstd_path=fcstd_path)
                
                if _HAS_SIGALRM:
                    signal.alarm(0)
                
                # 成功時のみカウントアップ
                if res['status'] == 'Success':
                    status = "success"
                    elapsed = time.time() - t0
                    
                    # 結果の取得
                    f1 = res["economic"]["cost_per_sqm"]
                    f2 = res["environmental"]["co2_per_sqm"]
                    f3 = res["comfort"]["comfort_score"]
                    f4 = res["constructability"]["constructability_score"]
                    f5 = res["safety"]["overall_safety_factor"]
                    tc = res["economic"]["total_cost"]
                    area = res["comfort"]["floor_area"]
                    
                    print(f"   ✅ 成功！安全率: {f5:.2f}, コスト: {f1:,.0f} 円/m²")
                    
                    # CSV行を作成
                    row = []
                    for col in header:
                        if col in dv:
                            row.append(dv[col])
                        elif col == "cost_per_sqm":
                            row.append(f1)
                        elif col == "co2_per_sqm":
                            row.append(f2)
                        elif col == "comfort_score":
                            row.append(f3)
                        elif col == "constructability_score":
                            row.append(f4)
                        elif col == "safety_factor":
                            row.append(f5)
                        elif col == "total_cost":
                            row.append(tc)
                        elif col == "floor_area":
                            row.append(area)
                        elif col == "design_pattern":
                            row.append(_classify(dv))
                        elif col == "evaluation_status":
                            row.append(status)
                        elif col == "evaluation_time_s":
                            row.append(elapsed)
                        elif col == "fcstd_path":
                            row.append(fcstd_path)
                        else:
                            row.append("")
                    
                    writer.writerow(row)
                    f.flush()
                    
                    n_ok += 1
                    success = True
                    created_samples.append(sample_num)
                    
                else:
                    # 失敗時は再試行
                    status = f"error:{res.get('message', 'unknown')[:30]}"
                    n_fail += 1
                    print(f"   ❌ 失敗: {res.get('message', 'unknown')}")
                    
            except TimeoutError:
                status = "timeout"
                n_timeout += 1
                print(f"   ⏱️ タイムアウト")
            except Exception as e:
                status = f"error:{str(e)[:30]}"
                n_fail += 1
                print(f"   ❌ エラー: {e}")
            finally:
                if _HAS_SIGALRM:
                    signal.alarm(0)
                _cleanup_freecad_memory()
                os.environ.pop('FEM_DETAILED_LOG', None)
                os.environ.pop('FEM_SAMPLE_ID', None)
        
        if not success:
            print(f"⚠️ サンプル {sample_num} は {max_attempts} 回試行後も作成できませんでした")

# 終了処理
elapsed_all = time.time() - t0_all
print("\n" + "="*80)
print(f"🏁 再試行処理完了")
print(f"✅ 成功: {n_ok}/{len(missing_samples)} 件")
print(f"❌ 失敗（延べ）: {n_fail} 件")
print(f"⏱️ タイムアウト（延べ）: {n_timeout} 件")
print(f"🕒 合計時間: {elapsed_all:.1f} 秒 ({elapsed_all/60:.1f} 分)")

if created_samples:
    print(f"\n📊 作成成功したサンプル: {created_samples}")

# 最終確認
final_missing = []
for sample_num in missing_samples:
    if not os.path.exists(os.path.join(fcstd_output_dir, f"sample{sample_num}.FCStd")):
        final_missing.append(sample_num)

if final_missing:
    print(f"\n⚠️ 依然として未作成のサンプル: {final_missing}")
    # 更新された欠番リストを保存
    with open(missing_samples_file, 'w') as f:
        for sample_num in final_missing:
            f.write(f"{sample_num}\n")
else:
    print(f"\n🎉 全ての欠番サンプルが作成されました！")
    # 欠番リストファイルを削除
    if os.path.exists(missing_samples_file):
        os.remove(missing_samples_file)

print("="*80)