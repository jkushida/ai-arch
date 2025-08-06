#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
monitor_pso.py
PSO実行の独立モニタリングツール
別プロセスで実行してpso_algorithm.pyの進捗を監視
"""

import json
import time
import os
import sys
from datetime import datetime
import threading
import io
import subprocess

# --- パスの設定 ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REALTIME_DATA_FILE = os.path.join(SCRIPT_DIR, "pso_realtime_data.json")

# Flask関連
try:
    from flask import Flask, Response, jsonify
    from flask_cors import CORS
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    print("Flask/matplotlib not installed. Console monitoring only.")

# OS別に日本語フォントを設定
if HAS_FLASK:
    import platform
    if platform.system() == 'Darwin':
        plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Hiragino Kaku Gothic Pro', 'Yu Gothic', 'Meirio']
    elif platform.system() == 'Windows':
        plt.rcParams['font.sans-serif'] = ['Yu Gothic', 'MS Gothic', 'MS PGothic', 'Meiryo', 'Meiryo UI', 'DejaVu Sans']
    else:
        plt.rcParams['font.sans-serif'] = ['Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

def _check_and_kill_process_on_port(port):
    print(f"Checking if port {port} is in use...")
    try:
        result = subprocess.run(['lsof', '-i', f':{port}'], capture_output=True, text=True, check=False)
        if result.returncode == 0 and result.stdout:
            pid_to_kill = None
            for line in result.stdout.splitlines():
                if "LISTEN" in line.upper():
                    parts = line.split()
                    if len(parts) > 1 and parts[1].isdigit():
                        pid_to_kill = parts[1]
                        break
            if pid_to_kill:
                print(f"Port {port} is in use by process PID: {pid_to_kill}. Terminating it.")
                subprocess.run(['kill', '-9', pid_to_kill], check=True)
                print(f"Process {pid_to_kill} terminated.")
                time.sleep(2)
        else:
            print(f"Port {port} is free.")
    except FileNotFoundError:
        print("Info: `lsof` command not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

class PSOMonitor:
    def __init__(self):
        self.data = None
        self.running = True
        if HAS_FLASK:
            self.app = Flask(__name__)
            CORS(self.app)
            self._setup_routes()
    
    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return self._render_dashboard()
        
        @self.app.route('/api/status')
        def get_status():
            if not self.data:
                return jsonify({'status': 'waiting'})
            return jsonify({
                'status': 'running' if os.path.exists(REALTIME_DATA_FILE) else 'completed',
                'iteration': self.data.get('iteration', 0),
                'max_iteration': max(0, self.data.get('max_iteration', 1) - 1),
                'progress': self.data.get('progress', 0),
                'gbest_fitness': self.data.get('gbest_fitness'),
                'n_particles': self.data.get('n_particles', 0),
                'elapsed_time': self.data.get('elapsed_time', 0)
            })
        
        @self.app.route('/api/pso_plot')
        def get_pso_plot():
            # 最新のデータを読み込んでからプロットを作成
            if os.path.exists(REALTIME_DATA_FILE):
                try:
                    with open(REALTIME_DATA_FILE, 'r') as f:
                        self.data = json.load(f)
                except:
                    pass
            
            fig = self._create_plots()
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', dpi=200, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close(fig)
            response = Response(img_buffer.getvalue(), mimetype='image/png')
            # キャッシュ無効化ヘッダーを追加
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            return response

        @self.app.route('/settings')
        def settings():
            return self._render_settings_page()

    def _create_plots(self):
        fig, axs = plt.subplots(2, 2, figsize=(8, 6))
        
        # self.dataから現在のiterationを取得（これが最新の値）
        iteration = 0
        if self.data and 'iteration' in self.data:
            iteration = self.data.get('iteration', 0)

        # タイトルなし（各グラフのタイトルで十分）

        # PSO.pyの出力ディレクトリ（絶対パス）
        IMAGE_DIR = '/Users/kushida2/Library/CloudStorage/GoogleDrive-kushida2008@gmail.com/マイドライブ/2025code/AI_arch/code/pso_output/images'
        plot_files = [
            {'ax': axs[0, 0], 'path': os.path.join(IMAGE_DIR, 'pso_all_positions_safety_vs_cost.png')},
            {'ax': axs[0, 1], 'path': os.path.join(IMAGE_DIR, 'pso_all_positions_safety_vs_co2.png')},
            {'ax': axs[1, 0], 'path': os.path.join(IMAGE_DIR, 'pso_all_positions_safety_vs_comfort.png')},
            {'ax': axs[1, 1], 'path': os.path.join(IMAGE_DIR, 'pso_all_positions_safety_vs_constructability.png')}
        ]

        for p_def in plot_files:
            ax = p_def['ax']
            path = p_def['path']
            ax.axis('off') 

            try:
                if os.path.exists(path):
                    # 画像を再読み込み（キャッシュを無効化）
                    from PIL import Image
                    pil_img = Image.open(path)
                    img = np.array(pil_img)
                    ax.imshow(img)
                else:
                    ax.text(0.5, 0.5, f'{os.path.basename(path)}\nが見つかりません', ha='center', va='center', fontsize=12, color='gray')
            except Exception as e:
                ax.text(0.5, 0.5, f'{os.path.basename(path)}\nの読み込みエラー: {str(e)}', ha='center', va='center', fontsize=12, color='red')

        plt.tight_layout(rect=[0, 0, 1, 0.95])
        return fig

    def _render_settings_page(self):
        settings_file = os.path.join(SCRIPT_DIR, 'pso_output', 'csv', 'pso_settings.csv')
        
        html = '''
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <title>PSO設定</title>
            <meta charset="utf-8">
            <meta http-equiv="refresh" content="60">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 20px; background-color: #f8f9fa; color: #343a40; }
                .container { max-width: 900px; margin: 0 auto; }
                .panel { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
                h1 { color: #343a40; border-bottom: 2px solid #dee2e6; padding-bottom: 10px; }
                h2 { margin-top: 0; color: #007bff; }
                table { width: 100%; border-collapse: collapse; margin-top: 15px; }
                th, td { border: 1px solid #dee2e6; padding: 10px; text-align: left; vertical-align: middle; font-size: 14px; }
                th { background-color: #f8f9fa; font-weight: 600; }
                .update-info { text-align: right; color: #6c757d; font-size: 12px; margin-bottom: 10px; }
            </style>
            <script>
                // 60秒ごとにページを更新
                setTimeout(function() { 
                    location.reload(); 
                }, 60000);
                
                // 次回更新までのカウントダウン表示
                var secondsLeft = 60;
                setInterval(function() {
                    secondsLeft--;
                    if (document.getElementById('countdown')) {
                        document.getElementById('countdown').textContent = secondsLeft;
                    }
                }, 1000);
            </script>
        </head>
        <body>
            <div class="container">
                <h1>PSO設定詳細</h1>
                <div class="update-info">
                    ※ このページは1分ごとに自動更新されます（次回更新まで <span id="countdown">60</span> 秒）
                </div>
        '''

        if not os.path.exists(settings_file):
            html += "<div class='panel'><h2>設定ファイルが見つかりません</h2><p>pso_algorithm.pyを一度実行すると生成されます。</p></div>"
        else:
            try:
                with open(settings_file, 'r', encoding='utf-8-sig') as f:
                    content_lines = f.readlines()
                
                # 実行開始時刻を探して最初に表示
                execution_time = None
                for line in content_lines:
                    if '実行開始時刻:' in line:
                        execution_time = line.strip()
                        break
                
                if execution_time:
                    html += f'<div class="panel"><h2>実行情報</h2><p style="font-size: 16px; font-weight: 600;">{execution_time}</p></div>'
                
                # 残りのコンテンツを処理
                is_in_table = False
                for line in content_lines:
                    line = line.strip()
                    
                    # 実行開始時刻は既に表示したのでスキップ
                    if '実行開始時刻:' in line:
                        continue
                        
                    if not line:
                        if is_in_table:
                            html += '</tbody></table></div>'
                            is_in_table = False
                        continue

                    cells = line.split(',')

                    if len(cells) == 1:
                        if is_in_table:
                            html += '</tbody></table></div>'
                        html += f'<div class="panel"><h2>{cells[0]}</h2>'
                        is_in_table = False # Reset for new section
                    else:
                        if not is_in_table:
                            html += '<table><thead><tr>'
                            for header in cells:
                                html += f'<th>{header}</th>'
                            html += '</tr></thead><tbody>'
                            is_in_table = True
                        else:
                            html += '<tr>'
                            for cell in cells:
                                html += f'<td>{cell}</td>'
                            html += '</tr>'
                
                if is_in_table: # Close last table if file doesn't end with newline
                    html += '</tbody></table></div>'

            except Exception as e:
                html += f"<div class='panel'><h2>ファイルの読み込みエラー</h2><p>{e}</p></div>"

        html += '''
            </div>
        </body>
        </html>
        '''
        return html

    def _render_dashboard(self):
        return """
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <title>PSOリアルタイムモニター</title>
            <meta charset="utf-8">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 20px; background-color: #f8f9fa; color: #343a40; }
                .container { max-width: 1400px; margin: 0 auto; }
                .panel { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
                .metric-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
                .metric-table th, .metric-table td { border: 1px solid #dee2e6; padding: 12px; text-align: center; vertical-align: middle; }
                .metric-table th { background-color: #f8f9fa; font-weight: 600; color: #495057; font-size: 14px; }
                .metric-table td { font-size: 26px; font-weight: 600; color: #007bff; }
                .progress-bar { width: 100%; height: 25px; background-color: #e9ecef; border-radius: 10px; overflow: hidden; margin-top: 20px; }
                .progress-fill { height: 100%; background-color: #28a745; transition: width 0.5s ease-in-out; text-align: center; color: white; font-weight: bold; line-height: 25px;}
                h1, h2 { color: #343a40; border-bottom: 2px solid #dee2e6; padding-bottom: 10px; }
                .status { font-weight: bold; padding: 5px 10px; border-radius: 5px; color: white; }
                .status-waiting { background-color: #ffc107; }
                .status-running { background-color: #28a745; }
                .status-completed { background-color: #007bff; }
                .settings-button { display: inline-block; margin-bottom: 15px; padding: 10px 15px; background-color: #6c757d; color: white; text-decoration: none; border-radius: 5px; font-size: 14px; }
                .settings-button:hover { background-color: #5a6268; }
                img { 
                    width: 100%; 
                    height: auto; 
                    max-width: 100%; 
                    border-radius: 5px; 
                    object-fit: contain;
                }
            </style>
            <script>
                function updateStatus() {
                    fetch('/api/status').then(response => response.json()).then(data => {
                        const statusEl = document.getElementById('status');
                        statusEl.textContent = data.status || 'waiting';
                        statusEl.className = 'status status-' + (data.status || 'waiting');
                        document.getElementById('iteration').textContent = data.iteration || 0;
                        document.getElementById('max-iteration').textContent = data.max_iteration || 0;
                        const fitnessValue = data.gbest_fitness;
                        if (fitnessValue === null || fitnessValue >= 1e10) {
                            document.getElementById('fitness').textContent = 'inf';
                        } else {
                            document.getElementById('fitness').textContent = fitnessValue.toExponential(3);
                        }
                        document.getElementById('particles').textContent = data.n_particles || 0;
                        document.getElementById('time').textContent = data.elapsed_time ? (data.elapsed_time / 60).toFixed(1) + ' min' : '0 min';
                        const progressFill = document.getElementById('progress-fill');
                        const progress = data.progress || 0;
                        progressFill.style.width = progress + '%';
                        progressFill.textContent = progress.toFixed(1) + '%';
                    });
                }

                function updatePlot() {
                    document.getElementById('pso-plot').src = '/api/pso_plot?' + new Date().getTime();
                }
                
                // ステータスとプロットを同時に更新
                function updateAll() {
                    // ステータスを先に更新してから、少し遅延を入れてプロットを更新
                    updateStatus();
                    setTimeout(updatePlot, 100);  // 100ms遅延
                }
                
                // 1分ごとに両方を更新（同期を保つ）
                setInterval(updateAll, 60000);

                // ページ読み込み時に初回実行
                window.onload = () => {
                    updateAll();
                };
            </script>
        </head>
        <body>
            <div class="container">
                <h1><span style="font-size: 2em;">🔍</span> PSO リアルタイムモニター</h1>
                <div class="panel">
                    <h2>最適化状態: <span id="status" class="status status-waiting">waiting</span></h2>
                    <a href="/settings" target="_blank" class="settings-button">PSOの設定を確認</a>
                    <table class="metric-table">
                        <thead>
                            <tr>
                                <th>ステップ</th>
                                <th>最良適応度</th>
                                <th>粒子数</th>
                                <th>経過時間</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td><span id="iteration">0</span> / <span id="max-iteration">0</span></td>
                                <td id="fitness">inf</td>
                                <td id="particles">0</td>
                                <td id="time">0 min</td>
                            </tr>
                        </tbody>
                    </table>
                    <div class="progress-bar">
                        <div class="progress-fill" id="progress-fill">0%</div>
                    </div>
                </div>
                <div class="panel">
                    <h2>粒子群の評価値のプロット（探索を通しての粒子の位置<i>x</i>の評価値）</h2>
                    <p style="color: #6c757d;">※このグラフは1分ごとに更新されます。</p>
                    <img id="pso-plot" src="/api/pso_plot" alt="PSO粒子群の評価値のプロット">
                </div>
            </div>
        </body>
        </html>
        """
    
    def console_monitor(self):
        print("PSO Console Monitor")
        print("=" * 50)
        print("Waiting for PSO to start...")
        while self.running:
            try:
                if os.path.exists(REALTIME_DATA_FILE):
                    with open(REALTIME_DATA_FILE, 'r') as f:
                        self.data = json.load(f)
                    fitness_display = self.data.get('gbest_fitness', 0)
                    if fitness_display >= 1e10:
                        fitness_display = 'inf'
                    else:
                        fitness_display = f"{fitness_display:.2e}"

                    print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Iter: {self.data.get('iteration', 0)}/{max(0, self.data.get('max_iteration', 1) - 1)} "
                          f"({self.data.get('progress', 0):.1f}%) "
                          f"Best: {fitness_display} "
                          f"Time: {self.data.get('elapsed_time', 0):.1f}s", end='', flush=True)
                else:
                    if self.data:
                        print("\n\n✅ PSO Optimization Completed!")
                        break
                time.sleep(1)
            except KeyboardInterrupt:
                print("\n\nMonitoring stopped by user.")
                self.running = False
                break
            except Exception as e:
                print(f"\nError: {e}")
                time.sleep(1)
    
    def start_web_ui(self, port=5001):
        if not HAS_FLASK:
            print("Flask not available. Using console mode only.")
            self.console_monitor()
            return
        
        def read_data():
            while self.running:
                try:
                    if os.path.exists(REALTIME_DATA_FILE):
                        with open(REALTIME_DATA_FILE, 'r') as f:
                            new_data = json.load(f)
                            self.data = new_data
                    elif self.data:
                        time.sleep(5)
                        self.running = False
                except Exception:
                    pass
                time.sleep(0.5)
        
        data_thread = threading.Thread(target=read_data, daemon=True)
        data_thread.start()
        
        print(f"Starting Web UI at http://localhost:{port}")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            self.app.run(host='0.0.0.0', port=port, debug=False)
        except KeyboardInterrupt:
            print("\nStopping monitor...")
            self.running = False

if __name__ == "__main__":
    monitor = PSOMonitor()
    web_port = 5001
    
    if len(sys.argv) > 1 and sys.argv[1] == '--console':
        monitor.console_monitor()
    else:
        _check_and_kill_process_on_port(web_port)
        monitor.start_web_ui(port=web_port)
