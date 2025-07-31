#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全率分析のインタラクティブHTMLを生成
"""

import pandas as pd
import json
import re

# CSVデータを読み込む
df = pd.read_csv('production_freecad_random_fem_evaluation2.csv')

# 成功したサンプルのみをフィルタリング
df_success = df[df['evaluation_status'] == 'success'].copy()

# 木材使用数を計算
material_cols = ['material_columns', 'material_floor1', 'material_floor2', 
                'material_roof', 'material_walls', 'material_balcony']
df_success['wood_count'] = df_success[material_cols].sum(axis=1)

# データを抽出
safety_factors = df_success['safety_factor'].tolist()
costs = df_success['cost_per_sqm'].tolist()
co2s = df_success['co2_per_sqm'].tolist()
comforts = df_success['comfort_score'].tolist()
constructabilities = df_success['constructability_score'].tolist()
wood_counts = df_success['wood_count'].tolist()

# サンプル番号を抽出（fcstd_pathから）
sample_numbers = []
for path in df_success['fcstd_path']:
    match = re.search(r'sample(\d+)\.FCStd', path)
    if match:
        sample_numbers.append(int(match.group(1)))
    else:
        sample_numbers.append(0)

# 設計変数を抽出
design_vars_list = []
design_var_names = ['Lx', 'Ly', 'H1', 'H2', 'tf', 'tr', 'bc', 'hc', 'tw_ext', 
                   'wall_tilt_angle', 'window_ratio_2f', 'roof_morph', 'roof_shift', 'balcony_depth']
for _, row in df_success.iterrows():
    design_vars = {}
    for var in design_var_names:
        design_vars[var] = row[var]
    design_vars_list.append(design_vars)

# HTMLファイルを生成
html_content = f'''<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>建築物安全率分析 - インタラクティブグラフ</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            text-align: center;
            color: #333;
            margin-bottom: 10px;
        }}
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}
        .graphs-container {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}
        .graph-wrapper {{
            background-color: #fafafa;
            border-radius: 8px;
            padding: 15px;
            border: 1px solid #e0e0e0;
        }}
        .graph-title {{
            text-align: center;
            font-weight: bold;
            color: #444;
            margin-bottom: 10px;
            font-size: 1.1em;
        }}
        .plot-container {{
            width: 100%;
            height: 350px;
            max-width: 700px;
            margin: 0 auto;
        }}
        .info-section {{
            background-color: #e3f2fd;
            padding: 20px;
            border-radius: 8px;
            margin-top: 30px;
        }}
        .info-section h3 {{
            margin-top: 0;
            color: #1976d2;
        }}
        .safety-zones {{
            margin-top: 15px;
            padding: 15px;
            background-color: #fff3e0;
            border-radius: 6px;
        }}
        .zone-item {{
            margin: 5px 0;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        .zone-danger {{ background-color: #ffebee; color: #c62828; }}
        .zone-warning {{ background-color: #fff8e1; color: #f57c00; }}
        .zone-safe {{ background-color: #e8f5e9; color: #2e7d32; }}
        .zone-excellent {{ background-color: #e1f5fe; color: #0277bd; }}
        .hover-container {{
            position: absolute;
            z-index: 1000;
            border: 2px solid #333;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            display: none;
            pointer-events: none;
            background: white;
            padding: 15px;
            max-width: 750px;
        }}
        .hover-content {{
            display: flex;
            gap: 15px;
            align-items: flex-start;
        }}
        .design-vars {{
            font-size: 12px;
            line-height: 1.4;
            min-width: 150px;
        }}
        .design-vars h4 {{
            margin: 0 0 8px 0;
            font-size: 14px;
            color: #333;
            border-bottom: 1px solid #ddd;
            padding-bottom: 4px;
        }}
        .design-var-item {{
            display: flex;
            justify-content: space-between;
            margin: 3px 0;
        }}
        .var-name {{
            font-weight: 500;
            color: #555;
        }}
        .var-value {{
            color: #222;
            font-family: monospace;
        }}
        .images-container {{
            display: flex;
            flex-direction: column;
            gap: 10px;
        }}
        .image-wrapper {{
            text-align: center;
        }}
        .image-label {{
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }}
        .hover-image img {{
            max-width: 450px;
            max-height: 300px;
            display: block;
            border: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏗️ 建築物安全率分析ダッシュボード</h1>
        <p class="subtitle">FEM解析による{len(df_success)}件のサンプルデータ</p>
        
        <div class="graphs-container">
            <div class="graph-wrapper">
                <div class="graph-title">💰 安全率 vs 建設コスト</div>
                <div id="plot1" class="plot-container"></div>
            </div>
            
            <div class="graph-wrapper">
                <div class="graph-title">🌱 安全率 vs CO2排出量</div>
                <div id="plot2" class="plot-container"></div>
            </div>
            
            <div class="graph-wrapper">
                <div class="graph-title">😊 安全率 vs 快適性スコア</div>
                <div id="plot3" class="plot-container"></div>
            </div>
            
            <div class="graph-wrapper">
                <div class="graph-title">🔨 安全率 vs 施工性スコア</div>
                <div id="plot4" class="plot-container"></div>
            </div>
        </div>
        
        <div class="info-section">
            <h3>📊 分析情報</h3>
            <p>各グラフの点にマウスを合わせると詳細値が表示されます。ズーム・パン機能でデータを詳しく探索できます。</p>
            
            <div class="safety-zones">
                <h4>🛡️ 安全率の目安</h4>
                <div class="zone-item zone-danger">危険領域: 0.5未満</div>
                <div class="zone-item zone-warning">注意領域: 0.5～1.0</div>
                <div class="zone-item zone-safe">安全領域: 1.0～2.0</div>
                <div class="zone-item zone-excellent">推奨領域: 2.0以上</div>
            </div>
        </div>
    </div>

    <div id="hoverContainer" class="hover-container">
        <div class="hover-content">
            <div class="design-vars" id="designVarsDisplay">
                <h4>設計変数</h4>
                <div id="designVarsList"></div>
            </div>
            <div class="images-container">
                <div class="image-wrapper">
                    <div class="image-label">アイソメトリック（南東）</div>
                    <div class="hover-image">
                        <img id="hoverImageContent1" src="" alt="Building visualization SE">
                    </div>
                </div>
                <div class="image-wrapper">
                    <div class="image-label">アイソメトリック（北西）</div>
                    <div class="hover-image">
                        <img id="hoverImageContent2" src="" alt="Building visualization NW">
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // データを直接埋め込み
        const safetyFactors = {json.dumps(safety_factors)};
        const costs = {json.dumps(costs)};
        const co2s = {json.dumps(co2s)};
        const comforts = {json.dumps(comforts)};
        const constructabilities = {json.dumps(constructabilities)};
        const sampleNumbers = {json.dumps(sample_numbers)};
        const designVars = {json.dumps(design_vars_list)};
        const woodCounts = {json.dumps(wood_counts)};
        
        // 設計変数の日本語名
        const varLabels = {{
            'Lx': 'X方向スパン',
            'Ly': 'Y方向スパン',
            'H1': '1階高',
            'H2': '2階高',
            'tf': '床スラブ厚',
            'tr': '屋根スラブ厚',
            'bc': '柱幅',
            'hc': '柱厚',
            'tw_ext': '外壁厚',
            'wall_tilt_angle': '壁傾斜角度',
            'window_ratio_2f': '窓開口率',
            'roof_morph': '屋根形態',
            'roof_shift': '屋根シフト',
            'balcony_depth': 'バルコニー奥行'
        }};
        
        // 単位
        const varUnits = {{
            'Lx': 'm',
            'Ly': 'm',
            'H1': 'm',
            'H2': 'm',
            'tf': 'mm',
            'tr': 'mm',
            'bc': 'mm',
            'hc': 'mm',
            'tw_ext': 'mm',
            'wall_tilt_angle': '°',
            'window_ratio_2f': '',
            'roof_morph': '',
            'roof_shift': '',
            'balcony_depth': 'm'
        }};
        
        // 共通のレイアウト設定
        const commonLayout = {{
            font: {{ family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' }},
            plot_bgcolor: '#fafafa',
            paper_bgcolor: '#fafafa',
            margin: {{ t: 30, r: 30, b: 50, l: 80 }},
            hovermode: 'closest',
            xaxis: {{
                title: '安全率',
                gridcolor: '#e0e0e0',
                range: [0, Math.max(...safetyFactors) * 1.1]
            }},
            shapes: [
                // 安全率の境界線
                {{
                    type: 'line',
                    x0: 0.5, y0: 0,
                    x1: 0.5, y1: 1,
                    yref: 'paper',
                    line: {{ color: 'orange', width: 2, dash: 'dash' }}
                }},
                {{
                    type: 'line',
                    x0: 1.0, y0: 0,
                    x1: 1.0, y1: 1,
                    yref: 'paper',
                    line: {{ color: 'green', width: 2, dash: 'dash' }}
                }},
                {{
                    type: 'line',
                    x0: 2.0, y0: 0,
                    x1: 2.0, y1: 1,
                    yref: 'paper',
                    line: {{ color: 'blue', width: 2, dash: 'dash' }}
                }}
            ]
        }};
        
        // カスタムカラースケール（7段階：青灰色→赤）
        const customColorscale = [
            [0, 'rgb(112, 128, 144)'],     // 0: 青灰色（コンクリート）
            [0.167, 'rgb(132, 112, 132)'], // 1: 青紫灰
            [0.333, 'rgb(152, 96, 120)'],  // 2: 紫赤
            [0.5, 'rgb(172, 80, 108)'],    // 3: 赤紫
            [0.667, 'rgb(192, 64, 96)'],   // 4: 深紅
            [0.833, 'rgb(212, 48, 84)'],   // 5: 赤
            [1, 'rgb(232, 32, 72)']        // 6: 鮮やかな赤（木材）
        ];
        
        // プロット1: 安全率 vs コスト
        const trace1 = {{
            x: safetyFactors,
            y: costs,
            mode: 'markers',
            type: 'scatter',
            marker: {{
                size: 8,
                color: woodCounts,
                colorscale: customColorscale,
                showscale: true,
                colorbar: {{ title: '木材使用数' }},
                cmin: 0,
                cmax: 6
            }},
            text: safetyFactors.map((sf, i) => 
                `安全率: ${{sf.toFixed(2)}}<br>` +
                `コスト: ¥${{Math.round(costs[i]).toLocaleString()}}/m²<br>` +
                `木材使用数: ${{woodCounts[i]}}/6<br>` +
                `サンプル: #${{sampleNumbers[i]}}`
            ),
            hoverinfo: 'text',
            customdata: sampleNumbers
        }};
        
        const layout1 = {{
            ...commonLayout,
            yaxis: {{ title: 'コスト (円/m²)', gridcolor: '#e0e0e0' }}
        }};
        
        Plotly.newPlot('plot1', [trace1], layout1, {{responsive: true}});
        
        // プロット2: 安全率 vs CO2
        const trace2 = {{
            x: safetyFactors,
            y: co2s,
            mode: 'markers',
            type: 'scatter',
            marker: {{
                size: 8,
                color: co2s,
                colorscale: 'Portland',
                showscale: true,
                colorbar: {{ title: 'CO2排出量<br>(kg/m²)' }}
            }},
            text: safetyFactors.map((sf, i) => 
                `安全率: ${{sf.toFixed(2)}}<br>` +
                `CO2: ${{co2s[i].toFixed(1)}} kg/m²<br>` +
                `サンプル: #${{sampleNumbers[i]}}`
            ),
            hoverinfo: 'text',
            customdata: sampleNumbers
        }};
        
        const layout2 = {{
            ...commonLayout,
            yaxis: {{ title: 'CO2排出量 (kg/m²)', gridcolor: '#e0e0e0' }}
        }};
        
        Plotly.newPlot('plot2', [trace2], layout2, {{responsive: true}});
        
        // プロット3: 安全率 vs 快適性
        const trace3 = {{
            x: safetyFactors,
            y: comforts,
            mode: 'markers',
            type: 'scatter',
            marker: {{
                size: 8,
                color: comforts,
                colorscale: 'RdYlGn',
                showscale: true,
                colorbar: {{ title: '快適性<br>スコア' }}
            }},
            text: safetyFactors.map((sf, i) => 
                `安全率: ${{sf.toFixed(2)}}<br>` +
                `快適性: ${{comforts[i].toFixed(2)}}/10<br>` +
                `サンプル: #${{sampleNumbers[i]}}`
            ),
            hoverinfo: 'text',
            customdata: sampleNumbers
        }};
        
        const layout3 = {{
            ...commonLayout,
            yaxis: {{ title: '快適性スコア', gridcolor: '#e0e0e0', range: [0, 10.5] }}
        }};
        
        Plotly.newPlot('plot3', [trace3], layout3, {{responsive: true}});
        
        // プロット4: 安全率 vs 施工性
        const trace4 = {{
            x: safetyFactors,
            y: constructabilities,
            mode: 'markers',
            type: 'scatter',
            marker: {{
                size: 8,
                color: constructabilities,
                colorscale: 'Blues',
                showscale: true,
                colorbar: {{ title: '施工性<br>スコア' }}
            }},
            text: safetyFactors.map((sf, i) => 
                `安全率: ${{sf.toFixed(2)}}<br>` +
                `施工性: ${{constructabilities[i].toFixed(2)}}/10<br>` +
                `サンプル: #${{sampleNumbers[i]}}`
            ),
            hoverinfo: 'text',
            customdata: sampleNumbers
        }};
        
        const layout4 = {{
            ...commonLayout,
            yaxis: {{ title: '施工性スコア', gridcolor: '#e0e0e0', range: [0, 10.5] }}
        }};
        
        Plotly.newPlot('plot4', [trace4], layout4, {{responsive: true}});
        
        // ホバーイベントのハンドラーを追加
        const plots = ['plot1', 'plot2', 'plot3', 'plot4'];
        const hoverContainer = document.getElementById('hoverContainer');
        const hoverImageContent1 = document.getElementById('hoverImageContent1');
        const hoverImageContent2 = document.getElementById('hoverImageContent2');
        const designVarsList = document.getElementById('designVarsList');
        
        plots.forEach(plotId => {{
            const plotElement = document.getElementById(plotId);
            
            plotElement.on('plotly_hover', function(data) {{
                if (data.points && data.points.length > 0) {{
                    const point = data.points[0];
                    const sampleNum = point.customdata;
                    const sampleIndex = data.points[0].pointIndex;
                    
                    // 画像パスを構築
                    const imagePath1 = `png_outputs/sample${{sampleNum}}_1.png`;
                    const imagePath2 = `png_outputs/sample${{sampleNum}}_4.png`;
                    
                    // デバッグ用：コンソールに表示
                    console.log(`Sample ${{sampleNum}}: ${{imagePath1}}, ${{imagePath2}}`);
                    
                    // 設計変数を表示
                    const vars = designVars[sampleIndex];
                    let varHtml = '';
                    for (const [key, value] of Object.entries(vars)) {{
                        const label = varLabels[key];
                        const unit = varUnits[key];
                        const displayValue = typeof value === 'number' && value % 1 !== 0 ? value.toFixed(2) : value;
                        varHtml += `<div class="design-var-item">
                            <span class="var-name">${{label}}:</span>
                            <span class="var-value">${{displayValue}}${{unit ? ' ' + unit : ''}}</span>
                        </div>`;
                    }}
                    designVarsList.innerHTML = varHtml;
                    
                    // 画像表示の準備（南東ビュー）
                    hoverImageContent1.src = imagePath1;
                    hoverImageContent1.onerror = function() {{
                        // 画像が見つからない場合の処理
                        const svg = `<svg width="450" height="300" xmlns="http://www.w3.org/2000/svg">
                            <rect width="450" height="300" fill="#f4f4f4"/>
                            <text x="225" y="150" text-anchor="middle" font-family="Arial" font-size="16" fill="#666">
                                <tspan x="225" dy="-10">Sample #${{sampleNum}}</tspan>
                                <tspan x="225" dy="20">Image not available</tspan>
                            </text>
                        </svg>`;
                        this.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svg)));
                    }};
                    
                    // 画像表示の準備（北西ビュー）
                    hoverImageContent2.src = imagePath2;
                    hoverImageContent2.onerror = function() {{
                        // 画像が見つからない場合の処理
                        const svg = `<svg width="450" height="300" xmlns="http://www.w3.org/2000/svg">
                            <rect width="450" height="300" fill="#f4f4f4"/>
                            <text x="225" y="150" text-anchor="middle" font-family="Arial" font-size="16" fill="#666">
                                <tspan x="225" dy="-10">Sample #${{sampleNum}}</tspan>
                                <tspan x="225" dy="20">Image not available</tspan>
                            </text>
                        </svg>`;
                        this.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svg)));
                    }};
                    
                    // マウス位置に画像を表示
                    const mouseX = data.event.clientX;
                    const mouseY = data.event.clientY;
                    
                    hoverContainer.style.left = (mouseX + 15) + 'px';
                    hoverContainer.style.top = (mouseY - 150) + 'px';
                    hoverContainer.style.display = 'block';
                }}
            }});
            
            plotElement.on('plotly_unhover', function() {{
                hoverContainer.style.display = 'none';
            }});
        }});
        
        console.log('データ数:', safetyFactors.length);
        console.log('安全率範囲:', Math.min(...safetyFactors).toFixed(2), '-', Math.max(...safetyFactors).toFixed(2));
    </script>
</body>
</html>'''

# HTMLファイルに書き込み
with open('safety_analysis_interactive.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✅ HTMLファイルを生成しました: safety_analysis_interactive.html")
print(f"📊 データ数: {len(df_success)}")
print(f"📈 安全率範囲: {df_success['safety_factor'].min():.2f} - {df_success['safety_factor'].max():.2f}")