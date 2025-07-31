# `generate_building_fem_analyze.py` 詳細レポート

## 概要

`generate_building_fem_analyze.py`は，FreeCADを使用して建築構造の自動生成とFEM（有限要素法）解析を行う中核モジュールです．このスクリプトは，パラメトリックな建物モデルを生成し，構造解析を実行して，安全性，経済性，環境負荷，快適性，施工性を総合的に評価します．



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

### 2. データクラス定義（189-205行）
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

### 3. 屋根関連関数（211-491行）

#### 屋根曲率計算
```python
def calculate_roof_curvature(roof_morph: float) -> float:
    """屋根の曲率を計算"""
```
- roof_morphパラメータ（0.0-1.0）から屋根の曲率を決定
- 3段階の変化：平坦→標準→急勾配

#### パラメトリックかまぼこ屋根生成
```python
def create_parametric_barrel_roof(
    Lx_mm, Ly_mm, total_height_mm, tr_mm,
    roof_morph: float = 0.5,
    roof_shift: float = 0.0
):
```
- roof_morphパラメータ（0.0-1.0）で基本形状を制御
  - 0.0: ほぼ平坦
  - 0.5: 標準的なかまぼこ形
  - 1.0: 急勾配
- roof_shiftパラメータ（-1.0 to 1.0）で非対称性を制御
  - 負値: 左側に偏る
  - 0.0: 対称
  - 正値: 右側に偏る
- エラー時は例外を発生（フォールバックなし）

## 関数コール構造

### 1. メインエントリーポイント
```
evaluate_building_from_params() [4057行]
└── evaluate_building() [3699行]
    ├── create_realistic_building_model() [533行]
    │   ├── create_simple_box_roof() [230行] - 平らな屋根の場合
    │   ├── create_parametric_barrel_roof() [252行] - かまぼこ屋根
    │   │   └── calculate_roof_curvature() [200行]
    │   ├── create_balcony() [477行] - バルコニー作成
    │   ├── create_external_stairs() [1513行] - 外部階段
    │   └── safe_gui_operations() [1459行] - GUI操作
    │       ├── safe_set_visibility() [1425行]
    │       └── safe_remove_object() [1402行]
    ├── setup_basic_fem_analysis() [1687行]
    │   └── setup_deterministic_fem() [1490行]
    ├── run_mesh_generation() [2136行]
    │   └── check_fixed_nodes() [2099行]
    ├── run_calculix_analysis() [2283行]
    ├── extract_fem_results() [2397行]
    └── 評価関数群
        ├── calculate_safety_factor() [2760行]
        ├── calculate_economic_cost() [2866行]
        ├── calculate_environmental_impact() [3176行]
        ├── calculate_comfort_score() [3391行]
        └── calculate_constructability_score() [3612行]
```

### 2. ユーティリティ関数
```
├── get_material_name() [134行] - 材料番号から名前への変換
├── is_gui_mode() [1383行] - GUI環境の判定
├── safe_remove_object() [1402行] - 安全なオブジェクト削除
├── safe_set_visibility() [1425行] - 安全な可視性設定
├── safe_gui_operations() [1459行] - GUI操作の安全実行
├── setup_deterministic_fem() [1490行] - 決定論的FEM設定
└── clean_document_for_fcstd_save() [3960行] - FCStd保存前のクリーンアップ
```


## パラメータから建物を作るプロセス

### 1. パラメータの準備

21個の設計パラメータを辞書形式で準備します．実際の数値は，この関数を呼び出す最適化アルゴリズム（PSO，NSGA-II，DEなど）やテストコードによって動的に指定されます．以下は説明用の例です：

