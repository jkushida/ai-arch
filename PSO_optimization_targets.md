# PSO最適化目標の設定例

## 概要
PSO.pyでは，`calculate_fitness`関数を編集することで様々な最適化目標を設定できます．このドキュメントでは，実用的な最適化目標の例を紹介します．

## 基本的な考え方

### 最小化問題と最大化問題
- 配布したPSOは**最小化**アルゴリズムです
- 小さい値を持つ解が「良い」と判断されます
- 最大化したい場合は，マイナスを付けて符号を反転させます

```python
# 最小化したい場合（コスト，CO2など）
fitness = cost  # そのまま使用

# 最大化したい場合（快適性，施工性など）
fitness = -comfort  # マイナスを付ける
```

## 実用的な最適化目標の例

### 1. 環境重視設計（CO2最小化）
地球温暖化対策として，CO2排出量を最小化する設計を探索します．

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    # CO2排出量を最小化
    fitness = co2
    
    # 安全率制約（必須）
    SAFETY_THRESHOLD = 2.0
    PENALTY_COEFFICIENT = 100000
    
    if safety < SAFETY_THRESHOLD:
        penalty = (SAFETY_THRESHOLD - safety) * PENALTY_COEFFICIENT
        fitness += penalty
    
    return fitness
```

**期待される結果**：

- 木材使用量が増える傾向
- コストは考慮されないため，高くなる可能性
- 環境性能証明書の取得に有利

### 2. 居住性重視設計（快適性最大化）
住む人の快適性を最優先する高級住宅向けの設計です．

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    # 快適性を最大化（マイナスを付ける）
    fitness = -comfort
    
    # 安全率制約（必須）
    SAFETY_THRESHOLD = 2.0
    PENALTY_COEFFICIENT = 100000
    
    if safety < SAFETY_THRESHOLD:
        penalty = (SAFETY_THRESHOLD - safety) * PENALTY_COEFFICIENT
        fitness += penalty
    
    # 追加制約：最低限の快適性を保証
    COMFORT_MINIMUM = 7.0
    if comfort < COMFORT_MINIMUM:
        fitness += (COMFORT_MINIMUM - comfort) * 50000
    
    return fitness
```

**期待される結果**：

- 窓面積比が大きくなる
- 階高が高くなる傾向
- 高コストだが住み心地の良い設計

### 3. 施工効率重視設計（施工性最大化）
工期短縮や施工の簡易性を重視する設計です．

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    # 施工性を最大化
    fitness = -constructability
    
    # 安全率制約（必須）
    SAFETY_THRESHOLD = 2.0
    PENALTY_COEFFICIENT = 100000
    
    if safety < SAFETY_THRESHOLD:
        penalty = (SAFETY_THRESHOLD - safety) * PENALTY_COEFFICIENT
        fitness += penalty
    
    return fitness
```

**期待される結果**：

- シンプルな形状
- 標準的な部材寸法
- 工期短縮による間接費削減

### 4. 経済性と環境性のバランス設計
コストとCO2を同時に考慮するサステナブル設計です．

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    # 正規化（スケールを合わせる）
    norm_cost = cost / 200000      # 20万円/m²を基準
    norm_co2 = co2 / 1000          # 1000kg/m²を基準
    
    # 重み付け（コスト60%，CO2 40%）
    w_cost = 0.6
    w_co2 = 0.4
    
    fitness = w_cost * norm_cost + w_co2 * norm_co2
    
    # 安全率制約（必須）
    SAFETY_THRESHOLD = 2.0
    PENALTY_COEFFICIENT = 100000
    
    if safety < SAFETY_THRESHOLD:
        penalty = (SAFETY_THRESHOLD - safety) * PENALTY_COEFFICIENT
        fitness += penalty
    
    return fitness
```

**期待される結果**：

- コストと環境性能の良好なバランス
- 実用的で持続可能な設計
- グリーン建築認証の取得可能性

