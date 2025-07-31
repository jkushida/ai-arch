# 第4段階：CO2-コスト相関をさらに低減する追加調整

## 現状分析
- CO2-コスト相関: 0.983（目標0.8）
- 木造が低CO2・低コストで線形関係が強い

## 追加調整案

### 1. 高級木材オプションの導入
```python
# 材料選択を3値に拡張
# 0: コンクリート（高CO2・中コスト）
# 1: 一般木材（低CO2・低コスト）
# 2: 高級木材（低CO2・高コスト）※CLTなど

'premium_wood': {
    'density': 600,           # kg/m³
    'E': 12000,              # MPa（CLT相当）
    'cost_per_m3': 80000,    # 円/m³（高級材）
    'co2_per_m3': 100,       # kg-CO2/m³（加工が複雑）
    'response_factor': 3.0,   # 応答倍率
}
```

### 2. リサイクルコンクリートの追加
```python
'recycled_concrete': {
    'density': 2300,          # kg/m³
    'E': 22000,              # MPa（やや低い）
    'cost_per_m3': 45000,    # 円/m³（処理コスト含む）
    'co2_per_m3': 200,       # kg-CO2/m³（通常の半分）
    'response_factor': 1.2,   # 応答倍率
}
```

### 3. 施工の複雑さによるコスト変動
```python
# 混合構造の場合，異種材料接合部のコスト増
if is_mixed_structure:
    joint_complexity = count_material_transitions()
    additional_cost = joint_complexity * 5000  # 円/m²
```

### 4. 建物形状による施工費変動
```python
# 壁傾斜や屋根形態による施工難易度
shape_complexity = abs(wall_tilt_angle) / 30.0 + roof_morph
construction_factor = 1.0 + 0.3 * shape_complexity
```

### 5. 地域差の導入（ランダム）
```python
# 地域による人件費・輸送費の差
region_factor = np.random.uniform(0.8, 1.2)
labor_cost *= region_factor
```

## 実装優先順位
1. 高級木材オプション（最も効果的）
2. リサイクルコンクリート
3. 混合構造のペナルティ
4. 形状複雑さ
5. 地域差

## 期待される効果
- 低CO2でも高コストの選択肢が増える
- 高CO2でも低コストの選択肢が増える
- 相関係数を0.8程度まで低減可能