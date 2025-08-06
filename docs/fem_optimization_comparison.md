# FEM解析高速化案 - 現在設定と提案設定の比較

## 1. メッシュサイズ設定

| 項目 | 現在の設定 | 高速化案 | 効果 | 注意点 |
|------|-----------|----------|------|--------|
| CharacteristicLengthMax | 600.0 mm | 1000.0 mm | 計算時間: 約40-60%削減 | 精度が若干低下 |
| CharacteristicLengthMin | 200.0 mm | 400.0 mm | メッシュ要素数: 約50%削減 | 応力集中部の精度注意 |
| 推定ノード数 | 約50,000-100,000 | 約15,000-30,000 | メモリ使用量: 大幅削減 | 複雑形状で不安定化リスク |

## 2. 並列計算設定

| 項目 | 現在の設定 | 高速化案 | 効果 | 注意点 |
|------|-----------|----------|------|--------|
| **GmshTools並列化** |  |  |  |  |
| General.NumThreads | 2 | 8-12 (CPUに応じて) | メッシュ生成: 2-3倍高速化 | メモリ使用量増加 |
| **CalculiXソルバー並列化** |  |  |  |  |
| Windows (i9-13900) | 16スレッド | 20-24スレッド | 解析時間: 20-30%短縮 | システム応答性低下 |
| macOS (M2) | 4スレッド | 6スレッド | 解析時間: 10-20%短縮 | 発熱に注意 |

## 3. ソルバー収束条件

| 項目 | 現在の設定 | 高速化案 | 効果 | 注意点 |
|------|-----------|----------|------|--------|
| IterationsControlMaximum | 2000 | 1000 | 最大計算時間: 50%削減 | 収束しない場合あり |
| ConvergenceTolerance | デフォルト (1e-6) | 1e-4 | 反復回数: 30-50%削減 | 解の精度低下 |
| GeometricalNonlinearity | False | False (変更なし) | - | - |

## 4. メッシュアルゴリズム

| 項目 | 現在の設定 | 高速化案 | 効果 | 注意点 |
|------|-----------|----------|------|--------|
| Algorithm2D | 'Automatic' | 'MeshAdapt' | 2Dメッシュ: 20-30%高速化 | 品質が不均一になる可能性 |
| Algorithm3D | 'Automatic' | 'Delaunay' | 3Dメッシュ: 15-25%高速化 | 複雑形状で失敗リスク |

## 5. 推奨される段階的実装

### Phase 1: 低リスク・高効果（推奨）
1. **メッシュサイズ調整**
   - CharacteristicLengthMax: 600 → 800 mm
   - CharacteristicLengthMin: 200 → 300 mm
   - 効果: 計算時間30%削減、精度維持

2. **並列化強化**
   - GmshTools: NumThreads 2 → 8
   - CalculiX: 現在の設定を維持
   - 効果: メッシュ生成2倍高速化

### Phase 2: 中リスク・中効果
3. **収束条件の調整**
   - ConvergenceTolerance: 1e-5
   - 効果: 反復回数20%削減

### Phase 3: 高リスク・変動効果
4. **アルゴリズム変更**
   - 形状に応じて選択的に適用
   - 効果: ケースバイケース

## 総合的な期待効果

| 最適化レベル | 計算時間削減率 | 精度への影響 | 推奨用途 |
|-------------|---------------|------------|----------|
| 保守的 (Phase 1のみ) | 40-50% | 最小 | 本番環境 |
| バランス型 (Phase 1+2) | 50-60% | 軽微 | 開発・検証環境 |
| アグレッシブ (全適用) | 60-75% | 中程度 | 初期探索・スクリーニング |

## 安全性評価への影響分析

### 安全率計算の仕組み
現在のコードでは、安全率は以下の2つの要因で決定されます：

1. **応力による安全率** = 許容応力 / 最大応力
   - コンクリート: 35.0 MPa
   - 木材: 6.0 MPa

2. **変形による安全率** = 許容変位 / 最大変位
   - 層間変形角: 1/200以下
   - 木造は0.3倍の厳しい係数を適用

**最終安全率 = min(応力安全率, 変形安全率)**

### 各最適化レベルの影響

| 最適化項目 | 安全性への影響 | リスク評価 | 推奨対策 |
|-----------|--------------|----------|---------|
| **メッシュサイズ** |  |  |  |
| 600→800mm | 応力集中部の解像度低下（5-10%） | 低 | 応力集中係数1.1を適用 |
| 600→1000mm | 応力ピーク値の過小評価（10-20%） | 中 | 安全係数1.2を適用 |
| **収束条件** |  |  |  |
| 1e-6→1e-5 | 応力精度±2% | 極低 | 特に対策不要 |
| 1e-6→1e-4 | 応力精度±5% | 低 | 重要部材は再計算 |
| **並列化** |  |  |  |
| スレッド数増加 | 数値誤差の可能性（<1%） | 極低 | 影響なし |

### 安全性を保つための補正案

```python
def apply_mesh_correction_factor(mesh_size, base_safety_factor):
    """
    メッシュサイズに応じた安全率補正
    """
    if mesh_size <= 600:
        return base_safety_factor  # 補正なし
    elif mesh_size <= 800:
        return base_safety_factor * 0.95  # 5%減
    elif mesh_size <= 1000:
        return base_safety_factor * 0.90  # 10%減
    else:
        return base_safety_factor * 0.85  # 15%減
```

