# Pythonファイル バージョン一覧

最終更新: 2025-07-07

## 📊 バージョン管理状況

| ファイル名 | バージョン | サイズ | 備考 |
|-----------|-----------|--------|------|
| **building_fem_analysis_piloti_with_stairs_v8.py** | v8→v9* | 140KB | メインモジュール（内部はv9表記） |
| building_fem_analysis_piloti_with_stairs_v8のコピー.py | v9 | 129KB | バックアップ |
| building_fem_analysis_piloti_with_stairs_v8のコピー2.py | v9 | 129KB | バックアップ |
| building_fem_analysis_piloti_with_stairs_v8のコピー3.py | v9 | 128KB | バックアップ |
| building_fem_analysis_piloti_with_stairs_v8のコピー4.py | v9 | 136KB | バックアップ |
| building_fem_analysis_piloti_with_stairs_v8のコピー5.py | v9 | 136KB | バックアップ |
| **DE.py** | v9 | 12KB | 差分進化最適化 |
| **simple_random_batch.py** | - | 20KB | v8をインポート |
| batch_fcstd_to_png.py | - | 9.5KB | バージョン表記なし |
| batch_fcstd_to_pngのコピー.py | - | 9.2KB | バックアップ |
| fcstd_to_png.py | - | 7.5KB | バージョン表記なし |
| fcstd_to_pngのコピー.py | - | 7.3KB | バックアップ |
| create_html_gallery.py | - | 12KB | バージョン表記なし |
| create_html_galleryのコピー.py | - | 15KB | バックアップ |
| create_html_galleryのコピー2.py | - | 14KB | バックアップ |

## 🔍 バージョン不整合の詳細

### 1. **building_fem_analysis_piloti_with_stairs_v8.py**
- ファイル名: v8
- 内部コメント: v9 (`building_fem_analysis_piloti_with_stairs_v9.py`)
- 説明: かまぼこ屋根対応版ピロティ建築FEM解析スクリプト（ねじれ機能削除版）

### 2. **DE.py**
- 内部コメント: v9 (`DE_optimization_v9.py`)
- インポート: `building_fem_analysis_piloti_with_stairs_v8`を使用

### 3. **simple_random_batch.py**
- バージョン表記なし
- インポート: `building_fem_analysis_piloti_with_stairs_v8`を使用
- 特徴: 並列処理対応版

## 📝 推奨アクション

1. **ファイル名の統一**
   - `building_fem_analysis_piloti_with_stairs_v8.py` → `building_fem_analysis_piloti_with_stairs_v9.py`にリネーム推奨
   - または内部のv9表記をv8に統一

2. **バージョン管理の追加**
   - batch_fcstd_to_png.py
   - fcstd_to_png.py
   - create_html_gallery.py
   - simple_random_batch.py
   
   これらのファイルにバージョン情報を追加

3. **バックアップファイルの整理**
   - 「のコピー」ファイルが多数存在
   - 必要なものを選別してバックアップディレクトリに移動推奨

## 🔄 最新の変更履歴

### v8 → v9の主な変更点（推定）
- ねじれ機能の削除
- かまぼこ屋根対応の強化
- バルコニー機能の追加
- tw_intパラメータの削除
- 色分け機能の実装

### 各ファイルの役割
- **コア**: building_fem_analysis系 - 建物生成とFEM解析
- **最適化**: DE.py - 差分進化アルゴリズム
- **バッチ**: simple_random_batch.py - ランダムサンプリング
- **可視化**: fcstd_to_png系, create_html_gallery系 - 結果の可視化