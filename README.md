# AI-Arch: パラメトリック建築設計とFEM解析

建築構造のパラメトリック設計と有限要素法（FEM）による構造解析を自動化するプロジェクトです。

## 概要

本プロジェクトは、FreeCADとCalculiXを使用して、パラメトリックな建物モデルを生成し、構造解析を自動実行します。安全性、経済性、環境性、快適性、施工性の5つの観点から建築設計を総合的に評価します。

## 主な機能

- **パラメトリック建物生成**: 21個のパラメータで無限の設計バリエーション
- **自動FEM解析**: 地震荷重（0.5G）を考慮した構造解析
- **多目的評価**: 
  - 構造安全率の計算
  - 建設コストの推定
  - CO2排出量の算出
  - 居住快適性の評価
  - 施工性の評価
- **最適化アルゴリズム**: PSO、GA、DEなどによる設計最適化
- **材料選択**: コンクリートと木材（CLT）の選択可能

## ドキュメント

詳細なドキュメントは[こちら](https://jkushida.github.io/ai-arch/docs/documentation_index.html)をご覧ください。

### 主要ドキュメント

- [技術仕様書](https://jkushida.github.io/ai-arch/docs/generate_building_fem_analyze_report.html) - システムの詳細な技術文書
- [使用ガイド](https://jkushida.github.io/ai-arch/docs/test_generate_building_usage.html) - 初学者向けチュートリアル
- [解析結果ギャラリー](https://jkushida.github.io/ai-arch/docs/index.html) - 生成された建物の3Dビューと解析結果

## 必要環境

- Python 3.8以上
- FreeCAD 1.0.0以上
- CalculiX（FEMソルバー）
- Gmsh（メッシュ生成）

## プロジェクト構成

```
ai-arch/
├── files/              # メインコードとサンプルデータ
│   ├── production_fem_evaluation.csv  # 解析結果データ
│   └── png_outputs/    # 生成された建物画像
├── docs/               # プロジェクトドキュメント
│   ├── documentation_index.html  # ドキュメント一覧
│   ├── generate_building_fem_analyze_report.html
│   └── test_generate_building_usage.html
└── README.md           # このファイル
```

## ライセンス

教育・研究目的での使用は自由です。商用利用については個別にお問い合わせください。

## 連絡先

質問や提案がある場合は、[Issues](https://github.com/jkushida/ai-arch/issues)を作成してください。

---

# AI-Arch: Parametric Architectural Design and FEM Analysis

A project automating parametric architectural design and structural analysis using Finite Element Method (FEM).

## Overview

This project uses FreeCAD and CalculiX to generate parametric building models and automatically perform structural analysis. It comprehensively evaluates architectural designs from five perspectives: safety, economy, environment, comfort, and constructability.

## Key Features

- **Parametric Building Generation**: Infinite design variations with 21 parameters
- **Automated FEM Analysis**: Structural analysis considering seismic loads (0.5G)
- **Multi-objective Evaluation**: 
  - Structural safety factor calculation
  - Construction cost estimation
  - CO2 emission calculation
  - Living comfort evaluation
  - Constructability assessment
- **Optimization Algorithms**: Design optimization using PSO, GA, DE, etc.
- **Material Selection**: Choice between concrete and wood (CLT)

## Documentation

For detailed documentation, visit [here](https://jkushida.github.io/ai-arch/docs/documentation_index.html).

### Main Documents

- [Technical Specifications](https://jkushida.github.io/ai-arch/docs/generate_building_fem_analyze_report.html) - Detailed technical documentation
- [Usage Guide](https://jkushida.github.io/ai-arch/docs/test_generate_building_usage.html) - Tutorial for beginners
- [Analysis Gallery](https://jkushida.github.io/ai-arch/docs/index.html) - 3D views and analysis results

## Requirements

- Python 3.8+
- FreeCAD 1.0.0+
- CalculiX (FEM solver)
- Gmsh (mesh generation)

## License

Free for educational and research use. Please contact for commercial use.

## Contact

For questions or suggestions, please create an [Issue](https://github.com/jkushida/ai-arch/issues).