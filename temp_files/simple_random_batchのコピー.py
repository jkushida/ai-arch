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
RUNNING_MARKER = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".simple_random_batch_running")
if os.path.exists(RUNNING_MARKER):
    print("⚠️ 別のインスタンスが実行中です。終了します。")
    sys.exit(1)

# 実行マーカーを作成
try:
    with open(RUNNING_MARKER, 'w') as f:
        f.write(str(os.getpid()))
except:
    pass


N_SAMPLES = 300  # サンプル数
print(f"📍 処理範囲: サンプル 1 から {N_SAMPLES} まで（計{N_SAMPLES}サンプル）")

# fcstd_outputsディレクトリの作成とクリア
fcstd_output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fcstd_outputs")
# ディレクトリが存在する場合は中身をクリア
if os.path.exists(fcstd_output_dir):
    print(f"🗑️ fcstd_outputsディレクトリの中身をクリア中...")
    shutil.rmtree(fcstd_output_dir)
os.makedirs(fcstd_output_dir, exist_ok=True)
print(f"📁 fcstd_outputsディレクトリを準備しました。")

# CSVファイルをクリア
csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "production_freecad_random_fem_evaluation.csv")
if os.path.exists(csv_path):
    os.remove(csv_path)
    print(f"🗑️ 既存のCSVファイルを削除しました。")

# 現在のスクリプトと同じディレクトリをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import generate_building_fem_analyze as analysis_module
evaluate_building_from_params = analysis_module.evaluate_building_from_params

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
production_freecad_random_batch_parallel.py (グラフ + CSV, 並列化版)
===================================================================
タイムアウト付き FreeCAD FEM ランダムサンプリング・バッチを並列実行。

追加点
------
* `concurrent.futures.ProcessPoolExecutor` を使用して、FreeCAD FEM 解析を並列化。
* 各解析にタイムアウトを設定し、ハングアップを防止。
* CSV はこれまで通りリアルタイムで追記。
* 解析が *全て* 終わったあとに `matplotlib(Agg)` で散布図 (PNG) を自動保存。
* pandas で CSV を再読込してプロットするため、FreeCAD 側の GUI とは独立して実行可能。

注意点:
* FreeCADはマルチプロセス環境での安定性に課題がある場合があります。
  問題が発生する場合は、逐次処理に戻すか、ワーカー数を減らしてください。
* 各プロセスでFreeCADが初期化されるため、全体のメモリ使用量が増加する可能性があります。
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
    # 建物寸法
    "Lx": (8.0, 15.0),          # 建物幅: 8-15m
    "Ly": (8.0, 15.0),          # 建物奥行: 8-15m
    "H1": (2.6, 4.2),           # 1階高: 2.6-4.2m
    "H2": (2.6, 3.8),           # 2階高: 2.6-3.8m
    
    # 構造部材寸法
    "tf": (180, 450),           # 床スラブ厚: 180-450mm
    "tr": (150, 350),           # 屋根スラブ厚: 150-350mm
    "bc": (300, 850),           # 柱幅: 300-850mm
    "hc": (300, 750),           # 柱高さ: 300-750mm
    "tw_ext": (150, 320),       # 外壁厚: 150-320mm
    
    # その他の設計パラメータ
    "wall_tilt_angle": (-30.0, 30.0),  # 壁傾斜角: -30〜30度
    "window_ratio_2f": (0.1, 0.7),     # 2階窓比率: 0.1〜0.7
    "roof_morph": (0.0, 0.7),          # 屋根形態: 0.0〜0.7
    "roof_shift": (-0.4, 0.4),         # 屋根シフト: -0.4〜0.4
    "balcony_depth": (1.0, 3.5),       # バルコニー深さ: 1.0〜3.5m
}

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
print("🚀 本格FreeCADランダムサンプリング開始")
print("🎯 目標: 設計空間の自由探索と極限性能の発見（安定実行 & 高速化）")
print("="*80)

