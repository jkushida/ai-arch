#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
コスト計算の修正案
"""

def calculate_structural_volume_factor(building_info):
    """
    構造体積に基づくコスト増加係数を計算
    大きな構造部材は特殊工法・運搬・施工の難易度が増すため、
    体積に対して二次関数的にコストが増加する
    """
    # 構造部材のサイズ
    bc = building_info.get('bc_mm', 600)
    hc = building_info.get('hc_mm', 600)
    tf = building_info.get('tf_mm', 300)
    tr = building_info.get('tr_mm', 300)
    tw_ext = building_info.get('tw_ext_mm', 300)
    
    # 各部材の「過大度」を評価
    # 標準サイズを基準に、どれだけ大きいかを評価
    column_oversize = max(1.0, (bc * hc) / (400 * 400))  # 400x400を標準とする
    floor_oversize = max(1.0, tf / 200)  # 200mmを標準とする
    roof_oversize = max(1.0, tr / 200)
    wall_oversize = max(1.0, tw_ext / 200)
    
    # 材料による補正
    mat_col = building_info.get('material_columns', 0)
    if mat_col == 1:  # 木材
        # 木材は大断面になると特殊材料・工法が必要
        material_factor = 1.2
    elif mat_col == 2:  # CLT
        # CLTは元々高価だが、大断面でもコスト増加は緩やか
        material_factor = 0.9
    else:  # コンクリート
        # コンクリートは標準
        material_factor = 1.0
    
    # 総合的な構造体積係数（二次関数的増加）
    # 1.0を基準として、構造が大きくなるほど急激に増加
    volume_factor = 1.0 + (
        0.3 * (column_oversize - 1.0) ** 1.5 +  # 柱の影響を最も重視
        0.2 * (floor_oversize - 1.0) ** 1.5 +
        0.1 * (roof_oversize - 1.0) ** 1.5 +
        0.1 * (wall_oversize - 1.0) ** 1.5
    ) * material_factor
    
    # 最小値を1.0に制限
    return max(1.0, volume_factor)

def calculate_strength_quality_factor(safety_factor):
    """
    高強度を実現するための品質管理コスト
    安全率が高いほど、より厳密な品質管理と高強度材料が必要
    """
    if safety_factor < 1.5:
        return 1.0
    elif safety_factor < 2.0:
        return 1.05
    elif safety_factor < 2.5:
        return 1.10
    elif safety_factor < 3.0:
        return 1.20
    else:
        # 安全率3.0以上は特殊な高強度設計
        return 1.30 + (safety_factor - 3.0) * 0.15

# 修正後のコスト計算の主要部分
def calculate_revised_cost(building_info, safety_factor):
    """
    修正版のコスト計算
    """
    # 既存の基本コスト計算（仮定）
    base_cost = 500000  # 円/m²
    
    # 構造体積係数
    volume_factor = calculate_structural_volume_factor(building_info)
    
    # 強度品質係数（ただし循環依存を避けるため、最小限に）
    # 実際の強度は構造設計の結果であり、コストの原因ではない
    # しかし、高強度材料の使用はコストに影響する
    strength_factor = 1.0  # 一旦無効化して独立性を保つ
    
    # 最終コスト
    final_cost_per_sqm = base_cost * volume_factor * strength_factor
    
    return final_cost_per_sqm

# テスト
if __name__ == "__main__":
    # Sample21のデータ
    sample21 = {
        'bc_mm': 753,
        'hc_mm': 634,
        'tf_mm': 467,
        'tr_mm': 505,
        'tw_ext_mm': 315,
        'material_columns': 1  # 木材
    }
    
    # Sample37のデータ
    sample37 = {
        'bc_mm': 921,
        'hc_mm': 784,
        'tf_mm': 337,
        'tr_mm': 483,
        'tw_ext_mm': 326,
        'material_columns': 0  # コンクリート
    }
    
    factor21 = calculate_structural_volume_factor(sample21)
    factor37 = calculate_structural_volume_factor(sample37)
    
    print(f"Sample21 構造体積係数: {factor21:.3f}")
    print(f"Sample37 構造体積係数: {factor37:.3f}")
    
    # 修正後の推定コスト
    revised_cost21 = calculate_revised_cost(sample21, 3.255)
    revised_cost37 = calculate_revised_cost(sample37, 3.505)
    
    print(f"\nSample21 修正後コスト: {revised_cost21:,.0f} 円/m²")
    print(f"Sample37 修正後コスト: {revised_cost37:,.0f} 円/m²")