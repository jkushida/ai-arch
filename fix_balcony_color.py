#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_balcony_color.py
FreeCADで開いた建物モデルのバルコニーを茶色に変更するスクリプト
FreeCADのPythonコンソールで実行してください
"""

import FreeCAD as App

# アクティブなドキュメントを取得
doc = App.ActiveDocument

if doc:
    # バルコニーオブジェクトを探す
    balcony_obj = None
    
    # オブジェクト名で探す
    if hasattr(doc, 'Balcony'):
        balcony_obj = doc.Balcony
    else:
        # ラベルで探す
        for obj in doc.Objects:
            if 'Balcony' in obj.Label or 'バルコニー' in obj.Label:
                balcony_obj = obj
                break
    
    if balcony_obj:
        # 木材の茶色（少し明るめ）
        wood_color = (0.6, 0.4, 0.25)  # 明るい茶色
        
        # ViewObjectが存在する場合
        if hasattr(balcony_obj, 'ViewObject') and balcony_obj.ViewObject:
            # ShapeColorを設定
            balcony_obj.ViewObject.ShapeColor = wood_color
            
            # Shape Appearanceも設定（FreeCAD 0.21以降）
            if hasattr(balcony_obj.ViewObject, 'ShapeAppearance'):
                balcony_obj.ViewObject.ShapeAppearance = wood_color
            
            # 透明度を0に（不透明）
            balcony_obj.ViewObject.Transparency = 0
            
            print(f"✅ バルコニーの色を茶色に変更しました: RGB{wood_color}")
            
            # 他の木材パーツも確認して色を変更
            wood_parts = {
                'Floor2': (0.55, 0.35, 0.2),      # 2階床
                'Walls': (0.6, 0.4, 0.25),        # 外壁（明るい茶色）
                'RoofSlab': (0.5, 0.3, 0.15),     # 屋根（濃い茶色）
            }
            
            for part_name, color in wood_parts.items():
                if hasattr(doc, part_name):
                    part = getattr(doc, part_name)
                    if hasattr(part, 'ViewObject') and part.ViewObject:
                        part.ViewObject.ShapeColor = color
                        if hasattr(part.ViewObject, 'ShapeAppearance'):
                            part.ViewObject.ShapeAppearance = color
                        part.ViewObject.Transparency = 0
                        print(f"✅ {part_name}の色も更新しました: RGB{color}")
        else:
            print("⚠️ バルコニーのViewObjectが見つかりません")
    else:
        print("⚠️ バルコニーオブジェクトが見つかりません")
    
    # ドキュメントを再計算
    doc.recompute()
    print("\n✅ 色の変更が完了しました。表示を更新してください。")
    
else:
    print("❌ アクティブなドキュメントがありません")