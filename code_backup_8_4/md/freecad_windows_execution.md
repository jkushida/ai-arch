# WindowsでのFreeCAD実行方法

## 基本的なコマンド構文

```powershell
& "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" test_generate_building.py
```

## コマンドの構成要素

### 1. `&` (Call Operator)
- PowerShellの実行演算子
- スペースを含むパスを実行する際に必要
- 引用符で囲まれた実行ファイルパスを正しく解釈

### 2. 実行ファイルパス
```
"C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe"
```
- `freecadcmd.exe`: FreeCADのコマンドライン版（GUIなし）
- バッチ処理やスクリプト実行に最適
- 引用符: パスにスペースが含まれるため必須

### 3. Pythonスクリプト
```
test_generate_building.py
```
- FreeCADの内蔵Pythonインタープリタで実行されるスクリプト
- 現在のディレクトリから相対パスで指定

## 実行方法のバリエーション

### PowerShellでの実行

#### 方法1: Call Operatorを使用（推奨）
```powershell
& "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" test_generate_building.py
```

#### 方法2: ディレクトリ移動後に実行
```powershell
cd "C:\Program Files\FreeCAD 1.0\bin"
.\freecadcmd.exe test_generate_building.py
```

#### 方法3: Start-Processを使用
```powershell
Start-Process -FilePath "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" -ArgumentList "test_generate_building.py" -NoNewWindow -Wait
```

### コマンドプロンプト（cmd.exe）での実行

```cmd
"C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" test_generate_building.py
```
- cmd.exeでは`&`演算子は不要
- 引用符だけで実行可能

## スクリプトへの引数渡し

### 単一の引数
```powershell
& "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" script.py arg1
```

### 複数の引数
```powershell
& "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" script.py arg1 arg2 arg3
```

### 引数にスペースが含まれる場合
```powershell
& "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" script.py "argument with spaces"
```

## 環境変数の設定

### PATH環境変数に追加する場合
```powershell
# 一時的に追加
$env:PATH += ";C:\Program Files\FreeCAD 1.0\bin"

# その後は直接実行可能
freecadcmd.exe test_generate_building.py
```

### システム環境変数に永続的に追加
1. システムのプロパティ → 環境変数
2. PATHに `C:\Program Files\FreeCAD 1.0\bin` を追加
3. 新しいPowerShell/cmdウィンドウで有効

## トラブルシューティング

### エラー: "用語が認識されません"
```
& : 用語 'C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe' は，コマンドレット，関数，スクリプト ファイル，
または操作可能なプログラムの名前として認識されません．
```
**解決方法:**
- FreeCADのインストールパスを確認
- 引用符が正しく使用されているか確認
- `&`演算子が正しく配置されているか確認

### エラー: "ファイルが見つかりません"
```
Error: No such file or directory: test_generate_building.py
```
**解決方法:**
- スクリプトファイルが現在のディレクトリに存在するか確認
- フルパスで指定: `& "C:\...\freecadcmd.exe" "C:\path\to\script.py"`

### PowerShell実行ポリシーエラー
```powershell
# 実行ポリシーを一時的に変更
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
```

## バッチファイルの作成

### run_freecad.bat
```batch
@echo off
"C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" %*
pause
```

使用方法:
```cmd
run_freecad.bat test_generate_building.py
```

## 推奨事項

1. **作業ディレクトリ**: スクリプトがあるディレクトリで実行
2. **エラーログ**: 出力をファイルにリダイレクト
   ```powershell
   & "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" script.py 2>&1 | Tee-Object -FilePath "output.log"
   ```
3. **バージョン確認**: 
   ```powershell
   & "C:\Program Files\FreeCAD 1.0\bin\freecadcmd.exe" --version
   ```

## 関連リンク

- [FreeCAD公式ドキュメント](https://wiki.freecad.org/Command_line_usage)
- [PowerShell Call Operator](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_operators)