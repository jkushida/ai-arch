#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
かまぼこ屋根対応版ピロティ建築FEM解析スクリプト（ねじれ機能削除版）

主な特徴：
- 1階：オープン構造（柱のみ）
- 2階：壁付き構造（傾斜壁対応）
- 屋根：パラメトリックかまぼこ屋根（2パラメータ：morph, shift）
- 外部階段：1階から2階への接続
- FEM解析：CalculiX統合、かまぼこ屋根の曲面荷重対応
"""

import os
import math
import traceback
import random
import time

from dataclasses import dataclass
from typing import Dict, Any

# 外部環境依存モジュール
try:
    import FreeCAD as App
    import Part
    import ObjectsFem
    # femmesh.gmshtools は外部ライブラリのため、FreeCAD環境によっては利用できない可能性があります。
    import femmesh.gmshtools as gmshtools
    from femtools.ccxtools import CcxTools
    FEM_AVAILABLE = True
    CCX_AVAILABLE = True
except ImportError:
    FEM_AVAILABLE = False
    CCX_AVAILABLE = False
    if 'VERBOSE_OUTPUT' not in globals():
        VERBOSE_OUTPUT = True
    if VERBOSE_OUTPUT:
        print("⚠️ FreeCAD FEMまたは必要な外部モジュール（femmesh.gmshtools）のインポートに失敗しました。")
        print("一部機能が制限されるか、エラーが発生する可能性があります。")
    gmshtools = None # gmshtools がインポートできなかったことを後続のコードで識別するために、gmshtools を None に設定


# GUI モジュールの安全なインポート
GUI_AVAILABLE = False
try:
    import FreeCADGui as Gui
    # コマンドラインモードでもGuiが存在する場合があるので、実際に使えるかチェック
    if hasattr(Gui, 'ActiveDocument'):
        GUI_AVAILABLE = True
    else:
        GUI_AVAILABLE = False
except ImportError:
    GUI_AVAILABLE = False

import numpy as np
import sys
from datetime import datetime

# グローバル変数: すべてのprint文を制御
VERBOSE_OUTPUT = False  # Falseに設定するとすべてのprint文が抑制される

# FreeCADのコンソール出力を抑制
# デバッグ時はコメントアウト
# if not VERBOSE_OUTPUT:
#     try:
#         import FreeCAD as App
#         App.Console.SetStatus("Console", "Log", False)
#         App.Console.SetStatus("Console", "Msg", False)
#         App.Console.SetStatus("Console", "Wrn", False)
#         App.Console.SetStatus("Console", "Err", False)
#     except:
#         pass  # FreeCADが利用できない場合は何もしない

@dataclass
class BuildingParameters:
    """建物パラメータ格納用データクラス"""
    Lx: float          # 建物幅 [m]
    Ly: float          # 建物奥行き [m]
    H1: float          # 1階高 [m]
    H2: float          # 2階高 [m]
    tf: float          # 床スラブ厚 [mm]
    tr: float          # 屋根スラブ厚 [mm]
    bc: float          # 柱幅 [mm]
    hc: float          # 柱厚 [mm]
    tw_ext: float      # 外壁厚 [mm]
    balcony_depth: float = 0.0  # バルコニー奥行き [m] (0.0-3.0)





def calculate_roof_curvature(roof_morph: float) -> float:
    """屋根の曲率を計算"""
    if roof_morph < 0.33:
        return roof_morph * 3  # 0 ~ 1
    elif roof_morph < 0.67:
        return 1.0  # 標準
    else:
        return 1.0 + (roof_morph - 0.67) * 2  # 1 ~ 1.66


def calculate_roof_efficiency(roof_morph: float, roof_shift: float) -> float:
    """屋根形状による構造効率を計算"""
    # アーチ効果による構造効率
    if roof_morph < 0.33:
        arch_efficiency = 0.6 + roof_morph  # 0.6 ~ 0.93
    elif roof_morph < 0.67:
        arch_efficiency = 0.93 + (roof_morph - 0.33) * 0.2  # 0.93 ~ 1.0
    else:
        arch_efficiency = 1.0 - (roof_morph - 0.67) * 0.3  # 1.0 ~ 0.9（急すぎると効率低下）
    
    # 非対称性による効率低下
    asymmetry_penalty = abs(roof_shift) * 0.2
    
    return max(0.5, arch_efficiency - asymmetry_penalty)


def set_part_color(obj, color_tuple):
    """パーツに色を設定（GUI環境でのみ動作）"""
    try:
        if GUI_AVAILABLE and hasattr(obj, 'ViewObject') and obj.ViewObject is not None:
            obj.ViewObject.ShapeColor = color_tuple
            obj.ViewObject.Transparency = 0  # 不透明に設定
            obj.ViewObject.Visibility = True  # 明示的に可視化
            if hasattr(obj.ViewObject, 'ShowInTree'):
                obj.ViewObject.ShowInTree = True  # ツリーにも表示
            return True
    except Exception as e:
        if VERBOSE_OUTPUT:
            print(f"⚠️ 色設定エラー: {e}")
    return False


def ensure_parts_visibility(doc):
    """保存前に全パーツの可視化を確実に設定"""
    try:
        if not GUI_AVAILABLE:
            return
        
        # 可視化を設定するパーツのリスト
        colorful_parts = ["Foundation", "Floor1", "Floor2", "Columns", "Walls", "RoofSlab", "Balcony", "Staircase", "AnalysisBuilding"]
        
        for part_name in colorful_parts:
            obj = doc.getObject(part_name)
            if obj and hasattr(obj, 'ViewObject') and obj.ViewObject:
                obj.ViewObject.Visibility = True
                obj.ViewObject.Transparency = 0
                if hasattr(obj.ViewObject, 'ShowInTree'):
                    obj.ViewObject.ShowInTree = True
                if VERBOSE_OUTPUT:
                    print(f"✅ {part_name}の可視化を設定")
        
        # ViewFit を試みる（全体表示）
        if hasattr(Gui, 'ActiveDocument') and Gui.ActiveDocument:
            try:
                Gui.ActiveDocument.ActiveView.viewIsometric()
                Gui.ActiveDocument.ActiveView.fitAll()
                if VERBOSE_OUTPUT:
                    print("✅ ビューを調整（アイソメトリック＆全体表示）")
            except:
                pass
                
    except Exception as e:
        if VERBOSE_OUTPUT:
            print(f"⚠️ 可視化設定エラー: {e}")


def create_simple_box_roof(Lx_mm, Ly_mm, total_height_mm, tr_mm):
    """シンプルなボックス型屋根を作成（フォールバック用）"""
    if VERBOSE_OUTPUT:
        print("  - フォールバック: シンプルなボックス型屋根を作成")
    roof_box = Part.makeBox(Lx_mm, Ly_mm, tr_mm)
    roof_box.translate(App.Vector(0, 0, total_height_mm))
    return roof_box


def create_parametric_barrel_roof(
    Lx_mm, Ly_mm, total_height_mm, tr_mm,
    roof_morph: float = 0.5,
    roof_shift: float = 0.0
):
    """最小パラメータで多様なかまぼこ屋根を生成（ねじれ機能なし）"""
    
    # デバッグ情報の出力
    if VERBOSE_OUTPUT:
        print(f"\n🏗️ かまぼこ屋根生成開始:")
        if VERBOSE_OUTPUT:
            print(f"  - 寸法: {Lx_mm}x{Ly_mm}mm, 高さ: {total_height_mm}mm")
        if VERBOSE_OUTPUT:
            print(f"  - 厚さ: {tr_mm}mm")
        if VERBOSE_OUTPUT:
            print(f"  - パラメータ: morph={roof_morph}, shift={roof_shift}")
    
    # パラメータの型を確実にfloatに
    roof_morph = float(roof_morph)
    roof_shift = float(roof_shift)
    
    # morphパラメータで形状を大きく変化
    if roof_morph < 0.33:
        curve_height = Lx_mm * roof_morph * 0.9
        profile_power = 2.0
    elif roof_morph < 0.67:
        curve_height = Lx_mm * 0.3
        profile_power = 2.0 - (roof_morph - 0.33) * 3
    else:
        curve_height = Lx_mm * (0.3 + (roof_morph - 0.67) * 1.2)
        profile_power = -1.0 - (roof_morph - 0.67) * 6
    
    # 断面の生成
    num_points = 50
    roof_sections = []
    
    # Y方向のセグメント数（ねじれなしなので1で固定）
    segments = 1
    
    for j in range(segments + 1):
        y_pos = float(Ly_mm * j / segments)
        
        section_points = []
        for i in range(num_points):
            x_base = float(Lx_mm * i / (num_points - 1))
            
            # shiftで非対称性を制御
            if abs(roof_shift) > 0.01:  # 浮動小数点誤差を考慮
                peak_x = Lx_mm * (0.5 + roof_shift * 0.4)
                if x_base < peak_x:
                    t = x_base / peak_x if peak_x > 0 else 0
                    exponent = 1 - roof_shift * 0.5
                    # 負の基数を避けるため、tが1を超えないようにクランプ
                    t = min(max(t, 0), 1)
                    base_curve = pow(t, exponent)
                else:
                    remaining = Lx_mm - peak_x
                    if remaining > 0:
                        t = (x_base - peak_x) / remaining
                        exponent = 1 + roof_shift * 0.5
                        # tを0-1の範囲にクランプして、(1-t)が負にならないようにする
                        t = min(max(t, 0), 1)
                        # 小数乗の場合、基数が負になると複素数になるので、absを使用
                        if exponent != int(exponent) and (1 - t) < 0:
                            base_curve = 0  # 負の基数の場合は0とする
                        else:
                            base_curve = pow(max(1 - t, 0), exponent)
                    else:
                        base_curve = 0
            else:
                # 対称な形状
                t = 2 * abs(x_base / Lx_mm - 0.5)
                if profile_power > 0:
                    base_curve = 1 - pow(t, profile_power) if t <= 1 else 0
                else:
                    # 負のprofile_powerの場合、(1-t)が負にならないように注意
                    if t <= 1:
                        base_value = max(1 - t, 0)  # 負にならないようにクランプ
                        base_curve = pow(base_value, abs(profile_power))
                    else:
                        base_curve = 0
            
            z_base = float(base_curve * curve_height)
            
            # ベクトル作成（確実にfloat型で）
            try:
                point = App.Vector(
                    float(x_base),
                    float(y_pos),
                    float(total_height_mm + z_base)
                )
                section_points.append(point)
            except Exception as e:
                if VERBOSE_OUTPUT:
                    print(f"ベクトル作成エラー: {e}")
                    if VERBOSE_OUTPUT:
                        print(f"値: x={x_base}, y={y_pos}, z={total_height_mm + z_base}")
                # フォールバック
                point = App.Vector(
                    float(x_base),
                    float(y_pos),
                    float(total_height_mm)
                )
                section_points.append(point)
        
        roof_sections.append(section_points)
    
    if VERBOSE_OUTPUT:
        print(f"  - セクション数: {len(roof_sections)}")
        if VERBOSE_OUTPUT:
            print(f"  - セクションあたりの点数: {len(roof_sections[0]) if roof_sections else 0}")
    
    # 面を生成
    roof_faces = []
    
    try:
        # 屋根面の生成（ねじれなしなので簡略化）
        for j in range(len(roof_sections) - 1):
            for i in range(len(roof_sections[j]) - 1):
                p1 = roof_sections[j][i]
                p2 = roof_sections[j][i + 1]
                p3 = roof_sections[j + 1][i + 1]
                p4 = roof_sections[j + 1][i]
                
                # 4点が有効か確認
                if p1.distanceToPoint(p2) > 0.1 and p2.distanceToPoint(p3) > 0.1:
                    wire = Part.makePolygon([p1, p2, p3, p4, p1])
                    face = Part.Face(wire)
                    roof_faces.append(face)
        
        # 端面の生成（南北の壁との接合部）
        # 南端面
        south_bottom_points = [
            App.Vector(0, 0, total_height_mm),
            App.Vector(Lx_mm, 0, total_height_mm)
        ]
        south_points = roof_sections[0] + south_bottom_points[::-1]
        south_wire = Part.makePolygon(south_points + [south_points[0]])
        south_face = Part.Face(south_wire)
        roof_faces.append(south_face)
        
        # 北端面
        north_bottom_points = [
            App.Vector(0, Ly_mm, total_height_mm),
            App.Vector(Lx_mm, Ly_mm, total_height_mm)
        ]
        north_points = roof_sections[-1] + north_bottom_points[::-1]
        north_wire = Part.makePolygon(north_points + [north_points[0]])
        north_face = Part.Face(north_wire)
        roof_faces.append(north_face)
        
        # 屋根の底面（天井）
        bottom_wire = Part.makePolygon([
            App.Vector(0, 0, total_height_mm),
            App.Vector(Lx_mm, 0, total_height_mm),
            App.Vector(Lx_mm, Ly_mm, total_height_mm),
            App.Vector(0, Ly_mm, total_height_mm),
            App.Vector(0, 0, total_height_mm)
        ])
        bottom_face = Part.Face(bottom_wire)
        roof_faces.append(bottom_face)
        
        if VERBOSE_OUTPUT:
            print(f"  - 生成された面数: {len(roof_faces)}")
        
        # すべての面を結合してソリッドを作成
        if len(roof_faces) > 0:
            if VERBOSE_OUTPUT:
                print(f"  - シェル作成中...")
            roof_shell = Part.Shell(roof_faces)
            if VERBOSE_OUTPUT:
                print(f"  - シェル作成: 成功")
            
            roof_solid = Part.Solid(roof_shell)
            if VERBOSE_OUTPUT:
                print(f"  - ソリッド作成: 成功")
            
            # 屋根の厚みを追加
            if tr_mm > 10:  # 最小厚さを確保
                try:
                    # 内側にオフセットして厚みを作成
                    inner_solid = roof_solid.makeOffsetShape(-float(tr_mm), 0.01)
                    roof_with_thickness = roof_solid.cut(inner_solid)
                    if VERBOSE_OUTPUT:
                        print(f"  - 厚み付き屋根生成: 成功")
                    return roof_with_thickness
                except Exception as e:
                    if VERBOSE_OUTPUT:
                        print(f"  - 屋根厚み生成に失敗: {e}")
                        if VERBOSE_OUTPUT:
                            print("  - ソリッドのまま返します")
                    return roof_solid
            
            return roof_solid
        else:
            # フォールバック：単純な箱型屋根
            if VERBOSE_OUTPUT:
                print("❌ かまぼこ屋根生成に失敗: 面が生成されませんでした")
            return create_simple_box_roof(Lx_mm, Ly_mm, total_height_mm, tr_mm)
            
    except Exception as e:
        if VERBOSE_OUTPUT:
            print(f"❌ 屋根生成エラー: {type(e).__name__}: {e}")
            traceback.print_exc()
        # エラー時は単純な平屋根を返す
        return create_simple_box_roof(Lx_mm, Ly_mm, total_height_mm, tr_mm)


def create_balcony(Lx_mm: float, Ly_mm: float, H1_mm: float, balcony_depth_mm: float) -> Any:
    """バルコニーを生成（西側壁面に設置）
    
    Args:
        Lx_mm: 建物幅 [mm]
        Ly_mm: 建物奥行き [mm]
        H1_mm: 1階高 [mm]
        balcony_depth_mm: バルコニー奥行き [mm]
    
    Returns:
        バルコニーの形状またはNone
    """
    if balcony_depth_mm <= 0:
        return None
    
    try:
        # バルコニーの床部分
        balcony_floor_thickness = 150  # 床厚150mm
        balcony_length = Ly_mm * 0.8  # 建物奥行きの80%
        balcony_y_offset = Ly_mm * 0.1  # 中央に配置
        
        # バルコニー床スラブ（西側に配置）
        balcony_floor = Part.makeBox(balcony_depth_mm, balcony_length, balcony_floor_thickness)
        balcony_floor.translate(App.Vector(-balcony_depth_mm, balcony_y_offset, H1_mm))
        
        # 手すり壁（安全性のため）
        railing_height = 1100  # 手すり高1100mm
        railing_thickness = 100  # 手すり厚100mm
        
        # 西側手すり（外側）
        west_railing = Part.makeBox(railing_thickness, balcony_length, railing_height)
        west_railing.translate(App.Vector(-balcony_depth_mm, balcony_y_offset, H1_mm + balcony_floor_thickness))
        
        # 北側手すり
        north_railing = Part.makeBox(balcony_depth_mm, railing_thickness, railing_height)
        north_railing.translate(App.Vector(-balcony_depth_mm, balcony_y_offset + balcony_length - railing_thickness, H1_mm + balcony_floor_thickness))
        
        # 南側手すり
        south_railing = Part.makeBox(balcony_depth_mm, railing_thickness, railing_height)
        south_railing.translate(App.Vector(-balcony_depth_mm, balcony_y_offset, H1_mm + balcony_floor_thickness))
        
        # バルコニーの全部品を統合
        balcony = balcony_floor.fuse(west_railing).fuse(north_railing).fuse(south_railing)
        
        return balcony
        
    except Exception as e:
        if VERBOSE_OUTPUT:
            print(f"⚠️ バルコニー生成エラー: {e}")
        return None


def create_realistic_building_model(
    # 既存パラメータ
    Lx: float, Ly: float, H1: float, H2: float,
    tf: float, tr: float, bc: float, hc: float,
    tw_ext: float,
    
    # 追加パラメータ
        wall_tilt_angle: float = 0.0,      # 壁の傾斜角度 [度] (-40.0 to 30.0)      # 壁の傾斜角度 [度] (-40.0 to 30.0)
    window_ratio_2f: float = 0.4,      # 2階窓面積率 (0.0-0.8)
    
    # かまぼこ屋根パラメータ（ねじれ削除）
    roof_morph: float = 0.5,
    roof_shift: float = 0.0,
    
    # バルコニーパラメータ
    balcony_depth: float = 0.0  # バルコニー奥行き [m]
) -> (Any, Any, Dict[str, Any]):
    """修正版：かまぼこ屋根付きピロティ建築"""
    if not FEM_AVAILABLE:
        return None, None, {}



    # 単位換算
    Lx_mm = int(Lx * 1000)
    Ly_mm = int(Ly * 1000)
    H1_mm = int(H1 * 1000)
    H2_mm = int(H2 * 1000)
    total_height_mm = H1_mm + H2_mm
    tf_mm = int(tf)
    tr_mm = int(tr)
    bc_mm = int(bc)
    hc_mm = int(hc)
    tw_ext_mm = int(tw_ext)
    balcony_depth_mm = int(balcony_depth * 1000)  # m -> mm

    try:
        # ドキュメント作成
        base_name = "BuildingFEMAnalysis"
        doc_name = base_name
        if hasattr(App, "listDocuments"):
            docs = App.listDocuments()
            if doc_name in docs:
                doc_name = f"{base_name}_{int(time.time()*1000)}"
        doc = App.newDocument(doc_name)
        
        # =================================================================
        # 1. 基礎
        # =================================================================
        foundation = Part.makeBox(Lx_mm, Ly_mm, 400).translate(App.Vector(0, 0, -400))

        # =================================================================
        # 2. 床配置
        # =================================================================
        # 1階床（地上階なので必要）
        floor1 = Part.makeBox(Lx_mm, Ly_mm, tf_mm)
        
        # 階段の最終段の位置を計算
        steps_1f = int(H1_mm // 200)  # 階段の段数
        stair_x = Lx_mm * 0.15  # 階段のX位置
        stair_y = Ly_mm * 0.15  # 階段のY開始位置
        landing_y_end = stair_y + steps_1f * 300  # 階段最終段のY終端位置

        # 2階床（階段用開口付き）
        floor2_base = Part.makeBox(Lx_mm, Ly_mm, tf_mm).translate(App.Vector(0, 0, H1_mm))

        # 開口部のサイズと位置（階段の終端から手前方向に開口）
        stair_opening_width = 1000      # 階段幅と同じ
        stair_opening_depth = 2000      # 奥行き2m
        stair_opening_thickness = tf_mm + 20
        stair_opening_x = stair_x       # 階段のX位置と完全に一致
        stair_opening_y = landing_y_end - stair_opening_depth  # 階段の終端から手前方向に開口
        stair_opening_z = H1_mm - 10

        stair_opening = Part.makeBox(stair_opening_width, stair_opening_depth, stair_opening_thickness)
        stair_opening.translate(App.Vector(stair_opening_x, stair_opening_y, stair_opening_z))

        floor2 = floor2_base.cut(stair_opening)

        # 傾斜角度をラジアンに変換（正=外傾斜、負=内傾斜）
        tilt_rad = math.radians(wall_tilt_angle)
        wall_offset_top = H2_mm * math.tan(tilt_rad)  # 上部でのオフセット量

        # =================================================================
        # かまぼこ屋根の生成
        # =================================================================
        
        # 傾斜壁に対応した屋根幅の調整
        if wall_tilt_angle < -0.1:  # 内傾斜の場合
            roof_width = Lx_mm + wall_offset_top
        else:
            roof_width = Lx_mm
        
        # かまぼこ屋根の生成
        roof = create_parametric_barrel_roof(
            roof_width, Ly_mm, total_height_mm, tr_mm,
            roof_morph, roof_shift
        )

        # =================================================================
        # =================================================================
        # 3. 柱配置（ピロティ用に強化）
        # =================================================================
        columns = []

        # 傾斜による柱位置の調整計算
        # 内傾斜の場合、東側の柱を内側にシフト
        column_shift_x = 0
        if wall_tilt_angle < 0:  # 内傾斜の場合
            # 壁の傾斜による上部のオフセット（負の値）
            # 柱は壁の内側に収まるようにシフト
            # 極端な内傾斜の場合は追加のマージンを設ける
            if wall_tilt_angle < -30:
                safety_margin = 100  # 追加の安全マージン
            else:
                safety_margin = 0
            column_shift_x = abs(wall_offset_top) + tw_ext_mm + safety_margin  # 壁厚分も考慮

        # 主要構造柱（1階〜2階通し柱）
        corner_offset = 100

        # 柱位置の定義（傾斜を考慮）
        main_positions = [
            # 西側の柱（傾斜の影響なし）
            (corner_offset, corner_offset),
            (corner_offset, Ly_mm - corner_offset - hc_mm * 1.2),
            
            # 東側の柱（傾斜の影響あり）
            (Lx_mm - corner_offset - bc_mm * 1.2 - column_shift_x, corner_offset),
            (Lx_mm - corner_offset - bc_mm * 1.2 - column_shift_x, Ly_mm - corner_offset - hc_mm * 1.2),
            
            # 中央柱（少しシフト）
            (Lx_mm * 0.5 - bc_mm * 0.6 - column_shift_x * 0.5, Ly_mm * 0.5 - hc_mm * 0.6),
        ]

        # 外傾斜の場合の追加調整
        if wall_tilt_angle > 0:  # 外傾斜の場合
            # 東側の柱を少し内側に配置（安全マージン）
            safety_margin = 50  # 50mm の安全マージン
            main_positions = [
                (corner_offset, corner_offset),
                (corner_offset, Ly_mm - corner_offset - hc_mm * 1.2),
                (Lx_mm - corner_offset - bc_mm * 1.2 - safety_margin, corner_offset),
                (Lx_mm - corner_offset - bc_mm * 1.2 - safety_margin, Ly_mm - corner_offset - hc_mm * 1.2),
                (Lx_mm * 0.5 - bc_mm * 0.6, Ly_mm * 0.5 - hc_mm * 0.6),
            ]

        # 極端な傾斜角度での追加柱（補強）
        if abs(wall_tilt_angle) > 25:  # 25度を超える傾斜
            # Y方向中間に補強柱を追加
            additional_positions = [
                (corner_offset, Ly_mm * 0.5 - hc_mm * 0.6),  # 西側中間
                (Lx_mm - corner_offset - bc_mm * 1.2 - column_shift_x, Ly_mm * 0.5 - hc_mm * 0.6),  # 東側中間
            ]
            main_positions.extend(additional_positions)

        # 柱の生成
        for (x, y) in main_positions:
            # 位置が建物範囲内かチェック
            if x > 0 and x + bc_mm * 1.2 < Lx_mm and y > 0 and y + hc_mm * 1.2 < Ly_mm:
                col = Part.makeBox(bc_mm * 1.2, hc_mm * 1.2, total_height_mm).translate(App.Vector(x, y, 0))
                columns.append(col)
            else:
                if VERBOSE_OUTPUT:
                    print(f"⚠️ 柱位置が範囲外のためスキップ: x={x}, y={y}")

        # =================================================================
        # 4. 壁配置（1階の壁を大幅削減）
        # =================================================================
        walls = []
        
        # 🔧 1階部分：最小限の壁のみ（階段周りとプライバシー確保）
        # 階段周りの保護壁のみ
#        stair_wall_1f = Part.makeBox(tw_ext_mm, 2000, H1_mm)
#        stair_wall_1f.translate(App.Vector(-tw_ext_mm, 0, tf_mm))
#        walls.append(stair_wall_1f)
        
        # =================================================================
        # 2階の外壁（東面のみ傾斜）
        # =================================================================
        
        # 東面壁（傾斜壁）- 隙間のない完全版
        if abs(wall_tilt_angle) > 0.1:  # 傾斜がある場合
            if wall_tilt_angle > 0:  # 外傾斜の場合
                # 五角形の断面を持つ壁（上部が屋根を貫通）
                points = [
                    App.Vector(Lx_mm, 0, H1_mm + tf_mm),                    # 左下
                    App.Vector(Lx_mm + tw_ext_mm, 0, H1_mm + tf_mm),       # 右下
                    App.Vector(Lx_mm + tw_ext_mm + wall_offset_top, 0, total_height_mm),  # 右中
                    App.Vector(Lx_mm + tw_ext_mm + wall_offset_top, 0, total_height_mm + tr_mm),  # 右上
                    App.Vector(Lx_mm, 0, total_height_mm + tr_mm),         # 左上
                    App.Vector(Lx_mm, 0, H1_mm + tf_mm)                    # 閉じる
                ]
            else:  # 内傾斜の場合
                # 通常の台形（屋根下端まで）
                points = [
                    App.Vector(Lx_mm, 0, H1_mm + tf_mm),                    # 左下
                    App.Vector(Lx_mm + tw_ext_mm, 0, H1_mm + tf_mm),       # 右下
                    App.Vector(Lx_mm + tw_ext_mm + wall_offset_top, 0, total_height_mm),  # 右上
                    App.Vector(Lx_mm + wall_offset_top, 0, total_height_mm),              # 左上
                    App.Vector(Lx_mm, 0, H1_mm + tf_mm)                     # 閉じる
                ]
            
            # ワイヤーを作成
            wire = Part.makePolygon(points)
            # Y方向に押し出して壁を作成
            east_wall_2f = Part.Face(wire).extrude(App.Vector(0, Ly_mm, 0))
            
            # 追加：外傾斜の場合は側面の三角形部分を埋める
            if wall_tilt_angle > 0:
                # 南側の三角形充填
                triangle_south_points = [
                    App.Vector(Lx_mm, 0, total_height_mm),
                    App.Vector(Lx_mm + wall_offset_top, 0, total_height_mm),
                    App.Vector(Lx_mm + wall_offset_top, 0, total_height_mm + tr_mm),
                    App.Vector(Lx_mm, 0, total_height_mm + tr_mm),
                    App.Vector(Lx_mm, 0, total_height_mm)
                ]
                wire_triangle_south = Part.makePolygon(triangle_south_points)
                triangle_south = Part.Face(wire_triangle_south).extrude(App.Vector(0, tw_ext_mm, 0))
                east_wall_2f = east_wall_2f.fuse(triangle_south)
                
                # 北側の三角形充填
                triangle_north_points = [
                    App.Vector(Lx_mm, Ly_mm - tw_ext_mm, total_height_mm),
                    App.Vector(Lx_mm + wall_offset_top, Ly_mm - tw_ext_mm, total_height_mm),
                    App.Vector(Lx_mm + wall_offset_top, Ly_mm - tw_ext_mm, total_height_mm + tr_mm),
                    App.Vector(Lx_mm, Ly_mm - tw_ext_mm, total_height_mm + tr_mm),
                    App.Vector(Lx_mm, Ly_mm - tw_ext_mm, total_height_mm)
                ]
                wire_triangle_north = Part.makePolygon(triangle_north_points)
                triangle_north = Part.Face(wire_triangle_north).extrude(App.Vector(0, tw_ext_mm, 0))
                east_wall_2f = east_wall_2f.fuse(triangle_north)
            
            # 窓開口（傾斜に合わせて調整）
            if window_ratio_2f > 0:
                # window_ratio_2fを面積率として解釈し、高さと幅を自動調整
                if window_ratio_2f > 0.7:  # 大きな窓を要求
                    # 傾斜角度に応じて幅と高さのバランスを調整
                    if abs(wall_tilt_angle) >= 40:
                        window_height = H2_mm * 0.70  # 高さを増やす
                        window_width = Ly_mm * min(0.95, window_ratio_2f * 1.3)  # 幅も調整
                        window_bottom_margin = 0.20   # 下部マージンを20%に
                    elif abs(wall_tilt_angle) >= 30:
                        window_height = H2_mm * 0.72  # 高さを増やす
                        window_width = Ly_mm * min(0.92, window_ratio_2f * 1.25)  # 幅も調整
                        window_bottom_margin = 0.18   # 下部マージンを18%に
                    elif abs(wall_tilt_angle) >= 20:
                        window_height = H2_mm * 0.75  # 高さを増やす
                        window_width = Ly_mm * min(0.90, window_ratio_2f * 1.2)  # 幅も調整
                        window_bottom_margin = 0.15   # 下部マージンを15%に
                    else:
                        window_height = H2_mm * 0.80  # 通常角度では高さ80%
                        window_width = Ly_mm * min(0.90, window_ratio_2f * 1.1)  # 幅も調整
                        window_bottom_margin = 0.12   # 下部マージンを12%に
                else:
                    # 通常サイズの窓（元の動的調整を維持）
                    if abs(wall_tilt_angle) >= 40:
                        window_height = H2_mm * 0.60  # 極端な角度では窓高さを60%に
                        window_bottom_margin = 0.25   # 下部マージンを25%に増加
                    elif abs(wall_tilt_angle) >= 30:
                        window_height = H2_mm * 0.65  # 中程度の角度では窓高さを65%に
                        window_bottom_margin = 0.225  # 下部マージンを22.5%に
                    elif abs(wall_tilt_angle) >= 20:
                        window_height = H2_mm * 0.70  # 20度以上では窓高さを70%に
                        window_bottom_margin = 0.20   # 下部マージンを20%に
                    else:
                        window_height = H2_mm * 0.75  # 通常角度では窓高さを75%に
                        window_bottom_margin = 0.15   # 下部マージンを15%に
                    
                    window_width = Ly_mm * window_ratio_2f
                
                # 窓の中心位置での壁のX座標を計算
                window_center_z = H1_mm + tf_mm + H2_mm * 0.5
                window_x_offset = (window_center_z - H1_mm - tf_mm) / H2_mm * wall_offset_top
                
                # 傾斜角度に応じて厚さを決定（水平窓用）
                if abs(wall_tilt_angle) > 30:
                    window_box_thickness = tw_ext_mm * 6 + abs(wall_offset_top) * 2
                elif abs(wall_tilt_angle) > 20:
                    window_box_thickness = tw_ext_mm * 5 + abs(wall_offset_top) * 1.5
                else:
                    window_box_thickness = tw_ext_mm * 4 + abs(wall_offset_top)
                
                # 窓用のボックスを作成（回転なし、水平のまま）
                window_box = Part.makeBox(window_box_thickness, window_width, window_height)
                
                # 内傾斜と外傾斜で異なる位置調整
                if wall_tilt_angle < 0:
                    # 内傾斜：壁の中央付近から外側に向けて配置
                    x_position = Lx_mm + window_x_offset - window_box_thickness * 0.3
                else:
                    # 外傾斜：壁の内側から外側に向けて配置
                    x_position = Lx_mm - window_box_thickness * 0.7
                
                # 実際の窓幅を使った中央配置計算
                window_y_position = (Ly_mm - window_width) / 2
                
                window_box.translate(App.Vector(
                    x_position,
                    window_y_position,  # 実際の窓幅に基づく中央配置
                    H1_mm + tf_mm + H2_mm * window_bottom_margin  # 動的マージンを使用
                ))
                east_wall_2f = east_wall_2f.cut(window_box)
        else:
            # 傾斜なしの通常の壁
            east_wall_2f = Part.makeBox(tw_ext_mm, Ly_mm, H2_mm).translate(App.Vector(Lx_mm, 0, H1_mm + tf_mm))
            # 通常の窓開口処理
            if window_ratio_2f > 0:
                window_thickness = tw_ext_mm * 4  # 壁厚の4倍
                glass_wall = Part.makeBox(window_thickness, Ly_mm * window_ratio_2f, H2_mm * 0.7)
                glass_wall.translate(App.Vector(Lx_mm - tw_ext_mm * 2, Ly_mm * (1 - window_ratio_2f) / 2, H1_mm + tf_mm + H2_mm * 0.15))
                east_wall_2f = east_wall_2f.cut(glass_wall)
        
        walls.append(east_wall_2f)
        
        # 西面壁（通常の垂直壁）
        west_wall_2f = Part.makeBox(tw_ext_mm, Ly_mm, H2_mm).translate(App.Vector(-tw_ext_mm, 0, H1_mm + tf_mm))
        
        # バルコニーへの入り口（バルコニーがある場合のみ）
        if balcony_depth_mm > 0:
            door_width = 900  # ドア幅900mm
            door_height = 2100  # ドア高さ2100mm
            door_thickness = tw_ext_mm + 20  # 壁厚より少し厚く
            
            # バルコニーの中央位置に合わせてドアを配置
            balcony_y_offset = Ly_mm * 0.1  # バルコニーのY方向オフセット
            balcony_length = Ly_mm * 0.8  # バルコニーの長さ
            door_y_position = balcony_y_offset + (balcony_length - door_width) / 2  # ドアをバルコニー中央に配置
            
            balcony_door = Part.makeBox(door_thickness, door_width, door_height)
            balcony_door.translate(App.Vector(-tw_ext_mm - 10, door_y_position, H1_mm + tf_mm + 100))  # 床から100mm上
            west_wall_2f = west_wall_2f.cut(balcony_door)
            if VERBOSE_OUTPUT:
                print(f"🚪 バルコニーへの入り口を設置しました（幅{door_width}mm×高さ{door_height}mm）")
        
        walls.append(west_wall_2f)
        
        # 南面壁（2階部分のみ） - 傾斜に完全対応
        if abs(wall_tilt_angle) > 0.1:  # 傾斜がある場合（内外問わず）
            # 台形の南面壁を作成（東側の端を傾斜に合わせる）
            south_points = [
                App.Vector(0, -tw_ext_mm, H1_mm + tf_mm),                    # 左下
                App.Vector(Lx_mm, -tw_ext_mm, H1_mm + tf_mm),               # 右下
                App.Vector(Lx_mm + wall_offset_top, -tw_ext_mm, total_height_mm),  # 右上（傾斜に合わせる）
                App.Vector(0, -tw_ext_mm, total_height_mm),                 # 左上
                App.Vector(0, -tw_ext_mm, H1_mm + tf_mm)                    # 閉じる
            ]
            wire_south = Part.makePolygon(south_points)
            south_wall_2f = Part.Face(wire_south).extrude(App.Vector(0, tw_ext_mm, 0))
            
            if VERBOSE_OUTPUT:
                print(f"🪟 南面壁（傾斜）の窓切り抜き開始...")
            initial_volume = south_wall_2f.Volume
            
            # 2階窓（傾斜を考慮）
            for i in range(4):
                # 傾斜を考慮した窓ボックスの厚さと位置の調整
                # 壁の厚さの3倍以上を確保して確実に貫通させる
                window_base_thickness = tw_ext_mm * 4
                
                # 傾斜角度に応じて窓ボックスをさらに大きく
                if abs(wall_tilt_angle) > 20:
                    window_thickness = window_base_thickness * 2
                elif abs(wall_tilt_angle) > 10:
                    window_thickness = window_base_thickness * 1.5
                else:
                    window_thickness = window_base_thickness
                
                # window_ratio_2fに基づいて窓幅を調整（最大0.15、最小0.05）
                window_width = Lx_mm * (0.05 + 0.10 * window_ratio_2f)
                
                # 傾斜角度に応じた動的な窓高さとマージン調整（window_ratio_2fも考慮）
                if abs(wall_tilt_angle) >= 40:
                    window_height = H2_mm * (0.30 + 0.30 * window_ratio_2f)  # 極端な角度では窓高さを30-60%
                    window_top_margin = 0.25  # 上部マージンを25%に増加
                elif abs(wall_tilt_angle) >= 30:
                    window_height = H2_mm * (0.35 + 0.30 * window_ratio_2f)  # 中程度の角度では窓高さを35-65%
                    window_top_margin = 0.225  # 上部マージンを22.5%に
                else:
                    window_height = H2_mm * (0.40 + 0.30 * window_ratio_2f)  # 通常角度では窓高さを40-70%
                    window_top_margin = 0.20  # 上部マージンを20%に
                
                # 窓の位置を壁の中心線上に配置
                window_x = Lx_mm * 0.1 + i * Lx_mm * 0.2
                
                # 壁の傾斜を考慮した窓の中心Z座標（動的マージンを適用）
                window_z_position = H1_mm + tf_mm + H2_mm * window_top_margin
                window_center_z = window_z_position + window_height * 0.5
                
                # 傾斜による窓のX位置のオフセット
                if abs(wall_tilt_angle) > 0.1:
                    x_offset_at_window = (window_center_z - (H1_mm + tf_mm)) * math.tan(tilt_rad)
                else:
                    x_offset_at_window = 0
                
                # 窓ボックスを作成（Y方向に十分な厚さを持たせる）
                window = Part.makeBox(window_width, window_thickness, window_height)
                
                # 窓を適切な位置に移動（壁を確実に貫通させる）
                # Y方向の位置を壁の外側から十分深く設定
                window.translate(App.Vector(
                    window_x + x_offset_at_window * 0.5,  # 傾斜を考慮したX位置
                    -window_thickness * 0.8,  # 壁の外側からさらに深く貫通
                    window_z_position  # 動的に計算されたZ位置を使用
                ))
                
                south_wall_2f = south_wall_2f.cut(window)
            
            final_volume = south_wall_2f.Volume
            if VERBOSE_OUTPUT:
                if VERBOSE_OUTPUT:
                    print(f"✅ 南面壁の体積変化: {initial_volume:.0f} → {final_volume:.0f} mm³")
                    if VERBOSE_OUTPUT:
                        print(f"   削減率: {(1 - final_volume/initial_volume)*100:.1f}%")
        else:
            # 傾斜なしの通常の南面壁
            south_wall_2f = Part.makeBox(Lx_mm, tw_ext_mm, H2_mm).translate(App.Vector(0, -tw_ext_mm, H1_mm + tf_mm))
            
            if VERBOSE_OUTPUT:
                print(f"🪟 南面壁（垂直）の窓切り抜き開始...")
            initial_volume = south_wall_2f.Volume
            
            # 2階窓
            for i in range(4):
                # 窓ボックスを十分大きく作成（確実に貫通させるため）
                window_thickness = tw_ext_mm * 4  # 壁厚の4倍
                # window_ratio_2fに基づいて窓サイズを調整
                window_width = Lx_mm * (0.05 + 0.10 * window_ratio_2f)  # 5-15%の幅
                window_height = H2_mm * (0.30 + 0.30 * window_ratio_2f)  # 30-60%の高さ
                window = Part.makeBox(window_width, window_thickness, window_height)
                window.translate(App.Vector(
                    Lx_mm * 0.1 + i * Lx_mm * 0.2,
                    -window_thickness * 0.8,  # 壁の外側からさらに深く貫通
                    H1_mm + tf_mm + H2_mm * 0.2
                ))
                south_wall_2f = south_wall_2f.cut(window)
            
            final_volume = south_wall_2f.Volume
            if VERBOSE_OUTPUT:
                if VERBOSE_OUTPUT:
                    print(f"✅ 南面壁の体積変化: {initial_volume:.0f} → {final_volume:.0f} mm³")
                    if VERBOSE_OUTPUT:
                        print(f"   削減率: {(1 - final_volume/initial_volume)*100:.1f}%")
        
        walls.append(south_wall_2f)
        
        # 北面壁（2階部分のみ） - 傾斜に完全対応
        if abs(wall_tilt_angle) > 0.1:  # 傾斜がある場合（内外問わず）
            # 台形の北面壁を作成（東側の端を傾斜に合わせる）
            north_points = [
                App.Vector(0, Ly_mm, H1_mm + tf_mm),                        # 左下
                App.Vector(Lx_mm, Ly_mm, H1_mm + tf_mm),                   # 右下
                App.Vector(Lx_mm + wall_offset_top, Ly_mm, total_height_mm),    # 右上（傾斜に合わせる）
                App.Vector(0, Ly_mm, total_height_mm),                      # 左上
                App.Vector(0, Ly_mm, H1_mm + tf_mm)                        # 閉じる
            ]
            wire_north = Part.makePolygon(north_points)
            north_wall_2f = Part.Face(wire_north).extrude(App.Vector(0, tw_ext_mm, 0))
            
            # 小窓（傾斜を考慮）
            for i in range(6):
                # 傾斜を考慮した窓ボックスの厚さと位置の調整
                window_base_thickness = tw_ext_mm * 4
                
                # 傾斜角度に応じて窓ボックスを大きく
                if abs(wall_tilt_angle) > 20:
                    window_thickness = window_base_thickness * 2
                else:
                    window_thickness = window_base_thickness
                
                # window_ratio_2fに基づいて窓サイズを調整
                window_width = Lx_mm * (0.03 + 0.05 * window_ratio_2f)  # 3-8%の幅
                window_height = H2_mm * (0.15 + 0.15 * window_ratio_2f)  # 15-30%の高さ
                
                # 窓の位置を壁の中心線上に配置
                window_x = Lx_mm * 0.1 + i * Lx_mm * 0.13
                
                # 壁の傾斜を考慮した窓の中心Z座標
                window_center_z = H1_mm + tf_mm + H2_mm * 0.5
                
                # 傾斜による窓のX位置のオフセット
                if abs(wall_tilt_angle) > 0.1:
                    x_offset_at_window = (window_center_z - (H1_mm + tf_mm)) * math.tan(tilt_rad)
                else:
                    x_offset_at_window = 0
                
                # 窓ボックスを作成（Y方向に十分な厚さを持たせる）
                small_window = Part.makeBox(window_width, window_thickness, window_height)
                
                # 窓を適切な位置に移動（壁を確実に貫通させる）
                small_window.translate(App.Vector(
                    window_x + x_offset_at_window * 0.5,  # 傾斜を考慮したX位置
                    Ly_mm - window_thickness * 0.2,  # 壁の内側から貫通
                    H1_mm + tf_mm + H2_mm * 0.35
                ))
                
                north_wall_2f = north_wall_2f.cut(small_window)
        else:
            # 傾斜なしの通常の北面壁
            north_wall_2f = Part.makeBox(Lx_mm, tw_ext_mm, H2_mm).translate(App.Vector(0, Ly_mm, H1_mm + tf_mm))
            for i in range(6):
                # 窓ボックスを十分大きく作成（確実に貫通させるため）
                window_thickness = tw_ext_mm * 4  # 壁厚の4倍
                # window_ratio_2fに基づいて窓サイズを調整
                window_width = Lx_mm * (0.03 + 0.05 * window_ratio_2f)  # 3-8%の幅
                window_height = H2_mm * (0.15 + 0.15 * window_ratio_2f)  # 15-30%の高さ
                small_window = Part.makeBox(window_width, window_thickness, window_height)
                small_window.translate(App.Vector(
                    Lx_mm * 0.1 + i * Lx_mm * 0.13,
                    Ly_mm - window_thickness * 0.2,  # 壁の内側から貫通
                    H1_mm + tf_mm + H2_mm * 0.35
                ))
                north_wall_2f = north_wall_2f.cut(small_window)
        
        walls.append(north_wall_2f)
        
        # 内部間仕切りは削除（オープンスペース）
        partitions = []
        
        # バルコニーの生成（西側壁面に設置）
        balcony = create_balcony(Lx_mm, Ly_mm, H1_mm, balcony_depth_mm)
        if balcony is not None and VERBOSE_OUTPUT:
            if VERBOSE_OUTPUT:
                print(f"🏠 バルコニーを生成しました（西側、奥行き: {balcony_depth}m）")

        # =================================================================
        # 5. 統合 - 基礎を含めた完全な一体化
        # =================================================================
        all_parts = [foundation, floor1, floor2, roof] + columns + walls + partitions
        if balcony is not None:
            all_parts.append(balcony)
        building_parts = list(all_parts)
        
        # 基礎から順番に確実に結合
        if VERBOSE_OUTPUT:
            if VERBOSE_OUTPUT:
                print("建物部品の統合を開始...")
        building_shape = foundation  # 基礎から開始
        fusion_count = 0
        
        parts_to_fuse = [floor1, floor2, roof] + columns + walls + partitions
        if balcony is not None:
            parts_to_fuse.append(balcony)
        
        for i, shp in enumerate(parts_to_fuse):
            try:
                building_shape = building_shape.fuse(shp)
                fusion_count += 1
            except Exception as e:
                if VERBOSE_OUTPUT:
                    print(f"⚠️ 部品 {i+1} の結合でエラー: {e}")
                continue
        
        if VERBOSE_OUTPUT:
            print(f"✅ {fusion_count+1}/{len(all_parts)} 個の部品を統合完了")

        # L字型階段の追加（既存コードをそのまま使用）
        stair_width = 1000  # 階段幅1000mm（開口部と同じ）
        stair_rise = 200
        stair_run = 300
        tread_thickness = 30
        riser_thickness = 20
        
        steps_1f = int(H1_mm // stair_rise)
        height_1f = steps_1f * stair_rise
        
        stair_1f_parts = []
        
        # 🔧 階段を中央寄りに配置（壁から離す）
        stair_x = Lx_mm * 0.15  # 建物幅の15%内側
        stair_y = Ly_mm * 0.15  # 建物奥行きの15%内側
        
        for i in range(steps_1f):
            step_z = i * stair_rise
            step_y = stair_y + i * stair_run
            
            tread = Part.makeBox(stair_width, stair_run, tread_thickness)
            tread.translate(App.Vector(stair_x, step_y, step_z + stair_rise - tread_thickness))
            
            riser = Part.makeBox(stair_width, riser_thickness, stair_rise)
            riser.translate(App.Vector(stair_x, step_y + stair_run - riser_thickness, step_z))
            
            try:
                step = tread.fuse(riser)
                stair_1f_parts.append(step)
            except:
                stair_1f_parts.append(tread)
        
        # L字型階段の最後の部分を調整
        landing_size = 1000
        landing = Part.makeBox(landing_size, landing_size + 100, 50)  # Y方向を少し延長
        landing.translate(App.Vector(stair_x, stair_y + steps_1f * stair_run - 50, height_1f))  # 位置を微調整
        
        all_stair_parts = stair_1f_parts + [landing]
        if all_stair_parts:
            staircase = all_stair_parts[0]
            for part in all_stair_parts[1:]:
                try:
                    staircase = staircase.fuse(part)
                except:
                    pass
        else:
            staircase = Part.makeBox(stair_width, stair_width, height_1f)
            staircase.translate(App.Vector(stair_x, stair_y, 0))
        
        # 階段は作成するが、建物本体には統合しない（異常変位の原因となる可能性があるため）
        stair_obj = doc.addObject("Part::Feature", "Staircase")
        stair_obj.Shape = staircase
        
        if is_gui_mode() and hasattr(stair_obj, "ViewObject") and stair_obj.ViewObject is not None:
            stair_obj.ViewObject.Visibility = True
            set_part_color(stair_obj, (0.4, 0.4, 0.4))  # 濃いグレー
        building_parts.append(stair_obj)
        
        # 階段は建物本体に統合しない（FEM解析から除外）
        if VERBOSE_OUTPUT:
            print("📌 階段は建物本体から除外してFEM解析を実行します")

        # 個別パーツのオブジェクト作成（色付き）
        # 基礎
        foundation_obj = doc.addObject("Part::Feature", "Foundation")
        foundation_obj.Shape = foundation
        foundation_obj.Visibility = True
        set_part_color(foundation_obj, (0.6, 0.6, 0.6))  # グレー
        
        # 1階床
        floor1_obj = doc.addObject("Part::Feature", "Floor1")
        floor1_obj.Shape = floor1
        floor1_obj.Visibility = True
        set_part_color(floor1_obj, (0.8, 0.8, 0.8))  # ライトグレー
        
        # 2階床
        floor2_obj = doc.addObject("Part::Feature", "Floor2")
        floor2_obj.Shape = floor2
        floor2_obj.Visibility = True
        set_part_color(floor2_obj, (0.8, 0.8, 0.8))  # ライトグレー
        
        # 柱（複数の柱を1つのオブジェクトに統合）
        if columns:
            columns_shape = columns[0]
            for col in columns[1:]:
                try:
                    columns_shape = columns_shape.fuse(col)
                except:
                    pass
            columns_obj = doc.addObject("Part::Feature", "Columns")
            columns_obj.Shape = columns_shape
            columns_obj.Visibility = True
            set_part_color(columns_obj, (0.5, 0.5, 0.5))  # 濃いグレー
        
        # 壁（複数の壁を1つのオブジェクトに統合）
        if walls:
            walls_shape = walls[0]
            for wall in walls[1:]:
                try:
                    walls_shape = walls_shape.fuse(wall)
                except:
                    pass
            walls_obj = doc.addObject("Part::Feature", "Walls")
            walls_obj.Shape = walls_shape
            walls_obj.Visibility = True
            set_part_color(walls_obj, (0.9, 0.85, 0.75))  # ベージュ
        
        # 屋根
        roof_obj = doc.addObject("Part::Feature", "RoofSlab")
        roof_obj.Shape = roof
        roof_obj.Visibility = True
        set_part_color(roof_obj, (0.6, 0.7, 0.9))  # 青みがかったグレー
        
        # バルコニー
        if balcony is not None:
            balcony_obj = doc.addObject("Part::Feature", "Balcony")
            balcony_obj.Shape = balcony
            balcony_obj.Visibility = True
            set_part_color(balcony_obj, (0.7, 0.9, 0.7))  # 薄い緑
        
        # FEM解析用の統合建物（非表示）
        building_obj = doc.addObject("Part::Feature", "AnalysisBuilding")
        building_obj.Shape = building_shape  # 基礎を含む完全な形状
        building_obj.Visibility = False  # FEM解析用なので非表示

        safe_set_display_mode(building_obj, "Shaded")
        safe_set_display_mode(roof_obj, "Shaded")

        import os
        import time
        detailed_log = os.environ.get('FEM_DETAILED_LOG', '') == '1'
        sample_id = os.environ.get('FEM_SAMPLE_ID', '')
        if detailed_log:
            print(f"{sample_id} ⏱️ doc.recompute() [建物モデル生成後] 実行開始: {time.strftime('%H:%M:%S')}")
        
        doc.recompute()
        
        if detailed_log:
            print(f"{sample_id} ✅ doc.recompute() [建物モデル生成後] 完了: {time.strftime('%H:%M:%S')}")
        
        # 視点を調整して建物全体を表示
        safe_gui_operations(doc)

        # メタ情報（階段を除いた建物本体のみ）
        volume_m3 = building_shape.Volume / 1e9
        mass_kg = volume_m3 * 2400
        face_count = len(building_shape.Faces)
        
        # 階段の体積情報（参考用）
        stair_volume_m3 = staircase.Volume / 1e9
        if VERBOSE_OUTPUT:
            print(f"📊 階段体積: {stair_volume_m3:.3f} m³（解析から除外）")
        
        building_info = {
            'volume': volume_m3,
            'mass': mass_kg,
            'faces': face_count,
            'span_length': max(Lx, Ly),
            'asymmetry_factor': abs(Lx - Ly) / max(Lx, Ly),
            'opening_complexity': 2.5,  # 開口部減少
            'structural_irregularity': 1.8,  # ピロティ化による不整形度
            'has_cantilever': False,  # キャンチレバーなし
            'floor_opening_ratio': 0.7,  # 1階の開放率増加
            'piloti_structure': True,  # ピロティ構造フラグ追加
            'wall_tilt_angle': wall_tilt_angle,  # 東面壁の傾斜角度
            'window_ratio_2f': window_ratio_2f,  # 2階窓面積率
            # かまぼこ屋根パラメータ
            'roof_type': 'barrel',
            'roof_morph': roof_morph,
            'roof_shift': roof_shift,
            'roof_curvature': calculate_roof_curvature(roof_morph),
            'roof_structural_efficiency': calculate_roof_efficiency(roof_morph, roof_shift),
            # コスト計算用に追加
            'bc_mm': bc_mm,
            'hc_mm': hc_mm,
            'tf_mm': tf_mm,
            'tr_mm': tr_mm,
            'tw_ext_mm': tw_ext_mm,
        }

        return doc, building_obj, building_info

    except Exception:
        if VERBOSE_OUTPUT:

            traceback.print_exc()
        return None, None, {}




def is_gui_mode():
    """GUIモードが有効かどうかを判定"""
    if not GUI_AVAILABLE:
        return False
    try:
        # ActiveDocumentが存在し、かつアクセス可能かチェック
        return hasattr(Gui, 'ActiveDocument') and Gui.ActiveDocument is not None
    except (AttributeError, RuntimeError):
        return False


def save_building_snapshot(doc, filename_base="piloti_building", view_angle="isometric"):
    """
    建物の3Dビューをスナップショット画像として保存
    
    Args:
        doc: FreeCADドキュメント
        filename_base: 保存ファイル名のベース
        view_angle: ビューアングル ("isometric", "front", "top", "right")
    """
    if not is_gui_mode():
        if VERBOSE_OUTPUT:
            print("⚠️ GUIモードではないため、スナップショットを保存できません")
        return False
    
    try:
        import FreeCADGui as Gui
        
        # アクティブビューを取得
        if not hasattr(Gui, 'ActiveDocument') or Gui.ActiveDocument is None:
            return False
            
        view = Gui.ActiveDocument.ActiveView
        if view is None:
            return False
        
        # ビューアングルを設定
        if view_angle == "isometric":
            view.viewIsometric()
        elif view_angle == "front":
            view.viewFront()
        elif view_angle == "top":
            view.viewTop()
        elif view_angle == "right":
            view.viewRight()
        
        # ビューにフィット
        Gui.SendMsgToActiveView("ViewFit")
        
        # 背景色を白に設定（オプション）
        view.setBackgroundColor((1.0, 1.0, 1.0, 1.0))
        
        # ファイル名にタイムスタンプを追加
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = f"{filename_base}_snapshot_{timestamp}.png"
        
        # スナップショットを保存
        # 解像度を指定（幅, 高さ）
        view.saveImage(snapshot_path, 1920, 1080, "Transparent")
        
        if VERBOSE_OUTPUT:
            print(f"✅ スナップショットを保存しました: {snapshot_path}")
        
        # 複数アングルの保存（オプション）
        if view_angle == "isometric":
            # 追加で他のアングルも保存
            angles = ["front", "top", "right"]
            for angle in angles:
                if angle == "front":
                    view.viewFront()
                elif angle == "top":
                    view.viewTop()
                elif angle == "right":
                    view.viewRight()
                
                Gui.SendMsgToActiveView("ViewFit")
                angle_path = f"{filename_base}_snapshot_{timestamp}_{angle}.png"
                view.saveImage(angle_path, 1920, 1080, "Transparent")
                if VERBOSE_OUTPUT:
                    print(f"✅ {angle}ビューを保存: {angle_path}")
        
        # 最後にアイソメトリックビューに戻す
        view.viewIsometric()
        Gui.SendMsgToActiveView("ViewFit")
        
        return True
        
    except Exception as e:
        if VERBOSE_OUTPUT:
            print(f"❌ スナップショット保存エラー: {e}")
        return False

def safe_remove_object(doc, obj_name):
    """安全にオブジェクトを削除する"""
    try:
        obj = doc.getObject(obj_name)
        if obj:
            doc.removeObject(obj.Name)
            if VERBOSE_OUTPUT:
                print(f"✅ {obj_name} を削除しました")
            return True
    except Exception as e:
        if VERBOSE_OUTPUT:
            print(f"⚠️ {obj_name} の削除でエラー: {e}")
    return False

def safe_set_visibility(obj, visible=True):
    """安全にオブジェクトの可視性を設定する（GUIモード時のみ）"""
    if obj is None:
        return False
    
    if not is_gui_mode():
        if VERBOSE_OUTPUT:
            print(f"コマンドラインモード: {obj.Name} の可視性設定をスキップ")
        return True
    
    try:
        if hasattr(obj, 'ViewObject') and obj.ViewObject is not None:
            obj.ViewObject.Visibility = visible
            return True
        else:
            if VERBOSE_OUTPUT:
                print(f"⚠️ {obj.Name} に有効なViewObjectがありません")
    except (AttributeError, RuntimeError) as e:
        if VERBOSE_OUTPUT:
            print(f"可視性設定エラー ({obj.Name}): {e}")
    return False

def safe_set_display_mode(obj, mode="Shaded"):
    """安全にオブジェクトの表示モードを設定する（GUIモード時のみ）"""
    if obj is None:
        return False
    
    if not is_gui_mode():
        if VERBOSE_OUTPUT:
            print(f"コマンドラインモード: {obj.Name} の表示モード設定をスキップ")
        return True
        
    try:
        if hasattr(obj, 'ViewObject') and obj.ViewObject is not None:
            if hasattr(obj.ViewObject, 'DisplayMode'):
                obj.ViewObject.DisplayMode = mode
            
            # 建物パーツの場合は見やすい設定にする
            if mode == "Shaded":
                if hasattr(obj.ViewObject, 'ShapeColor'):
                    obj.ViewObject.ShapeColor = (0.85, 0.85, 0.9)  # 薄いグレー
                if hasattr(obj.ViewObject, 'Transparency'):
                    obj.ViewObject.Transparency = 0  # 不透明
            
            return True
        else:
            if VERBOSE_OUTPUT:
                print(f"⚠️ {obj.Name} に有効なViewObjectがありません")
    except (AttributeError, RuntimeError) as e:
        if VERBOSE_OUTPUT:
            print(f"表示モード設定エラー ({obj.Name}): {e}")
    return False

def safe_gui_operations(doc):
    """GUI操作を安全に実行する（GUIモード時のみ）"""
    if not is_gui_mode():
        if VERBOSE_OUTPUT:
            print("コマンドラインモード: GUI操作をスキップ")
        return True
    
    try:
        if hasattr(Gui, 'ActiveDocument') and Gui.ActiveDocument is not None:
            if hasattr(Gui.ActiveDocument, 'ActiveView') and Gui.ActiveDocument.ActiveView is not None:
                Gui.ActiveDocument.ActiveView.viewIsometric()
                Gui.SendMsgToActiveView("ViewFit")
                return True
    except (AttributeError, RuntimeError) as e:
        if VERBOSE_OUTPUT:
            print(f"GUI操作エラー: {e}")
    return False

def create_load_visualization_arrows(doc, building_info):
    """荷重条件を矢印で可視化する"""
    try:
        Lx = building_info.get('span_length', 8.0) * 1000  # mm
        Ly = building_info.get('span_length', 8.0) * 1000  # mm (Lxに合わせる)
        
        # RoofSlabオブジェクトが存在すればそのZMaxを使用
        roof_obj = doc.getObject("RoofSlab")
        if roof_obj and hasattr(roof_obj, 'Shape') and roof_obj.Shape:
            roof_height = roof_obj.Shape.BoundBox.ZMax
        else:
            # building_infoにH1, H2がない場合に備えてLxから適当に推測
            if 'H1_mm' in building_info and 'H2_mm' in building_info and 'tr_mm' in building_info:
                 roof_height = building_info['H1_mm'] + building_info['H2_mm'] + building_info['tr_mm']
            else:
                roof_height = 6500 # 適当なデフォルト値 mm (Lx=8m, H1=3.5, H2=3.0 -> 6.5m)
        
        arrows = []
        
        # 屋根荷重の矢印を作成（下向き）
        arrow_spacing = 1000  # 1m間隔
        arrow_length = 500   # 矢印の長さ
        arrow_radius = 50    # 矢印の太さ
        
        num_arrows_x = max(1, int(Lx / arrow_spacing))
        num_arrows_y = max(1, int(Ly / arrow_spacing))
        
        # 荷重表示位置のオフセット (建物の中心を考慮)
        # 荷重は建物のLx, Ly範囲内に収まるように調整
        offset_x = (Lx - (num_arrows_x - 1) * arrow_spacing) / 2 if num_arrows_x > 1 else Lx / 2
        offset_y = (Ly - (num_arrows_y - 1) * arrow_spacing) / 2 if num_arrows_y > 1 else Ly / 2

        for i in range(num_arrows_x):
            for j in range(num_arrows_y):
                # 矢印のX, Y位置を建物の範囲内に配置
                x = offset_x + i * arrow_spacing
                y = offset_y + j * arrow_spacing
                z = roof_height + 100  # 屋根から少し上
                
                # 矢印のシャフト部分
                shaft = Part.makeCylinder(arrow_radius, arrow_length)
                shaft.translate(App.Vector(x, y, z))
                
                # 矢印の先端部分（円錐）
                cone = Part.makeCone(arrow_radius * 2, 0, arrow_radius * 2)
                cone.translate(App.Vector(x, y, z - arrow_length))
                
                # 矢印を結合
                arrow = shaft.fuse(cone)
                arrows.append(arrow)
        
        if arrows:
            # すべての矢印を一つのオブジェクトに結合
            combined_arrows = arrows[0]
            for arrow in arrows[1:]:
                try:
                    combined_arrows = combined_arrows.fuse(arrow)
                except:
                    continue
            
            # 荷重矢印オブジェクトを作成
            load_arrows = doc.addObject("Part::Feature", "LoadArrows")
            load_arrows.Shape = combined_arrows
            
            # 矢印の色を赤に設定（GUIモード時のみ）
            safe_set_display_mode(load_arrows, "Shaded")
            if is_gui_mode() and hasattr(load_arrows, 'ViewObject') and load_arrows.ViewObject:
                try:
                    load_arrows.ViewObject.ShapeColor = (1.0, 0.0, 0.0)  # 赤色
                    load_arrows.ViewObject.Transparency = 0
                except:
                    pass
            
            if VERBOSE_OUTPUT:
                print("✅ 荷重矢印を作成しました")
            return load_arrows
            
    except Exception as e:
        if VERBOSE_OUTPUT:
            print(f"荷重矢印作成エラー: {e}")
        if VERBOSE_OUTPUT:

            traceback.print_exc()
    
    return None

def create_support_visualization(doc, building_info):
    """支持条件を可視化する"""
    try:
        Lx = building_info.get('span_length', 8.0) * 1000  # mm
        Ly = building_info.get('span_length', 8.0) * 1000  # mm (Lxに合わせる)
        
        # 固定支持記号を作成（三角形のパターン）
        support_symbols = []
        symbol_size = 200
        spacing = 1000
        
        num_symbols_x = max(1, int(Lx / spacing))
        num_symbols_y = max(1, int(Ly / spacing))
        
        # 基礎の底面のZMinを実際の建物のBoundBoxから取得する方が確実
        building_obj = doc.getObject("AnalysisBuilding")
        if building_obj and hasattr(building_obj, 'Shape') and building_obj.Shape:
            base_z = building_obj.Shape.BoundBox.ZMin
        else:
            base_z = -400 # 基礎の仮の深さ

        # 支持記号の位置を建物の範囲内に配置
        # 支持記号の配置を柱の配置と一致させるか、基礎の四隅に配置する
        # ここでは基礎の四隅と中心に配置する例
        support_positions = [
            (0, 0), (Lx, 0), (0, Ly), (Lx, Ly), # 基礎の四隅
            (Lx/2, Ly/2) # 基礎の中心
        ]

        for x_coord, y_coord in support_positions:
            x = x_coord
            y = y_coord
            z = base_z - 200  # 基礎の底面より少し下
            
            # 三角形の支持記号（3つの点で三角形を作成）
            points = []
            for k in range(3):
                angle = k * 2 * math.pi / 3
                px = x + symbol_size * math.cos(angle)
                py = y + symbol_size * math.sin(angle)
                points.append(App.Vector(px, py, z))
            
            # 3点から三角形を作成
            try:
                triangle_wire = Part.makePolygon(points + [points[0]])  # 閉じた形状
                triangle_face = Part.Face(triangle_wire)
                triangle = triangle_face.extrude(App.Vector(0, 0, 50))
                support_symbols.append(triangle)
            except Exception as e:
                if VERBOSE_OUTPUT:
                    print(f"三角形作成エラー: {e}")
                # 代替として円柱を使用
                cylinder = Part.makeCylinder(symbol_size/2, 50)
                cylinder.translate(App.Vector(x, y, z))
                support_symbols.append(cylinder)
        
        if support_symbols:
            # すべての支持記号を結合
            combined_supports = support_symbols[0]
            for symbol in support_symbols[1:]:
                try:
                    combined_supports = combined_supports.fuse(symbol)
                except:
                    continue
            
            # 支持記号オブジェクトを作成
            support_obj = doc.addObject("Part::Feature", "SupportSymbols")
            support_obj.Shape = combined_supports
            
            # 支持記号の色を緑に設定（GUIモード時のみ）
            safe_set_display_mode(support_obj, "Shaded")
            if is_gui_mode() and hasattr(support_obj, 'ViewObject') and support_obj.ViewObject:
                try:
                    support_obj.ViewObject.ShapeColor = (0.0, 1.0, 0.0)  # 緑色
                    support_obj.ViewObject.Transparency = 0
                except:
                    pass
            
            if VERBOSE_OUTPUT:
                print("✅ 支持記号を作成しました")
            return support_obj
            
    except Exception as e:
        if VERBOSE_OUTPUT:
            print(f"支持記号作成エラー: {e}")
        if VERBOSE_OUTPUT:

            traceback.print_exc()
    
    return None

def setup_deterministic_fem():
    """FEM解析を決定論的にするためのセットアップ"""
    random.seed(12345)
    try:
        np.random.seed(12345)
    except:
        pass
    os.environ['GMSH_RANDOM_SEED'] = '12345'
    os.environ['CCX_NPROC_EQUATION_SOLVER'] = '1'
    os.environ['CCX_NPROC_RESULTS'] = '1'
    os.environ['OMP_NUM_THREADS'] = '1'
    os.environ['OPENBLAS_NUM_THREADS'] = '1'
    os.environ['MKL_NUM_THREADS'] = '1'
    return True

def create_external_stairs(Lx_mm, Ly_mm, H1_mm, H2_mm, tf_mm):
    """外部階段を作成する"""
    stairs = []
    
    # 階段の基本パラメータ
    stair_width = 1200  # 階段幅 1.2m
    step_height = 180   # 蹴上 18cm
    step_depth = 280    # 踏面 28cm
    
    # 2階フロアレベル（H1_mm）に正確に到達する段数を計算
    target_height = H1_mm  # 2階フロアレベル
    num_steps = int(target_height / step_height)
    
    # 最終段の高さが目標高さに正確に一致するよう調整
    if num_steps * step_height < target_height:
        num_steps += 1
    
    # 実際の段高を調整して目標高さに合わせる
    actual_step_height = target_height / num_steps
    
    if VERBOSE_OUTPUT:
        print(f"🎯 階段: 目標高さ: {target_height}mm")
    if VERBOSE_OUTPUT:
        print(f"📊 階段: 段数: {num_steps}段")
    if VERBOSE_OUTPUT:
        print(f"📏 階段: 調整後段高: {actual_step_height:.1f}mm")
    
    # 階段の配置（建物の西側からアクセス）
    # stair_start_x は建物のX=0より外側から開始
    stair_start_x = - (num_steps * step_depth + 500) # 階段の全長を考慮して開始位置を決定
    stair_start_y = Ly_mm * 0.5 - stair_width / 2 # 建物のY方向中央に配置
    
    # 各段を作成（調整後の段高を使用）- X方向に向かって上昇
    for i in range(num_steps):
        step_z = i * actual_step_height
        step_x = stair_start_x + i * step_depth
        
        # 段の作成（踏面 + 蹴上）
        tread = Part.makeBox(step_depth, stair_width, 50)  # 踏面
        tread.translate(App.Vector(step_x, stair_start_y, step_z))
        stairs.append(tread)
        
        # 蹴上部分
        if i < num_steps - 1:
            riser = Part.makeBox(50, stair_width, actual_step_height)
            riser.translate(App.Vector(step_x + step_depth - 50, stair_start_y, step_z))
            stairs.append(riser)
    
    # 手すり
    handrail_height = 900
    handrail_posts = []
    
    # 手すり支柱（階段の傾斜に沿って配置）
    # num_steps が小さい場合は、支柱の間隔を調整するか数を減らす
    post_interval_steps = max(1, num_steps // 3)
    
    for i in range(0, num_steps + 1, post_interval_steps): # 階段の開始から終了まで
        post_x = stair_start_x + i * step_depth
        post_base_z = i * actual_step_height
        
        # 支柱の高さを2階フロアレベルを超えないように制限
        max_post_top = target_height + tf_mm # 2階フロアの上面まで
        post_top_z = min(post_base_z + handrail_height, max_post_top)
        
        current_post_height = post_top_z - post_base_z
        
        if current_post_height > 100: # 最低限の高さがある場合のみ作成
            # 左側手すり支柱
            post_left = Part.makeCylinder(40, current_post_height)
            post_left.translate(App.Vector(post_x, stair_start_y - 50, post_base_z))
            handrail_posts.append(post_left)
            
            # 右側手すり支柱
            post_right = Part.makeCylinder(40, current_post_height)
            post_right.translate(App.Vector(post_x, stair_start_y + stair_width + 50, post_base_z))
            handrail_posts.append(post_right)
    
    # 手すり本体（階段の傾斜に沿って作成）
    handrail_points_left = []
    handrail_points_right = []
    
    for i in range(num_steps + 1): # 階段の開始と各段の終端
        point_x = stair_start_x + i * step_depth
        point_z = i * actual_step_height + handrail_height # 基準高さからの手すり高さ
        
        # 2階フロアの上面までで制限
        point_z = min(point_z, H1_mm + tf_mm)

        handrail_points_left.append(App.Vector(point_x, stair_start_y - 50, point_z))
        handrail_points_right.append(App.Vector(point_x, stair_start_y + stair_width + 50, point_z))

    # 手すりセグメントの作成
    for points in [handrail_points_left, handrail_points_right]:
        for i in range(len(points) - 1):
            start_point = points[i]
            end_point = points[i+1]
            
            direction = end_point.sub(start_point)
            length = direction.Length
            
            if length > 0.1: # 短すぎるセグメントはスキップ
                segment = Part.makeCylinder(25, length)
                
                # Z軸方向の円柱をdirection方向に向ける
                z_axis = App.Vector(0, 0, 1)
                direction_normalized = direction.normalize()
                
                rotation_axis = z_axis.cross(direction_normalized)
                if rotation_axis.Length > 0.001:
                    rotation_angle = math.acos(z_axis.dot(direction_normalized))
                    segment.rotate(App.Vector(0, 0, 0), rotation_axis, math.degrees(rotation_angle))
                
                segment.translate(start_point)
                handrail_posts.append(segment)

    # 階段と2階フロアの接合部を作成（プラットフォーム）
    # 階段の最終段が建物の敷地(X=0)を越えて建物内部に繋がる想定
    stair_end_x_at_platform = stair_start_x + num_steps * step_depth # 階段の最終段のX座標
    
    platform_x_start = max(0, stair_end_x_at_platform) # 建物のX=0から、または階段の終点から
    platform_depth_needed = 800 # 建物内部への奥行き
    
    # 階段の終点が建物の外側にある場合、プラットフォームは建物内部へ伸びる
    if stair_end_x_at_platform < 0:
        platform_x_start = 0 # 建物のX=0から開始
        platform_depth_actual = platform_depth_needed - stair_end_x_at_platform # 階段の終点から建物の端までの距離 + 必要な奥行き
    else:
        # 階段の終点が建物内部にある場合、プラットフォームはそこから始まる
        platform_x_start = stair_end_x_at_platform
        platform_depth_actual = platform_depth_needed

    platform_y = stair_start_y
    platform_width_for_cut = stair_width + 200 # 穴開け用に階段幅より少し広めに
    platform_z = H1_mm # 2階フロアレベル
    platform_height = 50 # プラットフォームの厚み

    connection_platform = Part.makeBox(platform_depth_actual, platform_width_for_cut, platform_height)
    connection_platform.translate(App.Vector(platform_x_start, platform_y - 100, platform_z)) # Y方向も少し広げる
    stairs.append(connection_platform)
    
    # 2階フロア入口の開口部を作成するための情報を記録
    stair_connection_info = {
        'platform_x': platform_x_start,
        'platform_y': platform_y - 100, # 穴開け用のY開始点
        'platform_z': platform_z,
        'platform_width': platform_width_for_cut, # Y方向の穴のサイズ
        'platform_depth': platform_depth_actual,   # X方向の穴のサイズ
        'entrance_needed': True
    }
    
    if VERBOSE_OUTPUT:
        print(f"🔗 階段接続プラットフォーム作成: X={platform_x_start}, Y={platform_y - 100}, Z={platform_z}, Width(X)={platform_depth_actual}, Depth(Y)={platform_width_for_cut}")
    
    # 階段と手すりを結合
    all_stair_parts = stairs + handrail_posts
    
    return all_stair_parts, stair_connection_info


def setup_basic_fem_analysis(doc: Any, building: Any, building_info: Dict[str, Any] = None) -> (Any, Any):
    """基本的なFEM解析設定（かまぼこ屋根対応版）"""
    if not (FEM_AVAILABLE and building):
        return None, None

    try:
        # 解析設定
        analysis = ObjectsFem.makeAnalysis(doc, "StructuralAnalysis")

        # ソルバー
        try:
            solver = ObjectsFem.makeSolverCalculixCcxTools(doc)
        except AttributeError:
            try:
                solver = ObjectsFem.makeSolverCalculix(doc)
            except AttributeError:
                solver = ObjectsFem.makeSolverObjectCalculix(doc)
        
        if solver:
            solver.AnalysisType = "static"
            analysis.addObject(solver)

        # 材料定義
        try:
            mat = ObjectsFem.makeMaterialSolid(doc, "Concrete")
            mat.Material = {
                'Name': "Concrete C35",
                'YoungsModulus': "30000 MPa",
                'PoissonRatio': "0.2",
                'Density': "2400 kg/m^3"
            }
            analysis.addObject(mat)
        except Exception as e:
            if VERBOSE_OUTPUT:
                print(f"材料定義エラー: {e}")
            if VERBOSE_OUTPUT:

                traceback.print_exc()

        # 境界条件（基礎固定）- より確実な方法
        try:
            fixed = ObjectsFem.makeConstraintFixed(doc, "FixedSupport")
            
            # 建物（基礎を含む）の底面を固定
            faces = building.Shape.Faces
            min_z = min(f.BoundBox.ZMin for f in faces)
            tol = 10  # 許容誤差
            
            # 基礎の底面Faceを探す
            base_faces = [
                (building, f"Face{i+1}")
                for i, f in enumerate(faces)
                if abs(f.BoundBox.ZMin - min_z) < tol and f.BoundBox.ZMax < 0  # Zが負の値（基礎部分）
            ]
            
            if base_faces:
                fixed.References = base_faces
                if VERBOSE_OUTPUT:
                    print(f"✅ 基礎底面を固定: {len(base_faces)}面")
                if VERBOSE_OUTPUT:
                    print(f"   固定面のZ座標: {min_z:.1f} mm")
            else:
                # フォールバック：頂点を固定
                vertices = building.Shape.Vertexes
                base_vertices = [
                    (building, f"Vertex{i+1}")
                    for i, v in enumerate(vertices)
                    if abs(v.Point.z - min_z) < tol
                ]
                if base_vertices:
                    fixed.References = base_vertices
                    if VERBOSE_OUTPUT:
                        print(f"✅ 基礎底部の頂点を固定: {len(base_vertices)}点")
                    if VERBOSE_OUTPUT:
                        print(f"   固定頂点のZ座標: {min_z:.1f} mm")
                else:
                    if VERBOSE_OUTPUT:
                        print("❌ 固定条件を設定できませんでした")
                    if VERBOSE_OUTPUT:
                        print(f"   建物の最下部Z座標: {min_z:.1f} mm")
            
            analysis.addObject(fixed)
            if VERBOSE_OUTPUT:
                print(f"固定条件の参照数: {len(fixed.References) if hasattr(fixed, 'References') else 0}")
            
        except Exception as e:
            if VERBOSE_OUTPUT:
                print(f"固定支持条件設定エラー: {e}")
            if VERBOSE_OUTPUT:

                traceback.print_exc()

        # 荷重設定
        # 自重を有効化（複数の方法を試す）
        self_weight_applied = False
        
        # 方法1: 重力を個別パーツに適用
        try:
            if VERBOSE_OUTPUT:
                print("⚙️ 個別パーツへの重力設定を試行中...")
            gravity_loads = []
            
            # 各主要パーツに対して重力を設定
            part_names = ["RoofSlab", "AnalysisBuilding"]
            for part_name in part_names:
                part = doc.getObject(part_name)
                if part and hasattr(part, 'Shape'):
                    try:
                        gravity = ObjectsFem.makeConstraintForce(doc, f"Gravity_{part_name}")
                        gravity.Direction = App.Vector(0, 0, -1)
                        gravity.Force = "1"  # 単位力
                        gravity.References = [(part, "Solid")]
                        gravity.ForceType = "gravity"  # 重力タイプを指定
                        analysis.addObject(gravity)
                        gravity_loads.append(gravity)
                        if VERBOSE_OUTPUT:
                            print(f"✅ {part_name}に重力を設定")
                    except:
                        pass
            
            if gravity_loads:
                self_weight_applied = True
                if VERBOSE_OUTPUT:
                    print(f"✅ {len(gravity_loads)}個のパーツに重力を設定しました")
        except Exception as e1:
            if VERBOSE_OUTPUT:
                print(f"⚠️ 個別パーツへの重力設定失敗: {e1}")
            
        # 方法2: 圧力として自重を模擬
        if not self_weight_applied:
            try:
                if VERBOSE_OUTPUT:
                    print("⚙️ 圧力荷重として自重を模擬...")
                # 上面に下向きの圧力を加える
                top_faces = []
                for i, f in enumerate(building.Shape.Faces):
                    if f.normalAt(0, 0).z > 0.5:  # 上向きの面
                        top_faces.append((building, f"Face{i+1}"))
                
                if top_faces:
                    self_weight_pressure = ObjectsFem.makeConstraintPressure(doc, "SelfWeightPressure")
                    self_weight_pressure.References = top_faces
                    # 建物高さと密度から概算圧力を計算
                    # 例: 高さ6.5m × 2400kg/m³ × 9.81m/s² ≈ 153kPa
                    self_weight_pressure.Pressure = "150000 Pa"
                    analysis.addObject(self_weight_pressure)
                    self_weight_applied = True
                    if VERBOSE_OUTPUT:
                        print("✅ 圧力荷重として自重を設定しました: 150 kPa")
            except Exception as e2:
                if VERBOSE_OUTPUT:
                    print(f"⚠️ 圧力荷重による自重設定失敗: {e2}")

        if not self_weight_applied:
            if VERBOSE_OUTPUT:
                print("❌ 警告: 自重が設定されていません！安全率が異常に高くなります。")

        # 屋根荷重（かまぼこ屋根対応）
        try:
            roof = doc.getObject("RoofSlab")
            if roof:
                roof_pressure = ObjectsFem.makeConstraintPressure(doc, "RoofPressure")
                roof_faces = []
                
                # かまぼこ屋根の曲面に対応
                for i, f in enumerate(roof.Shape.Faces):
                    normal = f.normalAt(0.5, 0.5)  # 面の中心での法線
                    
                    # 上向き成分を持つ面（屋根の外側）に荷重を適用
                    if normal.z > 0.1:  # わずかに上向きの面も含む
                        roof_faces.append((roof, f"Face{i+1}"))
                
                if roof_faces:
                    roof_pressure.References = roof_faces
                    
                    # 屋根形状による荷重係数の調整
                    load_factor = 1.0
                    if building_info:
                        roof_morph = building_info.get('roof_morph', 0.5)
                        if roof_morph < 0.33:  # 平らに近い
                            load_factor = 1.0
                        elif roof_morph < 0.67:  # 標準的なかまぼこ
                            load_factor = 0.9  # 雪が滑りやすい
                        else:  # 急勾配
                            load_factor = 0.8  # さらに雪が滑りやすい
                    
                    roof_pressure.Pressure = f"{10000 * load_factor} Pa"
                    analysis.addObject(roof_pressure)
                    if VERBOSE_OUTPUT:
                        print(f"✅ かまぼこ屋根荷重を設定: {10 * load_factor:.1f} kPa")
                    if VERBOSE_OUTPUT:
                        print(f"   荷重面数: {len(roof_faces)}")
                else:
                    if VERBOSE_OUTPUT:
                        print("⚠️ 屋根の荷重面が見つかりませんでした")
            else:
                if VERBOSE_OUTPUT:
                    print("⚠️ RoofSlabオブジェクトが見つかりませんでした")
        except Exception as e:
            if VERBOSE_OUTPUT:
                print(f"屋根荷重設定エラー: {e}")
            if VERBOSE_OUTPUT:

                traceback.print_exc()

        # バルコニー活荷重（建築基準法: 180kg/m² = 1800 Pa）
        if building_info and building_info.get('has_balcony', False):
            try:
                # バルコニーは建物本体に統合されているため、AnalysisBuildingから面を探す
                balcony_depth = building_info.get('balcony_depth', 0) * 1000  # m -> mm
                if balcony_depth > 0:
                    balcony_pressure = ObjectsFem.makeConstraintPressure(doc, "BalconyLiveLoad")
                    balcony_faces = []
                    
                    # バルコニー床面を検出（西側、2階レベルの上向き面）
                    for i, f in enumerate(building.Shape.Faces):
                        # 面の中心点を取得
                        u_mid = (f.ParameterRange[0] + f.ParameterRange[1]) / 2
                        v_mid = (f.ParameterRange[2] + f.ParameterRange[3]) / 2
                        center = f.valueAt(u_mid, v_mid)
                        normal = f.normalAt(u_mid, v_mid)
                        
                        # バルコニー床面の条件：
                        # 1. 上向きの面（normal.z > 0.9）
                        # 2. 西側（center.x < 0）
                        # 3. 2階レベル（H1_mm付近）
                        H1_mm = building_info.get('H1_mm', 3000)
                        if (normal.z > 0.9 and
                            center.x < -100 and  # 西側のバルコニー領域
                            abs(center.z - H1_mm) < 200):  # 2階床レベル付近
                            balcony_faces.append((building, f"Face{i+1}"))
                    
                    if balcony_faces:
                        balcony_pressure.References = balcony_faces
                        balcony_pressure.Pressure = "1800 Pa"  # 建築基準法の活荷重
                        analysis.addObject(balcony_pressure)
                        if VERBOSE_OUTPUT:
                            print(f"✅ バルコニー活荷重を設定: 1.8 kPa (建築基準法準拠)")
                        if VERBOSE_OUTPUT:
                            print(f"   荷重面数: {len(balcony_faces)}")
                    else:
                        if VERBOSE_OUTPUT:
                            print("⚠️ バルコニー床面が検出されませんでした")
            except Exception as e:
                if VERBOSE_OUTPUT:
                    print(f"バルコニー活荷重設定エラー: {e}")
                if VERBOSE_OUTPUT:

                    traceback.print_exc()

        # メッシュ設定
        mesh = ObjectsFem.makeMeshGmsh(doc, "BuildingMesh")
        shape_obj = doc.addObject("Part::Feature", "MeshShape")
        shape_obj.Shape = building.Shape
        mesh.Shape = shape_obj
        analysis.addObject(mesh)
        
        # メッシュサイズを少し粗くして、複雑な形状でのメッシュ生成成功率を上げる
        mesh.CharacteristicLengthMax = "600.0 mm"  # より粗く
        mesh.CharacteristicLengthMin = "200.0 mm" # より粗く
        
        import os
        import time
        detailed_log = os.environ.get('FEM_DETAILED_LOG', '') == '1'
        sample_id = os.environ.get('FEM_SAMPLE_ID', '')
        if detailed_log:
            print(f"{sample_id} ⏱️ doc.recompute() [FEM解析設定後] 実行開始: {time.strftime('%H:%M:%S')}")
        
        doc.recompute() # Gmshメッシュオブジェクトのプロパティが更新される
        
        if detailed_log:
            print(f"{sample_id} ✅ doc.recompute() [FEM解析設定後] 完了: {time.strftime('%H:%M:%S')}")
        safe_set_visibility(mesh, False) # 通常はメッシュを非表示にする

        return analysis, mesh

    except Exception:
        if VERBOSE_OUTPUT:

            traceback.print_exc()
        return None, None


def check_fixed_nodes(doc: Any, mesh_obj: Any) -> None:
    """固定条件が適用されているノードを確認（デバッグ用）"""
    try:
        fixed_constraint = doc.getObject("FixedSupport")
        if fixed_constraint and hasattr(fixed_constraint, 'References'):
            if VERBOSE_OUTPUT:
                print("\n📍 固定条件のデバッグ情報:")
            if VERBOSE_OUTPUT:
                print(f"  参照数: {len(fixed_constraint.References)}")
            for i, ref in enumerate(fixed_constraint.References):
                if VERBOSE_OUTPUT:
                    print(f"  参照 {i+1}: {ref[0].Name} - {ref[1]}")
            
            # メッシュの最下部ノードを確認
            if mesh_obj and hasattr(mesh_obj, 'FemMesh'):
                nodes = mesh_obj.FemMesh.Nodes
                if nodes:
                    z_coords = [nodes[node_id].z for node_id in nodes]
                    min_z = min(z_coords)
                    bottom_nodes = [node_id for node_id in nodes if abs(nodes[node_id].z - min_z) < 10]
                    if VERBOSE_OUTPUT:
                        print(f"  メッシュ最下部のノード数: {len(bottom_nodes)}")
                    if VERBOSE_OUTPUT:
                        print(f"  最下部Z座標: {min_z:.1f} mm")
    except Exception as e:
        if VERBOSE_OUTPUT:
            print(f"⚠️ 固定ノードのチェック中にエラー: {e}")

def run_mesh_generation(doc: Any, mesh_obj: Any) -> bool:
    """メッシュ生成を実行"""
    import os
    import time
    detailed_log = os.environ.get('FEM_DETAILED_LOG', '') == '1'
    sample_id = os.environ.get('FEM_SAMPLE_ID', '')
    
    if detailed_log:
        print(f"{sample_id} 🔍 メッシュ生成開始: {time.strftime('%H:%M:%S')}")
    
    if not mesh_obj:
        if VERBOSE_OUTPUT:
            print("❌ メッシュオブジェクトが存在しません。")
        return False

    # FEMログを抑制するため標準出力をリダイレクト
    if not VERBOSE_OUTPUT:
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

    try:
        # building_obj の形状有効性を再チェック (evaluate_building で既にチェック済みだが念のため)
        building_obj = doc.getObject("AnalysisBuilding")
        if not building_obj or not building_obj.Shape.isValid():
            if VERBOSE_OUTPUT:
                print("❌ メッシュ生成をスキップ: 建物モデルの形状が不正です。")
            return False

        # gmshtools の利用可能性を判定し、利用を試みる
        # sys.modules をチェックすることで、ImportError が発生した場合でもNameErrorを回避
        if gmshtools is not None and 'femmesh.gmshtools' in sys.modules and hasattr(sys.modules['femmesh.gmshtools'], 'GmshTools'):
            if VERBOSE_OUTPUT:
                print("⚙️ GmshTools (femmesh.gmshtools) を使用してメッシュ生成を試行中...")
            try:
                # global gmshtools がなくても、sys.modules からアクセス可能
                gmsh_tools = sys.modules['femmesh.gmshtools'].GmshTools(mesh_obj)
                # 強制的に3Dメッシュと決定論的オプションを適用
                gmsh_tools.Options = "".join([
                    "General.RandomSeed = 12345;",
                    "Mesh.ElementDimension = 3;",
                    "Mesh.VolumeEdges = 1;",
                    "Mesh.Algorithm3D = 1;", # 1: MeshAdapt, 2: Delaunay, 3: Frontal, 4: LcMesh, 5: HXT, 6: MMG, 7: Netgen
                    "Mesh.CharacteristicLengthFactor = 1.0;",
                    "Mesh.RandomFactor = 0.0;",
                    "Mesh.Smoothing = 10;",
                    "Mesh.Optimize = 1;",
                    "Mesh.OptimizeNetgen = 1;",
                    "General.NumThreads = 2;" # 0だと全コア
                ])
                if detailed_log:
                    print(f"{sample_id} ⏱️ GmshTools.create_mesh() 実行開始: {time.strftime('%H:%M:%S')}")
                gmsh_tools.create_mesh()
                if detailed_log:
                    print(f"{sample_id} ✅ GmshTools.create_mesh() 完了: {time.strftime('%H:%M:%S')}")
                if VERBOSE_OUTPUT:
                    print("✅ GmshToolsでメッシュ生成コマンドを実行しました。")
            except Exception as e:
                if VERBOSE_OUTPUT:
                    print(f"⚠️ GmshToolsを使ったメッシュ生成でエラー: {e}. FreeCAD内部のメッシュ生成へフォールバックします。")
                if detailed_log:
                    print(f"{sample_id} ⏱️ doc.recompute() [フォールバック] 実行開始: {time.strftime('%H:%M:%S')}")
                doc.recompute() # GmshToolsが失敗した場合のフォールバック (mesh_obj.execute()も含まれる)
                if detailed_log:
                    print(f"{sample_id} ✅ doc.recompute() [フォールバック] 完了: {time.strftime('%H:%M:%S')}")
        else:
            if VERBOSE_OUTPUT:
                print("⚙️ femmesh.gmshtools が利用できないため、FreeCAD内部のGmshメッシュ生成を試行中...")
            if detailed_log:
                print(f"{sample_id} ⏱️ doc.recompute() [通常] 実行開始: {time.strftime('%H:%M:%S')}")
            doc.recompute() # FreeCADにメッシュ生成を任せる (これも mesh_obj.execute() をトリガーする)
            if detailed_log:
                print(f"{sample_id} ✅ doc.recompute() [通常] 完了: {time.strftime('%H:%M:%S')}")

        # メッシュ生成後に FemMesh オブジェクトのノード数をチェック
        if hasattr(mesh_obj, 'FemMesh') and mesh_obj.FemMesh:
            if mesh_obj.FemMesh.NodeCount == 0:
                if VERBOSE_OUTPUT:
                    print("⚠️ メッシュ生成は完了しましたが、ノード数が0です。モデルの形状やメッシュ設定を確認してください。")
            else:
                # Fem.FemMesh オブジェクトに ElementCount 属性がない問題を修正
                try:
                    element_count = mesh_obj.FemMesh.ElementCount # これは前のエラーでAttributeErrorを出した
                except AttributeError:
                    # 互換性のため、getElementCount() メソッドを試すか、取得をスキップ
                    try:
                        element_count = mesh_obj.FemMesh.getElementCount()
                    except AttributeError:
                        element_count = "N/A" # 取得できない場合は表示しない
                
                if VERBOSE_OUTPUT:
                    print(f"✅ メッシュ生成成功。ノード数: {mesh_obj.FemMesh.NodeCount}, 要素数: {element_count}")
                # デバッグ情報の追加
                try:
                    bbox = mesh_obj.FemMesh.BoundBox
                    if VERBOSE_OUTPUT:
                        print(f"メッシュの範囲: X({bbox.XMin:.1f} - {bbox.XMax:.1f}), "
                          f"Y({bbox.YMin:.1f} - {bbox.YMax:.1f}), "
                          f"Z({bbox.ZMin:.1f} - {bbox.ZMax:.1f}) mm")
                except:
                    pass
                if detailed_log:
                    print(f"{sample_id} ✅ メッシュ生成成功: ノード数={mesh_obj.FemMesh.NodeCount}")
                return True
        
        if VERBOSE_OUTPUT:
            print("❌ メッシュ生成に失敗しました (FemMeshが見つからないかノード数が0)。")
        return False
    except Exception:
        if VERBOSE_OUTPUT:
            print("❌ メッシュ生成中に予期せぬエラーが発生しました。")
        if VERBOSE_OUTPUT:
            traceback.print_exc()
        return False
    finally:
        # 標準出力を復元
        if not VERBOSE_OUTPUT:
            sys.stdout = old_stdout

def run_calculix_analysis(analysis_obj: Any) -> Any:
    """CalculiX解析を実行"""
    import os
    import time
    detailed_log = os.environ.get('FEM_DETAILED_LOG', '') == '1'
    sample_id = os.environ.get('FEM_SAMPLE_ID', '')
    
    if detailed_log:
        print(f"{sample_id} 🔍 CalculiX解析開始: {time.strftime('%H:%M:%S')}")
    
    if not (analysis_obj and CCX_AVAILABLE):
        if VERBOSE_OUTPUT:
            print("❌ 解析オブジェクトまたはCalculiXが利用できません。")
        return None
        
    try:
        # ソルバーオブジェクトを探す
        solver = None
        for obj in analysis_obj.Group:
            if hasattr(obj, 'AnalysisType'):
                solver = obj
                break
                
        if solver is None:
            if VERBOSE_OUTPUT:
                print("❌ 解析ソルバーが見つかりませんでした。")
            return None

        # ソルバー設定（属性が存在する場合のみ設定）
        try:
            if hasattr(solver, 'IterationsControlMaximum'):
                solver.IterationsControlMaximum = 2000
            if hasattr(solver, 'GeometricalNonlinearity'):
                solver.GeometricalNonlinearity = False
            # その他の設定も同様に
        except Exception as e:
            if VERBOSE_OUTPUT:
                print(f"ソルバー設定の一部をスキップ: {e}")
            # エラーが発生しても処理を継続
        
        # CcxToolsで解析実行
        # FEMログを抑制するため標準出力をリダイレクト
        if not VERBOSE_OUTPUT:
            import io
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
        
        try:
            fea = CcxTools(solver)
            fea.update_objects()
            fea.setup_working_dir()
            fea.setup_ccx()
            
            if fea.check_prerequisites():
                if VERBOSE_OUTPUT:
                    print("❌ CalculiXの実行に必要な環境が整っていません。")
                return None
                
            # 解析実行
            if VERBOSE_OUTPUT:
                print("⚙️ CalculiX解析を実行中...")
            
            if detailed_log:
                print(f"{sample_id} ⏱️ fea.write_inp_file() 実行開始: {time.strftime('%H:%M:%S')}")
            fea.write_inp_file()
            if detailed_log:
                print(f"{sample_id} ✅ fea.write_inp_file() 完了: {time.strftime('%H:%M:%S')}")
            
            if detailed_log:
                print(f"{sample_id} ⏱️ fea.ccx_run() 実行開始: {time.strftime('%H:%M:%S')}")
            fea.ccx_run()
            if detailed_log:
                print(f"{sample_id} ✅ fea.ccx_run() 完了: {time.strftime('%H:%M:%S')}")
            
            if VERBOSE_OUTPUT:
                print("✅ CalculiX解析が完了しました。")
            
            # 結果をロード
            if VERBOSE_OUTPUT:
                print("📊 結果をロード中...")
            fea.load_results()
            if VERBOSE_OUTPUT:
                print("✅ 結果のロードが完了しました。")
        finally:
            # 標準出力を復元
            if not VERBOSE_OUTPUT:
                sys.stdout = old_stdout
        
        # 結果の簡易確認
        if hasattr(fea, 'result_object') and fea.result_object:
            if VERBOSE_OUTPUT:
                print("✅ 結果オブジェクトが正常に作成されました")
        
        return fea

    except Exception:
        if VERBOSE_OUTPUT:

            traceback.print_exc()
        return None



def extract_fem_results(fea_obj: Any) -> Dict[str, Any]:
    """FEM結果を直接オブジェクトから取得（拡張版）"""
    import os
    import time
    detailed_log = os.environ.get('FEM_DETAILED_LOG', '') == '1'
    sample_id = os.environ.get('FEM_SAMPLE_ID', '')
    
    if detailed_log:
        print(f"{sample_id} 🔍 FEM結果抽出開始: {time.strftime('%H:%M:%S')}")
    
    results = {
        'max_displacement': None,
        'max_stress': None,
        'max_local_stress': None,
        'critical_location': None,
        # 新規追加項目
        'avg_displacement': None,
        'displacement_cv': None,
        'critical_displacement': None,
        'avg_stress': None,
        'stress_uniformity': None,
        'stress_utilization': None
    }
    
    try:
        result = None
        
        # 方法1: fea_objから結果オブジェクトを取得
        if detailed_log:
            print(f"{sample_id} 🔍 結果オブジェクトの取得試行中...")
        
        if hasattr(fea_obj, 'result_object') and fea_obj.result_object:
            result = fea_obj.result_object
            if detailed_log:
                print(f"{sample_id} ✅ fea_obj.result_object から結果オブジェクト取得")
            if VERBOSE_OUTPUT:
                print("📊 fea_objから結果オブジェクトを取得")
        
        # 方法2: ドキュメントから結果オブジェクトを探す
        if result is None:
            if detailed_log:
                print(f"{sample_id} 🔍 ドキュメントから結果オブジェクトを探索中...")
            
            doc = App.ActiveDocument
            for obj in doc.Objects:
                # CCX_Resultsオブジェクトを探す
                if obj.Name == 'CCX_Results' or 'Result' in obj.Name:
                    result = obj
                    if detailed_log:
                        print(f"{sample_id} ✅ ドキュメントから結果オブジェクト発見: {obj.Name}")
                    if VERBOSE_OUTPUT:
                        print(f"📊 代替結果オブジェクト使用: {obj.Name}")
                    break
        
        if result is None:
            if VERBOSE_OUTPUT:
                print("❌ 結果オブジェクトが見つかりません")
            return results
        
        if VERBOSE_OUTPUT:
            print("\n📊 FEM結果を取得中...")
        
        # 結果オブジェクトの属性を確認（デバッグ用）
        if VERBOSE_OUTPUT:
            print("📋 結果オブジェクトの属性:")
        result_attrs = [attr for attr in dir(result) if not attr.startswith('_')]
        for attr in result_attrs[:10]:  # 最初の10個を表示
            if VERBOSE_OUTPUT:
                print(f"  - {attr}")
        
        if VERBOSE_OUTPUT:
            print("\n📋 応力関連の属性を詳しく確認:")
        for attr in result_attrs:
            if 'stress' in attr.lower() or 'von' in attr.lower() or 'mises' in attr.lower():
                if VERBOSE_OUTPUT:
                    print(f"  - {attr}")
                
        # Meshオブジェクトの属性も確認
        if hasattr(result, 'Mesh'):
            if VERBOSE_OUTPUT:
                print("\n📋 Mesh属性の確認:")
            mesh_attrs = [attr for attr in dir(result.Mesh) if not attr.startswith('_')]
            for attr in mesh_attrs[:20]:
                if 'stress' in attr.lower() or 'von' in attr.lower():
                    if VERBOSE_OUTPUT:
                        print(f"  - Mesh.{attr}")
        
        # 変位データの取得（複数の方法を試す）
        if detailed_log:
            print(f"{sample_id} 🔍 変位データ取得開始...")
        
        displacements = None
        
        # 方法1: DisplacementLengths属性
        if hasattr(result, 'DisplacementLengths'):
            displacements = result.DisplacementLengths
            if detailed_log:
                print(f"{sample_id} ✅ DisplacementLengths属性から変位データ取得")
            if VERBOSE_OUTPUT:
                print("✅ DisplacementLengths属性から変位データ取得")
        
        # 方法2: DisplacementVectors属性
        elif hasattr(result, 'DisplacementVectors'):
            vectors = result.DisplacementVectors
            if vectors:
                displacements = [v.Length for v in vectors]
                if VERBOSE_OUTPUT:
                    print("✅ DisplacementVectors属性から変位データ取得")
        
        # 方法3: Mesh属性から
        elif hasattr(result, 'Mesh') and hasattr(result.Mesh, 'DisplacementLengths'):
            displacements = result.Mesh.DisplacementLengths
            if VERBOSE_OUTPUT:
                print("✅ Mesh.DisplacementLengths属性から変位データ取得")
        
        # 変位データの処理（拡張版）
        if displacements is not None and len(displacements) > 0:
            # numpy配列かリストかを判定
            if hasattr(displacements, 'max'):
                max_disp = float(displacements.max())
                active_disps = displacements[displacements > 0.001]
                
                # 新規：統計情報の計算
                results['avg_displacement'] = float(np.mean(displacements))
                results['displacement_cv'] = float(np.std(displacements) / np.mean(displacements)) if np.mean(displacements) > 0 else 0
                
                # 上位10%の平均
                sorted_disps = np.sort(displacements)
                top_10_percent = sorted_disps[int(len(sorted_disps) * 0.9):]
                results['critical_displacement'] = float(np.mean(top_10_percent))
            else:
                max_disp = max(displacements)
                active_disps = [d for d in displacements if d > 0.001]
                
                # リストの場合の統計計算
                import statistics
                results['avg_displacement'] = statistics.mean(displacements)
                if results['avg_displacement'] > 0:
                    results['displacement_cv'] = statistics.stdev(displacements) / results['avg_displacement']
                else:
                    results['displacement_cv'] = 0
                
                # 上位10%の平均
                sorted_disps = sorted(displacements, reverse=True)
                top_10_count = max(1, int(len(sorted_disps) * 0.1))
                results['critical_displacement'] = statistics.mean(sorted_disps[:top_10_count])
            
            results['max_displacement'] = max_disp
            if VERBOSE_OUTPUT:
                print(f"✅ 最大変位: {max_disp:.3f} mm")
            if VERBOSE_OUTPUT:
                print(f"   総ノード数: {len(displacements)}")
            if VERBOSE_OUTPUT:
                print(f"   アクティブノード数: {len(active_disps)}")
            if VERBOSE_OUTPUT:
                print(f"   平均変位: {results['avg_displacement']:.3f} mm")
            if VERBOSE_OUTPUT:
                print(f"   変位CV: {results['displacement_cv']:.3f}")
            if VERBOSE_OUTPUT:
                print(f"   臨界変位（上位10%平均）: {results['critical_displacement']:.3f} mm")
            
            if len(active_disps) > 0:
                avg_disp = sum(active_disps) / len(active_disps)
                if VERBOSE_OUTPUT:
                    print(f"   平均変位（アクティブ）: {avg_disp:.3f} mm")
        else:
            if VERBOSE_OUTPUT:
                print("⚠️ 変位データが取得できませんでした")
        
        # Von Mises応力の取得（複数の方法を試す）
        if detailed_log:
            print(f"{sample_id} 🔍 Von Mises応力データ取得開始...")
        
        stresses = None
        
        # 方法1: VonMises属性
        if hasattr(result, 'VonMises'):
            stresses = result.VonMises
            if detailed_log:
                print(f"{sample_id} ✅ VonMises属性から応力データ取得")
            if VERBOSE_OUTPUT:
                print("✅ VonMises属性から応力データ取得")
        
        # 方法2: vonMises属性（小文字）
        elif hasattr(result, 'vonMises'):
            try:
                stresses = result.vonMises
                if VERBOSE_OUTPUT:
                    print("✅ vonMises属性から応力データ取得")
            except:
                # 属性アクセスの別の方法を試す
                stresses = getattr(result, 'vonMises', None)
                if stresses is not None:
                    if VERBOSE_OUTPUT:
                        print("✅ getattr経由でvonMises属性から応力データ取得")
        
        # 方法3: StressValues属性
        elif hasattr(result, 'StressValues'):
            stress_values = result.StressValues
            if stress_values:
                # Von Mises応力を計算
                von_mises = []
                for stress in stress_values:
                    if len(stress) >= 6:
                        s11, s22, s33, s12, s13, s23 = stress[:6]
                        vm = math.sqrt(0.5 * (
                            (s11 - s22)**2 + (s22 - s33)**2 + (s33 - s11)**2 +
                            6 * (s12**2 + s13**2 + s23**2)
                        ))
                        von_mises.append(vm)
                stresses = von_mises
                if VERBOSE_OUTPUT:
                    print("✅ StressValues属性から応力データ取得")
        
        # 方法4: Mesh属性から
        elif hasattr(result, 'Mesh') and hasattr(result.Mesh, 'VonMisesStress'):
            stresses = result.Mesh.VonMisesStress
            if VERBOSE_OUTPUT:
                print("✅ Mesh.VonMisesStress属性から応力データ取得")
        
        # 応力データの処理（拡張版）
        if stresses is not None and len(stresses) > 0:
            # numpy配列かリストかを判定
            if hasattr(stresses, 'max'):
                max_stress = float(stresses.max())
                max_idx = int(stresses.argmax())
                
                # 新規：統計情報の計算
                results['avg_stress'] = float(np.mean(stresses))
                if results['avg_stress'] > 0:
                    results['stress_uniformity'] = float(1 - np.std(stresses) / results['avg_stress'])
                else:
                    results['stress_uniformity'] = 0
                results['stress_utilization'] = float(results['avg_stress'] / 35.0)  # 許容応力35MPa
            else:
                max_stress = max(stresses)
                max_idx = stresses.index(max_stress) if isinstance(stresses, list) else 0
                
                # リストの場合の統計計算
                import statistics
                results['avg_stress'] = statistics.mean(stresses)
                if results['avg_stress'] > 0:
                    results['stress_uniformity'] = 1 - statistics.stdev(stresses) / results['avg_stress']
                else:
                    results['stress_uniformity'] = 0
                results['stress_utilization'] = results['avg_stress'] / 35.0
            
            results['max_stress'] = max_stress
            results['max_local_stress'] = max_stress
            results['critical_location'] = f"要素{max_idx}"
            
            if VERBOSE_OUTPUT:
                print(f"✅ 最大応力: {max_stress:.3f} MPa (要素{max_idx})")
            if VERBOSE_OUTPUT:
                print(f"   平均応力: {results['avg_stress']:.3f} MPa")
            if VERBOSE_OUTPUT:
                print(f"   応力均一性: {results['stress_uniformity']:.3f}")
            if VERBOSE_OUTPUT:
                print(f"   応力利用率: {results['stress_utilization']:.3f}")
        else:
            if VERBOSE_OUTPUT:
                print("⚠️ 応力データが取得できませんでした")
        
        # 最終チェック
        if results['max_displacement'] is None and results['max_stress'] is None:
            if VERBOSE_OUTPUT:
                print("\n⚠️ 変位・応力データがいずれも取得できませんでした")
            if VERBOSE_OUTPUT:
                print("結果オブジェクトの詳細な属性を確認してください:")
            for attr in result_attrs:
                try:
                    value = getattr(result, attr)
                    if not callable(value) and not attr.startswith('_'):
                        if VERBOSE_OUTPUT:
                            print(f"  {attr}: {type(value)}")
                except:
                    pass
        
        # 応力データが取得できなかった場合、FRDファイルから直接読み取り
        if results['max_stress'] is None and hasattr(fea_obj, 'working_dir'):
            if VERBOSE_OUTPUT:
                print("\n📄 FRDファイルから応力データを直接読み取り中...")
            try:
                working_dir = fea_obj.working_dir
                frd_files = [f for f in os.listdir(working_dir) if f.endswith('.frd')]
                if frd_files:
                    frd_path = os.path.join(working_dir, frd_files[0])
                    
                    # 簡易的なFRD読み取り
                    with open(frd_path, 'r') as f:
                        lines = f.readlines()
                    
                    stress_values = []
                    in_stress_block = False
                    for line in lines:
                        if 'STRESS' in line and line.strip().startswith('-4'):
                            in_stress_block = True
                            continue
                        elif line.strip().startswith('-3') and in_stress_block:
                            break
                        elif in_stress_block and line.strip().startswith('-1'):
                            parts = line.strip().split()
                            if len(parts) >= 8:
                                try:
                                    # Von Mises応力の計算
                                    s11 = float(parts[2])
                                    s22 = float(parts[3])
                                    s33 = float(parts[4])
                                    s12 = float(parts[5])
                                    s13 = float(parts[6])
                                    s23 = float(parts[7])
                                    
                                    vm = math.sqrt(0.5 * (
                                        (s11 - s22)**2 + (s22 - s33)**2 + (s33 - s11)**2 +
                                        6 * (s12**2 + s13**2 + s23**2)
                                    ))
                                    stress_values.append(vm)
                                except:
                                    pass
                    
                    if stress_values:
                        max_stress = max(stress_values)
                        results['max_stress'] = max_stress
                        results['max_local_stress'] = max_stress
                        if VERBOSE_OUTPUT:
                            print(f"✅ FRDファイルから最大応力取得: {max_stress:.3f} MPa")
                        
                        # FRDから読み取った場合も統計計算
                        import statistics
                        results['avg_stress'] = statistics.mean(stress_values)
                        if results['avg_stress'] > 0:
                            results['stress_uniformity'] = 1 - statistics.stdev(stress_values) / results['avg_stress']
                        else:
                            results['stress_uniformity'] = 0
                        results['stress_utilization'] = results['avg_stress'] / 35.0
                        
            except Exception as e:
                if VERBOSE_OUTPUT:
                    print(f"FRDファイル読み取りエラー: {e}")
        
        if detailed_log:
            print(f"{sample_id} ✅ FEM結果抽出完了: 最大変位={results['max_displacement']}, 最大応力={results['max_stress']}")
        
        return results
        
    except Exception as e:
        if VERBOSE_OUTPUT:
            print(f"❌ 結果取得エラー: {e}")
        if VERBOSE_OUTPUT:

            traceback.print_exc()
        return results
def calculate_safety_factor(max_stress: float, yield_strength_mpa: float = 35.0) -> float:
    """
    安全率を計算する。
    Args:
        max_stress (float): 計算された最大応力 (MPa)。
        yield_strength_mpa (float): 材料の許容応力（降伏強度） (MPa)。デフォルトはコンクリートの許容応力。
                                    通常、コンクリートの許容圧縮応力は Fc=24MPa-36MPa程度。
                                    ここでは簡易的に35MPaとする。
    Returns:
        float: 安全率。
    """
    if max_stress <= 0:
        return float('inf') # 応力が発生していない場合は無限大
    return yield_strength_mpa / max_stress


def calculate_economic_cost(building_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    建物の経済性を評価する（構造物量ベースの改良版）
    """
    volume_m3 = building_info.get('volume', 0.0)
    mass_kg = building_info.get('mass', 0.0)
    
    # 床面積計算
    Lx = building_info.get('Lx_mm', 8000) / 1000  # mm→m変換
    Ly = building_info.get('Ly_mm', 8000) / 1000  # mm→m変換
    total_floor_area_sqm = Lx * Ly
    
    # ========== 物量ベースのコスト計算 ==========
    
    # 1. コンクリート工事費
    # コンクリート体積はvolume_m3を使用
    concrete_unit_cost = 15000  # 円/m³（材料費）
    concrete_labor_cost = 10000  # 円/m³（労務費）
    concrete_cost = volume_m3 * (concrete_unit_cost + concrete_labor_cost)
    
    # 2. 鉄筋工事費（コンクリート量から概算）
    # RC造の鉄筋量：約100-150kg/m³として計算
    rebar_quantity = volume_m3 * 125  # kg
    rebar_unit_cost = 150  # 円/kg（材料＋労務）
    rebar_cost = rebar_quantity * rebar_unit_cost
    
    # 3. 型枠工事費（表面積ベース）
    # 簡易的に体積から表面積を推定
    formwork_area = volume_m3 * 4  # m²（概算係数）
    formwork_unit_cost = 8000  # 円/m²
    formwork_cost = formwork_area * formwork_unit_cost
    
    # 4. 構造部材サイズによる追加コスト
    # 大断面部材は施工難易度が上がる
    structural_complexity = 1.0
    
    # 柱断面が大きい場合の割増
    if 'bc_mm' in building_info and 'hc_mm' in building_info:
        avg_column_size = (building_info['bc_mm'] + building_info['hc_mm']) / 2
        if avg_column_size > 600:  # 600mm超
            structural_complexity *= 1.15
        elif avg_column_size > 500:  # 500mm超
            structural_complexity *= 1.08
    
    # スラブ厚による割増
    if 'tf_mm' in building_info and 'tr_mm' in building_info:
        avg_slab_thickness = (building_info['tf_mm'] + building_info['tr_mm']) / 2
        if avg_slab_thickness > 300:  # 300mm超
            structural_complexity *= 1.10
        elif avg_slab_thickness > 250:  # 250mm超
            structural_complexity *= 1.05
    
    # 5. 基本建築工事費（仕上げ、設備など）
    base_building_cost = 200000 * total_floor_area_sqm  # 20万円/㎡
    
    # 6. 複雑性によるコスト増
    complexity_factor = 1 + (
        building_info.get('asymmetry_factor', 0) * 0.1 +
        building_info.get('opening_complexity', 0) * 0.05 +
        building_info.get('structural_irregularity', 0) * 0.15 +
        building_info.get('has_cantilever', False) * 0.1 +
        building_info.get('has_stairs', False) * 0.08
    )
    
    # 7. 特殊要素による追加コスト
    special_cost = 0
    
    # 傾斜壁の施工難易度
    if abs(building_info.get('wall_tilt_angle', 0)) > 10:
        special_cost += total_floor_area_sqm * 20000  # 2万円/㎡追加
    
    # かまぼこ屋根の施工難易度
    if building_info.get('roof_morph', 0.5) > 0.7:
        special_cost += total_floor_area_sqm * 15000  # 1.5万円/㎡追加
    
    # ========== 総工事費計算 ==========
    structural_cost = (concrete_cost + rebar_cost + formwork_cost) * structural_complexity
    total_construction_cost_yen = (
        structural_cost +
        base_building_cost * complexity_factor +
        special_cost
    )
    
    # デバッグ情報
    if VERBOSE_OUTPUT:
        print(f"📊 コスト内訳:")
    if VERBOSE_OUTPUT:
        print(f"  構造工事費: {structural_cost:,.0f}円")
    if VERBOSE_OUTPUT:
        print(f"  基本建築費: {base_building_cost * complexity_factor:,.0f}円")
    if VERBOSE_OUTPUT:
        print(f"  特殊要素費: {special_cost:,.0f}円")
    if VERBOSE_OUTPUT:
        print(f"  合計: {total_construction_cost_yen:,.0f}円")
    if VERBOSE_OUTPUT:
        print(f"  ㎡単価: {total_construction_cost_yen / total_floor_area_sqm:,.0f}円/㎡")
    
    return {
        'total_construction_cost': total_construction_cost_yen,
        'cost_per_sqm': total_construction_cost_yen / total_floor_area_sqm if total_floor_area_sqm > 0 else 0,
        'mass_per_volume': mass_kg / volume_m3 if volume_m3 > 0 else 0,
        # 追加情報
        'structural_cost_ratio': structural_cost / total_construction_cost_yen,
        'concrete_volume': volume_m3
    }

