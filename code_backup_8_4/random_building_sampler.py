#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Random Building Sampler
=====================

建築パラメータ空間からランダムサンプリングを行い、
FEM解析による構造評価を実施するツール。

主な機能:
- 21個の設計パラメータ（形状15個、材料6個）のランダムサンプリング
- FreeCAD/CalculiXによるFEM構造解析
- 安全性、経済性、環境負荷、快適性、施工性の5指標評価
- 結果のCSVファイル出力とFCStdファイル保存

Usage:
    /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd random_building_sampler.py

Author: AI建築設計システム
Date: 2025-07-24
Version: 1.0
"""

import sys
import os
import shutil  # ディレクトリ削除用に追加

# グローバル変数: すべてのprint文を制御
VERBOSE_OUTPUT = False  # Falseに設定するとprint文が抑制される

# FreeCADのコンソール出力を抑制
if not VERBOSE_OUTPUT:
    try:
        import FreeCAD as App
        App.Console.SetStatus("Console", "Log", False)
        App.Console.SetStatus("Console", "Msg", False)
        App.Console.SetStatus("Console", "Wrn", False)
        App.Console.SetStatus("Console", "Err", False)
    except:
        pass  # FreeCADが利用できない場合は何もしない

# 重複実行を防ぐためのチェック
RUNNING_MARKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".random_building_sampler_running")
if os.path.exists(RUNNING_MARKER):
    print("⚠️ 別のインスタンスが実行中です。終了します。")
    print(f"削除コマンド: rm {RUNNING_MARKER}")
    sys.exit(1)

# 実行マーカーを作成
try:
    with open(RUNNING_MARKER, 'w') as f:
        f.write(str(os.getpid()))
except:
    pass


# ランダムサンプリング設定
N_SAMPLES = 400  # サンプル数（必ず400サンプルを作成）
print(f"📍 処理範囲: サンプル 1 から {N_SAMPLES} まで（計{N_SAMPLES}サンプル）")

# fcstd_outputsディレクトリの作成（既存ファイルは削除）
fcstd_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fcstd_outputs")
if os.path.exists(fcstd_output_dir):
    # 既存のディレクトリを削除
    print(f"🗑️ 既存のfcstd_outputsディレクトリを削除中...")
    shutil.rmtree(fcstd_output_dir)
    print(f"✅ 削除完了")

# 新規作成
os.makedirs(fcstd_output_dir, exist_ok=True)
print(f"📁 fcstd_outputsディレクトリを新規作成しました。")

# CSVファイルをクリア
csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "production_freecad_random_fem_evaluation.csv")
if os.path.exists(csv_path):
    os.remove(csv_path)
    print(f"🗑️ 既存のCSVファイルを削除しました。")

# 現在のスクリプトと同じディレクトリをPythonパスに追加
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# モジュールをリロードして最新の変更を反映
if 'generate_building_fem_analyze' in sys.modules:
    del sys.modules['generate_building_fem_analyze']

import generate_building_fem_analyze as analysis_module
evaluate_building_from_params = analysis_module.evaluate_building_from_params

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simple_random_batch2.py (材料選択もランダム版)
===================================================================
タイムアウト付き FreeCAD FEM ランダムサンプリング・バッチを並列実行。
材料選択（コンクリート/木材）もランダムに決定する。

追加点
------
* 各部材の材料（柱、床、屋根、壁、バルコニー）をランダムに0（コンクリート）または1（木材）で選択
* CSVファイル名を production_freecad_random_fem_evaluation2.csv に変更
* その他の機能は simple_random_batch.py と同じ
"""

import csv
import random
import time
import math
import signal
import sys
import os
import gc
import concurrent.futures # ProcessPoolExecutor のためにインポート

