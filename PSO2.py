#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PSO2_optimization.py
ビット変数対応の粒子群最適化アルゴリズムによる建築設計最適化
材料選択(0/1)を含む混合整数最適化問題対応版
simple_random_batch2.pyと同じパラメータ定義域を使用
"""

# ==================== ビット変換方法の選択 ====================
# 材料選択（0:コンクリート, 1:木材）をどのように決定するか
# 
# "threshold": 閾値法 - 0.5を境界として0/1を決定（最もシンプル）
# "sigmoid": 確率法 - 0〜1の値を確率として解釈（ランダム性あり）
# "bpso": Binary PSO - 速度を確率に変換する専用手法（理論的）
# ================================================================
BINARY_METHOD = "threshold"  # ← ここを変更して手法を選択

import numpy as np
import csv
import random
import time
import signal
import sys
import os
import gc

# PSOパラメータ
N_PARTICLES = int(os.environ.get('PSO_N_PARTICLES', 15))  # 粒子数
MAX_ITER = int(os.environ.get('PSO_N_ITERATIONS', 20))     # 反復回数
W = 0.7           # 慣性重み
C1 = 1.5          # 個人的最良解(pbest)への加速係数
C2 = 1.5          # 群れ全体の最良解(gbest)への加速係数
V_MAX = 0.2       # 最大速度（探索範囲の割合）- threshold/sigmoid用

# Binary PSO専用パラメータ
# bpso法では速度vをシグモイド関数 1/(1+exp(-v)) で確率に変換
# v=±4で確率が約0.02〜0.98となり、適度な探索が可能
# これより大きいと常に0か1になり探索できなくなる
V_MAX_BINARY = 4.0  # bpso法専用の速度制限


# ---------- 設計変数の境界値 ----------
# 連続値パラメータ範囲の定義（simple_random_batch2.pyと同じ値）
PARAM_RANGES = {
    # 建物寸法（安全率向上のため上限を制限）
    "Lx": (8.0, 12.0),          # 建物幅: 8-12m
    "Ly": (8.0, 12.0),          # 建物奥行: 8-12m
    "H1": (2.6, 3.5),           # 1階高: 2.6-3.5m
    "H2": (2.6, 3.2),           # 2階高: 2.6-3.2m
    
    # 構造部材寸法（安全率を抑えるため上限を下げる）
    "tf": (350, 500),           # 床スラブ厚: 350-500mm
    "tr": (350, 500),           # 屋根スラブ厚: 350-500mm
    "bc": (400, 800),           # 柱幅: 400-800mm
    "hc": (400, 800),           # 柱高さ: 400-800mm
    "tw_ext": (300, 450),       # 外壁厚: 300-450mm
    
    # その他の設計パラメータ（安定的な範囲に調整）
    "wall_tilt_angle": (-30.0, 30.0),  # 壁傾斜角: -30〜30度
    "window_ratio_2f": (0.1, 0.7),     # 2階窓比率: 0.1〜0.7
    "roof_morph": (0.1, 0.9),          # 屋根形態: 0.1〜0.9
    "roof_shift": (-0.5, 0.5),         # 屋根シフト: -0.5〜0.5
    "balcony_depth": (1.0, 3.5),       # バルコニー深さ: 1.0〜3.5m
}

# ビット変数（材料選択）の定義（simple_random_batch2.pyと同様に0/1のみ）
BINARY_PARAMS = {
    "material_columns": (0, 1),      # 柱材料（0:コンクリート, 1:木材）
    "material_floor1": (0, 1),       # 1階床材料
    "material_floor2": (0, 1),       # 2階床材料
    "material_roof": (0, 1),         # 屋根材料
    "material_walls": (0, 1),        # 外壁材料
    "material_balcony": (0, 1),      # バルコニー材料
}

# ---------- 目的関数の計算 ----------
def calculate_fitness(cost, safety):
    """
    目的関数の計算（コスト最小化 + 安全率制約）
    
    Parameters:
    -----------
    cost : float
        建設コスト（円/m²）
    safety : float
        安全率
        
    Returns:
    --------
    float
        適応度（最小化）
    """
    # 基本はコスト最小化
    fitness = cost
    
    # 安全率制約（2.0以上を推奨）
    if safety < 2.0:
        penalty = (2.0 - safety) * 100000  # 大きなペナルティ
        fitness += penalty
    
    return fitness




# ---------- オフスクリーン backend を指定 ----------
import matplotlib
matplotlib.use("Agg")  # X サーバ不要で PNG 保存
import matplotlib.pyplot as plt
# 日本語フォントの設定
import matplotlib.font_manager as fm
# macOSの日本語フォントを設定
plt.rcParams['font.family'] = 'Hiragino Sans'
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro', 'Yu Gothic', 'Meirio', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']
plt.rcParams['axes.unicode_minus'] = False  # マイナス記号の文字化け対策

# タイムアウト設定
EVALUATION_TIMEOUT = 20  # 20秒（FEM解析は時間がかかる）

# CSV設定
CSV_FILE = "pso2_optimization_log.csv"
# テキストログファイル設定
LOG_FILE = "pso2_progress.txt"
# 設定ファイル
SETTINGS_FILE = "pso2_settings.csv"

# 実行開始時刻を記録
start_time = time.time()

print("🚀 ビット変数対応PSO最適化による建築設計最適化開始")
print(f"⏰ 開始時刻: {time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(start_time))}")
print(f"📊 粒子数: {N_PARTICLES}, 反復回数: {MAX_ITER}")
print(f"🔧 PSO パラメータ: W={W}, C1={C1}, C2={C2}")
print(f"🔢 ビット変換方法: {BINARY_METHOD}")

# 乱数シード設定
base_seed = 123
rng = random.Random(base_seed)
np.random.seed(base_seed)

# ---------- 評価関数のインポート ----------
try:
    # 現在のディレクトリをパスに追加
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # モジュールをリロードして最新の変更を反映
    if 'generate_building_fem_analyze' in sys.modules:
        del sys.modules['generate_building_fem_analyze']
    
    from generate_building_fem_analyze import evaluate_building_from_params
    print("✅ 評価関数のインポート成功（最新版をロード）")
except Exception as e:
    print(f"❌ インポートエラー: {e}")
    sys.exit(1)



# パラメータ名のリスト（順序を保持）
PARAM_NAMES = list(PARAM_RANGES.keys()) + list(BINARY_PARAMS.keys())
CONTINUOUS_PARAMS = list(PARAM_RANGES.keys())
BINARY_PARAM_NAMES = list(BINARY_PARAMS.keys())

# 連続値パラメータのインデックス
continuous_indices = list(range(len(CONTINUOUS_PARAMS)))
# ビットパラメータのインデックス
binary_indices = list(range(len(CONTINUOUS_PARAMS), len(PARAM_NAMES)))

def get_bounds():
    """設計変数の上下限（ビット変数も0-1の連続値として扱う）"""
    lower = []
    upper = []
    # 連続値パラメータ
    for param in CONTINUOUS_PARAMS:
        lower.append(PARAM_RANGES[param][0])
        upper.append(PARAM_RANGES[param][1])
    # ビットパラメータ（内部的には0-1の連続値として扱う）
    for param in BINARY_PARAM_NAMES:
        lower.append(0.0)
        upper.append(1.0)
    return np.array(lower), np.array(upper)


# ---------- ビット変換関数 ----------
def sigmoid(x):
    """シグモイド関数"""
    return 1 / (1 + np.exp(-x))

def convert_to_binary(continuous_value, method="threshold"):
    """
    連続値を2値（0/1）に変換
    
    Parameters:
    -----------
    continuous_value : float or np.array
        連続値（0-1の範囲）※bpso法の場合は速度値
    method : str
        変換方法 ("threshold", "sigmoid", "bpso")
    """
    if method == "threshold":
        # ========== 閾値法 ==========
        # 0-1の範囲を2分割
        # 0.0-0.5: コンクリート(0)
        # 0.5-1.0: 木材(1)
        result = np.zeros_like(continuous_value, dtype=int)
        result[continuous_value > 0.5] = 1
        return result
    
    elif method == "sigmoid":
        # ========== 確率法 ==========
        # 連続値を材料選択の確率として解釈
        prob = continuous_value
        rand = np.random.random(prob.shape)
        result = np.zeros_like(continuous_value, dtype=int)
        # 確率的に木材を選択
        result[rand < prob] = 1  # 木材
        return result
    
    elif method == "bpso":
        # ========== Binary PSO法 ==========
        # 速度を確率に変換して2値を決定
        prob = sigmoid(continuous_value)
        rand = np.random.random(prob.shape)
        result = np.zeros_like(continuous_value, dtype=int)
        result[rand < prob] = 1  # 木材
        return result
    
    else:
        raise ValueError(f"Unknown conversion method: {method}")

# 後方互換性のため旧関数名も残す
def convert_to_ternary(continuous_value, method="threshold"):
    """旧関数名（廃止予定）"""
    return convert_to_binary(continuous_value, method)


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
    """SIGALRM で投げる独自例外"""
    pass

def _timeout_handler(signum, frame):
    raise TimeoutError("evaluation timeout")

_HAS_SIGALRM = hasattr(signal, "SIGALRM")

# ---------- 評価関数ラッパー ----------
def _evaluate_once(design_vars: dict, timeout_s: int = EVALUATION_TIMEOUT):
    """タイムアウト付き評価"""
    try:
        if _HAS_SIGALRM:
            signal.alarm(timeout_s)
        res = evaluate_building_from_params(design_vars, save_fcstd=False)
        if _HAS_SIGALRM:
            signal.alarm(0)  # タイムアウトキャンセル
        return res
    except TimeoutError:
        raise TimeoutError("evaluation timeout")
    except Exception as e:
        raise e
    finally:
        _cleanup_freecad_memory()

# ---------- ベクトル⇔設計変数変換 ----------
def _vector_to_design(vec):
    """ベクトル形式から設計変数辞書へ変換（ビット変換含む）"""
    dv = {}
    
    # 連続値パラメータ
    for i, k in enumerate(CONTINUOUS_PARAMS):
        v = vec[i]
        if k in ["tf", "tr", "bc", "hc", "tw_ext"]:
            dv[k] = int(round(v))
        else:
            dv[k] = float(v)
    
    # ビットパラメータ（変換方法に応じて処理）
    for i, k in enumerate(BINARY_PARAM_NAMES):
        idx = len(CONTINUOUS_PARAMS) + i
        continuous_val = vec[idx]
        
        if BINARY_METHOD == "bpso":
            # BPSOの場合は速度を使用するため、ここでは閾値法を使用
            if continuous_val > 0.5:
                dv[k] = 1  # 木材
            else:
                dv[k] = 0  # コンクリート
        else:
            # threshold または sigmoid の場合
            dv[k] = int(convert_to_binary(np.array([continuous_val]), method=BINARY_METHOD)[0])
    
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
        
        # ビット変数用の速度制限を設定
        if BINARY_METHOD == "bpso":
            for idx in binary_indices:
                self.velocity[idx] = np.clip(self.velocity[idx], -V_MAX_BINARY, V_MAX_BINARY)
        
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

    def update_velocity_and_position(self, gbest_position, w, c1, c2):
        """速度と位置の更新（Binary PSO対応）"""
        r1 = np.random.random(len(self.position))
        r2 = np.random.random(len(self.position))
        
        # 速度更新
        self.velocity = (
            w * self.velocity +
            c1 * r1 * (self.pbest_position - self.position) +
            c2 * r2 * (gbest_position - self.position)
        )
        
        # 速度制限（手法に応じて異なる）
        if BINARY_METHOD == "bpso":
            # ===== Binary PSO法の場合 =====
            # ビット変数と連続変数で異なる速度制限を適用
            
            # ビット変数：速度は確率に変換されるため、大きめの制限（±4）
            for idx in binary_indices:
                self.velocity[idx] = np.clip(self.velocity[idx], -V_MAX_BINARY, V_MAX_BINARY)
            
            # 連続変数：通常の速度制限
            for idx in continuous_indices:
                v_max = V_MAX * (self.bound_up[idx] - self.bound_low[idx])
                self.velocity[idx] = np.clip(self.velocity[idx], -v_max, v_max)
        else:
            # ===== threshold法・sigmoid法の場合 =====
            # すべての変数に同じ速度制限を適用
            v_max = V_MAX * (self.bound_up - self.bound_low)
            self.velocity = np.clip(self.velocity, -v_max, v_max)
        
        # 位置更新（手法に応じて異なる）
        if BINARY_METHOD == "bpso":
            # ===== Binary PSO法の場合 =====
            # 連続変数とビット変数を別々に処理
            new_position = np.copy(self.position)
            
            # 連続変数：通常の位置更新（位置 = 位置 + 速度）
            for idx in continuous_indices:
                new_position[idx] = self.position[idx] + self.velocity[idx]
            
            # ビット変数：速度を確率に変換して0/1を決定
            # 速度が大きい → 木材になりやすい
            for idx in binary_indices:
                prob = sigmoid(self.velocity[idx])
                rand = rng.random()
                # 確率的に2値を選択
                if rand < prob:
                    new_position[idx] = 1  # 木材
                else:
                    new_position[idx] = 0  # コンクリート
            
            self.position = new_position
        else:
            # ===== threshold法・sigmoid法の場合 =====
            # すべての変数を通常通り更新（ビット変換は評価時に行う）
            self.position = self.position + self.velocity

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
        
        # 目的関数の計算
        particle.fitness = calculate_fitness(particle.cost, particle.safety)
        
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
    writer.writerow([
        "iteration", "particle", "fitness", "cost", "safety",
        "co2", "comfort", "constructability",
        "material_columns", "material_floor1", "material_floor2", 
        "material_roof", "material_walls", "material_balcony"
    ])

# ---------- テキストログファイルの初期化 ----------
with open(LOG_FILE, "w") as f:
    f.write("PSO2最適化進捗ログ（ビット変数対応）\n")
    f.write(f"開始時刻: {time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(start_time))}\n")
    f.write(f"粒子数: {N_PARTICLES}, 反復回数: {MAX_ITER}\n")
    f.write(f"ビット変換方法: {BINARY_METHOD}\n")
    f.write("-"*60 + "\n")
    f.write("反復\tgbest値\tpbest平均\tpbest標準偏差\n")
    f.write("-"*60 + "\n")

# ---------- 設定パラメータをCSVに出力 ----------
lower_bounds, upper_bounds = get_bounds()

with open(SETTINGS_FILE, "w", newline="", encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    # PSOパラメータ
    writer.writerow(["PSO2設定（ビット変数対応）"])
    writer.writerow(["パラメータ", "値"])
    writer.writerow(["粒子数", N_PARTICLES])
    writer.writerow(["反復回数", MAX_ITER])
    writer.writerow(["慣性重み(W)", W])
    writer.writerow(["個人最良係数(C1)", C1])
    writer.writerow(["群最良係数(C2)", C2])
    writer.writerow(["最大速度(V_MAX)", V_MAX])
    writer.writerow(["ビット変換方法", BINARY_METHOD])
    writer.writerow(["評価タイムアウト(秒)", EVALUATION_TIMEOUT])
    writer.writerow(["乱数シード", base_seed])
    writer.writerow([])
    
    # 設計変数の範囲
    writer.writerow(["設計変数の範囲"])
    writer.writerow(["変数名", "最小値", "最大値", "単位", "タイプ"])
    
    # 連続変数
    for i, name in enumerate(CONTINUOUS_PARAMS):
        unit = ""
        if name in ["Lx", "Ly", "H1", "H2", "balcony_depth"]:
            unit = "m"
        elif name in ["tf", "tr", "bc", "hc", "tw_ext"]:
            unit = "mm"
        elif name == "wall_tilt_angle":
            unit = "度"
        elif name in ["window_ratio_2f", "roof_morph", "roof_shift"]:
            unit = "-"
        writer.writerow([name, PARAM_RANGES[name][0], PARAM_RANGES[name][1], unit, "連続"])
    
    # ビット変数
    for name in BINARY_PARAM_NAMES:
        writer.writerow([name, 0, 1, "-", "ビット"])
    
    writer.writerow([])
    writer.writerow([f"実行開始時刻: {time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(start_time))})"])

# ---------- 初期粒子群の生成 ----------
print("\n📊 初期粒子群の生成と評価...")
bounds = get_bounds()
swarm = []

# グローバルベスト
gbest_position = None
gbest_fitness = float("inf")

# シグナルハンドラの設定
if _HAS_SIGALRM:
    signal.signal(signal.SIGALRM, _timeout_handler)

for idx in range(N_PARTICLES):
    print(f"\n🧬 粒子 {idx+1}/{N_PARTICLES}")
    particle = Particle(bounds)
    evaluate_particle(particle, idx)
    
    # グローバルベストの更新
    if particle.fitness < gbest_fitness:
        gbest_fitness = particle.fitness
        gbest_position = np.copy(particle.position)
    
    # CSV記録
    dv = _vector_to_design(particle.position)
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            0, idx+1, particle.fitness, particle.cost, particle.safety,
            particle.co2, particle.comfort, particle.constructability,
            dv.get("material_columns", 0), dv.get("material_floor1", 0),
            dv.get("material_floor2", 0), dv.get("material_roof", 0),
            dv.get("material_walls", 0), dv.get("material_balcony", 0)
        ])
    
    swarm.append(particle)

# 最良粒子の表示
print(f"\n🏆 初期世代の最良解:")
print(f"  fitness = {gbest_fitness:.2f}")
best_design = _vector_to_design(gbest_position)
print(f"  設計変数 = {best_design}")

# 初期世代のログ記録
pbest_values = [p.pbest_fitness for p in swarm]
pbest_mean = np.mean(pbest_values)
pbest_std = np.std(pbest_values)
with open(LOG_FILE, "a") as f:
    f.write(f"0\t{gbest_fitness:.2f}\t{pbest_mean:.2f}\t{pbest_std:.2f}\n")

# ---------- PSO反復ループ ----------
history = []
all_positions = []  # 全世代の全粒子位置を記録

for iter_num in range(MAX_ITER):
    print(f"\n{'='*60}")
    print(f"反復 {iter_num+1}/{MAX_ITER}")
    print(f"{'='*60}")
    
    for idx, particle in enumerate(swarm):
        # 速度と位置の更新
        particle.update_velocity_and_position(gbest_position, W, C1, C2)
        
        # 境界処理（連続変数のみ）
        particle.position, particle.velocity = apply_reflection_boundary(
            particle.position, particle.velocity, particle.bound_low, particle.bound_up
        )
        
        # 評価
        print(f"\n反復 {iter_num+1}/{MAX_ITER}  評価 {idx+1}/{N_PARTICLES}")
        evaluate_particle(particle, idx)
        
        # グローバルベストの更新
        if particle.fitness < gbest_fitness:
            gbest_fitness = particle.fitness
            gbest_position = np.copy(particle.position)
        
        # CSV記録
        dv = _vector_to_design(particle.position)
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                iter_num+1, idx+1, particle.fitness, particle.cost, particle.safety,
                particle.co2, particle.comfort, particle.constructability,
                dv.get("material_columns", 0), dv.get("material_floor1", 0),
                dv.get("material_floor2", 0), dv.get("material_roof", 0),
                dv.get("material_walls", 0), dv.get("material_balcony", 0)
            ])
        
        # 現在の粒子位置を記録（安全率とコスト）
        if particle.safety > 0 and particle.cost < float('inf'):
            all_positions.append({
                'iteration': iter_num + 1,
                'particle': idx + 1,
                'safety': particle.safety,
                'cost': particle.cost
            })
    
    # 最良解の記録
    best_particle = min(swarm, key=lambda p: p.fitness)
    history.append({
        'iteration': iter_num+1,
        'fitness': gbest_fitness,
        'cost': best_particle.cost,
        'safety': best_particle.safety
    })
    
    print(f"\n🎯 現在の最良解:")
    print(f"  fitness = {gbest_fitness:.2f}")
    print(f"  cost = {best_particle.cost:.0f} 円/m²")
    print(f"  safety = {best_particle.safety:.2f}")
    
    # 材料選択の表示
    best_dv = _vector_to_design(gbest_position)
    materials = {k: v for k, v in best_dv.items() if k.startswith("material_")}
    print(f"  材料選択: {materials}")
    
    # 各反復後のログ記録
    pbest_values = [p.pbest_fitness for p in swarm]
    pbest_mean = np.mean(pbest_values)
    pbest_std = np.std(pbest_values)
    with open(LOG_FILE, "a") as f:
        f.write(f"{iter_num+1}\t{gbest_fitness:.2f}\t{pbest_mean:.2f}\t{pbest_std:.2f}\n")

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
    if k.startswith("material_"):
        material_names = {0: "コンクリート", 1: "木材"}
        material_name = material_names.get(v, "不明")
        print(f"  {k} = {v} ({material_name})")
    else:
        print(f"  {k} = {v}")

# ---------- 収束グラフ ----------
print("\n📈 収束グラフを生成中...")
plt.figure(figsize=(10, 6))

iterations = [h['iteration'] for h in history]
fitness_vals = [h['fitness'] for h in history]
cost_vals = [h['cost'] for h in history]
safety_vals = [h['safety'] for h in history]

# 適応度のプロット
plt.subplot(2, 2, 1)
plt.plot(iterations, fitness_vals, 'b-o', markersize=4)
plt.xlabel('反復回数')
plt.ylabel('適応度（最小化）')
plt.title('適応度の推移')
plt.grid(True)

# コストのプロット
plt.subplot(2, 2, 2)
plt.plot(iterations, cost_vals, 'g-o', markersize=4)
plt.xlabel('反復回数')
plt.ylabel('コスト（円/m²）')
plt.title('建設コストの推移')
plt.grid(True)

# 安全率のプロット
plt.subplot(2, 2, 3)
plt.plot(iterations, safety_vals, 'r-o', markersize=4)
plt.axhline(y=2.0, color='r', linestyle='--', label='推奨値')
plt.xlabel('反復回数')
plt.ylabel('安全率')
plt.title('安全率の推移')
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.savefig('pso2_convergence.png', dpi=150)
plt.close()

print("✅ 収束グラフを pso2_convergence.png に保存しました")
print("\n💾 詳細なログは pso2_optimization_log.csv を確認してください")
print("📝 進捗ログは pso2_progress.txt を確認してください")
print("⚙️ 実行時の設定は pso2_settings.csv を確認してください")

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