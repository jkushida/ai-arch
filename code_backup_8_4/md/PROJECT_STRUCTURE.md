# FreeCAD建築構造最適化プロジェクト

## プロジェクト概要

このプロジェクトは，FreeCADを使用した建築構造の自動生成とFEM解析による最適化を行うシステムです．建物の設計パラメータを最適化し，構造安全性，コスト，環境負荷，施工性などを総合的に評価します．

## ディレクトリ構造

```
new3/
├── 📄 CLAUDE.md                    # AI運用5原則とプロジェクトルール
├── 📄 PROJECT_STRUCTURE.md         # このファイル
│
├── 🔧 メイン解析モジュール
│   └── generate_building_fem_analyze.py    # 建物生成とFEM解析の中核モジュール
│
├── 🤖 最適化アルゴリズム
│   ├── DE.py                       # 差分進化法による最適化
│   ├── PSO.py                      # 粒子群最適化による最適化（安全率制約付き）
│   ├── PSO2.py                     # 改良版PSO（材料選択対応，0:コンクリート/1:木材）
│   ├── NSGA2.py                    # NSGA-II多目的最適化（安全性vs経済性）
│   ├── simple_random_batch.py      # ランダムサンプリングによるバッチ解析
│   ├── simple_random_batch2.py     # 改良版ランダムサンプリング（N_SAMPLES=400，材料0-1）
│   └── simple_random_batch_partial.py # 部分的なバッチ処理（問題のあるサンプルをスキップ）
│
├── 🛠️ ユーティリティ
│   ├── batch_fcstd_to_png.py      # FCStdファイルの一括PNG変換（材料色対応）
│   ├── fcstd_to_png.py            # 単一FCStdファイルのPNG変換
│   ├── fix_gui_colors.py          # FreeCAD GUIでの材料別色修正スクリプト
│   ├── apply_colors_simple.py     # シンプルな色適用スクリプト
│   ├── apply_material_colors.py   # 材料別色適用スクリプト
│   ├── apply_material_colors_console.py # コンソール版材料色適用
│   ├── create_html_gallery.py     # 解析結果のHTMLギャラリー生成
│   ├── regenerate_sample1.py      # sample1の画像再生成スクリプト
│   ├── check_gmsh_threads.py      # Gmshマルチスレッド確認（詳細版）
│   ├── check_gmsh_threads_simple.py # Gmshマルチスレッド確認（簡易版）
│   ├── clean_csv.py               # CSVファイルのNaN除去
│   ├── check_csv_data.py          # CSVデータ確認ツール
│   └── generate_safety_analysis_html.py # 安全性解析HTML生成
│
├── 📚 ドキュメント
│   ├── generate_building_fem_analyze_report.md # generate_building_fem_analyze.pyの詳細レポート
│   ├── gmsh_options_explanation.md # Gmshメッシュ生成オプションの詳細説明
│   ├── freecad_windows_execution.md # WindowsでのFreeCAD実行ガイド
│   ├── 材料選択機能の使い方.md   # 材料選択機能のマニュアル
│   └── deploy_github_pages.md     # GitHub Pagesデプロイガイド
│
├── 🌐 Webインターフェース
│   ├── building_analysis_gallery.html # 建物解析結果のギャラリー
│   ├── pso_simulator.html         # PSO最適化シミュレータ（最新版，インタラクティブ3D/2D可視化）
│   ├── pso_simulator_compact.html # PSO最適化シミュレータ（コンパクト版）
│   ├── safety_analysis_interactive.html # 安全性解析インタラクティブビューア
│   ├── safety_analysis_interactive_2col.html # 安全性解析（2列レイアウト）
│   └── safety_analysis_interactive_2col_csv.html # 安全性解析（CSVデータ対応版）
│
├── 📊 出力ファイル
│   ├── fcstd_outputs/             # FreeCAD 3Dモデルファイル（.FCStd）
│   ├── png_outputs/               # 3Dモデルの画像ファイル
│   ├── *.csv                      # 解析結果データ
│   ├── *.png                      # グラフ・図表
│   └── *.html                     # 結果ギャラリー
│
├── 🎯 FreeCADマクロ
│   ├── ApplyColors.FCMacro        # 材料別色適用マクロ（シンプル版）
│   └── ApplyColorsComplete.FCMacro # 材料別色適用マクロ（視点調整付き）
│
├── 🧪 テストスクリプト
│   ├── test_generate_building.py  # 建物生成・評価関数テスト（CSV追記モード，.FCBak自動削除）
│   ├── test_fem_reproducibility.py # FEM解析再現性テスト
│   ├── test_fem_size_effect.py   # メッシュサイズ影響テスト
│   ├── test_color_debug.py        # 色適用デバッグテスト
│   ├── test_color_diffuse.py      # DiffuseColor設定テスト
│   ├── test_material_colors.py    # 材料色適用テスト
│   ├── test_material_debug.py     # 材料デバッグテスト
│   ├── test_material_simple.py    # シンプル材料テスト
│   ├── test_minimal_case.py       # 最小テストケース
│   ├── test_simple_material.py    # 簡易材料テスト
│   └── test_sample95.py           # sample95特定テスト
│
├── 📁 ai-arch/                    # GitHubリポジトリ (https://github.com/jkushida/ai-arch)
│   ├── LICENSE                    # MITライセンス
│   ├── README.md                  # リポジトリの説明
│   ├── index.html                 # GitHub Pagesホームページ
│   ├── pso_simulator.html         # PSO最適化シミュレータ
│   ├── safety_analysis_interactive_2col_csv.html # 安全性解析ビューア
│   ├── building_analysis_gallery_csv.html # 建物解析ギャラリー
│   ├── production_freecad_random_fem_evaluation.csv # 300サンプルの解析結果
│   ├── png_outputs/               # 1200枚の建物画像（300サンプル×4ビュー）
│   ├── files/                     # HTMLファイルとPNG画像
│   │   ├── building_analysis_gallery_csv.html # 材料情報表示対応版（CLT対応済）
│   │   ├── safety_analysis_interactive_2col_csv.html # 材料ベース色分け対応版（CLT対応済）
│   │   ├── production_freecad_random_fem_evaluation.csv
│   │   └── png_outputs/            # 建物画像（300サンプル×4ビュー）
│   └── files2/                    # 材料選択対応版データ（2025-07-21追加）
│       ├── building_analysis_gallery_csv.html # 材料情報表示対応版
│       └── safety_analysis_interactive_2col_csv.html # 材料ベース色分け対応版
│
├── 🚀 バッチ処理
│   └── batch_simple_random.sh     # 500サンプルを100サンプルずつバッチ処理
│
└── 🗄️ データファイル
    ├── *.stl                      # 3Dモデルの部品データ
    ├── *.FCStd                    # FreeCADプロジェクトファイル
    └── problematic_samples.json   # 問題のあるサンプルのリスト
```