```python
params = {
    # 基本形状パラメータ（必須）
    'Lx': 8.0,          # 建物幅 [m]
    'Ly': 6.0,          # 建物奥行き [m]
    'H1': 3.5,          # 1階高 [m]
    'H2': 3.0,          # 2階高 [m]
    'tf': 250,          # 床スラブ厚 [mm]
    'tr': 150,          # 屋根スラブ厚 [mm]
    'bc': 400,          # 柱幅 [mm]
    'hc': 400,          # 柱厚 [mm]
    'tw_ext': 200,      # 外壁厚 [mm]
    
    # 追加パラメータ（オプション）
    'wall_tilt_angle': 0.0,    # 壁傾斜角度 [度]
    'window_ratio_2f': 0.4,    # 2階窓面積率
    'roof_morph': 0.5,         # 屋根形状
    'roof_shift': 0.0,         # 屋根非対称性
    'balcony_depth': 1.5,      # バルコニー奥行き [m]
    
    # 材料選択（0:コンクリート, 1:木材）
    'material_columns': 0,     # 柱材料
    'material_floor1': 0,      # 1階床材料
    'material_floor2': 0,      # 2階床材料
    'material_roof': 0,        # 屋根材料
    'material_walls': 0,       # 外壁材料
    'material_balcony': 0      # バルコニー材料
}
```

### 2. 建物生成の詳細な流れ

#### 2.1 前処理とパラメータ準備
1. **単位変換とパラメータ調整**
   - すべての寸法をm単位からmm単位に変換（×1000）
   - 材料選択に応じた断面調整:
     - 木材系床スラブ: 厚さ×1.5
     - 木材系柱: 断面×1.2
     - 木材系壁: 厚さ×1.5

2. **FreeCADドキュメントの準備**
   - 新規ドキュメント作成
   - 既存ドキュメントとの名前衝突を回避

#### 2.2 建物構造の生成順序

1. **基礎（Foundation）**
   - 寸法: 建物幅×奥行×400mm厚
   - 位置: Z=-400mm（地下に埋設）
   - 材料: 常にコンクリート（パラメトリック最適化の範囲外）
   - 設計上の理由:
     - 地中埋設部は土圧・地下水の影響で高耐久性が必要
     - 木材は地中で腐朽リスクが高い
     - 建築基準法でも基礎は原則コンクリート
     - したがって最適化対象から除外

2. **床スラブ（Floor1, Floor2）**
   - 1階床: 地上レベル（Z=0）に配置
   - 2階床: H1位置に配置，階段開口付き
     - 開口サイズ: 1000×2000mm
     - 階段終端位置に合わせて配置

3. **柱（Columns）**
   - 基本配置: 四隅＋中央の5本
   - 傾斜角度による位置調整:
     - 内傾斜時: 東側柱を内側にシフト
     - 外傾斜時: 安全マージンを確保
   - 極端な傾斜（±25度以上）で補強柱追加

4. **屋根（RoofSlab）**
   - かまぼこ屋根生成（roof_morph, roof_shiftパラメータ使用）
   - 内傾斜時: 屋根幅を調整
   - エラー時は例外発生（フォールバックなし）

5. **外壁（Walls）**
   - 1階: ピロティ構造のため最小限
   - 2階: 四面の外壁
     - 東面: 傾斜壁（wall_tilt_angleに応じた台形/五角形断面）
     - 西面: バルコニードア開口付き
     - 南北面: 窓開口付き（window_ratio_2fで制御）

6. **階段（Staircase）**
   - L字型外部階段
   - 踏面300mm，蹴上200mm
   - 踊り場付き
   - 建物本体とは分離（FEM解析から除外）

7. **バルコニー（Balcony）**
   - 西側2階レベルに設置
   - 手すり高1100mm（安全基準準拠）
   - balcony_depthパラメータで奥行制御

#### 2.3 形状の統合と最適化

1. **部品の融合（Fusion）**
   - 基礎から順番に全部品を結合
   - エラー処理で部分的な失敗を許容
   - 最終的に単一のソリッド形状を生成

2. **マテリアル情報の付与**
   - 各部品に材料タイプを設定（0:コンクリート, 1:木材）
   - FEM解析用の材料特性と連携

