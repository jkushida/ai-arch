#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接的な安全率計算テスト
"""

import sys
import os

# キャッシュクリア
for m in list(sys.modules.keys()):
    if 'generate_building_fem_analyze' in m:
        del sys.modules[m]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# VERBOSE出力を有効化
import generate_building_fem_analyze
generate_building_fem_analyze.VERBOSE_OUTPUT = True

from generate_building_fem_analyze import calculate_safety_factor

# テストデータ
max_stress = 20.0  # MPa
max_displacement = 3.0  # mm

# コンクリート造の建物情報
building_info_concrete = {
    'material_columns': 0,  # コンクリート
    'material_walls': 0,
    'material_floor1': 0,
    'material_floor2': 0,
    'H1': 3.0,
    'H2': 3.0,
}

# 木造の建物情報
building_info_wood = {
    'material_columns': 1,  # 木材
    'material_walls': 1,
    'material_floor1': 1,
    'material_floor2': 1,
    'H1': 3.0,
    'H2': 3.0,
}

print("=== 直接的な安全率計算テスト ===\n")

print("コンクリート造:")
safety_concrete = calculate_safety_factor(max_stress, building_info_concrete, max_displacement)
print(f"  最終安全率: {safety_concrete:.2f}\n")

print("\n木造:")
safety_wood = calculate_safety_factor(max_stress, building_info_wood, max_displacement)
print(f"  最終安全率: {safety_wood:.2f}\n")

print(f"\n安全率比（木造/コンクリート）: {safety_wood/safety_concrete:.2f}")

if safety_wood < safety_concrete:
    print("✅ 成功！木造の安全率がコンクリート造より低い")
else:
    print("❌ 失敗！木造の安全率が高い")