#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PSO.py
粒子群最適化アルゴリズムによる建築設計最適化
"""

# ---------- プロセスクリーンアップ ----------
import subprocess
import os
import platform

def cleanup_zombie_processes():
    """起動時に古いプロセスをクリーンアップ（subprocessのみ使用）"""
    print("\n🧹 古いプロセスをクリーンアップ中...")
    
    try:
        current_pid = os.getpid()
        killed_count = 0
        
        # macOS/Linuxでのクリーンアップ
        if platform.system() != 'Windows':
            # PSO.pyのプロセスを検索
            try:
                # 停止状態のPSO.pyプロセスを検索
                ps_cmd = "ps aux | grep 'freecadcmd.*PSO.py' | grep -v grep | awk '{print $2, $8}'"
                result = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True)
                
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            parts = line.split()
                            if len(parts) >= 2:
                                pid = int(parts[0])
                                status = parts[1]
                                
                                # 自分自身は除外
                                if pid == current_pid:
                                    continue
                                
                                # T（停止）状態のプロセスを終了
                                if 'T' in status:
                                    try:
                                        subprocess.run(f"kill -9 {pid}", shell=True, check=False)
                                        killed_count += 1
                                        print(f"  ✓ PID {pid} を終了しました")
                                    except:
                                        pass
                
                # ccxプロセスも同様にクリーンアップ
                ccx_cmd = "ps aux | grep 'ccx' | grep -v grep | awk '{print $2, $8}'"
                result = subprocess.run(ccx_cmd, shell=True, capture_output=True, text=True)
                
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            parts = line.split()
                            if len(parts) >= 2:
                                pid = int(parts[0])
                                status = parts[1]
                                
                                # T（停止）状態のプロセスを終了
                                if 'T' in status:
                                    try:
                                        subprocess.run(f"kill -9 {pid}", shell=True, check=False)
                                        killed_count += 1
                                        print(f"  ✓ CalculiX PID {pid} を終了しました")
                                    except:
                                        pass
                
            except Exception as e:
                print(f"  ⚠️ プロセス検索中にエラー: {e}")
        
        if killed_count > 0:
            print(f"✅ {killed_count}個の古いプロセスをクリーンアップしました")
        else:
            print("✅ クリーンアップが必要なプロセスはありません")
            
    except Exception as e:
        print(f"⚠️ プロセスクリーンアップ中にエラー: {e}")
        # エラーが発生してもPSOは続行

# 起動時にクリーンアップを実行
cleanup_zombie_processes()


# ========================================
# ★★★ 重要：PSOパラメータ設定（外部設定ファイルからインポート） ★★★
# ========================================
from pso_config import (
    N_PARTICLES,
    MAX_ITER,
    W,
    C1,
    C2,
    V_MAX,
    variable_ranges,
    calculate_fitness
)



PARAM_RANGES = variable_ranges


import pandas as pd
import numpy as np
import csv
import random
import time
import signal
import sys
import os
import gc
import json

# ---------- matplotlib関連のインポートを削除（monitor_pso_mac.pyに移行） ----------

# 最後の更新時刻を記録（1分ごとの更新用）
# リストを使ってグローバル変数の問題を回避
update_time_tracker = [0]

# 開始時刻を記録
start_time = time.time()

# タイムアウト設定
EVALUATION_TIMEOUT = 20  # 20秒（FEM解析は時間がかかる）

# 出力ディレクトリの設定
OUTPUT_DIR = "pso_output"
CSV_DIR = os.path.join(OUTPUT_DIR, "csv")
IMAGE_DIR = os.path.join(OUTPUT_DIR, "images")

# 出力ディレクトリの作成（存在しない場合）
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)

# CSV設定
CSV_FILE = os.path.join(CSV_DIR, "pso_particle_positions.csv")  # 各ステップの全粒子位置（現在位置）を記録
PBEST_CSV_FILE = os.path.join(CSV_DIR, "pso_pbest_positions.csv")  # 各ステップの全粒子のpbest（個人最良位置）を記録
# 設定ファイル
SETTINGS_FILE = os.path.join(CSV_DIR, "pso_settings.csv")

# リアルタイムデータ共有用ファイル（OUTPUT_DIRに変更）
REALTIME_DATA_FILE = os.path.join(OUTPUT_DIR, "pso_realtime_data.json")
# 完了フラグファイル
COMPLETED_FLAG_FILE = os.path.join(OUTPUT_DIR, "pso_completed.flag")

print("🚀 粒子群最適化アルゴリズムによる建築設計最適化開始")
print(f"📊 粒子数: {N_PARTICLES}, 反復回数: {MAX_ITER}")
print(f"🔧 PSO パラメータ: W={W}, C1={C1}, C2={C2}")
print(f"\n📝 リアルタイムデータ: {REALTIME_DATA_FILE}")
print("💡 別ターミナルで monitor_pso.py を実行するとリアルタイム監視できます")

# 乱数シード設定
base_seed = 123
rng = random.Random(base_seed)
np.random.seed(base_seed)

# ---------- 評価関数のインポート ----------
try:
    # 現在の環境に合わせて修正
    from generate_building_fem_analyze import evaluate_building_from_params
    print("✅ 評価関数のインポート成功")
except Exception as e:
    print(f"❌ インポートエラー: {e}")
    sys.exit(1)



# パラメータ名のリスト（順序を保持）
PARAM_NAMES = ["Lx", "Ly", "H1", "H2", "tf", "tr", "bc", "hc", "tw_ext",
               "wall_tilt_angle", "window_ratio_2f", "roof_morph", "roof_shift", "balcony_depth",
               "material_columns", "material_floor1", "material_floor2", 
               "material_roof", "material_walls", "material_balcony"]

def get_bounds():
    """設計変数の上下限"""
    lower = []
    upper = []
    for param in PARAM_NAMES:
        lower.append(PARAM_RANGES[param][0])
        upper.append(PARAM_RANGES[param][1])
    return np.array(lower), np.array(upper)


# ---------- 境界処理（鏡像反射） ----------
def apply_reflection_boundary(position, velocity, lower_bound, upper_bound):
    """
    鏡像反射による境界処理
    
    Parameters:
    -----------
    position : np.array
        粒子の位置
    velocity : np.array
        粒子の速度
    lower_bound : np.array
        下限値
    upper_bound : np.array
        上限値
        
    Returns:
    --------
    position : np.array
        反射後の位置
    velocity : np.array
        反射後の速度
    """
    # 各次元で境界チェックと反射処理
    for i in range(len(position)):
        # 下限を下回った場合
        if position[i] < lower_bound[i]:
            # 境界からの距離
            distance = lower_bound[i] - position[i]
            # 鏡像反射位置
            position[i] = lower_bound[i] + distance
            # 速度反転
            velocity[i] = -velocity[i]
            
        # 上限を上回った場合
        elif position[i] > upper_bound[i]:
            # 境界からの距離
            distance = position[i] - upper_bound[i]
            # 鏡像反射位置
            position[i] = upper_bound[i] - distance
            # 速度反転
            velocity[i] = -velocity[i]
    
    # それでも境界外の場合はクリッピング（保険）
    position = np.clip(position, lower_bound, upper_bound)
    
    return position, velocity

# ---------- FreeCADのメモリクリーンアップ ----------
def _cleanup_freecad_memory():
    """FreeCADの開いたDocを片付けてRAMリークを抑える"""
    try:
        import FreeCAD as App
        for doc in list(App.listDocuments().values()):
            try:
                App.closeDocument(doc.Name)
            except Exception:
                pass
    except Exception:
        pass
    gc.collect()

# ---------- タイムアウト制御 ----------
class TimeoutError(Exception):
    """タイムアウト例外"""
    pass

def _timeout_handler(signum, frame):
    raise TimeoutError("evaluation timeout")

_HAS_SIGALRM = hasattr(signal, "SIGALRM")

# ---------- 評価関数ラッパー ----------
def _evaluate_once(design_vars: dict, timeout_s: int = EVALUATION_TIMEOUT):
    """タイムアウト付き評価"""
    if _HAS_SIGALRM:
        # Unix系OS（Linux, macOS）の場合
        try:
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(timeout_s)
            res = evaluate_building_from_params(design_vars, save_fcstd=False)
            signal.alarm(0)  # タイムアウトキャンセル
            return res
        except TimeoutError:
            raise TimeoutError("evaluation timeout")
        except Exception as e:
            raise e
        finally:
            if _HAS_SIGALRM:
                signal.alarm(0)
            _cleanup_freecad_memory()
    else:
        # Windowsの場合（タイムアウトなし）
        try:
            res = evaluate_building_from_params(design_vars, save_fcstd=False)
            return res
        except Exception as e:
            raise e
        finally:
            _cleanup_freecad_memory()

# ---------- ベクトル⇔設計変数変換 ----------
def _vector_to_design(vec):
    """ベクトル形式から設計変数辞書へ変換"""
    dv = {}
    for k, v in zip(PARAM_NAMES, vec):
        if k in ["tf", "tr", "bc", "hc", "tw_ext"]:
            # 整数値（mm単位）
            dv[k] = int(round(v))
        elif k.startswith("material_"):
            # 材料パラメータ：連続値を離散値に変換
            # 0.5未満 → 0（コンクリート）、0.5以上 → 1（木材）
            dv[k] = 1 if v >= 0.5 else 0
        else:
            dv[k] = float(v)
    
    return dv

# ---------- 粒子クラス ----------
class Particle:
    def __init__(self, bounds):
        self.bound_low, self.bound_up = bounds
        dim = len(self.bound_low)
        
        # 位置の初期化（ランダム）
        self.position = np.array([
            low + (up - low) * rng.random()
            for low, up in zip(self.bound_low, self.bound_up)
        ])
        
        # 速度の初期化（小さなランダム値）
        self.velocity = np.array([
            (up - low) * (rng.random() - 0.5) * 0.1
            for low, up in zip(self.bound_low, self.bound_up)
        ])
        
        # 個人的最良位置
        self.pbest_position = np.copy(self.position)
        self.pbest_fitness = float("inf")
        
        # 現在の適応度
        self.fitness = float("inf")
        
        # 評価値の詳細
        self.safety = 0.0
        self.cost = float("inf")
        self.co2 = float("inf")
        self.comfort = 0.0
        self.constructability = 0.0

# ---------- 粒子評価関数 ----------
def evaluate_particle(particle: Particle, idx: int = None) -> float:
    """粒子の評価（コスト最小化 + 安全率制約）"""
    try:
        dv = _vector_to_design(particle.position)
        res = _evaluate_once(dv)
        
        if res['status'] != 'Success':
            raise Exception(f"評価失敗: {res['message']}")
        
        # 各評価値を取得
        particle.cost = res["economic"]["cost_per_sqm"]
        particle.safety = res["safety"]["overall_safety_factor"]
        particle.co2 = res["environmental"]["co2_per_sqm"]
        particle.comfort = res["comfort"]["comfort_score"]
        particle.constructability = res["constructability"]["constructability_score"]
        
        # 目的関数の計算（全ての評価値を渡す）
        particle.fitness = calculate_fitness(
            particle.cost,
            particle.safety,
            particle.co2,
            particle.comfort,
            particle.constructability
        )
        
        # 個人的最良解の更新
        if particle.fitness < particle.pbest_fitness:
            particle.pbest_fitness = particle.fitness
            particle.pbest_position = np.copy(particle.position)
        
        if idx is not None:
            print(f"  粒子 {idx+1}: cost={particle.cost:.0f}, safety={particle.safety:.2f}, "
                  f"CO2={particle.co2:.0f}, comfort={particle.comfort:.1f}")
        
        return particle.fitness
        
    except Exception as e:
        if idx is not None:
            print(f"  ❌ 粒子 {idx+1} の評価失敗: {e}")
        particle.fitness = float("inf")
        particle.safety = 0.0
        particle.cost = float("inf")
        particle.co2 = float("inf")
        particle.comfort = 0.0
        particle.constructability = 0.0
        return float("inf")

# ---------- CSVヘッダー作成 ----------
with open(CSV_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    # 全21個の設計変数を含むヘッダー
    writer.writerow([
        "iteration", "particle", "fitness", "cost", "safety",
        "co2", "comfort", "constructability",
        # 形状パラメータ（15個）
        "Lx", "Ly", "H1", "H2", "tf", "tr", "bc", "hc", "tw_ext",
        "wall_tilt_angle", "window_ratio_2f", "roof_morph", "roof_shift", "balcony_depth",
        # 材料パラメータ（6個）
        "material_columns", "material_floor1", "material_floor2",
        "material_roof", "material_walls", "material_balcony"
    ])

# ---------- pbestログCSVヘッダー作成 ----------
with open(PBEST_CSV_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    # pbestの全21個の設計変数を含むヘッダー
    writer.writerow([
        "iteration", "particle", "pbest_fitness", "pbest_cost", "pbest_safety",
        "pbest_co2", "pbest_comfort", "pbest_constructability",
        # 形状パラメータ（15個）
        "pbest_Lx", "pbest_Ly", "pbest_H1", "pbest_H2", "pbest_tf", "pbest_tr", 
        "pbest_bc", "pbest_hc", "pbest_tw_ext",
        "pbest_wall_tilt_angle", "pbest_window_ratio_2f", 
        "pbest_roof_morph", "pbest_roof_shift", "pbest_balcony_depth",
        # 材料パラメータ（6個）
        "pbest_material_columns", "pbest_material_floor1", "pbest_material_floor2",
        "pbest_material_roof", "pbest_material_walls", "pbest_material_balcony"
    ])

# ---------- 前回の結果をクリア ----------
import shutil
if os.path.exists(CSV_DIR):
    for file in os.listdir(CSV_DIR):
        if file.endswith('.csv'):
            os.remove(os.path.join(CSV_DIR, file))
if os.path.exists(IMAGE_DIR):
    for file in os.listdir(IMAGE_DIR):
        if file.endswith('.png'):
            os.remove(os.path.join(IMAGE_DIR, file))
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)
print("✅ 前回の結果をクリアしました")

# ---------- gbest履歴CSVヘッダー作成 ----------
GBEST_HISTORY_CSV_FILE = os.path.join(CSV_DIR, "pso_gbest_history.csv")
with open(GBEST_HISTORY_CSV_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    header = [
        "iteration", "gbest_fitness", "cost", "safety",
        "co2", "comfort", "constructability"
    ] + PARAM_NAMES
    writer.writerow(header)

# ---------- テキストログファイルの初期化 ----------
# (削除済み - リアルタイムデータとCSVファイルに統合)

# ---------- 設定パラメータをCSVに出力 ----------
lower_bounds, upper_bounds = get_bounds()

# 設計変数の日本語説明
PARAM_DESCRIPTIONS = {
    "Lx": "建物幅",
    "Ly": "建物奥行",
    "H1": "1階高さ",
    "H2": "2階高さ",
    "tf": "床スラブ厚",
    "tr": "屋根スラブ厚",
    "bc": "柱幅",
    "hc": "柱高さ",
    "tw_ext": "外壁厚",
    "wall_tilt_angle": "壁傾斜角",
    "window_ratio_2f": "2階窓比率",
    "roof_morph": "屋根形態",
    "roof_shift": "屋根シフト",
    "balcony_depth": "バルコニー奥行",
    "material_columns": "柱材料",
    "material_floor1": "1階床材料",
    "material_floor2": "2階床材料",
    "material_roof": "屋根材料",
    "material_walls": "外壁材料",
    "material_balcony": "バルコニー材料"
}


with open(SETTINGS_FILE, "w", newline="", encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    # PSOパラメータ
    writer.writerow(["PSO設定"])
    writer.writerow(["パラメータ", "値"])
    writer.writerow(["粒子数", N_PARTICLES])
    writer.writerow(["反復回数", MAX_ITER])
    writer.writerow(["慣性重み(W)", W])
    writer.writerow(["個人最良係数(C1)", C1])
    writer.writerow(["群最良係数(C2)", C2])
    writer.writerow(["最大速度(V_MAX)", V_MAX])
    #writer.writerow(["評価タイムアウト(秒)", EVALUATION_TIMEOUT])
    writer.writerow(["乱数シード", base_seed])
    writer.writerow([])
    
    # 設計変数の範囲
    writer.writerow(["設計変数の範囲"])
    writer.writerow(["変数名", "説明", "最小値", "最大値", "単位"])
    for i, name in enumerate(PARAM_NAMES):
        unit = ""
        if name in ["Lx", "Ly", "H1", "H2", "balcony_depth"]:
            unit = "m"
        elif name in ["tf", "tr", "bc", "hc", "tw_ext"]:
            unit = "mm"
        elif name == "wall_tilt_angle":
            unit = "度"
        elif name in ["window_ratio_2f", "roof_morph", "roof_shift"]:
            unit = "-"
        elif name.startswith("material_"):
            unit = "0:コンクリート／1:木材"
            
        description = PARAM_DESCRIPTIONS.get(name, "")
        writer.writerow([name, description, lower_bounds[i], upper_bounds[i], unit])
    
 
    

    
    writer.writerow([])
    writer.writerow([f"実行開始時刻: {time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(start_time))})"])


print("\n設計変数の範囲")
print("変数名\t最小値\t最大値\t単位")
for i, name in enumerate(PARAM_NAMES):
    unit = ""
    if name in ["Lx", "Ly", "H1", "H2", "balcony_depth"]:
        unit = "m"
    elif name in ["tf", "tr", "bc", "hc", "tw_ext"]:
        unit = "mm"
    elif name == "wall_tilt_angle":
        unit = "度"
    elif name in ["window_ratio_2f", "roof_morph", "roof_shift"]:
        unit = "-"
    lower_bounds, upper_bounds = get_bounds()
    print(f"{name}\t{lower_bounds[i]}\t{upper_bounds[i]}\t{unit}")

# ---------- プロット関連の関数は削除（monitor_pso_mac.pyに移行） ----------



# ---------- リアルタイムデータ保存関数 ----------
def save_realtime_data(iteration, gbest_fitness, particles, best_particle):
    """リアルタイムデータをJSONファイルに保存"""
    data = {
        'timestamp': time.time(),
        'iteration': iteration,
        'max_iteration': MAX_ITER,
        'n_particles': N_PARTICLES,
        'gbest_fitness': gbest_fitness,
        'best_particle': {
            'safety': best_particle.safety,
            'cost': best_particle.cost,
            'co2': best_particle.co2,
            'comfort': best_particle.comfort,
            'constructability': best_particle.constructability
        },
        'particles': [
            {
                'position': p.position.tolist(),
                'fitness': p.fitness,
                'safety': p.safety,
                'cost': p.cost
            } for p in particles
        ],
        'progress': ((iteration + 1) / MAX_ITER) * 100,  # ステップ0=10%, ステップ9=100%
        'elapsed_time': time.time() - start_time
    }
    
    with open(REALTIME_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ---------- 古いリアルタイムデータファイルを削除 ----------
if os.path.exists(REALTIME_DATA_FILE):
    os.remove(REALTIME_DATA_FILE)
    print(f"🗑️  古いリアルタイムデータファイルを削除しました: {REALTIME_DATA_FILE}")

# ---------- プロットの初期化は削除（monitor_pso_mac.pyに移行） ----------



# ---------- 初期状態のリアルタイムデータを保存（モニタ即座表示用） ----------
# 注意: float('inf')はJSONで"Infinity"になり、JavaScriptで正しく処理される
initial_data = {
    'timestamp': start_time,
    'iteration': 0,
    'max_iteration': MAX_ITER,
    'n_particles': N_PARTICLES,
    'gbest_fitness': float('inf'),  # 初期値として無限大を設定
    'best_particle': {
        'safety': 0.0,
        'cost': 0.0,
        'co2': 0.0,
        'comfort': 0.0,
        'constructability': 0.0
    },
    'particles': [],  # 空の粒子リスト
    'progress': 0.0,  # 初期状態は0%
    'elapsed_time': 0.0,
    'status': 'initializing'  # ステータスを追加
}
with open(REALTIME_DATA_FILE, 'w') as f:
    json.dump(initial_data, f, indent=2)
print(f"📊 リアルタイムデータを初期化しました: {REALTIME_DATA_FILE}")

# 最後の更新時刻を初期化
update_time_tracker[0] = start_time

# ---------- 初期粒子群の生成 ----------
print("\n📊 初期粒子群の生成と評価...")
bounds = get_bounds()
swarm = []

# グローバルベスト
gbest_position = None
gbest_fitness = float("inf")

for idx in range(N_PARTICLES):
    print(f"\n🧬 粒子 {idx+1}/{N_PARTICLES}")
    particle = Particle(bounds)
    evaluate_particle(particle, idx)
    
    # グローバルベストの更新
    if particle.fitness < gbest_fitness:
        gbest_fitness = particle.fitness
        gbest_position = np.copy(particle.position)
    
    # CSV記録
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        design = _vector_to_design(particle.position)
        writer.writerow([
            0, idx+1, particle.fitness, particle.cost, particle.safety,
            particle.co2, particle.comfort, particle.constructability,
            # 全21個の設計変数を出力
            design["Lx"], design["Ly"], design["H1"], design["H2"],
            design["tf"], design["tr"], design["bc"], design["hc"], design["tw_ext"],
            design["wall_tilt_angle"], design["window_ratio_2f"], 
            design["roof_morph"], design["roof_shift"], design["balcony_depth"],
            design["material_columns"], design["material_floor1"],
            design["material_floor2"], design["material_roof"],
            design["material_walls"], design["material_balcony"]
        ])
    
    swarm.append(particle)

# 最良粒子の表示
print(f"\n🏆 初期ステップの最良解:")
print(f"  fitness = {gbest_fitness:.2f}")
best_design = _vector_to_design(gbest_position)
print(f"  設計変数 = {best_design}")

# 初期ステップのログ記録
pbest_values = [p.pbest_fitness for p in swarm]
pbest_mean = np.mean(pbest_values)
pbest_std = np.std(pbest_values)
# 初期ステップのログはCSVファイルに記録済み

# 初期ステップのpbest記録
with open(PBEST_CSV_FILE, "a", newline="") as f:
    writer = csv.writer(f)
    for idx, particle in enumerate(swarm):
        pbest_design = _vector_to_design(particle.pbest_position)
        writer.writerow([
            0, idx+1, particle.pbest_fitness, particle.cost, particle.safety,
            particle.co2, particle.comfort, particle.constructability,
            # pbest位置の全21個の設計変数
            pbest_design["Lx"], pbest_design["Ly"], pbest_design["H1"], pbest_design["H2"],
            pbest_design["tf"], pbest_design["tr"], pbest_design["bc"], pbest_design["hc"], 
            pbest_design["tw_ext"], pbest_design["wall_tilt_angle"], pbest_design["window_ratio_2f"], 
            pbest_design["roof_morph"], pbest_design["roof_shift"], pbest_design["balcony_depth"],
            pbest_design["material_columns"], pbest_design["material_floor1"],
            pbest_design["material_floor2"], pbest_design["material_roof"],
            pbest_design["material_walls"], pbest_design["material_balcony"]
        ])

# リアルタイムデータ保存（初期ステップ）
best_particle = min(swarm, key=lambda p: p.fitness)
save_realtime_data(0, gbest_fitness, swarm, best_particle)

# 0世代目のgbest情報を記録
with open(GBEST_HISTORY_CSV_FILE, "a", newline="") as f:
    writer = csv.writer(f)
    best_design_dict = _vector_to_design(gbest_position)
    row = [
        0, gbest_fitness, best_particle.cost, best_particle.safety,
        best_particle.co2, best_particle.comfort, best_particle.constructability
    ] + [best_design_dict[name] for name in PARAM_NAMES]
    writer.writerow(row)

# ---------- PSO反復ループ ----------
history = []
# 全粒子位置を記録（初期ステップも含む）
initial_positions = [{'iteration': 0, 'particle': i+1, 'safety': p.safety, 'cost': p.cost, 'co2': p.co2, 'comfort': p.comfort, 'constructability': p.constructability} for i, p in enumerate(swarm)]
all_positions = []

# プロット更新は削除（monitor_pso_mac.pyに移行）


import statistics

for iter_num in range(1, MAX_ITER):
    print(f"\n🔄 反復 {iter_num}/{MAX_ITER} 開始")
    
    # 各粒子の更新と評価
    for idx, particle in enumerate(swarm):
        # 速度更新（PSO基本式）
        r1 = np.random.rand(len(particle.velocity))
        r2 = np.random.rand(len(particle.velocity))
        
        cognitive = C1 * r1 * (particle.pbest_position - particle.position)
        social = C2 * r2 * (gbest_position - particle.position)
        
        particle.velocity = W * particle.velocity + cognitive + social
        
        # 速度制限
        v_limit = V_MAX * (bounds[1] - bounds[0])
        particle.velocity = np.clip(particle.velocity, -v_limit, v_limit)
        
        # 位置更新
        particle.position = particle.position + particle.velocity
        
        # 境界処理（鏡像反射）
        particle.position, particle.velocity = apply_reflection_boundary(
            particle.position, particle.velocity, bounds[0], bounds[1]
        )
        
        # 評価
        evaluate_particle(particle, idx)
        
        # グローバルベストの更新
        if particle.fitness < gbest_fitness:
            gbest_fitness = particle.fitness
            gbest_position = np.copy(particle.position)
        
        # CSV記録
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            design = _vector_to_design(particle.position)
            writer.writerow([
                iter_num, idx+1, particle.fitness, particle.cost, particle.safety,
                particle.co2, particle.comfort, particle.constructability,
                # 全21個の設計変数を出力
                design["Lx"], design["Ly"], design["H1"], design["H2"],
                design["tf"], design["tr"], design["bc"], design["hc"], design["tw_ext"],
                design["wall_tilt_angle"], design["window_ratio_2f"], 
                design["roof_morph"], design["roof_shift"], design["balcony_depth"],
                design["material_columns"], design["material_floor1"],
                design["material_floor2"], design["material_roof"],
                design["material_walls"], design["material_balcony"]
            ])
        
        # 全粒子位置の記録
        all_positions.append({
            'iteration': iter_num,
            'particle': idx+1,
            'safety': particle.safety,
            'cost': particle.cost,
            'co2': particle.co2,
            'comfort': particle.comfort,
            'constructability': particle.constructability
        })
        
        # 1分ごとにリアルタイムデータを更新（モニタリング用）
        current_time = time.time()
        if current_time - update_time_tracker[0] >= 60:  # 60秒経過したら更新
            current_best = min(swarm, key=lambda p: p.fitness)
            save_realtime_data(iter_num, gbest_fitness, swarm, current_best)
            update_time_tracker[0] = current_time
    
    # 履歴に記録
    best_particle = min(swarm, key=lambda p: p.fitness)
    history.append({
        'iteration': iter_num+1,
        'fitness': gbest_fitness,
        'cost': best_particle.cost,
        'safety': best_particle.safety,
        'co2': best_particle.co2
    })
    
    # 各反復後のpbest記録
    with open(PBEST_CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        for idx, particle in enumerate(swarm):
            pbest_design = _vector_to_design(particle.pbest_position)
            # pbest_fitnessがinf以外の場合のみ有効な評価値を記録
            if not np.isinf(particle.pbest_fitness):
                # pbestの評価値は粒子の属性から取得（pbest更新時に保存されている）
                writer.writerow([
                    iter_num, idx+1, particle.pbest_fitness, 
                    particle.cost, particle.safety,  # 現在の評価値（pbest更新時のものと異なる可能性）
                    particle.co2, particle.comfort, particle.constructability,
                    # pbest位置の全21個の設計変数
                    pbest_design["Lx"], pbest_design["Ly"], pbest_design["H1"], pbest_design["H2"],
                    pbest_design["tf"], pbest_design["tr"], pbest_design["bc"], pbest_design["hc"], 
                    pbest_design["tw_ext"], pbest_design["wall_tilt_angle"], pbest_design["window_ratio_2f"], 
                    pbest_design["roof_morph"], pbest_design["roof_shift"], pbest_design["balcony_depth"],
                    pbest_design["material_columns"], pbest_design["material_floor1"],
                    pbest_design["material_floor2"], pbest_design["material_roof"],
                    pbest_design["material_walls"], pbest_design["material_balcony"]
                ])
    
    # pbest の統計（inf を除外）
    pbest_vals = [p.pbest_fitness for p in swarm if not np.isinf(p.pbest_fitness)]
    if not pbest_vals:
        pbest_mean = float("inf")
        pbest_std = 0.0
    else:
        pbest_mean = statistics.mean(pbest_vals)
        pbest_std = statistics.pstdev(pbest_vals) if len(pbest_vals) > 1 else 0.0

    # 現在の最良粒子（gbest）
    best_particle = min(swarm, key=lambda p: p.fitness)

    # 各指標
    safety = best_particle.safety
    cost = best_particle.cost
    co2 = best_particle.co2
    comfort = best_particle.comfort
    constructability = best_particle.constructability

    # サマリ出力（コンソール）
    print(f"\n{'='*100}")
    print(f"反復 {iter_num + 1}/{MAX_ITER} 進捗サマリ")
    print(f"{'='*100}")
    print("反復\tgbest値\tpbest平均\tpbest標準偏差\t安全率\t建設コスト\tCO2排出量\t快適性スコア\t施工性スコア")
    print(f"{iter_num + 1}\t{gbest_fitness:.4e}\t{pbest_mean:.4e}\t{pbest_std:.4e}\t{safety:.3f}\t{cost:.2f}\t{co2:.2f}\t{comfort:.3f}\t{constructability:.3f}")

    # テキストログ追記 (削除済み - リアルタイムデータとCSVファイルに統合)
    
    # リアルタイムデータ保存
    save_realtime_data(iter_num, gbest_fitness, swarm, best_particle)

    # gbest履歴をCSVに記録
    with open(GBEST_HISTORY_CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        best_design_dict = _vector_to_design(gbest_position)
        row = [
            iter_num, gbest_fitness, best_particle.cost, best_particle.safety,
            best_particle.co2, best_particle.comfort, best_particle.constructability
        ] + [best_design_dict[name] for name in PARAM_NAMES]
        writer.writerow(row)
    
    # プロット更新は削除（monitor_pso_mac.pyに移行）
    
    

# ---------- 最終結果 ----------
print("\n" + "="*60)
print("🏁 最適化完了！")
print("="*60)



best_particle = min(swarm, key=lambda p: p.fitness)
best_design = _vector_to_design(gbest_position)

print(f"\n🏆 最終的な最良解:")
print(f"  fitness = {gbest_fitness:.2f}")
print(f"  cost = {best_particle.cost:.0f} 円/m²")
print(f"  safety = {best_particle.safety:.2f}")
print(f"  CO2 = {best_particle.co2:.0f} kg-CO2/m²")
print(f"  comfort = {best_particle.comfort:.1f}")
print(f"  constructability = {best_particle.constructability:.1f}")
print(f"\n設計変数:")
for k, v in best_design.items():
    print(f"  {k} = {v}")



# ---------- グラフ生成は削除（monitor_pso_mac.pyに移行） ----------

# グラフ生成は削除（monitor_pso_mac.pyで生成）
print("\n📁 出力ファイル構造:")
print(f"  {OUTPUT_DIR}/")
print(f"    └── csv/  # CSVファイル")
print(f"        ├── pso_particle_positions.csv")
print(f"        ├── pso_pbest_positions.csv")
print(f"        ├── pso_gbest_history.csv")
print(f"        └── pso_settings.csv")

# 最終リアルタイムデータを削除（完了フラグとして）
if os.path.exists(REALTIME_DATA_FILE):
    os.remove(REALTIME_DATA_FILE)
    print("\n✅ リアルタイムデータファイルを削除（最適化完了）")

# 完了フラグファイルを作成
with open(COMPLETED_FLAG_FILE, 'w') as f:
    json.dump({
        'gbest_fitness': gbest_fitness,
        'elapsed_time': time.time() - start_time,
        'timestamp': time.time()
    }, f)
print("✅ 完了フラグファイルを作成")

# 実行時間の計算と表示
end_time = time.time()
elapsed_time = end_time - start_time

# 時間を時:分:秒形式に変換
hours = int(elapsed_time // 3600)
minutes = int((elapsed_time % 3600) // 60)
seconds = int(elapsed_time % 60)

print("\n" + "="*60)
print("⏱️  実行時間")
print("="*60)
print(f"開始時刻: {time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(start_time))}")
print(f"終了時刻: {time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(end_time))}")
print(f"経過時間: {hours}時間 {minutes}分 {seconds}秒 (合計 {elapsed_time:.1f}秒)")
print(f"1反復あたりの平均時間: {elapsed_time / MAX_ITER:.1f}秒")
print(f"1粒子評価あたりの平均時間: {elapsed_time / (MAX_ITER * N_PARTICLES + N_PARTICLES):.1f}秒")

# 完了フラグを作成
COMPLETED_FLAG_FILE = os.path.join(CSV_DIR, "pso_completed.flag")
completion_data = {
    "completed_at": time.strftime('%Y/%m/%d %H:%M:%S'),
    "elapsed_time": elapsed_time,
    "gbest_fitness": gbest_fitness
}
with open(COMPLETED_FLAG_FILE, "w") as f:
    json.dump(completion_data, f, indent=2)
print(f"\n🚩 完了フラグを作成しました: {COMPLETED_FLAG_FILE}")