3. **可視性とGUI設定**
   - GUI環境でのみ色設定を実行
   - 全部品の可視性を確保

#### 2.4 特殊な処理

**傾斜壁の対応**
- 壁の上端位置を計算: `wall_offset_top = H2_mm * tan(wall_tilt_angle)`
- 窓開口の位置と大きさを動的調整
- 極端な角度で追加の安全対策

**材料別の自動調整**
- 断面寸法を材料強度に応じて自動調整
- 木材系は一般的に大きな断面が必要

**エラーハンドリング**
- 各生成段階でtry-except処理
- 部分的な失敗でも継続可能な設計

### 3. 3Dモデルの構成要素

`create_realistic_building_model()`で以下の部品が生成されます：

- **基礎** (Foundation) - 400mm厚のコンクリート基礎
- **1階床** (Floor1) - ピロティ構造の床スラブ
- **柱** (Columns) - 4本の角柱
- **2階床** (Floor2) - 2階の床スラブ
- **外壁** (Walls) - 窓開口付きの2階外壁
- **屋根** (RoofSlab) - かまぼこ屋根または平屋根
- **階段** (Staircase) - 外部階段
- **バルコニー** (Balcony) - オプション

## 評価プロセス

### 1. FEM解析

1. **メッシュ生成**
   - Gmshを使用（3D自動メッシュ生成）
   - CharacteristicLengthMax: 600mm（最大要素サイズ）
   - CharacteristicLengthMin: 200mm（最小要素サイズ）
   - Algorithm2D/3D: 'Automatic'（自動選択）
   - NumThreads: 2（安定性向上，0だと全コア使用でクラッシュリスク）

2. **荷重条件**
   
   **自重（重力荷重）**
   - 全構造体に9.81 m/s²の重力加速度を適用
   - 材料密度に基づく自動計算
   
   **積載荷重**
   
   • 住宅床面: 1800 Pa（建築基準法準拠）
   
   • 屋根面: 基本荷重 10000 Pa × 荷重低減係数
     - 平坦屋根（roof_morph < 0.33）:  
       1.0（低減なし） → 10000 Pa × 1.0 = 10000 Pa
     - 標準かまぼこ（0.33-0.67）:  
       0.9（10%低減，雪が滑りやすい） → 10000 Pa × 0.9 = 9000 Pa
     - 急勾配（> 0.67）:  
       0.8（20%低減，さらに滑りやすい） → 10000 Pa × 0.8 = 8000 Pa
   
   • バルコニー床面: 1800 Pa（建築基準法準拠）
   
   **地震荷重**
   
   • 基本設定: 地震係数 0.5G（0.5×9.81 m/s²）
   
   • 適用位置: 建物南側面に水平圧力として
   
   • 材料別応答増幅
     - コンクリート: 1.0倍（減衰5%）
     - 木材: 1.5倍（減衰3%）
   
   • 地震力計算: 地震力 = 総質量 × 9.81 × 地震係数 × 応答増幅係数
   
   • 実装箇所: 1896行目にて base_seismic_coefficient = 0.5 として定義
   
   **注記**: 風荷重は現在の実装には含まれていません

3. **解析実行**
   - CalculiXソルバーで線形静的解析
   - 出力結果:
     - 応力分布（von Mises応力，主応力）
     - 変位量（節点変位ベクトル）
     - ひずみ分布
   - 最大値を抽出して安全性評価に使用

### 2. 評価指標の計算

#### 2.1 構造安全性 (Safety Factor)

**計算式：**
```
安全率 = min(応力による安全率, 変形による安全率)
応力による安全率 = 許容応力 / 最大応力
変形による安全率 = 許容変形 / 最大変形
```

**材料別許容応力（短期許容応力）：**
- コンクリート: 35.0 MPa（C30/37相当の短期許容圧縮応力）
- 木材: 6.0 MPa（構造用集成材の短期許容圧縮応力）

