# AI建築設計システム 学生課題集

## 概要
このドキュメントでは，AI建築設計システムを使用した様々な課題を提示します．基礎から応用まで，段階的に学習できるように構成されています．

## 課題の進め方
1. PSO.pyの`calculate_fitness`関数を課題に応じて書き換える
2. FreeCADコマンドラインで実行
   - **Mac**: `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd PSO.py`
   - **Windows**: `"C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe" PSO.py`
   - **Linux**: `freecadcmd PSO.py` または `/usr/bin/freecadcmd PSO.py`
   - **注意**: 上記のパスはお使いのPCの環境に合わせて調整してください
3. 結果を分析し，レポートにまとめる

---

## 1. 基礎課題（初級）

### 課題1-1: 環境配慮型住宅の設計
**目的**: CO2排出量を最小化しながら，快適性も確保する住宅を設計する

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    SAFETY_THRESHOLD = 2.0
    COMFORT_THRESHOLD = 6.0  # 快適性の最低基準
    PENALTY_COEFFICIENT = 100000
    
    fitness = co2  # CO2最小化が主目的
    
    # 制約条件
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * PENALTY_COEFFICIENT
    if comfort < COMFORT_THRESHOLD:
        fitness += (COMFORT_THRESHOLD - comfort) * 10000
    
    return fitness
```

**評価ポイント**:
- CO2排出量がどこまで削減できたか
- 快適性6.0以上を維持できているか
- どのような設計パラメータが有効だったか

### 課題1-2: 低コスト・高快適性住宅
**目的**: 建設コストを抑えつつ，快適な住環境を実現する

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    SAFETY_THRESHOLD = 2.0
    
    # コストと快適性の正規化
    normalized_cost = cost / 200000  # 20万円/m²を基準
    normalized_comfort = comfort / 10  # 10点満点
    
    # 重み付け（コスト60%，快適性40%）
    fitness = 0.6 * normalized_cost + 0.4 * (1 - normalized_comfort)
    
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 100
    
    return fitness
```

**評価ポイント**:
- コストと快適性のバランスが取れているか
- 重み係数を変更した場合の影響分析

### 課題1-3: 安全性重視設計
**目的**: 地震に強い安全な住宅を最小コストで実現する

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    ENHANCED_SAFETY_THRESHOLD = 2.5  # 通常より高い安全基準
    
    fitness = cost  # コスト最小化
    
    # 強化された安全性制約
    if safety < ENHANCED_SAFETY_THRESHOLD:
        penalty = (ENHANCED_SAFETY_THRESHOLD - safety) * 200000
        fitness += penalty
    
    return fitness
```

---

## 2. 応用課題（中級）

### 課題2-1: 施工性重視の実用設計
**目的**: 施工しやすく，現実的な建設が可能な設計を探索する

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    SAFETY_THRESHOLD = 2.0
    CONSTRUCTABILITY_THRESHOLD = 7.0  # 施工性の最低基準
    
    # 施工性が低いと実質的にコストが上がると仮定
    effective_cost = cost * (1 + (10 - constructability) / 10)
    fitness = effective_cost
    
    # 制約条件
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 100000
    if constructability < CONSTRUCTABILITY_THRESHOLD:
        fitness += (CONSTRUCTABILITY_THRESHOLD - constructability) * 5000
    
    return fitness
```

### 課題2-2: 多目的バランス設計
**目的**: 全ての評価指標をバランスよく満たす設計を見つける

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    SAFETY_THRESHOLD = 2.0
    
    # 各指標を0-1に正規化
    norm_cost = cost / 300000
    norm_co2 = co2 / 1500
    norm_comfort = comfort / 10
    norm_construct = constructability / 10
    
    # 均等な重み付けで統合
    fitness = (norm_cost + norm_co2 + (1-norm_comfort) + (1-norm_construct)) / 4
    
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 100
    
    return fitness
```

### 課題2-3: 段階的制約設計
**目的**: 複数の制約条件を段階的に満たす設計を実現する

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    # 段階的な制約（優先順位順）
    SAFETY_THRESHOLD = 2.0
    COST_LIMIT = 250000
    COMFORT_THRESHOLD = 6.0
    CO2_LIMIT = 1000
    
    fitness = 0
    
    # 第1優先: 安全性（必須）
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 1000000
    
    # 第2優先: コスト上限
    if cost > COST_LIMIT:
        fitness += (cost - COST_LIMIT) * 100
    
    # 第3優先: 快適性確保
    if comfort < COMFORT_THRESHOLD:
        fitness += (COMFORT_THRESHOLD - comfort) * 10000
    
    # 第4優先: CO2削減
    fitness += co2
    
    return fitness
```

---

## 3. 発展課題（上級）

