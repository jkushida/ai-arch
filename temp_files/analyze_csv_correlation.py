#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
既存のCSVファイルから安全率とコストの相関を分析
"""

import pandas as pd
import numpy as np

# CSVファイル読み込み
csv_file = 'production_freecad_random_fem_evaluation2.csv'

try:
    df = pd.read_csv(csv_file)
    print(f"CSVファイル読み込み成功: {csv_file}")
    print(f"総レコード数: {len(df)}")
    
    # 成功したサンプルのみ抽出
    df_success = df[df['evaluation_status'] == 'success'].copy()
    print(f"成功レコード数: {len(df_success)}")
    
    if len(df_success) > 1:
        # 相関計算
        corr_safety_cost = df_success['safety_factor'].corr(df_success['cost_per_sqm'])
        corr_co2_cost = df_success['co2_per_sqm'].corr(df_success['cost_per_sqm'])
        
        print("\n" + "=" * 60)
        print("📊 相関分析結果")
        print("=" * 60)
        print(f"安全率とコストの相関係数: {corr_safety_cost:.3f}")
        print(f"CO2とコストの相関係数: {corr_co2_cost:.3f}")
        
        # 材料別の平均値
        print("\n📊 材料別平均値")
        # 主に使用されている材料でグループ化（柱材料を基準）
        material_groups = df_success.groupby('material_columns').agg({
            'cost_per_sqm': 'mean',
            'safety_factor': 'mean',
            'co2_per_sqm': 'mean'
        })
        
        material_names = {0: 'コンクリート', 1: '木材', 2: 'CLT'}
        for mat_id, row in material_groups.iterrows():
            print(f"\n{material_names.get(mat_id, '不明')}:")
            print(f"  平均コスト: {row['cost_per_sqm']:,.0f} 円/m²")
            print(f"  平均安全率: {row['safety_factor']:.2f}")
            print(f"  平均CO2: {row['co2_per_sqm']:.0f} kg-CO2/m²")
        
    else:
        print("有効なデータが不足しています")
        
except FileNotFoundError:
    print(f"CSVファイルが見つかりません: {csv_file}")
except Exception as e:
    print(f"エラー: {e}")