**加重平均許容応力の計算：**
- 柱材料の影響: 40%
- 壁材料の影響: 30%
- 床材料の影響: 30%

**変形制限：**
- 層間変形角: 1/200以下
- 木造の場合: 変形制限を0.3倍（70%厳しく評価）
- 繰返し荷重疲労係数: 0.6～0.7（材料により異なる）

**安全率の目標値：**
- 目標安全率: 2.0以上（通常の安全基準）
- 最小許容安全率: 1.0（これ以下は構造的に危険）

#### 2.2 経済性 (Cost)

**総工事費の構成：**
```
総工事費 = 構造工事費 + 基本建築費 + 特殊要素費
```

**1. 材料費：**
- コンクリート: 20,000円/m³
- 木材: 15,000円/m³
- 材料選択による断面増加を考慮（木材は1.2～1.5倍）

**2. 労務費：**
- コンクリート工事: 25,000円/m³
- 木材工事: 45,000円/m³
- 型枠工事: 10,000円/m²
- 鉄筋工事: 150円/kg

**3. 構造複雑度による補正：**
- 柱断面過大（>400×400mm）: 対数的コスト増加
- 床版厚過大（>200mm）: 対数的コスト増加
- 壁傾斜: 傾斜角10度で10%コスト増
- 全木造（5箇所）: +10%
- 木造主体（3箇所以上）: +5%

**4. 特殊要素コスト：**
- 外部階段: 1,500,000円（固定）
- バルコニー: 深さに応じて200,000～800,000円
- かまぼこ屋根: 曲率に応じて追加コスト

#### 2.3 環境負荷 (CO2 Emission)

**CO2排出量の内訳：**
```
CO2総排出量 = 材料製造CO2 + 鉄筋CO2 + 運搬CO2 + 施工CO2
```

**1. 材料別CO2排出係数：**
- コンクリート: 300 kg-CO2/m³（環境配慮型セメント使用）
- 木材: 50 kg-CO2/m³（製造・加工・輸送のCO2）
- リサイクル材使用時: 排出量を20%削減

**2. 追加的CO2排出：**
- 鉄筋: 2.0 kg-CO2/kg（150kg/m³使用）
- 運搬: 0.1 kg-CO2/kg-km（50km想定）
- 施工: コンクリート50，木材30 kg-CO2/m³

**3. 最適化ポテンシャル：**
- FEM解析で安全率>3.0の場合: 材料削減により20～40%のCO2削減可能
- 応力分布の均一性が高い場合: さらに10%の削減余地

#### 2.4 快適性 (Comfort Score)

**評価項目と配点（合計10点）：**

**1. 空間の広がり感（25%）**
- 天井高評価:
  - 4.0m以上: 満点
  - 3.0m: 標準点
  - 2.4m未満: 大幅減点
- スパン長評価:
  - 15m以上: 満点
  - 8m: 標準点
  - 8m未満: 減点

**2. 採光・眺望（25%）**
- 窓面積率: 0.3～0.5が理想
- 階高による眺望: 高いほど良好
- 南向き窓の評価加点

**3. ピロティ開放感（20%）**
- 1階開放率70%による開放感
- 柱の細さによる視界の良さ
- 外部との連続性

**4. プライバシー（10%）**
- 2階窓配置の適切性
- 近隣との視線交錯の少なさ

**5. 構造的安心感（10%）**
- 変位量が小さいほど高評価
- 10mm未満: 満点
- 30mm以上: 減点

**6. デザイン要素（10%）**
- 傾斜壁: -1～-2点
- 特殊屋根: -0.5～-1.5点
- バルコニー: +0.5～+2点

#### 2.5 施工性 (Constructability)

**基本スコア: 10点（単純箱型構造）**

**減点要因：**
1. **構造的複雑さ**
   - カンチレバー: -2.0点
   - 外部階段: -1.5点
   - 開口部複雑度: -0.5点/単位

