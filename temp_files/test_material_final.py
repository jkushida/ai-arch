#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
最終材料特性テスト
"""

import sys
import os

# キャッシュクリア
for m in list(sys.modules.keys()):
    if 'generate_building' in m:
        del sys.modules[m]

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generate_building_fem_analyze import evaluate_building_from_params

# 小さめのテストケース（計算時間短縮）
design_vars = {
    "Lx": 6.0,
    "Ly": 6.0,
    "H1": 3.0,
    "H2": 3.0,
    "tf": 200,
    "tr": 150,
    "bc": 400,
    "hc": 400,
    "tw_ext": 200,
    "wall_tilt_angle": 0.0,
    "window_ratio_2f": 0.2,
    "roof_morph": 0.5,
    "roof_shift": 0.0,
    "balcony_depth": 0.0,
    "material_columns": 0,  # コンクリート
    "material_floor1": 0,
    "material_floor2": 0,
    "material_roof": 0,
    "material_walls": 0,
    "material_balcony": 0,
}

print("コンクリート造テスト中...")
result_c = evaluate_building_from_params(design_vars, save_fcstd=False)

# 木造
design_vars.update({
    "material_columns": 1,
    "material_floor1": 1,
    "material_floor2": 1,
    "material_roof": 1,
    "material_walls": 1,
    "material_balcony": 1,
})

print("\n木造テスト中...")
result_w = evaluate_building_from_params(design_vars, save_fcstd=False)

# 結果表示
print("\n" + "="*60)
print("最終結果")
print("="*60)

if result_c['status'] == 'Success' and result_w['status'] == 'Success':
    c_safety = result_c['safety']['overall_safety_factor']
    w_safety = result_w['safety']['overall_safety_factor']
    c_stress = result_c['safety'].get('max_stress', 0)
    w_stress = result_w['safety'].get('max_stress', 0)
    c_disp = result_c['safety'].get('max_displacement', 0)
    w_disp = result_w['safety'].get('max_displacement', 0)
    
    print(f"コンクリート造: 安全率={c_safety:.2f}, 応力={c_stress:.1f}MPa, 変位={c_disp:.1f}mm")
    print(f"木造: 安全率={w_safety:.2f}, 応力={w_stress:.1f}MPa, 変位={w_disp:.1f}mm")
    print(f"\n安全率比（木造/コンクリート）: {w_safety/c_safety:.2f}")
    print(f"応力比（木造/コンクリート）: {w_stress/c_stress:.2f}")
    print(f"変位比（木造/コンクリート）: {w_disp/c_disp:.2f}")
    
    if w_safety < c_safety:
        print("\n✅ 成功！木造の安全率がコンクリート造より低い")
    else:
        print("\n❌ 木造の安全率が依然として高い")
else:
    print("エラーが発生しました")