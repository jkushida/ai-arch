# 建築AI設計システム 簡素化演習

## はじめに - 5分でできる簡単スタート

### ステップ1: ターミナルを開く
1. Macの場合: Spotlight検索（⌘+スペース）で「ターミナル」と入力
2. アプリケーション → ユーティリティ → ターミナル

### ステップ2: 作業フォルダに移動
```bash
cd /Users/kushida2/Library/CloudStorage/GoogleDrive-kushida2008@gmail.com/マイドライブ/2025code/AI_arch
```

### ステップ3: テストスクリプトを実行（基準値で実行）
```bash
# まず現在の設定で実行してみる
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/test_generate_building.py
```

実行すると、1つの建物モデルが生成され、FEM解析結果が表示されます。
結果は`test_results.csv`に保存されます。

---

## 演習1: パラメータ変更による評価値の変化を観察（初心者向け）

### 目的
`test_generate_building.py`のパラメータを変更して、安全率や他の評価指標がどう変化するか理解する。

### 現在のパラメータ（33-61行目）
```python
test_params = {
    # 建物寸法
    'Lx': 6.0,           # 建物幅 [m]
    'Ly': 6.0,           # 建物奥行 [m]
    'H1': 3.0,           # 1階高さ [m]
    'H2': 3.0,           # 2階高さ [m]
    
    # 構造部材寸法
    'tf': 200,           # 床スラブ厚 [mm]
    'tr': 150,           # 屋根スラブ厚 [mm]
    'bc': 300,           # 柱幅 [mm]
    'hc': 300,           # 柱高さ [mm]
    'tw_ext': 150,       # 外壁厚 [mm]
    
    # 材料パラメータ（0:コンクリート, 1:木材）
    'material_columns': 0,      # 柱材料
    'material_walls': 1,        # 外壁材料（現在は木材）
    'material_roof': 0,         # 屋根材料
}
```

### 観察ポイント

#### 1. 安全率を上げるには？
以下のパラメータを変更すると安全率が向上します：
- **柱を太くする** (bc, hc を増やす) → 構造強度UP
- **スラブを厚くする** (tf, tr を増やす) → 剛性UP
- **建物を小さくする** (Lx, Ly を減らす) → 荷重減少
- **階高を低くする** (H1, H2 を減らす) → 重心低下

#### 2. 安全率を下げる要因
- **柱を細くする** → 構造強度DOWN
- **スラブを薄くする** → 剛性DOWN
- **建物を大きくする** → 荷重増加
- **材料を木材に変更** → 許容応力が低い



### 演習課題

#### 課題1: 基本的な観察（15分）

**手順：**
1. ファイルを開く
   ```bash
   open -e code/test_generate_building.py  # テキストエディタで開く
   ```

2. 現在のパラメータで実行
   ```bash
   /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/test_generate_building.py
   ```

3. 結果を記録（基準値）
   - 安全率: _____
   - コスト: _____ 円/m²
   - CO2排出: _____ kg-CO2/m²
   - 快適性: _____/10
   - 施工性: _____/10

4. CSVファイルを確認
   ```bash
   cat test_results.csv  # CSVファイルの内容を表示
   ```

#### 課題2: パラメータを変更して実験（30分）

**実験1: 柱を太くする**

1. `test_generate_building.py`の43-44行目を編集
   ```python
   # 元の値
   'bc': 300,           # 柱幅 [mm]
   'hc': 300,           # 柱高さ [mm]
   
   # 変更後
   'bc': 500,           # 柱幅 [mm] ← 500mmに変更
   'hc': 500,           # 柱高さ [mm] ← 500mmに変更
   ```

2. 保存して再実行
   ```bash
   /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/test_generate_building.py
   ```

3. 結果を記録
   - 安全率: _____ （基準値より上がった？）
   - コスト: _____ 円/m² （増加率: ___%）
   - 施工性: _____ （下がった？）