2. **形状の特殊性**
   - 壁傾斜: -0.1点/度
   - かまぼこ屋根:
     - 標準曲率: -0.5点
     - 急曲率: -1.5点
   - バルコニー深さ: -0.1～-0.5点

3. **材料・寸法の特殊性**
   - 過大断面（標準の1.5倍以上）: -1.0点
   - 異種材料混在: -0.5点
   - アクセス困難な高所作業: -1.0点

**加点要因：**
- ピロティ構造（型枠簡略化）: +1.0点
- 標準寸法の使用: +0.5点

### 2.6 評価指標の詳細計算式

#### 安全率の計算式
```python
# 材料別許容応力の加重平均
avg_allowable = (
    material_allowable[columns] * 0.4 +  # 柱: 40%
    material_allowable[walls] * 0.3 +    # 壁: 30%
    material_allowable[floors] * 0.3     # 床: 30%
)

# 応力による安全率
stress_safety = avg_allowable / max_stress

# 変形による安全率
allowable_displacement = building_height_mm / 200  # 層間変形角1/200
displacement_safety = allowable_displacement / max_displacement
if is_wood_structure:
    displacement_safety *= 0.3  # 木造は70%厳しく評価
    displacement_safety *= fatigue_factor  # 疲労係数0.6-0.7

# 最終安全率（小さい方を採用）
safety_factor = min(stress_safety, displacement_safety)
```

#### コスト計算式
```python
# 材料費（材料体積 × 単価 × リサイクル率考慮）
material_cost = Σ(
    part_volume * unit_cost * (1 - recycle_ratio) +
    part_volume * unit_cost * recycle_cost_factor * recycle_ratio
)

# 構造体積係数（対数的増加）
structural_volume_factor = 1.0 + (
    0.3 * log(column_oversize) +
    0.2 * log(floor_oversize) +
    0.1 * log(roof_oversize) +
    0.1 * log(wall_oversize)
) * material_factor * 0.8

# 総工事費
total_cost = (
    (material_cost + labor_cost + rebar_cost + formwork_cost) * 
    structural_complexity * quality_grade_factor * structural_volume_factor +
    base_building_cost * complexity_factor +
    special_element_cost
)
```

#### CO2排出量計算式
```python
# 材料別CO2（リサイクル率考慮）
material_co2 = Σ(
    part_volume * co2_per_m3 * (1 - recycle_ratio) +
    part_volume * co2_per_m3 * recycle_co2_factor * recycle_ratio
)

# 総CO2排出量
total_co2 = (
    material_co2 +                          # 材料製造
    rebar_kg * 2.0 +                       # 鉄筋製造
    total_material_kg * 0.05 * 0.1 +       # 運搬(50km)
    concrete_volume * 50 + wood_volume * 30 # 施工
)

# 最適化ポテンシャル
if safety_factor > 3.0:
    optimization_potential = 0.2 + (safety_factor - 3.0) * 0.05
```

#### 快適性スコア計算式
```python
# 各項目のスコア計算（-10～20の範囲）
height_score = f(avg_height)  # 天井高評価
span_score = f(avg_span)      # スパン長評価

# 重み付け合計
raw_comfort_score = (
    spaciousness * 0.25 +      # 空間の広がり感: 25%
    lighting * 0.25 +          # 採光・眺望: 25%
    piloti_openness * 0.20 +   # ピロティ開放感: 20%
    privacy * 0.10 +           # プライバシー: 10%
    structural_confidence * 0.10 + # 構造的安心感: 10%
    design_elements * 0.10     # デザイン要素: 10%
)

# 0-10スケールに正規化
comfort_score = max(0, min(10, 5 + raw_comfort_score * 0.5))
```

