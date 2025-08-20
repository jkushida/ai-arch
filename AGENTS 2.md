# Repository Guidelines

## プロジェクト構成と配置
- `code/`: 主要なPythonコードと一部のテスト（`test_*.py`）。
- `code並列化/`: 並列化・Windows向け支援スクリプトと詳細なテスト群。
- `docs/`: ユーザー向けドキュメント（`*.md` と生成物 `*.html`）、`convert_md_to_html.py` 等のツール。
- `FC_macro/`, `files/`, `backup/`: 付随スクリプトや補助データ。大きな成果物（`*.FCStd` など）は必要最小限のみを保持。

## ビルド・実行・開発コマンド
- 実行（例）: `python code/gbest_generate_building.py`
- テスト（推奨）: `pytest -q` または `cd code && pytest -q`
- ドキュメント生成（例）: `python docs/convert_md_to_html.py`
- 注意: 一部スクリプトは FreeCAD 環境を前提とします。必要に応じて `FREECADPATH` の設定やFreeCADのインストールを行ってください。

## コーディング規約・命名
- Python: PEP 8 準拠、インデントはスペース4。関数・変数は `snake_case`、クラスは `PascalCase`、モジュールは小文字 `snake_case`。
- ファイル名: 役割が分かる短い英語名を基本とし、日本語名は可能なら英語へ置換を検討。
- 型ヒントとdocstringを推奨（公開関数・クラス）。
- フォーマッタ/リンタ（推奨）: `black`・`ruff`。導入や設定変更はPRで合意の上で行ってください。

## テスト方針
- フレームワーク: `pytest`。テストファイルは `test_*.py` 命名、対象と同ディレクトリまたは `tests/` に配置。
- 実行例: `pytest -q code/`、`pytest -q code並列化/`。
- 追加実装時は主要分岐のテストを同時に追加し、回帰バグ再発防止のため失敗事例を最小ケースで再現するテストを作成。

## コミット・PRガイドライン
- コミット: 簡潔な要約 + 動機/影響。例: `feat: add PSO progress monitor for Windows`、`fix: handle missing FreeCAD path`。
- PR要件: 目的・背景、変更点、動作確認手順（コマンド例）、影響範囲、関連Issueのリンク、必要に応じてスクリーンショットやログを添付。
- 変更は小さく分割し、既存動作を壊さないこと。外部依存の追加は必要性と影響を説明して合意を得てください。

## セキュリティ/運用メモ
- 秘密情報（APIキー、個人情報）はコミットしない。大容量生成物は `.gitignore` 検討の上、共有先を分離。
- マルチプラットフォーム配慮（Windows/macOS/Linux）。OS依存処理は明示し、代替手順を記載してください。
