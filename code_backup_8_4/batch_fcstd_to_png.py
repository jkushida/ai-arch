#!/usr/bin/env python3
"""fcstd_outputs内のすべてのFCStdファイルをPNGに変換するバッチ処理スクリプト"""

import os
import subprocess
import glob
import time
from pathlib import Path

# FreeCADとBlenderのパス
FREECAD_CMD = "/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd"
BLENDER = "/Applications/Blender.app/Contents/MacOS/blender"

# 入出力ディレクトリ
INPUT_DIR = "fcstd_outputs"
OUTPUT_DIR = "png_outputs"

# 出力ディレクトリの作成
os.makedirs(OUTPUT_DIR, exist_ok=True)

def process_fcstd_file(fcstd_path, output_base_name):
    """単一のFCStdファイルを処理してPNGを生成"""
    
    # STLエクスポート用の一時ディレクトリ
    temp_dir = f"temp_stl_{output_base_name}"
    os.makedirs(temp_dir, exist_ok=True)
    
    # FreeCADスクリプトの生成
    export_script = f'''
import FreeCAD
import Mesh
import Part
import os
import json

# FCStdファイルを開く
doc = FreeCAD.open("{fcstd_path}")

# エクスポート対象のオブジェクト
building_parts = ["Foundation", "Floor1", "Floor2", "Columns", "Walls", "RoofSlab", "Balcony", "Staircase", "AnalysisBuilding"]

# 材料情報を収集
material_info = {{}}

for name in building_parts[:-1]:  # AnalysisBuildingを除く
    obj = doc.getObject(name)
    if obj:
        # MaterialTypeプロパティを確認
        material_type = 0  # デフォルトはコンクリート
        if hasattr(obj, 'MaterialType'):
            material_type = obj.MaterialType
        material_info[name] = material_type

# 材料情報を保存
with open(os.path.join("{temp_dir}", "material_info.json"), "w") as f:
    json.dump(material_info, f)

# 各オブジェクトをSTLとしてエクスポート
for name in building_parts:
    obj = doc.getObject(name)
    if obj and hasattr(obj, 'Shape') and obj.Shape.Solids:
        mesh = Mesh.Mesh(obj.Shape.tessellate(0.3))
        filename = os.path.join("{temp_dir}", f"{{name}}.stl")
        mesh.write(filename)
        print(f"Exported: {{filename}}")

# ドキュメントを閉じる
FreeCAD.closeDocument(doc.Name)
'''
    
    # FreeCADスクリプトをファイルに保存
    export_script_path = f"export_{output_base_name}.py"
    with open(export_script_path, "w") as f:
        f.write(export_script)
    
    # FreeCADでSTLエクスポート実行
    print(f"📋 STLエクスポート中: {fcstd_path}")
    result = subprocess.run([FREECAD_CMD, export_script_path], capture_output=True, text=True)
    
    # エクスポートスクリプトを削除
    os.remove(export_script_path)
    
    # Blenderスクリプトの生成
    render_script = f'''
import bpy
import math
import mathutils
import os
import json

# 材料情報を読み込み
try:
    with open(os.path.join("{temp_dir}", "material_info.json"), "r") as f:
        material_info = json.load(f)
except:
    material_info = {{}}

# シーンクリア
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# カメラ追加
bpy.ops.object.camera_add()
camera = bpy.context.object
bpy.context.scene.camera = camera

# 各パーツをインポート
parts = ["Foundation", "Floor1", "Floor2", "Columns", "Walls", "RoofSlab", "Balcony", "Staircase", "AnalysisBuilding"]

# 材料色の定義
# コンクリート色（グレー系）
concrete_colors = {{
    'Foundation': (0.85, 0.85, 0.85),      # 基礎（明るいグレー）
    'Floor1': (0.9, 0.9, 0.9),             # 1階床（非常に明るいグレー）
    'Floor2': (0.88, 0.88, 0.88),          # 2階床（明るいグレー）
    'Columns': (0.8, 0.8, 0.8),            # 柱（グレー）
    'Walls': (0.92, 0.92, 0.92),           # 壁（ほぼ白）
    'RoofSlab': (0.75, 0.75, 0.75),        # 屋根（中間グレー）
    'Balcony': (0.82, 0.82, 0.82),         # バルコニー（明るめグレー）
    'Staircase': (0.7, 0.7, 0.7),          # 階段（暗めグレー）
    'AnalysisBuilding': (0.9, 0.85, 0.75)  # 統合版（ベージュ）
}}

# 木材色（茶色系）
wood_colors = {{
    'Foundation': (0.85, 0.7, 0.5),        # 基礎（薄い黄土色 - コンクリートのまま）
    'Floor1': (0.9, 0.75, 0.55),           # 1階床（明るいベージュ）
    'Floor2': (0.95, 0.8, 0.6),            # 2階床（非常に薄い茶色）
    'Columns': (0.8, 0.65, 0.45),          # 柱（明るい茶色）
    'Walls': (0.75, 0.55, 0.35),           # 壁（濃い茶色）
    'RoofSlab': (0.75, 0.6, 0.4),          # 屋根（明るめの茶色）
    'Balcony': (0.85, 0.75, 0.6),          # バルコニー（薄い茶色）
    'Staircase': (0.8, 0.7, 0.55),         # 階段（明るい茶色）
    'AnalysisBuilding': (0.9, 0.85, 0.75)  # 統合版（ベージュ）
}}

all_objects = []
for i, part_name in enumerate(parts):
    stl_file = os.path.join("{temp_dir}", f"{{part_name}}.stl")
    if os.path.exists(stl_file):
        try:
            bpy.ops.import_mesh.stl(filepath=stl_file)
            obj = bpy.context.selected_objects[0]
            
            # スケール調整（mm → Blender単位）
            if max(obj.dimensions) > 100:
                obj.scale = (0.001, 0.001, 0.001)
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.transform_apply(scale=True)
            
            # 材料タイプを取得（デフォルトはコンクリート）
            material_type = material_info.get(part_name, 0)
            
            # 基礎は常にコンクリート色、AnalysisBuildingは特別扱い
            if part_name == 'Foundation':
                color = concrete_colors[part_name]
            elif part_name == 'AnalysisBuilding':
                color = concrete_colors[part_name]
            elif material_type == 1:  # 木材
                color = wood_colors[part_name]
            else:  # コンクリート
                color = concrete_colors[part_name]
            
            # マテリアル設定
            mat = bpy.data.materials.new(f"Mat_{{part_name}}")
            mat.use_nodes = False
            mat.diffuse_color = color + (1.0,)
            obj.data.materials.append(mat)
            
            all_objects.append(obj)
            obj.select_set(False)
        except:
            print(f"Failed to import: {{stl_file}}")

# バウンディングボックスの計算
if all_objects:
    coords_all = []
    for obj in all_objects:
        bbox = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
        coords_all.extend(bbox)
    
    xs = [v.x for v in coords_all]
    ys = [v.y for v in coords_all]
    zs = [v.z for v in coords_all]
    
    center = (
        (min(xs) + max(xs)) / 2,
        (min(ys) + max(ys)) / 2,
        (min(zs) + max(zs)) / 2
    )
    max_dim = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    
    # カメラ位置設定（アイソメトリックビュー）
    distance = max_dim * 1.4  # 1.8から1.4に変更して建物を拡大
    angle_h = math.radians(135)
    angle_v = math.radians(30)
    
    x = center[0] + distance * math.sin(angle_h) * math.cos(angle_v)
    y = center[1] + distance * math.cos(angle_h) * math.cos(angle_v)
    z = center[2] + distance * math.sin(angle_v)
    
    camera.location = (x, y, z)
    
    # カメラの向きを中心に向ける
    direction = mathutils.Vector(center) - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    camera.data.lens = 28
    
    # レンダリング設定
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x = 640
    scene.render.resolution_y = 480
    
    shading = scene.display.shading
    shading.light = 'STUDIO'
    shading.color_type = 'MATERIAL'
    scene.render.film_transparent = True
    shading.show_shadows = True
    
    # 複数視点からレンダリング
    # ビュー1: アイソメトリック（南東）
    output_path = os.path.join("{OUTPUT_DIR}", "{output_base_name}_1.png")
    scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {{output_path}}")
    
    # ビュー2: 正面（南）
    camera.location = (center[0], center[1] - distance, center[2])
    direction = mathutils.Vector(center) - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    output_path = os.path.join("{OUTPUT_DIR}", "{output_base_name}_2.png")
    scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {{output_path}}")
    
    # ビュー3: 側面（東）
    camera.location = (center[0] + distance, center[1], center[2])
    direction = mathutils.Vector(center) - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    output_path = os.path.join("{OUTPUT_DIR}", "{output_base_name}_3.png")
    scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {{output_path}}")
    
    # ビュー4: アイソメトリック（北西）
    angle_h = math.radians(-45)
    angle_v = math.radians(30)
    x = center[0] + distance * math.sin(angle_h) * math.cos(angle_v)
    y = center[1] + distance * math.cos(angle_h) * math.cos(angle_v)
    z = center[2] + distance * math.sin(angle_v)
    camera.location = (x, y, z)
    direction = mathutils.Vector(center) - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    output_path = os.path.join("{OUTPUT_DIR}", "{output_base_name}_4.png")
    scene.render.filepath = output_path
    bpy.ops.render.render(write_still=True)
    print(f"Rendered: {{output_path}}")
'''
    
    # Blenderスクリプトをファイルに保存
    render_script_path = f"render_{output_base_name}.py"
    with open(render_script_path, "w") as f:
        f.write(render_script)
    
    # Blenderでレンダリング実行
    print(f"📸 レンダリング中: {output_base_name}_1〜4.png")
    cmd = [BLENDER, "-b", "-P", render_script_path]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # レンダリングスクリプトを削除
    os.remove(render_script_path)
    
    # 一時STLファイルを削除
    import shutil
    shutil.rmtree(temp_dir)
    
    print(f"✅ 完了: {output_base_name}_1〜4.png\n")

