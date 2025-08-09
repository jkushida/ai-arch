# AI建築設計最適化システム：実践課題集

## 🏗️ はじめに

このシステムの最新バージョンに対応した課題集です。FreeCADとCalculiXを使用した建築設計最適化を実践的に学びます。

### 📚 システムの特徴
- **21個の設計パラメータ**（形状15個、材料6個）による詳細な建物定義
- **5つの評価指標**（安全性、経済性、環境性、快適性、施工性）による多角的評価
- **PSO（粒子群最適化）**による自動設計探索
- **リアルタイム監視**機能による最適化過程の可視化

### 🛠️ 事前準備
1. **FreeCAD 0.21以上**のインストール
2. **Python 3.8以上**環境
3. 必要なライブラリのインストール：
   ```bash
   pip install numpy pandas matplotlib flask
   ```
4. プロジェクトコードのダウンロード

---

## 📋 課題1：【初級】単一建物の評価と分析

### 🎯 学習目標
- `test_generate_building.py`を使った建物生成と評価の基本を理解する
- パラメータが建物設計に与える影響を観察する
- 5つの評価指標の意味と相互関係を理解する

### 📝 実習手順

#### Step 1: デフォルト建物の評価

**1. test_generate_building.pyの実行：**
```bash
# Mac
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/test_generate_building.py

# Windows
"C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" code\test_generate_building.py
```

**2. 実行結果の観察**
- ターミナルに表示される評価結果を確認
- 生成される`test_building_[timestamp].FCStd`ファイルの場所を記録
- CSVファイル`test_results.csv`が作成されることを確認

#### Step 2: パラメータの理解と変更

**1. test_generate_building.pyをエディタで開く**

**2. デフォルトパラメータを確認（33-63行目）：**
```python
# デフォルトのテスト用パラメータ
default_params = {
    # 建物寸法
    'Lx': 8.0,           # 建物幅 [m]
    'Ly': 6.0,           # 建物奥行 [m]
    'H1': 3.0,           # 1階高さ [m]
    'H2': 3.0,           # 2階高さ [m]
    
    # 構造部材寸法
    'tf': 200,           # 床スラブ厚 [mm]
    'tr': 150,           # 屋根スラブ厚 [mm]
    'bc': 300,           # 柱幅 [mm]
    'hc': 300,           # 柱高さ [mm]
    'tw_ext': 150,       # 外壁厚 [mm]
    
    # その他の設計パラメータ
    'wall_tilt_angle': -25,      # 壁傾斜角
    'window_ratio_2f': 0.7,      # 2階窓面積比
    'roof_morph': 0.9,           # 屋根形態
    'roof_shift': 0.7,           # 屋根シフト
    'balcony_depth': 1.8         # バルコニー奥行
}

# 材料パラメータ（0:コンクリート, 1:木材）
material_params = {
    'material_columns': 0,      # 柱材料
    'material_floor1': 0,       # 1階床材料
    'material_floor2': 0,       # 2階床材料
    'material_roof': 0,         # 屋根材料
    'material_walls': 1,        # 外壁材料（木材）
    'material_balcony': 0       # バルコニー材料
}
```

#### Step 3: 3パターンの建物を作成して比較

**パターンA: コンパクト住宅（経済性重視）**
```python
default_params = {
    'Lx': 6.0,           # 小さい幅
    'Ly': 5.0,           # 小さい奥行
    'H1': 2.8,           # 低い階高
    'H2': 2.5,           
    'tf': 150,           # 薄い床
    'tr': 120,           
    'bc': 250,           # 細い柱
    'hc': 250,
    'tw_ext': 120,       # 薄い壁
    'wall_tilt_angle': 0,       # 垂直壁（シンプル）
    'window_ratio_2f': 0.3,     # 小さい窓
    'roof_morph': 0.0,           # フラット屋根
    'roof_shift': 0.0,
    'balcony_depth': 0.0         # バルコニーなし
}
```

**パターンB: 標準住宅（バランス型）**
```python
default_params = {
    'Lx': 8.0,
    'Ly': 7.0,
    'H1': 3.0,
    'H2': 2.8,
    'tf': 200,
    'tr': 180,
    'bc': 300,
    'hc': 300,
    'tw_ext': 180,
    'wall_tilt_angle': -5,
    'window_ratio_2f': 0.5,
    'roof_morph': 0.5,
    'roof_shift': 0.0,
    'balcony_depth': 1.2
}
```

