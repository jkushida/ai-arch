#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
壁傾斜角30度でのデバッグテスト
"""
import math

# パラメータ
H2_mm = 3000  # 2階高さ
wall_tilt_angle = 30.0  # 壁傾斜角

# 計算
tilt_rad = math.radians(wall_tilt_angle)
wall_offset_top = H2_mm * math.tan(tilt_rad)

print(f"壁傾斜角: {wall_tilt_angle}度")
print(f"ラジアン: {tilt_rad:.4f}")
print(f"tan({wall_tilt_angle}°) = {math.tan(tilt_rad):.4f}")
print(f"H2_mm: {H2_mm}mm")
print(f"wall_offset_top: {wall_offset_top:.2f}mm")
print(f"wall_offset_top / H2_mm = {wall_offset_top / H2_mm:.2f}")

# 建物寸法との比較
Lx_mm = 8000  # 建物幅
tw_ext_mm = 150  # 壁厚

print(f"\n建物幅: {Lx_mm}mm")
print(f"壁厚: {tw_ext_mm}mm")
print(f"外傾斜での最大X座標: {Lx_mm + tw_ext_mm + wall_offset_top:.0f}mm")

# 外傾斜30度の場合、壁の上端が建物から大きく飛び出す
print(f"\n壁の張り出し量: {wall_offset_top:.0f}mm ({wall_offset_top/1000:.1f}m)")
print("これは2階高さの約{:.1f}%に相当".format(wall_offset_top/H2_mm * 100))