## 主要ファイルの説明

### 中核モジュール

#### `generate_building_fem_analyze.py`
- **役割**: 建物の3Dモデル生成とFEM構造解析
- **主要機能**:
  - パラメトリックな建物モデル生成（ピロティ構造，階段付き）
  - FEM解析（応力，変位，安全率の計算）
  - 経済性，環境性，快適性，施工性の総合評価
- **メッシュ設定**:
  - CharacteristicLengthMax: 600.0 mm
  - CharacteristicLengthMin: 200.0 mm
  - NumThreads: 2（安定性向上，0だと全コア使用）
- **テストコード**: 直接実行時のみ動作（バッチ処理時は無効）

### 最適化アルゴリズム

#### `DE.py`（差分進化法）
- **パラメータ**:
  - 個体数: 15
  - 世代数: 20
  - F（スケーリング係数）: 0.5
  - CR（交叉確率）: 0.9
- **タイムアウト**: 120秒/評価

#### `PSO.py`（粒子群最適化）
- **パラメータ**:
  - 粒子数: 15
  - 反復回数: 20
  - W（慣性重み）: 0.7
  - C1, C2（加速係数）: 1.5
- **タイムアウト**: 120秒/評価
- **制約**: 安全率 >= 2.0

#### `PSO2.py`（改良版粒子群最適化）
- **特徴**:
  - 適応的慣性重み（0.9から0.4へ線形減少）
  - 定期的な多様性注入（5反復ごと）
  - 改善率に基づく早期終了機能
  - 材料選択（0:コンクリート/1:木材）対応
  - パラメータ範囲をsimple_random_batch2.pyと統一

