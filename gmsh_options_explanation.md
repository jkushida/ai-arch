# Gmshメッシュ生成オプション詳細説明

## 概要
FreeCADでFEM解析を行う際，Gmshを使用してメッシュ生成を行います．以下は，より安定した解析を実現するためのGmshオプション設定の詳細説明です．

## オプション設定内容

```python
gmsh_tools.Options = "".join([
    "General.RandomSeed = 12345;",
    "Mesh.ElementDimension = 3;",
    "Mesh.VolumeEdges = 1;",
    "Mesh.Algorithm3D = 1;",
    "Mesh.CharacteristicLengthFactor = 1.0;",
    "Mesh.RandomFactor = 0.0;",
    "Mesh.Smoothing = 10;",
    "Mesh.Optimize = 1;",
    "Mesh.OptimizeNetgen = 1;",
    "General.NumThreads = 2;"
])
```

## 各オプションの詳細説明

### 1. General.RandomSeed = 12345
- **説明**: メッシュ生成の乱数シードを固定
- **効果**: 同じ入力に対して常に同じメッシュを生成（再現性の確保）
- **推奨理由**: デバッグやトラブルシューティングが容易になる

### 2. Mesh.ElementDimension = 3
- **説明**: 生成する要素の次元を3次元に設定
- **効果**: 3D体積メッシュ（テトラヘドラル要素）を生成
- **必須理由**: FEM解析には3次元要素が必要

### 3. Mesh.VolumeEdges = 1
- **説明**: 体積要素のエッジを表示/保存
- **効果**: メッシュの視覚化とデバッグが容易になる
- **注意**: ファイルサイズが若干増加する

### 4. Mesh.Algorithm3D = 1
- **説明**: 3Dメッシュ生成アルゴリズムの選択
- **選択肢**:
  - 1: MeshAdapt（適応的メッシュ）← **現在の設定**
  - 2: Delaunay（デローニー分割）
  - 3: Frontal（前進前線法）
  - 4: LcMesh
  - 5: HXT（並列テトラヘドラル）
  - 6: MMG
  - 7: Netgen
- **推奨理由**: MeshAdaptは安定性が高く，複雑な形状にも対応可能

### 5. Mesh.CharacteristicLengthFactor = 1.0
- **説明**: メッシュサイズの全体的なスケールファクター
- **効果**: 1.0で標準サイズ，小さくすると細かいメッシュ
- **注意**: 細かすぎるとメモリ使用量が増大

### 6. Mesh.RandomFactor = 0.0
- **説明**: メッシュ生成時のランダム性の度合い
- **効果**: 0.0で完全に決定論的なメッシュ生成
- **推奨理由**: 再現性と安定性の向上

### 7. Mesh.Smoothing = 10
- **説明**: メッシュ平滑化の反復回数
- **効果**: メッシュ品質の向上（歪んだ要素の改善）
- **トレードオフ**: 処理時間が増加

### 8. Mesh.Optimize = 1
- **説明**: 基本的なメッシュ最適化の有効化
- **効果**: 要素の品質向上
- **推奨理由**: FEM解析の精度向上

### 9. Mesh.OptimizeNetgen = 1
- **説明**: Netgenアルゴリズムによる追加最適化
- **効果**: さらなるメッシュ品質の向上
- **注意**: 処理時間が増加する可能性

### 10. General.NumThreads = 2 ⚠️ **最重要設定**
- **説明**: 使用するCPUスレッド数の制限
- **デフォルト**: 0（全コア使用）
- **推奨値**: 1または2
- **理由**:
  - segmentation fault回避
  - メモリ使用量の抑制
  - 他のプロセスとの競合防止
  - システム全体の安定性向上

## 安全な実行のための追加推奨事項

### 環境変数の設定
```bash
export OMP_NUM_THREADS=2  # OpenMPスレッド数も制限
export MKL_NUM_THREADS=2  # Intel MKLを使用している場合
```

### メモリ制限の設定
```bash
ulimit -v 4000000  # 仮想メモリを4GBに制限（例）
```

### 段階的なアプローチ
1. まずNumThreads=1で試す
2. 安定していればNumThreads=2に増やす
3. それでも問題があれば，メッシュサイズを大きくする

## トラブルシューティング

### segmentation faultが発生する場合
1. `General.NumThreads = 1;` に変更
2. メッシュサイズを大きくする（CharacteristicLengthMaxを増やす）
3. Mesh.Algorithm3D を 2（Delaunay）に変更してみる

### メモリ不足の場合
1. Mesh.Smoothing を 5 以下に減らす
2. Mesh.OptimizeNetgen を 0 に設定
3. バッチサイズを減らす（1サンプルずつ処理）

## まとめ
これらの設定により，Gmshメッシュ生成の安定性と再現性が大幅に向上します．特に`General.NumThreads`の制限は，FreeCADでのsegmentation fault回避に極めて重要です．