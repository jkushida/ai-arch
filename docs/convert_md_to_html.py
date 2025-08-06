#!/usr/bin/env python3
"""
Markdown to HTML converter for documentation
MDファイルを更新したら、このスクリプトを実行してHTMLを生成
"""

import os
import markdown
from pathlib import Path

# HTMLテンプレート
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
                inlineMath: [['$', '$'], ['\\\\(', '\\\\)']],
                displayMath: [['$$', '$$'], ['\\\\[', '\\\\]']]
            }}
        }};
    </script>
    
    <style>
        body {{
            box-sizing: border-box;
            min-width: 200px;
            max-width: 980px;
            margin: 0 auto;
            padding: 45px;
        }}
        .markdown-body {{
            box-sizing: border-box;
            min-width: 200px;
            max-width: 980px;
        }}
    </style>
    <script>
        mermaid.initialize({{ startOnLoad: true }});
    </script>
</head>
<body>
    <article class="markdown-body">
        {content}
    </article>
    <script>
        // Mermaidコードブロックを処理
        document.querySelectorAll('pre code.language-mermaid').forEach((element, index) => {{
            const graphDefinition = element.textContent;
            const graphDiv = document.createElement('div');
            graphDiv.className = 'mermaid';
            graphDiv.textContent = graphDefinition;
            element.parentElement.replaceWith(graphDiv);
        }});
    </script>
</body>
</html>
"""

def convert_md_to_html(md_file):
    """MDファイルをHTMLに変換"""
    
    # MDファイルを読み込み
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Markdownをパース
    md = markdown.Markdown(extensions=['extra', 'codehilite', 'toc', 'tables', 'fenced_code'])
    html_content = md.convert(md_content)
    
    # タイトルを取得（最初のH1から）
    title = Path(md_file).stem.replace('_', ' ').title()
    
    # HTMLを生成
    html = HTML_TEMPLATE.format(
        title=title,
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