#!/usr/bin/env python3
"""FCStdファイルからPNG画像を生成（材料色対応版）"""

import os
import sys
import subprocess

# デフォルトのファイル名
if len(sys.argv) > 1:
    FCSTD_FILE = sys.argv[1]
else:
    FCSTD_FILE = "test_building.FCStd"

# 出力ファイル名のベース（拡張子なし）
output_base = os.path.splitext(FCSTD_FILE)[0]

FREECAD_CMD = "/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd"
BLENDER = "/Applications/Blender.app/Contents/MacOS/blender"

# 材料情報を含むSTLエクスポート
export_script = f'''
import FreeCAD
import Mesh
import Part
import json

doc = FreeCAD.open("{FCSTD_FILE}")

print("\\n🔍 各オブジェクトの詳細情報:")
print("-" * 80)

# エクスポート対象のパーツ
building_parts = ["Foundation", "Floor1", "Floor2", "Columns", "Walls", "RoofSlab", "Balcony", "Staircase"]

# 材料情報を収集
material_info = {{}}

for name in building_parts:
    obj = doc.getObject(name)
    if obj and hasattr(obj, 'Shape'):
        shape = obj.Shape
        bbox = shape.BoundBox
        print(f"\\n📦 {{name}}:")
        print(f"  位置: X={{bbox.XMin:.1f}}~{{bbox.XMax:.1f}}, Y={{bbox.YMin:.1f}}~{{bbox.YMax:.1f}}, Z={{bbox.ZMin:.1f}}~{{bbox.ZMax:.1f}}")
        print(f"  サイズ: {{bbox.XLength:.1f}} x {{bbox.YLength:.1f}} x {{bbox.ZLength:.1f}} mm")
        
        # MaterialTypeプロパティを確認
        material_type = 0  # デフォルトはコンクリート
        if hasattr(obj, 'MaterialType'):
            material_type = obj.MaterialType
            print(f"  材料: {{'木材' if material_type == 1 else 'コンクリート'}}")
        
        material_info[name] = material_type

# 材料情報を保存
with open("material_info.json", "w") as f:
    json.dump(material_info, f)

# すべてをエクスポート（個別に）
print("\\n📋 個別にSTLエクスポート:")
for name in building_parts:
    obj = doc.getObject(name)
    if obj and hasattr(obj, 'Shape') and obj.Shape.Solids:
        mesh = Mesh.Mesh(obj.Shape.tessellate(0.3))
        filename = f"{{name}}.stl"
        mesh.write(filename)
        print(f"✅ {{filename}} ({{mesh.CountFacets}} faces)")

# 統合版もエクスポート（FEM解析用のAnalysisBuildingがあれば使用）
analysis_obj = doc.getObject("AnalysisBuilding")
if analysis_obj and hasattr(analysis_obj, 'Shape'):
    mesh = Mesh.Mesh(analysis_obj.Shape.tessellate(0.3))
    mesh.write("building_complete.stl")
    print(f"\\n✅ 統合版: building_complete.stl ({{mesh.CountFacets}} faces)")
'''

# エクスポート実行
with open("export_with_materials.py", "w") as f:
    f.write(export_script)

