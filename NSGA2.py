#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NSGA2_optimization.py
NSGA-II（Non-dominated Sorting Genetic Algorithm II）による建築設計の多目的最適化
目的1: 安全性の最大化（安全率）
目的2: コストの最小化
"""

import numpy as np
import csv
import random
import time
import signal
import sys
import os
import gc
from typing import List, Dict, Tuple

# ---------- オフスクリーン backend を指定 ----------
import matplotlib
matplotlib.use("Agg")  # X サーバ不要で PNG 保存
import matplotlib.pyplot as plt
# 日本語フォントの設定
plt.rcParams['font.family'] = 'Hiragino Sans'
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro', 'Yu Gothic', 'Meirio', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']
plt.rcParams['axes.unicode_minus'] = False  # マイナス記号の文字化け対策

# NSGA-IIパラメータ
POPULATION_SIZE = 50  # 個体群サイズ
N_GENERATIONS = 100    # 世代数
CROSSOVER_PROB = 0.9  # 交叉確率
MUTATION_PROB = 0.1   # 突然変異確率
TOURNAMENT_SIZE = 2   # トーナメントサイズ

# タイムアウト設定
EVALUATION_TIMEOUT = 20  # 20秒（FEM解析は時間がかかる）

# CSV設定
CSV_FILE = "nsga2_optimization_log.csv"
PARETO_FILE = "nsga2_pareto_solutions.csv"
# テキストログファイル設定
LOG_FILE = "nsga2_progress.txt"
# 設定ファイル
SETTINGS_FILE = "nsga2_settings.csv"

# 実行開始時刻を記録
start_time = time.time()

print("🚀 NSGA-IIによる建築設計の多目的最適化開始")
print(f"⏰ 開始時刻: {time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(start_time))}")
print(f"📊 個体群サイズ: {POPULATION_SIZE}, 世代数: {N_GENERATIONS}")
print(f"🎯 目的: 1) 安全性最大化, 2) コスト最小化")

# 乱数シード設定
base_seed = 123
rng = random.Random(base_seed)
np.random.seed(base_seed)

# ---------- 評価関数のインポート ----------
try:
    from generate_building_fem_analyze import evaluate_building_from_params
    print("✅ 評価関数のインポート成功")
except Exception as e:
    print(f"❌ インポートエラー: {e}")
    sys.exit(1)

# ---------- 設計変数の境界値 ----------
# パラメータ範囲の定義
PARAM_RANGES = {
    # 建物寸法
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
    
    # その他の設計パラメータ
    "wall_tilt_angle": (-30.0, 30.0),  # 壁傾斜角: -30〜30度
    "window_ratio_2f": (0.1, 0.7),     # 2階窓比率: 0.1〜0.7
    "roof_morph": (0.1, 0.9),          # 屋根形態: 0.1〜0.9
    "roof_shift": (-0.5, 0.5),         # 屋根シフト: -0.5〜0.5
    "balcony_depth": (1.0, 3.5),       # バルコニー奥行: 1.0〜3.5m
}

# パラメータ名のリスト（順序を保持）
PARAM_NAMES = ["Lx", "Ly", "H1", "H2", "tf", "tr", "bc", "hc", "tw_ext",
               "wall_tilt_angle", "window_ratio_2f", "roof_morph", "roof_shift", "balcony_depth"]

# バイナリパラメータ範囲の定義（材料選択）
BINARY_PARAMS = {
    "material_columns": (0, 1),      # 0:コンクリート, 1:木材
    "material_floor1": (0, 1),       # 0:コンクリート, 1:木材
    "material_floor2": (0, 1),       # 0:コンクリート, 1:木材
    "material_roof": (0, 1),         # 0:コンクリート, 1:木材
    "material_walls": (0, 1),        # 0:コンクリート, 1:木材
    "material_balcony": (0, 1),      # 0:コンクリート, 1:木材
}

BINARY_PARAM_NAMES = ["material_columns", "material_floor1", "material_floor2", 
                      "material_roof", "material_walls", "material_balcony"]

def get_bounds():
    """設計変数の上下限"""
    lower = []
    upper = []
    # 連続パラメータ
    for param in PARAM_NAMES:
        lower.append(PARAM_RANGES[param][0])
        upper.append(PARAM_RANGES[param][1])
    # バイナリパラメータ
    for param in BINARY_PARAM_NAMES:
        lower.append(BINARY_PARAMS[param][0])
        upper.append(BINARY_PARAMS[param][1])
    return np.array(lower), np.array(upper)

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
            signal.signal(signal.SIGALRM, _timeout_handler)
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
    """ベクトル形式から設計変数辞書へ変換"""
    dv = {}
    # 連続パラメータ
    for i, k in enumerate(PARAM_NAMES):
        v = vec[i]
        if k in ["tf", "tr", "bc", "hc", "tw_ext"]:
            dv[k] = int(round(v))
        else:
            dv[k] = float(v)
    
    # バイナリパラメータ（閾値0.5で0/1に変換）
    offset = len(PARAM_NAMES)
    for i, k in enumerate(BINARY_PARAM_NAMES):
        v = vec[offset + i]
        dv[k] = 1 if v >= 0.5 else 0
    
    return dv

# ---------- 個体クラス ----------
class Individual:
    def __init__(self, genes=None):
        self.lower_bound, self.upper_bound = get_bounds()
        
        if genes is None:
            # ランダムに初期化
            self.genes = np.array([
                low + (up - low) * rng.random() 
                for low, up in zip(self.lower_bound, self.upper_bound)
            ])
        else:
            self.genes = np.array(genes)
        
        # 目的関数値
        self.objectives = [float('inf'), float('inf')]  # [安全性（最大化）, コスト（最小化）]
        
        # その他の評価値
        self.co2 = float('inf')
        self.comfort = 0.0
        self.constructability = 0.0
        
        # NSGA-II用の属性
        self.rank = None  # パレートランク
        self.crowding_distance = 0.0  # 混雑距離
        self.domination_count = 0  # この個体を支配する個体数
        self.dominated_individuals = []  # この個体が支配する個体のリスト
        
    def evaluate(self, idx=None):
        """個体の評価"""
        try:
            dv = _vector_to_design(self.genes)
            res = _evaluate_once(dv)
            
            if res['status'] != 'Success':
                raise Exception(f"評価失敗: {res['message']}")
            
            # 目的関数値の設定
            # 目的1: 安全性（最大化） → 負値にして最小化問題に変換
            self.objectives[0] = -res["safety"]["overall_safety_factor"]
            # 目的2: コスト（最小化）
            self.objectives[1] = res["economic"]["cost_per_sqm"]
            
            # その他の評価値
            self.co2 = res["environmental"]["co2_per_sqm"]
            self.comfort = res["comfort"]["comfort_score"]
            self.constructability = res["constructability"]["constructability_score"]
            
            if idx is not None:
                print(f"  個体 {idx+1}: safety={-self.objectives[0]:.2f}, cost={self.objectives[1]:.0f}, "
                      f"CO2={self.co2:.0f}, comfort={self.comfort:.1f}")
            
        except Exception as e:
            if idx is not None:
                print(f"  ❌ 個体 {idx+1} の評価失敗: {e}")
            # 失敗時は最悪値を設定
            self.objectives[0] = 0.0  # 安全性0（負値にすると0）
            self.objectives[1] = float('inf')  # 無限大のコスト

# ---------- 非支配ソート ----------
def non_dominated_sort(population: List[Individual]) -> List[List[Individual]]:
    """非支配ソートを実行し、各ランクの個体リストを返す"""
    fronts = [[]]
    
    for p in population:
        p.domination_count = 0
        p.dominated_individuals = []
        
        for q in population:
            if p == q:
                continue
                
            # pがqを支配するかチェック
            if dominates(p, q):
                p.dominated_individuals.append(q)
            elif dominates(q, p):
                p.domination_count += 1
        
        if p.domination_count == 0:
            p.rank = 0
            fronts[0].append(p)
    
    i = 0
    while len(fronts[i]) > 0:
        next_front = []
        for p in fronts[i]:
            for q in p.dominated_individuals:
                q.domination_count -= 1
                if q.domination_count == 0:
                    q.rank = i + 1
                    next_front.append(q)
        fronts.append(next_front)
        i += 1
    
    return fronts[:-1]  # 最後の空リストを除く

def dominates(p: Individual, q: Individual) -> bool:
    """個体pが個体qを支配するかチェック"""
    better_in_any = False
    for i in range(len(p.objectives)):
        if p.objectives[i] > q.objectives[i]:  # 最小化問題
            return False
        elif p.objectives[i] < q.objectives[i]:
            better_in_any = True
    return better_in_any

# ---------- 混雑距離の計算 ----------
def calculate_crowding_distance(front: List[Individual]):
    """フロント内の各個体の混雑距離を計算"""
    n = len(front)
    if n <= 2:
        for ind in front:
            ind.crowding_distance = float('inf')
        return
    
    # 初期化
    for ind in front:
        ind.crowding_distance = 0.0
    
    # 各目的関数について
    for m in range(len(front[0].objectives)):
        # 目的関数mでソート
        front.sort(key=lambda x: x.objectives[m])
        
        # 境界の個体は無限大
        front[0].crowding_distance = float('inf')
        front[-1].crowding_distance = float('inf')
        
        # 目的関数の範囲
        obj_range = front[-1].objectives[m] - front[0].objectives[m]
        if obj_range == 0:
            continue
        
        # 中間の個体の混雑距離を計算
        for i in range(1, n-1):
            distance = (front[i+1].objectives[m] - front[i-1].objectives[m]) / obj_range
            front[i].crowding_distance += distance

# ---------- トーナメント選択 ----------
def tournament_selection(population: List[Individual], tournament_size: int = TOURNAMENT_SIZE) -> Individual:
    """トーナメント選択"""
    tournament = random.sample(population, tournament_size)
    
    # ランクが低い（良い）個体を選択
    tournament.sort(key=lambda x: (x.rank, -x.crowding_distance))
    return tournament[0]

# ---------- 交叉（SBX: Simulated Binary Crossover） ----------
def sbx_crossover(parent1: Individual, parent2: Individual, eta: float = 20.0) -> Tuple[Individual, Individual]:
    """SBX交叉"""
    child1_genes = np.copy(parent1.genes)
    child2_genes = np.copy(parent2.genes)
    
    for i in range(len(parent1.genes)):
        if rng.random() < 0.5:
            # SBX交叉を適用
            u = rng.random()
            
            if u <= 0.5:
                beta = (2 * u) ** (1 / (eta + 1))
            else:
                beta = (1 / (2 * (1 - u))) ** (1 / (eta + 1))
            
            child1_genes[i] = 0.5 * ((1 + beta) * parent1.genes[i] + (1 - beta) * parent2.genes[i])
            child2_genes[i] = 0.5 * ((1 - beta) * parent1.genes[i] + (1 + beta) * parent2.genes[i])
    
    # 境界内に収める
    lower_bound, upper_bound = get_bounds()
    child1_genes = np.clip(child1_genes, lower_bound, upper_bound)
    child2_genes = np.clip(child2_genes, lower_bound, upper_bound)
    
    return Individual(child1_genes), Individual(child2_genes)

# ---------- 突然変異（多項式突然変異） ----------
def polynomial_mutation(individual: Individual, eta: float = 20.0) -> Individual:
    """多項式突然変異"""
    mutated_genes = np.copy(individual.genes)
    lower_bound, upper_bound = get_bounds()
    
    for i in range(len(individual.genes)):
        if rng.random() < MUTATION_PROB:
            # バイナリパラメータの場合はビット反転
            if i >= len(PARAM_NAMES):
                mutated_genes[i] = 1 - mutated_genes[i]
            else:
                # 連続パラメータの場合は多項式突然変異
                u = rng.random()
                
                if u <= 0.5:
                    delta = (2 * u) ** (1 / (eta + 1)) - 1
                else:
                    delta = 1 - (2 * (1 - u)) ** (1 / (eta + 1))
                
                mutated_genes[i] = individual.genes[i] + delta * (upper_bound[i] - lower_bound[i])
                mutated_genes[i] = np.clip(mutated_genes[i], lower_bound[i], upper_bound[i])
    
    return Individual(mutated_genes)

# ---------- CSVヘッダー作成 ----------
with open(CSV_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "generation", "individual", "rank", "safety", "cost",
        "co2", "comfort", "constructability", "crowding_distance"
    ])

with open(PARETO_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    header = ["generation", "rank", "safety", "cost", "co2", "comfort", "constructability"] + PARAM_NAMES
    writer.writerow(header)

# ---------- テキストログファイルの初期化 ----------
with open(LOG_FILE, "w") as f:
    f.write("NSGA-II多目的最適化進捗ログ\n")
    f.write(f"開始時刻: {time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(start_time))}\n")
    f.write(f"個体群サイズ: {POPULATION_SIZE}, 世代数: {N_GENERATIONS}\n")
    f.write("-"*60 + "\n")
    f.write("世代\tパレート解数\t最良安全率\t最良コスト\n")
    f.write("-"*60 + "\n")

# ---------- 設定パラメータをCSVに出力 ----------
lower_bounds, upper_bounds = get_bounds()

with open(SETTINGS_FILE, "w", newline="", encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    # NSGA-IIパラメータ
    writer.writerow(["NSGA-II設定"])
    writer.writerow(["パラメータ", "値"])
    writer.writerow(["個体群サイズ", POPULATION_SIZE])
    writer.writerow(["世代数", N_GENERATIONS])
    writer.writerow(["交叉確率", CROSSOVER_PROB])
    writer.writerow(["突然変異確率", MUTATION_PROB])
    writer.writerow(["トーナメントサイズ", TOURNAMENT_SIZE])
    writer.writerow(["評価タイムアウト(秒)", EVALUATION_TIMEOUT])
    writer.writerow(["乱数シード", base_seed])
    writer.writerow([])
    
    # 設計変数の範囲
    writer.writerow(["設計変数の範囲"])
    writer.writerow(["変数名", "最小値", "最大値", "単位"])
    # 連続パラメータ
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
    
    # バイナリパラメータ
    offset = len(PARAM_NAMES)
    for i, name in enumerate(BINARY_PARAM_NAMES):
        writer.writerow([name, lower_bounds[offset + i], upper_bounds[offset + i], "0:コンクリート, 1:木材"])
    
    writer.writerow([])
    writer.writerow([f"実行開始時刻: {time.strftime('%Y/%m/%d %H:%M:%S', time.localtime(start_time))})"])

# ---------- 初期個体群の生成と評価 ----------
print("\n📊 初期個体群の生成と評価...")
population = []

for idx in range(POPULATION_SIZE):
    print(f"\n🧬 個体 {idx+1}/{POPULATION_SIZE}")
    individual = Individual()
    individual.evaluate(idx)
    population.append(individual)

# 非支配ソートと混雑距離の計算
fronts = non_dominated_sort(population)
for front in fronts:
    calculate_crowding_distance(front)

# 初期世代のログ記録
pareto_front = fronts[0]
best_safety = max(-ind.objectives[0] for ind in pareto_front)
best_cost = min(ind.objectives[1] for ind in pareto_front)

print(f"\n🏆 初期世代のパレート解数: {len(pareto_front)}")
print(f"  最良安全率: {best_safety:.2f}")
print(f"  最良コスト: {best_cost:.0f} 円/m²")

with open(LOG_FILE, "a") as f:
    f.write(f"0\t{len(pareto_front)}\t{best_safety:.2f}\t{best_cost:.0f}\n")

# CSV記録
for idx, ind in enumerate(population):
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            0, idx+1, ind.rank, -ind.objectives[0], ind.objectives[1],
            ind.co2, ind.comfort, ind.constructability, ind.crowding_distance
        ])

# ---------- 進化ループ ----------
all_pareto_fronts = []  # 各世代のパレートフロントを保存

for generation in range(1, N_GENERATIONS + 1):
    print(f"\n{'='*60}")
    print(f"世代 {generation}/{N_GENERATIONS}")
    print(f"{'='*60}")
    
    # 子個体群の生成
    offspring = []
    
    while len(offspring) < POPULATION_SIZE:
        # 親選択
        parent1 = tournament_selection(population)
        parent2 = tournament_selection(population)
        
        # 交叉
        if rng.random() < CROSSOVER_PROB:
            child1, child2 = sbx_crossover(parent1, parent2)
        else:
            child1 = Individual(parent1.genes)
            child2 = Individual(parent2.genes)
        
        # 突然変異
        child1 = polynomial_mutation(child1)
        child2 = polynomial_mutation(child2)
        
        offspring.extend([child1, child2])
    
    # 余分な個体を削除
    offspring = offspring[:POPULATION_SIZE]
    
    # 子個体群の評価
    print("\n📊 子個体群の評価...")
    for idx, child in enumerate(offspring):
        print(f"\n世代 {generation}/{N_GENERATIONS}  評価 {idx+1}/{POPULATION_SIZE}")
        child.evaluate(idx)
    
    # 親と子を結合
    combined_population = population + offspring
    
    # 非支配ソート
    fronts = non_dominated_sort(combined_population)
    
    # 次世代の選択
    new_population = []
    for front in fronts:
        calculate_crowding_distance(front)
        
        if len(new_population) + len(front) <= POPULATION_SIZE:
            new_population.extend(front)
        else:
            # 混雑距離でソートして選択
            front.sort(key=lambda x: x.crowding_distance, reverse=True)
            new_population.extend(front[:POPULATION_SIZE - len(new_population)])
            break
    
    population = new_population
    
    # パレートフロントの記録
    pareto_front = [ind for ind in population if ind.rank == 0]
    all_pareto_fronts.append(pareto_front)
    
    # 統計情報
    best_safety = max(-ind.objectives[0] for ind in pareto_front)
    best_cost = min(ind.objectives[1] for ind in pareto_front)
    
    print(f"\n🎯 世代 {generation} のパレート解数: {len(pareto_front)}")
    print(f"  最良安全率: {best_safety:.2f}")
    print(f"  最良コスト: {best_cost:.0f} 円/m²")
    
    # ログ記録
    with open(LOG_FILE, "a") as f:
        f.write(f"{generation}\t{len(pareto_front)}\t{best_safety:.2f}\t{best_cost:.0f}\n")
    
    # CSV記録
    for idx, ind in enumerate(population):
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                generation, idx+1, ind.rank, -ind.objectives[0], ind.objectives[1],
                ind.co2, ind.comfort, ind.constructability, ind.crowding_distance
            ])
    
    # パレート解の詳細をCSVに保存
    for ind in pareto_front:
        design = _vector_to_design(ind.genes)
        with open(PARETO_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            row = [generation, ind.rank, -ind.objectives[0], ind.objectives[1], 
                   ind.co2, ind.comfort, ind.constructability]
            row.extend([design[param] for param in PARAM_NAMES])
            writer.writerow(row)

# ---------- 最終結果 ----------
print("\n" + "="*60)
print("🏁 最適化完了！")
print("="*60)

final_pareto = [ind for ind in population if ind.rank == 0]
print(f"\n🏆 最終パレート解数: {len(final_pareto)}")

# パレート解の表示
print("\n📊 最終パレート解:")
print("-"*60)
print("No.\t安全率\tコスト\tCO2\t快適性\t施工性")
print("-"*60)
for i, ind in enumerate(final_pareto):
    print(f"{i+1}\t{-ind.objectives[0]:.2f}\t{ind.objectives[1]:.0f}\t"
          f"{ind.co2:.0f}\t{ind.comfort:.1f}\t{ind.constructability:.1f}")

# ---------- パレートフロントの可視化 ----------
print("\n📈 パレートフロントを生成中...")

# 1. 最終世代のパレートフロント
plt.figure(figsize=(10, 8))
safety_vals = [-ind.objectives[0] for ind in final_pareto]
cost_vals = [ind.objectives[1] for ind in final_pareto]

plt.scatter(safety_vals, cost_vals, s=100, alpha=0.7, edgecolors='black', linewidth=1.5)
plt.xlabel('安全率', fontsize=12)
plt.ylabel('建設コスト (円/m²)', fontsize=12)
plt.title('NSGA-IIによる最終パレートフロント', fontsize=14)
plt.grid(True, alpha=0.3)

# 安全率2.0の基準線
plt.axvline(x=2.0, color='r', linestyle='--', alpha=0.5, label='安全率2.0（推奨値）')
plt.legend()

plt.tight_layout()
plt.savefig('nsga2_final_pareto_front.png', dpi=150)
plt.close()

# 2. パレートフロントの進化
plt.figure(figsize=(12, 9))

# カラーマップ
import matplotlib.cm as cm
colors = cm.rainbow(np.linspace(0, 1, len(all_pareto_fronts)))

for i, (pareto, color) in enumerate(zip(all_pareto_fronts, colors)):
    if i % 5 == 0 or i == len(all_pareto_fronts) - 1:  # 5世代ごとまたは最終世代
        safety_vals = [-ind.objectives[0] for ind in pareto]
        cost_vals = [ind.objectives[1] for ind in pareto]
        plt.scatter(safety_vals, cost_vals, s=50, alpha=0.6, c=[color], 
                   label=f'世代{i+1}', edgecolors='black', linewidth=0.5)

plt.xlabel('安全率', fontsize=12)
plt.ylabel('建設コスト (円/m²)', fontsize=12)
plt.title('パレートフロントの進化過程', fontsize=14)
plt.grid(True, alpha=0.3)
plt.axvline(x=2.0, color='r', linestyle='--', alpha=0.5)
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig('nsga2_pareto_evolution.png', dpi=150, bbox_inches='tight')
plt.close()

# 3. 目的関数空間での全個体プロット
plt.figure(figsize=(10, 8))

# 全世代の全個体を薄くプロット
all_safety = []
all_cost = []
for generation in range(N_GENERATIONS + 1):
    # CSVから読み込む代わりに、現在のデータを使用
    pass

# 最終パレートを強調
final_safety = [-ind.objectives[0] for ind in final_pareto]
final_cost = [ind.objectives[1] for ind in final_pareto]

plt.scatter(final_safety, final_cost, s=150, c='red', alpha=0.8, 
           edgecolors='black', linewidth=2, label='最終パレート解', zorder=5)

plt.xlabel('安全率', fontsize=12)
plt.ylabel('建設コスト (円/m²)', fontsize=12)
plt.title('NSGA-II探索空間と最終パレート解', fontsize=14)
plt.grid(True, alpha=0.3)
plt.axvline(x=2.0, color='r', linestyle='--', alpha=0.5, label='安全率2.0（推奨値）')
plt.legend()
plt.tight_layout()
plt.savefig('nsga2_search_space.png', dpi=150)
plt.close()

print("✅ パレートフロント図を保存しました:")
print("  - nsga2_final_pareto_front.png: 最終パレートフロント")
print("  - nsga2_pareto_evolution.png: パレートフロントの進化過程")
print("  - nsga2_search_space.png: 探索空間と最終パレート解")

print("\n💾 詳細なログは以下のファイルを確認してください:")
print(f"  - {CSV_FILE}: 全個体の評価ログ")
print(f"  - {PARETO_FILE}: パレート解の詳細")
print(f"  - {LOG_FILE}: 進捗ログ")
print(f"  - {SETTINGS_FILE}: 実行設定")

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
print(f"1世代あたりの平均時間: {elapsed_time / N_GENERATIONS:.1f}秒")
print(f"1個体評価あたりの平均時間: {elapsed_time / ((N_GENERATIONS + 1) * POPULATION_SIZE):.1f}秒")
