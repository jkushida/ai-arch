#!/usr/bin/env python3
"""
Markdown to HTML converter for documentation with sidebar TOC
MDファイルを更新したら、このスクリプトを実行してHTMLを生成
"""

import os
import re
import markdown
from pathlib import Path

# HTMLテンプレート（サイドバー付き）
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown-light.min.css">
    <script src="https://unpkg.com/mermaid@10/dist/mermaid.min.js"></script>
    
    <!-- MathJax for LaTeX -->
    <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
    <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <script>
        window.MathJax = {{
            tex: {{
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']]
            }}
        }};
    </script>
    
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        }}
        .container {{
            display: flex;
            min-height: 100vh;
        }}
        .sidebar {{
            width: 280px;
            background-color: #f6f8fa;
            border-right: 1px solid #e1e4e8;
            padding: 20px;
            overflow-y: auto;
            position: fixed;
            height: 100vh;
            box-sizing: border-box;
        }}
        .sidebar h3 {{
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #24292e;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .sidebar ul {{
            list-style: none;
            padding: 0;
            margin: 0 0 20px 0;
        }}
        .sidebar > ul > li {{
            margin-bottom: 8px;
        }}
        .sidebar ul ul {{
            margin-left: 16px;
            margin-top: 4px;
        }}
        .sidebar a {{
            color: #0366d6;
            text-decoration: none;
            font-size: 14px;
            display: block;
            padding: 4px 8px;
            border-radius: 4px;
            transition: background-color 0.2s;
        }}
        .sidebar a:hover {{
            background-color: #e1e4e8;
        }}
        .sidebar a.active {{
            background-color: #0366d6;
            color: white;
        }}
        .main-content {{
            flex: 1;
            margin-left: 280px;
            padding: 40px;
            max-width: 980px;
            box-sizing: border-box;
        }}
        .markdown-body {{
            box-sizing: border-box;
            min-width: 200px;
            max-width: 980px;
        }}
        .back-to-top {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background-color: #0366d6;
            color: white;
            padding: 10px 15px;
            border-radius: 20px;
            text-decoration: none;
            font-size: 14px;
            opacity: 0;
            transition: opacity 0.3s;
            cursor: pointer;
        }}
        .back-to-top.visible {{
            opacity: 0.9;
        }}
        .back-to-top:hover {{
            opacity: 1;
        }}
        @media (max-width: 768px) {{
            .sidebar {{
                display: none;
            }}
            .main-content {{
                margin-left: 0;
                padding: 20px;
            }}
        }}
    </style>
    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
</head>
<body>
    <div class="container">
        <nav class="sidebar">
            <h3>📑 目次</h3>
            {toc}
            
            <h3>📁 その他のドキュメント</h3>
            <ul>
                <li><a href="index.html">📚 ドキュメントホーム</a></li>
                <li><a href="generate_building_fem_analyze_report.html">📊 FEM解析システム</a></li>
                <li><a href="PSO_usage.html">🚀 PSO使用ガイド</a></li>
                <li><a href="test_generate_building_usage.html">🧪 テストツール</a></li>
                <li><a href="fem_optimization_comparison.html">📈 最適化手法比較</a></li>
            </ul>
            
            <h3>🔗 リンク</h3>
            <ul>
                <li><a href="https://github.com/jkushida/ai-arch" target="_blank">GitHub →</a></li>
            </ul>
        </nav>
        
        <main class="main-content">
            <article class="markdown-body">
                {content}
            </article>
        </main>
    </div>
    
    <a href="#" class="back-to-top" id="back-to-top">↑ トップへ</a>
    
    <script>
        // Mermaidコードブロックを処理
        document.querySelectorAll('pre code.language-mermaid').forEach((element, index) => {{
            const graphDefinition = element.textContent;
            const graphDiv = document.createElement('div');
            graphDiv.className = 'mermaid';
            graphDiv.textContent = graphDefinition;
            element.parentElement.replaceWith(graphDiv);
        }});
        
        // スムーズスクロール
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {{
                    target.scrollIntoView({{
                        behavior: 'smooth',
                        block: 'start'
                    }});
                }}
            }});
        }});
        
        // アクティブセクションのハイライト
        const sections = document.querySelectorAll('h1[id], h2[id], h3[id]');
        const navLinks = document.querySelectorAll('.sidebar a[href^="#"]');
        
        window.addEventListener('scroll', () => {{
            let current = '';
            sections.forEach(section => {{
                const sectionTop = section.offsetTop;
                const sectionHeight = section.offsetHeight;
                if (scrollY >= (sectionTop - 100)) {{
                    current = section.getAttribute('id');
                }}
            }});
            
            navLinks.forEach(link => {{
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + current) {{
                    link.classList.add('active');
                }}
            }});
            
            // Back to top ボタンの表示/非表示
            const backToTop = document.getElementById('back-to-top');
            if (window.scrollY > 300) {{
                backToTop.classList.add('visible');
            }} else {{
                backToTop.classList.remove('visible');
            }}
        }});
        
        // MathJax再処理
        if (window.MathJax) {{
            MathJax.typesetPromise();
        }}
    </script>
