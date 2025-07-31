import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle, FancyArrowPatch
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

# 日本語フォントの設定
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'Hiragino Sans', 'Yu Gothic', 'Meiryo', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']
plt.rcParams['axes.unicode_minus'] = False

def create_building_generation_flowchart():
    """建物生成プロセスのフローチャート"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 10))
    
    # フローチャートの要素を定義
    box_props = dict(boxstyle="round,pad=0.3", facecolor="lightblue", edgecolor="navy", linewidth=2)
    process_props = dict(boxstyle="round,pad=0.3", facecolor="lightgreen", edgecolor="darkgreen", linewidth=2)
    decision_props = dict(boxstyle="round,pad=0.3", facecolor="lightyellow", edgecolor="orange", linewidth=2)
    
    # 入力パラメータ
    ax.text(0.5, 0.95, '21個の設計パラメータ', ha='center', va='center', 
           fontsize=14, fontweight='bold', bbox=box_props, transform=ax.transAxes)
    
    # パラメータの内訳
    param_text = '• 基本形状: 9個\n• 追加形状: 5個\n• 材料選択: 6個'
    ax.text(0.85, 0.92, param_text, ha='left', va='top', 
           fontsize=10, transform=ax.transAxes)
    
    # 矢印
    ax.annotate('', xy=(0.5, 0.87), xytext=(0.5, 0.93),
               arrowprops=dict(arrowstyle='->', lw=2, color='black'),
               transform=ax.transAxes)
    
    # 前処理
    ax.text(0.5, 0.85, '前処理・単位変換', ha='center', va='center', 
           fontsize=12, bbox=process_props, transform=ax.transAxes)
    
    # 材料による断面調整
    ax.text(0.5, 0.78, '材料別断面調整', ha='center', va='center', 
           fontsize=11, bbox=decision_props, transform=ax.transAxes)
    ax.text(0.85, 0.78, '木材選択時:\n床厚×1.5\n柱断面×1.2', ha='left', va='center', 
           fontsize=9, transform=ax.transAxes)
    
    # 3Dモデル生成のフロー
    y_pos = 0.68
    components = [
        '1. 基礎生成（400mm厚）',
        '2. 1階床スラブ生成',
        '3. 柱生成（4本）',
        '4. 2階床スラブ生成',
        '5. 屋根生成（パラメトリック）',
        '6. 外壁生成（窓開口付き）',
        '7. 階段生成（外部）',
        '8. バルコニー生成（オプション）'
    ]
    
    for i, comp in enumerate(components):
        y = y_pos - i * 0.07
        ax.text(0.3, y, comp, ha='center', va='center', 
               fontsize=10, bbox=process_props, transform=ax.transAxes)
        if i < len(components) - 1:
            ax.annotate('', xy=(0.3, y - 0.035), xytext=(0.3, y - 0.025),
                       arrowprops=dict(arrowstyle='->', lw=1.5, color='black'),
                       transform=ax.transAxes)
    
    # 統合処理
    ax.text(0.5, 0.15, '部品の統合（Fusion）', ha='center', va='center', 
           fontsize=12, bbox=process_props, transform=ax.transAxes)
    
    ax.annotate('', xy=(0.5, 0.17), xytext=(0.3, 0.2),
               arrowprops=dict(arrowstyle='->', lw=2, color='black'),
               transform=ax.transAxes)
    
    # エラーハンドリング
    ax.text(0.7, 0.4, 'エラー処理', ha='center', va='center', 
           fontsize=11, bbox=decision_props, transform=ax.transAxes)
    ax.text(0.7, 0.35, '部分的失敗\nを許容', ha='center', va='center', 
           fontsize=9, transform=ax.transAxes)
    
    # 出力
    ax.text(0.5, 0.08, '3Dモデル完成', ha='center', va='center', 
           fontsize=14, fontweight='bold', bbox=box_props, transform=ax.transAxes)
    
    ax.annotate('', xy=(0.5, 0.1), xytext=(0.5, 0.13),
               arrowprops=dict(arrowstyle='->', lw=2, color='black'),
               transform=ax.transAxes)
    
    # 特殊処理の注記
    special_box = FancyBboxPatch((0.65, 0.5), 0.3, 0.2, 
                                boxstyle="round,pad=0.02",
                                facecolor='lightyellow', 
                                edgecolor='orange',
                                transform=ax.transAxes)
    ax.add_patch(special_box)
    ax.text(0.8, 0.65, '特殊処理', ha='center', va='top', 
           fontsize=11, fontweight='bold', transform=ax.transAxes)
    ax.text(0.8, 0.58, '• 傾斜壁の対応\n• 窓開口の調整\n• 極端角度での\n  補強柱追加', 
           ha='center', va='center', fontsize=9, transform=ax.transAxes)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    ax.set_title('建物生成プロセスフロー', fontsize=16, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig('building_generation_flow.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

def create_fem_analysis_diagram():
    """FEM解析の荷重条件と境界条件を示す図"""
    fig = plt.figure(figsize=(14, 8))
    
    # 3D建物モデル
    ax1 = fig.add_subplot(121, projection='3d')
    
    # 建物の基本形状
    width, depth, height = 8, 6, 7
    
    # 建物の頂点
    vertices = [
        # 底面
        [0, 0, 0], [width, 0, 0], [width, depth, 0], [0, depth, 0],
        # 上面
        [0, 0, height], [width, 0, height], [width, depth, height], [0, depth, height]
    ]
    
    # 面を定義
    faces = [
        [vertices[0], vertices[1], vertices[5], vertices[4]],  # 前面
        [vertices[2], vertices[3], vertices[7], vertices[6]],  # 背面
        [vertices[0], vertices[3], vertices[7], vertices[4]],  # 左面
        [vertices[1], vertices[2], vertices[6], vertices[5]],  # 右面
        [vertices[4], vertices[5], vertices[6], vertices[7]],  # 上面
        [vertices[0], vertices[1], vertices[2], vertices[3]]   # 底面
    ]
    
    # 建物を描画
    for face in faces:
        poly = [[point[0], point[1], point[2]] for point in face]
        ax1.add_collection3d(Poly3DCollection([poly], alpha=0.3, facecolor='lightgray', edgecolor='black'))
    
    # 基礎（固定境界条件）
    foundation_x = [0, width, width, 0, 0]
    foundation_y = [0, 0, depth, depth, 0]
    foundation_z = [-0.5, -0.5, -0.5, -0.5, -0.5]
    ax1.plot(foundation_x, foundation_y, foundation_z, 'k-', linewidth=3)
    
    # 固定記号
    for i in range(4):
        x = foundation_x[i]
        y = foundation_y[i]
        ax1.plot([x, x], [y, y], [-0.5, -0.8], 'k-', linewidth=2)
        # 三角形の固定記号
        triangle_x = [x-0.3, x+0.3, x, x-0.3]
        triangle_y = [y, y, y, y]
        triangle_z = [-0.8, -0.8, -0.6, -0.8]
        ax1.plot(triangle_x, triangle_y, triangle_z, 'k-', linewidth=2)
    
    # 荷重の表示
    # 自重（下向き矢印）
    for x in np.linspace(1, width-1, 3):
        for y in np.linspace(1, depth-1, 2):
            ax1.quiver(x, y, height+0.5, 0, 0, -1, color='blue', arrow_length_ratio=0.3, length=0.8)
    
    # 地震荷重（水平矢印）
    for z in np.linspace(1, height-1, 3):
        ax1.quiver(-1, depth/2, z, 1, 0, 0, color='red', arrow_length_ratio=0.3, length=0.8)
    
    # 積載荷重（屋根面）
    for x in np.linspace(1, width-1, 3):
        for y in np.linspace(1, depth-1, 2):
            ax1.quiver(x, y, height+0.5, 0, 0, -0.5, color='green', arrow_length_ratio=0.3, length=0.5)
    
    ax1.set_xlabel('X [m]')
    ax1.set_ylabel('Y [m]')
    ax1.set_zlabel('Z [m]')
    ax1.set_title('荷重条件と境界条件', fontsize=14)
    ax1.view_init(elev=20, azim=45)
    
    # 凡例
    ax1.text2D(0.05, 0.95, '荷重条件:', transform=ax1.transAxes, fontsize=11, fontweight='bold')
    ax1.text2D(0.05, 0.90, '● 自重（青）', transform=ax1.transAxes, fontsize=10, color='blue')
    ax1.text2D(0.05, 0.85, '● 地震荷重（赤）', transform=ax1.transAxes, fontsize=10, color='red')
    ax1.text2D(0.05, 0.80, '● 積載荷重（緑）', transform=ax1.transAxes, fontsize=10, color='green')
    ax1.text2D(0.05, 0.75, '■ 基礎固定', transform=ax1.transAxes, fontsize=10)
    
    # 荷重の詳細
    ax2 = fig.add_subplot(122)
    ax2.axis('off')
    
    # タイトル
    ax2.text(0.5, 0.95, '荷重条件の詳細', ha='center', fontsize=16, fontweight='bold')
    
    # 荷重の表
    load_data = [
        ['荷重種別', '大きさ', '適用位置'],
        ['自重', '9.81 m/s²', '全構造体'],
        ['積載荷重（床）', '1,800 Pa', '住宅床面'],
        ['積載荷重（屋根）', '8,000-10,000 Pa', '屋根面（勾配により変動）'],
        ['積載荷重（バルコニー）', '1,800 Pa', 'バルコニー床面'],
        ['地震荷重', '0.5G（水平）', '建物南側面'],
    ]
    
    # 表を描画
    cell_height = 0.08
    cell_width = 0.3
    start_y = 0.75
    
    for i, row in enumerate(load_data):
        for j, cell in enumerate(row):
            if i == 0:  # ヘッダー
                rect = FancyBboxPatch((j*cell_width, start_y - i*cell_height), 
                                     cell_width, cell_height,
                                     boxstyle="round,pad=0.01",
                                     facecolor='lightblue',
                                     edgecolor='black')
                ax2.add_patch(rect)
                ax2.text(j*cell_width + cell_width/2, start_y - i*cell_height + cell_height/2,
                        cell, ha='center', va='center', fontweight='bold', fontsize=10)
            else:
                rect = Rectangle((j*cell_width, start_y - i*cell_height), 
                               cell_width, cell_height,
                               facecolor='white',
                               edgecolor='black')
                ax2.add_patch(rect)
                ax2.text(j*cell_width + cell_width/2, start_y - i*cell_height + cell_height/2,
                        cell, ha='center', va='center', fontsize=9)
    
    # 材料別応答増幅の説明
    ax2.text(0.5, 0.25, '材料別地震応答増幅係数', ha='center', fontsize=12, fontweight='bold')
    ax2.text(0.2, 0.18, 'コンクリート: 1.0倍（減衰5%）', fontsize=10)
    ax2.text(0.2, 0.13, '木材: 1.5倍（減衰3%）', fontsize=10)
    
    # メッシュ設定
    ax2.text(0.5, 0.05, 'Gmshメッシュ設定: 最大600mm, 最小200mm', 
            ha='center', fontsize=10, style='italic')
    
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig('fem_analysis_conditions.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

def create_evaluation_metrics_diagram():
    """評価指標の構成と計算方法を示す図"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 8))
    
    # 左側：評価指標の構成（レーダーチャート）
    categories = ['構造安全性', '経済性', '環境性', '快適性', '施工性']
    N = len(categories)
    
    # 角度を計算
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    # データ例（満点を10として）
    values_ideal = [10, 10, 10, 10, 10]
    values_example = [8.5, 6.0, 7.5, 8.0, 7.0]
    values_ideal += values_ideal[:1]
    values_example += values_example[:1]
    
    # レーダーチャートを描画
    ax1 = plt.subplot(121, projection='polar')
    ax1.plot(angles, values_ideal, 'o--', linewidth=2, label='理想値', color='lightgray')
    ax1.fill(angles, values_ideal, alpha=0.1, color='lightgray')
    ax1.plot(angles, values_example, 'o-', linewidth=2, label='評価例', color='blue')
    ax1.fill(angles, values_example, alpha=0.25, color='blue')
    
    ax1.set_xticks(angles[:-1])
    ax1.set_xticklabels(categories, fontsize=11)
    ax1.set_ylim(0, 10)
    ax1.set_title('5つの評価指標', fontsize=14, fontweight='bold', pad=20)
    ax1.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
    ax1.grid(True)
    
    # 右側：計算方法の詳細
    ax2.axis('off')
    
    # タイトル
    ax2.text(0.5, 0.95, '評価指標の計算方法', ha='center', fontsize=14, fontweight='bold')
    
    # 各指標の説明
    y_pos = 0.85
    metrics_info = [
        ('1. 構造安全性', '安全率 = min(許容応力/最大応力, 許容変形/最大変形)', 'navy'),
        ('2. 経済性', '総工事費 = 材料費 + 労務費 + 特殊要素費', 'darkgreen'),
        ('3. 環境性', 'CO2排出 = 材料製造 + 運搬 + 施工 - 炭素固定', 'darkorange'),
        ('4. 快適性', 'スコア = Σ(評価項目×重み) [0-10点]', 'purple'),
        ('5. 施工性', 'スコア = 10 - Σ(複雑度による減点)', 'darkred')
    ]
    
    for i, (title, formula, color) in enumerate(metrics_info):
        y = y_pos - i * 0.15
        
        # タイトル
        ax2.text(0.05, y, title, fontsize=12, fontweight='bold', color=color)
        
        # 計算式
        ax2.text(0.1, y - 0.04, formula, fontsize=10)
        
        # 詳細
        if i == 0:  # 構造安全性
            ax2.text(0.1, y - 0.08, '• 目標安全率: 2.0以上', fontsize=9, color='gray')
        elif i == 1:  # 経済性
            ax2.text(0.1, y - 0.08, '• 材料選択により大きく変動', fontsize=9, color='gray')
        elif i == 2:  # 環境性
            ax2.text(0.1, y - 0.08, '• 木材は炭素固定効果でマイナス', fontsize=9, color='gray')
        elif i == 3:  # 快適性
            ax2.text(0.1, y - 0.08, '• 6項目で評価（空間、採光、etc）', fontsize=9, color='gray')
        elif i == 4:  # 施工性
            ax2.text(0.1, y - 0.08, '• 複雑な形状ほど低スコア', fontsize=9, color='gray')
    
    # 重み付けの説明
    weight_box = FancyBboxPatch((0.05, 0.05), 0.9, 0.15,
                               boxstyle="round,pad=0.02",
                               facecolor='lightyellow',
                               edgecolor='orange')
    ax2.add_patch(weight_box)
    ax2.text(0.5, 0.15, '材料別許容応力の重み付け', ha='center', fontsize=11, fontweight='bold')
    ax2.text(0.5, 0.09, '柱: 40% / 壁: 30% / 床: 30%', ha='center', fontsize=10)
    
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    
    plt.tight_layout()
    plt.savefig('evaluation_metrics.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

def create_material_comparison_diagram():
    """材料選択による影響を示す比較図"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    
    # 1. 材料特性の比較（棒グラフ）
    materials = ['コンクリート', '木材']
    properties = {
        'ヤング率\n[GPa]': [33, 11],
        '密度\n[kg/m³]': [2400/100, 500/100],  # スケール調整
        '許容応力\n[MPa]': [35, 6],
        '減衰定数\n[%]': [5, 3]
    }
    
    x = np.arange(len(materials))
    width = 0.2
    
    for i, (prop, values) in enumerate(properties.items()):
        offset = (i - 1.5) * width
        bars = ax1.bar(x + offset, values, width, label=prop)
        # 値を表示
        for bar, val in zip(bars, values):
            if '密度' in prop:
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        f'{val*100:.0f}', ha='center', va='bottom', fontsize=9)
            else:
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                        f'{val}', ha='center', va='bottom', fontsize=9)
    
    ax1.set_xlabel('材料種別')
    ax1.set_ylabel('特性値')
    ax1.set_title('材料特性の比較', fontsize=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(materials)
    ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    ax1.grid(True, alpha=0.3)
    
    # 2. コストとCO2の比較
    cost_data = {
        '材料費': [20, 50],
        '労務費': [25, 45],
        'CO2排出': [410/10, -836/10]  # スケール調整
    }
    
    x = np.arange(len(materials))
    width = 0.25
    
    for i, (item, values) in enumerate(cost_data.items()):
        offset = (i - 1) * width
        bars = ax2.bar(x + offset, values, width, label=item)
        # 値を表示
        for bar, val in zip(bars, values):
            if 'CO2' in item:
                ax2.text(bar.get_x() + bar.get_width()/2, 
                        bar.get_height() + 2 if val > 0 else bar.get_height() - 5,
                        f'{val*10:.0f}', ha='center', va='bottom' if val > 0 else 'top', fontsize=9)
            else:
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                        f'{val}', ha='center', va='bottom', fontsize=9)
    
    ax2.axhline(y=0, color='black', linewidth=0.5)
    ax2.set_xlabel('材料種別')
    ax2.set_ylabel('コスト[千円/m³] / CO2[×10 kg/m³]')
    ax2.set_title('経済性と環境性の比較', fontsize=12)
    ax2.set_xticks(x)
    ax2.set_xticklabels(materials)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    # 3. 断面調整の図解
    ax3.set_title('材料による断面調整', fontsize=12)
    
    # コンクリート柱
    concrete_col = Rectangle((0.2, 0.3), 0.2, 0.4, 
                           facecolor='lightgray', edgecolor='black', linewidth=2)
    ax3.add_patch(concrete_col)
    ax3.text(0.3, 0.2, 'コンクリート柱\n400×400mm', ha='center', fontsize=10)
    
    # 木材柱
    wood_col = Rectangle((0.6, 0.25), 0.24, 0.48, 
                        facecolor='burlywood', edgecolor='brown', linewidth=2)
    ax3.add_patch(wood_col)
    ax3.text(0.72, 0.15, '木材柱\n480×480mm\n(×1.2)', ha='center', fontsize=10)
    
    # 矢印
    ax3.annotate('', xy=(0.55, 0.5), xytext=(0.45, 0.5),
               arrowprops=dict(arrowstyle='->', lw=2, color='red'))
    ax3.text(0.5, 0.55, '材料変更', ha='center', fontsize=10, color='red')
    
    ax3.set_xlim(0, 1)
    ax3.set_ylim(0, 1)
    ax3.axis('off')
    
    # 4. 地震応答の違い
    ax4.set_title('地震応答特性', fontsize=12)
    
    # 時間軸
    t = np.linspace(0, 5, 1000)
    # 地震波（簡略化）
    earthquake = np.sin(2 * np.pi * 2 * t) * np.exp(-0.5 * t)
    
    # コンクリートの応答（減衰5%）
    concrete_response = earthquake * 1.0 * np.exp(-0.05 * t)
    # 木材の応答（減衰3%、増幅1.5倍）
    wood_response = earthquake * 1.5 * np.exp(-0.03 * t)
    
    ax4.plot(t, concrete_response, 'b-', label='コンクリート（減衰5%）', linewidth=2)
    ax4.plot(t, wood_response, 'brown', label='木材（減衰3%、増幅1.5倍）', linewidth=2)
    ax4.axhline(y=0, color='black', linewidth=0.5)
    
    ax4.set_xlabel('時間 [秒]')
    ax4.set_ylabel('応答加速度')
    ax4.legend()
    ax4.grid(True, alpha=0.3)
    ax4.set_xlim(0, 5)
    
    plt.tight_layout()
    plt.savefig('material_comparison.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

def create_parametric_design_diagram():
    """パラメトリック設計の概念図"""
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))
    
    # 中央の建物
    building_center = Rectangle((0.4, 0.35), 0.2, 0.3,
                              facecolor='lightblue', edgecolor='navy', linewidth=3)
    ax.add_patch(building_center)
    ax.text(0.5, 0.5, '3D建物\nモデル', ha='center', va='center', 
           fontsize=14, fontweight='bold')
    
    # パラメータグループ
    param_groups = [
        # (x, y, width, height, title, params)
        (0.05, 0.7, 0.25, 0.2, '基本形状(9)', 
         ['Lx: 建物幅', 'Ly: 奥行き', 'H1: 1階高', 'H2: 2階高', 'tf: 床厚']),
        (0.05, 0.4, 0.25, 0.2, '追加形状(5)', 
         ['壁傾斜角', '窓面積率', '屋根形状', 'バルコニー']),
        (0.05, 0.1, 0.25, 0.2, '材料選択(6)', 
         ['柱材料', '床材料', '壁材料', '屋根材料']),
        (0.7, 0.7, 0.25, 0.15, 'FEM解析', 
         ['応力分布', '変位量', '固有振動数']),
        (0.7, 0.45, 0.25, 0.15, '評価結果', 
         ['安全率', 'コスト', 'CO2排出量']),
        (0.7, 0.2, 0.25, 0.15, '性能指標', 
         ['快適性', '施工性'])
    ]
    
    for x, y, w, h, title, params in param_groups:
        # ボックス
        if '形状' in title or '材料' in title:
            box = FancyBboxPatch((x, y), w, h,
                               boxstyle="round,pad=0.02",
                               facecolor='lightgreen',
                               edgecolor='darkgreen',
                               linewidth=2)
        else:
            box = FancyBboxPatch((x, y), w, h,
                               boxstyle="round,pad=0.02",
                               facecolor='lightyellow',
                               edgecolor='orange',
                               linewidth=2)
        ax.add_patch(box)
        
        # タイトル
        ax.text(x + w/2, y + h - 0.03, title, ha='center', va='top',
               fontsize=11, fontweight='bold')
        
        # パラメータリスト
        param_text = '\n'.join(params[:4])  # 最大4つまで表示
        if len(params) > 4:
            param_text += '\n...'
        ax.text(x + w/2, y + h/2 - 0.02, param_text, ha='center', va='center',
               fontsize=8)
        
        # 矢印
        if x < 0.4:  # 左側（入力）
            ax.annotate('', xy=(0.4, 0.5), xytext=(x + w, y + h/2),
                       arrowprops=dict(arrowstyle='->', lw=2, color='darkgreen'))
        else:  # 右側（出力）
            ax.annotate('', xy=(x, y + h/2), xytext=(0.6, 0.5),
                       arrowprops=dict(arrowstyle='->', lw=2, color='orange'))
    
    # タイトル
    ax.text(0.5, 0.95, 'パラメトリック建物設計システム', 
           ha='center', fontsize=16, fontweight='bold')
    ax.text(0.5, 0.9, '21個のパラメータ → 3Dモデル生成 → FEM解析 → 5つの評価指標', 
           ha='center', fontsize=11)
    
    # 最適化ループ
    loop_arrow = FancyArrowPatch((0.85, 0.15), (0.15, 0.05),
                               connectionstyle="arc3,rad=-.5",
                               arrowstyle='->', lw=2, color='red')
    ax.add_patch(loop_arrow)
    ax.text(0.5, 0.02, '最適化アルゴリズム（PSO, NSGA-II, DE）', 
           ha='center', fontsize=10, color='red')
    
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    plt.tight_layout()
    plt.savefig('parametric_design_system.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()

# すべての図を生成
if __name__ == "__main__":
    print("建物FEM解析説明図を生成中...")
    
    print("1. 建物生成プロセスフロー...")
    create_building_generation_flowchart()
    
    print("2. FEM解析条件...")
    create_fem_analysis_diagram()
    
    print("3. 評価指標...")
    create_evaluation_metrics_diagram()
    
    print("4. 材料比較...")
    create_material_comparison_diagram()
    
    print("5. パラメトリック設計システム...")
    create_parametric_design_diagram()
    
    print("完了！以下のファイルが生成されました：")
    print("- building_generation_flow.png")
    print("- fem_analysis_conditions.png")
    print("- evaluation_metrics.png")
    print("- material_comparison.png")
    print("- parametric_design_system.png")