#### `NSGA2.py`（多目的最適化）
- **最適化目標**:
  - 安全率の最大化
  - コストの最小化
- **パラメータ**:
  - 個体数: 100
  - 世代数: 100
  - 交叉率: 0.9
  - 突然変異率: 1/n_vars

#### `simple_random_batch.py`
- **サンプル数**: 可変（デフォルト300）
- **タイムアウト**: シングルプロセスモードで60秒/評価
- **並列処理**: 現在は無効化（NUM_PROCESSES = 1に固定）
- **メモリ管理**: 
  - 毎評価後にガベージコレクション
  - 2サンプルごとに徹底的なガベージコレクション
  - 10サンプルごとに詳細な進捗レポート表示
- **重複実行防止**: .simple_random_batch_runningマーカーファイル使用
- **CSV出力**: UTF-8 BOM付き（macOS Excel対応）
- **パラメータ範囲（更新版）**:
  - スパン: 8-15m
  - スラブ厚: 180-500mm（床），150-400mm（屋根）
  - 柱断面: 300-900mm（幅），300-800mm（高さ）
  - 外壁厚: 150-350mm
- **材料パラメータ**: 材料選択（0=コンクリート，1=木材）を各パーツに指定可能

#### `simple_random_batch2.py`
- **サンプル数**: 400（N_SAMPLES=400）
- **材料選択**: 0（コンクリート）または1（木材）のみ
- **屋根形状**: roof_morph範囲を0.0-1.0に拡張（完全なかまぼこ屋根対応）
- **パラメータ範囲**: PSO2.pyと統一された安全性重視の範囲
- **CSVエンコーディング**: utf-8-sig（Mac Excel対応）
- **fcstd_path**: 相対パスで保存

#### `simple_random_batch_partial.py`
- **用途**: 問題のあるサンプルをスキップして部分的にバッチ処理
- **スキップリスト**: sample201など，セグメンテーション違反を起こすサンプル

### 設計パラメータ範囲

| パラメータ | 説明 | 最小値 | 最大値 | 単位 |
|-----------|------|--------|--------|------|
| Lx | 建物幅 | 8.0 | 20.0 | m |
| Ly | 建物奥行き | 8.0 | 20.0 | m |
| H1 | 1階高さ | 2.5 | 4.5 | m |
| H2 | 2階高さ | 2.5 | 4.0 | m |
| tf | 床スラブ厚 | 120 | 500 | mm |
| tr | 屋根スラブ厚 | 100 | 400 | mm |
| bc | 柱幅 | 200 | 800 | mm |
| hc | 柱高さ | 200 | 800 | mm |
| tw_ext | 外壁厚 | 100 | 350 | mm |

※ simple_random_batch.pyの低安全率モードでは以下の範囲を使用：
- Lx, Ly: 10.0-15.0m（大スパン）
- tf: 200-350mm（薄め）
- tr: 180-300mm（薄め）
- bc, hc: 300-600mm（細め）
- tw_ext: 150-250mm（薄め）
| wall_tilt_angle | 壁傾斜角 | -40.0 | 40.0 | 度 |
| window_ratio_2f | 2階窓面積比 | 0.1 | 0.9 | - |
| roof_morph | 屋根形状 | 0.0 | 1.0 | - |
| roof_shift | 屋根シフト | -0.7 | 0.7 | - |
| balcony_depth | バルコニー奥行 | 1.0 | 6.0 | m |

