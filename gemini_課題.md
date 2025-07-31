# AI建築設計入門：演習課題集

## 🏗️ はじめに

この演習では、PythonとAIを活用した建築設計の自動最適化を実践的に学びます。実際に動くコードを使いながら、AIがどのように「良い建築」を見つけ出すのかを体験しましょう。

### 📚 必要な知識
- Python基礎（変数、関数、辞書の理解）
- FreeCADの基本操作
- 建築設計の基礎知識（推奨）

### 🛠️ 事前準備
1. FreeCAD 1.0.0以上のインストール
2. 必要なPythonライブラリのインストール
   ```bash
   pip install numpy pandas matplotlib tqdm flask flask-socketio
   ```
3. 提供されたコード一式をダウンロード

---

## 📋 課題1：【初級】AIによる建築最適化を体験しよう

### 🎯 学習目標
- PSOアルゴリズムによる最適化プロセスの理解
- 評価指標（安全性、コスト、環境性など）の読み方
- 最適化結果の3次元可視化

### 📝 実習手順

#### Step 1: 最適化の実行とモニタリング
```bash
# ターミナルで実行
python pso_with_monitor.py
```

実行中に観察すること：
- **ターミナル**: 反復回数、最良値の推移
- **Webブラウザ** (`http://localhost:5000`): 
  - 収束曲線の形状
  - 粒子の分布変化
  - パラメータ値の推移

#### Step 2: 最適化結果の記録
実行完了後、以下の形式で表示される最良パラメータをコピー：
```
最良パラメータ:
  Lx: 8.5432
  Ly: 7.2341
  H1: 3.2100
  ...（以下20個のパラメータ）
```

#### Step 3: 最適化された建物の生成

**推奨方法: test_generate_building.pyを使用**

1. `test_generate_building.py`をコピーして`test_optimal_building.py`として保存
2. ファイル内の`test_parameters`リストの最初の要素を、Step 2でメモした最良パラメータに置き換え：

```python
test_parameters = [
    # 最適化で得られたパラメータに置き換え
    {
        'Lx': 8.5432,  # あなたの結果
        'Ly': 7.2341,
        'H1': 3.2100,
        'H2': 2.8500,
        'tf': 250,
        'tr': 180,
        'bc': 400,
        'hc': 400,
        'tw_ext': 200,
        'wall_tilt_angle': -5.2,
        'window_ratio_2f': 0.45,
        'roof_morph': 0.6,
        'roof_shift': 0.1,
        'balcony_depth': 1.5,
        'material_columns': 0,
        'material_floor1': 0,
        'material_floor2': 0,
        'material_roof': 1,
        'material_walls': 0,
        'material_balcony': 0
    }
]
```

3. FreeCADで実行：
```bash
# Mac
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd test_optimal_building.py

# Windows
"C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe" test_optimal_building.py
```

4. 実行後、以下のファイルが生成されます：
   - `test_building_YYYYMMDD_HHMMSS.FCStd` - 3Dモデル
   - `test_results.csv` - 評価結果のログ

#### Step 4: 3Dモデルの確認
1. FreeCADのGUIで生成された`.FCStd`ファイルを開く
2. 以下の視点から建物を観察：
   - 正面図（View → Standard Views → Front）
   - 側面図（View → Standard Views → Right）
   - 鳥瞰図（View → Standard Views → Isometric）
   - 構造詳細（柱、床、屋根の接合部をズーム）

### 📊 提出物
1. **最適化された建物のスクリーンショット**（4視点以上）
2. **生成された評価結果**（`test_results.csv`の該当行）
3. **考察レポート** (A4 1-2ページ、以下の項目を含む)
   - 最適化プロセスの観察結果（収束に要した時間、収束曲線の特徴）
   - 最適化された建物の特徴（寸法、材料、特殊な形状など）
   - なぜAIはこの形状を「最適」と判断したのか？（評価値を基に考察）

---

## 🔧 課題2：【中級】設計思想をAIに教えよう

### 🎯 学習目標
- 多目的最適化における重み付けの影響理解
- 評価関数のカスタマイズ手法
- 設計意図のコード化

### 📝 実習手順

#### Step 1: pso_with_monitor.pyのコピーと編集
1. `pso_with_monitor.py`をコピーして、新しいファイル名で保存：
   - `my_pso_eco.py`（環境配慮型）
   - `my_pso_luxury.py`（高級住宅型）
   - `my_pso_economy.py`（経済性重視型）

2. 各ファイル内の`objective_function_with_constraints`関数内の`weights`辞書を編集：

**環境配慮型設計**
```python
weights = {
    'safety': 10.0,   # 安全性は必須
    'cost': 0.3,      # コストは抑制
    'co2': 5.0,       # CO2を大幅削減 ← ここを増やす
    'comfort': 1.0,   # 快適性も重視
    'construct': 0.2  # 施工性は最低限
}
```

**高級住宅設計**
```python
weights = {
    'safety': 10.0,   # 安全性は必須
    'cost': 0.1,      # コストは問わない ← ここを減らす
    'co2': 0.5,       # 環境性は標準
    'comfort': 5.0,   # 快適性を最重視 ← ここを増やす
    'construct': 3.0  # 施工品質も重要
}
```