</body>
</html>
"""

def extract_toc_from_markdown(md_content):
    """Markdownから目次を抽出してHTML形式で生成（H2のみ）"""
    lines = md_content.split('\n')
    toc_items = []
    
    for line in lines:
        # H2を検出（大見出しのみ）
        if line.startswith('## '):
            title = line[3:].strip()
            id_text = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF-]', '', title).replace(' ', '-').lower()
            toc_items.append(f'<li><a href="#{id_text}">{title}</a></li>')
    
    if toc_items:
        return f'<ul>{"".join(toc_items)}</ul>'
    return '<ul><li>No sections found</li></ul>'

def add_ids_to_headings(html_content):
    """見出しにIDを追加（日本語対応）"""
    def add_id(match):
        tag = match.group(1)
        content = match.group(2)
        # IDを生成（日本語文字も含める）
        id_text = re.sub(r'[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF-]', '', content).replace(' ', '-').lower()
        return f'<{tag} id="{id_text}">{content}</{tag}>'
    
    # H1, H2, H3タグにIDを追加
    html_content = re.sub(r'<(h[1-3])>([^<]+)</\1>', add_id, html_content)
    return html_content

def preprocess_mermaid_blocks(md_content):
    """Mermaidコードブロックを一時的にプレースホルダーに置換"""
    mermaid_blocks = []
    counter = 0
    
    def replace_mermaid(match):
        nonlocal counter
        mermaid_blocks.append(match.group(1))
        placeholder = f"<!--MERMAID_BLOCK_{counter}-->"
        counter += 1
        return placeholder
    
    # ```mermaid ... ``` ブロックを検出して置換
    md_content = re.sub(r'```mermaid\n(.*?)\n```', replace_mermaid, md_content, flags=re.DOTALL)
    
    return md_content, mermaid_blocks

def restore_mermaid_blocks(html_content, mermaid_blocks):
    """プレースホルダーをMermaidのdivタグに戻す"""
    for i, block in enumerate(mermaid_blocks):
        placeholder = f"<!--MERMAID_BLOCK_{i}-->"
        mermaid_div = f'<div class="mermaid">\n{block}\n</div>'
        html_content = html_content.replace(f'<p>{placeholder}</p>', mermaid_div)
        html_content = html_content.replace(placeholder, mermaid_div)
    
    return html_content

def convert_md_to_html(md_file):
    """MDファイルをHTMLに変換（サイドバー付き）"""
    
    # MDファイルを読み込み
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 目次を抽出
    toc_html = extract_toc_from_markdown(md_content)
    
    # Mermaidブロックを一時的に置換
    md_content_processed, mermaid_blocks = preprocess_mermaid_blocks(md_content)
    
    # Markdownをパース
    md = markdown.Markdown(extensions=['extra', 'codehilite', 'tables', 'fenced_code'])
    html_content = md.convert(md_content_processed)
    
    # Mermaidブロックを復元
    html_content = restore_mermaid_blocks(html_content, mermaid_blocks)
    
    # 見出しにIDを追加
    html_content = add_ids_to_headings(html_content)
    
    # タイトルを取得（最初のH1から）
    title_match = re.search(r'^#\s+(.+)$', md_content, re.MULTILINE)
    if title_match:
        title = title_match.group(1)
    else:
        title = Path(md_file).stem.replace('_', ' ').title()
    
    # HTMLを生成
    html = HTML_TEMPLATE.format(
        title=title,
        toc=toc_html,
        content=html_content
    )
    
    # HTMLファイルとして保存
    html_file = md_file.replace('.md', '.html')
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ 生成: {html_file}")

def main():
    """docs内の全MDファイルを変換"""
    docs_dir = Path(__file__).parent
    
    for md_file in docs_dir.glob('*.md'):
        if md_file.name != 'README.md':  # READMEは除外
            convert_md_to_html(str(md_file))

if __name__ == '__main__':
    main()
    print("\n🎉 変換完了！")