#### 施工性スコア計算式
```python
# 基本スコアから減点
constructability_score = 10.0

# 構造的複雑さによる減点
if has_cantilever: score -= 2.0
if has_stairs: score -= 1.5
score -= opening_complexity * 0.5

# 形状特殊性による減点
score -= abs(wall_tilt_angle) / 10.0
if roof_morph < 0.2: roof_penalty = 0
elif roof_morph < 0.7: roof_penalty = 0.5
else: roof_penalty = 1.5
score -= roof_penalty

# ピロティ構造による加点
score += 1.0  # 型枠簡略化

# 最終スコア（0-10範囲）
constructability_score = max(0, min(10, score))
```

### 3. 結果の返却

```python
# これは実際の計算結果の例です
results = {
    'status': 'Success',  # 処理状態（Success/Error）
    'safety': {
        'overall_safety_factor': 2.15,      # 構造安全率（目標: 2.0以上）
        'max_stress': 4.65,                 # 最大応力 [MPa]
        'max_displacement': 12.3            # 最大変位 [mm]
    },
    'economic': {
        'cost_per_sqm': 125000,            # 単位面積あたりコスト [円/m²]
        'total_cost': 12000000             # 総建設コスト [円]
    },
    'environmental': {
        'co2_per_sqm': 450,                # 単位面積あたりCO2排出量 [kg-CO2/m²]
        'total_co2': 43200                 # 総CO2排出量 [kg-CO2]
    },
    'comfort': {
        'comfort_score': 7.5,              # 快適性スコア [0-10点]
        'floor_area': 96.0                 # 床面積 [m²]
    },
    'constructability': {
        'constructability_score': 8.2      # 施工性スコア [0-10点]
    }
}
```

**注**: 上記の値は説明用の例です．実際の値は入力パラメータとFEM解析結果により変動します．

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
    
    # 材料選択（0:コンクリート, 1:木材）
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
| Lx | [5.0, 20.0] | [8.0, 10.0] | m | 建物幅（東西方向） |
| Ly | [4.0, 15.0] | [6.0, 8.0] | m | 建物奥行き（南北方向） |
| H1 | [2.5, 5.0] | [3.0, 3.5] | m | 1階高 |
| H2 | [2.5, 4.0] | [2.8, 3.0] | m | 2階高 |
| tf | [150, 400] | [200, 250] | mm | 床スラブ厚 |
| tr | [100, 300] | [150, 200] | mm | 屋根スラブ厚 |
| bc | [200, 600] | [300, 400] | mm | 柱幅 |
| hc | [200, 600] | [300, 400] | mm | 柱厚 |
| tw\_ext | [150, 300] | [180, 220] | mm | 外壁厚 |
| wall\_tilt\_angle | [-40.0, 30.0] | [-10.0, 10.0] | 度 | 壁傾斜角度 |
| window\_ratio\_2f | [0.0, 0.8] | [0.3, 0.5] | - | 2階窓面積率 |
| roof\_morph | [0.0, 1.0] | [0.3, 0.7] | - | 屋根形状（0:平坦→1:急勾配） |
| roof\_shift | [-1.0, 1.0] | [-0.3, 0.3] | - | 屋根非対称性 |
| balcony\_depth | [0.0, 3.0] | [1.0, 2.0] | m | バルコニー奥行き |

### 4. GUI関連関数（175-185行）
```python
def set_part_color(obj, color_tuple):
    """パーツに色を設定（GUI環境でのみ動作）"""

def ensure_parts_visibility(doc):
    """保存前に全パーツの可視化を確実に設定"""
```

### 5. バルコニー生成関数（493-543行）
```python
def create_balcony(Lx_mm: float, Ly_mm: float, H1_mm: float, balcony_depth_mm: float) -> Any:
    """バルコニーを生成（西側壁面に設置）"""
```
- 床スラブ，手すり壁を含む完全なバルコニー構造
- 安全基準に準拠（手すり高1100mm）