### 課題3-1: ライフサイクルコスト最適化
**目的**: 初期建設コストと長期運用コストの総和を最小化する

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    SAFETY_THRESHOLD = 2.0
    OPERATION_YEARS = 30  # 30年間の運用を想定
    
    # CO2排出量を運用コストの代理指標として使用
    # 断熱性能が高い（CO2が少ない）ほど冷暖房費が削減される
    annual_operation_cost = co2 * 50  # CO2 1kg = 年間50円と仮定
    lifecycle_cost = cost + (annual_operation_cost * OPERATION_YEARS)
    
    fitness = lifecycle_cost
    
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 100000
    
    return fitness
```

### 課題3-2: 地域適応型設計
**目的**: 特定の地域特性（気候・災害リスク等）に適応した設計を行う

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    # 寒冷地向け設定
    SAFETY_THRESHOLD = 2.5  # 雪害対策で高めの安全率
    COMFORT_THRESHOLD = 7.0  # 断熱重視で高めの快適性
    
    # 断熱性能を重視（CO2削減と快適性向上の相乗効果）
    insulation_score = (10 - co2/200) * comfort / 10
    
    fitness = cost - insulation_score * 20000
    
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 100000
    if comfort < COMFORT_THRESHOLD:
        fitness += (COMFORT_THRESHOLD - comfort) * 50000
    
    return fitness
```

### 課題3-3: イノベーティブ設計探索
**目的**: 従来にない斬新な設計を発見する（快適性と施工性の新しいバランス）

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    SAFETY_THRESHOLD = 2.0
    INNOVATION_BONUS_THRESHOLD = 8.0
    
    # 快適性と施工性が両方高い場合にボーナス
    innovation_score = 0
    if comfort >= INNOVATION_BONUS_THRESHOLD and constructability >= INNOVATION_BONUS_THRESHOLD:
        innovation_score = comfort * constructability / 100
    
    fitness = cost - innovation_score * 50000
    
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 100000
    
    # 極端に低い指標にペナルティ
    if comfort < 4.0 or constructability < 4.0:
        fitness += 100000
    
    return fitness
```

---

## 4. 分析課題

### 課題4-1: パラメータ感度分析
**実施内容**:
1. 基本となる適応度関数を選択
2. 各設計パラメータを個別に変化させて影響を分析
3. 最も影響力の大きいパラメータを特定
4. 結果をグラフ化してレポート作成

### 課題4-2: 収束過程の可視化
**実施内容**:
1. `pso_optimization_log.csv`からデータを読み込み
2. 各世代の最良解，平均値，標準偏差をプロット
3. 収束速度と最終解の品質の関係を分析
4. パラメータ設定（粒子数，反復回数）の影響を考察

### 課題4-3: パレートフロント探索
**実施内容**:
1. 2つの相反する目的（例：コストvs快適性）を設定
2. 重み係数を変えながら複数回PSOを実行
3. 得られた解をプロットしてパレートフロントを描画
4. トレードオフの関係を分析

---

## 5. 実装課題

### 課題5-1: 新しい制約条件の追加
**実施内容**:
1. 窓面積比と快適性の関係を考慮した制約を追加
2. 構造部材の比率に関する制約を追加
3. 実装結果を検証

### 課題5-2: 材料選択の最適化
**実施内容**:
1. FIXED_MATERIALSを変更可能にする
2. 材料の組み合わせも最適化対象に含める
3. 材料による性能差を分析

### 課題5-3: 動的ペナルティ係数
**実施内容**:
1. 反復回数に応じてペナルティ係数を変化させる
2. 初期は探索を広く，後期は制約を厳しくする
3. 収束性能の向上を検証

---

## レポート作成指針

### 必須項目
1. **課題の理解**: 選択した課題の目的と意義
2. **実装内容**: 適応度関数の設計思想と実装コード
3. **実験結果**: 
   - 得られた最適解の詳細
   - 収束グラフ
   - 各評価指標の値
4. **考察**:
   - なぜその結果が得られたか
   - 改善の余地はあるか
   - 実用性の評価
5. **結論**: 課題を通じて学んだこと

### 評価基準
- 適応度関数の設計の妥当性（40%）
- 実験結果の分析の深さ（30%）
- 考察の論理性と洞察（20%）
- レポートの構成と表現（10%）

### 提出物
1. 修正したPSO.pyのコード
2. 実行結果のCSVファイル
3. 生成されたグラフ（PNG）
4. レポート（PDF形式，5-10ページ）

---

## 発展的な学習

### 推奨される追加学習
1. **最適化理論**: 他のメタヒューリスティクス手法の学習
2. **建築工学**: 構造力学，環境工学の基礎
3. **プログラミング**: Pythonによるデータ分析，可視化
4. **機械学習**: 代理モデルによる高速化

### 参考文献
- 粒子群最適化（PSO）に関する論文
- 建築設計の多目的最適化に関する研究
- FreeCADとCalculiXのドキュメント