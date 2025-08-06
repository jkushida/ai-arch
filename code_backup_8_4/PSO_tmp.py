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
- 15粒子が10ステップにわたり設計空間を探索
- 形状15変数 + 材料6変数 = 21次元の最適化
- 離散値（材料選択）も連続PSOで最適化
"""

# =============================================================================
# ★★★ 学生の皆さんへ：このセクションを主に編集します ★★★
# =============================================================================

# 1. PSOパラメータ設定
# -----------------------------------------------------------------------------
N_PARTICLES = 15  # 粒子数：解候補の数。多いほど多様な解を探せるが計算時間が増える。
MAX_ITER = 10     # 反復回数：探索の世代数。多いほど良い解に収束しやすいが時間がかかる。
W = 0.7           # 慣性重み：現在の速度をどれだけ維持するか。大きいと広範囲、小さいと局所的に探索。
C1 = 1.5          # 個人的最良解への加速係数：自身の過去最良解にどれだけ引かれるか。
C2 = 1.5          # 全体の最良解への加速係数：群れ全体の最良解にどれだけ引かれるか。
V_MAX = 0.2       # 最大速度（探索範囲に対する割合）：粒子の移動速度の上限。


# 2. 設計変数の境界値（探索範囲）
# -----------------------------------------------------------------------------
PARAM_RANGES = {
    # 建物寸法
    "Lx": (8.0, 12.0),          # 建物幅 (m)
    "Ly": (8.0, 12.0),          # 建物奥行 (m)
    "H1": (2.6, 3.5),           # 1階高さ (m)
    "H2": (2.6, 3.2),           # 2階高さ (m)
    
    # 構造部材寸法
    "tf": (350, 600),           # 床スラブ厚 (mm)
    "tr": (350, 600),           # 屋根スラブ厚 (mm)
    "bc": (400, 1000),          # 柱幅 (mm)
    "hc": (400, 1000),          # 柱高さ (mm)
    "tw_ext": (300, 500),       # 外壁厚 (mm)
    
    # その他の設計パラメータ
    "wall_tilt_angle": (-30.0, 30.0),  # 壁傾斜角 (度)
    "window_ratio_2f": (0.1, 0.9),     # 2階窓比率
    "roof_morph": (0.0, 1.0),          # 屋根形態 (0:平坦, 1:かまぼこ)
    "roof_shift": (-0.5, 0.5),         # 屋根シフト
    "balcony_depth": (1.0, 3.5),       # バルコニー奥行 (m)
    
    # 材料パラメータ (0.0-1.0の連続値 → 0.5を閾値に離散化)
    "material_columns": (0.0, 1.0),      # 柱材料 (0:コンクリート, 1:木材)
    "material_floor1": (0.0, 1.0),       # 1階床材料
    "material_floor2": (0.0, 1.0),       # 2階床材料
    "material_roof": (0.0, 1.0),         # 屋根材料
    "material_walls": (0.0, 1.0),        # 外壁材料
    "material_balcony": (0.0, 1.0),      # バルコニー材料
}


# 3. 目的関数の定義（評価基準）
# -----------------------------------------------------------------------------
# この関数を編集して、AIに「どのような建物を良いとするか」を教えます。
# PSOアルゴリズムは、この関数の戻り値（fitness）が最も小さくなる設計を探します。

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
        適応度（この値が最小になるように最適化される）
    """
    # ===== ここからカスタマイズしてください =====
    
    # --- 目標設定の例 ---
    # 例1）コスト最小化（デフォルト）
    # fitness = cost
    
    # 例2）CO2排出量最小化（環境重視）
    # fitness = co2
    
    # 例3）快適性最大化（最大化したい場合はマイナスの値にする）
    # fitness = -comfort
    
    # 例4）施工性最大化
    # fitness = -constructability
    
    # 例5）多目的最適化（重み付け和）
    # w1, w2, w3 = 0.5, 0.3, 0.2  # 重み係数
    # fitness = w1 * (cost/100000) + w2 * (co2/1000) + w3 * (-comfort/10)
    
    # 現在の目的：コスト最小化
    fitness = cost
    
    # --- 制約条件 ---
    # 安全率の制約（これは変更しないことを推奨します）
    SAFETY_THRESHOLD = 2.0      # 安全率の最小値
    PENALTY_COEFFICIENT = 100000  # 違反した場合のペナルティの重み
    
    if safety < SAFETY_THRESHOLD:
        penalty = (SAFETY_THRESHOLD - safety) * PENALTY_COEFFICIENT
        fitness += penalty
    
    # --- 追加の制約条件の例（必要に応じてコメントを外して使う） ---
    # if comfort < 5.0:  # 快適性5.0以上を必須とする
    #     fitness += (5.0 - comfort) * 10000
    
    # if co2 > 1000:  # CO2排出量1000以下を必須とする
    #     fitness += (co2 - 1000) * 100
    
    # if constructability < 6.0:  # 施工性6.0以上を必須とする
    #     fitness += (6.0 - constructability) * 5000
    
    return fitness

