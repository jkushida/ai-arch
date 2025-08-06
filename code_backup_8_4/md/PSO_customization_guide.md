# PSO.py カスタマイズガイド（初学者向け）

## はじめに：Pythonの基本

### 「#」（シャープ）記号の役割
```python
# これはコメントです．プログラムには影響しません
# コメントは説明やメモを書くために使います

print("Hello World")  # 行の途中からもコメントが書けます

# 複数行をコメントアウトする例
# print("この行は実行されません")
# print("この行も実行されません")
print("この行だけ実行されます")

# 複数行を一度にコメントアウトする別の方法
'''
print("この部分は")
print("全て無視されます")
print("3つのクォートで囲みます")
'''
```

## calculate_fitness関数を変更する手順

### ステップ1: PSO.pyファイルを開く
1. テキストエディタでPSO.pyを開く
   - Windows: メモ帳，VS Code，Atom など
   - Mac: テキストエディット，VS Code，Atom など
2. 「calculate_fitness」で検索（Ctrl+F または Cmd+F）
3. 84行目付近にある関数定義を見つける

### ステップ2: 元の関数を確認する
```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    """
    目的関数の計算（全ての評価指標を必須引数として受け取る）
    
    Parameters:
    -----------
    cost : float
        建設コスト（円/m²）
    safety : float
        安全率
    co2 : float
        CO2排出量（kg-CO2/m²）
    comfort : float
        快適性スコア（0-10）
    constructability : float
        施工性スコア（0-10）
    """
    # ===== カスタマイズ可能な部分 =====
    
    # 1. 目的関数の選択（どの指標を最適化するか）
    # デフォルト：コスト最小化
    fitness = cost
    
    # 例1）CO2排出量最小化（環境重視）
    # fitness = co2
    
    # 例2）快適性最大化（※最大化問題は負の値にする）
    # fitness = -comfort  # 快適性を最大化（負の値）
    
    # 例3）施工性最大化
    # fitness = -constructability
    
    # 例4）多目的最適化（重み付け和）
    # w1, w2, w3 = 0.5, 0.3, 0.2  # 重み係数
    # fitness = w1 * (cost/100000) + w2 * (co2/1000) + w3 * (-comfort/10)
    
    # 例5）多目的最適化（コストとCO2の同時最小化）
    # fitness = 0.7 * (cost/100000) + 0.3 * (co2/1000)
    
    # 2. 制約条件の設定
    SAFETY_THRESHOLD = 2.0      # 安全率の最小値
    PENALTY_COEFFICIENT = 100000  # ペナルティの重み
    
    # 3. 安全率制約の適用（必須）
    if safety < SAFETY_THRESHOLD:
        penalty = (SAFETY_THRESHOLD - safety) * PENALTY_COEFFICIENT
        fitness += penalty
    
    # 4. 追加の制約条件（必要に応じてコメントアウトを外す）
    # if comfort < 5.0:  # 快適性5.0以上
    #     fitness += (5.0 - comfort) * 10000
    
    # if co2 > 1000:  # CO2排出量1000以下
    #     fitness += (co2 - 1000) * 100
    
    # if constructability < 6.0:  # 施工性6.0以上
    #     fitness += (6.0 - constructability) * 5000
    
    return fitness
```

### ステップ3: 関数を変更する

#### 変更例1: CO2排出量を最小化する
```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    # 1. 目的関数の選択
    # 元の行をコメントアウト（#を付ける）
    # fitness = cost  
    
    # 新しい行を追加
    fitness = co2  # CO2排出量を最小化
    
    # 2. 制約条件の設定
    SAFETY_THRESHOLD = 2.0
    PENALTY_COEFFICIENT = 100000
    
    # 3. 安全率制約の適用（必須）
    if safety < SAFETY_THRESHOLD:
        penalty = (SAFETY_THRESHOLD - safety) * PENALTY_COEFFICIENT
        fitness += penalty
    
    return fitness
```

#### 変更例2: 快適性を最大化する
```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    # 1. 目的関数の選択
    # 快適性は「大きい方が良い」ので，マイナスを付ける
    fitness = -comfort  # 快適性を最大化（負の値にする）
    
    # 2. 制約条件の設定
    SAFETY_THRESHOLD = 2.0
    PENALTY_COEFFICIENT = 100000
    
    # 3. 安全率制約の適用（必須）
    if safety < SAFETY_THRESHOLD:
        penalty = (SAFETY_THRESHOLD - safety) * PENALTY_COEFFICIENT
        fitness += penalty
    
    return fitness
```

