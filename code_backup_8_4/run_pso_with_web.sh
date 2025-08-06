#!/bin/bash
# PSO.pyをWeb UI付きで実行するスクリプト

echo "PSO.pyをWeb UIモニタリング付きで起動します..."
echo "================================================"

# 1行で実行
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd PSO.py --monitor --web

echo "================================================"
echo "実行が完了しました。"