### 5. 総合バランス設計（全指標考慮）
すべての評価指標をバランス良く考慮する設計です．

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    # 各指標の正規化
    norm_cost = cost / 250000              # 25万円/m²を基準
    norm_co2 = co2 / 1200                  # 1200kg/m²を基準
    norm_comfort = comfort / 10            # 10点満点
    norm_construct = constructability / 10  # 10点満点
    
    # 重み付け（合計1.0）
    w_cost = 0.4          # 経済性 40%
    w_co2 = 0.2           # 環境性 20%
    w_comfort = 0.2       # 快適性 20%
    w_construct = 0.2     # 施工性 20%
    
    # 快適性と施工性は大きい方が良いので反転
    fitness = (w_cost * norm_cost + 
               w_co2 * norm_co2 + 
               w_comfort * (1 - norm_comfort) + 
               w_construct * (1 - norm_construct))
    
    # 安全率制約（必須）
    SAFETY_THRESHOLD = 2.0
    PENALTY_COEFFICIENT = 100
    
    if safety < SAFETY_THRESHOLD:
        penalty = (SAFETY_THRESHOLD - safety) * PENALTY_COEFFICIENT
        fitness += penalty
    
    return fitness
```

**期待される結果**：

- 全体的にバランスの取れた設計
- 極端な解を避ける
- 実務的に採用しやすい

### 6. 災害対策重視設計（高安全率）
地震や台風に強い建物を目指す設計です．

```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    # コストを最小化しつつ，高い安全率を要求
    fitness = cost
    
    # より厳しい安全率制約
    SAFETY_THRESHOLD = 3.0  # 通常の2.0から3.0に引き上げ
    PENALTY_COEFFICIENT = 150000
    
    if safety < SAFETY_THRESHOLD:
        penalty = (SAFETY_THRESHOLD - safety) * PENALTY_COEFFICIENT
        fitness += penalty
    
    # 安全率が高いほどボーナス（任意）
    if safety > SAFETY_THRESHOLD:
        bonus = -(safety - SAFETY_THRESHOLD) * 10000  # 負の値でボーナス
        fitness += bonus
    
    return fitness
```

**期待される結果**：

- 構造部材が太くなる
- 高い耐震・耐風性能
- 保険料の削減可能性

## 重み係数の決め方

### 1. 要求仕様から決定
```python
# クライアントの優先順位に基づく
# 例：「環境性能を最重視，次にコスト」
w_co2 = 0.5      # 50%
w_cost = 0.3     # 30%
w_comfort = 0.2  # 20%
```

### 2. 正規化の基準値
各指標の典型的な値を基準にします：
- コスト：15～30万円/m² → 20万円を基準
- CO2：800～1500kg/m² → 1000kgを基準
- 快適性：4～8点 → 10点満点
- 施工性：4～8点 → 10点満点

### 3. ペナルティ係数の調整
```python
# 弱い制約（ソフト制約）
PENALTY_COEFFICIENT = 1000    # 違反を許容しやすい

# 強い制約（ハード制約）
PENALTY_COEFFICIENT = 100000  # 違反を許容しにくい
```

## 実験の進め方

### ステップ1：単一目標から始める
まず，1つの指標だけを最適化して，その特性を理解します．

### ステップ2：制約を追加
必要に応じて追加の制約条件を設定します．

### ステップ3：多目的最適化へ
複数の指標を組み合わせて，より実用的な解を探索します．

### ステップ4：重みの調整
重み係数を変えて，異なるトレードオフを探ります．

## デバッグのヒント

### 値の確認
```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    # デバッグ出力
    print(f"評価値 - コスト:{cost:.0f}, 安全率:{safety:.2f}, CO2:{co2:.0f}")
    
    fitness = cost
    
    # 制約違反の確認
    if safety < 2.0:
        penalty = (2.0 - safety) * 100000
        print(f"  安全率違反！ペナルティ:{penalty:.0f}")
        fitness += penalty
    
    print(f"  最終適応度:{fitness:.0f}")
    return fitness
```

### 結果の分析
- 最適化ログ（CSV）を確認
- 収束曲線で最適化の進行を確認
- 散布図で解の分布を確認

## まとめ

1. **目的を明確に**：何を最適化したいか決める
2. **制約を設定**：必須条件を明確にする
3. **実験と調整**：パラメータを調整しながら実験
4. **結果を評価**：得られた設計が要求を満たすか確認

最適な設計は，プロジェクトの要求によって異なります．PSO.pyの柔軟性を活用して，様々な設計目標を探索してください．