**経済性重視設計**
```python
weights = {
    'safety': 10.0,   # 安全性は必須
    'cost': 5.0,      # コストを最重視 ← ここを増やす
    'co2': 0.5,       # 環境性は標準
    'comfort': 0.3,   # 快適性は最低限
    'construct': 2.0  # 施工性で工期短縮
}
```

#### Step 2: 各設計思想で最適化を実行
```bash
# それぞれ実行（反復回数は20-30回で十分）
python my_pso_eco.py
python my_pso_luxury.py
python my_pso_economy.py
```

#### Step 3: 結果の比較分析
1. 各実行で得られた最良パラメータを使って建物モデルを生成（課題1のStep 3と同様）
2. 結果を比較表にまとめる

### 📊 提出物
1. **変更したコード**（weights部分のみでOK）
2. **3つの建物の比較**
   - スクリーンショット（同一視点で撮影）
   - 評価値の比較表

| 評価項目 | デフォルト | 環境配慮型 | 高級住宅 | 経済性重視 |
|---------|-----------|-----------|---------|------------|
| 安全率 | | | | |
| コスト（万円） | | | | |
| CO2排出量（kg） | | | | |
| 快適性スコア | | | | |
| 施工性スコア | | | | |

3. **考察レポート** (A4 1-2ページ)
   - 重み付けの変更が建物形状にどう影響したか？
   - 設計思想は適切に反映されたか？
   - 意外な結果があれば、その理由を考察

---

## 🚀 課題3：【上級】新しい設計要素を追加しよう

### 🎯 学習目標
- システム全体のコード構造理解
- 新規パラメータの追加と統合
- 評価関数の拡張

### 📝 実装課題：階段幅の最適化機能を追加

#### Step 1: パラメータの追加
1. `pso_with_monitor.py`の`bounds`配列に新しいパラメータ範囲を追加：
```python
bounds = np.array([
    # ... 既存のパラメータ ...
    [0, 1],           # material_balcony
    [800, 1500]       # stair_width（新規追加）mm単位
])
```

2. `param_names`リストにも追加：
```python
param_names = [
    # ... 既存のパラメータ名 ...
    'material_balcony',
    'stair_width'  # 新規追加
]
```

#### Step 2: 建物生成関数の修正
`generate_building_fem_analyze.py`の`create_realistic_building_model`関数を修正：

1. 関数の引数に`stair_width`を追加
2. 階段生成部分で、固定値1000mmの代わりに`stair_width`パラメータを使用

#### Step 3: 評価関数の更新
快適性評価に階段幅の影響を追加：
```python
def calculate_comfort_score(fem_results, building_info):
    # ... 既存のコード ...
    
    # 階段幅による快適性の加点
    stair_width = building_info.get('stair_width', 1000)
    if stair_width >= 1200:
        stair_comfort = 1.0  # 広い階段は快適
    elif stair_width >= 1000:
        stair_comfort = 0.5
    else:
        stair_comfort = 0.0  # 狭い階段は不快
    
    # 総合スコアに反映
    comfort_score += stair_comfort * 0.5
```

#### Step 4: 動作確認とテスト
1. 修正したコードで最適化を実行
2. 階段幅が実際に変化しているか確認
3. 評価値への影響を分析

### 📊 提出物
1. **修正したコード**（diff形式または変更箇所のハイライト）
2. **実装説明書**（A4 1-2ページ）
   - どの部分をどう修正したか
   - 設計意図（なぜ階段幅が重要か）
   - 実装で工夫した点
3. **動作確認結果**
   - 階段幅が異なる建物のスクリーンショット
   - パラメータと評価値の関係を示すグラフ
4. **考察レポート**
   - 実装の難しかった点と解決方法
   - 今後の改善案

---

## 💡 ヒントとサポート

### よくあるエラーと対処法

1. **ImportError: No module named 'XXX'**
   ```bash
   pip install XXX  # 不足しているモジュールをインストール
   ```

2. **FreeCADが起動しない**
   - パスが正しいか確認（`which freecadcmd`で確認）
   - 環境変数の設定を確認

3. **メモリ不足エラー**
   - 粒子数を減らす（n_particles=10など）
   - 反復回数を減らす（max_iter=20など）

### デバッグのコツ
```python
# デバッグプリントを追加
print(f"Debug: 現在のパラメータ = {params}")
print(f"Debug: 評価結果 = {results}")

# 中間結果を保存
import json
with open('debug_params.json', 'w') as f:
    json.dump(params, f, indent=2)
```

### 質問・相談先
- 授業内での質問を推奨
- コードのエラーメッセージは必ず全文をコピーして質問

---

## 📈 評価基準

### 共通評価項目
- コードの実行可能性（エラーなく動作するか）
- レポートの論理性と考察の深さ
- 提出物の完成度（指定された形式を守っているか）

### 課題別配点
- **初級**：実行結果の正確性(40%) + 考察(40%) + レポート(20%)
- **中級**：実装の正確性(30%) + 比較分析(40%) + 考察(30%)
- **上級**：実装の完成度(40%) + 創造性(30%) + ドキュメント(30%)

---

*最終更新: 2024年7月*