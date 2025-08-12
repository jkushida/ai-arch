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
    <!-- Mermaidを先に読み込み、即座に初期化 -->
    <script src="https://unpkg.com/mermaid@10/dist/mermaid.min.js"></script>
    <script>
        // Mermaidを即座に初期化（MathJaxより先に処理）
        mermaid.initialize({{ 
            startOnLoad: false,
            logLevel: 'error',
            flowchart: {{
                useMaxWidth: true,
                htmlLabels: true,
                curve: 'linear',
                rankSpacing: 100,
                nodeSpacing: 80,
                padding: 30,
                diagramPadding: 10,
                rankDir: 'TB'
            }},
            theme: 'default',
            themeVariables: {{
                primaryColor: '#fff',
                primaryTextColor: '#000',
                primaryBorderColor: '#333',
                lineColor: '#333',
                secondaryColor: '#f9f',
                tertiaryColor: '#9f9'
            }}
        }});
    </script>
    
    <!-- MathJax for LaTeX (Mermaidの後に読み込み) -->
    <script>
        window.MathJax = {{
            tex: {{
                inlineMath: [['$', '$'], ['\\(', '\\)']],
                displayMath: [['$$', '$$'], ['\\[', '\\]']],
                processEscapes: true,
            }},
            options: {{
                skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code', 'annotation', 'annotation-xml'],
                ignoreHtmlClass: 'mermaid|tex2jax_ignore'
            }},
            startup: {{
                ready: () => {{
                    MathJax.startup.defaultReady();
                    if (MathJax.typesetPromise) {{
                        MathJax.typesetPromise();
                    }} else if (MathJax.typeset) {{
                        MathJax.typeset();
                    }}
                }}
            }}
        }};
    </script>
    <script id="MathJax-script" src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
        }}
        /* ---- Mermaid font sizing (force) ---- */
        .markdown-body .mermaid {{
            font-size: 28px !important; /* base for HTML labels */
            max-width: 100%;
            overflow-x: auto;
        }}
        .markdown-body .mermaid svg {{
            display: block;
            max-width: 100% !important;      /* fit to container */
            width: 100% !important;          /* scale down when needed */
            height: auto !important;
        }}
        /* SVG text (node titles, cluster labels) */
        .markdown-body .mermaid text,
        .markdown-body .mermaid .cluster-label,
        .markdown-body .mermaid .edgeLabel text {{
            font-size: 28px !important;
        }}
        /* HTML labels inside foreignObject (most node labels) */
        .markdown-body .mermaid .label foreignObject div,
        .markdown-body .mermaid .nodeLabel,
        .markdown-body .mermaid .edgeLabel .label,
        .markdown-body .mermaid .label > div {{
            font-size: 28px !important;
            line-height: 1.35 !important;
        }}
        /* Fallback: increase overall scale slightly on very small renders */
        .markdown-body .mermaid .label {{
            transform-origin: center center;
        }}
        /* --- Responsive scaling for Mermaid diagrams --- */
        @media (max-width: 1200px) {{
            .markdown-body .mermaid,
            .markdown-body .mermaid text,
            .markdown-body .mermaid .cluster-label,
            .markdown-body .mermaid .edgeLabel text,
            .markdown-body .mermaid .label foreignObject div,
            .markdown-body .mermaid .nodeLabel,
            .markdown-body .mermaid .edgeLabel .label,
            .markdown-body .mermaid .label > div {{
                font-size: 24px !important;
            }}
        }}
        @media (max-width: 900px) {{
            .markdown-body .mermaid,
            .markdown-body .mermaid text,
            .markdown-body .mermaid .cluster-label,
            .markdown-body .mermaid .edgeLabel text,
            .markdown-body .mermaid .label foreignObject div,
            .markdown-body .mermaid .nodeLabel,
            .markdown-body .mermaid .edgeLabel .label,
            .markdown-body .mermaid .label > div {{
                font-size: 20px !important;
            }}
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
                <li><a href="test_generate_building_usage.html">🧪 テストツール</a></li>
                <li><a href="PSO_usage.html">🚀 PSO使用ガイド</a></li>
            </ul>
            
            <h3>🔗 リンク</h3>
            <ul>
                <li><a href="https://github.com/jkushida/ai-arch" target="_blank">GitHub →</a></li>
            </ul>
        </nav>
        
        <main class="main-content">
            <article class="markdown-body tex2jax_process">
                {content}
            </article>
        </main>
    </div>
    
    <a href="#" class="back-to-top" id="back-to-top">↑ トップへ</a>
    
    <script>
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
        
        // MermaidとMathJaxの初期化順序を保証
        document.addEventListener('DOMContentLoaded', function() {{
            // 先にMermaidを初期化
            try {{
                mermaid.init();
            }} catch (e) {{
                console.error('Mermaid init error:', e);
            }}


            // MathJaxはスクリプトの読み込み完了後にtypesetを実行
            if (window.MathJax && window.MathJax.startup && window.MathJax.startup.promise) {{
                window.MathJax.startup.promise.then(function() {{
                    const root = document.querySelector('.markdown-body');
                    if (!root) return;
                    if (window.MathJax.typesetPromise) {{
                        window.MathJax.typesetPromise([root]);
                    }} else if (window.MathJax.typeset) {{
                        window.MathJax.typeset([root]);
                    }}
                }});
            }} else if (window.MathJax) {{
                // フォールバック（遅延してからtypeset）
                setTimeout(function() {{
                    const root = document.querySelector('.markdown-body');
                    if (!root) return;
                    if (window.MathJax.typesetPromise) {{
                        window.MathJax.typesetPromise([root]);
                    }} else if (window.MathJax.typeset) {{
                        window.MathJax.typeset([root]);
                    }}
                }}, 0);
            }}
        }});
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

def preprocess_math_and_mermaid(md_content):
    """数式とMermaidコードブロックを保護"""
    protected_blocks = {'mermaid': [], 'display_math': [], 'inline_math': []}
    counter = {'mermaid': 0, 'display_math': 0, 'inline_math': 0}
    
    # デバッグ: 元のコンテンツ内の数式をカウント（コメントアウト）
    # inline_math_count = len(re.findall(r'\$[^$]+?\$', md_content))
    # if inline_math_count > 0:
    #     print(f"Found {inline_math_count} inline math expressions to protect")
    
    # Mermaidブロックを置換
    def replace_mermaid(match):
        protected_blocks['mermaid'].append(match.group(1))
        placeholder = f"<!--MERMAID_BLOCK_{counter['mermaid']}-->"
        counter['mermaid'] += 1
        return placeholder
    
    # 数式ブロック（$$...$$）を保護
    def replace_display_math(match):
        protected_blocks['display_math'].append(match.group(0))
        placeholder = f"<!--DISPLAY_MATH_BLOCK_{counter['display_math']}-->"
        counter['display_math'] += 1
        return placeholder
    
    # インライン数式（$...$）を保護
    def replace_inline_math(match):
        protected_blocks['inline_math'].append(match.group(0))
        placeholder = f"<!--INLINE_MATH_BLOCK_{counter['inline_math']}-->"
        counter['inline_math'] += 1
        return placeholder
    
    # Mermaidブロックを置換
    md_content = re.sub(r'```mermaid\n(.*?)\n```', replace_mermaid, md_content, flags=re.DOTALL)
    
    # 数式ブロックを保護（$$...$$形式）- 先に処理
    md_content = re.sub(r'\$\$[^$]+?\$\$', replace_display_math, md_content, flags=re.DOTALL)
    
    # インライン数式を保護（$...$形式）- より厳密なパターン
    # バックスラッシュを含む数式にも対応
    md_content = re.sub(r'\$(?:[^$]|\\\$)+?\$', replace_inline_math, md_content)
    
    return md_content, protected_blocks

def _normalize_tex_backslashes(s: str) -> str:
    """
    数式中に意図せず二重になったバックスラッシュを1つに正規化する。
    例: '\\\\boldsymbol' -> '\\boldsymbol'
    注意: HTML全体ではなく数式の内側だけに適用すること。
    """
    # 連続する2つのバックスラッシュを1つに縮約（最短一致で繰り返し適用）
    return re.sub(r'\\\\', r'\\', s)

def restore_protected_blocks(html_content, protected_blocks):
    """保護したブロックを復元"""
    # Mermaidブロックを復元
    for i, block in enumerate(protected_blocks['mermaid']):
        placeholder = f"<!--MERMAID_BLOCK_{i}-->"
        mermaid_div = f'<div class="mermaid">{block}</div>'
        html_content = html_content.replace(f'<p>{placeholder}</p>', mermaid_div)
        html_content = html_content.replace(placeholder, mermaid_div)
    
    # ディスプレイ数式ブロックを復元
    for i, block in enumerate(protected_blocks.get('display_math', [])):
        placeholder = f"<!--DISPLAY_MATH_BLOCK_{i}-->"
        # もとの $$...$$ 形式に戻す（HTMLに直接埋め込む）
        m = re.match(r'^\$\$(.*)\$\$$', block, flags=re.DOTALL)
        inner = f'$$\\displaystyle {m.group(1)}$$' if m else block
        inner = _normalize_tex_backslashes(inner)
        html_content = html_content.replace(f'<p>{placeholder}</p>', f'\n{inner}\n')
        html_content = html_content.replace(placeholder, inner)

    # インライン数式を復元
    for i, block in enumerate(protected_blocks.get('inline_math', [])):
        placeholder = f"<!--INLINE_MATH_BLOCK_{i}-->"
        # もとの $...$ 形式に戻す
        m = re.match(r'^\$(.*)\$$', block, flags=re.DOTALL)
        inner = f'${m.group(1)}$' if m else block
        inner = _normalize_tex_backslashes(inner)
        html_content = html_content.replace(placeholder, inner)
    
    # 旧形式の数式ブロックも復元（後方互換性）
    for i, block in enumerate(protected_blocks.get('math', [])):
        placeholder = f"<!--MATH_BLOCK_{i}-->"
        html_content = html_content.replace(f'<p>{placeholder}</p>', block)
        html_content = html_content.replace(placeholder, block)
    
    return html_content

def convert_md_to_html(md_file):
    """MDファイルをHTMLに変換（サイドバー付き）"""
    
    # MDファイルを読み込み
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # 目次を抽出
    toc_html = extract_toc_from_markdown(md_content)
    
    # 数式とMermaidブロックを保護
    md_content_processed, protected_blocks = preprocess_math_and_mermaid(md_content)
    
    # Markdownをパース（$記号をエスケープしないように設定）
    md = markdown.Markdown(extensions=['extra', 'codehilite', 'tables', 'fenced_code'])
    html_content = md.convert(md_content_processed)
    
    # 保護したブロックを復元
    html_content = restore_protected_blocks(html_content, protected_blocks)
    
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