# --------------------------------------------------------------------------------
# パラメータ範囲の定義（ユーザーがカスタマイズしやすいように先頭に配置）
# --------------------------------------------------------------------------------
# 全パラメータの範囲（最小値, 最大値）
PARAM_RANGES = {
    # 建物寸法（安全率向上のため上限を制限）
    "Lx": (8.0, 12.0),          # 建物幅: 8-12m
    "Ly": (8.0, 12.0),          # 建物奥行: 8-12m
    "H1": (2.6, 3.5),           # 1階高: 2.6-3.5m
    "H2": (2.6, 3.2),           # 2階高: 2.6-3.2m
    
    # 構造部材寸法（安全率を高めるため最小値を大幅に増加）
    "tf": (350, 600),           # 床スラブ厚: 350-600mm
    "tr": (350, 600),           # 屋根スラブ厚: 350-600mm
    "bc": (400, 1000),          # 柱幅: 400-1000mm
    "hc": (400, 1000),          # 柱高さ: 400-1000mm
    "tw_ext": (300, 500),       # 外壁厚: 300-500mm
    
    # その他の設計パラメータ（安定的な範囲に調整）
    "wall_tilt_angle": (-30.0, 30.0),  # 壁傾斜角: -30〜30度
    "window_ratio_2f": (0.1, 0.9),     # 2階窓比率: 0.1〜0.9
    "roof_morph": (0.0, 1.0),          # 屋根形態: 0.0〜1.0
    "roof_shift": (-0.5, 0.5),         # 屋根シフト: -0.5〜0.5
    "balcony_depth": (1.0, 3.5),       # バルコニー奥行: 1.0〜3.5m
}

# 材料パラメータの定義（0:コンクリート, 1:木材）
MATERIAL_PARAMS = [
    "material_columns",      # 柱材料
    "material_floor1",       # 1階床材料
    "material_floor2",       # 2階床材料
    "material_roof",         # 屋根材料
    "material_walls",        # 外壁材料
    "material_balcony",      # バルコニー材料
]


# --------------------------------------------------------------------------------
#  FCStd ファイル名生成ヘルパー
# --------------------------------------------------------------------------------
def _next_fcstd_name(base="sample", ext=".FCStd", sample_number=None):
    # fcstd_outputsディレクトリを使用するように修正
    fcstd_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fcstd_outputs")
    if sample_number is not None:
        return os.path.join(fcstd_output_dir, f"{base}{sample_number}{ext}")
    i = 0
    while os.path.exists(os.path.join(fcstd_output_dir, f"{base}{i}{ext}")):
        i += 1
    return os.path.join(fcstd_output_dir, f"{base}{i}{ext}")

# ---------- オフスクリーン backend を指定してから pyplot を import ----------
import matplotlib
matplotlib.use("Agg")  # X サーバ不要で PNG 保存
import matplotlib.pyplot as plt
# 日本語フォントの設定
import matplotlib.font_manager as fm
# macOSの日本語フォントを設定
plt.rcParams['font.family'] = 'Hiragino Sans'
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro', 'Yu Gothic', 'Meirio', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']
plt.rcParams['axes.unicode_minus'] = False  # マイナス記号の文字化け対策
import pandas as pd

print("\n" + "="*80)
print("🚀 本格FreeCADランダムサンプリング開始（材料選択もランダム版）")
print("🎯 目標: 設計空間の自由探索と極限性能の発見（材料の多様性含む）")
print("="*80)

# 固定ベースシード
base_seed = 123456
print(f"🎲 ベースシード: {base_seed}")
rng = random.Random(base_seed)  # 乱数状態を評価関数に汚染されない専用 RNG

# タイムアウト設定（秒）
EVALUATION_TIMEOUT = 10 # 各評価のタイムアウト時間
print(f"⏰ 各評価のタイムアウト: {EVALUATION_TIMEOUT} 秒")

# --- NumPy もあれば同じシードに ---
try:
    import numpy as np
    np.random.seed(base_seed)
except ImportError:
    pass



# --------------------------------------------------------------------------------
#  タイムアウト制御
# --------------------------------------------------------------------------------
class TimeoutError(Exception):
    """SIGALRM で投げる独自例外"""
    pass

def _timeout_handler(signum, frame):
    """SIGALRM のシグナルハンドラ"""
    raise TimeoutError("evaluation timeout")

# SIGALRM が無い Windows では無効化
_HAS_SIGALRM = hasattr(signal, "SIGALRM")
if _HAS_SIGALRM:
    # 親プロセスでシグナルハンドラを設定しても、子プロセスには継承されないか、
    # 適切に動作しない場合があるため、ワーカー関数内で設定する。
    pass

# --------------------------------------------------------------------------------
#  FreeCAD のドキュメント / メモリ掃除
# --------------------------------------------------------------------------------

