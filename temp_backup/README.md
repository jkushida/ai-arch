# 建築物安全率分析ダッシュボード

## 使用方法

このダッシュボードはCSVファイルを読み込むため，HTTPサーバー経由でアクセスする必要があります．

### 方法1: Pythonを使用

ターミナルで以下のコマンドを実行：

```bash
python3 -m http.server 8000
```

または，付属のスクリプトを実行：

```bash
./start_server.sh
```

### 方法2: 付属のPythonスクリプトを使用

```bash
python3 start_server.py
```

### ブラウザでアクセス

サーバーが起動したら，ブラウザで以下のURLを開いてください：

```
http://localhost:8000/safety_analysis_interactive_2col_csv.html
```

## ファイル構成

- `safety_analysis_interactive_2col_csv.html` - メインのダッシュボード
- `production_freecad_random_fem_evaluation.csv` - データファイル（278件の有効なデータ）
- `png_outputs/` - 建物の画像ファイル
- `start_server.py` - HTTPサーバー起動スクリプト
- `start_server.sh` - HTTPサーバー起動シェルスクリプト

## 注意事項

- `file://` プロトコル（ファイルを直接開く）では，セキュリティ制限によりCSVファイルを読み込めません
- 必ずHTTPサーバー経由でアクセスしてください
- データ数は278件（1件のnanデータを除外）