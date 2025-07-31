#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全率計算の詳細デバッグ
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_building_fem_analyze import calculate_safety_factor

# FEM解析結果（test_material_final.pyの結果より）
# コンクリート造
concrete_stress = 13.3  # MPa
concrete_disp = 2.4     # mm
concrete_info = {
    'material_columns': 0,
    'material_walls': 0,
    'material_floor1': 0,
    'material_floor2': 0,
    'H1': 3.0,
    'H2': 3.0,
}

# 木造
wood_stress = 11.5  # MPa  
wood_disp = 4.8     # mm
wood_info = {
    'material_columns': 1,
    'material_walls': 1,
    'material_floor1': 1,
    'material_floor2': 1,
    'H1': 3.0,
    'H2': 3.0,
}

print("=== 安全率計算の詳細デバッグ ===\n")

print("【コンクリート造】")
print(f"入力: 応力={concrete_stress} MPa, 変位={concrete_disp} mm")
safety_c = calculate_safety_factor(concrete_stress, concrete_info, concrete_disp)
print(f"→ 安全率: {safety_c:.2f}\n")

print("\n【木造】")
print(f"入力: 応力={wood_stress} MPa, 変位={wood_disp} mm")
safety_w = calculate_safety_factor(wood_stress, wood_info, wood_disp)
print(f"→ 安全率: {safety_w:.2f}\n")

print(f"\n安全率比（木造/コンクリート）: {safety_w/safety_c:.2f}")

# 変位による安全率を直接計算
print("\n【変位による安全率の詳細計算】")
building_height = 6000  # mm (3m + 3m)
allowable_disp = building_height / 200  # 層間変形角1/200
print(f"許容変位: {allowable_disp:.1f} mm")

disp_safety_c = allowable_disp / concrete_disp
disp_safety_w_raw = allowable_disp / wood_disp
disp_safety_w = disp_safety_w_raw * 0.3  # 木造は0.3倍

print(f"コンクリート造の変位安全率: {disp_safety_c:.2f}")
print(f"木造の変位安全率（補正前）: {disp_safety_w_raw:.2f}")
print(f"木造の変位安全率（補正後）: {disp_safety_w:.2f}")