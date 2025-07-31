#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sample21の修正後コスト計算テスト
"""

# 修正後の構造体積係数の計算を再現
def calculate_structural_volume_factor_fixed(bc, hc, tf, tr, tw_ext, 
                                            material_columns=0, 
                                            wood_count=0):
    # 各部材の「過大度」を評価
    column_oversize = max(1.0, (bc * hc) / (400 * 400))
    floor_oversize = max(1.0, tf / 200)
    roof_oversize = max(1.0, tr / 200)
    wall_oversize = max(1.0, tw_ext / 200)
    
    # 材料による補正（木材は1.5に強化）
    if material_columns == 1:  # 木材
        material_factor = 1.5  # 1.2→1.5
    elif material_columns == 2:  # CLT
        material_factor = 0.9
    else:  # コンクリート
        material_factor = 1.0
    
    # 総合的な構造体積係数
    structural_volume_factor = 1.0 + (
        0.5 * (column_oversize - 1.0) ** 2.0 +
        0.3 * (floor_oversize - 1.0) ** 2.0 +
        0.15 * (roof_oversize - 1.0) ** 2.0 +
        0.15 * (wall_oversize - 1.0) ** 2.0
    ) * material_factor
    
    # 大型構造の特殊工法コスト
    if bc * hc > 640000:
        structural_volume_factor *= 1.2
    
    # 床版厚が500mmを超える場合
    if tf > 500 or tr > 500:
        structural_volume_factor *= 1.15
    
    # 木材使用数による追加コスト
    if wood_count >= 5:  # 全木造
        structural_volume_factor *= 1.2
    elif wood_count >= 3:  # 木造主体
        structural_volume_factor *= 1.1
    
    # 木材で大断面の場合
    if material_columns == 1 and bc * hc > 400000:
        structural_volume_factor *= 1.15
    
    return max(1.0, structural_volume_factor)

print("Sample21の修正後コスト計算")
print("=" * 60)

# Sample21のデータ（安全率3.258）
sample21 = {
    'bc': 753, 'hc': 634, 'tf': 467, 'tr': 505, 'tw_ext': 315,
    'material_columns': 1,  # 木材
    'wood_count': 5  # 全木造（柱、床1、床2、屋根、壁すべて木材）
}

# 修正前の係数（材料係数1.2時代）
column_oversize = (753 * 634) / (400 * 400)
floor_oversize = 467 / 200
roof_oversize = 505 / 200
wall_oversize = 315 / 200

old_factor_base = 1.0 + (
    0.5 * (column_oversize - 1.0) ** 2.0 +
    0.3 * (floor_oversize - 1.0) ** 2.0 +
    0.15 * (roof_oversize - 1.0) ** 2.0 +
    0.15 * (wall_oversize - 1.0) ** 2.0
) * 1.2  # 古い材料係数

old_factor = old_factor_base * 1.15  # 床版>500mm

print("【修正前】")
print(f"  材料係数: 1.2")
print(f"  構造体積係数: {old_factor:.3f}")
print(f"  推定コスト: {500000 * old_factor:,.0f} 円/m²")
print(f"  実際のコスト: 1,220,871 円/m²")

# 修正後の係数
new_factor = calculate_structural_volume_factor_fixed(**sample21)

print("\n【修正後】")
print(f"  材料係数: 1.5（木材）")
print(f"  全木造追加係数: 1.2")
print(f"  木材大断面追加係数: 1.15")
print(f"  構造体積係数: {new_factor:.3f}")
print(f"  推定コスト: {500000 * new_factor:,.0f} 円/m²")

# 増加率
increase_rate = new_factor / old_factor
print(f"\n係数の増加率: {increase_rate:.2f}倍")
print(f"推定される新コスト: {1220871 * increase_rate:,.0f} 円/m²")

print("\n" + "=" * 60)