# 固定ベースシード
base_seed = 123
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
# ランダム設計の生成 / パターン分類 (変更なし) - これはメインプロセスで実行
# --------------------------------------------------------------------------------

def _generate_random_design_vector():
    """各設計変数を指定範囲からランダムに選択"""
    
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
    
    return dv



def _classify(dv):
    """設計変数を基に建物のパターンを分類する"""
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
    return f"{size}_{strength}_{height}"

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
        from generate_building_fem_analyze import evaluate_building_from_params
        print("✅ generate_building_fem_analyze インポート成功")  # ← 修正
    except ImportError as e:
        print(f"❌ モジュールインポートエラー: {e}")
        sys.exit(1)

    # FCStdファイル保存用ディレクトリ（重複定義を避けるためここで定義）
    output_dir = "fcstd_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    with open(CSV_PATH, open_mode, newline="", encoding="utf-8-sig") as f_csv:
        writer = csv.DictWriter(f_csv, fieldnames=header)
        if open_mode == "w":
            writer.writeheader()
        
        # 成功サンプル数がN_SAMPLESに達するまでループ
        total_attempts = 0
        while n_ok < N_SAMPLES:
            total_attempts += 1
            dv = _generate_random_design_vector()  # 新しいパラメータを生成
            
            print(f"\n{'='*60}")
            print(f"🔄 成功サンプル {n_ok}/{N_SAMPLES} | 総試行数 {total_attempts}")
            print(f"   進捗: {(n_ok/N_SAMPLES*100):.1f}% 完了")
            print(f"   パラメータ: Lx={dv['Lx']}, Ly={dv['Ly']}, H1={dv['H1']}, H2={dv['H2']}")
            print(f"   構造: tf={dv['tf']}mm, tr={dv['tr']}mm, bc={dv['bc']}mm, hc={dv['hc']}mm")
            print(f"{'='*60}")
            
            t0 = time.time()
            fcstd_path = os.path.join(output_dir, f"sample{n_ok + 1}.FCStd")
            
            # 詳細ログ出力の設定
            sample_id = f"[サンプル{n_ok + 1}]"
            print(f"\n{sample_id} 🔍 FEM解析開始 - 詳細ログモード")
            print(f"{sample_id} 📝 パラメータ: Lx={dv['Lx']}, Ly={dv['Ly']}, H1={dv['H1']}, H2={dv['H2']}")
            
            os.environ['FEM_DETAILED_LOG'] = '1'
            os.environ['FEM_SAMPLE_ID'] = sample_id
            
            # signal.alarmを使用したタイムアウト制御
            if _HAS_SIGALRM:
                signal.signal(signal.SIGALRM, _timeout_handler)
                signal.alarm(60)  # 60秒のタイムアウト（デバッグ用）
            
            try:
                # 評価を実行
                print(f"{sample_id} ⏱️ evaluate_building_from_params 開始: {time.strftime('%H:%M:%S')}")
                res = evaluate_building_from_params(dv, save_fcstd=True, fcstd_path=fcstd_path)
                print(f"{sample_id} ✅ evaluate_building_from_params 完了: {time.strftime('%H:%M:%S')}")
                status = "success"
                
                # 評価直後にFreeCADドキュメントをクリーンアップ
                _cleanup_freecad_memory()
                
                # 対応する.FCBakファイルを削除
                fcbak_path = fcstd_path.replace('.FCStd', '.FCBak')
                if os.path.exists(fcbak_path):
                    try:
                        os.remove(fcbak_path)
                    except:
                        pass
                
                # 毎回ガベージコレクションを実行
                gc.collect()
                
                # 2サンプルごとに徹底的なガベージコレクション
                if n_ok % 2 == 0:
                    gc.collect(2)
                
                f1 = res["economic"]["cost_per_sqm"]
                f2 = res["environmental"]["co2_per_sqm"]
                f3 = res["comfort"]["comfort_score"]
                f4 = res["constructability"]["constructability_score"]
                f5 = res["safety"]["overall_safety_factor"]
                tc = res["economic"]["total_cost"]
                area = res["comfort"]["floor_area"]
                
            except TimeoutError:
                print(f"\n⚠️  試行 {total_attempts} がタイムアウトしました（60秒）")
                print(f"   問題のパラメータ: {dv}")
                status = "timeout"
                f1 = f2 = f3 = f4 = f5 = tc = area = float("nan")
                fcstd_path = ""
                # 強制的にメモリクリーンアップ
                _cleanup_freecad_memory()
                
            except Exception as e:
                print(f"\n❌ 試行 {total_attempts} でエラー: {str(e)[:50]}")
                status = f"error:{str(e)[:30]}"
                f1 = f2 = f3 = f4 = f5 = tc = area = float("nan")
                fcstd_path = ""
                _cleanup_freecad_memory()
            
            finally:
                # タイムアウトをキャンセル
                if _HAS_SIGALRM:
                    signal.alarm(0)
                # 詳細ログフラグをクリア
                os.environ.pop('FEM_DETAILED_LOG', None)
                os.environ.pop('FEM_SAMPLE_ID', None)
            
            elapsed = time.time() - t0
            
            row = {
                **dv,
                "cost_per_sqm": f1,
                "co2_per_sqm": f2,
                "comfort_score": f3,
                "constructability_score": f4,
                "safety_factor": f5,
                "total_cost": tc,
                "floor_area": area,
                "design_pattern": _classify(dv),
                "evaluation_status": status,
                "evaluation_time_s": elapsed,
                "fcstd_path": fcstd_path,
            }
            
            writer.writerow(row)
            f_csv.flush()
            
            print(f"📝 試行 {total_attempts} 完了。 ⏱️ {elapsed:.1f}s   status = {status}")
            
            if status == "success":
                n_ok += 1
            elif status == "timeout":
                n_timeout += 1
            else:
                n_fail += 1
            
            # 定期的なメモリクリーンアップ（2成功サンプルごと）
            if n_ok % 2 == 0 and n_ok > 0:
                print(f"\n🧹 メモリクリーンアップ開始（{n_ok}成功サンプル完了）")
                _cleanup_freecad_memory()
                gc.collect(2)  # より徹底的なガベージコレクション
                print(f"✅ メモリクリーンアップ完了")
                
                # メモリ使用量を確認
                try:
                    import psutil
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    if memory_mb > 1500:  # 1.5GB以上使用している場合
                        print(f"⚠️  メモリ使用量が高い: {memory_mb:.1f} MB")
                        # 追加のクリーンアップ
                        _cleanup_freecad_memory()
                        gc.collect(2)
                        # さらに徹底的なクリーンアップ
                        for _ in range(3):
                            gc.collect(2)
                except ImportError:
                    pass
            
            # 10成功サンプルごとに詳細な状態表示
            if n_ok % 10 == 0 and n_ok > 0:
                try:
                    import psutil
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    print(f"\n{'='*60}")
                    print(f"📊 進捗状況レポート（成功サンプル {n_ok}）")
                    print(f"  成功進捗: {(n_ok/N_SAMPLES*100):.1f}% ({n_ok}/{N_SAMPLES})")
                    print(f"  総試行数: {total_attempts}回")
                    print(f"  成功: {n_ok}件, タイムアウト: {n_timeout}件, エラー: {n_fail}件")
                    print(f"  成功率: {(n_ok/total_attempts*100):.1f}%")
                    print(f"  メモリ使用量: {memory_mb:.1f} MB")
                    print(f"  経過時間: {(time.time() - t0_all):.1f}秒")
                    print(f"  平均処理時間: {((time.time() - t0_all)/total_attempts):.1f}秒/試行")
                    print(f"{'='*60}\n")
                except ImportError:
                    print(f"\n{'='*60}")
                    print(f"📊 進捗状況レポート（成功サンプル {n_ok}）")
                    print(f"  成功進捗: {(n_ok/N_SAMPLES*100):.1f}% ({n_ok}/{N_SAMPLES})")
                    print(f"  総試行数: {total_attempts}回")
                    print(f"  成功: {n_ok}件, タイムアウト: {n_timeout}件, エラー: {n_fail}件")
                    print(f"  成功率: {(n_ok/total_attempts*100):.1f}%")
                    print(f"  経過時間: {(time.time() - t0_all):.1f}秒")
                    print(f"  平均処理時間: {((time.time() - t0_all)/total_attempts):.1f}秒/試行")
                    print(f"{'='*60}\n")

