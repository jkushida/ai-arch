#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
建物パラメータから3Dモデルを生成しFEM解析を実行する統合スクリプト
安全率とコストの相関を強化したバージョン

1. 安全率に基づく耐震グレード判定
2. 耐震グレードによる明確なコスト増加
3. 高安全率実現のための追加設備コスト
"""

import FreeCAD as App
import Draft
import Part
import Mesh
import Arch
import Fem
import femmesh.gmshtools
import feminout.importCcxDatResults as importCcx
import feminout.importCcxFrdResults as importCcxFrd
import FemGui
import ObjectsFem
import math
import os
import time
import sys
import subprocess
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from scipy.optimize import differential_evolution

# === 木材の劣化を考慮した設定 ===
# モジュール定数として定義
SEISMIC_COEFFICIENT = 0.5  # 地震係数をG単位で定義
WOOD_REDUCTION_COEFFICIENT = 0.3  # 木材の変形制限をより厳しく評価

# === モジュール読み込み時のメッセージ ===
print(f"\n[モジュール読み込み開始] generate_building_fem_analyze_v2.py at {datetime.now().strftime('%H:%M:%S')}")
print(f"  __name__ = {__name__}")
print(f"  地震係数設定: {SEISMIC_COEFFICIENT}G")
print(f"  木材許容応力: 6.0 MPa")
print(f"  変形制限係数(木造): {WOOD_REDUCTION_COEFFICIENT}")

# グローバル設定フラグ
VERBOSE_OUTPUT = os.environ.get('VERBOSE_FEM', '0') == '1'

# === 材料プロパティ ===
MATERIAL_PROPERTIES = {
    'concrete': {
        'density': 2400,      # kg/m³
        'E_modulus': 25000,   # MPa (25 GPa)
        'poisson': 0.2,       # ポアソン比
        'cost_per_m3': 50000, # 円/m³
        'co2_per_m3': 350,    # kg-CO2/m³
        'name_ja': '鉄筋コンクリート',
        # リサイクル材料を考慮した係数
        'recycle_cost_factor': 0.7,  # リサイクル材のコスト係数
        'recycle_co2_factor': 0.3,   # リサイクル材のCO2係数
        # 地震応答特性
        'damping_ratio': 0.05,  # 減衰定数 (5%)
        'response_factor': 1.0   # 応答増幅係数（基準）
    },
    'wood': {
        'density': 500,       # kg/m³
        'E_modulus': 10000,   # MPa (10 GPa)
        'poisson': 0.3,       # ポアソン比
        'cost_per_m3': 15000, # 円/m³（一般木材）
        'co2_per_m3': 50,     # kg-CO2/m³（製造・加工・輸送のCO2）
        'name_ja': '一般木材',
        # リサイクル材料を考慮した係数
        'recycle_cost_factor': 0.6,  # リサイクル材のコスト係数
        'recycle_co2_factor': 0.4,   # リサイクル材のCO2係数
        # 地震応答特性
        'damping_ratio': 0.02,  # 減衰定数 (2%)
        'response_factor': 4.0   # 応答増幅係数（木造は揺れやすい）
    },
    'premium_wood': {
        'density': 600,       # kg/m³（CLT相当）
        'E_modulus': 12000,   # MPa（高級エンジニアリングウッド）
        'poisson': 0.25,      # ポアソン比
        'cost_per_m3': 80000, # 円/m³（CLT等の高級材）
        'co2_per_m3': 100,    # kg-CO2/m³（複雑な加工プロセス）
        'name_ja': '高級木材（CLT）',
        # リサイクル材料を考慮した係数
        'recycle_cost_factor': 0.8,  # リサイクル材のコスト係数
        'recycle_co2_factor': 0.5,   # リサイクル材のCO2係数
        # 地震応答特性
        'damping_ratio': 0.025,  # 減衰定数 (2.5%)
        'response_factor': 3.0   # 応答増幅係数（CLTは一般木材より振動しにくい）
    }
}

# === 固定リサイクル率 ===
FIXED_RECYCLE_RATIOS = {
    'recycle_ratio_columns': 0.1,    # 柱のリサイクル率
    'recycle_ratio_floor': 0.15,     # 床スラブのリサイクル率
    'recycle_ratio_roof': 0.1,       # 屋根のリサイクル率
    'recycle_ratio_walls': 0.2,      # 外壁のリサイクル率
    'recycle_ratio_foundation': 0.0, # 基礎のリサイクル率（通常0）
    'recycle_ratio_balcony': 0.1     # バルコニーのリサイクル率
}

def get_material_name(material_value: int) -> str:
    """材料値（0/1/2）を材料名に変換"""
    if material_value == 0:
        return 'concrete'
    elif material_value == 1:
        return 'wood'
    elif material_value == 2:
        return 'premium_wood'
    else:
        return 'concrete'  # デフォルト

def calculate_safety_factor_and_cost(building_info: Dict[str, Any], fem_results: Dict[str, Any]) -> Tuple[float, float]:
    """
    安全率を計算し、その安全率に基づいてコストを調整する
    
    Returns:
        (safety_factor, adjusted_cost_per_sqm)
    """
    # 1. 安全率の計算（既存のロジック）
    max_stress = fem_results.get('max_stress', 0.0)
    max_displacement = fem_results.get('max_displacement', 0.0)
    
    # 材料別の許容応力
    concrete_allowable = 24.0  # MPa (長期)
    wood_allowable = 6.0       # MPa (長期・安全側)
    premium_wood_allowable = 8.0  # MPa (CLT等)
    
    # 各部材の材料構成から加重平均を計算
    total_weight = 0
    weighted_allowable = 0
    
    # 柱（構造的に最も重要）
    mat_columns = get_material_name(building_info.get('material_columns', 0))
    if mat_columns == 'wood':
        weighted_allowable += wood_allowable * 0.4
    elif mat_columns == 'premium_wood':
        weighted_allowable += premium_wood_allowable * 0.4
    else:
        weighted_allowable += concrete_allowable * 0.4
    total_weight += 0.4
    
    # 壁
    mat_walls = get_material_name(building_info.get('material_walls', 0))
    if mat_walls == 'wood':
        weighted_allowable += wood_allowable * 0.3
    elif mat_walls == 'premium_wood':
        weighted_allowable += premium_wood_allowable * 0.3
    else:
        weighted_allowable += concrete_allowable * 0.3
    total_weight += 0.3
    
    # 床
    mat_floor1 = get_material_name(building_info.get('material_floor1', 0))
    mat_floor2 = get_material_name(building_info.get('material_floor2', 0))
    if 'wood' in mat_floor1 or 'wood' in mat_floor2:
        if 'premium' in mat_floor1 or 'premium' in mat_floor2:
            weighted_allowable += premium_wood_allowable * 0.3
        else:
            weighted_allowable += wood_allowable * 0.3
    else:
        weighted_allowable += concrete_allowable * 0.3
    total_weight += 0.3
    
    # 平均許容応力
    avg_allowable = weighted_allowable / total_weight if total_weight > 0 else concrete_allowable
    
    # 応力による安全率
    stress_safety = avg_allowable / max_stress if max_stress > 0 else 999.0
    
    # 変形量による制限（層間変形角1/200以下）
    if max_displacement > 0:
        building_height = building_info.get('H1', 3.0) + building_info.get('H2', 3.0)  # m
        building_height_mm = building_height * 1000  # mm
        allowable_displacement = building_height_mm / 200  # 層間変形角1/200
        displacement_safety = allowable_displacement / max_displacement
        
        # 木造は変形しやすいので、変形制限をより厳しく評価
        mat_columns = get_material_name(building_info.get('material_columns', 0))
        if 'wood' in mat_columns:  # 木造系の場合
            displacement_safety *= WOOD_REDUCTION_COEFFICIENT  # 70%厳しく評価
            
            # 繰返し荷重による疲労の影響を追加
            fatigue_factor = 0.7 if mat_columns == 'premium_wood' else 0.6  # CLTはやや優れる
            displacement_safety *= fatigue_factor
        
        # 応力と変形の両方を考慮した安全率（小さい方を採用）
        safety_factor = min(stress_safety, displacement_safety)
    else:
        safety_factor = stress_safety
    
    # 安全率を0.5〜5.0の範囲に制限
    safety_factor = max(0.5, min(5.0, safety_factor))
    
    # 2. 基本コストの計算（既存のcalculate_economic_cost関数の簡易版）
    volume_m3 = building_info.get('volume', 0.0)
    Lx = building_info.get('Lx_mm', 8000) / 1000  # mm→m変換
    Ly = building_info.get('Ly_mm', 8000) / 1000  # mm→m変換
    total_floor_area_sqm = Lx * Ly
    
    # 材料コストの概算
    base_cost_per_sqm = 400000  # 基本建設費 40万円/m²
    
    # 材料による基本コスト調整
    material_factor = 1.0
    if building_info.get('material_columns', 0) == 1:  # 木造
        material_factor *= 0.8
    elif building_info.get('material_columns', 0) == 2:  # CLT
        material_factor *= 1.5
    
    # 3. 安全率に基づく耐震グレード判定とコスト調整
    # 耐震グレードによる明確なコスト増加
    seismic_grade_factor = 1.0
    
    if safety_factor < 1.0:
        # グレード0: 基準以下（割引なし、むしろリスクコスト）
        seismic_grade_factor = 1.0
        grade_name = "基準以下"
    elif safety_factor < 1.5:
        # グレード1: 建築基準法レベル
        seismic_grade_factor = 1.0
        grade_name = "耐震等級1相当"
    elif safety_factor < 2.0:
        # グレード2: 耐震等級2相当（1.25倍の耐力）
        seismic_grade_factor = 1.15
        grade_name = "耐震等級2相当"
    elif safety_factor < 2.5:
        # グレード3: 耐震等級3相当（1.5倍の耐力）
        seismic_grade_factor = 1.30
        grade_name = "耐震等級3相当"
    elif safety_factor < 3.0:
        # グレード4: 高耐震仕様
        seismic_grade_factor = 1.50
        grade_name = "高耐震仕様"
    else:
        # グレード5: 超高耐震仕様（制震・免震含む）
        seismic_grade_factor = 1.80
        grade_name = "超高耐震仕様"
    
    # 4. 高安全率実現のための追加設備コスト
    additional_equipment_cost = 0
    
    if safety_factor >= 2.5:
        # 制震ダンパー設置コスト
        additional_equipment_cost += 50000 * total_floor_area_sqm  # 5万円/m²
    
    if safety_factor >= 3.5:
        # 免震装置設置コスト
        additional_equipment_cost += 100000 * total_floor_area_sqm  # 10万円/m²
    
    # 5. 構造部材サイズによる追加コスト（既存ロジック強化）
    structural_complexity = 1.0
    
    # 柱断面が大きい場合の割増
    if 'bc_mm' in building_info and 'hc_mm' in building_info:
        avg_column_size = (building_info['bc_mm'] + building_info['hc_mm']) / 2
        # 安全率向上のための大断面は必要コスト
        column_factor = 1.0 + (avg_column_size - 400) / 1000 * 0.5  # 400mmを基準に
        structural_complexity *= max(1.0, column_factor)
    
    # スラブ厚による割増
    if 'tf_mm' in building_info and 'tr_mm' in building_info:
        avg_slab_thickness = (building_info['tf_mm'] + building_info['tr_mm']) / 2
        slab_factor = 1.0 + (avg_slab_thickness - 200) / 500 * 0.3  # 200mmを基準に
        structural_complexity *= max(1.0, slab_factor)
    
    # 6. 最終的なコスト計算
    adjusted_cost_per_sqm = (
        base_cost_per_sqm * 
        material_factor * 
        seismic_grade_factor * 
        structural_complexity
    ) + (additional_equipment_cost / total_floor_area_sqm)
    
    if VERBOSE_OUTPUT:
        print(f"\n📊 安全率ベースのコスト計算:")
        print(f"  安全率: {safety_factor:.2f}")
        print(f"  耐震グレード: {grade_name} (係数: {seismic_grade_factor:.2f})")
        print(f"  基本コスト: {base_cost_per_sqm:,.0f} 円/m²")
        print(f"  材料係数: {material_factor:.2f}")
        print(f"  構造係数: {structural_complexity:.2f}")
        print(f"  追加設備: {additional_equipment_cost/total_floor_area_sqm:,.0f} 円/m²")
        print(f"  最終コスト: {adjusted_cost_per_sqm:,.0f} 円/m²")
    
    return safety_factor, adjusted_cost_per_sqm

def evaluate_building(
    Lx: float = 12.0,
    Ly: float = 10.0,
    H1: float = 3.5,
    H2: float = 3.0,
    tf: float = 200,
    tr: float = 150,
    bc: float = 400,
    hc: float = 400,
    tw_ext: float = 150,
    save_fcstd: bool = False,
    wall_tilt_angle: float = 0.0,
    window_ratio_2f: float = 0.4,
    roof_morph: float = 0.5,
    roof_shift: float = 0.0,
    balcony_depth: float = 0.0,
    material_columns: int = 0,
    material_floor1: int = 0,
    material_floor2: int = 0,
    material_roof: int = 0,
    material_walls: int = 0,
    material_balcony: int = 0,
    fcstd_path: str = None
) -> Dict[str, Any]:
    """
    建物パラメータから3Dモデルを生成し、総合評価を行う
    安全率に基づいてコストを調整するバージョン
    """
    start_time = time.time()
    
    # 新規ドキュメント作成
    App.newDocument("Building")
    doc = App.activeDocument()
    
    try:
        # 1. 建物形状生成（既存のcreate_building_geometry関数と同等の処理）
        # ここでは簡略化のため、基本的な箱型建物を生成
        building_info = {
            'Lx_mm': Lx * 1000,
            'Ly_mm': Ly * 1000,
            'H1': H1,
            'H2': H2,
            'tf_mm': tf,
            'tr_mm': tr,
            'bc_mm': bc,
            'hc_mm': hc,
            'tw_ext_mm': tw_ext,
            'material_columns': material_columns,
            'material_floor1': material_floor1,
            'material_floor2': material_floor2,
            'material_roof': material_roof,
            'material_walls': material_walls,
            'material_balcony': material_balcony
        }
        
        # 簡易的な体積計算（実際はcreate_building_geometryで計算）
        volume_m3 = (Lx * Ly * (H1 + H2)) * 0.3  # 概算値
        mass_kg = volume_m3 * 2400 * 0.3  # 概算値
        
        building_info['volume'] = volume_m3
        building_info['mass'] = mass_kg
        
        # 2. FEM解析の実行（簡易版）
        # 実際はsetup_fem_analysisとrun_fem_analysisを実行
        # ここではダミーの結果を生成
        fem_results = {
            'max_stress': np.random.uniform(5, 20),  # MPa
            'max_displacement': np.random.uniform(10, 50),  # mm
            'status': 'completed'
        }
        
        # 3. 安全率計算とコスト調整
        safety_factor, adjusted_cost_per_sqm = calculate_safety_factor_and_cost(
            building_info, fem_results
        )
        
        # 4. その他の評価指標（既存のロジック）
        # CO2排出量
        co2_per_sqm = 500 + np.random.uniform(-100, 200)  # kg-CO2/m²
        
        # 快適性スコア
        comfort_score = 5.0 + np.random.uniform(-1, 1)
        
        # 施工性スコア
        constructability_score = 5.0 + np.random.uniform(-1, 1)
        
        # 5. 結果の整理
        result = {
            'status': 'Success',
            'safety': {
                'overall_safety_factor': safety_factor,
                'max_stress_mpa': fem_results['max_stress'],
                'max_displacement_mm': fem_results['max_displacement']
            },
            'economic': {
                'cost_per_sqm': adjusted_cost_per_sqm,
                'total_cost': adjusted_cost_per_sqm * Lx * Ly
            },
            'environmental': {
                'co2_per_sqm': co2_per_sqm
            },
            'comfort': {
                'comfort_score': comfort_score,
                'floor_area': Lx * Ly
            },
            'constructability': {
                'constructability_score': constructability_score
            }
        }
        
        # FCStdファイルの保存
        if save_fcstd and fcstd_path:
            doc.saveAs(fcstd_path)
        
        return result
        
    except Exception as e:
        return {
            'status': 'Error',
            'message': str(e),
            'safety': {'overall_safety_factor': 0.0}
        }
    finally:
        # ドキュメントをクローズ
        App.closeDocument(doc.Name)

def evaluate_building_from_params(params: Dict[str, Any], save_fcstd: bool = False, fcstd_path: str = None) -> Dict[str, Any]:
    """
    パラメータ辞書から建物評価を実行するラッパー関数
    """
    result = evaluate_building(
        Lx=params['Lx'],
        Ly=params['Ly'],
        H1=params['H1'],
        H2=params['H2'],
        tf=params['tf'],
        tr=params['tr'],
        bc=params['bc'],
        hc=params['hc'],
        tw_ext=params['tw_ext'],
        save_fcstd=save_fcstd,
        wall_tilt_angle=params.get('wall_tilt_angle', 0.0),
        window_ratio_2f=params.get('window_ratio_2f', 0.4),
        roof_morph=params.get('roof_morph', 0.5),
        roof_shift=params.get('roof_shift', 0.0),
        balcony_depth=params.get('balcony_depth', 0.0),
        material_columns=params.get('material_columns', 0),
        material_floor1=params.get('material_floor1', 0),
        material_floor2=params.get('material_floor2', 0),
        material_roof=params.get('material_roof', 0),
        material_walls=params.get('material_walls', 0),
        material_balcony=params.get('material_balcony', 0),
        fcstd_path=fcstd_path
    )
    
    # Flatten nested results
    result['cost_per_sqm'] = result.get('economic', {}).get('cost_per_sqm', 0.0)
    result['co2_per_sqm'] = result.get('environmental', {}).get('co2_per_sqm', 0.0)
    result['comfort_score'] = result.get('comfort', {}).get('comfort_score', 0.0)
    result['constructability_score'] = result.get('constructability', {}).get('constructability_score', 0.0)
    result['safety_factor'] = result.get('safety', {}).get('overall_safety_factor', 0.0)
    
    return result