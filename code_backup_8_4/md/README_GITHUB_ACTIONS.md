# Claude Code GitHub Actions 設定ガイド

## 概要
このプロジェクトでは，Claude Code GitHub Actionを使用して建築物FEM解析データの分析とレポート生成を自動化します．

## セットアップ手順

### 1. Anthropic APIキーの取得
1. [Anthropic Console](https://console.anthropic.com/)にアクセス
2. APIキーを作成（課金設定が必要）
3. キーをコピー

### 2. GitHub Secretsの設定
1. GitHubリポジトリの「Settings」→「Secrets and variables」→「Actions」
2. 「New repository secret」をクリック
3. 以下を設定：
   - **Name**: `ANTHROPIC_API_KEY`
   - **Value**: コピーしたAPIキー

### 3. ワークフローの使用方法

#### 手動実行
1. リポジトリの「Actions」タブを開く
2. 左側から「Update Building Analysis」を選択
3. 「Run workflow」をクリック
4. タスクを選択：
   - `analyze`: CSVデータの統計分析
   - `update-html`: HTMLギャラリーの改善
   - `optimize`: パラメータ最適化の提案
5. 「Run workflow」ボタンをクリック

#### 自動実行
以下のファイルが更新されたPRで自動実行されます：
- `production_freecad_random_fem_evaluation.csv`
- `building_analysis_gallery_csv.html`
- `simple_random_batch.py`

## ワークフローの詳細

### analyze タスク
- CSVデータの安全率分布を分析
- 高安全率サンプルの特徴抽出
- 低安全率サンプルの問題点特定
- `analysis_report.md`を生成

### update-html タスク
- HTMLギャラリーの改善提案
- 新機能の追加（ソート，フィルタなど）
- UI/UXの改善

### optimize タスク
- パラメータ範囲の最適化提案
- コスト効率の良い組み合わせ提案
- `optimization_report.md`を生成

## 制限事項

### トークン制限
- **入力**: 最大200,000トークン
- **出力**: 最大4,096トークン（設定可能）
- 大きなファイルは自動的にトランケートされる可能性があります

### 環境制限
- FreeCADは使用できません（GitHub Actions環境のため）
- 新規サンプル生成はローカル環境で実行する必要があります

### コスト
- Claude 3.5 Sonnetの使用料金が発生します
- 入力: $3 / 1Mトークン
- 出力: $15 / 1Mトークン

## ベストプラクティス

1. **タスクを明確に**
   - 具体的なタスクを選択して実行
   - 一度に多くの変更を要求しない

2. **レビューの重要性**
   - 生成されたPRは必ずレビュー
   - 自動生成されたコードやレポートを検証

3. **コスト管理**
   - 必要な時だけ手動実行
   - 大きなファイルの分析は避ける

## トラブルシューティング

### APIキーエラー
```
Error: Invalid API key
```
→ Secretsの設定を確認

### トークン制限エラー
```
Error: Token limit exceeded
```
→ 分析対象ファイルのサイズを確認

### 権限エラー
```
Error: Resource not accessible by integration
```
→ リポジトリの設定でActionsの権限を確認

## 参考リンク
- [Claude Code GitHub Action](https://github.com/anthropics/claude-code-action)
- [Anthropic API Documentation](https://docs.anthropic.com/claude/reference/getting-started)
- [GitHub Actions Documentation](https://docs.github.com/actions)