# =============================================================================
# ★★★ ここから下は、通常は編集する必要はありません ★★★
# =============================================================================

import numpy as np
import csv
import random
import time
import signal
import sys
import os
import gc
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
import statistics

try:
    from generate_building_fem_analyze import evaluate_building_from_params
except Exception as e:
    print(f"❌ 評価関数のインポートエラー: {e}")
    sys.exit(1)

# 最後の更新時刻を記録（1分ごとの更新用）
update_time_tracker = [0]

# 開始時刻をグローバル変数として初期化
start_time = None

# 日本語フォントの設定
if platform.system() == 'Darwin':  # macOS
    plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro', 'Yu Gothic', 'Meirio']
elif platform.system() == 'Windows':  # Windows
    plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'MS Gothic', 'MS PGothic', 'Meiryo', 'Meiryo UI', 'DejaVu Sans']
else:  # Linux
    plt.rcParams['font.sans-serif'] = ['Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# タイムアウト設定
EVALUATION_TIMEOUT = 20

# 出力ディレクトリの設定
OUTPUT_DIR = "pso_output"
CSV_DIR = os.path.join(OUTPUT_DIR, "csv")
IMAGE_DIR = os.path.join(OUTPUT_DIR, "images")
FCSTD_DIR = os.path.join(OUTPUT_DIR, "fcstd")
os.makedirs(CSV_DIR, exist_ok=True)
os.makedirs(IMAGE_DIR, exist_ok=True)
os.makedirs(FCSTD_DIR, exist_ok=True)

# ファイルパス設定
CSV_FILE = os.path.join(CSV_DIR, "pso_particle_positions.csv")
PBEST_CSV_FILE = os.path.join(CSV_DIR, "pso_pbest_positions.csv")
GBEST_HISTORY_CSV_FILE = os.path.join(CSV_DIR, "pso_gbest_history.csv")
LOG_FILE = os.path.join(CSV_DIR, "pso_progress.txt")
SETTINGS_FILE = os.path.join(CSV_DIR, "pso_settings.csv")
REALTIME_DATA_FILE = "pso_realtime_data.json"

print("🚀 粒子群最適化アルゴリズムによる建築設計最適化開始")
print(f"📊 粒子数: {N_PARTICLES}, 反復回数: {MAX_ITER}")
print(f"🔧 PSO パラメータ: W={W}, C1={C1}, C2={C2}")
print(f"\n📝 リアルタイムデータ: {REALTIME_DATA_FILE}")
print("💡 別ターミナルで monitor_pso.py を実行するとリアルタイム監視できます")

# 乱数シード設定
base_seed = 123
rng = random.Random(base_seed)
np.random.seed(base_seed)

# パラメータ名のリスト（順序を保持）
PARAM_NAMES = list(PARAM_RANGES.keys())

def get_bounds():
    """設計変数の上下限"""
    lower = [PARAM_RANGES[param][0] for param in PARAM_NAMES]
    upper = [PARAM_RANGES[param][1] for param in PARAM_NAMES]
    return np.array(lower), np.array(upper)

def apply_reflection_boundary(position, velocity, lower_bound, upper_bound):
    for i in range(len(position)):
        if position[i] < lower_bound[i]:
            position[i] = lower_bound[i] + (lower_bound[i] - position[i])
            velocity[i] *= -1
        elif position[i] > upper_bound[i]:
            position[i] = upper_bound[i] - (position[i] - upper_bound[i])
            velocity[i] *= -1
    return np.clip(position, lower_bound, upper_bound), velocity

def _cleanup_freecad_memory():
    try:
        import FreeCAD as App
        for doc in list(App.listDocuments().values()):
            App.closeDocument(doc.Name)
    except Exception:
        pass
    gc.collect()

class TimeoutError(Exception):
    pass

def _timeout_handler(signum, frame):
    raise TimeoutError("evaluation timeout")

_HAS_SIGALRM = hasattr(signal, "SIGALRM")

def _evaluate_once(design_vars: dict, timeout_s: int = EVALUATION_TIMEOUT, save_fcstd=False, fcstd_path=None):
    if _HAS_SIGALRM:
        try:
            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(timeout_s)
            res = evaluate_building_from_params(design_vars, save_fcstd=save_fcstd, fcstd_path=fcstd_path)
            signal.alarm(0)
            return res
        except TimeoutError:
            raise TimeoutError("evaluation timeout")
        finally:
            if _HAS_SIGALRM:
                signal.alarm(0)
            _cleanup_freecad_memory()
    else:
        try:
            return evaluate_building_from_params(design_vars, save_fcstd=save_fcstd, fcstd_path=fcstd_path)
        finally:
            _cleanup_freecad_memory()

def _vector_to_design(vec):
    dv = {}
    for k, v in zip(PARAM_NAMES, vec):
        if k in ["tf", "tr", "bc", "hc", "tw_ext"]:
            dv[k] = int(round(v))
        elif k.startswith("material_"):
            dv[k] = 1 if v >= 0.5 else 0
        else:
            dv[k] = float(v)
    return dv

class Particle:
    def __init__(self, bounds):
        self.bound_low, self.bound_up = bounds
        self.position = np.array([low + (up - low) * rng.random() for low, up in zip(self.bound_low, self.bound_up)])
        self.velocity = np.array([(up - low) * (rng.random() - 0.5) * 0.1 for low, up in zip(self.bound_low, self.bound_up)])
        self.pbest_position = np.copy(self.position)
        self.pbest_fitness = float("inf")
        self.fitness = float("inf")
        self.safety = 0.0
        self.cost = float("inf")
        self.co2 = float("inf")
        self.comfort = 0.0
        self.constructability = 0.0

def evaluate_particle(particle: Particle, idx: int = None):
    try:
        dv = _vector_to_design(particle.position)
        res = _evaluate_once(dv)
        if res['status'] != 'Success':
            raise Exception(f"評価失敗: {res['message']}")
        
        particle.cost = res["economic"]["cost_per_sqm"]
        particle.safety = res["safety"]["overall_safety_factor"]
        particle.co2 = res["environmental"]["co2_per_sqm"]
        particle.comfort = res["comfort"]["comfort_score"]
        particle.constructability = res["constructability"]["constructability_score"]
        
        particle.fitness = calculate_fitness(particle.cost, particle.safety, particle.co2, particle.comfort, particle.constructability)
        
        if particle.fitness < particle.pbest_fitness:
            particle.pbest_fitness = particle.fitness
            particle.pbest_position = np.copy(particle.position)
        
        if idx is not None:
            print(f"  粒子 {idx+1}: cost={particle.cost:.0f}, safety={particle.safety:.2f}, CO2={particle.co2:.0f}, comfort={particle.comfort:.1f}")
        
    except Exception as e:
        if idx is not None:
            print(f"  ❌ 粒子 {idx+1} の評価失敗: {e}")
        particle.fitness = float("inf")


# ファイルヘッダー書き込み
with open(CSV_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["iteration", "particle", "fitness", "cost", "safety", "co2", "comfort", "constructability"] + PARAM_NAMES)

with open(PBEST_CSV_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["iteration", "particle", "pbest_fitness"] + [f"pbest_{name}" for name in PARAM_NAMES])

with open(GBEST_HISTORY_CSV_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["iteration", "gbest_fitness", "cost", "safety", "co2", "comfort", "constructability"] + PARAM_NAMES)

with open(LOG_FILE, "w", encoding="utf-8") as f:
    f.write("PSO最適化進捗ログ\n")

# 設定ファイル書き込み
lower_bounds, upper_bounds = get_bounds()
PARAM_DESCRIPTIONS = {
    "Lx": "建物幅", "Ly": "建物奥行", "H1": "1階高さ", "H2": "2階高さ",
    "tf": "床スラブ厚", "tr": "屋根スラブ厚", "bc": "柱幅", "hc": "柱高さ", "tw_ext": "外壁厚",
    "wall_tilt_angle": "壁傾斜角", "window_ratio_2f": "2階窓比率", "roof_morph": "屋根形態",
    "roof_shift": "屋根シフト", "balcony_depth": "バルコニー奥行", "material_columns": "柱材料",
    "material_floor1": "1階床材料", "material_floor2": "2階床材料", "material_roof": "屋根材料",
    "material_walls": "外壁材料", "material_balcony": "バルコニー材料"
}
with open(SETTINGS_FILE, "w", newline="", encoding='utf-8-sig') as f:
    writer = csv.writer(f)
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
    writer.writerow(["設計変数の範囲"])
    writer.writerow(["変数名", "説明", "最小値", "最大値", "単位"])
    for i, name in enumerate(PARAM_NAMES):
        unit = "m" if name in ["Lx", "Ly", "H1", "H2", "balcony_depth"] else "mm" if name in ["tf", "tr", "bc", "hc", "tw_ext"] else "度" if name == "wall_tilt_angle" else "0:コンクリート, 1:木材" if name.startswith("material_") else "-"
        writer.writerow([name, PARAM_DESCRIPTIONS.get(name, ""), lower_bounds[i], upper_bounds[i], unit])


def _initialize_plots():
    print("\n🖼️  Initializing plots...")
    plot_configs = [
        {'y_col': 'cost', 'ylabel': '建設コスト (円/m²)', 'title': '建設コスト vs 安全率'},
        {'y_col': 'co2', 'ylabel': 'CO2排出量 (kg-CO2/m²)', 'title': 'CO2排出量 vs 安全率'},
        {'y_col': 'comfort', 'ylabel': '快適性スコア', 'title': '快適性スコア vs 安全率'},
        {'y_col': 'constructability', 'ylabel': '施工性スコア', 'title': '施工性スコア vs 安全率'}
    ]
    for config in plot_configs:
        plt.figure(figsize=(8, 6))
        plt.xlabel('安全率')
        plt.ylabel(config['ylabel'])
        plt.title(config['title'])
        plt.grid(True, alpha=0.3)
        plt.axvline(x=2.0, color='r', linestyle='--', alpha=0.5, label='安全率2.0（推奨値）')
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(IMAGE_DIR, f'pso_all_positions_safety_vs_{config["y_col"]}.png'), dpi=200)
        plt.close()
    print("✅ All plots initialized.")

