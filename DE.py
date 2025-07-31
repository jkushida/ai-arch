#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DE_optimization_v9.py
差分進化アルゴリズムによる建築設計最適化
"""

import numpy as np
import csv
import random
import time
import signal
import sys
import os
import gc

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

# DEパラメータ
N_SAMPLES = 15  # 初期個体数
MAX_GEN = 20    # 世代数
F = 0.5         # 差分ベクトルのスケーリングファクタ
CR = 0.9        # 交叉確率

# タイムアウト設定
EVALUATION_TIMEOUT = 120  # 2分（FEM解析は時間がかかる）

# CSV設定
CSV_FILE = "de_optimization_log.csv"

print("🚀 差分進化アルゴリズムによる建築設計最適化開始")
print(f"📊 個体数: {N_SAMPLES}, 世代数: {MAX_GEN}")
print(f"🔧 DE パラメータ: F={F}, CR={CR}")

# 乱数シード設定
base_seed = 42
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

# ---------- 設計変数の範囲定義 ----------
def get_bounds():
    """現在のモデルに合わせた設計変数の範囲"""
    # [Lx, Ly, H1, H2, tf, tr, bc, hc, tw_ext, wall_tilt, window_ratio, roof_morph, roof_shift, balcony_depth]
    bound_low = [
        5.0,    # Lx [m]
        5.0,    # Ly [m]
        2.5,    # H1 [m]
        2.5,    # H2 [m]
        120,    # tf [mm]
        100,    # tr [mm]
        200,    # bc [mm]
        200,    # hc [mm]
        100,    # tw_ext [mm]
        -40.0,  # wall_tilt_angle [°]
        0.1,    # window_ratio_2f
        0.0,    # roof_morph
        -0.7,   # roof_shift
        0.1     # balcony_depth [m]
    ]
    bound_up = [
        20.0,   # Lx [m]
        20.0,   # Ly [m]
        4.5,    # H1 [m]
        4.0,    # H2 [m]
        500,    # tf [mm]
        400,    # tr [mm]
        800,    # bc [mm]
        800,    # hc [mm]
        350,    # tw_ext [mm]
        40.0,   # wall_tilt_angle [°]
        0.9,    # window_ratio_2f
        1.0,    # roof_morph
        0.7,    # roof_shift
        5.0     # balcony_depth [m]
    ]
    return bound_low, bound_up

# ---------- タイムアウト制御 ----------
class TimeoutError(Exception):
    pass

def _timeout_handler(signum, frame):
    raise TimeoutError("evaluation timeout")

_HAS_SIGALRM = hasattr(signal, "SIGALRM")
if _HAS_SIGALRM:
    signal.signal(signal.SIGALRM, _timeout_handler)

# ---------- FreeCADメモリクリーンアップ ----------
def _cleanup_freecad_memory():
    """FreeCADのドキュメントを閉じてメモリリークを防ぐ"""
    try:
        import FreeCAD as App
        for doc in list(App.listDocuments().values()):
            try:
                App.closeDocument(doc.Name)
            except:
                pass
    except:
        pass
    gc.collect()

# ---------- 評価関数ラッパー ----------
def _evaluate_once(design_vars: dict, timeout_s: int = EVALUATION_TIMEOUT):
    """タイムアウト付き評価"""
    if _HAS_SIGALRM:
        signal.alarm(timeout_s)
    try:
        res = evaluate_building_from_params(design_vars, save_fcstd=False)
        if _HAS_SIGALRM:
            signal.alarm(0)  # タイムアウトキャンセル
        return res
    except TimeoutError:
        raise TimeoutError("evaluation timeout")
    except Exception as e:
        if _HAS_SIGALRM:
            signal.alarm(0)
        raise e
    finally:
        _cleanup_freecad_memory()

# ---------- ベクトル⇔設計変数変換 ----------
def _vector_to_design(vec):
    """ベクトル形式から設計変数辞書へ変換"""
    keys = ["Lx", "Ly", "H1", "H2", "tf", "tr", "bc", "hc", "tw_ext",
            "wall_tilt_angle", "window_ratio_2f", "roof_morph", "roof_shift", "balcony_depth"]
    dv = {}
    for k, v in zip(keys, vec):
        if k in ["tf", "tr", "bc", "hc", "tw_ext"]:
            dv[k] = int(round(v))
        else:
            dv[k] = float(v)
    return dv

# ---------- 個体クラス ----------
class Individual:
    def __init__(self, vec):
        self.x = np.asarray(vec, dtype=float)
        self.fit = None
        self.safety = None
        self.cost = None
        self.co2 = None
        self.comfort = None
        self.constructability = None

# ---------- 個体評価関数 ----------
def evaluate_individual(ind: Individual, idx: int = None) -> float:
    """個体の評価（コスト最小化 + 安全率制約）"""
    try:
        dv = _vector_to_design(ind.x)
        res = _evaluate_once(dv)
        
        if res['status'] != 'Success':
            raise Exception(f"評価失敗: {res['message']}")
        
        # 各評価値を取得
        ind.cost = res["economic"]["cost_per_sqm"]
        ind.safety = res["safety"]["overall_safety_factor"]
        ind.co2 = res["environmental"]["co2_per_sqm"]
        ind.comfort = res["comfort"]["comfort_score"]
        ind.constructability = res["constructability"]["constructability_score"]
        
        # 目的関数：コスト最小化 + 安全率ペナルティ
        f1 = ind.cost
        
        # 安全率制約（2.5以上を推奨）
        if ind.safety < 2.5:
            penalty = (2.5 - ind.safety) * 100000  # 大きなペナルティ
            f1 += penalty
        
        ind.fit = f1
        
        if idx is not None:
            print(f"  個体 {idx+1}: cost={ind.cost:.0f}, safety={ind.safety:.2f}, "
                  f"CO2={ind.co2:.0f}, comfort={ind.comfort:.1f}")
        
        return ind.fit
        
    except Exception as e:
        if idx is not None:
            print(f"  ❌ 個体 {idx+1} の評価失敗: {e}")
        ind.fit = float("inf")
        ind.safety = 0.0
        ind.cost = float("inf")
        ind.co2 = float("inf")
        ind.comfort = 0.0
        ind.constructability = 0.0
        return float("inf")

# ---------- CSVヘッダー作成 ----------
with open(CSV_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "generation", "individual", "fitness", "cost", "safety",
        "co2", "comfort", "constructability"
    ])

# ---------- 初期個体群の生成 ----------
print("\n📊 初期個体群の生成と評価...")
bound_low, bound_up = get_bounds()
NP = N_SAMPLES
Pop = []

for idx in range(NP):
    print(f"\n🧬 個体 {idx+1}/{NP}")
    # ランダムな設計ベクトル生成
    vec = [low + (up - low) * rng.random() for low, up in zip(bound_low, bound_up)]
    ind = Individual(vec)
    evaluate_individual(ind, idx)
    
    # CSV記録
    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            0, idx+1, ind.fit, ind.cost, ind.safety,
            ind.co2, ind.comfort, ind.constructability
        ])
    
    Pop.append(ind)

# 最良個体の表示
best = min(Pop, key=lambda ind: ind.fit)
print(f"\n🏆 初期世代の最良個体:")
print(f"  fitness = {best.fit:.2f}")
print(f"  cost = {best.cost:.0f} 円/m²")
print(f"  safety = {best.safety:.2f}")
print(f"  設計変数 = {_vector_to_design(best.x)}")

# ---------- 進化ループ ----------
history = []

for gen in range(MAX_GEN):
    print(f"\n{'='*60}")
    print(f"世代 {gen+1}/{MAX_GEN}")
    print(f"{'='*60}")
    
    new_pop = []
    
    for i in range(NP):
        # 差分進化の操作
        # 3個体をランダム選択（i以外）
        idxs = list(range(NP))
        idxs.remove(i)
        r1, r2, r3 = rng.sample(idxs, 3)
        x1, x2, x3 = Pop[r1].x, Pop[r2].x, Pop[r3].x
        
        # 変異（Mutation）
        mutant = x1 + F * (x2 - x3)
        
        # 境界処理
        mutant = np.clip(mutant, bound_low, bound_up)
        
        # 交叉（Crossover）
        trial = np.copy(Pop[i].x)
        j_rand = rng.randint(0, len(trial)-1)
        for j in range(len(trial)):
            if rng.random() < CR or j == j_rand:
                trial[j] = mutant[j]
        
        # 評価
        ind = Individual(trial)
        print(f"\n世代 {gen+1}/{MAX_GEN}  評価 {i+1}/{NP}")
        evaluate_individual(ind, i)
        
        # CSV記録
        with open(CSV_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                gen+1, i+1, ind.fit, ind.cost, ind.safety,
                ind.co2, ind.comfort, ind.constructability
            ])
        
        # 選択（Selection）
        if ind.fit < Pop[i].fit:
            new_pop.append(ind)
        else:
            new_pop.append(Pop[i])
    
    # 世代更新
    Pop = new_pop
    
    # 最良個体の記録
    best_ind = min(Pop, key=lambda ind: ind.fit)
    history.append({
        'generation': gen+1,
        'fitness': best_ind.fit,
        'cost': best_ind.cost,
        'safety': best_ind.safety,
        'co2': best_ind.co2,
        'comfort': best_ind.comfort
    })
    
    print(f"\n📊 世代 {gen+1} の最良個体:")
    print(f"  fitness = {best_ind.fit:.2f}")
    print(f"  cost = {best_ind.cost:.0f} 円/m²")
    print(f"  safety = {best_ind.safety:.2f}")
    print(f"  CO2 = {best_ind.co2:.0f} kg-CO2/m²")
    print(f"  comfort = {best_ind.comfort:.1f}")

# ---------- 最終結果 ----------
print(f"\n{'='*60}")
print("🏆 最終結果")
print(f"{'='*60}")
final_best = min(Pop, key=lambda ind: ind.fit)
print(f"最良設計:")
print(f"  cost = {final_best.cost:.0f} 円/m²")
print(f"  safety = {final_best.safety:.2f}")
print(f"  CO2 = {final_best.co2:.0f} kg-CO2/m²")
print(f"  comfort = {final_best.comfort:.1f}")
print(f"  constructability = {final_best.constructability:.1f}")
print(f"\n設計変数:")
design = _vector_to_design(final_best.x)
for k, v in design.items():
    print(f"  {k}: {v}")

# ---------- グラフ作成 ----------
if len(history) > 0:
    generations = [h['generation'] for h in history]
    
    # 収束曲線
    plt.figure(figsize=(10, 6))
    plt.plot(generations, [h['fitness'] for h in history], 'b-', label='Fitness')
    plt.xlabel('Generation')
    plt.ylabel('Fitness (Cost with Penalty)')
    plt.title('DE Convergence Curve')
    plt.grid(True)
    plt.legend()
    plt.savefig('de_convergence_curve.png')
    print("\n✅ 収束曲線を 'de_convergence_curve.png' に保存")
    
    # 多目的の推移
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # コスト
    axes[0, 0].plot(generations, [h['cost'] for h in history], 'r-')
    axes[0, 0].set_xlabel('Generation')
    axes[0, 0].set_ylabel('Cost [JPY/m²]')
    axes[0, 0].set_title('Cost Evolution')
    axes[0, 0].grid(True)
    
    # 安全率
    axes[0, 1].plot(generations, [h['safety'] for h in history], 'g-')
    axes[0, 1].axhline(y=2.5, color='r', linestyle='--', label='Target')
    axes[0, 1].set_xlabel('Generation')
    axes[0, 1].set_ylabel('Safety Factor')
    axes[0, 1].set_title('Safety Factor Evolution')
    axes[0, 1].grid(True)
    axes[0, 1].legend()
    
    # CO2
    axes[1, 0].plot(generations, [h['co2'] for h in history], 'b-')
    axes[1, 0].set_xlabel('Generation')
    axes[1, 0].set_ylabel('CO2 [kg-CO2/m²]')
    axes[1, 0].set_title('CO2 Emission Evolution')
    axes[1, 0].grid(True)
    
    # 快適性
    axes[1, 1].plot(generations, [h['comfort'] for h in history], 'm-')
    axes[1, 1].set_xlabel('Generation')
    axes[1, 1].set_ylabel('Comfort Score')
    axes[1, 1].set_title('Comfort Score Evolution')
    axes[1, 1].grid(True)
    
    plt.tight_layout()
    plt.savefig('de_multiobjective_evolution.png')
    print("✅ 多目的推移を 'de_multiobjective_evolution.png' に保存")

print("\n🎉 差分進化アルゴリズムによる最適化完了！")
