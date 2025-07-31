#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_single_analysis.py (単一解析ワーカー)
========================================
コマンドライン引数で設計パラメータを受け取り、1回だけFEM解析を実行する。
結果はJSON形式で標準出力に書き出す。
このスクリプトはメインコントローラーからサブプロセスとして呼び出される。
"""
import sys
import os
import json
import time
import gc

# FreeCADのコンソール出力を抑制
os.environ['FREECAD_CONSOLE_LOG_ALL'] = '0'

# --- このスクリプトの唯一の仕事 ---
def main():
    if len(sys.argv) != 3:
        print(json.dumps({"evaluation_status": "error: invalid arguments"}), file=sys.stderr)
        sys.exit(1)

    # コマンドライン引数からパラメータを取得
    design_vars_json = sys.argv[1]
    fcstd_path = sys.argv[2]
    
    try:
        design_vars = json.loads(design_vars_json)
    except json.JSONDecodeError:
        print(json.dumps({"evaluation_status": "error: json decode failed"}), file=sys.stderr)
        sys.exit(1)

    t0 = time.time()
    result = {}

    try:
        # このワーカープロセス内でのみFreeCAD関連モジュールをインポート
        # これにより、依存関係がこのプロセス内に閉じ込められる
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        from generate_building_fem_analyze import evaluate_building_from_params

        # 解析を実行
        res = evaluate_building_from_params(design_vars, save_fcstd=True, fcstd_path=fcstd_path)

        # 成功時の結果を整形
        result = {
            "cost_per_sqm": res["economic"]["cost_per_sqm"],
            "co2_per_sqm": res["environmental"]["co2_per_sqm"],
            "comfort_score": res["comfort"]["comfort_score"],
            "constructability_score": res["constructability"]["constructability_score"],
            "safety_factor": res["safety"]["overall_safety_factor"],
            "total_cost": res["economic"]["total_cost"],
            "floor_area": res["comfort"]["floor_area"],
            "design_pattern": classify_design(design_vars), # 分類もここで行う
            "evaluation_status": "success",
            "fcstd_path": fcstd_path,
        }

    except ImportError as e:
        result["evaluation_status"] = f"import_error: {e}"
    except Exception as e:
        # FreeCADの実行中に発生したあらゆる例外をキャッチ
        result["evaluation_status"] = f"fem_error: {type(e).__name__}: {str(e)[:50]}"
    
    finally:
        # 念のためのクリーンアップ
        try:
            import FreeCAD as App
            App.closeAllDocuments()
            gc.collect()
        except:
            pass
        
        result["evaluation_time_s"] = time.time() - t0
        # 常にJSONを出力して終了
        print(json.dumps(result))

# --- ヘルパー関数 (コントローラーから移動) ---
def classify_design(dv):
    """設計変数を基に建物のパターンを分類する"""
    area = dv["Lx"] * dv["Ly"]
    size = "大型" if area >= 300 else "中型" if area >= 100 else "小型" if area >= 50 else "超小型"
    
    avg_slab_m = (dv["tf"] + dv["tr"]) / 2000.0
    col_area_m2 = (dv["bc"] / 1000.0) * (dv["hc"] / 1000.0)
    
    strength = "超重構造" if avg_slab_m > 0.4 or col_area_m2 > 0.6 else \
               "重構造" if avg_slab_m > 0.25 or col_area_m2 > 0.3 else \
               "標準構造" if avg_slab_m > 0.15 or col_area_m2 > 0.1 else \
               "軽構造"
    
    avg_h = (dv["H1"] + dv["H2"]) / 2
    height = "超高天井" if avg_h > 4.5 else "高天井" if avg_h > 3.5 else "標準天井" if avg_h > 2.8 else "低天井"
    
    return f"{size}_{strength}_{height}"

if __name__ == "__main__":
    main()
