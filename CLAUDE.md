# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

このプロジェクトは、FreeCADとCalculiXを使用した建築設計最適化システムです。主な機能：
- パラメトリック建築物生成（かまぼこ屋根対応）
- FEM構造解析による安全性評価
- 粒子群最適化（PSO）による設計最適化
- 3Dモデルの可視化とエクスポート

## 開発環境とコマンド

### FreeCAD環境での実行
```bash
# メインスクリプトの実行（FreeCADコマンドラインモード）
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/random_building_sampler.py

# 建物生成とFEM解析
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/generate_building_fem_analyze.py

# PSO最適化の実行
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/PSO.py

# FCStdファイルからPNG画像生成
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/fcstd_to_png.py <input.FCStd>

# バッチ処理でPNG生成
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/batch_fcstd_to_png.py
```

### PSO実行時のモニタリング
```bash
# PSO実行中のリアルタイムモニタリング（Mac版）
python3 code/monitor_pso_mac.py

# PSO実行中のリアルタイムモニタリング（Windows版）
python code/monitor_pso_win.py

# PSO実行中のリアルタイムモニタリング（コンソールのみ）
python3 code/monitor_pso_mac.py --console
```

### テストの実行
```bash
# 建物生成機能のテスト
/Applications/FreeCAD.app/Contents/Resources/bin/freecadcmd code/test_generate_building.py
```

## アーキテクチャと主要コンポーネント

### 1. generate_building_fem_analyze.py
- **役割**: コア建築物生成とFEM解析エンジン
- **主要クラス**: `BuildingDesigner`
- **機能**:
  - パラメトリック建築物モデリング（1階柱構造、2階壁構造、かまぼこ屋根）
  - CalculiX統合によるFEM解析
  - 安全性・経済性・環境負荷・快適性・施工性の評価
- **重要定数**:
  - 地震係数: 0.5G
  - 木材許容応力: 6.0 MPa
  - 変形制限係数: 0.3

### 2. random_building_sampler.py
- **役割**: パラメータ空間のランダムサンプリングと評価
- **パラメータ数**: 20個（形状14個、材料6個）
- **出力**:
  - CSVファイル（`production_freecad_random_fem_evaluation.csv`）
  - FCStdファイル（`sample_*.FCStd`）
  - FEM解析結果

### 3. PSO.py / pso_algorithm.py
- **役割**: 粒子群最適化による設計最適化
- **パラメータ**:
  - 粒子数: 10
  - 反復回数: 10 (MAX_ITER)
  - 慣性重み: 0.4〜0.9（線形減少）
- **最適化目標**: 統合指標（安全性、経済性、環境負荷の重み付け合計）
- **出力ディレクトリ**: `pso_output/`
  - `csv/`: 最適化ログ、設定ファイル
  - `images/`: 収束グラフ、散布図
  - `fcstd/`: 3Dモデルファイル

### 4. モニタリングツール（monitor_pso_mac.py / monitor_pso_win.py）
- **役割**: PSO実行のリアルタイムモニタリング
- **機能**:
  - Web UIでの進捗表示（http://localhost:5001）
  - 粒子群の評価値プロット
  - 収束グラフの表示
  - 設定ファイルの確認
- **更新頻度**: 1分ごと（60秒）
- **必要パッケージ**: Flask, matplotlib, PIL

### 5. 可視化ツール（FC_macro/）
- `ApplyColors.FCMacro`: 基本的な色付け
- `ApplyColorsComplete.FCMacro`: 詳細な材質別色付け

## ワークフロー管理

### 4段階フロー（.claude_workflow/）
1. **要件定義** → requirements.md
2. **設計** → design.md  
3. **タスク化** → tasks.md
4. **実行** → 各タスクの実施

### 実行ルール
- 各フェーズ開始時に前段階のmdファイルを読み込む
- フェーズ完了時に必ず確認を取る
- エラーは解決してから次へ進む
- 指示にない機能を勝手に追加しない

## ドキュメント記述規則

### 句読点の統一
すべてのMarkdownファイル（*.md）では、句読点を以下に統一します:
- **読点**: `,` (半角カンマ)
- **句点**: `.` (半角ピリオド)

## ディレクトリ構造

```
AI_arch/
├── code/                    # ソースコード（GitHub対象）
├── files/                   # 出力ファイル（GitHub対象）
│   ├── png_outputs/        # PNG画像出力
│   └── *.html             # 可視化HTMLファイル
├── docs/                   # ドキュメント（GitHub対象）
├── FC_macro/              # FreeCADマクロ（GitHub対象）
└── .claude_workflow/      # ワークフロー管理
```

## GitHub連携ルール

