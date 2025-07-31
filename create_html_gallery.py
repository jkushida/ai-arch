#!/usr/bin/env python3
"""CSVデータとPNG画像からHTMLギャラリーを生成"""

import pandas as pd
import os
from pathlib import Path

# 設定
CSV_FILE = "production_freecad_random_fem_evaluation.csv"
PNG_DIR = "png_outputs"
OUTPUT_HTML = "building_analysis_gallery.html"

def create_html_gallery():
    """HTMLギャラリーを生成"""
    
    # CSVファイルを読み込み
    print(f"📊 CSVファイルを読み込み中: {CSV_FILE}")
    df = pd.read_csv(CSV_FILE)
    
    # HTMLテンプレート
    html_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>建築物FEM解析ギャラリー</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: #333;
            margin-bottom: 40px;
        }
        .sample-card {
            background-color: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 25px;
            padding: 15px;
            overflow: hidden;
        }
        .sample-header {
            background-color: #2c3e50;
            color: white;
            padding: 10px;
            margin: -15px -15px 15px -15px;
            font-size: 1em;
            font-weight: bold;
        }
        .content-wrapper {
            display: grid;
            grid-template-columns: 0.5fr 2fr;
            gap: 15px;
        }
        .left-section {
            display: flex;
            flex-direction: column;
            gap: 15px;
        }
        .parameters-section {
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 8px;
        }
        .evaluation-section {
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 8px;
        }
        .images-grid-2x2 {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            grid-template-rows: repeat(2, 1fr);
            gap: 10px;
        }
        .section-title {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
            font-size: 0.95em;
        }
        .data-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.65em;
            border: 1px solid #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
        }
        .data-table td {
            border: 1px solid #e0e0e0;
            padding: 2px 5px;
        }
        .data-table td:first-child {
            color: #666;
            background-color: #f9f9f9;
        }
        .data-table td:last-child {
            font-weight: 500;
            color: #333;
            text-align: right;
        }
        .image-wrapper {
            display: flex;
            flex-direction: column;
        }
        .image-container {
            position: relative;
            background-color: #f0f0f0;
            border-radius: 8px 8px 0 0;
            overflow: hidden;
            aspect-ratio: 5/3;
        }
        .image-container img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            display: block;
        }
        .image-label {
            background-color: #333;
            color: white;
            padding: 4px;
            text-align: center;
            font-size: 0.7em;
            border-radius: 0 0 8px 8px;
            margin-top: 0;
        }
        .safety-factor {
            color: #28a745;
            font-weight: bold;
        }
        .safety-factor.low {
            color: #dc3545;
        }
        .safety-factor.medium {
            color: #ffc107;
        }
        .pattern-badge {
            display: inline-block;
            background-color: #e3f2fd;
            color: #1976d2;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.7em;
            margin-top: 5px;
        }
        .no-image {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
            color: #999;
            font-size: 0.9em;
        }
        @media (max-width: 768px) {
            .first-row {
                grid-template-columns: 1fr;
            }
            .bottom-images {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏗️ 建築物FEM解析ギャラリー</h1>
"""
    
    # 各サンプルのHTML生成
    sample_html = ""
    for idx, row in df.iterrows():
        # サンプル番号の抽出
        fcstd_path = row['fcstd_path']
        sample_name = Path(fcstd_path).stem if pd.notna(fcstd_path) else f"sample{idx+1}"
        
        # 安全率に応じた色分け
        safety_factor = row['safety_factor']
        safety_class = ""
        if safety_factor < 0.5:
            safety_class = "low"
        elif safety_factor < 1.0:
            safety_class = "medium"
        
        sample_html += f"""
        <div class="sample-card">
            <div class="sample-header">
                {sample_name.upper()} - {row['design_pattern']}
            </div>
            
            <div class="content-wrapper">
                <div class="left-section">
                    <div class="parameters-section">
                        <div class="section-title">📐 設計変数</div>
                        <table class="data-table">
                            <tr>
                                <td>建物幅 (Lx)</td>
                                <td>{row['Lx']:.2f} m</td>
                            </tr>
                            <tr>
                                <td>建物奥行 (Ly)</td>
                                <td>{row['Ly']:.2f} m</td>
                            </tr>
                            <tr>
                                <td>1階高 (H1)</td>
                                <td>{row['H1']:.2f} m</td>
                            </tr>
                            <tr>
                                <td>2階高 (H2)</td>
                                <td>{row['H2']:.2f} m</td>
                            </tr>
                            <tr>
                                <td>床スラブ厚 (tf)</td>
                                <td>{row['tf']:.0f} mm</td>
                            </tr>
                            <tr>
                                <td>屋根スラブ厚 (tr)</td>
                                <td>{row['tr']:.0f} mm</td>
                            </tr>
                            <tr>
                                <td>柱幅 (bc)</td>
                                <td>{row['bc']:.0f} mm</td>
                            </tr>
                            <tr>
                                <td>柱厚 (hc)</td>
                                <td>{row['hc']:.0f} mm</td>
                            </tr>
                            <tr>
                                <td>外壁厚 (tw_ext)</td>
                                <td>{row['tw_ext']:.0f} mm</td>
                            </tr>
                            <tr>
                                <td>壁傾斜角度</td>
                                <td>{row['wall_tilt_angle']:.1f}°</td>
                            </tr>
                            <tr>
                                <td>窓開口率</td>
                                <td>{row['window_ratio_2f']:.2f}</td>
                            </tr>
                            <tr>
                                <td>屋根形態</td>
                                <td>{row['roof_morph']:.2f}</td>
                            </tr>
                            <tr>
                                <td>屋根シフト</td>
                                <td>{row['roof_shift']:.2f}</td>
                            </tr>
                            <tr>
                                <td>バルコニー奥行</td>
                                <td>{row.get('balcony_depth', 0.0):.1f} m</td>
                            </tr>
                        </table>
                    </div>
                    
                    <div class="evaluation-section">
                        <div class="section-title">📊 評価指標</div>
                        <table class="data-table">
                            <tr>
                                <td>💰 コスト (円/m²)</td>
                                <td>¥{row['cost_per_sqm']:,.0f}</td>
                            </tr>
                            <tr>
                                <td>🌱 CO2排出量 (kg/m²)</td>
                                <td>{row['co2_per_sqm']:.1f}</td>
                            </tr>
                            <tr>
                                <td>😊 快適性スコア</td>
                                <td>{row['comfort_score']:.2f}</td>
                            </tr>
                            <tr>
                                <td>🔨 施工性スコア</td>
                                <td>{row['constructability_score']:.2f}</td>
                            </tr>
                            <tr>
                                <td>🛡️ 安全率</td>
                                <td class="safety-factor {safety_class}">{row['safety_factor']:.3f}</td>
                            </tr>
                            <tr>
                                <td>📏 床面積 (m²)</td>
                                <td>{row['floor_area']:.2f}</td>
                            </tr>
                            <tr>
                                <td>💴 総工費</td>
                                <td>¥{row['total_cost']:,.0f}</td>
                            </tr>
                        </table>
                        <div class="pattern-badge">{row['design_pattern']}</div>
                    </div>
                </div>
                
                <!-- 右側：2x2グリッドの画像 -->
                <div class="images-grid-2x2">
        """
        
        # 4つの画像を2x2グリッドで表示
        image_labels = ["アイソメトリック（南東）", "正面（南）", "側面（東）", "アイソメトリック（北西）"]
        for i in range(1, 5):
            img_path = f"{PNG_DIR}/{sample_name}_{i}.png"
            if os.path.exists(img_path):
                sample_html += f"""
                    <div class="image-wrapper">
                        <div class="image-container">
                            <img src="{img_path}" alt="{sample_name} {image_labels[i-1]}">
                        </div>
                        <div class="image-label">{image_labels[i-1]}</div>
                    </div>
                """
            else:
                sample_html += f"""
                    <div class="image-wrapper">
                        <div class="image-container">
                            <div class="no-image">画像なし</div>
                        </div>
                        <div class="image-label">{image_labels[i-1]}</div>
                    </div>
                """
        
        sample_html += """
                </div>
            </div>
        </div>
        """
    
    # HTMLの完成
    html_content = html_template + sample_html + """
    </div>
</body>
</html>
"""
    
    # HTMLファイルの保存
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✅ HTMLギャラリーを生成しました: {OUTPUT_HTML}")
    print(f"📊 {len(df)}件のサンプルを表示")

if __name__ == "__main__":
    create_html_gallery()