def _cleanup_freecad_memory():
    """FreeCAD の開いた Doc を片付けて RAM リークを抑える"""
    # この関数は、FreeCAD をインポートした各プロセス（ワーカープロセス）内で呼び出す必要がある
    try:
        import FreeCAD as App # 各プロセスでFreeCADをインポート
        
        # FreeCAD GUIを無効化（メモリ節約）
        if hasattr(App, 'GuiUp') and App.GuiUp:
            try:
                import FreeCADGui
                FreeCADGui.activateWorkbench("NoneWorkbench")
            except:
                pass
        
        # すべてのドキュメントをリストに保存
        docs_to_close = list(App.listDocuments().values())
        
        # 各ドキュメントを閉じる
        for doc in docs_to_close:
            try:
                doc_name = doc.Name
                # オブジェクトを明示的にクリア
                for obj in doc.Objects:
                    try:
                        doc.removeObject(obj.Name)
                    except:
                        pass
                App.closeDocument(doc_name)
                if VERBOSE_OUTPUT:
                    print(f"   ドキュメント '{doc_name}' を閉じました")
            except Exception as e:
                if VERBOSE_OUTPUT:
                    print(f"   ドキュメントクローズエラー: {e}")
        
        # オブジェクトキャッシュのクリア
        if hasattr(App, 'clearDocumentCache'):
            App.clearDocumentCache()
        
        # アクティブドキュメントもクリア
        if hasattr(App, 'ActiveDocument') and App.ActiveDocument:
            try:
                App.closeDocument(App.ActiveDocument.Name)
            except:
                pass
            
    except Exception as e:
        if VERBOSE_OUTPUT:
            print(f"   FreeCADメモリクリーンアップエラー: {e}")
    
    # .FCBakファイルの削除
    try:
        import glob
        fcstd_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fcstd_outputs")
        fcbak_files = glob.glob(os.path.join(fcstd_output_dir, "*.FCBak"))
        if fcbak_files and VERBOSE_OUTPUT:
            print(f"   🗑️ {len(fcbak_files)}個の.FCBakファイルを削除中...")
        for fcbak in fcbak_files:
            try:
                os.remove(fcbak)
            except:
                pass
    except Exception as e:
        if VERBOSE_OUTPUT:
            print(f"   .FCBakファイル削除エラー: {e}")
    
    # 強制的なガベージコレクション
    gc.collect()
    
    # もう一度念のため
    gc.collect(2)

# --------------------------------------------------------------------------------
# ワーカー関数（1件だけ評価、タイムアウト付き）
# ProcessPoolExecutorで実行されるため、ここに必要なインポートや設定を行う
# --------------------------------------------------------------------------------

