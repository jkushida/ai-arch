#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PSO.pyにモニタリング機能を統合した例
既存のPSOクラスにモニタリング機能を追加
"""

import sys
import numpy as np
from PSO import PSO, Particle
from pso_monitor import PSOMonitor
from generate_building_fem_analyze import evaluate_building_from_params


class MonitoredPSO(PSO):
    """モニタリング機能付きPSOクラス"""
    
    def __init__(self, 
                 objective_func,
                 bounds,
                 n_particles=20,
                 max_iter=100,
                 enable_monitoring=True,
                 enable_live_plot=False,
                 enable_web_ui=False):
        """
        Args:
            enable_monitoring: モニタリングを有効化
            enable_live_plot: リアルタイムプロットを有効化
            enable_web_ui: Web UIを有効化
        """
        super().__init__(objective_func, bounds, n_particles, max_iter)
        
        self.enable_monitoring = enable_monitoring
        self.monitor = None
        
        if enable_monitoring:
            # パラメータ名の定義
            param_names = [
                'Lx', 'Ly', 'H1', 'H2', 'tf', 'tr', 'bc', 'hc', 'tw_ext',
                'wall_tilt_angle', 'window_ratio_2f', 'roof_morph', 'roof_shift',
                'balcony_depth', 'material_columns', 'material_floor1',
                'material_floor2', 'material_roof', 'material_walls', 'material_balcony'
            ]
            
            # モニタの初期化
            self.monitor = PSOMonitor(
                n_particles=n_particles,
                n_iterations=max_iter,
                n_dimensions=len(bounds),
                param_names=param_names[:len(bounds)]
            )
            
            # リアルタイムプロットの有効化
            if enable_live_plot:
                self.monitor.create_live_plot()
            
            # Web UIは自動的に起動される（Flask利用可能な場合）
            if enable_web_ui and hasattr(self.monitor, 'app'):
                print("Web monitoring UI available at http://localhost:5000")
    
    def optimize(self):
        """最適化の実行（モニタリング付き）"""
        
        # 初期評価
        for particle in self.particles:
            particle.evaluate(self.objective_func)
            # 初期のgbest更新
            if particle.cost < self.gbest_cost:
                self.gbest_position = particle.position.copy()
                self.gbest_cost = particle.cost
        
        print(f"初期最良値: {self.gbest_cost}")
        
        # メインループ
        for iteration in range(self.max_iter):
            # 通常のPSO更新
            for particle in self.particles:
                # 速度更新
                r1, r2 = np.random.random(2)
                particle.velocity = (
                    self.W * particle.velocity +
                    self.C1 * r1 * (particle.pbest_position - particle.position) +
                    self.C2 * r2 * (self.gbest_position - particle.position)
                )
                
                # 速度制限
                particle.velocity = np.clip(particle.velocity, -self.max_velocity, self.max_velocity)
                
                # 位置更新
                particle.position += particle.velocity
                particle.position = np.clip(particle.position, self.bounds[:, 0], self.bounds[:, 1])
                
                # 評価
                particle.evaluate(self.objective_func)
                
                # gbest更新
                if particle.cost < self.gbest_cost:
                    self.gbest_position = particle.position.copy()
                    self.gbest_cost = particle.cost
            
            # モニタリング更新
            if self.enable_monitoring and self.monitor:
                # 粒子の位置と評価値を収集
                particles_positions = np.array([p.position for p in self.particles])
                particles_values = np.array([p.cost for p in self.particles])
                
                # モニタを更新
                self.monitor.update(
                    iteration=iteration,
                    particles_positions=particles_positions,
                    particles_values=particles_values,
                    gbest_position=self.gbest_position,
                    gbest_value=self.gbest_cost
                )
                
                # リアルタイムプロットの更新
                if hasattr(self.monitor, 'plot_initialized') and self.monitor.plot_initialized:
                    self.monitor.update_live_plot()
            
            # 収束判定（オプション）
            if iteration > 10:
                recent_improvements = []
                for i in range(max(0, iteration-10), iteration):
                    if i < len(self.monitor.history['best_value'])-1:
                        improvement = abs(self.monitor.history['best_value'][i] - 
                                        self.monitor.history['best_value'][i+1])
                        recent_improvements.append(improvement)
                
                if recent_improvements and np.mean(recent_improvements) < 1e-6:
                    print(f"\n収束判定: {iteration}回で収束")
                    break
        
        # 最終レポートの保存
        if self.enable_monitoring and self.monitor:
            self.monitor.save_final_report()
        
        return self.gbest_position, self.gbest_cost


def objective_function_with_constraints(params):
    """
    建物評価関数（制約付き）
    最小化問題として定式化
    """
    # パラメータ辞書の作成
    param_names = [
        'Lx', 'Ly', 'H1', 'H2', 'tf', 'tr', 'bc', 'hc', 'tw_ext',
        'wall_tilt_angle', 'window_ratio_2f', 'roof_morph', 'roof_shift',
        'balcony_depth', 'material_columns', 'material_floor1',
        'material_floor2', 'material_roof', 'material_walls', 'material_balcony'
    ]
    
    # 材料パラメータは整数に変換
    params_dict = {}
    for i, name in enumerate(param_names):
        if i < len(params):
            if 'material' in name:
                params_dict[name] = int(round(params[i]))
            else:
                params_dict[name] = params[i]
    
    try:
        # 建物評価
        results = evaluate_building_from_params(params_dict)
        
        if results['status'] != 'success':
            return 1e10  # ペナルティ
        
        # 多目的最適化（重み付き和）
        # 最小化問題なので、良い値ほど小さくなるように変換
        safety_score = max(0, 2.0 - results['safety_factor'])  # 安全率2.0以上が目標
        cost_score = results['cost'] / 1e8  # 正規化
        co2_score = results['co2_emission'] / 1e5  # 正規化
        comfort_score = max(0, 10 - results['comfort_score'])  # 快適性は高いほど良い
        construct_score = max(0, 10 - results['constructability_score'])  # 施工性は高いほど良い
        
        # 重み付き和（調整可能）
        weights = {
            'safety': 10.0,    # 安全性を最重視
            'cost': 1.0,
            'co2': 0.5,
            'comfort': 0.3,
            'construct': 0.3
        }
        
        total_score = (
            weights['safety'] * safety_score +
            weights['cost'] * cost_score +
            weights['co2'] * co2_score +
            weights['comfort'] * comfort_score +
            weights['construct'] * construct_score
        )
        
        # 制約違反のペナルティ
        if results['safety_factor'] < 1.0:
            total_score += 1000  # 安全率1.0未満は大きなペナルティ
        
        return total_score
        
    except Exception as e:
        print(f"評価エラー: {e}")
        return 1e10


if __name__ == "__main__":
    # パラメータ範囲の定義
    bounds = np.array([
        [5.0, 20.0],      # Lx
        [4.0, 15.0],      # Ly
        [2.5, 5.0],       # H1
        [2.5, 4.0],       # H2
        [150, 400],       # tf
        [100, 300],       # tr
        [200, 600],       # bc
        [200, 600],       # hc
        [150, 300],       # tw_ext
        [-40.0, 30.0],    # wall_tilt_angle
        [0.0, 0.8],       # window_ratio_2f
        [0.0, 1.0],       # roof_morph
        [-1.0, 1.0],      # roof_shift
        [0.0, 3.0],       # balcony_depth
        [0, 1],           # material_columns
        [0, 1],           # material_floor1
        [0, 1],           # material_floor2
        [0, 1],           # material_roof
        [0, 1],           # material_walls
        [0, 1]            # material_balcony
    ])
    
    # モニタリング付きPSOの実行
    pso = MonitoredPSO(
        objective_func=objective_function_with_constraints,
        bounds=bounds,
        n_particles=20,
        max_iter=50,
        enable_monitoring=True,
        enable_live_plot=True,  # リアルタイムプロットを表示
        enable_web_ui=True      # Web UIを起動
    )
    
    print("PSO最適化を開始します...")
    print("モニタリング機能:")
    print("- コンソール出力: 有効")
    print("- リアルタイムプロット: 有効")
    print("- Web UI: http://localhost:5000")
    print("- ログ保存先: pso_logs/")
    print("")
    
    # 最適化実行
    best_position, best_value = pso.optimize()
    
    print("\n最適化完了!")
    print(f"最良値: {best_value}")
    print("最良パラメータ:")
    param_names = [
        'Lx', 'Ly', 'H1', 'H2', 'tf', 'tr', 'bc', 'hc', 'tw_ext',
        'wall_tilt_angle', 'window_ratio_2f', 'roof_morph', 'roof_shift',
        'balcony_depth', 'material_columns', 'material_floor1',
        'material_floor2', 'material_roof', 'material_walls', 'material_balcony'
    ]
    for name, value in zip(param_names, best_position):
        if 'material' in name:
            print(f"  {name}: {int(round(value))}")
        else:
            print(f"  {name}: {value:.4f}")