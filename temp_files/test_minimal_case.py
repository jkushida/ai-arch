#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最小限のケースで材料選択機能をテスト
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# VERBOSE出力を有効化
os.environ['VERBOSE_OUTPUT'] = 'True'

from generate_building_fem_analyze import evaluate_building_from_params

# 成功したパラメータと同じ
base_params = {
    'Lx': 6.0,
    'Ly': 6.0,
    'H1': 3.0,
    'H2': 3.0,
    'tf': 200,
    'tr': 150,
    'bc': 300,
    'hc': 300,
    'tw_ext': 150,
    'wall_tilt_angle': 0.0,
    'window_ratio_2f': 0.2,
    'roof_morph': 0.5,
    'roof_shift': 0.0,
    'balcony_depth': 0.0,
    # 材料選択
    'material_columns': 0,
    'material_floor1': 0,
    'material_floor2': 0,
    'material_roof': 0,
    'material_walls': 0,
    'material_balcony': 0
}

print("=== 最小限のケーステスト ===")

# ケース1: ベースケース（成功済み）
print("\n【ケース1: ベースケース】")
try:
    result = evaluate_building_from_params(base_params)
    print(f"結果: {result['status']}")
except Exception as e:
    print(f"エラー: {e}")

# ケース2: 壁傾斜を追加
print("\n【ケース2: 壁傾斜10度】")
params2 = base_params.copy()
params2['wall_tilt_angle'] = 10.0
try:
    result = evaluate_building_from_params(params2)
    print(f"結果: {result['status']}")
except Exception as e:
    print(f"エラー: {e}")

# ケース3: バルコニーを追加
print("\n【ケース3: バルコニー1m】")
params3 = base_params.copy()
params3['balcony_depth'] = 1.0
try:
    result = evaluate_building_from_params(params3)
    print(f"結果: {result['status']}")
except Exception as e:
    print(f"エラー: {e}")

# ケース4: 全て木材
print("\n【ケース4: 全て木材】")
params4 = base_params.copy()
params4.update({
    'material_columns': 1,
    'material_floor1': 1,
    'material_floor2': 1,
    'material_roof': 1,
    'material_walls': 1,
    'material_balcony': 1
})
try:
    result = evaluate_building_from_params(params4)
    print(f"結果: {result['status']}")
except Exception as e:
    print(f"エラー: {e}")

print("\n=== テスト完了 ===")