else:
    # マルチプロセス実行（標準Python環境用）
    with concurrent.futures.ProcessPoolExecutor(max_workers=NUM_PROCESSES) as executor, \
         open(CSV_PATH, open_mode, newline="", encoding="utf-8-sig") as f_csv:

        writer = csv.DictWriter(f_csv, fieldnames=header)
        if open_mode == "w":
            writer.writeheader()

        # submitでタスクを投入し、as_completedで完了したものから結果を取得
        futures = {
            executor.submit(_worker_evaluate_design, dv, EVALUATION_TIMEOUT, idx): idx
            for idx, dv in enumerate(all_design_vars, start=1)
        }

        for future in concurrent.futures.as_completed(futures):
            idx = futures[future] # タスクに対応する元のインデックスを取得
            try:
                row = future.result() # ワーカーからの結果辞書を取得
                writer.writerow(row)
                f_csv.flush() # 即書き出し
                
                status = row["evaluation_status"]
                elapsed = row["evaluation_time_s"]
                
                print(f"📝 サンプル {idx}/{N_SAMPLES} 完了。 ⏱️ {elapsed:.1f}s   status = {status}")
                
                if status == "success":
                    n_ok += 1
                elif status == "timeout":
                    n_timeout += 1
                else:
                    n_fail += 1

            except Exception as e:
                print(f"❌ サンプル {idx} の処理中に予期せぬプロセスエラー: {e}")
                # プロセス自体でエラーが発生した場合も、設計変数とエラー状態を記録する
                # 元の設計変数 (all_design_vars[idx-1]) を使用してエラー行を構築
                original_dv_for_error = all_design_vars[idx-1]
                error_row = {
                    "Lx": original_dv_for_error["Lx"],
                    "Ly": original_dv_for_error["Ly"],
                    "H1": original_dv_for_error["H1"],
                    "H2": original_dv_for_error["H2"],
                    "tf": original_dv_for_error["tf"],
                    "tr": original_dv_for_error["tr"],
                    "bc": original_dv_for_error["bc"],
                    "hc": original_dv_for_error["hc"],
                    "tw_ext": original_dv_for_error["tw_ext"],
                    "wall_tilt_angle": original_dv_for_error.get("wall_tilt_angle", 0.0),
                    "window_ratio_2f": original_dv_for_error.get("window_ratio_2f", 0.4),
                    "roof_morph": original_dv_for_error.get("roof_morph", 0.5),
                    "roof_shift": original_dv_for_error.get("roof_shift", 0.0),
                    "balcony_depth": original_dv_for_error.get("balcony_depth", 0.0),
                    "cost_per_sqm": float("nan"),
                    "co2_per_sqm": float("nan"),
                    "comfort_score": float("nan"),
                    "constructability_score": float("nan"),
                    "safety_factor": float("nan"),
                    "total_cost": float("nan"),
                    "floor_area": float("nan"),
                    "design_pattern": "",
                    "evaluation_status": "error",
                    "evaluation_time_s": float("nan"),
                    "fcstd_path": "",
                }
                writer.writerow(error_row)
                f_csv.flush()
                n_fail += 1

