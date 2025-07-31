#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
地震荷重追加のテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# デバッグ出力は常に有効

from generate_building_fem_analyze import evaluate_building_from_params

# テストケース1: コンクリート造
print("=" * 60)
print("テストケース1: コンクリート造")
print("=" * 60)

design_vars_concrete = {
    "Lx": 10.0,
    "Ly": 10.0,
    "H1": 3.0,
    "H2": 3.0,
    "tf": 300,
    "tr": 250,
    "bc": 500,
    "hc": 500,
    "tw_ext": 250,
    "wall_tilt_angle": 0.0,
    "window_ratio_2f": 0.3,
    "roof_morph": 0.5,
    "roof_shift": 0.0,
    "balcony_depth": 2.0,
    # すべてコンクリート
    "material_columns": 0,
    "material_floor1": 0,
    "material_floor2": 0,
    "material_roof": 0,
    "material_walls": 0,
    "material_balcony": 0,
}

result_concrete = evaluate_building_from_params(design_vars_concrete, save_fcstd=True, fcstd_path="test_seismic_concrete.FCStd")

if result_concrete['status'] == 'Success':
    print(f"✅ コンクリート造 - 安全率: {result_concrete['safety']['overall_safety_factor']:.2f}")
    print(f"   コスト: {result_concrete['economic']['cost_per_sqm']:,.0f} 円/m²")
    print(f"   CO2: {result_concrete['environmental']['co2_per_sqm']:.1f} kg-CO2/m²")
else:
    print(f"❌ エラー: {result_concrete['message']}")

print("\n" + "=" * 60)
print("テストケース2: 木造")
print("=" * 60)

# テストケース2: 木造
design_vars_wood = design_vars_concrete.copy()
design_vars_wood.update({
    # すべて木材
    "material_columns": 1,
    "material_floor1": 1,
    "material_floor2": 1,
    "material_roof": 1,
    "material_walls": 1,
    "material_balcony": 1,
})

result_wood = evaluate_building_from_params(design_vars_wood, save_fcstd=True, fcstd_path="test_seismic_wood.FCStd")

if result_wood['status'] == 'Success':
    print(f"✅ 木造 - 安全率: {result_wood['safety']['overall_safety_factor']:.2f}")
    print(f"   コスト: {result_wood['economic']['cost_per_sqm']:,.0f} 円/m²")
    print(f"   CO2: {result_wood['environmental']['co2_per_sqm']:.1f} kg-CO2/m²")
else:
    print(f"❌ エラー: {result_wood['message']}")

# 結果比較
if result_concrete['status'] == 'Success' and result_wood['status'] == 'Success':
    print("\n" + "=" * 60)
    print("結果比較（地震荷重あり）")
    print("=" * 60)
    
    safety_ratio = result_wood['safety']['overall_safety_factor'] / result_concrete['safety']['overall_safety_factor']
    print(f"安全率比（木造/コンクリート）: {safety_ratio:.2f}")
    
    if safety_ratio > 1.5:
        print("⚠️ 木造の安全率が依然として高すぎます。地震荷重の効果が不十分かもしれません。")
    elif safety_ratio < 0.8:
        print("✅ 地震荷重により、木造の相対的な安全率が低下しました。")
    else:
        print("🔄 地震荷重の効果はありますが、まだ調整が必要かもしれません。")