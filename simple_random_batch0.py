#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_batch.py - 【最終決定版】
=================================================
FreeCADの特殊なPython実行環境に完全対応した、安定逐次処理スクリプト。
全ての実行ロジックをグローバルスコープに直接記述することで、確実な動作を目指す。

【実行方法】
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd run_batch.py
"""
import sys
import os
import shutil
import random
import time
import csv
import gc
import signal

# --- グローバル設定 ---
N_SAMPLES = 300  # 収集目標とする「成功」サンプル数
EVALUATION_TIMEOUT_SECONDS = 30 # ハングアップ防止のため、タイムアウトを十分に長く設定

# --- FreeCADの初期化とチェック ---
try:
    import FreeCAD as App
    App.Console.SetStatus("Console", "Log", False); App.Console.SetStatus("Console", "Msg", False)
    App.Console.SetStatus("Console", "Wrn", False); App.Console.SetStatus("Console", "Err", False)
    print("✅ FreeCADモジュール検出、コンソール出力を抑制。")
except ImportError:
    print("❌ FreeCAD環境外です。このスクリプトは freecadcmd で実行してください。")
    sys.exit(1)

# --- パラメータ範囲の定義 ---
PARAM_RANGES = {
    "Lx": (8.0, 15.0), "Ly": (8.0, 15.0), "H1": (2.6, 4.2), "H2": (2.6, 3.8),
    "tf": (180, 450), "tr": (150, 350), "bc": (300, 850), "hc": (300, 750),
    "tw_ext": (150, 320), "wall_tilt_angle": (-30.0, 30.0), "window_ratio_2f": (0.1, 0.7),
    "roof_morph": (0.0, 0.7), "roof_shift": (-0.4, 0.4), "balcony_depth": (1.0, 3.5),
}

# --- ヘルパー関数定義 ---
def cleanup_freecad_memory():
    """メモリリーク抑制のため、FreeCADのドキュメントとメモリを徹底的に掃除する"""
    try:
        for doc in App.listDocuments().values(): App.closeDocument(doc.Name)
        if hasattr(App, 'clearDocumentCache'): App.clearDocumentCache()
        gc.collect(0); gc.collect(1); gc.collect(2)
        print("   -> 🧹 メモリクリーンアップ実行")
    except Exception as e:
        print(f"   -> ⚠️ クリーンアップ中に軽微なエラー: {e}")

class TimeoutError(Exception): pass
def timeout_handler(signum, frame):
    raise TimeoutError("Timeout")

def generate_design_vector(rng_instance):
    """ランダムな設計パラメータを生成する"""
    dv = {}
    for k, v in PARAM_RANGES.items():
        dv[k] = round(rng_instance.uniform(*v), 2) if isinstance(v[0], float) else rng_instance.randint(*v)
    return dv

# ===================================================================
#  メイン処理の開始 (関数や __main__ ブロックで囲わず、グローバルスコープで直接実行)
# ===================================================================

script_dir = os.path.dirname(os.path.abspath(__file__))
marker_path = os.path.join(script_dir, ".batch_running")

# このtry...finallyブロックが、スクリプト全体の実行を保証する
try:
    # --- 重複実行防止 ---
    if os.path.exists(marker_path):
        print("⚠️ 別のインスタンスが実行中のため終了します。")
        sys.exit(1)
    with open(marker_path, 'w') as f:
        f.write(str(os.getpid()))

    # --- 事前準備 ---
    print("\n===================================================================")
    print(f"🚀 FreeCAD安定逐次実行モード【最終決定版】")
    print(f"🎯 目標成功サンプル数: {N_SAMPLES}, タイムアウト: {EVALUATION_TIMEOUT_SECONDS}秒")
    print("===================================================================")
    
    fcstd_output_dir = os.path.join(script_dir, "fcstd_outputs")
    if os.path.exists(fcstd_output_dir): shutil.rmtree(fcstd_output_dir)
    os.makedirs(fcstd_output_dir)
    print(f"📁 出力ディレクトリ '{fcstd_output_dir}' を準備しました。")

    csv_path = os.path.join(script_dir, "production_freecad_random_fem_evaluation.csv")
    if os.path.exists(csv_path): os.remove(csv_path)
    print(f"🗑️ 既存のCSV '{csv_path}' を削除しました。")
    
    # --- 解析モジュールのインポート ---
    sys.path.append(script_dir)
    try:
        from generate_building_fem_analyze import evaluate_building_from_params
        print("✅ 解析モジュールをインポートしました。")
    except ImportError as e:
        print(f"❌ 解析モジュールのインポートに失敗: {e}"); sys.exit(1)

    # --- CSVヘッダーとカウンターの準備 ---
    header = list(PARAM_RANGES.keys()) + ["cost_per_sqm", "co2_per_sqm", "comfort_score", "constructability_score", "safety_factor", "total_cost", "floor_area", "design_pattern", "evaluation_status", "evaluation_time_s", "fcstd_path"]
    rng = random.Random(123)
    t_start_total = time.time()
    n_ok, n_fail, n_timeout = 0, 0, 0
    total_attempts = 0

    # --- メインループ ---
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=header)
        writer.writeheader()

        while n_ok < N_SAMPLES:
            total_attempts += 1
            print(f"\n--- 試行 {total_attempts} (現在、成功 {n_ok} / 目標 {N_SAMPLES}) ---")
            
            dv = generate_design_vector(rng)
            fcstd_path = os.path.join(fcstd_output_dir, f"sample_{n_ok + 1:04d}.FCStd")
            
            t_start_loop = time.time()
            status = "error"
            result_data = {}

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(EVALUATION_TIMEOUT_SECONDS)

            try:
                fem_result = evaluate_building_from_params(dv, save_fcstd=True, fcstd_path=fcstd_path)
                
                economic_res = fem_result.get("economic", {})
                environmental_res = fem_result.get("environmental", {})
                comfort_res = fem_result.get("comfort", {})
                constructability_res = fem_result.get("constructability", {})
                safety_res = fem_result.get("safety", {})
                
                result_data = {
                    "cost_per_sqm": economic_res.get("cost_per_sqm"), "total_cost": economic_res.get("total_cost"),
                    "co2_per_sqm": environmental_res.get("co2_per_sqm"),
                    "comfort_score": comfort_res.get("comfort_score"), "floor_area": comfort_res.get("floor_area"),
                    "constructability_score": constructability_res.get("constructability_score"),
                    "safety_factor": safety_res.get("overall_safety_factor"),
                }
                
                if None in result_data.values():
                    status = "incomplete_result"; n_fail += 1
                    print(f"   -> ❌ 失敗 (データ不完全) (⏱️ {time.time() - t_start_loop:.1f}s)")
                else:
                    status = "success"; n_ok += 1
                    print(f"   -> ✅ 成功 (⏱️ {time.time() - t_start_loop:.1f}s)")

            except TimeoutError:
                status = "timeout"; n_timeout += 1
                print(f"   -> ⏰ タイムアウト ({EVALUATION_TIMEOUT_SECONDS}秒)"); fcstd_path = ""
            except Exception as e:
                status = "error"; n_fail += 1
                print(f"   -> ❌ 失敗 (エラー: {e})"); fcstd_path = ""
            finally:
                signal.alarm(0)
                cleanup_freecad_memory()
            
            # 成功した場合のみCSVに書き出す
            if status == "success":
                row = {**dv, **result_data}
                row.update({
                    "evaluation_status": status, "evaluation_time_s": time.time() - t_start_loop,
                    "fcstd_path": fcstd_path, "design_pattern": "N/A",
                })
                writer.writerow({h: row.get(h) for h in header})
                f_csv.flush()

    # --- 最終結果表示 ---
    print("\n" + "="*80)
    print(f"✅ 全バッチ処理完了！ 合計時間: {time.time() - t_start_total:.1f}s")
    print(f"📊 最終結果: 成功 {n_ok}件")
    print(f"   (参考: 総試行回数 {total_attempts}回, うち失敗 {n_fail}件, タイムアウト {n_timeout}件)")
    print("="*80)

finally:
    # どんなことがあっても、スクリプト終了時に必ず実行マーカーを削除
    if os.path.exists(marker_path):
        os.remove(marker_path)
        print("\n🧹 実行マーカーを削除しました。")
