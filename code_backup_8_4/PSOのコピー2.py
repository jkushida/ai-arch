#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PSO_optimization.py
粒子群最適化アルゴリズムによる建築設計最適化

Here's to the crazy ones. The rebels. The troublemakers.
The ones who think differently in the design space.
The ones who see optimal solutions where others see constraints.

They're not fond of fixed parameters. And they have
no respect for the traditional design methods.

You can evaluate them, constrain them, optimize them,
randomize them, evolve or mutate them. About the only
thing you can't do is ignore them. Because they
find better designs.

They explore. They search. They discover.
They iterate. They converge. They optimize.
They push the boundaries of architectural design forward.

Maybe they have to be stochastic. How else
can you escape from local minima and
find a global optimum? Or navigate through
a high-dimensional design space and
discover innovative structural solutions?

粒子群最適化（PSO）：建築設計の革新的最適化
- 15粒子が20世代にわたり設計空間を探索
- 形状15変数 + 材料6変数 = 21次元の最適化
- 離散値（材料選択）も連続PSOで最適化
"""

# PSOパラメータ
N_PARTICLES = 15  # 粒子数
MAX_ITER = 20     # 反復回数
W = 0.7           # 慣性重み
C1 = 1.5          # 個人的最良解(pbest)への加速係数
C2 = 1.5          # 群れ全体の最良解(gbest)への加速係数
V_MAX = 0.2       # 最大速度（探索範囲の割合）


# ---------- 設計変数の境界値 ----------
# パラメータ範囲の定義（random_building_sampler.pyと同一）
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
    
    # 材料パラメータ（0.0-1.0の連続値、0.5未満:コンクリート、0.5以上:木材）
    "material_columns": (0.0, 1.0),      # 柱材料（固定：コンクリート）
    "material_floor1": (0.0, 1.0),       # 1階床材料（固定：コンクリート）
    "material_floor2": (0.0, 1.0),       # 2階床材料（固定：コンクリート）
    "material_roof": (0.0, 1.0),         # 屋根材料（固定：コンクリート）
    "material_walls": (0.0, 1.0),        # 外壁材料（最適化対象）
    "material_balcony": (0.0, 1.0),      # バルコニー材料（固定：コンクリート）
}

# ---------- 目的関数の計算 ----------
# ===== 学生の皆さんへ：ここを自由にカスタマイズしてください！ =====
#
# 以下の例を参考に、自分の目的に合わせて適応度関数を変更できます：
#
# 例1）CO2排出量最小化（環境重視）
# def calculate_fitness(cost, safety, co2, comfort, constructability):
#     SAFETY_THRESHOLD = 2.0
#     fitness = co2  # CO2を最小化
#     if safety < SAFETY_THRESHOLD:
#         fitness += (SAFETY_THRESHOLD - safety) * 1000
#     return fitness
#
# 例2）快適性最大化（※最大化問題は負の値にする）
# def calculate_fitness(cost, safety, co2, comfort, constructability):
#     SAFETY_THRESHOLD = 2.0
#     fitness = -comfort  # 快適性を最大化（負の値）
#     if safety < SAFETY_THRESHOLD:
#         fitness += (SAFETY_THRESHOLD - safety) * 10000
#     return fitness
#
# 例3）多目的最適化（重み付け和）
# def calculate_fitness(cost, safety, co2, comfort, constructability):
#     SAFETY_THRESHOLD = 2.0
#     w1, w2, w3 = 0.5, 0.3, 0.2  # 重み係数
#     fitness = w1 * (cost/100000) + w2 * (co2/1000) + w3 * (-comfort/10)
#     if safety < SAFETY_THRESHOLD:
#         fitness += (SAFETY_THRESHOLD - safety) * 100
#     return fitness
#
# ============================================================

def calculate_fitness(cost, safety, co2, comfort, constructability):
    """
    目的関数の計算（全ての評価指標を必須引数として受け取る）
    
    Parameters:
    -----------
    cost : float
        建設コスト（円/m²）
    safety : float
        安全率
    co2 : float
        CO2排出量（kg-CO2/m²）
    comfort : float
        快適性スコア（0-10）
    constructability : float
        施工性スコア（0-10）
        
    Returns:
    --------
    float
        適応度（最小化問題として定義）
    """
    # ===== カスタマイズ可能な部分 =====
    
    # 1. 目的関数の選択（どの指標を最適化するか）
    # デフォルト：コスト最小化
    fitness = cost
    
    # 例1）CO2排出量最小化（環境重視）
    # fitness = co2
    
    # 例2）快適性最大化（※最大化問題は負の値にする）
    # fitness = -comfort  # 快適性を最大化（負の値）
    
    # 例3）施工性最大化
    # fitness = -constructability
    
    # 例4）多目的最適化（重み付け和）
    # w1, w2, w3 = 0.5, 0.3, 0.2  # 重み係数
    # fitness = w1 * (cost/100000) + w2 * (co2/1000) + w3 * (-comfort/10)
    
    # 例5）多目的最適化（コストとCO2の同時最小化）
    # fitness = 0.7 * (cost/100000) + 0.3 * (co2/1000)
    
    # 2. 制約条件の設定
    SAFETY_THRESHOLD = 2.0      # 安全率の最小値
    PENALTY_COEFFICIENT = 100000  # ペナルティの重み
    
    # 3. 安全率制約の適用（必須）
    if safety < SAFETY_THRESHOLD:
        penalty = (SAFETY_THRESHOLD - safety) * PENALTY_COEFFICIENT
        fitness += penalty
    
    # 4. 追加の制約条件（必要に応じてコメントアウトを外す）
    # if comfort < 5.0:  # 快適性5.0以上
    #     fitness += (5.0 - comfort) * 10000
    
    # if co2 > 1000:  # CO2排出量1000以下
    #     fitness += (co2 - 1000) * 100
    
    # if constructability < 6.0:  # 施工性6.0以上
    #     fitness += (6.0 - constructability) * 5000
    
    return fitness




import numpy as np
import csv
import random
import time
import signal
import sys
import os
import gc
import json

# ---------- オフスクリーン backend を指定 ----------
import matplotlib
matplotlib.use("Agg")  # X サーバ不要で PNG 保存
import matplotlib.pyplot as plt
# 日本語フォントの設定
import matplotlib.font_manager as fm
import platform

# OS別に日本語フォントを設定
if platform.system() == 'Darwin':  # macOS
    plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro', 'Yu Gothic', 'Meirio']
elif platform.system() == 'Windows':  # Windows
    # Windowsで利用可能な日本語フォント
    plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'MS Gothic', 'MS PGothic', 'Meiryo', 'Meiryo UI', 'DejaVu Sans']
else:  # Linux
    plt.rcParams['font.sans-serif'] = ['Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP', 'DejaVu Sans']

plt.rcParams['axes.unicode_minus'] = False  # マイナス記号の文字化け対策

# タイムアウト設定
EVALUATION_TIMEOUT = 20  # 20秒（FEM解析は時間がかかる）

# CSV設定
CSV_FILE = "pso_optimization_log.csv"
# テキストログファイル設定
LOG_FILE = "pso_progress.txt"
# 設定ファイル
SETTINGS_FILE = "pso_settings.csv"

# リアルタイムデータ共有用ファイル
REALTIME_DATA_FILE = "pso_realtime_data.json"

# 実行開始時刻を記録
start_time = time.time()

print("🚀 粒子群最適化アルゴリズムによる建築設計最適化開始")
print(f"⏰ 開始時刻: {time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(start_time))}")
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
    writer.writerow([
        "iteration", "particle", "fitness", "cost", "safety",
        "co2", "comfort", "constructability",
        "material_columns", "material_floor1", "material_floor2",
        "material_roof", "material_walls", "material_balcony"
    ])

# ---------- テキストログファイルの初期化 ----------
with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("PSO最適化進捗ログ\n")
    f.write(f"開始時刻: {time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(start_time))}\n")
    f.write(f"粒子数: {N_PARTICLES}, 反復回数: {MAX_ITER}\n")
    f.write("-" * 140 + "\n")
    f.write("反復\tgbest値\tpbest平均\tpbest標準偏差\t安全率\t建設コスト[円/m²]\tCO2排出量[kg-CO2/m²]\t快適性スコア\t施工性スコア\n")
    f.write("-" * 140 + "\n")

# ---------- 設定パラメータをCSVに出力 ----------
lower_bounds, upper_bounds = get_bounds()

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
    writer.writerow(["評価タイムアウト(秒)", EVALUATION_TIMEOUT])
    writer.writerow(["乱数シード", base_seed])
    writer.writerow([])
    
    # 設計変数の範囲
    writer.writerow(["設計変数の範囲"])
    writer.writerow(["変数名", "最小値", "最大値", "単位"])
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
        writer.writerow([name, lower_bounds[i], upper_bounds[i], unit])
    
    writer.writerow([])
    
    # 材料パラメータ説明
    writer.writerow(["材料パラメータ"])
    writer.writerow(["部位", "最適化対象", "変換ルール"])
    writer.writerow(["柱", "はい", "連続値 < 0.5 → コンクリート、≥ 0.5 → 木材"])
    writer.writerow(["1階床", "はい", "連続値 < 0.5 → コンクリート、≥ 0.5 → 木材"])
    writer.writerow(["2階床", "はい", "連続値 < 0.5 → コンクリート、≥ 0.5 → 木材"])
    writer.writerow(["屋根", "はい", "連続値 < 0.5 → コンクリート、≥ 0.5 → 木材"])
    writer.writerow(["外壁", "はい", "連続値 < 0.5 → コンクリート、≥ 0.5 → 木材"])
    writer.writerow(["バルコニー", "はい", "連続値 < 0.5 → コンクリート、≥ 0.5 → 木材"])
    
    writer.writerow([])
    writer.writerow([f"実行開始時刻: {time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(start_time))})"])

# 表形式で設定内容をコンソール出力
print("\n材料パラメータ（最適化対象）")
print("部位\t範囲\t変換ルール")
print("柱\t[0.0, 1.0]\t< 0.5 → コンクリート、≥ 0.5 → 木材")
print("1階床\t[0.0, 1.0]\t< 0.5 → コンクリート、≥ 0.5 → 木材")
print("2階床\t[0.0, 1.0]\t< 0.5 → コンクリート、≥ 0.5 → 木材")
print("屋根\t[0.0, 1.0]\t< 0.5 → コンクリート、≥ 0.5 → 木材")
print("外壁\t[0.0, 1.0]\t< 0.5 → コンクリート、≥ 0.5 → 木材")
print("バルコニー\t[0.0, 1.0]\t< 0.5 → コンクリート、≥ 0.5 → 木材")

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
        'progress': (iteration / MAX_ITER) * 100,
        'elapsed_time': time.time() - start_time
    }
    
    with open(REALTIME_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

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
            design["material_columns"], design["material_floor1"],
            design["material_floor2"], design["material_roof"],
            design["material_walls"], design["material_balcony"]
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

# リアルタイムデータ保存（初期世代）
best_particle = min(swarm, key=lambda p: p.fitness)
save_realtime_data(0, gbest_fitness, swarm, best_particle)

# ---------- PSO反復ループ ----------
history = []
all_positions = []  # 全世代の全粒子位置を記録

import statistics

for iter_num in range(MAX_ITER):
    print(f"\n🔄 反復 {iter_num+1}/{MAX_ITER} 開始")
    
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
                iter_num+1, idx+1, particle.fitness, particle.cost, particle.safety,
                particle.co2, particle.comfort, particle.constructability,
                design["material_columns"], design["material_floor1"],
                design["material_floor2"], design["material_roof"],
                design["material_walls"], design["material_balcony"]
            ])
        
        # 全粒子位置の記録
        all_positions.append({
            'iteration': iter_num+1,
            'particle': idx+1,
            'safety': particle.safety,
            'cost': particle.cost,
            'co2': particle.co2
        })
    
    # 履歴に記録
    best_particle = min(swarm, key=lambda p: p.fitness)
    history.append({
        'iteration': iter_num+1,
        'fitness': gbest_fitness,
        'cost': best_particle.cost,
        'safety': best_particle.safety,
        'co2': best_particle.co2
    })
    
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
    print(f"反復 {iter_num+1}/{MAX_ITER} 進捗サマリ")
    print(f"{'='*100}")
    print("反復\tgbest値\tpbest平均\tpbest標準偏差\t安全率\t建設コスト\tCO2排出量\t快適性スコア\t施工性スコア")
    print(f"{iter_num+1}\t{gbest_fitness:.4e}\t{pbest_mean:.4e}\t{pbest_std:.4e}\t{safety:.3f}\t{cost:.2f}\t{co2:.2f}\t{comfort:.3f}\t{constructability:.3f}")

    # テキストログ追記
    with open(LOG_FILE, "a", encoding="utf-8") as f_log:
        f_log.write(f"{iter_num+1}\t{gbest_fitness:.4e}\t{pbest_mean:.4e}\t{pbest_std:.4e}\t{safety:.3f}\t{cost:.2f}\t{co2:.2f}\t{comfort:.3f}\t{constructability:.3f}\n")
    
    # リアルタイムデータ保存
    save_realtime_data(iter_num+1, gbest_fitness, swarm, best_particle)

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
plt.savefig('pso_convergence.png', dpi=150)
plt.close()

# ---------- pbestの散布図（安全率 vs 建設コスト） ----------
print("\n📊 pbestの散布図を生成中...")
plt.figure(figsize=(8, 6))

# 全粒子のpbestを収集
pbest_safety = []
pbest_cost = []
for particle in swarm:
    # pbest位置での評価値を取得するため、再評価
    temp_position = particle.position
    particle.position = particle.pbest_position
    try:
        dv = _vector_to_design(particle.position)
        res = _evaluate_once(dv)
        if res['status'] == 'Success':
            pbest_safety.append(res["safety"]["overall_safety_factor"])
            pbest_cost.append(res["economic"]["cost_per_sqm"])
    except:
        # エラーの場合は粒子の保存値を使用
        if hasattr(particle, 'pbest_fitness') and particle.pbest_fitness < float('inf'):
            pbest_safety.append(particle.safety)
            pbest_cost.append(particle.cost)
    finally:
        particle.position = temp_position

# 散布図の作成
if pbest_safety and pbest_cost:
    plt.scatter(pbest_safety, pbest_cost, alpha=0.6, s=50)
    plt.xlabel('安全率')
    plt.ylabel('建設コスト (円/m²)')
    plt.title('PSO探索で得られた個人最良解（pbest）の分布')
    plt.grid(True, alpha=0.3)
    
    # 安全率2.0の基準線
    plt.axvline(x=2.0, color='r', linestyle='--', alpha=0.5, label='安全率2.0（推奨値）')
    
    # 軸の範囲設定
    plt.xlim(0, max(7, max(pbest_safety) * 1.1))
    plt.ylim(min(pbest_cost) * 0.9, max(pbest_cost) * 1.1)
    
    plt.legend()
    plt.tight_layout()
    plt.savefig('pso_pbest_safety_vs_cost.png', dpi=150)
    plt.close()
    print("✅ pbestの散布図を pso_pbest_safety_vs_cost.png に保存しました")
else:
    print("⚠️ pbest散布図の生成に必要なデータが不足しています")

# ---------- 全世代の全粒子位置の散布図 ----------
print("\n📍 全世代の粒子位置の散布図を生成中...")
if all_positions:
    plt.figure(figsize=(10, 8))
    
    # 世代ごとに色を変えるためのカラーマップ
    import matplotlib.cm as cm
    colors = cm.rainbow(np.linspace(0, 1, MAX_ITER + 1))
    
    # 初期世代の粒子位置も含める
    for particle in swarm:
        if particle.safety > 0 and particle.cost < float('inf'):
            plt.scatter(particle.safety, particle.cost, c=[colors[0]], s=30, alpha=0.6)
    
    # 各世代の粒子位置をプロット
    for iter_num in range(1, MAX_ITER + 1):
        iter_positions = [pos for pos in all_positions if pos['iteration'] == iter_num]
        if iter_positions:
            safety_vals = [pos['safety'] for pos in iter_positions]
            cost_vals = [pos['cost'] for pos in iter_positions]
            plt.scatter(safety_vals, cost_vals, c=[colors[iter_num]],
                       s=30, alpha=0.6, label=f'世代{iter_num}')
    
    plt.xlabel('安全率')
    plt.ylabel('建設コスト (円/m²)')
    plt.title('PSO探索過程：全世代の粒子位置')
    plt.grid(True, alpha=0.3)
    
    # 安全率2.0の基準線
    plt.axvline(x=2.0, color='r', linestyle='--', alpha=0.5, label='安全率2.0（推奨値）')
    
    # 軸の範囲設定
    all_safety = [pos['safety'] for pos in all_positions if pos['safety'] > 0]
    all_cost = [pos['cost'] for pos in all_positions if pos['cost'] < float('inf')]
    if all_safety and all_cost:
        plt.xlim(0, max(7, max(all_safety) * 1.1))
        plt.ylim(min(all_cost) * 0.9, max(all_cost) * 1.1)
    
    # 凡例を右外に配置（世代数が多い場合）
    if MAX_ITER > 10:
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
    else:
        plt.legend(fontsize=8)
    
    plt.tight_layout()
    plt.savefig('pso_all_positions_safety_vs_cost.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✅ 全世代の粒子位置散布図を pso_all_positions_safety_vs_cost.png に保存しました")
    print(f"📊 記録されたデータ点数: {len(all_positions)}点")
else:
    print("⚠️ 粒子位置散布図の生成に必要なデータが不足しています")

print("✅ 収束グラフを pso_convergence.png に保存しました")
print("\n💾 詳細なログは pso_optimization_log.csv を確認してください")
print("📝 進捗ログは pso_progress.txt を確認してください")
print("⚙️ 実行時の設定は pso_settings.csv を確認してください")
print("📈 生成されたグラフ:")
print("  - pso_convergence.png: 収束曲線")
print("  - pso_pbest_safety_vs_cost.png: 個人最良解(pbest)の分布")
print("  - pso_all_positions_safety_vs_cost.png: 全世代の粒子位置")

# 最終リアルタイムデータを削除（完了フラグとして）
if os.path.exists(REALTIME_DATA_FILE):
    os.remove(REALTIME_DATA_FILE)
    print("\n✅ リアルタイムデータファイルを削除（最適化完了）")

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