**パターンC: 高級住宅（快適性重視）**
```python
default_params = {
    'Lx': 12.0,          # 広い幅
    'Ly': 10.0,          # 広い奥行
    'H1': 3.5,           # 高い階高
    'H2': 3.2,
    'tf': 250,           # 厚い床（遮音性）
    'tr': 200,
    'bc': 400,           # 太い柱（安定性）
    'hc': 400,
    'tw_ext': 200,
    'wall_tilt_angle': -10,      # 傾斜壁（デザイン性）
    'window_ratio_2f': 0.7,      # 大きい窓（採光）
    'roof_morph': 0.8,            # かまぼこ屋根
    'roof_shift': 0.2,            # 非対称デザイン
    'balcony_depth': 2.0          # 広いバルコニー
}
```

**実行手順：**
1. 各パターンのパラメータに変更してファイルを保存
2. ファイル名を変更（`test_compact.py`, `test_standard.py`, `test_luxury.py`）
3. それぞれ実行してCSVに結果を記録

#### Step 4: 結果の分析と3Dモデルの観察

**1. CSVファイルから比較表を作成**

`test_results.csv`から3つのパターンの結果を抽出して比較：

| 項目 | コンパクト住宅 | 標準住宅 | 高級住宅 |
|---|---|---|---|
| 床面積 [m²] | | | |
| 建設コスト [円/m²] | | | |
| 総工費 [円] | | | |
| CO2排出量 [kg-CO2/m²] | | | |
| 安全率 | | | |
| 快適性スコア | | | |
| 施工性スコア | | | |

**2. FreeCADで3Dモデルを比較**

1. 各パターンの`.FCStd`ファイルをFreeCADで開く
2. 同じ視点（Isometric View）でスクリーンショットを撮影
3. 特徴的な違いを観察：
   - 建物の大きさと比率
   - 屋根の形状
   - 壁の傾斜
   - バルコニーの有無

### 📊 提出課題1

#### a) パラメータ変更の記録
3つのパターンで変更したパラメータとその理由を表にまとめる：

| パラメータ | コンパクト住宅 | 標準住宅 | 高級住宅 | 変更の狙い |
|---|---|---|---|---|
| Lx×Ly [m] | 6.0×5.0 | 8.0×7.0 | 12.0×10.0 | 床面積によるコスト/快適性の調整 |
| H1, H2 [m] | 2.8, 2.5 | 3.0, 2.8 | 3.5, 3.2 | 階高による空間の質の変化 |
| 柱サイズ [mm] | 250×250 | 300×300 | 400×400 | 構造安定性と材料コストのバランス |
| 壁傾斜角 [度] | 0 | -5 | -10 | デザイン性と施工難易度のトレードオフ |
| （他のパラメータも同様に記載） | | | | |

#### b) 評価結果の比較分析
CSVファイルから抽出したデータを基に、3パターンの性能を比較：

| 評価項目 | コンパクト住宅 | 標準住宅 | 高級住宅 | 最良値 |
|---|:---:|:---:|:---:|:---:|
| **経済性** |
| 建設コスト [円/m²] | | | | ◎ |
| 総工費 [万円] | | | | ◎ |
| **環境性** |
| CO2排出量 [kg-CO2/m²] | | | | ◎ |
| **安全性** |
| 構造安全率 | | | | ◎ |
| 最大変位 [mm] | | | | ◎ |
| **快適性** |
| 快適性スコア [/10] | | | | ◎ |
| 床面積 [m²] | | | | |
| **施工性** |
| 施工性スコア [/10] | | | | ◎ |

#### c) 3Dモデルの視覚的比較
- 3つの建物の同一視点スクリーンショット（正面、側面、鳥瞰図）
- 各建物の特徴的な部分のクローズアップ
- 材料の違いが分かる表示設定での比較

#### d) 考察とレポート（800字以上）
以下の観点から分析：

1. **パラメータと評価指標の関係**
   - どのパラメータが最もコストに影響したか？
   - 快適性スコアを上げる要因は何か？
   - 安全性と経済性のトレードオフはどこにあるか？

2. **設計思想の違い**
   - 各パターンの長所と短所
   - 想定される居住者層
   - 実際の建築での実現可能性

3. **最適なバランスの探求**
   - 3つのパターンから学んだこと
   - 理想的な第4のパターンの提案
   - AIによる最適化の必要性

