#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
対数的構造体積係数のテスト
"""
import math

def calculate_structural_volume_factor_old(bc, hc, tf, tr, tw_ext, material_factor=1.0):
    """旧バージョン（二次関数）"""
    column_oversize = max(1.0, (bc * hc) / (400 * 400))
    floor_oversize = max(1.0, tf / 200)
    roof_oversize = max(1.0, tr / 200)
    wall_oversize = max(1.0, tw_ext / 200)
    
    factor = 1.0 + (
        0.5 * (column_oversize - 1.0) ** 2.0 +
        0.3 * (floor_oversize - 1.0) ** 2.0 +
        0.15 * (roof_oversize - 1.0) ** 2.0 +
        0.15 * (wall_oversize - 1.0) ** 2.0
    ) * material_factor
    
    return factor

def calculate_structural_volume_factor_new(bc, hc, tf, tr, tw_ext, material_factor=1.0):
    """新バージョン（対数）"""
    column_oversize = max(1.0, (bc * hc) / (400 * 400))
    floor_oversize = max(1.0, tf / 200)
    roof_oversize = max(1.0, tr / 200)
    wall_oversize = max(1.0, tw_ext / 200)
    
    factor = 1.0 + (
        0.5 * math.log(column_oversize) +
        0.3 * math.log(floor_oversize) +
        0.15 * math.log(roof_oversize) +
        0.15 * math.log(wall_oversize)
    ) * material_factor
    
    return factor

# テストケース
test_cases = [
    # 標準的なケース
    {"name": "標準", "bc": 400, "hc": 400, "tf": 200, "tr": 200, "tw_ext": 200},
    # 中規模
    {"name": "中規模", "bc": 600, "hc": 600, "tf": 300, "tr": 300, "tw_ext": 300},
    # 大規模
    {"name": "大規模", "bc": 800, "hc": 800, "tf": 400, "tr": 400, "tw_ext": 400},
    # sample3のケース
    {"name": "sample3", "bc": 897, "hc": 933, "tf": 513, "tr": 553, "tw_ext": 471},
    # 超大規模
    {"name": "超大規模", "bc": 1000, "hc": 1000, "tf": 600, "tr": 600, "tw_ext": 500},
]

print("構造体積係数の比較（木材、material_factor=1.5）")
print("=" * 80)
print(f"{'ケース':<10} {'柱断面積':>10} {'旧方式':>10} {'新方式':>10} {'削減率':>10}")
print("-" * 80)

for case in test_cases:
    col_area = case["bc"] * case["hc"]
    old_factor = calculate_structural_volume_factor_old(**{k: v for k, v in case.items() if k != "name"}, material_factor=1.5)
    new_factor = calculate_structural_volume_factor_new(**{k: v for k, v in case.items() if k != "name"}, material_factor=1.5)
    reduction = (1 - new_factor / old_factor) * 100
    
    print(f"{case['name']:<10} {col_area:>10,} {old_factor:>10.2f} {new_factor:>10.2f} {reduction:>9.1f}%")

print("\nコスト計算例（基本単価: 500,000円/m²）")
print("-" * 80)

for case in test_cases:
    old_factor = calculate_structural_volume_factor_old(**{k: v for k, v in case.items() if k != "name"}, material_factor=1.5)
    new_factor = calculate_structural_volume_factor_new(**{k: v for k, v in case.items() if k != "name"}, material_factor=1.5)
    
    # 追加補正を含む（大型構造1.2、木材大断面1.15）
    if case["bc"] * case["hc"] > 640000:
        old_factor *= 1.2
        new_factor *= 1.2
    if case["bc"] * case["hc"] > 400000:
        old_factor *= 1.15
        new_factor *= 1.15
    
    old_cost = 500_000 * old_factor
    new_cost = 500_000 * new_factor
    
    print(f"{case['name']:<10} 旧: {old_cost:>12,.0f}円/m² → 新: {new_cost:>12,.0f}円/m²")