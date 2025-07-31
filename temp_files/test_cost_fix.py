#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正後のコスト計算テスト
"""

import sys
import os

# FreeCAD環境の初期化
FREECAD_PATH = '/Applications/FreeCAD.app/Contents/Resources/lib'
if FREECAD_PATH not in sys.path:
    sys.path.append(FREECAD_PATH)

# モジュールの強制リロード
if 'generate_building_fem_analyze' in sys.modules:
    del sys.modules['generate_building_fem_analyze']

from generate_building_fem_analyze import evaluate_building_from_params

print("修正後のコスト計算テスト")
print("=" * 60)

# Sample21のパラメータ（安全率3.255、元コスト491,435円/m²）
sample21_params = {
    'Lx': 9.73,
    'Ly': 10.69,
    'H1': 2.68,
    'H2': 2.61,
    'tf': 467,
    'tr': 505,
    'bc': 753,
    'hc': 634,
    'tw_ext': 315,
    'wall_tilt_angle': -26.5,
    'window_ratio_2f': 0.14,
    'roof_morph': 0.84,
    'roof_shift': -0.21,
    'balcony_depth': 1.3,
    'material_columns': 1,  # 木材
    'material_floor1': 1,
    'material_floor2': 1,
    'material_roof': 1,
    'material_walls': 1,
    'material_balcony': 0
}

# Sample37のパラメータ（安全率3.505、元コスト705,397円/m²）
sample37_params = {
    'Lx': 8.92,
    'Ly': 10.79,
    'H1': 3.26,
    'H2': 2.67,
    'tf': 337,
    'tr': 483,
    'bc': 921,
    'hc': 784,
    'tw_ext': 326,
    'wall_tilt_angle': -18.2,
    'window_ratio_2f': 0.15,
    'roof_morph': 0.2,
    'roof_shift': -0.33,
    'balcony_depth': 1.2,
    'material_columns': 0,  # コンクリート
    'material_floor1': 0,
    'material_floor2': 0,
    'material_roof': 0,
    'material_walls': 0,
    'material_balcony': 0
}

# テスト実行
for name, params in [("Sample21", sample21_params), ("Sample37", sample37_params)]:
    print(f"\n{name}のテスト:")
    print(f"  柱サイズ: {params['bc']}x{params['hc']} mm")
    print(f"  材料: {['コンクリート', '木材', 'CLT'][params['material_columns']]}")
    
    try:
        result = evaluate_building_from_params(params, save_fcstd=False)
        
        if result.get('status') == 'Success':
            cost_per_sqm = result.get('economic', {}).get('cost_per_sqm', 0)
            safety_factor = result.get('safety', {}).get('overall_safety_factor', 0)
            
            print(f"  ✅ 成功:")
            print(f"     安全率: {safety_factor:.3f}")
            print(f"     修正後コスト: {cost_per_sqm:,.0f} 円/m²")
        else:
            print(f"  ❌ 失敗: {result.get('message', 'Unknown error')}")
    except Exception as e:
        print(f"  ❌ エラー: {e}")

print("\n" + "=" * 60)