**実験2: 建物を大きくする**

1. 35-36行目を編集
   ```python
   # 変更後
   'Lx': 10.0,          # 建物幅 [m] ← 10mに変更
   'Ly': 10.0,          # 建物奥行 [m] ← 10mに変更
   ```

2. 実行して結果を記録
   - 安全率: _____ （下がった？）
   - コスト: _____ 円/m²

**実験3: 材料を木材に変更**

1. 49行目（屋根材料）を編集
   ```python
   # 変更後（屋根を木材に）
   'material_roof': 1,         # 屋根材料 ← 1(木材)に変更
   # 注: material_walls は既に1(木材)になっている
   ```

2. 結果を記録
   - 安全率: _____
   - コスト: _____ 円/m² （減った？）
   - CO2: _____ kg-CO2/m² （減った？）

#### 課題3: 最適なバランスを探す（30分）

**目標：** 以下の条件をすべて満たす設計を見つける
- ✅ 安全率 ≥ 1.5
- ✅ コスト ≤ 350,000 円/m²
- ✅ 快適性 ≥ 5.0

**ヒント：**
```python
# バランスを探すためのパラメータ調整例
test_params = {
    'Lx': 8.0,           # 建物幅を少し大きく
    'Ly': 8.0,           # 建物奥行を少し大きく  
    'bc': 400,           # 柱を少し太く
    'hc': 400,           # 柱を少し太く
    'tf': 250,           # 床スラブを少し厚く
    
    # 材料の組み合わせも考慮
    'material_roof': 1,      # 屋根を木材に（軽量化）
    'material_walls': 1,     # 壁を木材に（コスト削減）
    'material_columns': 0,   # 柱はコンクリート（強度確保）
    # ...
}
```

**調整のコツ：**
- 安全率が低い → 柱を太く(bc,hc↑) or スラブを厚く(tf,tr↑)
- コストが高い → 材料を木材に(material_*=1) or 建物を小さく(Lx,Ly↓)
- 快適性が低い → 窓を大きく(window_ratio_2f↑) or 階高を高く(H1,H2↑)

**成功した設計を記録：**
```
成功パラメータ：
- 建物サイズ: Lx=___m, Ly=___m
- 柱サイズ: bc=___mm, hc=___mm
- スラブ厚: tf=___mm, tr=___mm
- 材料: 柱=___, 屋根=___, 壁=___

結果：
- 安全率: _____ ✅
- コスト: _____円/m² ✅
- 快適性: _____/10 ✅
```

---

---

## 演習2: PSO最適化の準備（中級者向け）

### PSO（粒子群最適化）とは？
- 鳥の群れの動きを模倣した最適化アルゴリズム
- 複数の「粒子」が解空間を探索
- 各粒子は自分の最良解と群れ全体の最良解を参考に移動

### PSO実行前の確認事項

#### 1. 最適化の目的を明確にする
```python
# 例: 安全性重視の最適化
weights = {
    "safety": 0.5,      # 安全性を最重視
    "economic": 0.3,    # コストも考慮
    "environmental": 0.2 # 環境負荷も考慮
}
```

#### 2. パラメータ範囲の確認
```python
# sampling_code/random_building_sampler.py の PARAM_RANGES を確認
PARAM_RANGES = {
    "Lx": (8.0, 12.0),        # 建物幅
    "Ly": (8.0, 12.0),        # 建物奥行
    "H1": (2.6, 3.5),         # 1階高さ
    "H2": (2.6, 3.5),         # 2階高さ
    "tf": (350, 600),         # 床スラブ厚
    "tr": (350, 600),         # 屋根スラブ厚
    "bc": (400, 1000),        # 柱幅
    "hc": (400, 1000),        # 柱高さ
    "tw_ext": (300, 500),     # 外壁厚
    # ... その他のパラメータ
}
```

#### 3. 制約条件の理解
- 建築基準法の遵守（階高2.6m以上）
- 構造的妥当性（安全率1.0以上、推奨2.0以上）
- 現実的な施工可能性