print("\n" + "="*80)
total_elapsed = time.time() - t0_all
print(f"✅ 全バッチ処理完了！")
print(f"  合計時間: {total_elapsed:.1f}s")
print(f"  成功: {n_ok}件, タイムアウト: {n_timeout}件, エラー: {n_fail}件")

# --------------------------------------------------------------------------------
# 後処理: グラフ生成
# --------------------------------------------------------------------------------
print("\n📈 グラフ生成中 ...")
try:
    df = pd.read_csv(CSV_PATH)
    # ∞ を NaN に置換し，プロット対象で欠損を除外
    df.replace([float("inf"), -float("inf")], pd.NA, inplace=True)
    pairs = [
        ("safety_factor", "cost_per_sqm"),
        ("safety_factor", "co2_per_sqm"),
        ("safety_factor", "comfort_score"),
        ("safety_factor", "constructability_score"),
    ]
    for x, y in pairs:
        plt.figure(figsize=(6,5))
        plot_df = df[[x, y]].dropna() # NaN値を除外してプロット
        plt.scatter(plot_df[x], plot_df[y], alpha=0.7, edgecolors="k")
        
        # 英語ラベルに変更
        x_label_map = {
            "Lx": "建物幅",
            "Ly": "建物奥行き",
            "H1": "1階高さ",
            "H2": "2階高さ",
            "tf": "床スラブ厚",
            "tr": "屋根スラブ厚",
            "bc": "柱幅",
            "hc": "柱高さ",
            "tw_ext": "外壁厚",
            "safety_factor": "安全率",
            "cost_per_sqm": "建設コスト（円/m²）",
            "co2_per_sqm": "CO2排出量（kg-CO2/m²）",
            "comfort_score": "快適性スコア",
            "constructability_score": "施工性スコア"
        }
        plt.xlabel(x_label_map.get(x, x))
        plt.ylabel(x_label_map.get(y, y))
        plt.title(f"{x_label_map.get(y, y)} vs {x_label_map.get(x, x)}")
        
        plt.grid(True)
        plt.tight_layout()
        out_png = f"{x}_vs_{y}.png"
        plt.savefig(out_png)
        plt.close()
        print(f"   📊 {out_png} 出力済み")
