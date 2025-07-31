#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FreeCADで開いたドキュメントに材料の色を適用するスクリプト

使い方:
1. FreeCADでファイルを開く
2. FreeCADのPythonコンソールでこのスクリプトを実行:
   exec(open('/path/to/apply_material_colors.py').read())
"""

import FreeCAD as App
import FreeCADGui as Gui

def apply_material_colors(doc=None):
    """開いているドキュメントのオブジェクトに色を適用"""
    
    if doc is None:
        doc = App.ActiveDocument
    
    if doc is None:
        print("エラー: アクティブなドキュメントがありません")
        return
    
    print(f"ドキュメント '{doc.Name}' の色を適用中...")
    
    # 各オブジェクトをチェックして色を適用
    color_applied = 0
    for obj in doc.Objects:
        if hasattr(obj, 'ShapeColor') and hasattr(obj, 'ViewObject'):
            if obj.ViewObject is not None:
                try:
                    # カスタムプロパティから色を取得
                    color = obj.ShapeColor
                    # ViewObjectに適用
                    obj.ViewObject.ShapeColor = color
                    obj.ViewObject.Transparency = 0
                    print(f"✅ {obj.Label}: 色を適用 RGB{color}")
                    color_applied += 1
                except Exception as e:
                    print(f"⚠️ {obj.Label}: 色の適用に失敗 - {e}")
    
    print(f"\n完了: {color_applied} 個のオブジェクトに色を適用しました")
    
    # ビューを更新
    if hasattr(Gui, 'ActiveDocument') and Gui.ActiveDocument:
        Gui.ActiveDocument.ActiveView.fitAll()
        print("ビューを更新しました")

# 実行
if __name__ == "__main__" or __name__ == "__console__":
    apply_material_colors()