#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web UIの動作テスト用スクリプト
"""

import subprocess
import time
import webbrowser
import sys

print("PSO Web UIデモを開始します...")
print("=" * 50)

# PSO.pyを実行（バックグラウンド）
print("1. PSO最適化を開始...")
cmd = [
    "/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd",
    "code/PSO.py",
    "--monitor",
    "--web"
]

# サブプロセスとして実行
process = subprocess.Popen(cmd)

# Web UIが起動するまで少し待機
print("2. Web UIの起動を待機中...")
time.sleep(3)

# ブラウザを自動的に開く
print("3. ブラウザでWeb UIを開きます...")
webbrowser.open("http://localhost:5000")

print("\n" + "=" * 50)
print("Web UIがブラウザで開かれました！")
print("最適化の進捗をリアルタイムで確認できます。")
print("\n終了するには Ctrl+C を押してください。")
print("=" * 50)

try:
    # プロセスの終了を待つ
    process.wait()
except KeyboardInterrupt:
    print("\n\n最適化を中断しました。")
    process.terminate()
    sys.exit(0)