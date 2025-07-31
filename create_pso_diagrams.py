import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle
from matplotlib import patches
import matplotlib.patches as mpatches
from mpl_toolkits.mplot3d import Axes3D

# 日本語フォントの設定
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']
plt.rcParams['axes.unicode_minus'] = False

def create_particle_components_diagram():
    """粒子の構成要素を示す図"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    # 粒子の現在位置
    particle_x, particle_y = 0.4, 0.5
    ax.scatter(particle_x, particle_y, s=200, c='red', zorder=5, label='現在位置')
    
    # 速度ベクトル
    velocity_x, velocity_y = 0.2, 0.15
    ax.arrow(particle_x, particle_y, velocity_x, velocity_y, 
             head_width=0.03, head_length=0.02, fc='blue', ec='blue', 
             linewidth=2, label='速度ベクトル')
    
    # 個体最良位置 (pbest)
    pbest_x, pbest_y = 0.3, 0.7
    ax.scatter(pbest_x, pbest_y, s=150, c='green', marker='s', 
              zorder=4, label='個体最良位置 (pbest)')
    
    # pbestへの引力
    ax.plot([particle_x, pbest_x], [particle_y, pbest_y], 
           'g--', linewidth=1, alpha=0.5)
    
    # 全体最良位置 (gbest)
    gbest_x, gbest_y = 0.8, 0.8
    ax.scatter(gbest_x, gbest_y, s=250, c='gold', marker='*', 
              zorder=4, label='全体最良位置 (gbest)')
    
    # gbestへの引力
    ax.plot([particle_x, gbest_x], [particle_y, gbest_y], 
           'y--', linewidth=1, alpha=0.5)
    
    # 注釈
    ax.annotate('現在位置\n(x, y)', xy=(particle_x, particle_y), 
               xytext=(particle_x-0.1, particle_y-0.1),
               fontsize=10, ha='center')
    
    ax.annotate('速度\n(vx, vy)', xy=(particle_x+velocity_x, particle_y+velocity_y), 
               xytext=(particle_x+velocity_x+0.1, particle_y+velocity_y),
               fontsize=10)
    
    ax.annotate('個体最良\n(過去の最良解)', xy=(pbest_x, pbest_y), 
               xytext=(pbest_x-0.15, pbest_y+0.05),
               fontsize=10)
    
    ax.annotate('全体最良\n(群れの最良解)', xy=(gbest_x, gbest_y), 
               xytext=(gbest_x-0.05, gbest_y+0.08),
               fontsize=10)
    
    # 速度更新の要素を示す矢印
    ax.arrow(particle_x+0.02, particle_y+0.02, 
            (pbest_x-particle_x)*0.3, (pbest_y-particle_y)*0.3,
            head_width=0.02, head_length=0.015, fc='green', ec='green', 
            alpha=0.7, linewidth=1.5)
    
    ax.arrow(particle_x-0.02, particle_y-0.02, 
            (gbest_x-particle_x)*0.3, (gbest_y-particle_y)*0.3,
            head_width=0.02, head_length=0.015, fc='orange', ec='orange', 
            alpha=0.7, linewidth=1.5)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel('X座標', fontsize=12)
    ax.set_ylabel('Y座標', fontsize=12)
    ax.set_title('PSO: 粒子の構成要素', fontsize=16, fontweight='bold')
    ax.legend(loc='lower left', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('pso_particle_components.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_birds_to_pso_concept():
    """鳥の群れからPSOへの概念図"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # 左側：鳥の群れ
    ax1.set_title('鳥の群れの行動', fontsize=14, fontweight='bold')
    
    # 鳥の位置
    birds_x = [0.2, 0.3, 0.25, 0.4, 0.35, 0.5, 0.45]
    birds_y = [0.3, 0.4, 0.5, 0.35, 0.45, 0.4, 0.55]
    
    # 餌の位置
    food_x, food_y = 0.8, 0.7
    
    # 鳥を描画
    for i, (x, y) in enumerate(zip(birds_x, birds_y)):
        # 鳥の形を簡単に表現
        ax1.scatter(x, y, s=150, c='darkblue', marker='>', zorder=5)
        # 餌への方向
        ax1.arrow(x, y, (food_x-x)*0.2, (food_y-y)*0.2,
                 head_width=0.02, head_length=0.015, 
                 fc='lightblue', ec='lightblue', alpha=0.5)
    
    # 餌
    ax1.scatter(food_x, food_y, s=300, c='orange', marker='*', 
               zorder=6, label='餌（目標）')
    
    # リーダーの鳥
    leader_x, leader_y = 0.6, 0.6
    ax1.scatter(leader_x, leader_y, s=200, c='red', marker='>', 
               zorder=5, label='リーダー（最も餌に近い）')
    ax1.arrow(leader_x, leader_y, (food_x-leader_x)*0.3, (food_y-leader_y)*0.3,
             head_width=0.03, head_length=0.02, 
             fc='red', ec='red', alpha=0.7)
    
    ax1.annotate('個体の経験\n（前に餌を見つけた場所）', 
                xy=(0.3, 0.6), xytext=(0.1, 0.8),
                arrowprops=dict(arrowstyle='->', color='green'),
                fontsize=10)
    
    ax1.annotate('群れの情報共有\n（リーダーの方向）', 
                xy=(0.5, 0.5), xytext=(0.6, 0.3),
                arrowprops=dict(arrowstyle='->', color='red'),
                fontsize=10)
    
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.set_xlabel('空間のX座標', fontsize=11)
    ax1.set_ylabel('空間のY座標', fontsize=11)
    ax1.legend(loc='lower left')
    ax1.grid(True, alpha=0.3)
    
    # 右側：PSO
    ax2.set_title('PSO（粒子群最適化）', fontsize=14, fontweight='bold')
    
    # 粒子の位置
    particles_x = [0.2, 0.3, 0.25, 0.4, 0.35, 0.5, 0.45]
    particles_y = [0.3, 0.4, 0.5, 0.35, 0.45, 0.4, 0.55]
    
    # 最適解の位置
    optimum_x, optimum_y = 0.8, 0.7
    
    # 粒子を描画
    for i, (x, y) in enumerate(zip(particles_x, particles_y)):
        ax2.scatter(x, y, s=100, c='red', zorder=5)
        # 個体最良への方向（緑の破線）
        pbest_x = x + np.random.uniform(-0.1, 0.1)
        pbest_y = y + np.random.uniform(-0.1, 0.1)
        ax2.plot([x, pbest_x], [y, pbest_y], 'g--', linewidth=1, alpha=0.5)
    
    # 最適解
    ax2.scatter(optimum_x, optimum_y, s=300, c='gold', marker='*', 
               zorder=6, label='最適解（未知）')
    
    # 現在の最良粒子
    best_x, best_y = 0.6, 0.6
    ax2.scatter(best_x, best_y, s=150, c='blue', 
               zorder=5, label='現在の最良粒子（gbest）')
    
    # 全粒子からgbestへの引力を示す
    for x, y in zip(particles_x, particles_y):
        ax2.plot([x, best_x], [y, best_y], 'b:', linewidth=1, alpha=0.3)
    
    # 等高線（目的関数の地形）
    xx, yy = np.meshgrid(np.linspace(0, 1, 50), np.linspace(0, 1, 50))
    zz = ((xx - optimum_x)**2 + (yy - optimum_y)**2)
    contour = ax2.contour(xx, yy, zz, levels=10, alpha=0.3, colors='gray')
    
    ax2.annotate('個体最良（pbest）\n過去の最良位置', 
                xy=(0.35, 0.55), xytext=(0.1, 0.8),
                arrowprops=dict(arrowstyle='->', color='green'),
                fontsize=10)
    
    ax2.annotate('全体最良（gbest）\n群れの最良位置', 
                xy=(best_x, best_y), xytext=(0.7, 0.4),
                arrowprops=dict(arrowstyle='->', color='blue'),
                fontsize=10)
    
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.set_xlabel('パラメータ1', fontsize=11)
    ax2.set_ylabel('パラメータ2', fontsize=11)
    ax2.legend(loc='lower left')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('pso_birds_concept.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_search_space_visualization():
    """2D/3D探索空間での粒子配置図"""
    fig = plt.figure(figsize=(15, 6))
    
    # 2D探索空間
    ax1 = fig.add_subplot(121)
    
    # 目的関数の等高線
    x = np.linspace(-2, 2, 100)
    y = np.linspace(-2, 2, 100)
    X, Y = np.meshgrid(x, y)
    # Rosenbrock関数
    Z = (1 - X)**2 + 100 * (Y - X**2)**2
    
    # 等高線を描画
    contour = ax1.contour(X, Y, np.log10(Z + 1), levels=20, cmap='viridis', alpha=0.6)
    ax1.clabel(contour, inline=True, fontsize=8)
    
    # 粒子を配置
    np.random.seed(42)
    n_particles = 15
    particles_x = np.random.uniform(-1.5, 1.5, n_particles)
    particles_y = np.random.uniform(-1.5, 1.5, n_particles)
    
    # 粒子を描画
    ax1.scatter(particles_x, particles_y, s=80, c='red', 
               edgecolors='darkred', zorder=5, label='粒子')
    
    # 最適解
    ax1.scatter(1, 1, s=200, c='gold', marker='*', 
               edgecolors='orange', linewidth=2, zorder=6, label='最適解')
    
    # 現在の最良位置
    best_idx = np.argmin((particles_x - 1)**2 + (particles_y - 1)**2)
    ax1.scatter(particles_x[best_idx], particles_y[best_idx], 
               s=120, c='blue', marker='D', zorder=5, label='現在の最良(gbest)')
    
    ax1.set_xlabel('パラメータ X', fontsize=12)
    ax1.set_ylabel('パラメータ Y', fontsize=12)
    ax1.set_title('2D探索空間での粒子分布', fontsize=14, fontweight='bold')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(-2, 2)
    ax1.set_ylim(-2, 2)
    
    # 3D探索空間
    ax2 = fig.add_subplot(122, projection='3d')
    
    # 3Dサーフェス
    X_3d, Y_3d = np.meshgrid(np.linspace(-2, 2, 50), np.linspace(-2, 2, 50))
    Z_3d = (1 - X_3d)**2 + 100 * (Y_3d - X_3d**2)**2
    Z_3d = np.log10(Z_3d + 1)  # 対数スケールで表示
    
    # サーフェスプロット
    surf = ax2.plot_surface(X_3d, Y_3d, Z_3d, cmap='viridis', 
                           alpha=0.6, edgecolor='none')
    
    # 粒子を3D空間に配置
    particles_z = [(1 - x)**2 + 100 * (y - x**2)**2 for x, y in zip(particles_x, particles_y)]
    particles_z = np.log10(np.array(particles_z) + 1)
    
    ax2.scatter(particles_x, particles_y, particles_z, 
               s=80, c='red', edgecolors='darkred', label='粒子')
    
    # 最適解
    ax2.scatter([1], [1], [0], s=200, c='gold', marker='*', 
               edgecolors='orange', linewidth=2, label='最適解')
    
    ax2.set_xlabel('パラメータ X', fontsize=11)
    ax2.set_ylabel('パラメータ Y', fontsize=11)
    ax2.set_zlabel('評価値 (log scale)', fontsize=11)
    ax2.set_title('3D探索空間での粒子分布', fontsize=14, fontweight='bold')
    
    # 視点を調整
    ax2.view_init(elev=20, azim=45)
    
    plt.tight_layout()
    plt.savefig('pso_search_space.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_velocity_update_diagram():
    """速度更新メカニズムの図"""
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    # 粒子の現在位置
    particle_x, particle_y = 0.3, 0.3
    
    # ベクトルの始点
    origin_x, origin_y = particle_x, particle_y
    
    # 1. 慣性項（現在の速度）
    inertia_x, inertia_y = 0.15, 0.1
    ax.arrow(origin_x, origin_y, inertia_x, inertia_y,
            head_width=0.02, head_length=0.015, fc='gray', ec='gray',
            linewidth=3, label='慣性項 (w×v)')
    
    # 2. 認知的要素（pbest方向）
    pbest_x, pbest_y = 0.6, 0.7
    cognitive_x = (pbest_x - particle_x) * 0.3
    cognitive_y = (pbest_y - particle_y) * 0.3
    ax.arrow(origin_x, origin_y, cognitive_x, cognitive_y,
            head_width=0.02, head_length=0.015, fc='green', ec='green',
            linewidth=3, label='認知項 (c1×r1×(pbest-x))')
    
    # 3. 社会的要素（gbest方向）
    gbest_x, gbest_y = 0.8, 0.6
    social_x = (gbest_x - particle_x) * 0.25
    social_y = (gbest_y - particle_y) * 0.25
    ax.arrow(origin_x, origin_y, social_x, social_y,
            head_width=0.02, head_length=0.015, fc='orange', ec='orange',
            linewidth=3, label='社会項 (c2×r2×(gbest-x))')
    
    # 合成ベクトル（新しい速度）
    new_velocity_x = inertia_x + cognitive_x + social_x
    new_velocity_y = inertia_y + cognitive_y + social_y
    ax.arrow(origin_x, origin_y, new_velocity_x, new_velocity_y,
            head_width=0.03, head_length=0.02, fc='red', ec='red',
            linewidth=4, label='新しい速度', zorder=10)
    
    # 位置をマーク
    ax.scatter(particle_x, particle_y, s=200, c='red', 
              edgecolors='darkred', zorder=15, label='現在位置')
    ax.scatter(pbest_x, pbest_y, s=150, c='green', marker='s', 
              zorder=12, label='個体最良(pbest)')
    ax.scatter(gbest_x, gbest_y, s=200, c='gold', marker='*', 
              zorder=12, label='全体最良(gbest)')
    
    # ベクトル分解を示す補助線
    ax.plot([origin_x + inertia_x, origin_x + inertia_x + cognitive_x],
           [origin_y + inertia_y, origin_y + inertia_y + cognitive_y],
           'g--', linewidth=1, alpha=0.5)
    ax.plot([origin_x + inertia_x + cognitive_x, origin_x + new_velocity_x],
           [origin_y + inertia_y + cognitive_y, origin_y + new_velocity_y],
           'orange', linestyle='--', linewidth=1, alpha=0.5)
    
    # 注釈
    ax.text(origin_x + inertia_x/2, origin_y + inertia_y/2 - 0.03, 
           'w=0.7', fontsize=10, ha='center')
    ax.text(origin_x + cognitive_x/2 - 0.03, origin_y + cognitive_y/2, 
           'c1=1.5\nr1=0.8', fontsize=10, ha='center')
    ax.text(origin_x + social_x/2 + 0.03, origin_y + social_y/2, 
           'c2=1.5\nr2=0.6', fontsize=10, ha='center')
    
    # 速度更新式
    ax.text(0.5, 0.05, 
           r'$v_{new} = w \cdot v + c_1 \cdot r_1 \cdot (pbest - x) + c_2 \cdot r_2 \cdot (gbest - x)$',
           fontsize=12, ha='center', transform=ax.transAxes,
           bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow"))
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel('X座標', fontsize=12)
    ax.set_ylabel('Y座標', fontsize=12)
    ax.set_title('PSO速度更新メカニズム', fontsize=16, fontweight='bold')
    ax.legend(loc='upper left', fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig('pso_velocity_update.png', dpi=300, bbox_inches='tight')
    plt.close()

# すべての図を生成
if __name__ == "__main__":
    print("PSO説明図を生成中...")
    
    print("1. 粒子の構成要素図...")
    create_particle_components_diagram()
    
    print("2. 鳥の群れからPSOへの概念図...")
    create_birds_to_pso_concept()
    
    print("3. 探索空間の可視化...")
    create_search_space_visualization()
    
    print("4. 速度更新メカニズム図...")
    create_velocity_update_diagram()
    
    print("完了！以下のファイルが生成されました：")
    print("- pso_particle_components.png")
    print("- pso_birds_concept.png")
    print("- pso_search_space.png")
    print("- pso_velocity_update.png")