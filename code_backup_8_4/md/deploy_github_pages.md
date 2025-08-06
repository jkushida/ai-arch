# GitHub Pagesでbuilding_analysis_gallery_csv.htmlを公開する手順

## 必要なファイル
- `building_analysis_gallery_csv.html`
- `production_freecad_random_fem_evaluation.csv`
- `png_outputs/` フォルダ内のすべての画像ファイル

## 手順

### 1. GitHubリポジトリの作成
```bash
# 新しいリポジトリを作成する場合
git init
git add building_analysis_gallery_csv.html
git add production_freecad_random_fem_evaluation.csv
git add png_outputs/
git commit -m "Initial commit: Building analysis gallery"
```

### 2. GitHubにプッシュ
```bash
# GitHubで新しいリポジトリを作成後
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY_NAME.git
git branch -M main
git push -u origin main
```

### 3. GitHub Pages設定
1. GitHubのリポジトリページで「Settings」タブをクリック
2. 左サイドバーの「Pages」をクリック
3. 「Source」セクションで：
   - 「Deploy from a branch」を選択
   - Branch: `main`を選択
   - Folder: `/ (root)`を選択
4. 「Save」をクリック

### 4. index.htmlの作成（重要）
GitHub Pagesはデフォルトで`index.html`を探すため，以下のいずれかを実行：

#### 方法A: ファイル名を変更
```bash
mv building_analysis_gallery_csv.html index.html
git add index.html
git commit -m "Rename to index.html for GitHub Pages"
git push
```

#### 方法B: リダイレクト用のindex.htmlを作成
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=building_analysis_gallery_csv.html">
    <title>Redirecting...</title>
</head>
<body>
    <p>リダイレクト中... <a href="building_analysis_gallery_csv.html">こちらをクリック</a></p>
</body>
</html>
```

### 5. CORS問題の対処
CSVファイルの読み込みでCORS問題が発生する場合があります．対処法：

#### 方法A: 相対パスを使用（推奨）
`building_analysis_gallery_csv.html`内のCSV読み込み部分を確認：
```javascript
Papa.parse('production_freecad_random_fem_evaluation.csv', {
    download: true,
    // ...
});
```

#### 方法B: CSVをJSONに変換
CSVデータをJSONファイルに変換し，scriptタグで読み込む方法もあります．

### 6. 画像パスの確認
画像のパスが正しいことを確認：
```javascript
<img src="png_outputs/SAMPLE${sampleNumber}${view.suffix}.png" 
     alt="${view.label}" 
     onerror="this.parentElement.innerHTML='<div class=\\'no-image\\'>画像なし</div>'">
```

### 7. デプロイの確認
1. GitHub Pagesが有効になるまで数分待つ
2. 以下のURLでアクセス：
   ```
   https://YOUR_USERNAME.github.io/YOUR_REPOSITORY_NAME/
   ```

### 8. トラブルシューティング

#### CSVが読み込めない場合
- ブラウザのコンソールでエラーを確認
- CSVファイルのパスが正しいか確認
- CSVファイルがGitHubにプッシュされているか確認

#### 画像が表示されない場合
- 画像ファイルがすべてプッシュされているか確認
- 大文字小文字の違いに注意（GitHubは大文字小文字を区別）
- `.gitignore`で画像が除外されていないか確認

#### ページが404エラーの場合
- GitHub Pages設定が正しいか確認
- index.htmlが存在するか確認
- デプロイが完了するまで待つ（最大10分程度）

### 9. 更新方法
データやコードを更新した場合：
```bash
git add .
git commit -m "Update data and visualizations"
git push
```

GitHub Pagesは自動的に更新されます（数分かかる場合があります）．

## 注意事項
- 無料のGitHub Pagesは公開リポジトリでのみ利用可能
- プライベートリポジトリでGitHub Pagesを使用するにはGitHub Proが必要
- リポジトリサイズは1GB以下を推奨
- 帯域幅制限は月100GB