def _worker_evaluate_design(design_vars: dict, timeout_s: int, idx: int = None):
    """
    evaluate_building_from_params をラップし、タイムアウトをかける。
    ProcessPoolExecutor のワーカーとして機能する。
    FreeCAD モジュールはこの関数が実行される子プロセス内でインポートされる。
    """
    # 子プロセス内で FreeCAD 関連モジュールをインポート
    # これにより、各プロセスが独立した FreeCAD 環境を持つ
    try:
        # 現在のディレクトリをシステムパスに追加
        import sys
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # モジュールをリロードして最新の変更を反映
        if 'generate_building_fem_analyze' in sys.modules:
            del sys.modules['generate_building_fem_analyze']
        
        from generate_building_fem_analyze import evaluate_building_from_params
        # FreeCAD が自動的にインポートされる
    except ImportError as e:
        return {
            **design_vars,
            "cost_per_sqm": float("nan"),
            "co2_per_sqm": float("nan"),
            "comfort_score": float("nan"),
            "constructability_score": float("nan"),
            "safety_factor": float("nan"),
            "total_cost": float("nan"),
            "floor_area": float("nan"),
            "design_pattern": _classify(design_vars),
            "evaluation_status": f"import_error:{str(e)[:30]}",
            "evaluation_time_s": float("nan"),
        }

    # 各ワーカープロセス内でシグナルハンドラを設定する
    if _HAS_SIGALRM:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout_s)
    
    status = "error"
    res = None
    # サンプル番号を使用
    actual_sample_number = idx if idx is not None else None
    save_path = _next_fcstd_name(sample_number=actual_sample_number)
    t0 = time.time()
    
    # 詳細ログ出力（サンプル番号付き）
    sample_id = f"[サンプル{actual_sample_number}]" if actual_sample_number is not None else "[サンプル]"
    print(f"\n{sample_id} 🔍 FEM解析開始 - 詳細ログモード")
    print(f"{sample_id} 📝 パラメータ: Lx={design_vars['Lx']}, Ly={design_vars['Ly']}, H1={design_vars['H1']}, H2={design_vars['H2']}")
    
    # 材料情報を表示
    materials = []
    for mat_param in MATERIAL_PARAMS:
        mat_type = "木材" if design_vars.get(mat_param, 0) == 1 else "コンクリート"
        materials.append(f"{mat_param}={mat_type}")
    print(f"{sample_id} 🏗️ 材料: {', '.join(materials)}")
    
    # evaluate_building_from_paramsに詳細ログフラグを渡す準備
    import os
    os.environ['FEM_DETAILED_LOG'] = '1'
    os.environ['FEM_SAMPLE_ID'] = sample_id
    
    try:
        # evaluate_building_from_params は save_fcstd=True で呼ぶ
        print(f"{sample_id} ⏱️ evaluate_building_from_params 開始: {time.strftime('%H:%M:%S')}")
        res = evaluate_building_from_params(design_vars, save_fcstd=True, fcstd_path=save_path)
        status = "success"
        print(f"{sample_id} ✅ evaluate_building_from_params 完了: {time.strftime('%H:%M:%S')}")
    except TimeoutError:
        status = "timeout"
    except Exception as e:
        status = f"error:{str(e)[:30]}"
    finally:
        if _HAS_SIGALRM:
            signal.alarm(0)  # シグナルをキャンセル
        # 各ワーカープロセスでFreeCADのメモリをクリーンアップ
        _cleanup_freecad_memory()
        # 詳細ログフラグをクリア
        os.environ.pop('FEM_DETAILED_LOG', None)
        os.environ.pop('FEM_SAMPLE_ID', None)
    
    elapsed = time.time() - t0
    
    # CSV書き込み用に整形
    if status == "success" and res is not None:
        f1 = res["economic"]["cost_per_sqm"]
        f2 = res["environmental"]["co2_per_sqm"]
        f3 = res["comfort"]["comfort_score"]
        f4 = res["constructability"]["constructability_score"]
        f5 = res["safety"]["overall_safety_factor"]
        tc = res["economic"]["total_cost"]
        area = res["comfort"]["floor_area"]
    else:
        f1 = f2 = f3 = f4 = f5 = tc = area = float("nan")

    return {
        **design_vars, # 設計変数をそのまま展開
        "cost_per_sqm": f1,
        "co2_per_sqm": f2,
        "comfort_score": f3,
        "constructability_score": f4,
        "safety_factor": f5,
        "total_cost": tc,
        "floor_area": area,
        "design_pattern": _classify(design_vars), # パターン分類もここで実行
        "evaluation_status": status,
        "evaluation_time_s": elapsed,
        "fcstd_path": save_path if status == "success" else "",
    }

# --------------------------------------------------------------------------------
# ランダム設計の生成 / パターン分類 (材料もランダム化)
# --------------------------------------------------------------------------------

def _generate_random_design_vector():
    """各設計変数を指定範囲からランダムに選択（材料もランダム）"""
    
    # 各パラメータを範囲内からランダムに生成
    dv = {
        # 実数値パラメータ
        "Lx": round(rng.uniform(*PARAM_RANGES["Lx"]), 2),
        "Ly": round(rng.uniform(*PARAM_RANGES["Ly"]), 2),
        "H1": round(rng.uniform(*PARAM_RANGES["H1"]), 2),
        "H2": round(rng.uniform(*PARAM_RANGES["H2"]), 2),
        
        # 整数値パラメータ
        "tf": rng.randint(*PARAM_RANGES["tf"]),
        "tr": rng.randint(*PARAM_RANGES["tr"]),
        "bc": rng.randint(*PARAM_RANGES["bc"]),
        "hc": rng.randint(*PARAM_RANGES["hc"]),
        "tw_ext": rng.randint(*PARAM_RANGES["tw_ext"]),
        
        # その他のパラメータ
        "wall_tilt_angle": round(rng.uniform(*PARAM_RANGES["wall_tilt_angle"]), 1),
        "window_ratio_2f": round(rng.uniform(*PARAM_RANGES["window_ratio_2f"]), 2),
        "roof_morph": round(rng.uniform(*PARAM_RANGES["roof_morph"]), 2),
        "roof_shift": round(rng.uniform(*PARAM_RANGES["roof_shift"]), 2),
        "balcony_depth": round(rng.uniform(*PARAM_RANGES["balcony_depth"]), 1),
    }
    
    # 材料パラメータをランダムに追加（0:コンクリート, 1:木材）
    # 各パーツごとに完全ランダムに選択
    for mat_param in MATERIAL_PARAMS:
        # 各部材を50%の確率でコンクリート(0)または木材(1)に
        dv[mat_param] = rng.choice([0, 1])
    
    return dv