## 評価指標

1. **構造安全性**
   - 安全率（目標: 2.5以上）
   - 最大応力，最大変位

2. **経済性**
   - 建設コスト（円/m²）
   - 総工費

3. **環境性**
   - CO2排出量（kg-CO2/m²）

4. **快適性**
   - 床面積，天井高，開口率

5. **施工性**
   - 標準化度，アクセス性，重量制限

## 主要な変更履歴

### 2025-07-23
- **generate_building_fem_analyze_report.mdを作成**：
  - generate_building_fem_analyze.pyの詳細レポート
  - 使用方法セクションを追加（パラメータ辞書からの評価方法）
  - パラメータ範囲と推奨値の表を追加
  - 材料選択機能の詳細（CLTは現在未実装）
  - FEM使用CPU数：NumThreads = 2（安定性向上， 0だと全コア）
- **HTMLファイルのCLT対応**：
  - files/building_analysis_gallery_csv.html
  - files/safety_analysis_interactive_2col_csv.html
  - 材料表示をコンクリート（0），木材（1），CLT（2）に対応
- **simple_random_batch2.pyの改善**：
  - CSVエンコーディングをutf-8-sigに変更（Macでの文字化け対策）
  - fcstd_pathを絶対パスから相対パスに変換

### 2025-07-21
- **HTMLビジュアライゼーションの改良**：
  - `files2/building_analysis_gallery_csv.html`に材料情報表示機能追加
  - `files2/safety_analysis_interactive_2col_csv.html`に材料ベース色分け機能追加
  - 木材使用量に基づくグラデーション（灰色→濃い赤茶）
  - 設計変数テーブルに材料選択情報（0:コンクリート，1:木材）を追加
- **最適化アルゴリズムの統一**：
  - `PSO2.py`のパラメータ範囲を`simple_random_batch2.py`と統一
  - 材料選択を3値（0/1/2）から2値（0/1）に変更
  - 安全性を重視したパラメータ範囲に調整
- **test_generate_building.pyの機能拡張**：
  - CSV追記モードの実装（test_results.csv）
  - タイムスタンプ列を第1列に追加
  - evaluation_time_sを小数点以下第1位に丸め
  - FCStdファイル名にタイムスタンプ付与オプション
  - .FCBakファイル（FreeCADバックアップ）の自動削除機能

### 2025-07-19
- **材料別色表示システムの実装**：
  - `generate_building_fem_analyze.py`から色関連コード（PART_COLORS，set_part_color等）を削除
  - GUI専用の色適用スクリプト`fix_gui_colors.py`を作成
  - FreeCADマクロ（ApplyColors.FCMacro，ApplyColorsComplete.FCMacro）を作成
  - DisplayMode「Flat Lines」でエッジ表示を維持しつつ材料色を表示
- **材料パラメータの実装**：
  - 各パーツ（柱，床，壁等）ごとに材料（0:コンクリート，1:木材）を指定可能
  - 材料によって強度，コスト，CO2排出量が変化
  - リサイクル率も材料別に設定（床50%，壁60%等）
- **テストスクリプトの追加**：
  - `test_generate_building.py`に材料パラメータ対応
  - FEM解析再現性テスト（変動率1%未満を確認）
  - 木造とコンクリート構造の安全率比較分析
- **最適化アルゴリズムの追加**：
  - `PSO2.py`：改良版PSO（適応慣性重み，定期的な多様性注入）
  - `NSGA2.py`：多目的最適化（安全性vs経済性）
- **コストとCO2の相関分析**：
  - 相関係数0.994の強い正の相関を確認
  - 材料使用量が両方の主要因であることを特定

