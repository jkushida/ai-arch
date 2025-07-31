#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to HTML converter with GitHub Pages support
"""

import markdown
import os
from pathlib import Path

def convert_md_to_html(md_file_path, output_dir="docs"):
    """Convert Markdown file to HTML with proper styling for GitHub Pages"""
    
    # Read the markdown file
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Configure markdown extensions
    md = markdown.Markdown(extensions=[
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.tables',
        'markdown.extensions.toc',
        'markdown.extensions.nl2br',
        'markdown.extensions.attr_list'
    ])
    
    # Convert to HTML
    html_content = md.convert(md_content)
    
    # Create full HTML document with styling
    html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>generate_building_fem_analyze.py 詳細レポート</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background-color: #fff;
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            font-weight: 600;
            line-height: 1.25;
        }}
        
        h1 {{
            font-size: 2em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }}
        
        h2 {{
            font-size: 1.5em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }}
        
        h3 {{
            font-size: 1.25em;
        }}
        
        code {{
            background-color: rgba(27,31,35,0.05);
            border-radius: 3px;
            font-size: 85%;
            margin: 0;
            padding: 0.2em 0.4em;
        }}
        
        pre {{
            background-color: #f6f8fa;
            border-radius: 3px;
            font-size: 85%;
            line-height: 1.45;
            overflow: auto;
            padding: 16px;
        }}
        
        pre code {{
            background-color: transparent;
            border: 0;
            display: inline;
            line-height: inherit;
            margin: 0;
            overflow: visible;
            padding: 0;
            word-wrap: normal;
        }}
        
        table {{
            border-collapse: collapse;
            margin: 1em 0;
            display: block;
            overflow: auto;
            width: 100%;
        }}
        
        table th, table td {{
            border: 1px solid #dfe2e5;
            padding: 6px 13px;
        }}
        
        table th {{
            background-color: #f6f8fa;
            font-weight: 600;
        }}
        
        table tr {{
            background-color: #fff;
            border-top: 1px solid #c6cbd1;
        }}
        
        table tr:nth-child(2n) {{
            background-color: #f6f8fa;
        }}
        
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        
        a:hover {{
            text-decoration: underline;
        }}
        
        /* TOC styling */
        .toc {{
            background-color: #f6f8fa;
            border: 1px solid #d1d5da;
            border-radius: 3px;
            padding: 16px;
            margin-bottom: 16px;
        }}
        
        .toc ul {{
            list-style-type: none;
            padding-left: 1em;
        }}
        
        .toc > ul {{
            padding-left: 0;
        }}
        
        .toc li {{
            margin: 0.25em 0;
        }}
        
        /* Responsive design */
        @media (max-width: 767px) {{
            body {{
                padding: 1rem;
            }}
            
            table {{
                font-size: 14px;
            }}
        }}
        
        /* Print styles */
        @media print {{
            body {{
                max-width: 100%;
                padding: 0;
            }}
            
            pre {{
                white-space: pre-wrap;
            }}
        }}
        
        /* Custom styles for better readability */
        blockquote {{
            border-left: 4px solid #dfe2e5;
            color: #6a737d;
            padding-left: 1em;
            margin-left: 0;
        }}
        
        hr {{
            border: 0;
            border-top: 1px solid #eaecef;
            margin: 2em 0;
        }}
        
        /* Highlight important sections */
        strong {{
            font-weight: 600;
        }}
        
        em {{
            font-style: italic;
        }}
        
        /* Code syntax highlighting */
        .codehilite {{
            background-color: #f6f8fa;
            border-radius: 3px;
            padding: 16px;
            overflow: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        {html_content}
    </div>
    
    <script>
        // Smooth scrolling for anchor links
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
        
        // Add copy button to code blocks
        document.querySelectorAll('pre').forEach(pre => {{
            const button = document.createElement('button');
            button.textContent = 'Copy';
            button.style.cssText = 'position: absolute; top: 8px; right: 8px; padding: 4px 8px; font-size: 12px; cursor: pointer; background: #fff; border: 1px solid #d1d5da; border-radius: 3px;';
            button.onclick = () => {{
                const code = pre.querySelector('code');
                if (code) {{
                    navigator.clipboard.writeText(code.textContent);
                    button.textContent = 'Copied!';
                    setTimeout(() => button.textContent = 'Copy', 2000);
                }}
            }};
            pre.style.position = 'relative';
            pre.appendChild(button);
        }});
    </script>
</body>
</html>"""
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Write HTML file
    html_file_path = output_path / "index.html"
    with open(html_file_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"HTML file created: {html_file_path}")
    return html_file_path

if __name__ == "__main__":
    # Convert the markdown file
    md_file = "doc/generate_building_fem_analyze_report.md"
    html_file = convert_md_to_html(md_file)
    print(f"Conversion complete! HTML file saved to: {html_file}")