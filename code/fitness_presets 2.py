"""
fitness_presets.py

建築設計最適化向けの目的関数プリセット集。
すべての関数は既存シグネチャに準拠:
    calculate_fitness(cost, safety, co2, comfort, constructability) -> float

メモ:
- fitness は小さいほど良い（最小化）
- 安全率閾値は 2.0 を基本とし、各関数内で必要に応じてペナルティ
- コストやCO2の基準値は、ドキュメントと整合する代表値を使用
"""
from __future__ import annotations

# ---- 1) 経済性重視（安全率ペナルティ付き） ----
def fitness_economic_with_safety_penalty(cost, safety, co2, comfort, constructability):
    SAFETY_THRESHOLD = 2.0
    fitness = cost
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 100000
    return fitness

# ---- 2) 重み付き合成（バランス型） ----
# コスト0.4、CO2 0.3、快適性0.3（最大化なので 1−comfort/10）
def fitness_weighted_sum_balanced(cost, safety, co2, comfort, constructability):
    SAFETY_THRESHOLD = 2.0
    COST_BASE, CO2_BASE, COMFORT_BASE = 350000.0, 500.0, 10.0
    cost_n = cost / COST_BASE
    co2_n = co2 / CO2_BASE
    comfort_n = max(0.0, min(1.0, comfort / COMFORT_BASE))
    fitness = 0.4 * cost_n + 0.3 * co2_n + 0.3 * (1.0 - comfort_n)
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 100
    return fitness

# ---- 3) 低炭素重視（CO2最小 + 制約ペナルティ） ----
def fitness_low_carbon_priority(cost, safety, co2, comfort, constructability):
    SAFETY_TH, COST_CAP, CO2_CAP = 2.0, 350000.0, 500.0
    fitness = co2 / CO2_CAP
    if safety < SAFETY_TH:
        fitness += (SAFETY_TH - safety) * 100
    if cost > COST_CAP:
        fitness += (cost - COST_CAP) * 0.5 / COST_CAP
    return fitness

# ---- 4) 快適性重視（予算内最大快適） ----
def fitness_comfort_priority(cost, safety, co2, comfort, constructability):
    SAFETY_TH, COST_CAP, CO2_CAP = 2.0, 350000.0, 500.0
    comfort_n = max(0.0, min(1.0, comfort / 10.0))
    fitness = (1.0 - comfort_n)
    if safety < SAFETY_TH:
        fitness += (SAFETY_TH - safety) * 100
    if cost > COST_CAP:
        fitness += (cost - COST_CAP) * 0.5 / COST_CAP
    if co2 > CO2_CAP:
        fitness += (co2 - CO2_CAP) * 0.1 / CO2_CAP
    return fitness

# ---- 5) ロバスト安全余裕（目標2.2を緩く推奨） ----
def fitness_robust_safety_margin(cost, safety, co2, comfort, constructability):
    SAFETY_TH = 2.0
    TARGET_SAFETY = 2.2
    fitness = cost / 350000.0 + co2 / 500.0
    if safety < SAFETY_TH:
        fitness += (SAFETY_TH - safety) * 100
    if safety < TARGET_SAFETY:
        fitness += (TARGET_SAFETY - safety) * 10
    return fitness

# ---- 6) 施工性トレードオフ（厚すぎ/形状難の抑制を代理） ----
# 施工性は10が良い想定 → (1−constructability/10)を最小化に加える
def fitness_constructability_tradeoff(cost, safety, co2, comfort, constructability):
    SAFETY_TH = 2.0
    construct_n = max(0.0, min(1.0, constructability / 10.0))
    fitness = 0.5 * (cost / 350000.0) + 0.2 * (co2 / 500.0) + 0.3 * (1.0 - construct_n)
    if safety < SAFETY_TH:
        fitness += (SAFETY_TH - safety) * 100
    return fitness

# ---- 7) 辞書式（安全性最優先 → コスト → CO2） ----
def fitness_lexicographic_safety_cost_co2(cost, safety, co2, comfort, constructability):
    SAFETY_TH = 2.0
    if safety < SAFETY_TH:
        return 1e9 + (SAFETY_TH - safety) * 1e7
    return cost + 100.0 * (co2 / 500.0)

# ---- 8) 体積（軽量化）志向 + 安全ペナルティ ----
# コストが体積近似の場合に有効
def fitness_lightweight_volume_proxy(cost, safety, co2, comfort, constructability):
    SAFETY_TH = 2.0
    fitness = cost / 350000.0
    if safety < SAFETY_TH:
        fitness += (SAFETY_TH - safety) * 100
    fitness += 0.1 * (1.0 - max(0.0, min(1.0, comfort / 10.0)))
    return fitness

# エイリアス（日本語/英語）
PRESET_NAME_TO_FUNC = {
    # 英語キー
    "economic_with_safety_penalty": fitness_economic_with_safety_penalty,
    "weighted_sum_balanced": fitness_weighted_sum_balanced,
    "low_carbon_priority": fitness_low_carbon_priority,
    "comfort_priority": fitness_comfort_priority,
    "robust_safety_margin": fitness_robust_safety_margin,
    "constructability_tradeoff": fitness_constructability_tradeoff,
    "lexicographic_safety_cost_co2": fitness_lexicographic_safety_cost_co2,
    "lightweight_volume_proxy": fitness_lightweight_volume_proxy,
    # 日本語キー
    "経済性重視": fitness_economic_with_safety_penalty,
    "重み付き合成(バランス)": fitness_weighted_sum_balanced,
    "低炭素重視": fitness_low_carbon_priority,
    "快適性重視": fitness_comfort_priority,
    "ロバスト安全余裕": fitness_robust_safety_margin,
    "施工性トレードオフ": fitness_constructability_tradeoff,
    "辞書式(安全→コスト→CO2)": fitness_lexicographic_safety_cost_co2,
    "軽量化志向": fitness_lightweight_volume_proxy,
}
