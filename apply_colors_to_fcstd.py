#!/usr/bin/env python3
"""
FCStdファイルに自動的に色を適用して保存するスクリプト
使用方法:
    /Applications/FreeCAD.app/Contents/MacOS/FreeCAD --run-script apply_colors_to_fcstd.py -- input.FCStd [output.FCStd]
"""

import sys
import os
import FreeCAD
import FreeCADGui

# コマンドライン引数の処理
if len(sys.argv) < 2:
    print("使用方法: FreeCAD --run-script apply_colors_to_fcstd.py -- input.FCStd [output.FCStd]")
    sys.exit(1)

# 引数の取得（FreeCADの引数処理の特殊性に対応）
input_file = None
output_file = None

# "--" 以降の引数を探す
try:
    dash_index = sys.argv.index("--")
    if dash_index + 1 < len(sys.argv):
        input_file = sys.argv[dash_index + 1]
        if dash_index + 2 < len(sys.argv):
            output_file = sys.argv[dash_index + 2]
        else:
            # 出力ファイル名が指定されていない場合は、入力ファイル名に_coloredを追加
            base, ext = os.path.splitext(input_file)
            output_file = f"{base}_colored{ext}"
except ValueError:
    # "--" が見つからない場合は最後の引数を使用
    input_file = sys.argv[-1]
    base, ext = os.path.splitext(input_file)
    output_file = f"{base}_colored{ext}"

print(f"入力ファイル: {input_file}")
print(f"出力ファイル: {output_file}")

# FCStdファイルを開く
try:
    doc = FreeCAD.open(input_file)
    print(f"✅ ファイルを開きました: {input_file}")
except Exception as e:
    print(f"❌ ファイルを開けませんでした: {e}")
    sys.exit(1)

# fix_gui_colors.pyの内容を実行
fix_colors_script = """
# 材料に基づいてオブジェクトの色を修正するスクリプト

def get_material_from_properties(obj):
    '''オブジェクトのプロパティから材料タイプを取得'''
    if hasattr(obj, 'MaterialType'):
        return obj.MaterialType
    
    # MaterialTypeプロパティがない場合は他のプロパティを確認
    if hasattr(obj, 'Label'):
        label = obj.Label.lower()
        if 'wood' in label or '木' in label:
            return 1
        elif 'concrete' in label or 'コンクリート' in label:
            return 0
    
    return None

def fix_object_colors():
    '''アクティブドキュメントのオブジェクトに材料色を適用'''
    
    # 木材色の定義（パーツごとに微妙に異なる色）
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
    
    # 各オブジェクトの材料を確認
    material_info = {}
    for obj_name in building_parts:
        obj = FreeCAD.ActiveDocument.getObject(obj_name)
        if obj:
            material = get_material_from_properties(obj)
            if material is not None:
                material_info[obj_name] = material
                material_name = "木材" if material == 1 else "コンクリート"
                print(f"  {obj_name}: {material_name}")
    
    applied_count = 0
    wood_count = 0
    concrete_count = 0
    unknown_count = 0
    
    for obj_name in building_parts:
        obj = FreeCAD.ActiveDocument.getObject(obj_name)
        if obj:
            if hasattr(obj, 'ViewObject') and obj.ViewObject is not None:
                
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
                        color = wood_colors.get(obj.Label, wood_colors.get('Walls'))
                        wood_count += 1
                    else:  # コンクリート
                        color = concrete_color
                        concrete_count += 1
                    
                    # 色を設定
                    obj.ViewObject.ShapeColor = color
                    
                    # 透明度を0に設定（不透明）
                    if hasattr(obj.ViewObject, 'Transparency'):
                        obj.ViewObject.Transparency = 0
                    
                    # DisplayModeをFlat Linesに設定（面の色＋エッジ線）
                    if hasattr(obj.ViewObject, 'DisplayMode'):
                        try:
                            obj.ViewObject.DisplayMode = "Flat Lines"
                        except:
                            pass
                    
                    applied_count += 1
                    material_name = "木材" if material == 1 else "コンクリート"
                    print(f"✅ {obj.Label}: {material_name}色を適用 RGB{color}")
                    
                except Exception as e:
                    print(f"⚠️ {obj.Label}: 色の適用中にエラー: {str(e)}")
            else:
                print(f"⚠️ {obj_name}: ViewObjectが見つかりません")
        else:
            print(f"❌ {obj_name}: オブジェクトが見つかりません")
    
    # ビューの調整
    try:
        FreeCADGui.ActiveDocument.ActiveView.viewIsometric()
        FreeCADGui.ActiveDocument.ActiveView.fitAll()
        print("\\nビューを調整しました（アイソメトリック表示）")
    except Exception as e:
        print(f"\\n⚠️ ビュー調整中にエラー: {str(e)}")
    
    print(f"\\n=== 処理完了 ===")
    print(f"✅ {applied_count} 個のオブジェクトの色を適用しました")
    print(f"📊 内訳: 木材 {wood_count}個、コンクリート {concrete_count}個")
    if unknown_count > 0:
        print(f"⚠️  {unknown_count}個のオブジェクトは材料情報が見つからず、コンクリートとして扱いました")

# 実行
fix_object_colors()
"""

# fix_gui_colors.pyの内容を実行
try:
    exec(fix_colors_script)
    print("\n✅ 色付け処理が完了しました")
except Exception as e:
    print(f"\n❌ 色付け処理中にエラーが発生しました: {e}")
    import traceback
    traceback.print_exc()

# ドキュメントを保存
try:
    doc.saveAs(output_file)
    print(f"\n✅ ファイルを保存しました: {output_file}")
except Exception as e:
    print(f"\n❌ ファイルの保存に失敗しました: {e}")

# FreeCADを終了（オプション）
# コメントアウトを外すと処理後に自動的にFreeCADが終了します
# print("\nFreeCADを終了します...")
# FreeCADGui.getMainWindow().close()