def _update_plots(all_positions_data, current_iteration, max_iterations):
    print(f"* Updating plots for iteration {current_iteration}")
    colors = cm.rainbow(np.linspace(0, 1, max_iterations + 1))
    plot_configs = [
        {'y_col': 'cost', 'ylabel': '建設コスト (円/m²)', 'title': '建設コスト vs 安全率'},
        {'y_col': 'co2', 'ylabel': 'CO2排出量 (kg-CO2/m²)', 'title': 'CO2排出量 vs 安全率'},
        {'y_col': 'comfort', 'ylabel': '快適性スコア', 'title': '快適性スコア vs 安全率'},
        {'y_col': 'constructability', 'ylabel': '施工性スコア', 'title': '施工性スコア vs 安全率'}
    ]
    for config in plot_configs:
        plt.figure(figsize=(8, 6))
        for i in range(current_iteration + 1):
            iter_data = [p for p in all_positions_data if p['iteration'] == i]
            if iter_data:
                safety_vals = [p['safety'] for p in iter_data if p['safety'] > 0]
                y_vals = [p[config['y_col']] for p in iter_data if p['safety'] > 0]
                if safety_vals:
                    plt.scatter(safety_vals, y_vals, c=[colors[i]], s=30, alpha=0.6, label=f'ステップ{i}')
        plt.xlabel('安全率', fontsize=12)
        plt.ylabel(config['ylabel'], fontsize=12)
        plt.title(f'{config["title"]} (ステップ {current_iteration}/{max_iterations - 1})', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.axvline(x=2.0, color='r', linestyle='--', alpha=0.5, label='安全率2.0（推奨値）')
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=10)
        plt.tight_layout()
        plt.savefig(os.path.join(IMAGE_DIR, f'pso_all_positions_safety_vs_{config["y_col"]}.png'), dpi=200)
        plt.close()