### 6. メイン建物生成関数（545-1392行）
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
2. **床スラブ**（1階，2階）
3. **柱**（4本，ピロティ構造）
4. **階段**（外部設置，踊り場付き）
5. **2階壁**（傾斜対応，窓開口部付き）
6. **屋根**（パラメトリックかまぼこ屋根）
7. **バルコニー**（オプション）

### 7. FEM解析関数（1515-2773行）
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

3. **境界条件**
   - 基礎底面を完全固定

4. **荷重設定**
   - 自重
   - 積載荷重（住宅：1800 N/m²，屋根：600 N/m²）
   - 風荷重（基準風速34m/s，地表面粗度区分Ⅲ）

5. **メッシュ生成**
   - Gmshを使用
   - CharacteristicLengthMax: 600.0 mm
   - CharacteristicLengthMin: 200.0 mm
   - NumThreads: 2（安定性向上，0だと全コア）
   - Mesh.Optimize = 1
   - Mesh.OptimizeNetgen = 1

6. **解析実行**
   - CalculiXソルバーで静的解析
   - 結果取得（応力，変位，歪み）

### 8. 結果評価関数

#### 構造安全性評価
```python
def calculate_safety_factor(max_stress, building_info, max_displacement) -> float:
    """安全率を計算する（材料別の許容応力と変形量を考慮）"""
```
- 材料別の許容応力を考慮（柱40%，壁30%，床30%の加重平均）
- コンクリート短期許容圧縮応力: 35.0 MPa
- 木材短期許容圧縮応力: 6.0 MPa
- 層間変形角1/200以下の制限

#### 経済性評価
```python
def calculate_economic_cost(building_info) -> Dict[str, Any]:
    """建物の経済性を評価する（材料選択対応版）"""
```
- 材料費，労務費，施工費を総合評価
- 構造複雑度による対数的コスト増加

#### 環境負荷評価
```python
def calculate_environmental_impact(building_info, fem_results=None) -> Dict[str, Any]:
    """建物の環境負荷（CO2排出量）を評価する（材料選択対応版）"""
```
- 材料製造，鉄筋，運搬，施工から発生するCO2を総合計算
- FEM解析結果に基づく最適化ポテンシャル評価

#### 快適性評価
```python
def calculate_comfort_score(fem_results, building_info) -> Dict[str, Any]:
    """居住快適性を評価する（建築設計要素重視版）"""
```
- 空間の広がり感，採光・眺望，開放感等を6項目で評価

#### 施工性評価
```python
def calculate_constructability_score(building_info, fem_results=None) -> Dict[str, Any]:
    """施工性を評価する（かまぼこ屋根対応版，ねじれ削除）"""
```
- 構造の複雑さ，特殊要素，応力集中等から施工難易度を評価

### 9. 統合評価関数（4086行以降）
```python
def evaluate_building_from_params(params_dict):
    """パラメータから建物を生成・解析・評価する統合関数"""
```

## 主要な特徴

### 1. パラメトリック設計
- 21個の設計パラメータで多様な建物形状を生成
  - 基本形状パラメータ: 15個
  - 材料選択パラメータ: 6個（柱，1階床，2階床，屋根，外壁，バルコニー）
  - 材料選択肢: 0:コンクリート，1:木材
  - 注：基礎は最適化対象外（常にコンクリート）
- かまぼこ屋根の形状を2つのパラメータで制御
- 材料に応じた断面寸法の自動調整機能

### 2. コード品質の向上（2025-07-24）
- 全主要関数に詳細なdocstringを追加
  - 関数の目的と処理内容の明確化
  - 引数の型，単位，値の範囲を明記
  - 戻り値の構造と意味を詳細に記述
- 不要な可視化関数を削除してコードを簡潔化
- 材料選択と評価プロセスの文書化を強化
- 未使用変数のコメント化（target_safety_factor）
- パラメータ範囲の明確な文書化（roof_morph: 0.0-1.0，roof_shift: -1.0 to 1.0）