### 2025-07-12
- `generate_building_fem_analyze.py`の修正：
  - テスト実行条件を修正（`if __name__ == "__main__":`のみに変更）
  - バッチ処理時の不要なログ出力を削除
  - 快適性評価の改善（簡単に10点満点にならないよう調整）
  - 経済性のcomplexity_factor計算バグ修正
  - 床面積取得の修正（span_lengthからLx/Lyに変更）
- `simple_random_batch.py`の更新：
  - パラメータ範囲を拡大（より広い設計空間の探索）
  - 重複実行防止メッセージに削除コマンドを追加
  - メモリクリーンアップ頻度を調整（2サンプルごと）
- `test_generate_building.py`を新規作成：
  - generate_building_fem_analyze.pyのテストスクリプト
  - 全評価指標の結果表示
  - CSV追記モード対応（実行のたびに結果を追加）
  - タイムスタンプ列を第1列に追加
  - evaluation_time_sを小数点以下第1位に丸め
  - FCStdファイル名にタイムスタンプ付与
  - .FCBakファイル自動削除機能（関連ファイルのみ）
- `gmsh_options_explanation.md`を新規作成：
  - Gmshメッシュ生成オプションの詳細説明
  - 安全な実行のための推奨設定（NumThreads = 2）
  - トラブルシューティングガイド
- 推奨Gmsh設定の変更：
  - General.NumThreads: 0 → 2（segmentation fault回避）
  - 決定論的メッシュ生成のための設定追加
- GitHubへのデータアップロード：
  - ai-archリポジトリに300サンプルの解析結果をアップロード
  - png_outputs/: 1200枚の建物画像（300サンプル×4ビュー）
  - production_freecad_random_fem_evaluation.csv: FEM解析結果データ

### 2025-07-11
- `simple_random_batch.py`のメモリ管理を大幅改善：
  - FreeCADドキュメントのオブジェクト明示的削除
  - より頻繁なガベージコレクション（毎評価後）
  - メモリ使用量監視と自動クリーンアップ機能
  - CSV出力にUTF-8 BOM追加（macOS Excel文字化け対策）
  - 低安全率を狙うパラメータ範囲に調整
- `pso_simulator.html`を大幅更新：
  - PSO（粒子群最適化）の対話型可視化シミュレータ
  - 3Dグラフと2D等高線マップのリアルタイム表示
  - 4つの目的関数対応（Sphere，Rastrigin，Rosenbrock，Ackley）
  - Ackley関数の3D表示Z軸スケールを9.0に拡大
  - 全体の最良解(gbest)と個人の最良解(pbest)の表示
  - 収束状態の自動判定（最良値1e-6未満で収束）
  - 初期速度を探索範囲の50%に設定
  - Rosenbrock関数の2D軸刻み幅を0.5に調整
  - GitHub Pages（https://jkushida.github.io/ai-arch/pso_simulator.html）に公開

### 2025-01-09
- バッチ処理中のセグメンテーション違反に対応するため，以下を実装：
  - `batch_simple_random.sh`: 100サンプルごとのバッチ処理スクリプト
  - `simple_random_batch_partial.py`: 問題のあるサンプルをスキップする機能
  - タイムアウト処理の強化（signal.alarmを使用）
- PSO最適化シミュレータのHTML版を追加
- `batch_fcstd_to_png.py`の制限を解除（全ファイル処理対応）

### 2025-01-08
- ファイル名を`building_fem_analysis_piloti_with_stairs_v8.py`から`generate_building_fem_analyze.py`に変更
- 関連ファイルの参照も同時に更新
- Gmshのスレッド数設定を1から0（自動検出）に変更
- 日本語フォント設定を追加（文字化け対策）

## 使用方法

### 基本的な実行

#### Mac
```bash
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd [スクリプト名].py
```

#### Windows
```bash
"C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe" [スクリプト名].py
```

