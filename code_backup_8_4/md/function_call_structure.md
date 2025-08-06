# test_generate_building.py から呼ばれる関数構造

## エントリーポイント

```
test_generate_building.py
└── evaluate_building_from_params() [3436行]
    └── evaluate_building() [3105行]
```

## evaluate_building() 内の主要な関数呼び出し

### 1. 初期設定
```
evaluate_building()
├── setup_deterministic_fem() [1541行]
│   └── メッシュ生成の決定論的設定
```

### 2. 建物モデル生成
```
evaluate_building()
├── create_realistic_building_model() [439行]
│   ├── create_simple_box_roof() [170行] - 平らな屋根の場合
│   ├── create_parametric_barrel_roof() [179行] - かまぼこ屋根
│   │   ├── calculate_roof_curvature() [94行]
│   │   └── calculate_roof_efficiency() [104行]
│   ├── create_balcony() [387行] - バルコニー作成
│   ├── create_external_stairs() [1556行] - 外部階段
│   ├── set_part_color() [120行] - 色設定
│   ├── ensure_parts_visibility() [136行] - 可視性設定
│   ├── safe_set_display_mode() [1315行]
│   └── safe_gui_operations() [1346行]
```

### 3. FEM解析設定
```
evaluate_building()
├── setup_basic_fem_analysis() [1715行]
│   ├── is_gui_mode() [1187行]
│   ├── safe_set_visibility() [1293行]
│   └── 各種FEM設定（材料，境界条件，荷重）
```

### 4. メッシュ生成と解析
```
evaluate_building()
├── run_mesh_generation() [2026行]
├── check_fixed_nodes() [1998行] - デバッグ用
├── run_calculix_analysis() [2145行]
└── extract_fem_results() [2248行]
```

### 5. 評価関数
```
evaluate_building()
├── calculate_safety_factor() [2600行]
├── calculate_economic_cost() [2616行]
├── calculate_environmental_impact() [2722行]
├── calculate_comfort_score() [2850行]
└── calculate_constructability_score() [3024行]
```

### 6. ファイル保存（オプション）
```
evaluate_building()
└── clean_document_for_fcstd_save() [3346行] ※save_fcstd=Trueの場合のみ
    ├── safe_remove_object() [1279行]
    ├── create_load_visualization_arrows() [1364行]
    └── create_support_visualization() [1450行]
```

## 削除可能な関数

以下の関数は現在の使用状況では削除可能：

1. **save_building_snapshot()** [1198行] - 使用されていない
2. **__main__ブロック** [3504行以降] - テスト用コード

## GUI関連のユーティリティ関数（保持推奨）

これらの関数はGUI/CUI両対応のために必要：

- is_gui_mode() [1187行]
- safe_set_visibility() [1293行]
- safe_set_display_mode() [1315行]
- safe_gui_operations() [1346行]
- safe_remove_object() [1279行]

## まとめ

test_generate_building.py から実際に使用される関数は，FEM解析の本質的な処理に関わるものがほとんどで，可視化関連の一部の関数（save_building_snapshot，create_load_visualization_arrows，create_support_visualization）は削除可能です．