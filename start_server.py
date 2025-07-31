#!/usr/bin/env python3
import http.server
import socketserver
import os

# ポート番号
PORT = 8000

# このスクリプトのディレクトリに移動
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# HTTPサーバーを起動
Handler = http.server.SimpleHTTPRequestHandler
Handler.extensions_map['.csv'] = 'text/csv'

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"サーバーが起動しました: http://localhost:{PORT}")
    print(f"safety_analysis_interactive_2col_csv.html を開くには:")
    print(f"http://localhost:{PORT}/safety_analysis_interactive_2col_csv.html")
    print("\n終了するには Ctrl+C を押してください")
    httpd.serve_forever()