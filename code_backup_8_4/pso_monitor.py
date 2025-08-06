#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pso_monitor.py
PSO最適化のリアルタイムモニタリングツール
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import json
import os
import datetime
from collections import deque
import threading
import time

# Flask関連（オプション）
try:
    from flask import Flask, render_template, jsonify, Response
    from flask_cors import CORS
    import io
    import base64
    HAS_FLASK = True
except ImportError:
    HAS_FLASK = False
    print("Flask not installed. Web UI will be disabled.")

class PSOMonitor:
    """PSO最適化のモニタリングクラス"""
    
    def __init__(self, n_particles, max_iter, param_names=None):
        """
        Parameters:
        -----------
        n_particles : int
            粒子数
        max_iter : int
            最大反復回数
        param_names : list
            パラメータ名のリスト
        """
        self.n_particles = n_particles
        self.max_iter = max_iter - 1
        self.param_names = param_names or []
        
        # 履歴データ
        self.history = {
            'iteration': [],
            'gbest_fitness': [],
            'pbest_mean': [],
            'pbest_std': [],
            'particles': [],  # 各反復での全粒子の位置と適応度
            'computation_time': [],
            'safety_factor': [],
            'cost': [],
            'co2': [],
            'comfort': [],
            'constructability': []
        }
        
        # リアルタイムプロット用
        self.fig = None
        self.axes = None
        self.plot_initialized = False
        self.animation = None
        
        # Web UI用
        self.app = None
        self.web_thread = None
        if HAS_FLASK:
            self._setup_web_ui()
    
    def _setup_web_ui(self):
        """Flask Web UIのセットアップ"""
        self.app = Flask(__name__)
        CORS(self.app)
        
        @self.app.route('/')
        def index():
            return self._render_dashboard()
        
        @self.app.route('/api/status')
        def get_status():
            """現在の最適化状態を返す"""
            if not self.history['iteration']:
                return jsonify({'status': 'not_started'})
            
            current_iter = self.history['iteration'][-1]
            progress = (current_iter / self.max_iter) * 100
            
            return jsonify({
                'status': 'running' if current_iter < self.max_iter else 'completed',
                'iteration': current_iter,
                'max_iteration': self.max_iter,
                'progress': progress,
                'gbest_fitness': self.history['gbest_fitness'][-1] if self.history['gbest_fitness'] else None,
                'n_particles': self.n_particles,
                'computation_time': sum(self.history['computation_time'])
            })
        
        @self.app.route('/api/history')
        def get_history():
            """最適化履歴を返す"""
            return jsonify(self.history)
        
        @self.app.route('/api/convergence_plot')
        def get_convergence_plot():
            """収束曲線の画像を返す"""
            fig = self._create_convergence_plot()
            img = io.BytesIO()
            fig.savefig(img, format='png', dpi=100, bbox_inches='tight')
            img.seek(0)
            plt.close(fig)  # 正しいclose方法
            
            return Response(img.getvalue(), mimetype='image/png')
        
        @self.app.route('/api/particles_plot')
        def get_particles_plot():
            """粒子群分布の画像を返す"""
            fig = self._create_particles_plot()
            img = io.BytesIO()
            fig.savefig(img, format='png', dpi=100, bbox_inches='tight')
            img.seek(0)
            plt.close(fig)  # 正しいclose方法
            
            return Response(img.getvalue(), mimetype='image/png')
    
    def _render_dashboard(self):
        """ダッシュボードのHTML"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PSO Optimization Monitor</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .container { max-width: 1400px; margin: 0 auto; }
                .status-panel { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .metric { display: inline-block; margin: 10px 20px; }
                .metric-value { font-size: 24px; font-weight: bold; color: #2196F3; }
                .metric-label { font-size: 14px; color: #666; }
                .progress-bar { width: 100%; height: 20px; background-color: #e0e0e0; border-radius: 10px; overflow: hidden; }
                .progress-fill { height: 100%; background-color: #4CAF50; transition: width 0.3s ease; }
                .plot-container { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
                .plots-row { display: flex; gap: 20px; }
                .plot-box { flex: 1; }
                h1 { color: #333; }
                h2 { color: #555; margin-top: 30px; }
            </style>
            <script>
                function updateStatus() {
                    fetch('/api/status')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('iteration').textContent = data.iteration || 0;
                            document.getElementById('max-iteration').textContent = data.max_iteration || 0;
                            document.getElementById('fitness').textContent = data.gbest_fitness ? data.gbest_fitness.toFixed(6) : 'N/A';
                            document.getElementById('particles').textContent = data.n_particles || 0;
                            document.getElementById('time').textContent = data.computation_time ? data.computation_time.toFixed(1) + 's' : '0s';
                            document.getElementById('progress-fill').style.width = (data.progress || 0) + '%';
                            
                            // プロットを更新
                            document.getElementById('convergence-plot').src = '/api/convergence_plot?' + new Date().getTime();
                            document.getElementById('particles-plot').src = '/api/particles_plot?' + new Date().getTime();
                        });
                }
                
                // 1分ごとに更新
                setInterval(updateStatus, 60000);
                updateStatus();
            </script>
        </head>
        <body>
            <div class="container">
                <h1>🔬 PSO建築設計最適化モニター</h1>
                
                <div class="status-panel">
                    <h2>最適化状態</h2>
                    <div class="metric">
                        <div class="metric-label">反復回数</div>
                        <div class="metric-value"><span id="iteration">0</span> / <span id="max-iteration">0</span></div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">最良適応度</div>
                        <div class="metric-value" id="fitness">N/A</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">粒子数</div>
                        <div class="metric-value" id="particles">0</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">経過時間</div>
                        <div class="metric-value" id="time">0s</div>
                    </div>
                    
                    <div style="margin-top: 20px;">
                        <div class="metric-label">進捗</div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="progress-fill"></div>
                        </div>
                    </div>
                </div>
                
                <div class="plots-row">
                    <div class="plot-box">
                        <div class="plot-container">
                            <h2>収束曲線</h2>
                            <img id="convergence-plot" src="/api/convergence_plot" style="width: 100%;">
                        </div>
                    </div>
                    <div class="plot-box">
                        <div class="plot-container">
                            <h2>粒子群分布（安全率 vs コスト）</h2>
                            <img id="particles-plot" src="/api/particles_plot" style="width: 100%;">
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _create_convergence_plot(self):
        """収束曲線のプロット作成"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6))
        
        if self.history['iteration']:
            iterations = self.history['iteration']
            
            # 適応度の推移
            ax1.plot(iterations, self.history['gbest_fitness'], 'b-', linewidth=2, label='Global Best')
            if self.history['pbest_mean']:
                ax1.plot(iterations, self.history['pbest_mean'], 'g--', label='Mean of Personal Bests')
                if self.history['pbest_std']:
                    pbest_mean = np.array(self.history['pbest_mean'])
                    pbest_std = np.array(self.history['pbest_std'])
                    ax1.fill_between(iterations, 
                                   pbest_mean - pbest_std, 
                                   pbest_mean + pbest_std, 
                                   alpha=0.3, color='green')
            
            ax1.set_xlabel('Iteration')
            ax1.set_ylabel('Fitness Value')
            ax1.set_title('Convergence History')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            # 評価指標の推移
            if self.history['safety_factor']:
                ax2.plot(iterations, self.history['safety_factor'], 'r-', label='Safety Factor')
                ax2.axhline(y=2.0, color='r', linestyle='--', alpha=0.5)
                ax2.set_xlabel('Iteration')
                ax2.set_ylabel('Safety Factor')
                ax2.set_title('Safety Factor Evolution')
                ax2.legend()
                ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def _create_particles_plot(self):
        """粒子群分布のプロット作成（安全率 vs コスト）"""
        fig = plt.figure(figsize=(8, 6))
        ax = fig.add_subplot(111)
        
        if self.history['particles']:
            # カラーマップ設定
            import matplotlib.cm as cm
            colors = cm.rainbow(np.linspace(0, 1, len(self.history['particles'])))
            
            # 各世代の粒子をプロット
            for i, particles in enumerate(self.history['particles']):
                if particles and len(particles[0]) > 1:  # 位置と適応度のデータがある
                    # 各粒子の安全率とコストを取得
                    safety_values = []
                    cost_values = []
                    
                    # 履歴から対応する世代のデータを取得
                    if i < len(self.history['safety_factor']) and i < len(self.history['cost']):
                        # 簡易的に最良粒子のデータを使用（本来は全粒子のデータが必要）
                        safety = self.history['safety_factor'][i]
                        cost = self.history['cost'][i]
                        
                        # 散布図としてプロット
                        ax.scatter(safety, cost, c=[colors[i]], s=50, alpha=0.6, 
                                 label=f'Generation {i}' if i % 5 == 0 else '')
            
            # 安全率2.0の基準線
            ax.axvline(x=2.0, color='r', linestyle='--', alpha=0.5, label='Safety Factor = 2.0')
            
            ax.set_xlabel('Safety Factor')
            ax.set_ylabel('Cost (円/m²)')
            ax.set_title('Particle Distribution: Safety vs Cost')
            ax.grid(True, alpha=0.3)
            
            # 凡例（世代数が多い場合は一部のみ表示）
            if len(self.history['particles']) <= 10:
                ax.legend()
            else:
                ax.legend(loc='best', fontsize=8)
        
        plt.tight_layout()
        return fig
    
    def start_web_ui(self, port=5000):
        """Web UIを起動"""
        if not HAS_FLASK or not self.app:
            print("Flask is not available. Cannot start Web UI.")
            return
        
        def run_app():
            self.app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)
        
        self.web_thread = threading.Thread(target=run_app, daemon=True)
        self.web_thread.start()
        print(f"Web UI started at http://localhost:{port}")
    
    def update(self, iteration, gbest_fitness, pbest_mean, pbest_std, 
               particles_data=None, metrics=None, computation_time=0):
        """モニタリングデータを更新"""
        self.history['iteration'].append(iteration)
        self.history['gbest_fitness'].append(gbest_fitness)
        self.history['pbest_mean'].append(pbest_mean)
        self.history['pbest_std'].append(pbest_std)
        self.history['computation_time'].append(computation_time)
        
        if particles_data:
            self.history['particles'].append(particles_data)
        
        if metrics:
            for key in ['safety_factor', 'cost', 'co2', 'comfort', 'constructability']:
                if key in metrics:
                    self.history[key].append(metrics[key])
    
    def create_live_plot(self):
        """リアルタイムプロットの初期化"""
        plt.ion()  # インタラクティブモード
        self.fig, self.axes = plt.subplots(2, 2, figsize=(8, 6))
        self.fig.suptitle('PSO Optimization Real-time Monitor', fontsize=16)
        
        # 各サブプロットの設定
        self.axes[0, 0].set_title('Convergence Curve')
        self.axes[0, 0].set_xlabel('Iteration')
        self.axes[0, 0].set_ylabel('Fitness')
        
        self.axes[0, 1].set_title('Safety Factor')
        self.axes[0, 1].set_xlabel('Iteration')
        self.axes[0, 1].set_ylabel('Safety Factor')
        
        self.axes[1, 0].set_title('Cost Evolution')
        self.axes[1, 0].set_xlabel('Iteration')
        self.axes[1, 0].set_ylabel('Cost (円/m²)')
        
        self.axes[1, 1].set_title('Particle Distribution')
        self.axes[1, 1].set_xlabel('Parameter 1')
        self.axes[1, 1].set_ylabel('Parameter 2')
        
        for ax in self.axes.flat:
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        self.plot_initialized = True
    
    def update_live_plot(self):
        """リアルタイムプロットを更新"""
        if not self.plot_initialized or not self.history['iteration']:
            return
        
        # 各軸をクリア
        for ax in self.axes.flat:
            ax.clear()
        
        iterations = self.history['iteration']
        
        # 収束曲線
        self.axes[0, 0].plot(iterations, self.history['gbest_fitness'], 'b-', linewidth=2)
        self.axes[0, 0].set_title('Convergence Curve')
        self.axes[0, 0].set_xlabel('Iteration')
        self.axes[0, 0].set_ylabel('Fitness')
        
        # 安全率
        if self.history['safety_factor']:
            self.axes[0, 1].plot(iterations, self.history['safety_factor'], 'r-')
            self.axes[0, 1].axhline(y=2.0, color='r', linestyle='--', alpha=0.5)
            self.axes[0, 1].set_title('Safety Factor')
            self.axes[0, 1].set_xlabel('Iteration')
            self.axes[0, 1].set_ylabel('Safety Factor')
        
        # コスト
        if self.history['cost']:
            self.axes[1, 0].plot(iterations, self.history['cost'], 'g-')
            self.axes[1, 0].set_title('Cost Evolution')
            self.axes[1, 0].set_xlabel('Iteration')
            self.axes[1, 0].set_ylabel('Cost (円/m²)')
        
        # 粒子分布（最新の反復のみ）
        if self.history['particles'] and len(self.history['particles'][-1]) > 0:
            latest_particles = self.history['particles'][-1]
            if len(latest_particles[0]) >= 2:  # 少なくとも2次元
                x_coords = [p[0] for p in latest_particles]
                y_coords = [p[1] for p in latest_particles]
                self.axes[1, 1].scatter(x_coords, y_coords, alpha=0.6)
                self.axes[1, 1].set_title(f'Particle Distribution (Iter {iterations[-1]})')
                self.axes[1, 1].set_xlabel(self.param_names[0] if self.param_names else 'Parameter 1')
                self.axes[1, 1].set_ylabel(self.param_names[1] if len(self.param_names) > 1 else 'Parameter 2')
        
        for ax in self.axes.flat:
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.pause(0.01)  # プロットを更新
    
    def save_report(self, filename='pso_optimization_report.txt'):
        """最適化レポートを保存"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("PSO Optimization Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("Configuration:\n")
            f.write(f"  Number of particles: {self.n_particles}\n")
            f.write(f"  Maximum iterations: {self.max_iter}\n")
            f.write(f"  Total iterations run: {len(self.history['iteration'])}\n\n")
            
            if self.history['gbest_fitness']:
                f.write("Results:\n")
                f.write(f"  Best fitness achieved: {self.history['gbest_fitness'][-1]:.6f}\n")
                f.write(f"  Initial fitness: {self.history['gbest_fitness'][0]:.6f}\n")
                f.write(f"  Improvement: {((self.history['gbest_fitness'][0] - self.history['gbest_fitness'][-1]) / self.history['gbest_fitness'][0] * 100):.2f}%\n\n")
                
                if self.history['safety_factor']:
                    f.write(f"  Final safety factor: {self.history['safety_factor'][-1]:.3f}\n")
                if self.history['cost']:
                    f.write(f"  Final cost: {self.history['cost'][-1]:.0f} 円/m²\n")
                if self.history['co2']:
                    f.write(f"  Final CO2: {self.history['co2'][-1]:.0f} kg-CO2/m²\n")
            
            f.write(f"\nTotal computation time: {sum(self.history['computation_time']):.1f} seconds\n")
