# generate_building_fem_analyze.py 詳細レポート

## 概要

`generate_building_fem_analyze.py`は、FreeCADを使用して建築構造の自動生成とFEM（有限要素法）解析を行う中核モジュールです。このスクリプトは、パラメトリックな建物モデルを生成し、構造解析を実行して、安全性、経済性、環境負荷、快適性、施工性を総合的に評価します。

### 最新バージョンの変更点
- 材料選択機能の追加（コンクリート、木材、CLT）
- 各構造部位（柱、床、壁、屋根、バルコニー）で独立した材料選択が可能
- 材料特性に基づく断面寸法の自動調整
- リサイクル材料係数の考慮によるCO2排出量計算の精緻化

## ファイル構造

### 1. ヘッダー部（1-75行）
- エンコーディング宣言とドキュメント文字列
- モジュールインポート
  - FreeCAD関連モジュール（App, Part, ObjectsFem, gmshtools, CcxTools）
  - 標準ライブラリ（os, math, traceback, random, time）
  - データ構造（dataclasses, numpy）
- グローバル変数定義
  - `VERBOSE_OUTPUT`: デバッグ出力制御フラグ（デフォルト: False）
  - `FEM_AVAILABLE`, `CCX_AVAILABLE`, `GUI_AVAILABLE`: 利用可能機能フラグ

### 2. データクラス定義（76-89行）
```python
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
    balcony_depth: float = 0.0  # バルコニー奥行き [m]
```

### 3. 屋根関連関数（94-385行）

#### 屋根曲率計算
```python
def calculate_roof_curvature(roof_morph: float) -> float:
    """屋根の曲率を計算"""
```
- roof_morphパラメータ（0.0-1.0）から屋根の曲率を決定
- 3段階の変化：平坦→標準→急勾配

#### 屋根効率計算
```python
def calculate_roof_efficiency(roof_morph: float, roof_shift: float) -> float:
    """屋根形状による構造効率を計算"""
```
- アーチ効果による構造効率を評価
- 非対称性によるペナルティを考慮

#### パラメトリックかまぼこ屋根生成
```python
def create_parametric_barrel_roof(
    Lx_mm, Ly_mm, total_height_mm, tr_mm,
    roof_morph: float = 0.5,
    roof_shift: float = 0.0
):
```
- 最小パラメータで多様な屋根形状を生成
- morphパラメータで形状を大きく変化
- shiftパラメータで非対称性を制御
- エラー時はシンプルなボックス型屋根にフォールバック

## 使用方法

### 基本的な使い方

#### 1. パラメータ辞書からの建物評価（推奨）
```python
from generate_building_fem_analyze import evaluate_building_from_params

# パラメータ辞書を準備
params = {
    # 基本形状パラメータ
    'Lx': 8.0,          # 建物幅 [m]
    'Ly': 6.0,          # 建物奥行き [m]
    'H1': 3.5,          # 1階高 [m]
    'H2': 3.0,          # 2階高 [m]
    'tf': 250,          # 床スラブ厚 [mm]
    'tr': 150,          # 屋根スラブ厚 [mm]
    'bc': 400,          # 柱幅 [mm]
    'hc': 400,          # 柱厚 [mm]
    'tw_ext': 200,      # 外壁厚 [mm]
    
    # 追加パラメータ
    'wall_tilt_angle': 0.0,    # 壁傾斜角度 [度] (-40.0 to 30.0)
    'window_ratio_2f': 0.4,    # 2階窓面積率 (0.0-0.8)
    'roof_morph': 0.5,         # 屋根形状 (0.0-1.0)
    'roof_shift': 0.0,         # 屋根非対称性 (-1.0 to 1.0)
    'balcony_depth': 1.5,      # バルコニー奥行き [m]
    
    # 材料選択（0:コンクリート, 1:木材, 2:CLT）
    'material_columns': 0,     # 柱材料
    'material_floor1': 0,      # 1階床材料
    'material_floor2': 0,      # 2階床材料
    'material_roof': 0,        # 屋根材料
    'material_walls': 0,       # 外壁材料
    'material_balcony': 0      # バルコニー材料
}

# 評価実行
results = evaluate_building_from_params(
    params, 
    save_fcstd=True,                    # FCStdファイルを保存
    fcstd_path='test_building.FCStd'    # 保存パス
)

# 結果確認
print(f"構造安全率: {results['safety_factor']}")
print(f"建設コスト: {results['cost']} 円")
print(f"CO2排出量: {results['co2_emission']} kg-CO2")
```