except Exception as e:
    print(f"⚠️ グラフ生成失敗: {e}")
    print(f"エラー詳細: {e}")

print("\n✅ バッチ完了！ CSV と PNG グラフを確認してください。")

# --------------------------------------------------------------------------------
# 終了処理: FreeCADプロセスを確実に終了
# --------------------------------------------------------------------------------
print("\n🧹 FreeCADプロセスのクリーンアップ中...")
try:
    # FreeCADドキュメントをすべてクローズ
    import FreeCAD as App
    if hasattr(App, 'listDocuments'):
        for doc_name in App.listDocuments():
            try:
                App.closeDocument(doc_name)
                print(f"  ✅ ドキュメント '{doc_name}' をクローズしました")
            except:
                pass
    
    # FreeCADをクリーンに終了
    if hasattr(App, 'closeAllDocuments'):
        App.closeAllDocuments()
    
    # ガベージコレクションを実行
    import gc
    gc.collect()
    
    print("✅ FreeCADクリーンアップ完了")
    
except Exception as e:
    print(f"⚠️ クリーンアップ中にエラー: {e}")

# 最後にもう一度.FCBakファイルを削除
print("\n🗑️ 残っている.FCBakファイルを削除中...")
try:
    import glob
    fcbak_files = glob.glob(os.path.join(fcstd_output_dir, "*.FCBak"))
    if fcbak_files:
        print(f"  {len(fcbak_files)}個の.FCBakファイルを削除")
        for fcbak in fcbak_files:
            try:
                os.remove(fcbak)
            except:
                pass
        print("✅ .FCBakファイル削除完了")
    else:
        print("✅ 削除する.FCBakファイルはありません")
except Exception as e:
    print(f"⚠️ .FCBakファイル削除エラー: {e}")

# 実行マーカーを削除
try:
    if os.path.exists(RUNNING_MARKER):
        os.remove(RUNNING_MARKER)
        print("✅ 実行マーカーを削除しました")
except:
    pass

# プロセスを確実に終了
print("\n👋 プロセスを終了します...")
import sys
sys.exit(0)