### アップロード対象フォルダ（4つ）
以下の4つのフォルダのみGitHubと連携します：
1. **code/** - Pythonソースコード、設定ファイル
2. **docs/** - HTMLドキュメント、Markdownファイル、画像
3. **FC_macro/** - FreeCADマクロファイル
4. **files/** - 出力ファイル、HTML可視化ツール、PNG画像

### トップディレクトリのMarkdownファイル
- **README.md** - プロジェクトルートでGitHubにアップロードする唯一のMarkdownファイル
- **CLAUDE.md** - ローカル専用（GitHubにアップロードしない）

### アップロード対象外
- backup/ - バックアップファイル
- sampling_code/ - サンプリング用コード
- *.FCStd - FreeCAD 3Dモデルファイル（サイズが大きいため）
- *.FCBak - FreeCADバックアップファイル
- test_results.csv - ローカルテスト結果
- CLAUDE.md - Claude Code用設定ファイル（ローカル専用）
- その他の一時ファイル

## 技術的注意事項

### FreeCAD/FEM依存
- FreeCADモジュールが必要（App, Part, Fem, ObjectsFem）
- CalculiXソルバーが必要（ccxtools）
- 実行マーカーファイル（`.random_building_sampler_running`）でプロセス管理

### パフォーマンス考慮事項
- FEM解析は計算量が多い（1建物あたり数分）
- 大量サンプリング時はバッチ処理推奨
- VERBOSE_OUTPUT変数でログ出力制御可能

### データ形式
- 入力: パラメータ辞書（20個の設計変数）
- 出力: CSV（評価指標）、FCStd（3Dモデル）、PNG（可視化）

## PSOでの変数固定方法

### 定義域による変数固定
PSO.pyでは、パラメータの定義域（上限・下限）を同じ値に設定することで、その変数を固定できます。

```python
# 例1: 材料を木材（1.0）に固定
"material_roof": (1.0, 1.0),    # 屋根材料（固定：木材）

# 例2: 材料をコンクリート（0.0）に固定
"material_columns": (0.0, 0.0),  # 柱材料（固定：コンクリート）

# 例3: 寸法を固定値に設定
"tf": (500, 500),               # 床スラブ厚（固定：500mm）
```

### 固定の仕組み
1. **初期化**: 上限=下限なので、初期値は必ずその値になる
2. **速度計算**: 探索範囲が0なので、速度成分も0になる
3. **位置更新**: 速度が0なので位置が変化しない
4. **境界処理**: 仮に位置が動いても、境界処理で固定値に戻される

### 活用例
- 構造安全性のため特定部材を固定材料にする
- 設計制約により特定寸法を固定する
- 最適化変数を減らして計算時間を短縮する

## 最近の更新履歴

### 2025年8月10日 - test_generate_building.pyの強化とドキュメント整備
- `test_generate_building.py`にパラメータ推奨範囲の追加
- 入力パラメータ（20個）と出力評価指標（5項目）の詳細ドキュメント化
- FEM解析の乱数性による結果変動についての注意事項を追記
- `test_generate_building_usage.md`と`student_exercises_v2.html`の作成
- CSV出力形式の標準化とFCBakファイル自動削除機能の実装

### 2025年8月5日 - PSO監視ツールの更新頻度調整
- `monitor_pso_mac.py`の更新間隔を5秒から1分（60秒）に変更
- グラフ更新メッセージも「1分ごと」に修正
- サーバー負荷軽減とより安定した監視を実現

### 2025年8月 - クロスプラットフォーム対応と離散値最適化

#### PSO.py - 離散値（材料選択）の最適化対応
- 材料パラメータ6個を最適化対象に追加（連続値0.0-1.0で表現）
- 連続値を離散値に変換する仕組みを実装：
  - 0.5未満 → 0（コンクリート）
  - 0.5以上 → 1（木材）
- 定義域による変数固定機能（上限=下限で固定）

#### PSO.py - Windows互換性修正
- `signal.alarm()`がWindowsで使用できない問題を修正
- Unix系OS（macOS/Linux）では従来通りタイムアウト機能を維持
- Windowsではタイムアウトなしで実行

#### generate_building_fem_analyze.py - CalculiX並列計算の最適化
- OS/CPU自動検出による最適なスレッド数設定を実装
- 各環境での推奨設定：
  - **macOS (Apple Silicon M1/M2)**: 4スレッド
  - **macOS (Apple Silicon Pro/Max)**: 最大8スレッド
  - **Windows**: CPUコア数の半分（最大16スレッド）
  - **Linux**: CPUコア数の70%（最大20スレッド）
- 実行時にスレッド数を表示（`VERBOSE_OUTPUT=True`の場合）

## よくある作業

### 新しい最適化実行
1. `PSO.py`のパラメータ調整
2. FreeCADコマンドラインで実行
3. 結果CSVとFCStdファイルを確認

### 可視化画像の生成
1. FCStdファイルを`files/`に配置
2. `batch_fcstd_to_png.py`実行
3. `files/png_outputs/`に画像生成

### FEM解析デバッグ
- `VERBOSE_OUTPUT = True`に設定
- エラーメッセージとトレースバック確認
- CalculiXソルバーのパス確認