def calculate_environmental_impact(building_info: Dict[str, Any], fem_results: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    建物の環境負荷（CO2排出量）を評価する（より現実的な版）
    """
    volume_m3 = building_info.get('volume', 0.0)
    mass_kg = building_info.get('mass', 0.0)
    
    # ========== 1. 材料別のCO2排出量計算 ==========
    # コンクリート体積から各材料を推定
    concrete_volume_m3 = volume_m3
    
    # セメント量の推定（コンクリート1m³あたり300-350kg）
    cement_kg = concrete_volume_m3 * 325  # kg
    cement_co2_per_kg = 0.9  # kg-CO2/kg（セメント製造）
    cement_co2 = cement_kg * cement_co2_per_kg
    
    # 骨材（砂利・砂）のCO2
    aggregate_kg = concrete_volume_m3 * 1850  # kg（コンクリート1m³あたり）
    aggregate_co2_per_kg = 0.004  # kg-CO2/kg（採取・運搬）
    aggregate_co2 = aggregate_kg * aggregate_co2_per_kg
    
    # 鉄筋のCO2
    # ピロティ構造は通常より鉄筋量が多い
    if building_info.get('piloti_structure', False):
        rebar_kg_per_m3 = 150  # kg/m³（ピロティ構造）
    else:
        rebar_kg_per_m3 = 125  # kg/m³（通常）
    
    rebar_kg = concrete_volume_m3 * rebar_kg_per_m3
    rebar_co2_per_kg = 2.0  # kg-CO2/kg（鉄鋼製造）
    rebar_co2 = rebar_kg * rebar_co2_per_kg
    
    # 運搬のCO2（材料重量の5%程度）
    total_material_kg = cement_kg + aggregate_kg + rebar_kg
    transport_co2 = total_material_kg * 0.05 * 0.1  # 0.1 kg-CO2/kg-km × 50km想定
    
    # 施工時のCO2（建設機械、型枠等）
    construction_co2_per_m3 = 50  # kg-CO2/m³
    construction_co2 = concrete_volume_m3 * construction_co2_per_m3
    
    # ========== 2. 総CO2排出量 ==========
    total_co2_emission_kg = (
        cement_co2 +
        aggregate_co2 +
        rebar_co2 +
        transport_co2 +
        construction_co2
    )
    
    # 床面積計算
    Lx = building_info.get('Lx_mm', 8000) / 1000  # mm→m変換
    Ly = building_info.get('Ly_mm', 8000) / 1000  # mm→m変換
    total_floor_area_sqm = Lx * Ly
    
    # ========== 3. FEM結果を活用した最適化評価 ==========
    optimization_potential = 0
    material_efficiency_score = 0.5  # デフォルト値
    
    if fem_results:
        stress_utilization = fem_results.get('stress_utilization', 0.5)
        stress_uniformity = fem_results.get('stress_uniformity', 0.7)
        avg_displacement = fem_results.get('avg_displacement', 0)
        
        # 材料効率スコア（0-1）
        material_efficiency_score = stress_utilization * stress_uniformity
        
        # 最適化ポテンシャルの計算（より現実的に）
        if stress_utilization < 0.3:  # 30%未満
            # 応力が非常に低い = 過剰設計
            optimization_potential = 0.20  # 20%削減可能
        elif stress_utilization < 0.5:  # 50%未満
            optimization_potential = 0.10  # 10%削減可能
        elif stress_utilization < 0.7:  # 70%未満
            optimization_potential = 0.05  # 5%削減可能
        else:
            optimization_potential = 0  # 既に効率的
        
        # 応力の不均一性による追加の最適化余地
        if stress_uniformity < 0.6:
            optimization_potential += 0.05  # 追加5%
        
        # 最大30%に制限
        optimization_potential = min(0.30, optimization_potential)
    
    # ========== 4. 最適化後のCO2排出量 ==========
    # 構造最適化により主に鉄筋とセメント量が削減可能
    optimizable_co2 = cement_co2 + rebar_co2
    optimization_savings = optimizable_co2 * optimization_potential
    optimized_co2_emission = total_co2_emission_kg - optimization_savings
    
    # ========== 5. ベンチマーク比較 ==========
    # 一般的なRC造建物のCO2原単位：400-600 kg-CO2/m²
    benchmark_co2_per_sqm = 500
    performance_ratio = (total_co2_emission_kg / total_floor_area_sqm) / benchmark_co2_per_sqm
    
    # デバッグ情報
    if building_info.get('VERBOSE_OUTPUT', False):
        print(f"\n📊 CO2排出量内訳:")
        print(f"  セメント: {cement_co2:,.0f} kg-CO2 ({cement_co2/total_co2_emission_kg*100:.1f}%)")
        print(f"  骨材: {aggregate_co2:,.0f} kg-CO2 ({aggregate_co2/total_co2_emission_kg*100:.1f}%)")
        print(f"  鉄筋: {rebar_co2:,.0f} kg-CO2 ({rebar_co2/total_co2_emission_kg*100:.1f}%)")
        print(f"  運搬: {transport_co2:,.0f} kg-CO2 ({transport_co2/total_co2_emission_kg*100:.1f}%)")
        print(f"  施工: {construction_co2:,.0f} kg-CO2 ({construction_co2/total_co2_emission_kg*100:.1f}%)")
        print(f"  合計: {total_co2_emission_kg:,.0f} kg-CO2")
        print(f"  床面積あたり: {total_co2_emission_kg/total_floor_area_sqm:.0f} kg-CO2/m²")
        print(f"  ベンチマーク比: {performance_ratio:.2f}")
        if fem_results:
            print(f"  最適化ポテンシャル: {optimization_potential*100:.1f}%")
            print(f"  最適化後: {optimized_co2_emission:,.0f} kg-CO2")
    
    return {
        'total_co2_emission': total_co2_emission_kg,
        'co2_per_sqm': total_co2_emission_kg / total_floor_area_sqm if total_floor_area_sqm > 0 else 0,
        'optimized_co2_emission': optimized_co2_emission,
        'optimized_co2_per_sqm': optimized_co2_emission / total_floor_area_sqm if total_floor_area_sqm > 0 else 0,
        'optimization_potential': optimization_potential,
        'material_efficiency_score': material_efficiency_score,
        # 詳細情報
        'cement_co2': cement_co2,
        'rebar_co2': rebar_co2,
        'aggregate_co2': aggregate_co2,
        'transport_co2': transport_co2,
        'construction_co2': construction_co2,
        'performance_vs_benchmark': performance_ratio
    }



def calculate_comfort_score(fem_results: Dict[str, Any], building_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    居住快適性を評価する（建築設計要素重視版）
    """
    
    # ========== 1. 空間の広がり感（25%） ==========
    # 天井高による開放感
    H1 = building_info.get('H1_mm', 3000) / 1000  # m変換
    H2 = building_info.get('H2_mm', 3000) / 1000
    avg_height = (H1 + H2) / 2
    
    # より厳しい評価基準
    if avg_height >= 4.0:  # 4m以上で満点
        height_score = 10.0
    elif avg_height >= 3.5:
        height_score = 8.0 + (avg_height - 3.5) * 4.0
    elif avg_height >= 3.0:
        height_score = 6.0 + (avg_height - 3.0) * 4.0
    elif avg_height >= 2.4:
        height_score = 3.0 + (avg_height - 2.4) * 5.0
    else:
        height_score = avg_height / 2.4 * 3.0  # 基本点を下げる
    
    # スパン長による広さ感
    Lx = building_info.get('Lx_mm', 8000) / 1000
    Ly = building_info.get('Ly_mm', 8000) / 1000
    avg_span = (Lx + Ly) / 2
    
    # より厳しい評価基準
    if avg_span >= 15:  # 15m以上で満点
        span_score = 10.0
    elif avg_span >= 12:
        span_score = 7.0 + (avg_span - 12) * 1.0
    elif avg_span >= 8:
        span_score = 4.0 + (avg_span - 8) * 0.75
    else:
        span_score = avg_span / 8 * 4.0  # 基本点を下げる
    
    spaciousness_score = (height_score + span_score) / 2
    
    # ========== 2. 採光・眺望（30%） ==========
    window_ratio = building_info.get('window_ratio_2f', 0.4)
    
    # 窓の評価をより厳しく（構造とのバランスも考慮）
    if window_ratio >= 0.8:
        daylight_score = 9.0  # 窓が多すぎても満点にはしない
    elif window_ratio >= 0.6:
        daylight_score = 7.0 + (window_ratio - 0.6) * 10.0
    elif window_ratio >= 0.4:
        daylight_score = 5.0 + (window_ratio - 0.4) * 5.0
    elif window_ratio >= 0.2:
        daylight_score = 3.0 + (window_ratio - 0.2) * 10.0
    else:
        daylight_score = window_ratio / 0.2 * 3.0
    
    # 階高による眺望の良さ（より厳しく）
    view_score = min(9.0, H1 / 4.0 * 6.0 + 3.0)  # より高い基準
    
    lighting_score = (daylight_score * 0.7 + view_score * 0.3)
    
    # ========== 3. ピロティによる開放感（20%） ==========
    piloti_score = 6.0  # 基本点を下げる
    
    # 1階の開放率
    floor_opening_ratio = building_info.get('floor_opening_ratio', 0.7)
    if floor_opening_ratio > 0.8:
        piloti_score += 1.5
    elif floor_opening_ratio > 0.6:
        piloti_score += 0.5
    
    # 柱の細さによる開放感
    bc = building_info.get('bc_mm', 400)
    if bc <= 300:
        piloti_score += 0.5  # 細い柱は開放的
    elif bc >= 600:
        piloti_score -= 1.0  # 太い柱は圧迫感
    
    # ========== 4. プライバシー・静粛性（15%） ==========
    # 2階居住による静粛性
    privacy_score = 5.0  # 基本点を下げる
    
    # 壁厚による遮音性
    tw_ext = building_info.get('tw_ext_mm', 150)
    if tw_ext >= 200:
        privacy_score += 1.0
    elif tw_ext <= 100:
        privacy_score -= 1.0
    
    # ========== 5. 構造的安心感（10%）- FEM結果を軽く反映 ==========
    max_disp = fem_results.get('max_displacement', 0.0)
    span_length = building_info.get('span_length', 8.0) * 1000
    allowable_disp = span_length / 300
    
    disp_ratio = max_disp / allowable_disp if allowable_disp > 0 else 0
    # より厳しい評価
    if disp_ratio <= 0.3:  # 許容値の30%以下で満点
        structural_comfort = 10.0
    elif disp_ratio <= 0.6:
        structural_comfort = 10.0 - (disp_ratio - 0.3) * 10.0
    elif disp_ratio <= 1.0:
        structural_comfort = 7.0 - (disp_ratio - 0.6) * 10.0
    else:
        structural_comfort = max(0, 3.0 - (disp_ratio - 1.0) * 3.0)
    
    # ========== 6. デザイン性（ペナルティ） ==========
    design_penalty = 0
    
    # 極端な傾斜壁
    wall_tilt = abs(building_info.get('wall_tilt_angle', 0))
    if wall_tilt > 30:
        design_penalty += 1.5  # 住みにくそう
    elif wall_tilt > 20:
        design_penalty += 0.5
    
    # 極端な屋根形状
    roof_morph = building_info.get('roof_morph', 0.5)
    if roof_morph > 0.8 or roof_morph < 0.2:
        design_penalty += 0.5
    
    # ========== 7. バルコニーによる快適性向上 ==========
    balcony_bonus = 0
    if building_info.get('has_balcony', False):
        balcony_depth = building_info.get('balcony_depth', 0)
        if balcony_depth >= 3.0:
            balcony_bonus = 1.0  # 非常に広いバルコニーでも上限1.0
        elif balcony_depth >= 2.0:
            balcony_bonus = 0.7  # 広いバルコニー
        elif balcony_depth >= 1.5:
            balcony_bonus = 0.5  # 標準的なバルコニー
        else:
            balcony_bonus = 0.3  # 小さなバルコニー
    
    # ========== 総合評価 ==========
    # 基本評価を計算
    base_score = (
        spaciousness_score * 0.25 +     # 空間の広がり（25%）
        lighting_score * 0.30 +          # 採光・眺望（30%）
        piloti_score * 0.20 +           # 開放感（20%）
        privacy_score * 0.15 +          # プライバシー（15%）
        structural_comfort * 0.10       # 構造的安心感（10%）
    )
    
    # 相乗効果：複数の要素が優れている場合のみ高得点
    # 各要素が高得点（8以上）の数をカウント
    high_score_count = 0
    if spaciousness_score >= 8: high_score_count += 1
    if lighting_score >= 8: high_score_count += 1
    if piloti_score >= 8: high_score_count += 1
    if privacy_score >= 8: high_score_count += 1
    if structural_comfort >= 8: high_score_count += 1
    
    # 相乗効果係数（0.9〜1.1）
    synergy_factor = 0.9 + (high_score_count * 0.04)
    
    comfort_score = base_score * synergy_factor - design_penalty + balcony_bonus
    comfort_score = max(0, min(10, comfort_score))
    
    return {
        'comfort_score': comfort_score,
        'spaciousness_score': spaciousness_score,
        'lighting_score': lighting_score,
        'piloti_openness_score': piloti_score,
        'privacy_score': privacy_score,
        'structural_comfort_score': structural_comfort,
        'design_penalty': design_penalty,
        'balcony_bonus': balcony_bonus,
        # 詳細情報
        'height_score': height_score,
        'span_score': span_score,
        'daylight_score': daylight_score,
        'view_score': view_score
    }


def calculate_constructability_score(building_info: Dict[str, Any], fem_results: Dict[str, Any] = None) -> Dict[str, Any]:
#def calculate_constructability_score(building_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    施工性を評価する（かまぼこ屋根対応版、ねじれ削除）。
    Args:
        building_info (Dict[str, Any]): 建物情報を含む辞書。
    Returns:
        Dict[str, Any]: 施工性評価結果。
    """
    has_cantilever = building_info.get('has_cantilever', False)
    has_stairs = building_info.get('has_stairs', False)
    
    # 基本スコア (単純な箱型構造を10点とする)
    constructability_score = 10.0
    
    # 複雑な要素による減点
    if has_cantilever:
        constructability_score -= 2.0 # カンチレバーは施工が複雑
    if has_stairs:
        constructability_score -= 1.5 # 外部階段は手間が増える
    
    # 1階ピロティ構造による施工性への影響
    # 型枠・足場の簡易化と、柱の精度要求の厳しさのトレードオフ
    constructability_score += 1.0 # 1階壁がない分、全体としては少し楽になる側面も考慮
    
    # 開口部の複雑さも影響
    opening_complexity = building_info.get('opening_complexity', 0)
    constructability_score -= opening_complexity * 0.5 # 開口が多いほど手間がかかる
    
    # 傾斜壁による施工難易度の増加
    wall_tilt_angle = abs(building_info.get('wall_tilt_angle', 0))
    if wall_tilt_angle > 0:
        constructability_score -= wall_tilt_angle / 10.0  # 傾斜角度10度で1点減点
    
    # かまぼこ屋根による施工難易度
    roof_morph = building_info.get('roof_morph', 0.5)
    
    if roof_morph < 0.2:  # ほぼ平ら
        roof_penalty = 0
    elif roof_morph < 0.7:  # 標準的な曲率
        roof_penalty = 0.5
    else:  # 急曲率
        roof_penalty = 1.5
    
    constructability_score -= roof_penalty
    
    # バルコニーによる施工難易度の増加
    if building_info.get('has_balcony', False):
        balcony_depth = building_info.get('balcony_depth', 0)
        if balcony_depth >= 2.0:
            constructability_score -= 1.5  # 大きなバルコニーは施工が複雑
        elif balcony_depth >= 1.0:
            constructability_score -= 1.0  # 標準的なバルコニー
        else:
            constructability_score -= 0.5  # 小さなバルコニー

    # スコアを0～10点に正規化
    constructability_score = max(0, min(10, constructability_score))
    
    
    # FEM結果による追加評価
    stress_concentration_penalty = 0
    if fem_results:
        max_stress = fem_results.get('max_stress', 0)
        avg_stress = fem_results.get('avg_stress', 1)
        if avg_stress > 0:
            stress_concentration = max_stress / avg_stress
            if stress_concentration > 3.0:
                stress_concentration_penalty = 0.5  # 応力集中部は配筋が複雑
    
    constructability_score -= stress_concentration_penalty
    constructability_score = max(0, min(10, constructability_score))
    
    return {
        'constructability_score': constructability_score,
        'cantilever_penalty': -2.0 if has_cantilever else 0,
        'stairs_penalty': -1.5 if has_stairs else 0,
        'roof_complexity_penalty': -roof_penalty,
        'stress_concentration_penalty': -stress_concentration_penalty
    }

def evaluate_building(
    # 既存パラメータ
    Lx: float, Ly: float, H1: float, H2: float,
    tf: float, tr: float, bc: float, hc: float,
    tw_ext: float, save_fcstd: bool = False,
    
    # 追加パラメータ
    wall_tilt_angle: float = 0.0,
    window_ratio_2f: float = 0.4,
    
    # かまぼこ屋根パラメータ（ねじれ削除）
    roof_morph: float = 0.5,
    roof_shift: float = 0.0,
    
    # バルコニーパラメータ
    balcony_depth: float = 0.0,
    
    # FCStdファイル保存用パラメータ
    fcstd_path: str = None,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    建物のFEM解析と評価を実行するメイン関数。
    Args:
        Lx (float): 建物幅 [m]
        Ly (float): 建物奥行き [m]
        H1 (float): 1階高 [m]
        H2 (float): 2階高 [m]
        tf (float): 床スラブ厚 [mm]
        tr (float): 屋根スラブ厚 [mm]
        bc (float): 柱幅 [mm]
        hc (float): 柱厚 [mm]
        tw_ext (float): 外壁厚 [mm]
        save_fcstd (bool): FreeCADファイルを保存するかどうか。
    Returns:
        Dict[str, Any]: 評価結果を含む辞書。
    """
    overall_results = {
        'safety': {},
        'economic': {},
        'environmental': {},
        'comfort': {},
        'constructability': {},
        'raw_fem_results': {},
        'building_info': {},
        'status': 'Failed',
        'message': ''
    }

    if VERBOSE_OUTPUT:
        print(f"\n--- 建物モデル生成とFEM解析開始 (Lx={Lx}m, Ly={Ly}m, H1={H1}m, H2={H2}m) ---")
    
    # 既存ドキュメントのクリーンアップ
    if App.ActiveDocument:
        if VERBOSE_OUTPUT:
            print("🧹 既存ドキュメントをクリーンアップ中...")
        App.closeDocument(App.ActiveDocument.Name)
        if VERBOSE_OUTPUT:
            print("✅ 既存ドキュメントをクローズしました")
    
    # 決定論的設定の適用
    setup_deterministic_fem()

    doc, building_obj, building_info = None, None, {}
    try:
        # モデル生成
        doc, building_obj, building_info = create_realistic_building_model(
            Lx, Ly, H1, H2, tf, tr, bc, hc, tw_ext,
            wall_tilt_angle, window_ratio_2f,
            roof_morph, roof_shift,
            balcony_depth
        )
        if not (doc and building_obj):
            overall_results['message'] = "建物モデルの生成に失敗しました。"
            if VERBOSE_OUTPUT:
                print(overall_results['message'])
            return overall_results
        
        # building_info に入力パラメータの mm 単位版も追加して、後続関数で使いやすくする
        building_info['Lx_mm'] = int(Lx * 1000)
        building_info['Ly_mm'] = int(Ly * 1000)
        building_info['H1_mm'] = int(H1 * 1000)
        building_info['H2_mm'] = int(H2 * 1000)
        building_info['tf_mm'] = int(tf)
        building_info['tr_mm'] = int(tr)
        building_info['bc_mm'] = int(bc)
        building_info['hc_mm'] = int(hc)
        building_info['tw_ext_mm'] = int(tw_ext)
        building_info['balcony_depth'] = balcony_depth
        building_info['has_balcony'] = balcony_depth > 0

        # モデルの形状検証 (最終結合後)
        if not building_obj.Shape.isValid():
            if VERBOSE_OUTPUT:
                print("❌ 警告: 最終生成された建物モデルの形状が不正です。FEM解析に問題が発生する可能性が非常に高いです。")
            building_info['is_valid_shape'] = False
            # FEM解析が失敗する可能性が高いため、ここで早期終了する
            overall_results['message'] = "最終生成された建物モデルの形状が不正です。FEM解析を中止します。"
            return overall_results # True ではなく、エラーメッセージ付きで返すように修正
        else:
            building_info['is_valid_shape'] = True
            if VERBOSE_OUTPUT:
                print("✅ 建物モデルの最終形状は有効です。")


        if VERBOSE_OUTPUT:
            print("✅ 建物モデル生成完了。FEM解析設定へ。")

        # FEM解析設定
        analysis_obj, mesh_obj = setup_basic_fem_analysis(doc, building_obj, building_info)
        if not (analysis_obj and mesh_obj):
            overall_results['message'] = "FEM解析設定に失敗しました。"
            if VERBOSE_OUTPUT:
                print(overall_results['message'])
            return overall_results
        if VERBOSE_OUTPUT:
            print("✅ FEM解析設定完了。メッシュ生成へ。")

        # メッシュ生成
        mesh_success = run_mesh_generation(doc, mesh_obj)
        if not mesh_success:
            overall_results['message'] = "メッシュ生成に失敗しました。"
            if VERBOSE_OUTPUT:
                print(overall_results['message'])
            return overall_results
        if VERBOSE_OUTPUT:
            print("✅ メッシュ生成完了。CalculiX解析へ。")
        
        # デバッグ：固定ノードの確認
        check_fixed_nodes(doc, mesh_obj)

        # CalculiX解析実行
        fea_obj = run_calculix_analysis(analysis_obj)
        if not fea_obj:
            overall_results['message'] = "CalculiX解析の実行または結果の読み込みに失敗しました。"
            if VERBOSE_OUTPUT:
                print(overall_results['message'])
            return overall_results
        if VERBOSE_OUTPUT:
            print("✅ CalculiX解析完了。結果抽出へ。")

        # FEM結果抽出
        fem_results = extract_fem_results(fea_obj)
        if fem_results['max_displacement'] is None and fem_results['max_stress'] is None:
            overall_results['message'] = "FEM結果の抽出に失敗しました。"
            if VERBOSE_OUTPUT:
                print(overall_results['message'])
            return overall_results
        overall_results['raw_fem_results'] = fem_results
        if VERBOSE_OUTPUT:
            print("✅ FEM結果抽出完了。評価計算へ。")


        # 各種評価指標の計算
        # 安全性
        max_stress_mpa = fem_results.get('max_stress', 0.0)  # すでにMPa単位
        if max_stress_mpa is not None and max_stress_mpa > 0:
            overall_safety_factor = calculate_safety_factor(max_stress_mpa)
        else:
            overall_safety_factor = float('inf')  # 応力が0の場合は無限大
            if VERBOSE_OUTPUT:
                print("⚠️ 最大応力が0です。自重荷重が正しく設定されていない可能性があります。")

        overall_results['safety'] = {
            'overall_safety_factor': overall_safety_factor,
            'max_stress_mpa': max_stress_mpa,
            'max_displacement_mm': fem_results.get('max_displacement', 0.0)
        }

        # 経済性
        overall_results['economic'] = calculate_economic_cost(building_info)

        # 環境負荷
#        overall_results['environmental'] = calculate_environmental_impact(building_info)
        # 環境負荷（FEM結果を渡すように修正）
        overall_results['environmental'] = calculate_environmental_impact(building_info, fem_results)
        
        # 快適性
        overall_results['comfort'] = calculate_comfort_score(fem_results, building_info)

        # 施工性
#        overall_results['constructability'] = calculate_constructability_score(building_info)
        overall_results['constructability'] = calculate_constructability_score(building_info, fem_results)

        overall_results['building_info'] = building_info
        overall_results['status'] = 'Success'
        overall_results['message'] = "建物モデルの生成、FEM解析、評価がすべて成功しました。"
        if VERBOSE_OUTPUT:
            print(overall_results['message'])

    except Exception as e:
        overall_results['message'] = f"処理中に予期せぬエラーが発生しました: {e}"
        if VERBOSE_OUTPUT:
            print(overall_results['message'])
            if VERBOSE_OUTPUT:

                traceback.print_exc()
    finally:
        if save_fcstd and doc:
            try:
                if VERBOSE_OUTPUT:
                    print("💾 FCStdファイル保存処理開始...")
                # building_infoを引数に渡す
                clean_document_for_fcstd_save(doc, building_info)
                
                # スナップショットを保存（新規追加）
                if is_gui_mode():
                    if VERBOSE_OUTPUT:
                        print("📸 建物のスナップショットを保存中...")
                    save_building_snapshot(doc, "piloti_building_fem_analysis")
                
                # FCStdファイルを保存
                if fcstd_path is None:
                    fcstd_path = os.path.join(os.getcwd(), "piloti_building_fem_analysis.FCStd")
                else:
                    # fcstd_pathが相対パスの場合、絶対パスに変換
                    if not os.path.isabs(fcstd_path):
                        fcstd_path = os.path.join(os.getcwd(), fcstd_path)
                
                # 保存直前に再度可視化設定を確実に行う
                ensure_parts_visibility(doc)
                doc.recompute()
                
                doc.saveAs(fcstd_path)
                if VERBOSE_OUTPUT:
                    print(f"✅ FCStdファイルを保存しました: {fcstd_path}")
            except Exception as e:
                if VERBOSE_OUTPUT:
                    print(f"保存処理エラー: {e}")
                if VERBOSE_OUTPUT:

                    traceback.print_exc()
        elif doc:
            # GUIモードで保存しない場合でも、ドキュメントを閉じておく（コマンドライン実行時など）
            if not is_gui_mode():
                App.closeDocument(doc.Name)

    return overall_results



def clean_document_for_fcstd_save(doc, building_info=None):
    """FCStd保存用にドキュメントをクリーンアップ"""
    if VERBOSE_OUTPUT:
        print("🧹 FCStd保存用ドキュメントクリーンアップ開始...")
    
    # メッシュ関連オブジェクトを削除
    mesh_objects = ["CCX_Results_Mesh", "MeshShape", "BuildingMesh"]
    for obj_name in mesh_objects:
        safe_remove_object(doc, obj_name)
    
    # FEM解析関連オブジェクトも削除
    fem_objects = ["StructuralAnalysis"]
    for obj_name in fem_objects:
        safe_remove_object(doc, obj_name)
    
    # ソルバー関連オブジェクトを削除
    solver_objects = []
    for obj in doc.Objects:
        if hasattr(obj, 'TypeId'):
            if 'Solver' in obj.TypeId or 'Ccx' in obj.TypeId:
                solver_objects.append(obj.Name)
    
    for obj_name in solver_objects:
        safe_remove_object(doc, obj_name)
    
    # 建物パーツの表示設定
    # FEM解析用の統合建物は非表示のまま
    building = doc.getObject("AnalysisBuilding")
    if building:
        safe_set_visibility(building, False)
        if VERBOSE_OUTPUT:
            print("✅ AnalysisBuilding を非表示に設定")
    
    # 個別のカラフルなパーツを表示
    colorful_parts = [
        "Foundation",    # 基礎
        "Floor1",        # 1階床
        "Floor2",        # 2階床
        "Columns",       # 柱
        "Walls",         # 壁
        "RoofSlab",      # 屋根
        "Balcony",       # バルコニー
        "Staircase"      # 階段
    ]
    
    for part_name in colorful_parts:
        obj = doc.getObject(part_name)
        if obj:
            safe_set_visibility(obj, True)
            if is_gui_mode() and hasattr(obj, 'ViewObject') and obj.ViewObject is not None:
                obj.ViewObject.DisplayMode = "Shaded"
            if VERBOSE_OUTPUT:
                print(f"✅ {part_name} を表示状態に設定")
    
    # 荷重と支持条件の可視化を追加
    # create_load_visualization_arrows と create_support_visualization は building_info を使用
    if building_info:
        load_arrows = create_load_visualization_arrows(doc, building_info)
        support_symbols = create_support_visualization(doc, building_info)
    
    # 荷重条件オブジェクトは保持
    load_objects = ["FixedSupport", "RoofPressure", "SelfWeight"] # 以前のコードで生成されるオブジェクト
    for obj_name in load_objects:
        obj = doc.getObject(obj_name)
        if obj:
            safe_set_visibility(obj, True)
            if VERBOSE_OUTPUT:
                print(f"✅ {obj_name} を表示状態に設定しました")

    # 荷重・支持可視化オブジェクトも表示状態に設定
    for obj_name in ["LoadArrows", "SupportSymbols", "DebugStairHole"]: # DebugStairHoleも残す
        obj = doc.getObject(obj_name)
        if obj:
            safe_set_visibility(obj, True)
            if VERBOSE_OUTPUT:
                print(f"✅ {obj_name} を表示状態に設定しました")

    # 材料オブジェクトは削除
    material_objects = ["Concrete"]
    for obj_name in material_objects:
        safe_remove_object(doc, obj_name)
    
    doc.recompute()
    safe_gui_operations(doc)
    
    if VERBOSE_OUTPUT:
        print("✅ ドキュメントクリーンアップ完了")
    return True


def evaluate_building_from_params(params: Dict[str, Any], save_fcstd: bool = False, fcstd_path: str = None) -> Dict[str, Any]:
    """
    パラメータ辞書から建物評価を実行するラッパー関数
    
    Args:
        params: 設計パラメータの辞書
        verbose: 詳細出力の有無
        save_fcstd: FCStdファイルを保存するか
    
    Returns:
        評価結果の辞書（evaluate_buildingと同じ形式）
    """
    # VERBOSE_OUTPUTフラグに応じて出力を制御
    if not VERBOSE_OUTPUT:
        # 標準出力を一時的に無効化
        import sys
        import io
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
    
    try:
        result = evaluate_building(
            Lx=params['Lx'],
            Ly=params['Ly'],
            H1=params['H1'],
            H2=params['H2'],
            tf=params['tf'],
            tr=params['tr'],
            bc=params['bc'],
            hc=params['hc'],
            tw_ext=params['tw_ext'],
            save_fcstd=save_fcstd,
            wall_tilt_angle=params.get('wall_tilt_angle', 0.0),
            window_ratio_2f=params.get('window_ratio_2f', 0.4),
            roof_morph=params.get('roof_morph', 0.5),
            roof_shift=params.get('roof_shift', 0.0),
            balcony_depth=params.get('balcony_depth', 0.0),
            fcstd_path=fcstd_path
        )
        # Flatten nested results so simple_random_batch can access them
        result['cost_per_sqm'] = result.get('economic', {}).get('cost_per_sqm', 0.0)
        result['co2_per_sqm'] = result.get('environmental', {}).get('co2_per_sqm', 0.0)
        result['comfort_score'] = result.get('comfort', {}).get('comfort_score', 0.0)
        result['constructability_score'] = result.get('constructability', {}).get('constructability_score', 0.0)
        
        # 床面積と総コストを追加
        floor_area = params['Lx'] * params['Ly']
        if 'comfort' not in result:
            result['comfort'] = {}
        if 'economic' not in result:
            result['economic'] = {}
            
        result['comfort']['floor_area'] = floor_area
        
        # 総コストの計算
        if 'cost_per_sqm' in result.get('economic', {}):
            result['economic']['total_cost'] = result['economic']['cost_per_sqm'] * floor_area
        else:
            result['economic']['total_cost'] = 0.0
        
        return result
        
    finally:
        if not VERBOSE_OUTPUT:
            # 標準出力を復元
            sys.stdout = old_stdout

# 直接実行テスト
if __name__ == "__main__":
    # サンプルパラメータ（ねじれ削除）
    test_params = {
        # 既存パラメータ
        'Lx': 12.0,      # 建物幅 [m]
        'Ly': 10.0,      # 建物奥行き [m]
        'H1': 3.5,       # 1階高 [m] (ピロティの高さ)
        'H2': 3.0,       # 2階高 [m] (2階部分の高さ)
        'tf': 200,       # 床スラブ厚 [mm]
        'tr': 150,       # 屋根スラブ厚 [mm]
        'bc': 300,       # 柱幅 [mm] (少し太く)
        'hc': 400,       # 柱厚 [mm] (少し太く)
        'tw_ext': 150,   # 外壁厚 [mm]
        'wall_tilt_angle': -20.0,    # 傾斜 [-40, 40]
        'window_ratio_2f': 0.5,      # 窓面積
        
        # かまぼこ屋根パラメータ（ねじれ削除）
        'roof_morph': 0.7,    # 標準的なかまぼこ (0.0, 1.0)
        'roof_shift': 0.5,    # 左右対称 (-0.7, 0.7)
        
        # バルコニーパラメータ
        'balcony_depth': 2.5  # バルコニーの奥行き
    }
    
    # 入力設計変数を出力
    print("=== 入力設計変数 ===")
    for k, v in test_params.items():
        print(f"{k}: {v}")
    
    try:
        # evaluate_building を直接呼び出してテスト
        test_results = evaluate_building(
            test_params['Lx'], test_params['Ly'],
            test_params['H1'], test_params['H2'],
            test_params['tf'], test_params['tr'],
            test_params['bc'], test_params['hc'],
            test_params['tw_ext'],
            save_fcstd=True, # FCStdファイルを保存する
            wall_tilt_angle=test_params.get('wall_tilt_angle', 0.0),
            window_ratio_2f=test_params.get('window_ratio_2f', 0.4),
            roof_morph=test_params.get('roof_morph', 0.5),
            roof_shift=test_params.get('roof_shift', 0.0),
            balcony_depth=test_params.get('balcony_depth', 0.0)
        )
        
        if test_results['status'] == 'Success':
            print("\n=== FEM解析結果 ===")
            print(f"安全率: {test_results['safety']['overall_safety_factor']:.3f}")
            print(f"最大変位: {test_results['safety']['max_displacement_mm']:.3f} mm")
            
            # 応力がNoneの場合の処理
            max_stress = test_results['safety'].get('max_stress_mpa')
            if max_stress is not None:
                print(f"最大応力: {max_stress:.3f} MPa")
            else:
                print("最大応力: データなし")
                
            print(f"建設コスト: {test_results['economic']['cost_per_sqm']:.1f} 円/㎡")
            print(f"CO2排出: {test_results['environmental']['co2_per_sqm']:.1f} kg-CO2/㎡")
            print(f"快適性: {test_results['comfort']['comfort_score']:.3f}")
            print(f"施工性: {test_results['constructability']['constructability_score']:.3f}")
        else:
            print(f"\n解析失敗: {test_results['message']}")
            
    except Exception as e:
        print(f"エラー: {e}")