### なぜマイナスを付けるのか？
```python
# 配布したPSOは「最小化」するアルゴリズムです

# ＜最小化の例：コスト＞
# 建物A: コスト10万円
# 建物B: コスト20万円
# → 10万円 < 20万円 なので，建物Aが選ばれる（小さい方が良い）

# ＜最大化の例：快適性＞
# 建物A: 快適性8点
# 建物B: 快適性5点
# → 8点 > 5点 なので，建物Aの方が良い（大きい方が良い）

# でもPSOは小さい方を選ぶので，マイナスを付けて逆転させます
# 建物A: -8
# 建物B: -5
# → -8 < -5 なので，建物A（快適性8点）が選ばれる！
```

## よく使うカスタマイズパターン

### パターン1: 単一指標の最適化
```python
# コスト最小化（デフォルト）
fitness = cost

# CO2最小化
fitness = co2

# 快適性最大化
fitness = -comfort

# 施工性最大化  
fitness = -constructability
```

### パターン2: 複数の制約条件
```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    # 主目的
    fitness = cost
    
    # 制約1: 安全率
    SAFETY_THRESHOLD = 2.0
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 100000
    
    # 制約2: 快適性
    COMFORT_THRESHOLD = 6.0
    if comfort < COMFORT_THRESHOLD:
        fitness += (COMFORT_THRESHOLD - comfort) * 10000
    
    # 制約3: CO2排出量
    CO2_LIMIT = 1000
    if co2 > CO2_LIMIT:
        fitness += (co2 - CO2_LIMIT) * 100
    
    return fitness
```

### パターン3: 重み付け和（多目的最適化）
```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    SAFETY_THRESHOLD = 2.0
    
    # 各指標を0-1に正規化（同じスケールにする）
    norm_cost = cost / 300000        # 30万円を基準
    norm_co2 = co2 / 1500            # 1500kgを基準
    norm_comfort = comfort / 10       # 10点満点
    
    # 重み付け（合計1.0になるように）
    w_cost = 0.5     # コストを50%重視
    w_co2 = 0.3      # CO2を30%重視  
    w_comfort = 0.2  # 快適性を20%重視
    
    # 重み付け和を計算
    fitness = (w_cost * norm_cost + 
               w_co2 * norm_co2 + 
               w_comfort * (1 - norm_comfort))  # 快適性は大きい方が良いので反転
    
    # 安全率制約
    if safety < SAFETY_THRESHOLD:
        fitness += (SAFETY_THRESHOLD - safety) * 100
    
    return fitness
```

## 実験の進め方

### 1. バックアップを取る
```bash
# PSO.pyのバックアップを作成
cp PSO.py PSO_backup.py
```

### 2. 小さな変更から始める
最初は1つの指標だけを変更して，動作を確認する

### 3. 実行して結果を確認
```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd PSO.py
```

### 4. 結果を記録する
- どの指標を最適化したか
- どんな結果が得られたか
- 予想と違った点はあるか

### 5. 徐々に複雑にする
単一指標 → 制約追加 → 多目的最適化

## デバッグのヒント

### print文を使って値を確認
```python
def calculate_fitness(cost, safety, co2, comfort, constructability):
    # デバッグ用：値を表示
    print(f"コスト: {cost}, 安全率: {safety}, CO2: {co2}")
    
    fitness = cost
    
    # 制約違反も確認
    if safety < 2.0:
        print(f"警告: 安全率{safety}は基準未満です")
        fitness += (2.0 - safety) * 100000
    
    print(f"最終適応度: {fitness}")
    return fitness
```

### エラーが出た場合
1. **IndentationError**: インデント（字下げ）を確認
2. **NameError**: 変数名のスペルを確認
3. **TypeError**: 引数の数や型を確認

## 練習問題

### 問題1: 環境重視の設計
CO2排出量を最小化しつつ，快適性6.0以上を確保する適応度関数を作成してください．

### 問題2: 災害に強い設計  
安全率3.0以上を必須条件として，その中で最もコストが低い設計を探す適応度関数を作成してください．

### 問題3: バランス型設計
コスト，CO2，快適性の3つを，4:3:3の重みで評価する適応度関数を作成してください．

## まとめ
- `#`でコメントアウトして，元のコードを残しながら変更する
- 最大化したい場合はマイナスを付ける
- 制約条件はペナルティとして加算する
- print文でデバッグしながら進める
- 小さな変更から始めて，徐々に複雑にする