#### 2. 直接関数呼び出し（詳細制御が必要な場合）
```python
from generate_building_fem_analyze import (
    create_realistic_building_model,
    run_fem_analysis,
    evaluate_structural_safety,
    evaluate_economy,
    evaluate_environmental_impact
)

# 建物モデル生成
doc, building_obj, building_info = create_realistic_building_model(
    Lx=8.0, Ly=6.0, H1=3.5, H2=3.0,
    tf=250, tr=150, bc=400, hc=400, tw_ext=200,
    wall_tilt_angle=0.0,
    window_ratio_2f=0.4,
    roof_morph=0.5,
    roof_shift=0.0,
    balcony_depth=1.5
)

# FEM解析実行
fem_results = run_fem_analysis(doc, building_obj, mesh_size_mm=200)

# 各種評価
safety = evaluate_structural_safety(fem_results)
economy = evaluate_economy(building_info)
environmental = evaluate_environmental_impact(building_info)
```

### パラメータ範囲と推奨値

| パラメータ | 範囲 | 推奨値 | 単位 | 説明 |
|-----------|------|--------|------|------|
| Lx | 5.0-20.0 | 8.0-10.0 | m | 建物幅（東西方向） |
| Ly | 4.0-15.0 | 6.0-8.0 | m | 建物奥行き（南北方向） |
| H1 | 2.5-5.0 | 3.0-3.5 | m | 1階高 |
| H2 | 2.5-4.0 | 2.8-3.0 | m | 2階高 |
| tf | 150-400 | 200-250 | mm | 床スラブ厚 |
| tr | 100-300 | 150-200 | mm | 屋根スラブ厚 |
| bc | 200-600 | 300-400 | mm | 柱幅 |
| hc | 200-600 | 300-400 | mm | 柱厚 |
| tw_ext | 150-300 | 180-220 | mm | 外壁厚 |
| wall_tilt_angle | -40.0-30.0 | -10.0-10.0 | 度 | 壁傾斜角度 |
| window_ratio_2f | 0.0-0.8 | 0.3-0.5 | - | 2階窓面積率 |
| roof_morph | 0.0-1.0 | 0.3-0.7 | - | 屋根形状（0:平坦→1:急勾配） |
| roof_shift | -1.0-1.0 | -0.3-0.3 | - | 屋根非対称性 |
| balcony_depth | 0.0-3.0 | 1.0-2.0 | m | バルコニー奥行き |

### 4. GUI関連関数（120-168行）
```python
def set_part_color(obj, color_tuple):
    """パーツに色を設定（GUI環境でのみ動作）"""

def ensure_parts_visibility(doc):
    """保存前に全パーツの可視化を確実に設定"""
```

### 5. バルコニー生成関数（387-437行）
```python
def create_balcony(Lx_mm: float, Ly_mm: float, H1_mm: float, balcony_depth_mm: float) -> Any:
    """バルコニーを生成（西側壁面に設置）"""
```
- 床スラブ、手すり壁を含む完全なバルコニー構造
- 安全基準に準拠（手すり高1100mm）

### 6. メイン建物生成関数（439-1036行）
```python
def create_realistic_building_model(
    # 基本パラメータ
    Lx: float, Ly: float, H1: float, H2: float,
    tf: float, tr: float, bc: float, hc: float,
    tw_ext: float,
    # 追加パラメータ
    wall_tilt_angle: float = 0.0,
    window_ratio_2f: float = 0.4,
    roof_morph: float = 0.5,
    roof_shift: float = 0.0,
    balcony_depth: float = 0.0,
    # 材料選択パラメータ（0:コンクリート, 1:木材, 2:CLT）
    material_columns: int = 0,
    material_floor1: int = 0,
    material_floor2: int = 0,
    material_roof: int = 0,
    material_walls: int = 0,
    material_balcony: int = 0
) -> (Any, Any, Dict[str, Any]):
```

#### 生成される構造要素
1. **基礎**（400mm厚）
2. **床スラブ**（1階、2階）
3. **柱**（4本、ピロティ構造）
4. **階段**（外部設置、踊り場付き）
5. **2階壁**（傾斜対応、窓開口部付き）
6. **屋根**（パラメトリックかまぼこ屋根）
7. **バルコニー**（オプション）

### 7. FEM解析関数（1038-1336行）
```python
def run_fem_analysis(doc, model, mesh_size_mm=200):
    """FEM解析の実行"""
```

#### 解析プロセス
1. **解析準備**
   - 解析コンテナ作成
   - ソルバーオブジェクト設定（CalculiX）
   
2. **材料設定**
   - **コンクリート**（C30/37相当）
     - ヤング率: 33,000 MPa
     - ポアソン比: 0.17
     - 密度: 2400 kg/m³
     - CO2排出: 410 kg/m³
   - **木材**（構造用集成材）
     - ヤング率: 11,000 MPa
     - ポアソン比: 0.3
     - 密度: 500 kg/m³
     - CO2排出: -836 kg/m³（炭素固定効果）
   - **CLT**（直交集成板）
     - ヤング率: 9,000 MPa
     - ポアソン比: 0.3
     - 密度: 500 kg/m³
     - CO2排出: -752 kg/m³（炭素固定効果）

