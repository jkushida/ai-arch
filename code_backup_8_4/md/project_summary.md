# FreeCAD建築FEM解析プロジェクト - 現在の実装状況

最終更新: 2025-07-07

## プロジェクト概要

FreeCADを使用した2階建てピロティ構造建築物の自動生成とFEM解析システム．遺伝的アルゴリズム（差分進化）による最適化機能を含む．

## 主要ファイル構成

### 1. building_fem_analysis_piloti_with_stairs_v8.py
**メインの建物生成・FEM解析モジュール**

#### 主要パラメータ（BuildingParametersクラス）
- `Lx`: 建物幅 [m]
- `Ly`: 建物奥行き [m]
- `H1`: 1階高 [m]
- `H2`: 2階高 [m]
- `tf`: 床スラブ厚 [mm]
- `tr`: 屋根スラブ厚 [mm]
- `bc`: 柱幅 [mm]
- `hc`: 柱厚 [mm]
- `tw_ext`: 外壁厚 [mm]
- `balcony_depth`: バルコニー奥行き [m] (0.0-3.0) **[NEW]**

#### 追加パラメータ
- `wall_tilt_angle`: 壁の傾斜角度 [度] (-40.0 to 40.0)
- `window_ratio_2f`: 2階窓面積率 (0.0-0.8)
- `roof_morph`: かまぼこ屋根の形態 (0.0-1.0)
- `roof_shift`: 屋根の左右シフト (-0.7-0.7)

#### 主要機能
- **create_balcony()**: 西側壁面にバルコニーを生成
- **create_realistic_building_model()**: 建物3Dモデル生成
- **evaluate_building()**: FEM解析と各種評価を実行
- **evaluate_building_from_params()**: パラメータ辞書からの評価実行

#### 最新の変更点
1. **tw_int（間仕切り壁厚）パラメータを削除** - 未使用のため
2. **バルコニー機能を追加**
   - 西側（階段側）の壁面に設置
   - 片持ち梁構造として実装
   - 手すり付き（高さ1100mm）
3. **バルコニーへの入り口を追加**
   - 西側壁に幅900mm×高さ2100mmのドア開口部
   - バルコニーの中央に配置
4. **バルコニー活荷重を追加**
   - 建築基準法準拠：180kg/m²（1800Pa）
   - FEM解析に自動的に含まれる

### 2. simple_random_batch.py
**ランダムサンプリングによるバッチ解析**

#### 更新内容
- tw_intパラメータを削除
- balcony_depthパラメータを追加（0.0-3.0m）
- CSVヘッダーを更新

#### 生成パラメータ範囲
```python
"Lx": round(rng.uniform(8.0, 20.0), 2),      # 8-20m
"Ly": round(rng.uniform(8.0, 20.0), 2),      # 8-20m
"H1": round(rng.uniform(2.5, 4.5), 2),       # 2.5-4.5m
"H2": round(rng.uniform(2.5, 4.0), 2),       # 2.5-4.0m
"tf": rng.randint(120, 500),                 # 120-500mm
"tr": rng.randint(100, 400),                 # 100-400mm
"bc": rng.randint(200, 800),                 # 200-800mm
"hc": rng.randint(200, 800),                 # 200-800mm
"tw_ext": rng.randint(100, 350),             # 100-350mm
"wall_tilt_angle": round(rng.uniform(-40.0, 40.0), 1),
"window_ratio_2f": round(rng.uniform(0.1, 0.9), 2),
"roof_morph": round(rng.uniform(0.0, 1.0), 2),
"roof_shift": round(rng.uniform(-0.7, 0.7), 2),
"balcony_depth": round(rng.uniform(0.0, 3.0), 1)  # NEW
```

### 3. DE.py
**差分進化アルゴリズムによる最適化**

#### 更新内容
- tw_intパラメータを削除
- balcony_depthパラメータを追加
- 設計変数の次元が14次元に更新

#### 最適化範囲
```python
# [Lx, Ly, H1, H2, tf, tr, bc, hc, tw_ext, wall_tilt, window_ratio, roof_morph, roof_shift, balcony_depth]
bound_low = [5.0, 5.0, 2.5, 2.5, 120, 100, 200, 200, 100, -40.0, 0.1, 0.0, -0.7, 0.0]
bound_up = [20.0, 20.0, 4.5, 4.0, 500, 400, 800, 800, 350, 40.0, 0.9, 1.0, 0.7, 3.0]
```

### 4. create_html_gallery.py
**解析結果のHTMLギャラリー生成**

#### 更新内容
- tw_int表示を削除
- balcony_depth表示を追加

### 5. fcstd_to_png.py / batch_fcstd_to_png.py
**FCStdファイルをPNG画像に変換**

#### 更新内容
- Floor2オブジェクトへの参照を削除（存在しないため）
- 色設定を修正

## 評価項目

### 1. 安全性評価
- 安全率（FEM解析結果に基づく）
- 最大変位
- 最大応力
- バルコニーの片持ち梁効果も考慮

### 2. 経済性評価
- 建設コスト（円/m²）
- 材料費
- 総工費

### 3. 環境性評価
- CO2排出量（kg-CO2/m²）
- 材料の環境負荷

### 4. 快適性評価
- 空間の広がり
- 採光・眺望
- ピロティによる開放感
- プライバシー
- **バルコニーボーナス（NEW）**
  - 0.5-1.5ポイントの加点

### 5. 施工性評価
- 基本スコア：10点
- 各種ペナルティ
  - カンチレバー：-2.0
  - 階段：-1.5
  - 傾斜壁：角度/10
  - かまぼこ屋根：-0.5～-1.5
  - **バルコニー（NEW）**：-0.5～-1.5

## バルコニー機能の詳細

### 設置位置
- 西側壁面（階段に最も近い壁）
- 2階床レベル（H1の高さ）

### 構造
- 片持ち梁構造
- 床厚：150mm
- 手すり高：1100mm
- 手すり厚：100mm

### アクセス
- 西側壁に幅900mm×高さ2100mmのドア開口部
- 床から100mm上に配置

### FEM解析での考慮
- 構造体として建物本体に統合
- 活荷重：1800Pa（建築基準法準拠）
- 奥行きが長いほど安全率が低下

## 使用方法

### 単体テスト
```python
python building_fem_analysis_piloti_with_stairs_v8.py
```

### ランダムバッチ解析
```python
python simple_random_batch.py
```

### 最適化実行
```python
python DE.py
```

### HTMLギャラリー生成
```python
python create_html_gallery.py
```

## 注意事項

1. **FreeCAD環境が必要**
2. **CalculiXソルバーが必要**（FEM解析用）
3. **Blenderが必要**（PNG生成用）
4. **バルコニーの奥行きと安全性**
   - 1.5m以下：比較的安全
   - 2.0m以上：補強が必要
   - 3.0m：特別な構造設計が必要