#### Linux
```bash
freecadcmd [スクリプト名].py
```

**注意**: 上記のパスはお使いのPCの環境に合わせて調整してください．

### 例: ランダムサンプリング
- **Mac**: `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd simple_random_batch.py`
- **Windows**: `"C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe" simple_random_batch.py`
- **Linux**: `freecadcmd simple_random_batch.py`

### 例: 差分進化法による最適化
- **Mac**: `/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd DE.py`
- **Windows**: `"C:\Program Files\FreeCAD 0.21\bin\FreeCADCmd.exe" DE.py`
- **Linux**: `freecadcmd DE.py`

## 依存関係

### 必須
- FreeCAD 1.0.0以上
- Python 3.x（FreeCAD内蔵）
- CalculiX（FEM解析ソルバー）

### オプション
- gmshtools（メッシュ生成の高速化）
- matplotlib（グラフ生成）
- pandas（データ処理）
- numpy（数値計算）

## 主要ファイルの依存関係

### 依存関係図

```
                    generate_building_fem_analyze.py
                    （中核モジュール：建物生成・FEM解析）
                              ↑
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        │                     │                     │
   DE.py │                PSO.py               simple_random_batch.py
（差分進化法）         （粒子群最適化）          （ランダムサンプリング）
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ↓
                    ┌─────────────────────┐
                    │   出力ファイル群    │
                    ├─────────────────────┤
                    │ *.csv（解析結果）   │
                    │ *.FCStd（3Dモデル） │
                    │ *.png（グラフ）     │
                    └─────────────────────┘
                              ↓
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
batch_fcstd_to_png.py  create_html_gallery.py  generate_safety_analysis_html.py
（PNG画像変換）        （HTMLギャラリー生成）    （安全性解析HTML生成）
```

### モジュール間の依存関係詳細

#### 1. **中核モジュール**
- `generate_building_fem_analyze.py`
  - 他のすべての解析モジュールが依存
  - 提供する関数：`evaluate_building_from_params()`
  - FreeCAD API，CalculiX（FEMソルバー）に依存

#### 2. **最適化モジュール**
- `DE.py`（差分進化法）
  - `generate_building_fem_analyze`をインポート
  - 出力：`de_optimization_log.csv`，`de_convergence_curve.png`
  
- `PSO.py`（粒子群最適化）
  - `generate_building_fem_analyze`をインポート
  - 出力：`pso_optimization_log.csv`，`pso_convergence.png`，`pso_progress.txt`，`pso_settings.csv`
  
- `simple_random_batch.py`（ランダムサンプリング）
  - `generate_building_fem_analyze`をインポート
  - 出力：`production_freecad_random_fem_evaluation.csv`

### ユーティリティ・色処理モジュール

#### `fix_gui_colors.py`
- **役割**: FreeCAD GUIでの材料別色修正スクリプト
- **機能**:
  - 材料情報の自動判定（MaterialTypeプロパティから）
  - パーツごとに異なる木材色の適用
  - DisplayMode「Flat Lines」でエッジ表示
  - 視点の自動調整（アイソメトリック＋全体表示）

#### `apply_colors_simple.py`/`apply_material_colors.py`
- **役割**: 材料別色適用のテストスクリプト
- **用途**: 色適用機能の開発・デバッグ用

### FreeCADマクロ

#### `ApplyColors.FCMacro`
- **役割**: 材料別色適用マクロ（シンプル版）
- **機能**: MaterialTypeプロパティから色を自動適用

#### `ApplyColorsComplete.FCMacro`  
- **役割**: 材料別色適用マクロ（完全版）
- **機能**: 
  - 色適用に加えて視点調整（ViewFit，viewIsometric）
  - 処理結果のメッセージボックス表示
  - 材料不明時のデフォルト処理（コンクリートとして扱う）