def save_realtime_data(iteration, gbest_fitness, particles, best_particle):
    data = {
        'timestamp': time.time(), 'iteration': iteration, 'max_iteration': MAX_ITER,
        'n_particles': N_PARTICLES, 'gbest_fitness': gbest_fitness,
        'best_particle': {'safety': best_particle.safety, 'cost': best_particle.cost, 'co2': best_particle.co2, 'comfort': best_particle.comfort, 'constructability': best_particle.constructability},
        'particles': [{'position': p.position.tolist(), 'fitness': p.fitness, 'safety': p.safety, 'cost': p.cost} for p in particles],
        'progress': (iteration / MAX_ITER) * 100, 'elapsed_time': time.time() - start_time
    }
    with open(REALTIME_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# Main execution block
if __name__ == "__main__":
    if os.path.exists(REALTIME_DATA_FILE):
        os.remove(REALTIME_DATA_FILE)
    
    _initialize_plots()
    start_time = time.time()
    
    initial_data = {
        'timestamp': start_time, 'iteration': 0, 'max_iteration': MAX_ITER, 'n_particles': N_PARTICLES,
        'gbest_fitness': float("inf"), 'best_particle': {},
        'particles': [], 'progress': 0.0, 'elapsed_time': 0.0, 'status': 'initializing'
    }
    with open(REALTIME_DATA_FILE, 'w') as f:
        json.dump(initial_data, f, indent=2)

    bounds = get_bounds()
    swarm = [Particle(bounds) for _ in range(N_PARTICLES)]
    gbest_position = None
    gbest_fitness = float("inf")
    all_positions_history = []

    print("\n📊 初期粒子群の生成と評価...")
    for idx, p in enumerate(swarm):
        evaluate_particle(p, idx)
        if p.fitness < gbest_fitness:
            gbest_fitness = p.fitness
            gbest_position = np.copy(p.position)
        all_positions_history.append({'iteration': 0, 'particle': idx, **p.__dict__})

    best_particle_initial = min(swarm, key=lambda p: p.fitness)
    save_realtime_data(0, gbest_fitness, swarm, best_particle_initial)
    with open(GBEST_HISTORY_CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        row = [0, gbest_fitness, best_particle_initial.cost, best_particle_initial.safety, best_particle_initial.co2, best_particle_initial.comfort, best_particle_initial.constructability] + _vector_to_design(gbest_position).values()
        writer.writerow(row)

    _update_plots(all_positions_history, 0, MAX_ITER)

    for iter_num in range(1, MAX_ITER):
        print(f"\n🔄 反復 {iter_num}/{MAX_ITER} 開始")
        for idx, p in enumerate(swarm):
            r1, r2 = np.random.rand(2)
            cognitive = C1 * r1 * (p.pbest_position - p.position)
            social = C2 * r2 * (gbest_position - p.position)
            p.velocity = W * p.velocity + cognitive + social
            p.velocity = np.clip(p.velocity, -V_MAX * (bounds[1] - bounds[0]), V_MAX * (bounds[1] - bounds[0]))
            p.position += p.velocity
            p.position, p.velocity = apply_reflection_boundary(p.position, p.velocity, bounds[0], bounds[1])
            evaluate_particle(p, idx)
            if p.fitness < gbest_fitness:
                gbest_fitness = p.fitness
                gbest_position = np.copy(p.position)
            all_positions_history.append({'iteration': iter_num, 'particle': idx, **p.__dict__})

        best_particle_iter = min(swarm, key=lambda p: p.fitness)
        save_realtime_data(iter_num, gbest_fitness, swarm, best_particle_iter)
        with open(GBEST_HISTORY_CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            row = [iter_num, gbest_fitness, best_particle_iter.cost, best_particle_iter.safety, best_particle_iter.co2, best_particle_iter.comfort, best_particle_iter.constructability] + _vector_to_design(gbest_position).values()
            writer.writerow(row)
        _update_plots(all_positions_history, iter_num, MAX_ITER)

    print("\n🏁 最適化完了！")
    best_particle_final = min(swarm, key=lambda p: p.fitness)
    best_design_final = _vector_to_design(gbest_position)
    print(f"🏆 最終的な最良解: fitness={gbest_fitness:.2f}")
    for k, v in best_design_final.items():
        print(f"  {k} = {v}")

    # 最良モデルのFCStdファイルを保存
    print("\n💾 最良モデルの3Dモデル(.FCStd)を保存中...")
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        fcstd_filename = f"pso_best_solution_{timestamp}.FCStd"
        fcstd_path = os.path.join(FCSTD_DIR, fcstd_filename)
        
        # 再評価して保存
        evaluate_building_from_params(best_design_final, save_fcstd=True, fcstd_path=fcstd_path)
        print(f"✅ 3Dモデルを保存しました: {fcstd_path}")
    except Exception as e:
        print(f"❌ 3Dモデルの保存中にエラーが発生しました: {e}")

    if os.path.exists(REALTIME_DATA_FILE):
        os.remove(REALTIME_DATA_FILE)