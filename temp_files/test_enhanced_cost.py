#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
強化されたコスト計算のテスト
"""

# 構造体積係数の計算を再現
def calculate_structural_volume_factor(bc, hc, tf, tr, tw_ext, material_columns=0):
    # 各部材の「過大度」を評価
    column_oversize = max(1.0, (bc * hc) / (400 * 400))  # 400x400を標準とする
    floor_oversize = max(1.0, tf / 200)  # 200mmを標準とする
    roof_oversize = max(1.0, tr / 200)
    wall_oversize = max(1.0, tw_ext / 200)
    
    # 材料による補正
    if material_columns == 1:  # 木材
        material_factor = 1.2
    elif material_columns == 2:  # CLT
        material_factor = 0.9
    else:  # コンクリート
        material_factor = 1.0
    
    # 総合的な構造体積係数（二次関数的増加）
    structural_volume_factor = 1.0 + (
        0.5 * (column_oversize - 1.0) ** 2.0 +  # 柱の影響を最も重視
        0.3 * (floor_oversize - 1.0) ** 2.0 +   # 床版の影響
        0.15 * (roof_oversize - 1.0) ** 2.0 +   # 屋根の影響
        0.15 * (wall_oversize - 1.0) ** 2.0     # 壁の影響
    ) * material_factor
    
    # 大型構造の特殊工法コスト
    if bc * hc > 640000:  # 800x800を超える
        structural_volume_factor *= 1.2
    
    # 床版厚が500mmを超える場合
    if tf > 500 or tr > 500:
        structural_volume_factor *= 1.15
    
    return max(1.0, structural_volume_factor)

# 過剰カテゴリーのサンプルをテスト
print("強化されたコスト計算のテスト")
print("=" * 60)

# Sample21（安全率3.26、柱753x634）
sample21 = {
    'bc': 753, 'hc': 634, 'tf': 467, 'tr': 505, 'tw_ext': 315,
    'material_columns': 1  # 木材
}

# Sample37（安全率3.46、柱921x784）
sample37 = {
    'bc': 921, 'hc': 784, 'tf': 337, 'tr': 483, 'tw_ext': 326,
    'material_columns': 0  # コンクリート
}

# Sample32（安全率3.23、柱637x987）
sample32 = {
    'bc': 637, 'hc': 987, 'tf': 353, 'tr': 337, 'tw_ext': 398,
    'material_columns': 0  # コンクリート
}

# 比較用：標準的なサンプル（安全率1.5程度を想定）
standard = {
    'bc': 500, 'hc': 500, 'tf': 350, 'tr': 350, 'tw_ext': 300,
    'material_columns': 0
}

print("\n【構造体積係数の計算結果】")
for name, params in [("標準", standard), ("Sample21", sample21), 
                     ("Sample32", sample32), ("Sample37", sample37)]:
    factor = calculate_structural_volume_factor(**params)
    print(f"\n{name}:")
    print(f"  柱: {params['bc']}x{params['hc']}mm (面積: {params['bc']*params['hc']:,}mm²)")
    print(f"  床版厚: {params['tf']}mm, 屋根版厚: {params['tr']}mm")
    print(f"  構造体積係数: {factor:.3f}")
    
    # 推定コスト（基本コスト500,000円/m²と仮定）
    estimated_cost = 500000 * factor
    print(f"  推定コスト: {estimated_cost:,.0f} 円/m²")

print("\n" + "=" * 60)