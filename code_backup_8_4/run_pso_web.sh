#!/bin/bash
# PSO.pyをWeb UI付きで実行するスクリプト

echo "========================================"
echo "PSO Web UIモニタリングを起動します"
echo "========================================"
echo ""

# 環境変数を設定（デフォルトで有効になっているが念のため）
export PSO_MONITOR=true
export PSO_WEB_UI=true
export PSO_LIVE_PLOT=false

# PSO.pyを実行
echo "🚀 PSO.pyを起動中..."
echo "📡 Web UIは http://localhost:5000 でアクセスできます"
echo ""

/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd PSO.py

echo ""
echo "========================================"
echo "実行が完了しました"
echo "========================================"