#### 3. **後処理モジュール**
- `batch_fcstd_to_png.py`
  - FreeCAD APIに依存
  - Blenderを使用（外部依存）
  - 入力：`fcstd_outputs/*.FCStd`
  - 出力：`png_outputs/*.png`
  - **更新**: MaterialTypeプロパティから材料色を読み取って適用

- `create_html_gallery.py`
  - pandas，matplotlibに依存
  - 入力：`production_freecad_random_fem_evaluation.csv`，`png_outputs/`
  - 出力：`building_analysis_gallery.html`

- `generate_safety_analysis_html.py`
  - 入力：CSVファイル
  - 出力：インタラクティブHTMLビューア

#### 4. **テストスクリプト**
- `test_generate_building.py`：建物生成・評価関数テスト（材料パラメータ対応）
- `test_fem_reproducibility.py`：FEM解析再現性テスト（変動率1%未満を確認）
- `test_fem_size_effect.py`：メッシュサイズ影響テスト
- 色関連テスト：
  - `test_color_debug.py`，`test_color_diffuse.py`
  - `test_material_colors.py`，`test_material_simple.py`
  - `fix_balcony_color.py`：バルコニー色修正テスト

#### 5. **その他のユーティリティ**
- `clean_csv.py`：CSVファイルのNaN除去
- `check_gmsh_threads.py`：Gmshマルチスレッド診断
- `check_csv_data.py`：CSVデータ確認ツール
- `generate_safety_analysis_html.py`：安全性解析HTML生成

### 外部依存関係

```
プロジェクト
    ├── FreeCAD (>= 1.0.0)
    │   ├── Part（形状モデリング）
    │   ├── Fem（有限要素解析）
    │   └── Mesh（メッシュ生成）
    ├── CalculiX（FEMソルバー）
    ├── Gmsh（メッシュ生成）
    ├── Python標準ライブラリ
    │   ├── csv
    │   ├── json
    │   ├── signal
    │   └── multiprocessing
    └── 外部Pythonパッケージ
        ├── numpy
        ├── pandas
        ├── matplotlib
        └── Blender（PNG生成時のみ）
```

### データフロー

1. **パラメータ生成**
   - 最適化アルゴリズム（DE/PSO）またはランダム生成
   
2. **FEM解析**
   - `generate_building_fem_analyze.py`で3Dモデル生成→FEM解析
   
3. **結果保存**
   - CSV：数値データ（安全率，コスト，CO2等）
   - FCStd：3Dモデルファイル
   
4. **可視化**
   - PNG：3Dモデルの画像
   - HTML：インタラクティブなギャラリーとグラフ

## 注意事項

1. **メモリ使用**: FEM解析は大量のメモリを使用します
2. **実行時間**: 複雑なモデルでは解析に数分かかることがあります
3. **並列処理**: FreeCAD環境では自動的にシングルプロセスモードになります
4. **ファイル保存**: fcstd_outputs/ディレクトリに3Dモデルが保存されます

## トラブルシューティング

- **文字化け**: 日本語フォントが設定されているか確認
- **メッシュ生成エラー**: メッシュサイズを大きくして再試行
- **タイムアウト**: EVALUATION_TIMEOUTの値を増やす
- **メモリ不足**: サンプル数を減らすか，モデルを簡略化
- **Segmentation fault**: Gmshの`General.NumThreads`を1または2に設定
- **重複実行エラー**: `rm .simple_random_batch_running`でマーカーファイルを削除

## 注記
CSVファイル内の数値について：画像表示と実際の値が異なっているように見える場合，単位はすべてミリメートル（mm）で記録されています．
例：
- tf=199 → 床スラブ厚 199mm（実際の設計値）
- tr=247 → 屋根スラブ厚 247mm（実際の設計値）
- bc=849 → 柱幅 849mm（実際の設計値）
- hc=587 → 柱高さ 587mm（実際の設計値）
- tw_ext=235 → 外壁厚 235mm（実際の設計値）

---
*最終更新: 2025-07-23*