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
import inspect
import pso_config

# --- パスの設定 ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "pso_output")
REALTIME_DATA_FILE = os.path.join(OUTPUT_DIR, "pso_realtime_data.json")
CSV_DIR = os.path.join(OUTPUT_DIR, "csv")

# Flask関連
try:
    from flask import Flask, Response, jsonify
    from flask_cors import CORS
    import plotly
    import plotly.graph_objs as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import pandas as pd
    import numpy as np
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    print("Flask/plotly not installed. Console monitoring only.")

def _check_and_kill_process_on_port(port):
    import platform, subprocess, time
    system = platform.system()
    print(f"Checking if port {port} is in use...")
    try:
        if system == 'Windows':
            # Windows: Use netstat to find PID
            result = subprocess.run(f"netstat -ano | findstr :{port}", shell=True, capture_output=True, text=True)
            if result.stdout:
                for line in result.stdout.strip().split("\n"):
                    parts = line.strip().split()
                    if len(parts) >= 5 and parts[-1].isdigit() and parts[-1] != "0":
                        pid = parts[-1]
                        print(f"Port {port} in use by PID {pid}. Killing...")
                        subprocess.run(f"taskkill /PID {pid} /F", shell=True)
                time.sleep(1)
            else:
                print(f"Port {port} is free.")
        else:
            # macOS/Linux: Use lsof with LISTEN filtering
            result = subprocess.run(f"lsof -nP -i :{port} | grep LISTEN", shell=True, capture_output=True, text=True)
            if result.stdout:
                lines = result.stdout.strip().split("\n")
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 2 and parts[1].isdigit():
                        pid = parts[1]
                        print(f"Port {port} in use by PID {pid}. Killing...")
                        subprocess.run(f"kill -9 {pid}", shell=True)
                # Wait briefly for port release
                time.sleep(1)
                # Re-check to confirm port is free
                confirm = subprocess.run(f"lsof -i :{port}", shell=True, capture_output=True, text=True)
                if confirm.stdout:
                    print(f"Warning: Port {port} may still be in use.")
            else:
                print(f"Port {port} is free.")
    except Exception as e:
        print(f"Failed to check/kill process on port {port}: {e}")