def _classify(dv):
    """設計変数を基に建物のパターンを分類する（材料も考慮）"""
    area = dv["Lx"] * dv["Ly"]
    if area < 50:
        size = "超小型"
    elif area < 100:
        size = "小型"
    elif area < 300:
        size = "中型"
    else:
        size = "大型"
    
    # スラブ厚と柱断面積の積から強度カテゴリを分類
    # 単位を合わせて乗算
    avg_slab_m = (dv["tf"] + dv["tr"]) / 2000.0 # mm -> m
    col_area_m2 = (dv["bc"] / 1000.0) * (dv["hc"] / 1000.0) # mm*mm -> m^2
    
    # 分類閾値をより現実的な値に調整
    if avg_slab_m > 0.4 or col_area_m2 > 0.6: # 0.6m^2 = 60cmx100cm
        strength = "超重構造"
    elif avg_slab_m > 0.25 or col_area_m2 > 0.3: # 0.3m^2 = 50cmx60cm
        strength = "重構造"
    elif avg_slab_m > 0.15 or col_area_m2 > 0.1: # 0.1m^2 = 30cmx30cm
        strength = "標準構造"
    else:
        strength = "軽構造"
    
    avg_h = (dv["H1"] + dv["H2"]) / 2
    height = (
        "超高天井" if avg_h > 4.5 else
        "高天井" if avg_h > 3.5 else
        "標準天井" if avg_h > 2.8 else
        "低天井"
    )
    
    # 材料の傾向を追加（0:RC, 1:木材のみ）
    material_sum = 0
    for mat_param in MATERIAL_PARAMS:
        mat_val = dv.get(mat_param, 0)
        if mat_val > 0:  # 木材の場合
            material_sum += 1
    
    if material_sum >= 4:
        material_type = "_木造中心"
    elif material_sum >= 2:
        material_type = "_混合構造"
    else:
        material_type = "_RC中心"
    
    return f"{size}_{strength}_{height}{material_type}"

# --------------------------------------------------------------------------------
# メインループ
# --------------------------------------------------------------------------------
CSV_PATH = "production_freecad_random_fem_evaluation.csv"
# 常に新規作成モード
open_mode = "w"


# FreeCADコマンドライン実行時は並列処理を無効化
if "FreeCAD" in sys.modules or "freecadcmd" in sys.argv[0].lower():
    NUM_PROCESSES = 1  # FreeCAD環境ではシングルプロセス
    print("🔧 FreeCAD環境検出: シングルプロセスモードで実行")
else:
    NUM_PROCESSES = os.cpu_count() or 2 # CPUコア数を利用、最低2プロセス
    
    NUM_PROCESSES = 1
    print(f"🚀 標準環境: {NUM_PROCESSES}プロセスで並列実行")

header = [
    "Lx", "Ly", "H1", "H2", "tf", "tr", "bc", "hc", "tw_ext",
    "wall_tilt_angle", "window_ratio_2f", "roof_morph", "roof_shift", "balcony_depth",
    "material_columns", "material_floor1", "material_floor2", "material_roof", "material_walls", "material_balcony",
    "cost_per_sqm", "co2_per_sqm", "comfort_score", "constructability_score",
    "safety_factor", "total_cost", "floor_area", "design_pattern", "evaluation_status",
    "evaluation_time_s", "fcstd_path",
]

# シングルプロセスモードでは事前生成しない（必要に応じて動的生成）
if NUM_PROCESSES > 1:
    # マルチプロセスの場合は事前にN_SAMPLES個生成
    print(f"⚙️ {N_SAMPLES}個の設計パラメータを生成中...")
    all_design_vars = []
    for _ in range(N_SAMPLES):
        all_design_vars.append(_generate_random_design_vector())
    print("✅ 設計パラメータ生成完了。")

print(f"🚀 処理開始（プロセス数: {NUM_PROCESSES}）")

n_ok = n_fail = n_timeout = 0
t0_all = time.time()

