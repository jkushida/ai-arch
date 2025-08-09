# AI-Arch ドキュメント

## 🏗️ プロジェクト概要

AI-Archは、FreeCADとCalculiXを活用した建築設計最適化システムです。パラメトリックモデリング、有限要素解析（FEM）、粒子群最適化（PSO）を組み合わせ、構造的に安全で経済的、環境に優しい建築設計を自動的に探索します。

## 📚 ドキュメント一覧

### コアシステム

#### [📊 FEM解析システム詳細](generate_building_fem_analyze_report.html)
建物生成とFEM構造解析の中核となるエンジンの詳細説明。20個の設計変数、5つの評価指標、CalculiXを用いた解析プロセスについて解説しています。

#### [🚀 PSO使用ガイド](PSO_usage.html)
粒子群最適化（PSO）による設計最適化の使用方法。`pso_config.py`での設定変更、目的関数のカスタマイズ、実行方法を説明しています。

### ツールとユーティリティ

#### [🧪 テストツール使用ガイド](test_generate_building_usage.html)
`test_generate_building.py`を使った単体テストの実行方法。パラメータ調整、結果の確認、初学者向けの実験方法を解説しています。

### 分析と比較

#### [📈 最適化手法比較](fem_optimization_comparison.html)
PSO、差分進化（DE）、CMA-ESなど、各種最適化アルゴリズムの特徴と適用場面の比較分析です。

## 🚀 クイックスタート

### 1. 単一建物の評価テスト
```bash
# Mac
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/test_generate_building.py

# Windows
"C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" code/test_generate_building.py
```

### 2. PSO最適化の実行
```bash
# 最適化開始
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/pso_algorithm.py

# 別ターミナルで監視
python3 code/monitor_pso_mac.py
```

## 🔧 主要コンポーネント

### 設計変数（20個）
- **形状パラメータ（14個）**: 建物寸法、構造部材サイズ、建築的特徴
- **材料パラメータ（6個）**: 各部位の材料選択（コンクリート/木材）

### 評価指標（5つ）
1. **安全性**: 構造安全率（≥2.0必須）
2. **経済性**: 建設コスト（円/m²）
3. **環境性**: CO2排出量（kg-CO2/m²）
4. **快適性**: 空間品質スコア（0-10）
5. **施工性**: 施工難易度スコア（0-10）

## 📂 プロジェクト構造

```
ai-arch/
├── code/                    # ソースコード
│   ├── generate_building_fem_analyze.py
│   ├── pso_algorithm.py
│   ├── pso_config.py
│   └── test_generate_building.py
├── docs/                    # ドキュメント（このディレクトリ）
├── files/                   # 可視化ツール
└── pso_output/             # 最適化結果
```

## 🔗 関連リンク

- [GitHubリポジトリ](https://github.com/jkushida/ai-arch)
- [プロジェクトREADME](https://github.com/jkushida/ai-arch/blob/main/README.md)

## 📝 更新履歴

- **2025年8月**: PSO監視ツールの更新頻度調整、Windows互換性改善
- **2025年8月**: 離散値（材料選択）の最適化対応
- **2025年8月**: ドキュメントシステムの構築

---

*このドキュメントは継続的に更新されています。最新情報は[GitHubリポジトリ](https://github.com/jkushida/ai-arch)をご確認ください。*