class PSOMonitor:
    def __init__(self):
        self.data = None
        self.running = True
        self.data_lock = threading.Lock()  # データアクセスを保護するためのロック
        if HAS_FLASK:
            # 設定値をインスタンス変数として保持
            self.max_iterations = pso_config.MAX_ITER
            self.n_particles = pso_config.N_PARTICLES

            self.app = Flask(__name__)
            CORS(self.app)
            self._setup_routes()
    
    def _setup_routes(self):
        @self.app.route('/')
        def index():
            return self._render_dashboard()
        
        @self.app.route('/api/status')
        def get_status():
            # 1. 実行中の状態を確認
            if os.path.exists(REALTIME_DATA_FILE):
                with self.data_lock:
                    data = self.data if self.data else {}
                    return jsonify({
                        'status': 'running',
                        'iteration': data.get('iteration', 0),
                        'max_iteration': self.max_iterations - 1,
                        'progress': data.get('progress', 0),
                        'gbest_fitness': data.get('gbest_fitness'),
                        'n_particles': data.get('n_particles', 0),
                        'elapsed_time': data.get('elapsed_time', 0)
                    })

            # 2. 完了済みの状態を確認 (フラグファイルを使用)
            completed_flag_file = os.path.join(OUTPUT_DIR, "pso_completed.flag")
            if os.path.exists(completed_flag_file):
                try:
                    with open(completed_flag_file, 'r') as f:
                        completion_data = json.load(f)
                    return jsonify({
                        'status': 'completed',
                        'iteration': self.max_iterations - 1,
                        'max_iteration': self.max_iterations - 1,
                        'progress': 100,
                        'gbest_fitness': completion_data.get('gbest_fitness'),
                        'n_particles': self.n_particles,
                        'elapsed_time': completion_data.get('elapsed_time', 0)
                    })
                except Exception as e:
                    print(f"[ERROR] Could not read completion flag: {e}")

            # 3. 上記以外は待機中
            return jsonify({
                'status': 'waiting',
                'iteration': 0,
                'max_iteration': self.max_iterations - 1,
                'progress': 0,
                'gbest_fitness': None,
                'n_particles': 0,
                'elapsed_time': 0
            })
        
        @self.app.route('/api/plotly/convergence')
        def get_convergence_plot():
            """Plotlyで収束グラフを生成"""
            gbest_file = os.path.join(CSV_DIR, "pso_gbest_history.csv")
            
            if not os.path.exists(gbest_file):
                return jsonify({'error': 'Convergence data (pso_gbest_history.csv) not found.'})
            
            try:
                df = pd.read_csv(gbest_file)
                if df.empty:
                    return jsonify({'error': 'Convergence data is empty.'})

                fig = make_subplots(rows=1, cols=2, subplot_titles=('適応度の推移', '安全率の推移'))
                
                fig.add_trace(go.Scatter(x=df['iteration'].tolist(), y=df['gbest_fitness'].tolist(), mode='lines+markers', name='Best Fitness', line=dict(color='blue', width=2), marker=dict(size=8)), row=1, col=1)
                fig.add_trace(go.Scatter(x=df['iteration'].tolist(), y=df['safety'].tolist(), mode='lines+markers', name='Safety Factor', line=dict(color='red', width=2), marker=dict(size=8)), row=1, col=2)
                
                if not df.empty:
                    fig.add_trace(go.Scatter(x=[df['iteration'].min(), df['iteration'].max()], y=[2.0, 2.0], mode='lines', name='推奨値', line=dict(color='red', dash='dash'), showlegend=False), row=1, col=2)
                
                fig.update_xaxes(title_text="反復回数", row=1, col=1)
                fig.update_xaxes(title_text="反復回数", row=1, col=2)
                fig.update_yaxes(title_text="適応度", row=1, col=1)
                fig.update_yaxes(title_text="安全率", row=1, col=2)
                fig.update_layout(height=400, showlegend=True, template="plotly_white")
                
                return jsonify({'plot': fig.to_json()})
                
            except Exception as e:
                print(f"[ERROR] Exception in convergence plot: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': str(e)})
        
        @self.app.route('/api/plotly/scatter')
        def get_scatter_plots():
            """Plotlyで粒子群の散布図を生成"""
            particle_file = os.path.join(CSV_DIR, "pso_particle_positions.csv")
            gbest_file = os.path.join(CSV_DIR, "pso_gbest_history.csv")

            if not os.path.exists(particle_file):
                return jsonify({'error': 'Particle data (pso_particle_positions.csv) not found.'})

            try:
                # 粒子データCSVにはヘッダーがないため、列名を指定して読み込む
                particle_columns = [
                    'iteration', 'particle_id', 'fitness', 'cost', 'safety', 'co2',
                    'comfort', 'constructability', 'Lx', 'Ly', 'H1', 'H2', 'tf', 'tr',
                    'bc', 'hc', 'tw_ext', 'wall_tilt_angle', 'window_ratio_2f',
                    'roof_morph', 'roof_shift', 'balcony_depth', 'material_columns',
                    'material_floor1', 'material_floor2', 'material_roof',
                    'material_walls', 'material_balcony'
                ]
                df = pd.read_csv(particle_file, header=None, names=particle_columns)

                if df.empty:
                    return jsonify({'error': 'Particle data is empty.'})

                gbest_df = None
                if os.path.exists(gbest_file):
                    try:
                        gbest_df = pd.read_csv(gbest_file)
                        if gbest_df.empty: gbest_df = None
                    except pd.errors.EmptyDataError:
                        gbest_df = None

                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=('建設コスト (円/m²) vs 安全率', 'CO2排出量 (kg-CO2/m²) vs 安全率', '快適性スコア vs 安全率', '施工性スコア vs 安全率'),
                    vertical_spacing=0.12, # 垂直方向の隙間を調整
                    horizontal_spacing=0.12 # 水平方向の隙間を調整
                )

                # グラデーションカラースケールを設定
                colorscale = px.colors.sequential.Viridis
                min_iter = df['iteration'].min()
                max_iter = df['iteration'].max()
                # 0除算を避ける
                iter_range = (max_iter - min_iter) if (max_iter > min_iter) else 1.0

                plot_configs = [
                    {'y': 'cost', 'row': 1, 'col': 1, 'ylabel': '建設コスト (円/m²)'},
                    {'y': 'co2', 'row': 1, 'col': 2, 'ylabel': 'CO2排出量 (kg-CO2/m²)'},
                    {'y': 'comfort', 'row': 2, 'col': 1, 'ylabel': '快適性スコア'},
                    {'y': 'constructability', 'row': 2, 'col': 2, 'ylabel': '施工性スコア'}
                ]

                shown_legends = set()

                for iteration in sorted(df['iteration'].unique()):
                    iter_df = df[df['iteration'] == iteration]

                    # 世代に基づいて色を決定
                    color_fraction = (iteration - min_iter) / iter_range
                    color_index = int(color_fraction * (len(colorscale) - 1))
                    color = colorscale[color_index]

                    legend_name = f'ステップ{iteration}'
                    # 凡例は各ステップで1回だけ表示
                    show_legend = legend_name not in shown_legends

                    for config in plot_configs:
                        valid_df = iter_df[(iter_df['safety'] > 0) & (np.isfinite(iter_df[config['y']]))]
                        if not valid_df.empty:
                            fig.add_trace(go.Scatter(
                                x=valid_df['safety'].tolist(),
                                y=valid_df[config['y']].tolist(),
                                mode='markers',
                                name=legend_name,
                                marker=dict(color=color, size=6, opacity=0.6),
                                showlegend=show_legend
                            ), row=config['row'], col=config['col'])
                            # このステップの凡例は一度表示したら、他のサブプロットでは表示しない
                            if show_legend:
                                show_legend = False

                    if legend_name not in shown_legends:
                        shown_legends.add(legend_name)

                if gbest_df is not None and not gbest_df.empty:
                    show_gbest_legend = True
                    # gbestのホバーテキストを世代情報に設定
                    gbest_hover_texts = [f'ステップ {int(row.iteration)}' for index, row in gbest_df.iterrows()]

                    for config in plot_configs:
                        fig.add_trace(go.Scatter(
                            x=gbest_df['safety'].tolist(),
                            y=gbest_df[config['y']].tolist(),
                            mode='lines+markers',
                            name='gbest', # 凡例用の名前
                            text=gbest_hover_texts, # ホバー用のテキスト
                            hoverinfo='x+y+text', # ホバーにx, y, textを表示
                            marker=dict(color='red', size=10, symbol='star', line=dict(color='black', width=1)),
                            line=dict(color='rgba(100, 100, 100, 0.7)', width=1.5, dash='dot'),
                            showlegend=show_gbest_legend
                        ), row=config['row'], col=config['col'])
                        if show_gbest_legend:
                            show_gbest_legend = False # gbestの凡例は一度しか表示しない

                for config in plot_configs:
                    fig.add_vline(x=2.0, line_dash="dash", line_color="red", opacity=0.5, row=config['row'], col=config['col'])

                # レイアウト設定
                fig.update_xaxes(title_text="安全率")
                for config in plot_configs:
                    fig.update_yaxes(title_text=config['ylabel'], row=config['row'], col=config['col'])
                
                fig.update_layout(height=1000, showlegend=True, template="plotly_white")

                return jsonify({'plot': fig.to_json()})

            except Exception as e:
                import traceback
                traceback.print_exc()
                return jsonify({'error': str(e)})

        @self.app.route('/settings')
        def settings():
            return self._render_settings_page()

        @self.app.route('/gbest')
        def gbest():
            return self._render_gbest_page()

    def _render_settings_page(self):
        settings_file = os.path.join(CSV_DIR, 'pso_settings.csv')
        
        html = '''<!DOCTYPE html><html lang="ja"><head><title>PSO設定</title><meta charset="utf-8"><meta http-equiv="refresh" content="60"><style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;margin:20px;background-color:#f8f9fa;color:#343a40}.container{max-width:900px;margin:0 auto}.panel{background:white;padding:20px;border-radius:10px;margin-bottom:20px;box-shadow:0 4px 6px rgba(0,0,0,0.05)}h1{color:#343a40;border-bottom:2px solid #dee2e6;padding-bottom:10px}h2{margin-top:0;color:#007bff}table{width:100%;border-collapse:collapse;margin-top:15px}th,td{border:1px solid #dee2e6;padding:10px;text-align:left;vertical-align:middle;font-size:14px}th{background-color:#f8f9fa;font-weight:600}.update-info{text-align:right;color:#6c757d;font-size:12px;margin-bottom:10px}</style></head><body><div class="container"><h1>PSO設定詳細</h1><div class="update-info">※ このページは1分ごとに自動更新されます</div>'''

        if not os.path.exists(settings_file):
            html += "<div class='panel'><h2>設定ファイルが見つかりません</h2><p>pso_algorithm.pyを一度実行すると生成されます。</p></div>"
        else:
            try:
                with open(settings_file, 'r', encoding='utf-8-sig') as f:
                    content_lines = f.readlines()
                
                execution_time_line = next((line for line in content_lines if '実行開始時刻:' in line), None)
                if execution_time_line:
                    html += f'<div class="panel"><h2>実行情報</h2><p style="font-size:16px;font-weight:600;">{execution_time_line.strip()}</p></div>'

                sections = []
                current_section = None
                for line in content_lines:
                    line = line.strip()
                    if not line or '実行開始時刻:' in line: continue
                    
                    cells = [cell.strip() for cell in line.split(',')]
                    
                    if len(cells) == 1 and cells[0]:
                        current_section = {'title': cells[0], 'rows': []}
                        sections.append(current_section)
                    elif len(cells) > 1 and current_section is not None:
                        current_section['rows'].append(cells)

                for section in sections:
                    html += f'<div class="panel"><h2>{section["title"]}</h2>'
                    if section['rows']:
                        html += '<table>'
                        header = section['rows'][0]
                        html += f'<thead><tr><th>' + '</th><th>'.join(header) + '</th></tr></thead>'
                        html += '<tbody>'
                        for row in section['rows'][1:]:
                            html += f'<tr><td>' + '</td><td>'.join(row) + '</td></tr>'
                        html += '</tbody></table>'
                    html += '</div>'

            except Exception as e:
                html += f"<div class='panel'><h2>ファイルの読み込みエラー</h2><p>{e}</p></div>"

        try:
            fitness_code = inspect.getsource(pso_config.calculate_fitness)
            html += f"<div class='panel'><h2>適応度関数 (pso_config.py)</h2><pre style='background:#f0f0f0;padding:10px;border-radius:5px;overflow-x:auto;'>{fitness_code}</pre></div>"
        except Exception as e:
            html += f"<div class='panel'><h2>適応度関数の読み込みエラー</h2><p>{e}</p></div>"

        html += '</div></body></html>'
        return html

    def _render_gbest_page(self):
        """gbestの詳細情報を表示するページ"""
        html = '''<!DOCTYPE html><html lang="ja"><head><title>gbest詳細情報</title><meta charset="utf-8"><meta http-equiv="refresh" content="60"><style>body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;margin:15px;background-color:#f8f9fa;color:#343a40}.container{max-width:1100px;margin:0 auto}.panel{background:white;padding:12px;border-radius:6px;margin-bottom:12px;box-shadow:0 2px 4px rgba(0,0,0,0.05)}h1{color:#343a40;border-bottom:2px solid #dee2e6;padding-bottom:8px;font-size:22px;margin:8px 0 12px}h2{margin-top:0;color:#007bff;font-size:16px;margin-bottom:8px}table{width:100%;border-collapse:collapse}th,td{border:1px solid #dee2e6;padding:4px 6px;text-align:left;vertical-align:middle;font-size:12px;line-height:1.3}th{background-color:#f8f9fa;font-weight:600;white-space:nowrap}.update-info{text-align:right;color:#6c757d;font-size:11px;margin-bottom:8px}.variable-name{color:#495057;font-size:12px}.variable-name small{font-size:10px;color:#868e96;display:block;margin-top:2px}.material-concrete{background-color:#e3f2fd !important;font-weight:600;text-align:center;font-size:12px}.material-wood{background-color:#f5d5cc !important;font-weight:600;text-align:center;font-size:12px;color:#7a4a3a !important}.compact-table{font-size:12px}.compact-table th,.compact-table td{padding:4px 6px}td.numeric{text-align:right;font-family:monospace;font-size:12px}.two-column{display:flex;gap:15px}.column{flex:1}.value-fitness{color:#17a2b8 !important;font-weight:700}.value-cost{color:#dc3545 !important;font-weight:700}.value-safety{color:#fd7e14 !important;font-weight:700}.value-co2{color:#6f42c1 !important;font-weight:700}.value-comfort{color:#e83e8c !important;font-weight:700}.value-constructability{color:#20c997 !important;font-weight:700}</style></head><body><div class="container"><h1>現在のgbest詳細情報</h1><div class="update-info">※ このページは1分ごとに自動更新されます</div>'''
        
        gbest_file = os.path.join(CSV_DIR, "pso_gbest_history.csv")
        
        if not os.path.exists(gbest_file):
            html += "<div class='panel'><h2>gbestデータが見つかりません</h2><p>最適化を実行すると生成されます。</p></div>"
        else:
            try:
                df = pd.read_csv(gbest_file)
                if df.empty:
                    html += "<div class='panel'><h2>gbestデータが空です</h2></div>"
                else:
                    # 最新のgbest（最後の行）を取得
                    latest_gbest = df.iloc[-1]
                    current_step = int(latest_gbest['iteration'])
                    
                    # タイトルにステップ数を追加
                    html = html.replace('<h1>現在のgbest詳細情報</h1>', f'<h1>現在のgbest詳細情報（{current_step}ステップ）</h1>')
                    
                    # FCStd作成の案内を追加
                    html += '<div style="background-color:#e7f3ff;padding:10px;border-radius:5px;margin-bottom:15px;border-left:4px solid #007bff;">'
                    html += '<p style="margin:0;font-size:13px;color:#004085;">このgbestでFCStdを作成する場合は、<code style="background-color:#fff;padding:2px 4px;border-radius:3px;font-family:monospace;">gbest_generate_building.py</code> を実行してください。</p>'
                    html += '</div>'
                    
                    # 評価値と材料パラメータを横に並べて表示
                    html += '<div class="two-column">'
                    
                    # 左側：評価値セクション
                    html += '<div class="column"><div class="panel"><h2>評価値</h2><table class="compact-table">'
                    html += '<tr><th style="width:60%">指標</th><th style="width:40%">値</th></tr>'
                    html += f'<tr><td>適応度 (fitness)</td><td class="numeric value-fitness">{latest_gbest["gbest_fitness"]:.2f}</td></tr>'
                    html += f'<tr><td>建設コスト (円/m²)</td><td class="numeric value-cost">{latest_gbest["cost"]:.2f}</td></tr>'
                    html += f'<tr><td>安全率</td><td class="numeric value-safety">{latest_gbest["safety"]:.3f}</td></tr>'
                    html += f'<tr><td>CO2排出量 (kg-CO2/m²)</td><td class="numeric value-co2">{latest_gbest["co2"]:.2f}</td></tr>'
                    html += f'<tr><td>快適性スコア</td><td class="numeric value-comfort">{latest_gbest["comfort"]:.3f}</td></tr>'
                    html += f'<tr><td>施工性スコア</td><td class="numeric value-constructability">{latest_gbest["constructability"]:.3f}</td></tr>'
                    html += '</table></div></div>'
                    
                    # 右側：材料パラメータセクション
                    html += '<div class="column"><div class="panel"><h2>材料パラメータ</h2><table class="compact-table">'
                    html += '<tr><th style="width:50%">部材</th><th style="width:50%">材料</th></tr>'
                    material_params = [
                        ('material_columns', '柱'),
                        ('material_floor1', '1階床'),
                        ('material_floor2', '2階床'),
                        ('material_roof', '屋根'),
                        ('material_walls', '壁'),
                        ('material_balcony', 'バルコニー')
                    ]
                    for param, description in material_params:
                        value = int(latest_gbest[param])
                        material = "木材" if value == 1 else "コンクリート"
                        material_class = "material-wood" if value == 1 else "material-concrete"
                        html += f'<tr><td class="variable-name">{description}</td><td class="{material_class}">{material}</td></tr>'
                    html += '</table></div></div>'
                    
                    html += '</div>'
                    
                    # 設計変数セクション - 形状パラメータ（2列表示）
                    html += '<div class="panel"><h2>設計変数 - 形状パラメータ</h2><div class="two-column">'
                    
                    shape_params = [
                        ('Lx', 'X方向長さ', 'm'),
                        ('Ly', 'Y方向長さ', 'm'),
                        ('H1', '1階高さ', 'm'),
                        ('H2', '2階高さ', 'm'),
                        ('tf', '床スラブ厚', 'mm'),
                        ('tr', '屋根スラブ厚', 'mm'),
                        ('bc', '柱寸法', 'mm'),
                        ('hc', '梁高さ', 'mm'),
                        ('tw_ext', '外壁厚', 'mm'),
                        ('wall_tilt_angle', '壁傾斜角度', '度'),
                        ('window_ratio_2f', '2階窓面積比', '-'),
                        ('roof_morph', '屋根形状係数', '-'),
                        ('roof_shift', '屋根ずれ係数', '-'),
                        ('balcony_depth', 'バルコニー奥行き', 'm')
                    ]
                    
                    # 左列
                    html += '<div class="column"><table class="compact-table">'
                    html += '<tr><th>変数</th><th>値</th><th>単位</th></tr>'
                    for i in range(0, 7):
                        param, description, unit = shape_params[i]
                        value = latest_gbest[param]
                        html += f'<tr><td class="variable-name">{param}<br><small>{description}</small></td><td class="numeric">{value:.3f}</td><td>{unit}</td></tr>'
                    html += '</table></div>'
                    
                    # 右列
                    html += '<div class="column"><table class="compact-table">'
                    html += '<tr><th>変数</th><th>値</th><th>単位</th></tr>'
                    for i in range(7, 14):
                        param, description, unit = shape_params[i]
                        value = latest_gbest[param]
                        html += f'<tr><td class="variable-name">{param}<br><small>{description}</small></td><td class="numeric">{value:.3f}</td><td>{unit}</td></tr>'
                    html += '</table></div>'
                    
                    html += '</div></div>'
                    
            except Exception as e:
                html += f"<div class='panel'><h2>データの読み込みエラー</h2><p>{e}</p></div>"
        
        html += '</div></body></html>'
        return html

    def _render_dashboard(self):
        return """
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <title>PSOリアルタイムモニター</title>
            <meta charset="utf-8">
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; margin: 20px; background-color: #f8f9fa; color: #343a40; }
                .container { max-width: 1400px; margin: 0 auto; }
                .panel { background: white; padding: 20px; border-radius: 10px; margin-bottom: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
                .metric-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
                .metric-table th, .metric-table td { border: 1px solid #dee2e6; padding: 12px; text-align: center; vertical-align: middle; }
                .metric-table th { background-color: #f8f9fa; font-weight: 600; color: #495057; font-size: 14px; }
                .metric-table td { font-size: 26px; font-weight: 600; color: #007bff; }
                .progress-bar { width: 100%; height: 25px; background-color: #e9ecef; border-radius: 10px; overflow: hidden; margin-top: 20px; position: relative; }
                .progress-fill { height: 100%; background-color: #28a745; transition: width 0.5s ease-in-out; width: 0%; }
                .progress-text { position: absolute; width: 100%; text-align: center; line-height: 25px; color: #495057; font-weight: bold; z-index: 1; }
                h1, h2 { color: #343a40; border-bottom: 2px solid #dee2e6; padding-bottom: 10px; }
                .status { font-weight: bold; padding: 5px 10px; border-radius: 5px; color: white; }
                .status-waiting { background-color: #ffc107; }
                .status-running { background-color: #28a745; }
                .status-completed { background-color: #007bff; }
                .settings-button { display: inline-block; margin-bottom: 15px; padding: 10px 15px; background-color: #6c757d; color: white; text-decoration: none; border-radius: 5px; font-size: 14px; }
                .settings-button:hover { background-color: #5a6268; }
            </style>
            <script>
                let isGbestVisible = false; // gbestの表示状態を管理するグローバル変数 (デフォルトは非表示)

                function updateStatus() {
                    fetch('/api/status').then(response => response.json()).then(data => {
                        const statusEl = document.getElementById('status');
                        statusEl.textContent = data.status || 'waiting';
                        statusEl.className = 'status status-' + (data.status || 'waiting');
                        document.getElementById('iteration').textContent = data.iteration || 0;
                        document.getElementById('max-iteration').textContent = data.max_iteration !== undefined ? data.max_iteration : 0;
                        const fitnessValue = data.gbest_fitness;
                        document.getElementById('fitness').textContent = (fitnessValue === null || fitnessValue >= 1e10) ? 'inf' : fitnessValue.toExponential(3);
                        document.getElementById('particles').textContent = data.n_particles || 0;
                        document.getElementById('time').textContent = data.elapsed_time ? (data.elapsed_time / 60).toFixed(1) + ' min' : '0 min';
                        document.getElementById('current-elapsed-time').textContent = data.elapsed_time ? (data.elapsed_time / 60).toFixed(1) + ' min' : '0 min';
                        const progress = data.progress || 0;
                        document.getElementById('progress-fill').style.width = progress + '%';
                        document.getElementById('progress-text').textContent = progress.toFixed(1) + '%';
                    });
                }

                function applyGbestVisibility() {
                    const scatterPlot = document.getElementById('scatter-plot');
                    const btn = document.getElementById('toggle-gbest-btn');
                    if (!scatterPlot || !scatterPlot.data) return;

                    const gbestIndices = [];
                    scatterPlot.data.forEach((trace, index) => {
                        if (trace.name === 'gbest') {
                            gbestIndices.push(index);
                        }
                    });

                    if (gbestIndices.length > 0) {
                        Plotly.restyle(scatterPlot, { visible: isGbestVisible }, gbestIndices);
                    }
                    btn.textContent = isGbestVisible ? 'gbestを非表示' : 'gbestを表示';
                }

                function toggleGbestVisibility() {
                    isGbestVisible = !isGbestVisible;
                    applyGbestVisibility();
                }

                function updatePlotlyGraphs() {
                    // 収束グラフの更新
                    fetch('/api/plotly/convergence').then(response => response.json()).then(data => {
                        if (data.error) { console.error('Convergence plot error:', data.error); return; }
                        if (data.plot) Plotly.newPlot('convergence-plot', JSON.parse(data.plot).data, JSON.parse(data.plot).layout, {responsive: true});
                    }).catch(err => console.error('Error loading convergence plot:', err));
                    
                    // 散布図の更新
                    fetch('/api/plotly/scatter').then(response => response.json()).then(data => {
                        if (data.error) { console.error('Scatter plot error:', data.error); return; }
                        if (data.plot) {
                            // newPlotでグラフを再描画し、完了後に表示状態を適用
                            Plotly.newPlot('scatter-plot', JSON.parse(data.plot).data, JSON.parse(data.plot).layout, {responsive: true})
                                .then(applyGbestVisibility);
                        }
                    }).catch(err => console.error('Error loading scatter plot:', err));
                }
                
                function updateAll() {
                    updateStatus();
                    updatePlotlyGraphs();
                }
                
                setInterval(updateAll, 60000); // 60秒ごとに更新
                window.onload = updateAll;
            </script>
        </head>
        <body>
            <div class="container">
                <h1><span style="font-size: 2em;">🔍</span> PSO リアルタイムモニター</h1>
                <div class="panel">
                    <h2>最適化状態: <span id="status" class="status status-waiting">waiting</span></h2>
                    <a href="/settings" target="_blank" class="settings-button">PSOの設定を確認</a>
                    <a href="/gbest" target="_blank" class="settings-button" style="margin-left:10px;">現在のgbest詳細</a>
                    <p style="font-size:14px; color:#6c757d; margin-bottom:5px;">*ステップは0から開始</p>
                    <table class="metric-table">
                        <thead><tr><th>処理中のステップ</th><th>最良適応度</th><th>粒子数</th><th>経過時間</th></tr></thead>
                        <tbody><tr><td><span id="iteration">0</span> / <span id="max-iteration">0</span></td><td id="fitness">inf</td><td id="particles">0</td><td id="time">0 min</td></tr></tbody>
                    </table>
                    <div class="progress-bar">
                        <div class="progress-text" id="progress-text">0%</div>
                        <div class="progress-fill" id="progress-fill"></div>
                    </div>
                </div>
                <div class="panel">
                    <h2>各世代のgbestの適応度と安全率</h2>
                    <p style="color: #6c757d;">※グラフは1分ごとに更新（ページのリロードでも更新）</p>
                    <div id="convergence-plot" style="width: 100%; height: 400px;"></div>
                </div>
                <div class="panel">
                    <h2>粒子群の評価値のプロット（探索を通しての粒子の位置<i>x</i>の評価値）
                        <button id="toggle-gbest-btn" onclick="toggleGbestVisibility()" class="settings-button" style="font-size: 12px; padding: 5px 10px; float: right;">gbestを表示</button>
                    </h2>
                    <div id="scatter-plot" style="width: 100%; height: 1000px;"></div>
                </div>
            </div>
        </body>
        </html>
        """
    
    def console_monitor(self):
        print("PSO Console Monitor")
        print("=" * 50)
        print("Waiting for PSO to start...")
        pso_started = False
        while self.running:
            try:
                if os.path.exists(REALTIME_DATA_FILE):
                    pso_started = True
                    with open(REALTIME_DATA_FILE, 'r') as f:
                        self.data = json.load(f)
                    
                    fitness_display = self.data.get('gbest_fitness', 0)
                    fitness_display = 'inf' if fitness_display >= 1e10 else f"{fitness_display:.2e}"

                    print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                          f"Iter: {self.data.get('iteration', 0)}/{self.data.get('max_iteration', 1) - 1} "
                          f"({self.data.get('progress', 0):.1f}%) "
                          f"Best: {fitness_display} "
                          f"Time: {self.data.get('elapsed_time', 0):.1f}s", end='', flush=True)
                elif pso_started:
                    print("\n\n✅ PSO Optimization Completed!")
                    self.running = False
                
                time.sleep(1)
            except KeyboardInterrupt:
                print("\n\nMonitoring stopped by user.")
                self.running = False
            except Exception as e:
                print(f"\nError: {e}")
                time.sleep(1)
    
    def start_web_ui(self, port=5001):
        if not HAS_FLASK:
            print("Flask not available. Using console mode only.")
            self.console_monitor()
            return

        _check_and_kill_process_on_port(port)

        def read_data():
            while self.running:
                try:
                    if os.path.exists(REALTIME_DATA_FILE):
                        with open(REALTIME_DATA_FILE, 'r') as f:
                            new_data = json.load(f)
                        with self.data_lock:
                            self.data = new_data
                    else:
                        # ファイルが存在しない場合、データをリセット
                        with self.data_lock:
                            self.data = None
                except json.JSONDecodeError:
                    # ファイルが部分的に書き込まれている可能性があるため、少し待って再試行
                    time.sleep(0.1)
                except Exception as e:
                    print(f"\nError in data reading thread: {e}")
                time.sleep(0.5)

        data_thread = threading.Thread(target=read_data, daemon=True)
        data_thread.start()

        print(f"Starting Web UI at http://localhost:{port}")
        print("Press Ctrl+C to stop monitoring")

        try:
            self.app.run(host='0.0.0.0', port=port, debug=False)
        except KeyboardInterrupt:
            print("\nStopping monitor...")
        finally:
            self.running = False

if __name__ == "__main__":
    monitor = PSOMonitor()
    web_port = 5001
    if len(sys.argv) > 1 and sys.argv[1] == '--console':
        monitor.console_monitor()
    else:
        monitor.start_web_ui(port=web_port)
