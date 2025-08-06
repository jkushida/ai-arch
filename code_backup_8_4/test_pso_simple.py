#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PSOの簡易テスト（粒子数を減らして実行）
"""

import os
import sys

# 環境変数を設定
os.environ['PSO_MONITOR'] = 'true'
os.environ['PSO_WEB_UI'] = 'false'  # Web UIなしでテスト
os.environ['PSO_LIVE_PLOT'] = 'false'

# PSO設定を上書き
import PSO

# 粒子数と反復数を減らす
PSO.N_PARTICLES = 3  # 15 → 3
PSO.MAX_ITER = 2     # 20 → 2

print("=" * 60)
print("簡易PSO実行テスト")
print(f"粒子数: {PSO.N_PARTICLES}")
print(f"反復数: {PSO.MAX_ITER}")
print("=" * 60)

# PSO.pyのメイン部分を実行
if __name__ == "__main__":
    # PSO.pyのメインコードを実行
    exec(open('PSO.py').read())