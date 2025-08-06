# FreeCAD建築FEM解析プロジェクト - フォルダ構成

最終更新: 2025-07-07

## 📁 ディレクトリ構造

```
/Users/kushida2/Library/CloudStorage/GoogleDrive-kushida2008@gmail.com/マイドライブ/2025code/CadProg/new3/
├── __pycache__/              # Pythonキャッシュファイル
├── fcstd_outputs/            # FCStdファイル出力 (230ファイル)
├── png_outputs/              # PNG画像出力 (276ファイル)
└── .claude/                  # Claude関連設定
```

## 📄 主要ファイル

### 🔧 コアモジュール

#### `building_fem_analysis_piloti_with_stairs_v8.py` (140KB)
- **メイン建物生成・FEM解析モジュール**
- ピロティ構造の2階建て建築物を生成
- FEM解析（CalculiX統合）
- パラメトリック設計対応
- 最新機能：バルコニー生成，個別パーツ色分け

#### `CLAUDE.md` (3.6KB)
- **AI運用5原則とプロジェクトガイドライン**
- コーディング規約
- FreeCAD開発規約
- プロジェクト管理ガイドライン

### 🎯 最適化・解析スクリプト

#### `DE.py` (12KB)
- **差分進化アルゴリズムによる最適化**
- 14次元設計変数の最適化
- コスト最小化と安全率制約
- balcony_depth: 1.0-7.0m（要更新）

#### `simple_random_batch.py` (20KB)
- **ランダムサンプリングバッチ処理**
- 並列処理対応（マルチプロセス）
- N_SAMPLES = 500
- balcony_depth: 1.0-6.0m

### 🖼️ 可視化・出力関連

#### `fcstd_to_png.py` (7.5KB)
- **単一FCStdファイルをPNGに変換**
- Blenderレンダリング
- 8パーツの色分け対応
- 4視点からの画像生成

#### `batch_fcstd_to_png.py` (9.5KB)
- **バッチPNG変換処理**
- fcstd_outputs内の全ファイルを処理
- 8パーツの色分け対応
- 各ファイル4視点（計12枚生成済み）

#### `create_html_gallery.py` (12KB)
- **HTMLギャラリー生成**
- CSVデータとPNG画像を統合表示
- 評価指標の可視化
- balcony_depth表示対応

### 📊 出力ファイル

#### 画像ファイル
- `angle1-4.png` - 最新の建物レンダリング（4視点）
- `cost_per_sqm_vs_safety_factor.png` - コスト対安全率グラフ
- `co2_per_sqm_vs_safety_factor.png` - CO2排出対安全率グラフ
- `comfort_score_vs_safety_factor.png` - 快適性対安全率グラフ
- `constructability_score_vs_safety_factor.png` - 施工性対安全率グラフ
- `de_convergence_curve.png` - DE収束曲線
- `de_multiobjective_evolution.png` - 多目的推移グラフ

#### データファイル
- `production_freecad_random_fem_evaluation.csv` (53KB) - ランダムサンプリング結果
- `de_optimization_log.csv` (10KB) - 最適化ログ
- `building_analysis_gallery.html` (190KB) - 結果ギャラリー

#### 3Dモデルファイル
- `piloti_building_fem_analysis.FCStd` (1.5MB) - 最新の建物モデル
- 各種STLファイル（Foundation, Walls, Columns等）

### 📝 ドキュメント
- `project_summary.md` (5.6KB) - プロジェクト概要と実装状況

## 🔄 最近の更新

1. **バルコニー機能の実装**
   - balcony_depthパラメータ追加（0-7m）
   - 西側壁面に設置
   - FEM解析に活荷重考慮

2. **tw_intパラメータの削除**
   - 未使用の間仕切り壁厚パラメータを全ファイルから削除

3. **パーツ色分け機能**
   - 8パーツ個別色設定（FCStd保存時の可視化は制限あり）
   - PNG出力時の色分けは実装済み

4. **バッチ処理の強化**
   - simple_random_batch.py: N_SAMPLES = 500
   - 並列処理による高速化

## 📊 統計情報

- Python スクリプト: 14ファイル
- FCStdファイル: 230個（fcstd_outputs内）
- PNG画像: 276枚（png_outputs内）
- 総ファイルサイズ: 約17MB（ルートディレクトリのみ）