if NUM_PROCESSES == 1:
    # シングルプロセス実行（FreeCAD環境用）
    print("🔧 シングルプロセスモードで実行中...")
    
    # 直接モジュールをインポート（シングルプロセスでは安全）
    try:
        # モジュールをリロードして最新の変更を反映
        if 'generate_building_fem_analyze' in sys.modules:
            del sys.modules['generate_building_fem_analyze']
        
        from generate_building_fem_analyze import evaluate_building_from_params
        print("✅ generate_building_fem_analyze インポート成功（最新版をロード）")
    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {e}")
        sys.exit(1)
    
    # CSV開始
    output_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(output_dir, CSV_PATH)
    with open(csv_path, open_mode, newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        
        # 1からN_SAMPLESまでの各サンプルを確実に作成
        created_samples = 0
        for sample_num in range(1, N_SAMPLES + 1):
            
            # このサンプル番号が成功するまで無限に繰り返す
            attempt_count = 0
            success = False
            
            while not success:  # 成功するまで無限ループ
                attempt_count += 1
                dv = _generate_random_design_vector()  # 新しいパラメータを生成
                
                print(f"\n{'='*60}")
                print(f"🔄 サンプル {sample_num}/{N_SAMPLES} | 試行 {attempt_count}")
                print(f"   全体進捗: {(created_samples/N_SAMPLES*100):.1f}% 完了 ({created_samples}/{N_SAMPLES})")
                print(f"   パラメータ: Lx={dv['Lx']}, Ly={dv['Ly']}, H1={dv['H1']}, H2={dv['H2']}")
                print(f"   構造: tf={dv['tf']}mm, tr={dv['tr']}mm, bc={dv['bc']}mm, hc={dv['hc']}mm")
                
                # 材料情報を表示
                materials = []
                for mat_param in MATERIAL_PARAMS:
                    mat_type = "木材" if dv.get(mat_param, 0) == 1 else "コンクリート"
                    materials.append(f"{mat_param}={mat_type}")
                print(f"   材料: {', '.join(materials[:3])}")
                print(f"        {', '.join(materials[3:])}")
                print(f"{'='*60}")
                
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
                        
                        # 結果の取得
                        f1 = res["economic"]["cost_per_sqm"]
                        f2 = res["environmental"]["co2_per_sqm"]
                        f3 = res["comfort"]["comfort_score"]
                        f4 = res["constructability"]["constructability_score"]
                        f5 = res["safety"]["overall_safety_factor"]
                        tc = res["economic"]["total_cost"]
                        area = res["comfort"]["floor_area"]
                        
                        print(f"✅ 評価成功！サンプル{sample_num}を保存")
                        print(f"   コスト: {f1:,.0f} 円/m²")
                        print(f"   CO2: {f2:.1f} kg-CO2/m²")
                        print(f"   快適性: {f3:.1f}")
                        print(f"   施工性: {f4:.1f}")
                        print(f"   安全率: {f5:.2f}")
                        
                        # 成功したのでループを抜ける
                        elapsed = time.time() - t0
                        created_samples += 1
                        n_ok += 1
                        success = True
                        break
                    else:
                        # 失敗時は再試行（新しいランダムパラメータで）
                        status = f"error:{res.get('message', 'unknown')[:30]}"
                        n_fail += 1
                        print(f"❌ 評価失敗: {res.get('message', 'unknown')} → 再試行します（試行{attempt_count+1}回目）")
                        continue
                        
                except TimeoutError:
                    status = "timeout"
                    n_timeout += 1
                    print(f"⏱️ タイムアウト → 再試行します（試行{attempt_count+1}回目）")
                    continue
                except Exception as e:
                    status = f"error:{str(e)[:30]}"
                    n_fail += 1
                    print(f"❌ エラー: {e} → 再試行します（試行{attempt_count+1}回目）")
                    continue
                finally:
                    if _HAS_SIGALRM:
                        signal.alarm(0)
                    _cleanup_freecad_memory()
                    os.environ.pop('FEM_DETAILED_LOG', None)
                    os.environ.pop('FEM_SAMPLE_ID', None)
            
            # CSV行を作成して書き込み（必ず成功してここに到達）
            if success and status == "success":
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
                        # 相対パスに変換
                        rel_path = os.path.relpath(fcstd_path, output_dir)
                        row.append(rel_path)
                    else:
                        row.append("")
                
                writer.writerow(row)
                f.flush()  # リアルタイムで保存
                
                print(f"⏱️  処理時間: {elapsed:.2f} 秒")
                print(f"📊 進捗: {created_samples}/{N_SAMPLES} サンプル完了 ({(created_samples/N_SAMPLES*100):.1f}%)")

else:
    # マルチプロセス実行（通常環境用）
    # （simple_random_batch.pyと同じマルチプロセス処理を実装可能）
    print("⚠️ マルチプロセスモードは現在無効化されています")

# --------------------------------------------------------------------------------
# 終了処理
# --------------------------------------------------------------------------------
elapsed_all = time.time() - t0_all
print("\n" + "="*80)
print(f"🏁 バッチ処理完了")
print(f"✅ 成功: {n_ok} 件")
print(f"❌ 失敗（再試行含む）: {n_fail} 件")
print(f"⏱️ タイムアウト（再試行含む）: {n_timeout} 件")
print(f"🕒 合計時間: {elapsed_all:.1f} 秒 ({elapsed_all/60:.1f} 分)")
if n_ok > 0:
    print(f"⚡ 平均時間: {elapsed_all/n_ok:.1f} 秒/成功サンプル")

print(f"\n📊 最終結果:")
print(f"   作成完了: {created_samples}/{N_SAMPLES} サンプル")
print(f"   🎉 全{N_SAMPLES}サンプルの作成が完了しました！")
print("="*80)

# 実行マーカーを削除
try:
    if os.path.exists(RUNNING_MARKER):
        os.remove(RUNNING_MARKER)
except:
    pass

# --------------------------------------------------------------------------------
# matplotlib でグラフを描く
# --------------------------------------------------------------------------------
# CSV読み込み
print("\n📊 散布図グラフを生成中...")
output_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(output_dir, CSV_PATH)
try:
    df = pd.read_csv(csv_path, encoding='utf-8-sig')
    # 成功したものだけフィルタ
    df_success = df[df['evaluation_status'] == 'success'].copy()
    
    if len(df_success) == 0:
        print("⚠️ 成功したサンプルがないため、グラフ生成をスキップします。")
    else:
        # 散布図を作成
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # カスタムカラーマップを作成（7段階：青灰色→赤）
        from matplotlib.colors import ListedColormap

        colors = [
            (170/255, 170/255, 170/255), # 6: 灰色
            (210/255, 190/255, 130/255), # 5: ベージュ
            (240/255, 180/255, 70/255),  # 4: 黄橙
            (220/255, 130/255, 60/255),  # 3: 橙
            (180/255, 80/255, 40/255),   # 2: オレンジ茶
            (130/255, 40/255, 20/255),   # 1: 赤茶
            (90/255, 20/255, 20/255)     # 0: 濃い赤茶
        ]

        cm = ListedColormap(colors, name='gray_to_red')


        # 材料の混合度を計算（木材の数）
        material_sum = (df_success['material_columns'] + df_success['material_floor1'] + 
                       df_success['material_floor2'] + df_success['material_roof'] + 
                       df_success['material_walls'] + df_success['material_balcony'])
        
        # 1. 安全率 vs 建設コスト
        ax1 = axes[0, 0]
        scatter1 = ax1.scatter(df_success['safety_factor'], df_success['cost_per_sqm'], 
                              c=material_sum, cmap=cm, alpha=0.6)
        ax1.set_xlabel('安全率')
        ax1.set_ylabel('建設コスト (円/m²)')
        ax1.set_title('建設コスト (円/m²) vs 安全率')
        ax1.grid(True, alpha=0.3)
        ax1.axvline(x=2.0, color='red', linestyle='--', label='推奨安全率')
        # カラーバーを追加（木材使用数を示す）
        cbar1 = plt.colorbar(scatter1, ax=ax1)
        cbar1.set_label('木材使用数 (0-6)')
        ax1.legend()
        
        # 2. 安全率 vs CO2排出量
        ax2 = axes[0, 1]
        scatter2 = ax2.scatter(df_success['safety_factor'], df_success['co2_per_sqm'],
                              c=material_sum, cmap=cm, alpha=0.6)
        ax2.set_xlabel('安全率')
        ax2.set_ylabel('CO2排出量 (kg-CO2/m²)')
        ax2.set_title('CO2排出量 (kg-CO2/m²) vs 安全率')
        ax2.grid(True, alpha=0.3)
        ax2.axvline(x=2.0, color='red', linestyle='--', label='推奨安全率')
        # カラーバーを追加（木材使用数を示す）
        cbar2 = plt.colorbar(scatter2, ax=ax2)
        cbar2.set_label('木材使用数 (0-6)')
        ax2.legend()
        
        # 3. 安全率 vs 快適性スコア
        ax3 = axes[1, 0]
        scatter3 = ax3.scatter(df_success['safety_factor'], df_success['comfort_score'],
                              c=material_sum, cmap=cm, alpha=0.6)
        ax3.set_xlabel('安全率')
        ax3.set_ylabel('快適性スコア')
        ax3.set_title('快適性スコア vs 安全率')
        ax3.grid(True, alpha=0.3)
        ax3.axvline(x=2.0, color='red', linestyle='--', label='推奨安全率')
        ax3.set_ylim(0, 10)
        # カラーバーを追加（材料の混合度を示す）
        cbar3 = plt.colorbar(scatter3, ax=ax3)
        cbar3.set_label('木材使用数 (0-6)')
        ax3.legend()
        
        # 4. 安全率 vs 施工性スコア
        ax4 = axes[1, 1]
        scatter4 = ax4.scatter(df_success['safety_factor'], df_success['constructability_score'],
                              c=material_sum, cmap=cm, alpha=0.6)
        ax4.set_xlabel('安全率')
        ax4.set_ylabel('施工性スコア')
        ax4.set_title('施工性スコア vs 安全率')
        ax4.grid(True, alpha=0.3)
        ax4.axvline(x=2.0, color='red', linestyle='--', label='推奨安全率')
        ax4.set_ylim(0, 10)
        # カラーバーを追加（材料の混合度を示す）
        cbar4 = plt.colorbar(scatter4, ax=ax4)
        cbar4.set_label('木材使用数 (0-6)')
        ax4.legend()
        
        plt.tight_layout()
        
        # グラフを保存
        graph_path = os.path.join(output_dir, 'safety_analysis_with_materials2.png')
        plt.savefig(graph_path, dpi=150, bbox_inches='tight')
        print(f"✅ 散布図を保存しました: {graph_path}")
        
        # 材料組み合わせの統計を表示
        print("\n📊 材料組み合わせの統計:")
        print(f"   全コンクリート構造: {len(df_success[material_sum == 0])} 件")
        print(f"   混合構造 (1-5材料): {len(df_success[(material_sum >= 1) & (material_sum <= 5)])} 件")
        print(f"   全木造構造: {len(df_success[material_sum == 6])} 件")
        
        # コストとCO2の相関を材料別に分析
        if len(df_success) > 3:
            correlation = df_success['cost_per_sqm'].corr(df_success['co2_per_sqm'])
            print(f"\n📈 コストとCO2の相関係数: {correlation:.3f}")
            
            # 安全率とコストの相関を計算（重要！）
            safety_cost_corr = df_success['safety_factor'].corr(df_success['cost_per_sqm'])
            print(f"📊 安全率とコストの相関係数: {safety_cost_corr:.3f}")
            
            # 相関が低い場合は警告
            if safety_cost_corr < 0.5:
                print(f"⚠️  警告: 安全率とコストの相関が低い ({safety_cost_corr:.3f} < 0.5)")
                print("   → generate_building_fem_analyze.pyのコスト計算を見直す必要があります")
                
                # 安全率レベル別の平均コストを確認
                print("\n📊 安全率レベル別の平均コスト:")
                df_success['safety_level'] = pd.cut(df_success['safety_factor'], 
                                                   bins=[0, 1, 1.5, 2, 2.5, 3, 10],
                                                   labels=['危険', '最低限', '標準', '良好', '優秀', '過剰'])
                for level in ['危険', '最低限', '標準', '良好', '優秀', '過剰']:
                    level_df = df_success[df_success['safety_level'] == level]
                    if len(level_df) > 0:
                        avg_cost = level_df['cost_per_sqm'].mean()
                        avg_safety = level_df['safety_factor'].mean()
                        print(f"   {level}: {avg_cost:,.0f} 円/m² (平均安全率: {avg_safety:.2f}, n={len(level_df)})")
            else:
                print(f"✅ 安全率とコストの相関が適切です ({safety_cost_corr:.3f} ≥ 0.5)")
            
except Exception as e:
    print(f"❌ グラフ生成エラー: {e}")

print("\n✨ ランダムサンプリングが完了しました！")
print(f"📊 生成されたサンプル数: {len(completed_samples)}")
print(f"📁 出力ファイル:")
print(f"   - CSVファイル: {csv_path}")
print(f"   - FCStdファイル: {fcstd_output_dir}")
print(f"   - グラフファイル: {output_dir}")

# 実行マーカーを削除
try:
    if os.path.exists(RUNNING_MARKER):
        os.remove(RUNNING_MARKER)
except:
    pass