4. **システムの評価**
   - 評価指標の妥当性
   - パラメータの十分性
   - 改善提案

---

## 🔧 課題2：【中級】設計思想をカスタマイズしよう

### 🎯 学習目標
- `pso_config.py` を編集して目的関数をカスタマイズ
- 異なる設計思想による結果の違いを理解
- 多目的最適化のトレードオフを体験

### 📝 実習手順

#### Step 1: pso_config.pyのバックアップ
```bash
cp code/pso_config.py code/pso_config_original.py
```

#### Step 2: 3つの設計思想を実装

**A. 環境配慮型設計**
`pso_config.py` の `calculate_fitness` 関数を編集：
```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    """環境性能を最重視した評価関数"""
    # CO2排出量を主目的とする
    fitness = co2 * 2.0  # CO2を2倍重視
    
    # コストも考慮（エコ建築は高価でもOK）
    fitness += cost * 0.1
    
    # 安全性制約（必須）
    SAFETY_THRESHOLD = 2.0
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 100000
    
    # 快適性ボーナス（エコで快適なら最高）
    if comfort > 7.0:
        fitness -= 1000  # ボーナス
    
    return fitness
```

**B. 高級住宅設計**
```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    """快適性と品質を最重視した評価関数"""
    # 快適性を最大化（負の値なので符号反転）
    fitness = -comfort * 10000
    
    # 施工品質も重要
    fitness += -constructability * 5000
    
    # コストは問わない（むしろ高級感）
    # fitness += cost * 0  # コスト無視
    
    # 安全性は絶対条件
    SAFETY_THRESHOLD = 2.5  # より高い安全基準
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 200000
    
    return fitness
```

**C. 経済性重視設計**
```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    """コストパフォーマンス最大化"""
    # コストを最小化
    fitness = cost
    
    # 施工性で工期短縮（コスト削減）
    fitness += (10 - constructability) * 5000
    
    # 最低限の安全性確保
    SAFETY_THRESHOLD = 2.0
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 100000
    
    # 快適性は最低限（コスト優先）
    if comfort < 4.0:
        fitness += 10000  # ペナルティ
    
    return fitness
```

#### Step 3: 各設計思想で最適化実行

```bash
# 環境配慮型
cp code/pso_config_eco.py code/pso_config.py
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/pso_algorithm.py
mv pso_output pso_output_eco

# 高級住宅
cp code/pso_config_luxury.py code/pso_config.py
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/pso_algorithm.py
mv pso_output pso_output_luxury

# 経済性重視
cp code/pso_config_economy.py code/pso_config.py
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/pso_algorithm.py
mv pso_output pso_output_economy
```

### 📊 提出課題2

#### a) 実装レポート
- 各設計思想の詳細説明
- 評価関数の設計理由
- 重み付けの根拠

#### b) 比較分析表
| 項目 | 環境配慮型 | 高級住宅 | 経済性重視 |
|---|---|---|---|
| **主要パラメータ** |
| 建物サイズ (m²) | | | |
| 主要材料 | | | |
| 特徴的な形状 | | | |
| **評価結果** |
| 安全率 | | | |
| コスト (円/m²) | | | |
| CO2 (kg/m²) | | | |
| 快適性 (/10) | | | |
| 施工性 (/10) | | | |
| **特徴** |
| 長所 | | | |
| 短所 | | | |

#### c) 3Dモデル比較
- 各設計の3Dモデルを同一視点でスクリーンショット
- 形状の違いを視覚的に比較
- 特徴的な差異を矢印等で注釈

#### d) 考察（800字以上）
- 設計思想が形状に与えた影響
- トレードオフの分析
- 実用性の評価
- 改善提案

---

## 🚀 課題3：【上級】システムを拡張しよう

### 🎯 学習目標
- 既存システムへの新機能追加
- コードの統合とテスト
- ドキュメント作成

### 📝 実装課題（1つ選択）

#### Option A: 新評価指標「耐震性能」の追加

**実装内容：**
1. `generate_building_fem_analyze.py` に耐震性評価関数を追加
2. 地震応答スペクトル解析の簡易実装
3. 層間変形角の詳細評価
4. 評価結果の統合

