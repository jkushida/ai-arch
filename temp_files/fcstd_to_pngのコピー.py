#!/usr/bin/env python3
"""各オブジェクトの位置とサイズを確認してSTLエクスポート"""

import os
import subprocess

FCSTD_FILE = "piloti_building_fem_analysis.FCStd"
FREECAD_CMD = "/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd"
BLENDER = "/Applications/Blender.app/Contents/MacOS/blender"

# 詳細な診断とエクスポート
diagnosis_script = f'''
import FreeCAD
import Mesh
import Part

doc = FreeCAD.open("{FCSTD_FILE}")

print("\\n🔍 各オブジェクトの詳細情報:")
print("-" * 80)

building_parts = ["Staircase", "RoofSlab", "AnalysisBuilding", "Foundation", "Floor2"]

for name in building_parts:
    obj = doc.getObject(name)
    if obj and hasattr(obj, 'Shape'):
        shape = obj.Shape
        bbox = shape.BoundBox
        print(f"\\n📦 {{name}}:")
        print(f"  位置: X={{bbox.XMin:.1f}}~{{bbox.XMax:.1f}}, Y={{bbox.YMin:.1f}}~{{bbox.YMax:.1f}}, Z={{bbox.ZMin:.1f}}~{{bbox.ZMax:.1f}}")
        print(f"  サイズ: {{bbox.XLength:.1f}} x {{bbox.YLength:.1f}} x {{bbox.ZLength:.1f}} mm")
        print(f"  中心: ({{bbox.Center.x:.1f}}, {{bbox.Center.y:.1f}}, {{bbox.Center.z:.1f}})")
        print(f"  ソリッド数: {{len(shape.Solids)}}, 面数: {{len(shape.Faces)}}")

# 屋根の詳細確認
roof = doc.getObject("RoofSlab")
if roof:
    print("\\n🏠 RoofSlabの詳細解析:")
    for i, solid in enumerate(roof.Shape.Solids):
        bbox = solid.BoundBox
        print(f"  Solid {{i}}: Z範囲 = {{bbox.ZMin:.1f}} ~ {{bbox.ZMax:.1f}} mm")

# すべてをエクスポート（個別に）
print("\\n📋 個別にSTLエクスポート:")
for name in building_parts:
    obj = doc.getObject(name)
    if obj and hasattr(obj, 'Shape') and obj.Shape.Solids:
        mesh = Mesh.Mesh(obj.Shape.tessellate(0.3))
        filename = f"{{name}}.stl"
        mesh.write(filename)
        print(f"✅ {{filename}} ({{mesh.CountFacets}} faces)")

# 統合版もエクスポート
shapes = []
for name in building_parts:
    obj = doc.getObject(name)
    if obj and hasattr(obj, 'Shape') and obj.Shape.Solids:
        shapes.extend(obj.Shape.Solids)

if shapes:
    compound = Part.makeCompound(shapes)
    mesh = Mesh.Mesh(compound.tessellate(0.3))
    mesh.write("building_complete.stl")
    print(f"\\n✅ 統合版: building_complete.stl ({{mesh.CountFacets}} faces)")
'''

# 診断実行
with open("diagnose_roof.py", "w") as f:
    f.write(diagnosis_script)

print("🔍 屋根の位置を診断中...")
result = subprocess.run([FREECAD_CMD, "diagnose_roof.py"], capture_output=True, text=True)
print(result.stdout)
os.remove("diagnose_roof.py")

# 全体を正しい順序でレンダリング
print("\n📸 建物全体をレンダリング（Z軸を考慮）...")

render_script = '''
import bpy
import math

# シーンクリア
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# カメラ
bpy.ops.object.camera_add()
camera = bpy.context.object
bpy.context.scene.camera = camera

# 各パーツをインポート
parts = ["Foundation", "AnalysisBuilding", "Floor2", "Staircase", "RoofSlab"]
# 色設定を変更: 基礎(グレー), 建物1階(ベージュ), 2階床(緑がかった青), 階段(濃いグレー), 屋根(青)
colors = [(0.6,0.6,0.6), (0.9,0.85,0.75), (0.5,0.8,0.7), (0.4,0.4,0.4), (0.6,0.7,0.9)]

all_objects = []
for i, part_name in enumerate(parts):
    stl_file = f"{part_name}.stl"
    try:
        bpy.ops.import_mesh.stl(filepath=stl_file)
        obj = bpy.context.selected_objects[0]
        
        # スケール調整
        if max(obj.dimensions) > 100:
            obj.scale = (0.001, 0.001, 0.001)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(scale=True)
        
        # マテリアル設定
        mat = bpy.data.materials.new(f"Mat_{part_name}")
        mat.use_nodes = False
        mat.diffuse_color = colors[i] + (1.0,)
        obj.data.materials.append(mat)
        
        all_objects.append(obj)
        print(f"✅ {part_name}: Z={obj.location.z}")
        
        # 選択解除
        obj.select_set(False)
    except:
        print(f"❌ {part_name} not found")

import mathutils

# ワールド座標系でのバウンディングボックスを収集
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

distance = max_dim * 1.8
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
# shading.background_type = 'SINGLE_COLOR'
# scene.display.shading.background_type = 'VIEWPORT'
scene.render.film_transparent = True
# shading.background_color = (1.0, 1.0, 1.0)
shading.show_shadows = True

# レンダリング
scene.render.filepath = "angle1.png"
bpy.ops.render.render(write_still=True)
print("✅ angle1.png")

# 別視点の追加レンダリング

# 正面ビュー（南）
camera.location = (center[0], center[1] - distance, center[2])
direction = mathutils.Vector(center) - camera.location
rot_quat = direction.to_track_quat('-Z', 'Y')
camera.rotation_euler = rot_quat.to_euler()
scene.render.filepath = "angle2.png"
bpy.ops.render.render(write_still=True)
print("✅ angle2.png")

# 側面ビュー（東）
camera.location = (center[0] + distance, center[1], center[2])
direction = mathutils.Vector(center) - camera.location
rot_quat = direction.to_track_quat('-Z', 'Y')
camera.rotation_euler = rot_quat.to_euler()
scene.render.filepath = "angle3.png"
bpy.ops.render.render(write_still=True)
print("✅ angle3.png")

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
scene.render.filepath = "angle4.png"
bpy.ops.render.render(write_still=True)
print("✅ angle4.png")
'''

with open("render_all_parts.py", "w") as f:
    f.write(render_script)

cmd = [BLENDER, "-b", "-P", "render_all_parts.py"]
result = subprocess.run(cmd, capture_output=True, text=True)

for line in result.stdout.split('\n'):
    if "✅" in line or "❌" in line:
        print(line)

os.remove("render_all_parts.py")
