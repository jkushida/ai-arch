#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fix_gui_colors.py
FreeCAD GUIで開いたモデルの色を修正するスクリプト
FreeCADのPythonコンソールで実行してください
"""

import FreeCAD as App
import FreeCADGui as Gui

def get_material_from_properties(obj):
    """オブジェクトのプロパティから材料情報を取得（0=コンクリート、1=木材）"""
    # ViewColorプロパティをチェック（保存された色情報）
    if hasattr(obj, 'ViewColor') and obj.ViewColor:
        r, g, b = obj.ViewColor[0], obj.ViewColor[1], obj.ViewColor[2]
        # 木材色に近いかチェック
        if abs(r - 0.55) < 0.1 and abs(g - 0.35) < 0.1 and abs(b - 0.2) < 0.1:
            return 1  # 木材
    
    # DiffuseColorプロパティをチェック
    if hasattr(obj, 'DiffuseColor') and obj.DiffuseColor and len(obj.DiffuseColor) > 0:
        color = obj.DiffuseColor[0][:3]
        r, g, b = color[0], color[1], color[2]
        # 木材色に近いかチェック
        if abs(r - 0.55) < 0.1 and abs(g - 0.35) < 0.1 and abs(b - 0.2) < 0.1:
            return 1  # 木材
    
    # カスタムプロパティ（材料タイプ）をチェック
    if hasattr(obj, 'MaterialType'):
        return obj.MaterialType
    
    return None  # 不明

def fix_object_colors():
    """全オブジェクトの色を修正"""
    
    doc = App.ActiveDocument
    if not doc:
        print("❌ アクティブなドキュメントがありません")
        return
    
    # 材料色の定義
    # 木材色（パーツごとに微妙に変える - さらに明るめの茶色）
    wood_colors = {
        'Foundation': (0.85, 0.7, 0.5),     # 基礎（薄い黄土色）
        'Floor1': (0.9, 0.75, 0.55),        # 1階床（明るいベージュ）
        'Floor2': (0.95, 0.8, 0.6),         # 2階床（非常に薄い茶色）
        'Columns': (0.8, 0.65, 0.45),       # 柱（明るい茶色）
        'Walls': (0.75, 0.55, 0.35),        # 壁（濃い茶色）
        'RoofSlab': (0.75, 0.6, 0.4),       # 屋根（明るめの茶色）
        'Balcony': (0.85, 0.75, 0.6),       # バルコニー（薄い茶色）
        'Staircase': (0.8, 0.7, 0.55)       # 階段（明るい茶色）
    }
    concrete_color = (0.9, 0.9, 0.9)  # コンクリート（非常に明るいグレー）
    
    # 修正対象のオブジェクト
    building_parts = ['Foundation', 'Floor1', 'Floor2', 'Columns', 'Walls', 'RoofSlab', 'Balcony', 'Staircase']
    
    # デフォルト材料設定（材料情報が見つからない場合は全てコンクリート）
    default_material = 0  # 0: コンクリート
    
    print("=== 材料色適用開始 ===")
    print("プロパティから材料情報を読み取っています...")
    
    applied_count = 0
    wood_count = 0
    concrete_count = 0
    unknown_count = 0
    
    # 全オブジェクトを処理
    for obj in doc.Objects:
        # ViewObjectが存在する場合のみ処理
        if hasattr(obj, 'ViewObject') and obj.ViewObject:
            # 建物パーツの場合
            if obj.Label in building_parts:
                # 可視化
                if hasattr(obj.ViewObject, 'Visibility'):
                    obj.ViewObject.Visibility = True
                
                # プロパティから材料を判定
                material = get_material_from_properties(obj)
                
                # 材料が不明な場合はコンクリートとして扱う
                if material is None:
                    material = default_material
                    print(f"❓ {obj.Label}: 材料情報が見つからないため、コンクリートとして扱います")
                    unknown_count += 1
                
                # 材料に応じて色を設定
                try:
                    if material == 1:  # 木材
                        # パーツごとに異なる木材色を使用
                        color = wood_colors.get(obj.Label, (0.75, 0.55, 0.35))  # デフォルト木材色
                        material_name = '木材'
                        wood_count += 1
                    else:  # コンクリート
                        color = concrete_color
                        material_name = 'コンクリート'
                        concrete_count += 1
                    
                    # 色を設定
                    obj.ViewObject.ShapeColor = color
                    obj.ViewObject.Transparency = 0
                    
                    # ShapeMaterialを作成して設定
                    if hasattr(App, 'Material'):
                        mat = App.Material()
                        mat.DiffuseColor = color + (1.0,)  # RGBA形式
                        mat.AmbientColor = tuple(c * 0.3 for c in color) + (1.0,)
                        mat.SpecularColor = (0.5, 0.5, 0.5, 1.0)
                        mat.EmissiveColor = (0.0, 0.0, 0.0, 1.0)
                        mat.Shininess = 0.2
                        mat.Transparency = 0.0
                        
                        # ShapeMaterialプロパティとして設定
                        if hasattr(obj.ViewObject, 'ShapeMaterial'):
                            obj.ViewObject.ShapeMaterial = mat
                    
                    # DisplayModeをFlat Linesに設定（面の色＋エッジ線）
                    if hasattr(obj.ViewObject, 'DisplayMode'):
                        try:
                            obj.ViewObject.DisplayMode = "Flat Lines"
                        except:
                            pass
                    
                    # LineWidthは残す（線を少し太くする）
                    if hasattr(obj.ViewObject, 'LineWidth'):
                        obj.ViewObject.LineWidth = 2.0  # 線を太くする
                    
                    # DrawStyleは残す
                    if hasattr(obj.ViewObject, 'DrawStyle'):
                        try:
                            obj.ViewObject.DrawStyle = "Solid"  # 実線
                        except:
                            pass
                    
                    # OverrideMaterialを有効にする（FreeCAD 0.21以降）
                    if hasattr(obj.ViewObject, 'OverrideMaterial'):
                        obj.ViewObject.OverrideMaterial = True
                    
                    print(f"✅ {obj.Label}: {material_name}色を適用 RGB{color}")
                    applied_count += 1
                    
                except Exception as e:
                    print(f"⚠️ {obj.Label}: 色の適用に失敗 - {str(e)}")
    
    # ドキュメントを再計算
    doc.recompute()
    
    # GUIを更新
    if hasattr(Gui, 'updateGui'):
        Gui.updateGui()
    
    # ビューを調整（全体表示＆アイソメトリック）
    try:
        Gui.SendMsgToActiveView("ViewFit")
        Gui.activeDocument().activeView().viewIsometric()
        print("\n✅ ビューを調整しました（全体表示・アイソメトリック）")
    except Exception as e:
        print(f"\n⚠️ ビュー調整中にエラー: {str(e)}")
    
    print(f"\n=== 処理完了 ===")
    print(f"✅ {applied_count} 個のオブジェクトの色を適用しました")
    print(f"📊 内訳: 木材 {wood_count}個、コンクリート {concrete_count}個")
    if unknown_count > 0:
        print(f"⚠️  {unknown_count}個のオブジェクトは材料情報が見つからず、コンクリートとして扱いました")
    print("\n💡 ヒント: 材料情報が正しく保存されていない場合は、")
    print("   generate_building_fem_analyze.pyで建物を再生成してください")

# スクリプトを実行
if __name__ == "__main__":
    fix_object_colors()