def main():
    """メイン処理"""
    print("🚀 FCStd → PNG バッチ変換開始")
    print(f"📁 入力ディレクトリ: {INPUT_DIR}")
    print(f"📁 出力ディレクトリ: {OUTPUT_DIR}\n")
    
    # FCStdファイルのリストを取得
    fcstd_files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.FCStd")))
    
    if not fcstd_files:
        print(f"❌ {INPUT_DIR}内にFCStdファイルが見つかりません")
        return
    
    print(f"📊 {len(fcstd_files)}個のファイルを処理します\n")
    
    # 各ファイルを処理
    start_time = time.time()
    success_count = 0
    
    for i, fcstd_path in enumerate(fcstd_files, 1):
        base_name = Path(fcstd_path).stem
        print(f"[{i}/{len(fcstd_files)}] 処理中: {base_name}")
        
        try:
            process_fcstd_file(fcstd_path, base_name)
            success_count += 1
        except Exception as e:
            print(f"❌ エラー: {base_name} - {str(e)}\n")
    
    # 処理時間の計算
    elapsed_time = time.time() - start_time
    minutes = int(elapsed_time // 60)
    seconds = int(elapsed_time % 60)
    
    print("\n" + "="*60)
    print(f"✅ バッチ処理完了！")
    print(f"📊 成功: {success_count}/{len(fcstd_files)} ファイル")
    print(f"🖼️  生成画像: {success_count * 4} 枚（各ファイル4視点）")
    print(f"⏱️  処理時間: {minutes}分{seconds}秒")
    print(f"📁 出力先: {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()