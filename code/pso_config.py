# pso_config.py

# ========================================
# ★★★ PSOパラメータ設定 ★★★
# ========================================
N_PARTICLES = 15  # 粒子数
MAX_ITER = 20     # 反復回数
W = 0.7           # 慣性重み
C1 = 1.5          # 個人的最良解(pbest)への加速係数
C2 = 1.5          # 群れ全体の最良解(gbest)への加速係数
V_MAX = 0.2       # 最大速度（探索範囲の割合）


# ========================================
# 設計変数の範囲定義
# ========================================
variable_ranges = {
    "Lx": (8, 12),             # 建物幅 [m]
    "Ly": (6, 12),             # 建物奥行 [m]
    "H1": (2.6, 3.5),          # 1階高さ [m]
    "H2": (2.6, 3.2),          # 2階高さ [m]
    "tf": (350, 600),          # 床スラブ厚 [mm]
    "tr": (350, 600),          # 屋根スラブ厚 [mm]
    "bc": (400, 1000),         # 柱幅 [mm]
    "hc": (400, 1000),         # 柱高さ [mm]
    "tw_ext": (300, 500),      # 外壁厚 [mm]
    "wall_tilt_angle": (-30, 30),   # 壁傾斜角 [度]
    "window_ratio_2f": (0.1, 1.0),  # 2階窓面積比
    "roof_morph": (0.0, 1.0),       # 屋根形態
    "roof_shift": (0.0, 1.0),       # 屋根シフト
    "balcony_depth": (1.0, 3.0),    # バルコニー奥行 [m]
    # 材料パラメータ（0: コンクリート, 1: 木材）
    "material_columns": (0, 1),
    "material_floor1": (0, 1),
    "material_floor2": (0, 1),
    "material_roof": (0, 1),
    "material_walls": (0, 1),
    "material_balcony": (0, 1),
}


# ========================================
# 目的関数
# ========================================
def calculate_fitness(cost, safety, co2, comfort, constructability):

    # 安全率の閾値
    SAFETY_THRESHOLD = 2.0

    # 基本適応度：コストのみ
    fitness = cost

    # 安全率ペナルティ
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 100000

     
    return fitness