### PSO実行コマンド
```bash
# PSO最適化の実行
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/pso_algorithm.py

# 実行中のモニタリング（別ターミナル）
python3 code/monitor_pso_mac.py
```

### 演習課題

#### 課題4: PSO設定の調整（20分）

**手順：**
1. 設定ファイルを開く
   ```bash
   open -e code/pso_config.py
   ```

2. 以下の値を変更（テスト用に小さく）
   ```python
   # 元の値
   N_PARTICLES = 10  # → 5に変更
   MAX_ITER = 10     # → 5に変更
   ```

3. 重みを調整（安全性重視の例）
   ```python
   # 重み設定（合計1.0になるように）
   w_safety = 0.7        # 安全性70%
   w_economic = 0.2      # 経済性20%
   w_environmental = 0.1 # 環境10%
   ```

4. 保存して実行
   ```bash
   /Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/pso_algorithm.py
   ```

5. 別ターミナルでモニタリング（オプション）
   ```bash
   python3 code/monitor_pso_mac.py
   ```
   ブラウザで http://localhost:5001 を開く

#### 課題5: 結果の分析（30分）

**手順：**
1. 収束グラフを開く
   ```bash
   open pso_output/images/convergence_*.png
   ```
   観察ポイント：
   - グラフは下がっている？（コスト最小化）
   - 何世代目で安定した？

2. CSVファイルで最適解を確認
   ```bash
   # 最後の5行を表示
   tail -5 pso_output/csv/pso_history.csv
   ```
   確認項目：
   - best_fitness（最良評価値）
   - 各パラメータの最終値

3. 最適解の3Dモデルを確認（FreeCADがある場合）
   ```bash
   # FreeCADで開く
   open -a FreeCAD pso_output/fcstd/best_particle_final.FCStd
   ```

4. 分析結果をまとめる
   ```
   最適化結果：
   - 初期値の評価: ___
   - 最終値の評価: ___
   - 改善率: ___%
   - 特徴的なパラメータ: ___
   ```

---

---

## クイックリファレンス

### よく使うコマンド一覧
```bash
# 作業ディレクトリに移動
cd /Users/kushida2/Library/CloudStorage/GoogleDrive-kushida2008@gmail.com/マイドライブ/2025code/AI_arch

# テストスクリプト実行
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/test_generate_building.py

# ファイル編集
open -e code/test_generate_building.py

# CSV結果を確認
cat test_results.csv

# CSVをExcelで開く
open test_results.csv

# PSO最適化実行（上級者向け）
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/pso_algorithm.py

# モニタリング（上級者向け）
python3 code/monitor_pso_mac.py
```

### トラブルシューティング

**Q: 「モジュールが見つかりません」エラー**
A: 作業ディレクトリが正しいか確認
```bash
pwd  # 現在地を確認
```

**Q: 実行が遅い**
A: パラメータを減らしてテスト
- N_PARTICLES = 3
- MAX_ITER = 3

**Q: 結果が期待と違う**
A: 重み設定を確認（合計1.0になっているか）

---

## まとめ

### 今日学んだことチェックリスト

□ `test_generate_building.py`を実行できた
□ パラメータを変更して再実行できた
□ 柱を太くすると安全率が上がることを確認した
□ 建物を大きくすると安全率が下がることを確認した
□ 木材を使うとコストとCO2が下がることを確認した
□ 目標を満たすパラメータを見つけた
□ CSVファイルに結果が保存されることを確認した

### 次のステップ
1. パラメータをもっと細かく調整
2. 独自の評価関数を作成
3. 実際の建築制約を追加

### 参考資料
- [PSO アルゴリズムの詳細](./pso_summary.md)
- [建物生成システムの仕組み](./generate_building_fem_analyze_report.md)
- [ランダムサンプリングガイド](./random_sampling_guide.md)