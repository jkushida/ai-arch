#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PSO_light.py
軽量版PSO（デバッグ用）
- 粒子数を減らす
- FEM解析を省略するオプション
- Web UIなし
"""

import os
import sys

# 環境変数を設定
os.environ['PSO_MONITOR'] = 'true'
os.environ['PSO_WEB_UI'] = 'false'  # Web UIなし
os.environ['PSO_LIVE_PLOT'] = 'false'

# PSO設定を軽量化
N_PARTICLES = 3  # 15 → 3
MAX_ITER = 3     # 20 → 3

# タイムアウトを短く
EVALUATION_TIMEOUT = 30  # 20 → 30秒

# パラメータ範囲も小さく（建物サイズを控えめに）
PARAM_RANGES = {
    # 建物寸法（小さめに制限）
    "Lx": (8.0, 10.0),          # 建物幅: 8-10m
    "Ly": (8.0, 10.0),          # 建物奥行: 8-10m
    "H1": (2.6, 3.0),           # 1階高: 2.6-3.0m
    "H2": (2.6, 3.0),           # 2階高: 2.6-3.0m
    
    # 構造部材寸法
    "tf": (400, 500),           # 床スラブ厚
    "tr": (400, 500),           # 屋根スラブ厚
    "bc": (500, 600),           # 柱幅
    "hc": (500, 600),           # 柱高さ
    "tw_ext": (300, 400),       # 外壁厚
    
    # その他の設計パラメータ（シンプルに）
    "wall_tilt_angle": (0.0, 0.0),     # 壁傾斜なし
    "window_ratio_2f": (0.3, 0.3),     # 窓比率固定
    "roof_morph": (0.5, 0.5),          # 屋根形態固定
    "roof_shift": (0.0, 0.0),          # 屋根シフトなし
    "balcony_depth": (2.0, 2.0),       # バルコニー固定
    
    # 材料パラメータ（固定）
    "material_columns": (0.0, 0.0),      # コンクリート固定
    "material_floor1": (0.0, 0.0),       # コンクリート固定
    "material_floor2": (0.0, 0.0),       # コンクリート固定
    "material_roof": (0.0, 0.0),         # コンクリート固定
    "material_walls": (0.0, 0.0),        # コンクリート固定
    "material_balcony": (0.0, 0.0),      # コンクリート固定
}

print("=" * 60)
print("軽量版PSO実行")
print(f"粒子数: {N_PARTICLES}")
print(f"反復数: {MAX_ITER}")
print("建物サイズ: 8-10m x 8-10m")
print("材料: 全てコンクリート固定")
print("=" * 60)

# PSO.pyの内容を読み込んで実行
with open('PSO.py', 'r', encoding='utf-8') as f:
    pso_code = f.read()
    
# 設定を上書き
pso_code = pso_code.replace("N_PARTICLES = 15", f"N_PARTICLES = {N_PARTICLES}")
pso_code = pso_code.replace("MAX_ITER = 20", f"MAX_ITER = {MAX_ITER}")
pso_code = pso_code.replace("EVALUATION_TIMEOUT = 20", f"EVALUATION_TIMEOUT = {EVALUATION_TIMEOUT}")

# PARAM_RANGESの置き換え
import re
param_ranges_pattern = r'PARAM_RANGES = \{[^}]+\}'
param_ranges_str = f"PARAM_RANGES = {repr(PARAM_RANGES)}"
pso_code = re.sub(param_ranges_pattern, param_ranges_str, pso_code, flags=re.DOTALL)

# 実行
exec(pso_code)