print(f"🔍 {FCSTD_FILE}をエクスポート中...")
result = subprocess.run([FREECAD_CMD, "export_with_materials.py"], capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("エラー:", result.stderr)
os.remove("export_with_materials.py")

# 材料情報を読み込み
import json
try:
    with open("material_info.json", "r") as f:
        material_info = json.load(f)
except:
    material_info = {}

# Blenderでレンダリング（材料色対応）
render_script = f'''
import bpy
import math
import json
import os

# 材料情報を読み込み
try:
    with open("material_info.json", "r") as f:
        material_info = json.load(f)
except:
    material_info = {{}}

# シーンクリア
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# カメラ
bpy.ops.object.camera_add()
camera = bpy.context.object
bpy.context.scene.camera = camera

# 各パーツをインポート
parts = ["Foundation", "Floor1", "Floor2", "Columns", "Walls", "RoofSlab", "Balcony", "Staircase"]

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
    'Staircase': (0.7, 0.7, 0.7)           # 階段（暗めグレー）
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
    'Staircase': (0.8, 0.7, 0.55)          # 階段（明るい茶色）
}}

all_objects = []
for i, part_name in enumerate(parts):
    stl_file = f"{{part_name}}.stl"
    if os.path.exists(stl_file):
        try:
            bpy.ops.import_mesh.stl(filepath=stl_file)
            obj = bpy.context.selected_objects[0]
            
            # スケール調整
            if max(obj.dimensions) > 100:
                obj.scale = (0.001, 0.001, 0.001)
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.transform_apply(scale=True)
            
            # 材料タイプを取得（デフォルトはコンクリート）
            material_type = material_info.get(part_name, 0)
            
            # 基礎は常にコンクリート色
            if part_name == 'Foundation':
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
            material_name = "木材" if material_type == 1 and part_name != 'Foundation' else "コンクリート"
            print(f"✅ {{part_name}}: {{material_name}}, 色={{color}}")
            
            # 選択解除
            obj.select_set(False)
        except Exception as e:
            print(f"❌ {{part_name}} エラー: {{e}}")

import mathutils

# ワールド座標系でのバウンディングボックスを収集
coords_all = []
for obj in all_objects:
    bbox = [obj.matrix_world @ mathutils.Vector(corner) for corner in obj.bound_box]
    coords_all.extend(bbox)

if coords_all:
    xs = [v.x for v in coords_all]
    ys = [v.y for v in coords_all]
    zs = [v.z for v in coords_all]
    
    center = (
        (min(xs) + max(xs)) / 2,
        (min(ys) + max(ys)) / 2,
        (min(zs) + max(zs)) / 2
    )
    max_dim = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
    
    distance = max_dim * 1.4
    angle_h = math.radians(135)
    angle_v = math.radians(30)
    
    x = center[0] + distance * math.sin(angle_h) * math.cos(angle_v)
    y = center[1] + distance * math.cos(angle_h) * math.cos(angle_v)
    z = center[2] + distance * math.sin(angle_v)
    
    camera.location = (x, y, z)
    
    direction = mathutils.Vector(center) - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    camera.data.lens = 28
    
    # レンダリング設定
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 960
    
    shading = scene.display.shading
    shading.light = 'STUDIO'
    shading.color_type = 'MATERIAL'
    scene.render.film_transparent = True
    shading.show_shadows = True
    
    # レンダリング
    scene.render.filepath = "{output_base}_angle1.png"
    bpy.ops.render.render(write_still=True)
    print(f"✅ {output_base}_angle1.png")
    
    # 別視点の追加レンダリング
    
    # 正面ビュー（南）
    camera.location = (center[0], center[1] - distance, center[2])
    direction = mathutils.Vector(center) - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    scene.render.filepath = "{output_base}_angle2.png"
    bpy.ops.render.render(write_still=True)
    print(f"✅ {output_base}_angle2.png")
    
    # 側面ビュー（東）- 少し上から見下ろす角度
    camera.location = (center[0] + distance, center[1], center[2] + distance * 0.2)
    direction = mathutils.Vector(center) - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    scene.render.filepath = "{output_base}_angle3.png"
    bpy.ops.render.render(write_still=True)
    print(f"✅ {output_base}_angle3.png")
    
    # 斜めビュー（北西）
    angle_h = math.radians(-45)
    angle_v = math.radians(30)
    x = center[0] + distance * math.sin(angle_h) * math.cos(angle_v)
    y = center[1] + distance * math.cos(angle_h) * math.cos(angle_v)
    z = center[2] + distance * math.sin(angle_v)
    camera.location = (x, y, z)
    direction = mathutils.Vector(center) - camera.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    camera.rotation_euler = rot_quat.to_euler()
    scene.render.filepath = "{output_base}_angle4.png"
    bpy.ops.render.render(write_still=True)
    print(f"✅ {output_base}_angle4.png")
'''

with open("render_with_materials.py", "w") as f:
    f.write(render_script)

print("\n📸 材料色を反映してレンダリング中...")
cmd = [BLENDER, "-b", "-P", "render_with_materials.py"]
result = subprocess.run(cmd, capture_output=True, text=True)

for line in result.stdout.split('\n'):
    if "✅" in line or "❌" in line:
        print(line)

# クリーンアップ
os.remove("render_with_materials.py")
if os.path.exists("material_info.json"):
    os.remove("material_info.json")

# STLファイルも削除
for part in ["Foundation", "Floor1", "Floor2", "Columns", "Walls", "RoofSlab", "Balcony", "Staircase", "building_complete"]:
    stl_file = f"{part}.stl"
    if os.path.exists(stl_file):
        os.remove(stl_file)

print(f"\n✅ 完了！ 出力ファイル: {output_base}_angle1-4.png")