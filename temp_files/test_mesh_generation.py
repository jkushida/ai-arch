#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
メッシュ生成テストスクリプト
"""

import sys
import os

# FreeCAD環境の初期化
FREECAD_PATH = '/Applications/FreeCAD.app/Contents/Resources/lib'
if FREECAD_PATH not in sys.path:
    sys.path.append(FREECAD_PATH)

# generate_building_fem_analyzeモジュールの強制リロード
if 'generate_building_fem_analyze' in sys.modules:
    del sys.modules['generate_building_fem_analyze']

from generate_building_fem_analyze import evaluate_building_from_params

print("メッシュ生成テスト開始")
print("=" * 60)

# シンプルなテストパラメータ
dv = {
    'Lx': 8.0,
    'Ly': 8.0,
    'H1': 3.0,
    'H2': 3.0,
    'tf': 300,
    'tr': 300,
    'bc': 600,
    'hc': 600,
    'tw_ext': 300,
    'wall_tilt_angle': 0.0,
    'window_ratio_2f': 0.3,
    'roof_morph': 0.5,
    'roof_shift': 0.0,
    'balcony_depth': 1.5,
    'material_columns': 0,  # コンクリート
    'material_floor1': 0,
    'material_floor2': 0,
    'material_roof': 0,
    'material_walls': 0,
    'material_balcony': 0
}

# 評価実行
try:
    result = evaluate_building_from_params(dv, save_fcstd=False)
    
    if result.get('status') == 'Success':
        print("\n✅ テスト成功")
        print(f"安全率: {result.get('safety', {}).get('overall_safety_factor', 0.0):.2f}")
        print(f"コスト: {result.get('economic', {}).get('cost_per_sqm', 0.0):,.0f} 円/m²")
    else:
        print(f"\n❌ テスト失敗: {result.get('message', 'Unknown error')}")
        
except Exception as e:
    print(f"\n❌ エラー発生: {e}")
    import traceback
    traceback.print_exc()