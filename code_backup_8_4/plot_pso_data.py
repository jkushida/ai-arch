import pandas as pd
import plotly.express as px
import os

# CSVファイルのパス
CSV_FILE = "pso_optimization_log.csv"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(SCRIPT_DIR, CSV_FILE)

def generate_plotly_plots():
    if not os.path.exists(CSV_PATH):
        print(f"エラー: {CSV_FILE} が見つかりません。PSO最適化を実行してログファイルを生成してください。")
        return

    df = pd.read_csv(CSV_PATH)

    # 必要な列が存在するか確認
    required_cols = ['iteration', 'safety', 'cost', 'co2', 'comfort', 'constructability']
    if not all(col in df.columns for col in required_cols):
        print(f"エラー: {CSV_FILE} に必要な列 ({', '.join(required_cols)}) が含まれていません。")
        return

    # 無限大の値をNaNに変換し、プロットから除外
    df.replace([float('inf'), -float('inf')], pd.NA, inplace=True)
    df.dropna(subset=['safety', 'cost', 'co2', 'comfort', 'constructability'], inplace=True)

    # 世代をカテゴリカルデータとして扱う (この行は不要になるため削除)
    # df['iteration_str'] = df['iteration'].astype(str)

    # プロット設定
    plot_configs = [
        {'y_col': 'cost', 'y_label': '建設コスト (円/m²)', 'filename': 'plotly_safety_vs_cost.html'},
        {'y_col': 'co2', 'y_label': 'CO2排出量 (kg-CO2/m²)', 'filename': 'plotly_safety_vs_co2.html'},
        {'y_col': 'comfort', 'y_label': '快適性スコア', 'filename': 'plotly_safety_vs_comfort.html'},
        {'y_col': 'constructability', 'y_label': '施工性スコア', 'filename': 'plotly_safety_vs_constructability.html'}
    ]

    for config in plot_configs:
        fig = px.scatter(df,
                         x='safety',
                         y=config['y_col'],
                         color='iteration', # 数値型の 'iteration' を使用してグラデーションを適用
                         color_continuous_scale=px.colors.sequential.Viridis, # グラデーションのカラースケールを指定
                         title=f'PSO探索過程：安全率 vs {config["y_label"]}',
                         labels={'safety': '安全率', config['y_col']: config['y_label']},
                         hover_data=['iteration', 'particle', 'fitness', 'cost', 'safety', 'co2', 'comfort', 'constructability'])
        
        # 安全率2.0の基準線を追加
        fig.add_vline(x=2.0, line_width=2, line_dash="dash", line_color="red", annotation_text="安全率2.0（推奨値）", annotation_position="top right")

        # レイアウト調整
        fig.update_layout(
            xaxis_title='安全率',
            yaxis_title=config['y_label'],
            legend_title='世代',
            hovermode="closest"
        )
        
        # HTMLファイルとして保存
        output_path = os.path.join(SCRIPT_DIR, config['filename'])
        fig.write_html(output_path)
        print(f"✅ Plotlyグラフを {output_path} に保存しました。")

if __name__ == "__main__":
    generate_plotly_plots()
