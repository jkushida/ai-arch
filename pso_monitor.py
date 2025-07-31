#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PSO探索のリアルタイムモニタリングシステム
複数の方法でPSOの進行状況を可視化・監視
"""

import os
import sys
import time
import json
import threading
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import matplotlib.patches as patches

# オプション: Web UIを使う場合
try:
    from flask import Flask, render_template, jsonify
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

# オプション: プログレスバーを使う場合
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


class PSOMonitor:
    """PSO探索の進行状況をモニタリングするクラス"""
    
    def __init__(self, 
                 n_particles: int,
                 n_iterations: int,
                 n_dimensions: int,
                 param_names: Optional[List[str]] = None,
                 log_dir: str = "pso_logs"):
        """
        Args:
            n_particles: 粒子数
            n_iterations: 最大反復回数
            n_dimensions: 次元数（パラメータ数）
            param_names: パラメータ名のリスト
            log_dir: ログ保存ディレクトリ
        """
        self.n_particles = n_particles
        self.n_iterations = n_iterations
        self.n_dimensions = n_dimensions
        self.param_names = param_names or [f"param_{i}" for i in range(n_dimensions)]
        self.log_dir = log_dir
        
        # ログディレクトリの作成
        os.makedirs(log_dir, exist_ok=True)
        
        # 実行IDの生成
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # データ記録用
        self.history = {
            'iteration': [],
            'best_value': [],
            'mean_value': [],
            'std_value': [],
            'best_position': [],
            'particles': [],
            'timestamp': []
        }
        
        # プログレスバー（利用可能な場合）
        self.pbar = None
        if TQDM_AVAILABLE:
            self.pbar = tqdm(total=n_iterations, desc="PSO Progress", 
                           ncols=100, leave=True)
        
        # リアルタイムプロット用
        self.fig = None
        self.axes = None
        self.plot_initialized = False
        
        # Web UI用（利用可能な場合）
        self.app = None
        self.socketio = None
        if FLASK_AVAILABLE:
            self._setup_web_ui()
    
    def update(self, 
               iteration: int,
               particles_positions: np.ndarray,
               particles_values: np.ndarray,
               gbest_position: np.ndarray,
               gbest_value: float):
        """
        探索状況を更新
        
        Args:
            iteration: 現在の反復回数
            particles_positions: 粒子の位置 (n_particles, n_dimensions)
            particles_values: 粒子の評価値 (n_particles,)
            gbest_position: 全体最良位置
            gbest_value: 全体最良値
        """
        # データの記録
        self.history['iteration'].append(iteration)
        self.history['best_value'].append(gbest_value)
        self.history['mean_value'].append(np.mean(particles_values))
        self.history['std_value'].append(np.std(particles_values))
        self.history['best_position'].append(gbest_position.tolist())
        self.history['particles'].append(particles_positions.tolist())
        self.history['timestamp'].append(datetime.now().isoformat())
        
        # プログレスバーの更新
        if self.pbar:
            self.pbar.update(1)
            self.pbar.set_postfix({
                'Best': f'{gbest_value:.4f}',
                'Mean': f'{np.mean(particles_values):.4f}',
                'Std': f'{np.std(particles_values):.4f}'
            })
        
        # コンソール出力（詳細モード）
        if iteration % 10 == 0:  # 10反復ごとに出力
            self._print_status(iteration, gbest_value, gbest_position)
        
        # CSVログの保存
        self._save_csv_log(iteration)
        
        # Web UIへの送信（利用可能な場合）
        if FLASK_AVAILABLE and self.socketio:
            self._emit_web_update(iteration, particles_positions, 
                                particles_values, gbest_position, gbest_value)
    
    def _print_status(self, iteration: int, gbest_value: float, gbest_position: np.ndarray):
        """コンソールに詳細状況を出力"""
        print(f"\n{'='*60}")
        print(f"Iteration: {iteration}/{self.n_iterations}")
        print(f"Best Value: {gbest_value:.6f}")
        print(f"Best Position:")
        for i, (name, value) in enumerate(zip(self.param_names, gbest_position)):
            print(f"  {name}: {value:.4f}")
        print(f"{'='*60}")
    
    def _save_csv_log(self, iteration: int):
        """CSVファイルにログを保存"""
        # 収束履歴
        convergence_file = os.path.join(self.log_dir, f"convergence_{self.run_id}.csv")
        convergence_df = pd.DataFrame({
            'iteration': self.history['iteration'],
            'best_value': self.history['best_value'],
            'mean_value': self.history['mean_value'],
            'std_value': self.history['std_value'],
            'timestamp': self.history['timestamp']
        })
        convergence_df.to_csv(convergence_file, index=False)
        
        # 最良解の詳細
        if iteration % 10 == 0:  # 10反復ごとに保存
            best_solution_file = os.path.join(self.log_dir, f"best_solution_{self.run_id}.csv")
            best_position = self.history['best_position'][-1]
            best_df = pd.DataFrame({
                'parameter': self.param_names,
                'value': best_position
            })
            best_df.to_csv(best_solution_file, index=False)
    
    def _setup_web_ui(self):
        """Web UIのセットアップ"""
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        @self.app.route('/')
        def index():
            return render_template('pso_monitor.html')
        
        @self.app.route('/api/history')
        def get_history():
            return jsonify(self.history)
        
        # Web UIを別スレッドで起動
        def run_web():
            self.socketio.run(self.app, port=5000, debug=False, allow_unsafe_werkzeug=True)
        
        web_thread = threading.Thread(target=run_web, daemon=True)
        web_thread.start()
        print("Web UI available at http://localhost:5000")
    
    def _emit_web_update(self, iteration, particles_positions, 
                        particles_values, gbest_position, gbest_value):
        """Web UIに更新を送信"""
        data = {
            'iteration': iteration,
            'best_value': float(gbest_value),
            'mean_value': float(np.mean(particles_values)),
            'std_value': float(np.std(particles_values)),
            'best_position': gbest_position.tolist(),
            'particles': {
                'positions': particles_positions.tolist(),
                'values': particles_values.tolist()
            }
        }
        self.socketio.emit('pso_update', data)
    
    def create_live_plot(self):
        """リアルタイムプロットの作成"""
        plt.ion()  # インタラクティブモード
        self.fig, self.axes = plt.subplots(2, 2, figsize=(12, 10))
        self.fig.suptitle('PSO Real-time Monitor', fontsize=16)
        
        # 収束曲線
        self.ax_convergence = self.axes[0, 0]
        self.ax_convergence.set_title('Convergence Curve')
        self.ax_convergence.set_xlabel('Iteration')
        self.ax_convergence.set_ylabel('Best Value')
        self.ax_convergence.grid(True)
        
        # 粒子分布（2Dプロジェクション）
        self.ax_particles = self.axes[0, 1]
        self.ax_particles.set_title('Particle Distribution (2D projection)')
        self.ax_particles.set_xlabel(self.param_names[0] if self.n_dimensions > 0 else 'Dim 0')
        self.ax_particles.set_ylabel(self.param_names[1] if self.n_dimensions > 1 else 'Dim 1')
        self.ax_particles.grid(True)
        
        # パラメータ値の箱ひげ図
        self.ax_params = self.axes[1, 0]
        self.ax_params.set_title('Parameter Distribution')
        self.ax_params.set_xlabel('Parameters')
        self.ax_params.set_ylabel('Value')
        
        # 多様性指標
        self.ax_diversity = self.axes[1, 1]
        self.ax_diversity.set_title('Population Diversity')
        self.ax_diversity.set_xlabel('Iteration')
        self.ax_diversity.set_ylabel('Standard Deviation')
        self.ax_diversity.grid(True)
        
        plt.tight_layout()
        self.plot_initialized = True
    
    def update_live_plot(self):
        """リアルタイムプロットを更新"""
        if not self.plot_initialized or len(self.history['iteration']) == 0:
            return
        
        # 収束曲線の更新
        self.ax_convergence.clear()
        self.ax_convergence.plot(self.history['iteration'], 
                               self.history['best_value'], 'b-', label='Best')
        self.ax_convergence.plot(self.history['iteration'], 
                               self.history['mean_value'], 'g--', label='Mean')
        self.ax_convergence.set_xlabel('Iteration')
        self.ax_convergence.set_ylabel('Value')
        self.ax_convergence.set_title('Convergence Curve')
        self.ax_convergence.legend()
        self.ax_convergence.grid(True)
        
        # 粒子分布の更新（最新の状態）
        if self.history['particles']:
            particles = np.array(self.history['particles'][-1])
            if particles.shape[1] >= 2:
                self.ax_particles.clear()
                self.ax_particles.scatter(particles[:, 0], particles[:, 1], 
                                        alpha=0.6, s=50)
                # 最良解を強調
                best_pos = np.array(self.history['best_position'][-1])
                self.ax_particles.scatter(best_pos[0], best_pos[1], 
                                        color='red', s=200, marker='*', 
                                        label='Global Best')
                self.ax_particles.set_xlabel(self.param_names[0])
                self.ax_particles.set_ylabel(self.param_names[1])
                self.ax_particles.set_title('Particle Distribution')
                self.ax_particles.legend()
                self.ax_particles.grid(True)
        
        # パラメータ分布の更新
        if self.history['particles']:
            particles = np.array(self.history['particles'][-1])
            self.ax_params.clear()
            self.ax_params.boxplot(particles.T, labels=self.param_names[:self.n_dimensions])
            self.ax_params.set_title('Parameter Distribution')
            self.ax_params.set_ylabel('Value')
            plt.setp(self.ax_params.xaxis.get_majorticklabels(), rotation=45)
        
        # 多様性の更新
        self.ax_diversity.clear()
        self.ax_diversity.plot(self.history['iteration'], 
                             self.history['std_value'], 'r-')
        self.ax_diversity.set_xlabel('Iteration')
        self.ax_diversity.set_ylabel('Standard Deviation')
        self.ax_diversity.set_title('Population Diversity')
        self.ax_diversity.grid(True)
        
        plt.tight_layout()
        plt.pause(0.1)  # プロットを更新
    
    def save_final_report(self):
        """最終レポートを保存"""
        if self.pbar:
            self.pbar.close()
        
        # 最終結果のサマリー
        report_file = os.path.join(self.log_dir, f"final_report_{self.run_id}.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"PSO Optimization Report\n")
            f.write(f"{'='*60}\n")
            f.write(f"Run ID: {self.run_id}\n")
            f.write(f"Total Iterations: {len(self.history['iteration'])}\n")
            f.write(f"Number of Particles: {self.n_particles}\n")
            f.write(f"Number of Dimensions: {self.n_dimensions}\n")
            f.write(f"\nFinal Results:\n")
            f.write(f"Best Value: {self.history['best_value'][-1]:.6f}\n")
            f.write(f"\nBest Position:\n")
            for name, value in zip(self.param_names, self.history['best_position'][-1]):
                f.write(f"  {name}: {value:.6f}\n")
            f.write(f"\nConvergence Statistics:\n")
            f.write(f"  Initial Best: {self.history['best_value'][0]:.6f}\n")
            f.write(f"  Final Best: {self.history['best_value'][-1]:.6f}\n")
            f.write(f"  Improvement: {self.history['best_value'][0] - self.history['best_value'][-1]:.6f}\n")
        
        # 最終プロットの保存
        plt.ioff()  # インタラクティブモードをオフ
        fig, axes = plt.subplots(2, 2, figsize=(12, 10))
        
        # 収束曲線
        axes[0, 0].plot(self.history['iteration'], self.history['best_value'], 'b-')
        axes[0, 0].set_xlabel('Iteration')
        axes[0, 0].set_ylabel('Best Value')
        axes[0, 0].set_title('Convergence History')
        axes[0, 0].grid(True)
        
        # その他のプロット...
        
        plt.tight_layout()
        plot_file = os.path.join(self.log_dir, f"final_plot_{self.run_id}.png")
        plt.savefig(plot_file, dpi=300)
        plt.close()
        
        print(f"\nOptimization completed!")
        print(f"Reports saved in: {self.log_dir}")
        print(f"  - Convergence data: convergence_{self.run_id}.csv")
        print(f"  - Final report: final_report_{self.run_id}.txt")
        print(f"  - Final plot: final_plot_{self.run_id}.png")


# 使用例
if __name__ == "__main__":
    # テストデータでデモ
    monitor = PSOMonitor(
        n_particles=20,
        n_iterations=100,
        n_dimensions=5,
        param_names=['width', 'depth', 'height', 'thickness', 'angle']
    )
    
    # リアルタイムプロットを有効化
    monitor.create_live_plot()
    
    # シミュレーション（実際のPSOループの代わり）
    for i in range(100):
        # ダミーデータ
        particles_pos = np.random.randn(20, 5)
        particles_val = np.random.randn(20)
        gbest_pos = np.random.randn(5)
        gbest_val = -i * 0.1 + np.random.randn() * 0.1
        
        monitor.update(i, particles_pos, particles_val, gbest_pos, gbest_val)
        monitor.update_live_plot()
        time.sleep(0.1)  # デモのため
    
    monitor.save_final_report()