```python
def calculate_seismic_performance(fem_results, building_info):
    """耐震性能の評価"""
    # 層間変形角の計算
    story_drift = calculate_story_drift(fem_results)
    
    # 固有周期の推定
    natural_period = estimate_natural_period(building_info)
    
    # 耐震性能スコア（0-10）
    score = evaluate_seismic_score(story_drift, natural_period)
    
    return {
        'seismic_score': score,
        'story_drift': story_drift,
        'natural_period': natural_period
    }
```

#### Option B: 変数固定機能のGUI化

**実装内容：**
1. Flaskベースの設定画面作成
2. 変数範囲の動的設定機能
3. プリセット管理システム
4. 実行管理インターフェース

```python
# web_config.py
from flask import Flask, render_template, request
import json

app = Flask(__name__)

@app.route('/config')
def config_page():
    """設定画面の表示"""
    return render_template('config.html', 
                         variables=load_variables())

@app.route('/save_config', methods=['POST'])
def save_config():
    """設定の保存"""
    config = request.json
    save_to_pso_config(config)
    return {'status': 'success'}
```

#### Option C: 機械学習による高速化

**実装内容：**
1. サロゲートモデルの構築
2. FEM解析結果の学習
3. 高速評価モードの実装
4. 精度検証システム

```python
# ml_surrogate.py
from sklearn.ensemble import RandomForestRegressor
import joblib

class FEMSurrogate:
    """FEM解析の代替モデル"""
    
    def __init__(self):
        self.model = RandomForestRegressor(n_estimators=100)
        
    def train(self, X_params, y_results):
        """過去のFEM結果から学習"""
        self.model.fit(X_params, y_results)
        
    def predict(self, params):
        """高速予測"""
        return self.model.predict([params])[0]
        
    def save(self, path):
        """モデルの保存"""
        joblib.dump(self.model, path)
```

### 📊 提出課題3

#### a) 技術仕様書（3-5ページ）
- システムアーキテクチャ図
- データフロー図
- API仕様
- テスト計画

#### b) 実装コード
- GitHubリポジトリ（またはZIP）
- README.mdによる説明
- サンプルデータ
- テストコード

#### c) 動作デモ
- 実行動画（3-5分）
- ビフォー/アフター比較
- パフォーマンス測定結果

#### d) 技術レポート（5-8ページ）
- 実装の動機
- 技術的課題と解決法
- 性能評価
- 将来の拡張案

---

## 📈 評価基準

### 共通評価項目
- **技術的正確性** (30%)：コードが正しく動作するか
- **理解度** (30%)：システムの仕組みを理解しているか
- **分析力** (25%)：結果を適切に分析できているか
- **表現力** (15%)：レポートの分かりやすさ

### 課題別配点
- **初級**：実行40点、分析30点、考察30点
- **中級**：実装30点、比較40点、考察30点
- **上級**：設計20点、実装50点、検証30点

---

## 💡 トラブルシューティング

### よくあるエラーと対処法

**1. ImportError**
```bash
# モジュールパスの確認
export PYTHONPATH=$PYTHONPATH:/path/to/AI_arch/code
```

**2. FEM解析タイムアウト**
```python
# pso_algorithm.py のタイムアウト値を増やす
EVALUATION_TIMEOUT = 300  # 5分に延長
```

**3. メモリ不足**
```python
# pso_config.py で粒子数を減らす
N_PARTICLES = 5  # 10から5に削減
```

**4. 収束しない**
```python
# 慣性重みを調整
W_START = 0.9  # 初期値を大きく
W_END = 0.4    # 終了値を小さく
```

### デバッグのコツ
```python
# 詳細ログの有効化
VERBOSE_OUTPUT = True  # generate_building_fem_analyze.py

# 中間結果の保存
import pickle
with open('debug_state.pkl', 'wb') as f:
    pickle.dump(particles, f)
```

---

## 🔗 参考資料

### プロジェクトドキュメント
- [FEM解析システム詳細](https://jkushida.github.io/ai-arch/docs/generate_building_fem_analyze_report.html)
- [PSO使用ガイド](https://jkushida.github.io/ai-arch/docs/PSO_usage.html)
- [GitHubリポジトリ](https://github.com/jkushida/ai-arch)

### 外部リソース
- [FreeCAD Python API](https://wiki.freecad.org/Python_scripting_tutorial)
- [PSO理論解説](https://en.wikipedia.org/wiki/Particle_swarm_optimization)
- [建築基準法](https://elaws.e-gov.go.jp/document?lawid=325AC0000000201)

---

*最終更新: 2025年8月*