### 3. 包括的な構造解析
- CalculiXによる高精度FEM解析
- 自重，積載荷重，風荷重を考慮

### 4. 多目的評価
- 構造安全性（安全率）
- 経済性（建設コスト）
- 環境性（CO2排出量）
- 快適性（空間品質）
- 施工性（施工難易度）

### 5. エラーハンドリング
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
- Gmsh NumThreads: 2（安定性向上，0だと全コア使用）
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

4. **FEMモジュールエラー（'Fem::FemAnalysis' is not a document object type）**
   - 親ディレクトリにFem.pyファイルがある場合，モジュール名の競合が発生
   - 解決策：Pythonパスから親ディレクトリを除外し，現在のディレクトリのみを追加
   - test_generate_building.pyで実装済みの修正を参照

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

### 材料選択による自動調整

- **床スラブ厚**: 木材選択時は自動的に厚みを増加（×1.5）
- **柱断面**: 木材選択時は断面を増加（×1.2）
- **壁厚**: 木材選択時は×1.5

### 材料別の特徴比較

| 項目 | コンクリート | 木材 |
|------|------------|------|
| 初期コスト | 20,000円/m³ | 50,000円/m³ |
| CO2排出量 | 410 kg/m³ | -836 kg/m³ |
| ヤング率 | 33,000 MPa | 11,000 MPa |
| 密度 | 2400 kg/m³ | 500 kg/m³ |
| 減衰定数 | 5% | 3% |
| 地震応答増幅 | 1.0倍 | 1.5倍 |
| 耐久性 | 高 | 中 |
| メンテナンス | 低 | 中 |

## テストと検証

### テストコード
- **`test_generate_building.py`** - 基本的な動作確認用テストスクリプト
  - 様々なパラメータでの建物生成と評価をテスト
  - 結果をtest_results.csvに保存
  - FreeCADのCUIモード（freecadcmd）で実行

### テスト実行方法

#### Mac
```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd test_generate_building.py
```

#### Windows
```bash
"C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe" test_generate_building.py
```

#### Linux
```bash
freecadcmd test_generate_building.py
```

**注意**: 上記のパスはお使いのPCの環境に合わせて調整してください．

### 出力データ
`test_results.csv`には以下の情報が記録されます：

• **設計パラメータ（21個）**

| カテゴリ | 内容 |
|---------|------|
| 基本形状 | 建物幅，奥行，各階高さ |
| 構造寸法 | 床・屋根スラブ厚，柱サイズ，壁厚 |
| 追加要素 | 壁傾斜角，窓面積比，屋根形状，バルコニー奥行 |
| 材料選択 | 各部位の材料（0:コンクリート，1:木材） |

• **評価指標（5項目）**

| 評価項目 | 説明 | 単位 |
|---------|------|------|
| 安全率 | FEM解析による構造安全性 | - |
| コスト | 建設費用 | 円/m² |
| CO2排出量 | 環境負荷 | kg-CO2/m² |
| 快適性スコア | 空間品質評価 | 0-10 |
| 施工性スコア | 施工難易度評価 | 0-10 |

• **実行メタデータ**
  - タイムスタンプ: 実行日時
  - 処理時間: 評価に要した時間 [秒]
  - FCStdファイルパス: 生成された3Dモデルファイル

---
*レポート作成日: 2025-07-16*
*最終更新日: 2025-07-31*

## 更新履歴
- 2025-07-31: 地震荷重の実装箇所（1896行目）を明記
- 2025-07-24: コード品質改善（重複if文修正，未使用変数コメント化，パラメータ範囲明確化）
- 2025-07-23: 材料選択機能追加，関数docstring追加，フォールバック処理削除
*更新内容: 関数行番号の更新，docstring改善の記載，削除関数の明記，calculate_roof_efficiency削除の詳細追加，テストコードの移動とトラブルシューティング情報の追加*