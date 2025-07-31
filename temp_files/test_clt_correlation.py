#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLTオプション追加後のCO2-コスト相関確認テスト
"""

import os
import sys
import time
import subprocess

print("=" * 60)
print("CLTオプション追加後の相関テスト")
print("=" * 60)

# 少数サンプルで高速テスト
os.environ['TEST_N_SAMPLES'] = '30'

print("\n【実施内容】")
print("1. 高級木材（CLT）オプションを追加")
print("   - 高コスト（80,000円/m³）")
print("   - 低CO2（100 kg-CO2/m³）")
print("2. 材料選択を0/1/2の3値に拡張")
print("3. 出現確率：RC 50%, 木材 40%, CLT 10%")

print("\n【期待される効果】")
print("- 低CO2でも高コストの選択肢が増える")
print("- CO2-コスト相関が0.8程度に低下")

# FreeCADでsimple_random_batch2.pyを実行
print("\n実行開始...")
start_time = time.time()

try:
    # simple_random_batch2.pyを実行
    cmd = [
        "/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd",
        "simple_random_batch2.py"
    ]
    
    result = subprocess.run(cmd, 
                          cwd=os.path.dirname(os.path.abspath(__file__)),
                          capture_output=True,
                          text=True)
    
    if result.returncode != 0:
        print(f"エラー: {result.stderr}")
    else:
        # 結果を簡潔に表示
        lines = result.stdout.split('\n')
        for line in lines:
            if '✅' in line or '❌' in line or 'CO2' in line or '相関' in line:
                print(line)
    
except Exception as e:
    print(f"実行エラー: {e}")

elapsed = time.time() - start_time
print(f"\n実行時間: {elapsed:.1f}秒")

# CSVファイルを分析
print("\n結果分析中...")
try:
    import pandas as pd
    import numpy as np
    
    df = pd.read_csv('production_freecad_random_fem_evaluation2.csv')
    df_success = df[df['evaluation_status'] == 'success'].copy()
    
    if len(df_success) > 0:
        # 材料使用数を計算
        df_success['wood_count'] = (
            df_success['material_columns'] + 
            df_success['material_floor1'] + 
            df_success['material_floor2'] + 
            df_success['material_roof'] + 
            df_success['material_walls'] + 
            df_success['material_balcony']
        )
        
        # CLT使用数を計算
        clt_cols = ['material_columns', 'material_floor1', 'material_floor2', 
                    'material_roof', 'material_walls', 'material_balcony']
        df_success['clt_count'] = sum(df_success[col] == 2 for col in clt_cols)
        
        print(f"\n【分析結果】")
        print(f"成功サンプル数: {len(df_success)}")
        
        # 材料分布
        rc_only = len(df_success[(df_success['wood_count'] == 0)])
        wood_only = len(df_success[(df_success['wood_count'] > 0) & (df_success['clt_count'] == 0)])
        clt_used = len(df_success[df_success['clt_count'] > 0])
        
        print(f"\n材料分布:")
        print(f"  RC造のみ: {rc_only} ({rc_only/len(df_success)*100:.1f}%)")
        print(f"  木造のみ: {wood_only} ({wood_only/len(df_success)*100:.1f}%)")
        print(f"  CLT使用: {clt_used} ({clt_used/len(df_success)*100:.1f}%)")
        
        # CO2-コスト相関
        corr = df_success['cost_per_sqm'].corr(df_success['co2_per_sqm'])
        print(f"\nCO2-コスト相関係数: {corr:.3f}")
        print(f"目標値(0.8)との差: {abs(corr - 0.8):.3f}")
        
        # CLT使用建物の統計
        if clt_used > 0:
            clt_df = df_success[df_success['clt_count'] > 0]
            print(f"\nCLT使用建物の特性:")
            print(f"  平均コスト: {clt_df['cost_per_sqm'].mean():,.0f} 円/m²")
            print(f"  平均CO2: {clt_df['co2_per_sqm'].mean():.0f} kg-CO2/m²")
            print(f"  平均安全率: {clt_df['safety_factor'].mean():.2f}")
        
except Exception as e:
    print(f"分析エラー: {e}")

print("\n" + "=" * 60)