### 推奨される安全な高速化設定

```python
# 安全性を重視した高速化設定
SAFE_OPTIMIZATION_SETTINGS = {
    'mesh': {
        'CharacteristicLengthMax': 800.0,  # 600→800（控えめ）
        'CharacteristicLengthMin': 300.0,  # 200→300（控えめ）
    },
    'solver': {
        'ConvergenceTolerance': 1e-5,  # 1桁緩和のみ
        'safety_correction': 0.95,      # 5%の安全側補正
    }
}
```

## 並列化パラメータの詳細

### solver.NumberOfThreads と General.NumThreads の違い

| パラメータ | 対象ツール | 用途 | 処理内容 | 設定場所 |
|-----------|----------|------|----------|----------|
| **solver.NumberOfThreads** | CalculiX（FEMソルバー） | FEM解析の並列化 | ・剛性マトリクスの分解<br>・応力/変位の計算<br>・数値解析の反復計算 | generate_building_fem_analyze.py<br>2341-2361行目 |
| **General.NumThreads** | Gmsh（メッシュ生成） | メッシュ生成の並列化 | ・3D形状の要素分割<br>・ノード生成<br>・メッシュ品質最適化 | generate_building_fem_analyze.py<br>2196-2207行目 |

### 処理フローにおける位置づけ

```
建物モデル生成
    ↓
メッシュ生成（Gmsh）     ← General.NumThreads = 2（現在値）
    ↓
FEM解析（CalculiX）     ← solver.NumberOfThreads = 16（Windows設定値）
    ↓
結果出力
```

### 現在の設定と推奨値

| 環境 | ツール | 現在値 | 推奨値 | 改善効果 |
|------|--------|--------|--------|----------|
| **Windows (i9-13900)** |  |  |  |  |
| | Gmsh | 2 | 8-12 | メッシュ生成2-4倍高速化 |
| | CalculiX | 16 | 16-20 | 既に最適（現状維持可） |
| **macOS (M2)** |  |  |  |  |
| | Gmsh | 2 | 4 | メッシュ生成2倍高速化 |
| | CalculiX | 4 | 4-6 | 解析10-20%高速化 |

### 最適化のための設定例

```python
# Gmshの並列化強化（generate_building_fem_analyze.py 2206行目付近）
if platform.system() == 'Windows':
    gmsh_threads = min(12, os.cpu_count() // 3)  # 現在の2から増加
elif platform.system() == 'Darwin':  # macOS
    gmsh_threads = 4 if os.cpu_count() <= 8 else 6
else:  # Linux
    gmsh_threads = min(8, os.cpu_count() // 4)

gmsh_tools.Options = "".join([
    f"General.NumThreads = {gmsh_threads};",  # 動的に設定
    # 他のオプション...
])
```

### 並列化による全体的な高速化効果

| 段階 | 現在の処理時間比率 | 並列化強化後 | 削減率 |
|------|------------------|------------|--------|
| メッシュ生成 | 30% | 10-15% | 50-67% |
| FEM解析 | 60% | 50-55% | 8-17% |
| その他 | 10% | 10% | 0% |
| **合計** | 100% | 70-80% | **20-30%削減** |

## 実装時の注意事項

1. **精度検証**: 高速化設定導入前後で、既知の解析結果と比較検証を実施
2. **段階的導入**: Phase 1から順次導入し、各段階で効果と精度を確認
3. **パラメータ調整**: 建物の規模や複雑さに応じて、パラメータを動的に調整
4. **エラーハンドリング**: メッシュ生成失敗時の自動フォールバック機能を実装

## コード例

```python
# 高速化設定の実装例
def apply_optimization_level(mesh_obj, solver, level='balanced'):
    """
    最適化レベルに応じたFEM設定を適用
    
    Args:
        mesh_obj: メッシュオブジェクト
        solver: ソルバーオブジェクト
        level: 'conservative', 'balanced', 'aggressive'
    """
    if level == 'conservative':
        # Phase 1のみ
        mesh_obj.CharacteristicLengthMax = 800.0
        mesh_obj.CharacteristicLengthMin = 300.0
        # GmshTools設定は別途
        
    elif level == 'balanced':
        # Phase 1 + 2
        mesh_obj.CharacteristicLengthMax = 800.0
        mesh_obj.CharacteristicLengthMin = 300.0
        if hasattr(solver, 'ConvergenceTolerance'):
            solver.ConvergenceTolerance = 1e-5
            
    elif level == 'aggressive':
        # 全Phase適用
        mesh_obj.CharacteristicLengthMax = 1000.0
        mesh_obj.CharacteristicLengthMin = 400.0
        if hasattr(solver, 'ConvergenceTolerance'):
            solver.ConvergenceTolerance = 1e-4
        if hasattr(solver, 'IterationsControlMaximum'):
            solver.IterationsControlMaximum = 1000
        mesh_obj.Algorithm2D = 'MeshAdapt'
        mesh_obj.Algorithm3D = 'Delaunay'
```