3. **境界条件**
   - 基礎底面を完全固定

4. **荷重設定**
   - 自重
   - 積載荷重（住宅：1800 N/m²、屋根：600 N/m²）
   - 風荷重（基準風速34m/s、地表面粗度区分Ⅲ）

5. **メッシュ生成**
   - Gmshを使用
   - CharacteristicLengthMax: 600.0 mm
   - CharacteristicLengthMin: 200.0 mm
   - NumThreads: 2（安定性向上、0だと全コア）
   - Mesh.Optimize = 1
   - Mesh.OptimizeNetgen = 1

6. **解析実行**
   - CalculiXソルバーで静的解析
   - 結果取得（応力、変位、歪み）

### 8. 結果評価関数（1339-1556行）

#### 構造安全性評価
```python
def evaluate_structural_safety(fem_results):
    """構造安全性の評価"""
```
- 許容応力度設計法に基づく評価
- コンクリート許容圧縮応力: 10 MPa（長期）
- 安全率計算

#### 経済性評価
```python
def evaluate_economy(building_info):
    """経済性の評価"""
```
- 材料費、施工費を考慮
- 複雑形状による追加コスト

#### 環境性評価
```python
def evaluate_environmental_impact(building_info):
    """環境負荷の評価"""
```
- CO2排出量計算（コンクリート、鉄筋）

#### 快適性評価
```python
def evaluate_comfort(building_info):
    """快適性の評価"""
```
- 床面積、天井高、開口率を評価

#### 施工性評価
```python
def evaluate_constructability(building_info):
    """施工性の評価"""
```
- 標準化度、アクセス性、重量制限を考慮

### 9. 統合評価関数（1558-1630行）
```python
def evaluate_building_from_params(params_dict):
    """パラメータから建物を生成・解析・評価する統合関数"""
```

## 主要な特徴

### 1. パラメトリック設計
- 21個の設計パラメータで多様な建物形状を生成
  - 基本形状パラメータ: 15個
  - 材料選択パラメータ: 6個（各部位独立）
- かまぼこ屋根の形状を2つのパラメータで制御
- 材料に応じた断面寸法の自動調整機能

### 2. 包括的な構造解析
- CalculiXによる高精度FEM解析
- 自重、積載荷重、風荷重を考慮

### 3. 多目的評価
- 構造安全性（安全率）
- 経済性（建設コスト）
- 環境性（CO2排出量）
- 快適性（空間品質）
- 施工性（施工難易度）

### 4. エラーハンドリング
- 各処理段階でのエラーキャッチ
- フォールバック機構（簡略化モデル）

## 使用上の注意

### 必須環境
- FreeCAD 1.0.0以上
- CalculiX（FEMソルバー）
- Gmsh（メッシュ生成）

### メモリ使用
- 複雑なモデルでは大量のメモリを使用
- 推奨: 8GB以上のRAM

### 実行時間
- 1モデルあたり30秒〜2分（モデル複雑度による）

### 推奨設定
- Gmsh NumThreads: 2（安定性向上、0だと全コア使用）
- メッシュサイズ: 200-600mm

## トラブルシューティング

### よくある問題
1. **Segmentation Fault**
   - Gmshのスレッド数を1または2に設定
   - メッシュサイズを大きくする

2. **メモリ不足**
   - モデルを簡略化
   - メッシュサイズを大きくする

3. **解析収束しない**
   - 境界条件を確認
   - 荷重条件を段階的に適用

## 材料選択機能詳細

### サポートされる材料

1. **コンクリート（material_value = 0）**
   - 標準的なRC構造
   - 高い圧縮強度と耐久性
   - 最も汎用的な選択肢

2. **木材（material_value = 1）**
   - 構造用集成材
   - 軽量で環境負荷が低い
   - 炭素固定効果によりCO2排出量がマイナス

3. **CLT（material_value = 2）**
   - 直交集成板
   - 大断面の面材として使用
   - 木材より高い剛性と寸法安定性

### 材料選択による自動調整

- **床スラブ厚**: 木材系選択時は自動的に厚みを増加（×1.5）
- **柱断面**: 材料強度に応じて適切なサイズに調整
- **壁厚**: 材料特性を考慮した最適厚みを設定

### 材料別の特徴比較

| 項目 | コンクリート | 木材 | CLT |
|------|------------|------|-----|
| 初期コスト | 低 | 中 | 高 |
| CO2排出量 | 高 | マイナス | マイナス |
| 施工性 | 標準 | 良好 | 良好 |
| 耐久性 | 高 | 中 | 中 |
| メンテナンス | 低 | 中 | 中 |

---
*レポート作成日: 2025-07-16*
*最終更新日: 2025-07-23*