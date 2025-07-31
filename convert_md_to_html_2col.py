#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Markdown to HTML converter with 2-column layout (TOC on left, content on right)
"""

import markdown
import re
from pathlib import Path

def extract_toc_from_html(html_content):
    """Extract TOC from converted HTML content"""
    # Find all headers with IDs
    headers = re.findall(r'<h([2-4])[^>]*id="([^"]+)"[^>]*>(?:<a[^>]*>)?([^<]+)(?:</a>)?</h[2-4]>', html_content)
    
    if not headers:
        return ""
    
    # Build TOC HTML
    html_toc = ['<h2>目次</h2>', '<ul>']
    prev_level = 2
    
    for level_str, anchor_id, title in headers:
        level = int(level_str)
        
        # Clean up title (remove any HTML tags)
        title = re.sub(r'<[^>]+>', '', title)
        
        # Close/open nested lists as needed
        if level > prev_level:
            html_toc.append('<ul>' * (level - prev_level))
        elif level < prev_level:
            html_toc.append('</ul>' * (prev_level - level))
        
        html_toc.append(f'<li><a href="#{anchor_id}">{title}</a></li>')
        prev_level = level
    
    # Close remaining lists
    if prev_level > 2:
        html_toc.append('</ul>' * (prev_level - 2))
    html_toc.append('</ul>')
    
    return '\n'.join(html_toc)

def convert_md_to_html_2col(md_file_path, output_dir="docs", output_filename=None):
    """Convert Markdown file to HTML with 2-column layout"""
    
    # Read the markdown file
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Remove TOC section from markdown content before conversion
    md_content_no_toc = re.sub(r'^###?\s*目次\s*\n(?:[-*]\s*.+\n)*', '', md_content, flags=re.MULTILINE)
    
    # Configure markdown extensions with headerid for auto ID generation
    md = markdown.Markdown(extensions=[
        'markdown.extensions.fenced_code',
        'markdown.extensions.codehilite',
        'markdown.extensions.tables',
        'markdown.extensions.nl2br',
        'markdown.extensions.attr_list',
        'markdown.extensions.extra',
        'markdown.extensions.toc'
    ], extension_configs={
        'markdown.extensions.toc': {
            'permalink': False,
            'toc_depth': 4,
            'anchorlink': True
        }
    })
    
    # Convert to HTML
    main_content = md.convert(md_content_no_toc)
    
    # Extract TOC from the converted HTML
    toc_content = extract_toc_from_html(main_content)
    
    # Create full HTML document with 2-column layout
    html_template = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>generate_building_fem_analyze.py 詳細レポート</title>
    <style>
        * {{
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }}
        
        .container {{
            display: flex;
            max-width: 1600px;
            margin: 0 auto;
            min-height: 100vh;
        }}
        
        /* Left sidebar for TOC */
        .sidebar {{
            width: 320px;
            background-color: #fff;
            border-right: 1px solid #e1e4e8;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            padding: 2rem 1rem;
        }}
        
        .sidebar h2 {{
            font-size: 1.2em;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #0366d6;
        }}
        
        .sidebar ul {{
            list-style: none;
            padding-left: 0;
            margin: 0;
        }}
        
        .sidebar ul ul {{
            padding-left: 1.5rem;
            margin-top: 0.25rem;
        }}
        
        .sidebar li {{
            margin: 0.5rem 0;
        }}
        
        .sidebar a {{
            color: #24292e;
            text-decoration: none;
            display: block;
            padding: 0.25rem 0;
            font-size: 0.9em;
            transition: color 0.2s;
        }}
        
        .sidebar a:hover {{
            color: #0366d6;
        }}
        
        .sidebar a.active {{
            color: #0366d6;
            font-weight: 600;
        }}
        
        /* Main content area */
        .main-content {{
            flex: 1;
            margin-left: 320px;
            background-color: #fff;
            padding: 2rem 3rem;
            min-height: 100vh;
        }}
        
        /* Content styling */
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 2rem;
            margin-bottom: 1rem;
            font-weight: 600;
            line-height: 1.25;
        }}
        
        h1 {{
            font-size: 2.5em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
            margin-top: 0;
        }}
        
        h2 {{
            font-size: 1.8em;
            border-bottom: 1px solid #eaecef;
            padding-bottom: 0.3em;
        }}
        
        h3 {{
            font-size: 1.4em;
        }}
        
        h4 {{
            font-size: 1.2em;
        }}
        
        code {{
            background-color: rgba(27,31,35,0.05);
            border-radius: 3px;
            font-size: 85%;
            margin: 0;
            padding: 0.2em 0.4em;
            font-family: SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace;
        }}
        
        pre {{
            background-color: #f6f8fa;
            border-radius: 6px;
            font-size: 85%;
            line-height: 1.45;
            overflow: auto;
            padding: 16px;
            margin: 1rem 0;
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
            margin: 1rem 0;
            width: 100%;
        }}
        
        table th, table td {{
            border: 1px solid #dfe2e5;
            padding: 8px 13px;
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
        
        blockquote {{
            border-left: 4px solid #dfe2e5;
            color: #6a737d;
            padding-left: 1em;
            margin-left: 0;
            margin-right: 0;
        }}
        
        hr {{
            border: 0;
            border-top: 1px solid #eaecef;
            margin: 2rem 0;
        }}
        
        /* Scroll indicator */
        .scroll-indicator {{
            position: fixed;
            top: 0;
            left: 320px;
            right: 0;
            height: 3px;
            background-color: #0366d6;
            transform-origin: left;
            transform: scaleX(0);
            transition: transform 0.2s;
            z-index: 1000;
        }}
        
        /* Mobile responsive */
        @media (max-width: 1024px) {{
            .sidebar {{
                transform: translateX(-100%);
                transition: transform 0.3s;
                z-index: 1000;
            }}
            
            .sidebar.open {{
                transform: translateX(0);
            }}
            
            .main-content {{
                margin-left: 0;
                padding: 1rem;
            }}
            
            .menu-toggle {{
                position: fixed;
                top: 1rem;
                left: 1rem;
                z-index: 1001;
                background: #0366d6;
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 4px;
                cursor: pointer;
            }}
            
            .scroll-indicator {{
                left: 0;
            }}
        }}
        
        @media (min-width: 1025px) {{
            .menu-toggle {{
                display: none;
            }}
        }}
        
        /* Print styles */
        @media print {{
            .sidebar {{
                display: none;
            }}
            
            .main-content {{
                margin-left: 0;
                padding: 0;
            }}
            
            pre {{
                white-space: pre-wrap;
            }}
        }}
        
        /* Copy button for code blocks */
        .code-container {{
            position: relative;
        }}
        
        .copy-button {{
            position: absolute;
            top: 8px;
            right: 8px;
            padding: 4px 8px;
            font-size: 12px;
            cursor: pointer;
            background: #fff;
            border: 1px solid #d1d5da;
            border-radius: 3px;
            opacity: 0;
            transition: opacity 0.2s;
        }}
        
        pre:hover .copy-button {{
            opacity: 1;
        }}
        
        /* Back to top button */
        .back-to-top {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: #0366d6;
            color: white;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.3s;
            border: none;
            font-size: 20px;
        }}
        
        .back-to-top.visible {{
            opacity: 1;
        }}
    </style>
</head>
<body>
    <button class="menu-toggle" onclick="toggleSidebar()">☰ 目次</button>
    
    <div class="scroll-indicator" id="scrollIndicator"></div>
    
    <div class="container">
        <nav class="sidebar" id="sidebar">
            {toc_content}
        </nav>
        
        <main class="main-content">
            {main_content}
        </main>
    </div>
    
    <button class="back-to-top" id="backToTop" onclick="scrollToTop()">↑</button>
    
    <script>
        // Toggle sidebar on mobile
        function toggleSidebar() {{
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('open');
        }}
        
        // Smooth scrolling for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {{
            anchor.addEventListener('click', function (e) {{
                e.preventDefault();
                const href = this.getAttribute('href');
                let target = null;
                const id = href.substring(1);
                
                // Strategy 1: Try exact match first
                try {{
                    // Escape special characters for querySelector
                    const escapedId = CSS.escape(id);
                    target = document.getElementById(escapedId);
                    if (!target) {{
                        target = document.querySelector('#' + escapedId);
                    }}
                }} catch (err) {{
                    console.warn('Escaped selector failed:', err);
                }}
                
                // Strategy 2: Try without escaping
                if (!target) {{
                    target = document.getElementById(id);
                }}
                
                // Strategy 3: Try normalized ID (convert to lowercase, remove special chars)
                if (!target) {{
                    // Normalize the ID by converting to the same format as markdown generates
                    const normalizedId = id.toLowerCase()
                        .replace(/[\s\-]+/g, '-')  // Replace spaces and hyphens with single hyphen
                        .replace(/[^\w\-\u4e00-\u9fa5\u3040-\u309f\u30a0-\u30ff]/g, ''); // Keep alphanumeric, hyphen, and Japanese chars
                    
                    target = document.getElementById(normalizedId);
                }}
                
                // Strategy 4: Find element whose ID starts with or contains the search term
                if (!target) {{
                    const searchTerm = id.toLowerCase().replace(/[\-\s]+/g, '');
                    const allElements = document.querySelectorAll('[id]');
                    
                    for (const el of allElements) {{
                        const elementId = el.id.toLowerCase().replace(/[\-\s]+/g, '');
                        if (elementId === searchTerm || elementId.includes(searchTerm)) {{
                            target = el;
                            break;
                        }}
                    }}
                }}
                
                if (target) {{
                    target.scrollIntoView({{
                        behavior: 'smooth',
                        block: 'start'
                    }});
                    
                    // Close sidebar on mobile after clicking
                    if (window.innerWidth <= 1024) {{
                        document.getElementById('sidebar').classList.remove('open');
                    }}
                }} else {{
                    console.error('Target not found for href:', href);
                    console.error('Searched for ID:', id);
                    
                    // Show first 10 available IDs for debugging
                    const allIds = Array.from(document.querySelectorAll('[id]')).map(el => el.id).filter(id => id);
                    console.log('Available IDs (first 10):', allIds.slice(0, 10));
                    console.log('Total IDs found:', allIds.length);
                }}
            }});
        }});
        
        // Active link highlighting in TOC
        const observerOptions = {{
            rootMargin: '-10% 0% -70% 0%'
        }};
        
        const observer = new IntersectionObserver(entries => {{
            entries.forEach(entry => {{
                const id = entry.target.getAttribute('id');
                const tocLink = document.querySelector(`.sidebar a[href="#${{id}}"]`);
                
                if (tocLink) {{
                    if (entry.intersectionRatio > 0) {{
                        document.querySelectorAll('.sidebar a').forEach(link => {{
                            link.classList.remove('active');
                        }});
                        tocLink.classList.add('active');
                    }}
                }}
            }});
        }}, observerOptions);
        
        // Observe all sections
        document.querySelectorAll('h1[id], h2[id], h3[id], h4[id]').forEach(section => {{
            observer.observe(section);
        }});
        
        // Scroll indicator
        window.addEventListener('scroll', () => {{
            const windowHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrolled = window.pageYOffset;
            const scrollPercentage = scrolled / windowHeight;
            document.getElementById('scrollIndicator').style.transform = `scaleX(${{scrollPercentage}})`;
            
            // Back to top button visibility
            const backToTop = document.getElementById('backToTop');
            if (scrolled > 300) {{
                backToTop.classList.add('visible');
            }} else {{
                backToTop.classList.remove('visible');
            }}
        }});
        
        // Back to top function
        function scrollToTop() {{
            window.scrollTo({{
                top: 0,
                behavior: 'smooth'
            }});
        }}
        
        // Add copy buttons to code blocks
        document.querySelectorAll('pre').forEach(pre => {{
            const wrapper = document.createElement('div');
            wrapper.className = 'code-container';
            pre.parentNode.insertBefore(wrapper, pre);
            wrapper.appendChild(pre);
            
            const button = document.createElement('button');
            button.className = 'copy-button';
            button.textContent = 'Copy';
            button.onclick = () => {{
                const code = pre.querySelector('code');
                if (code) {{
                    navigator.clipboard.writeText(code.textContent);
                    button.textContent = 'Copied!';
                    setTimeout(() => button.textContent = 'Copy', 2000);
                }}
            }};
            wrapper.appendChild(button);
        }});
    </script>
</body>
</html>"""
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Write HTML file
    if output_filename is None:
        output_filename = "index.html"
    html_file_path = output_path / output_filename
    with open(html_file_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"HTML file created: {html_file_path}")
    return html_file_path

if __name__ == "__main__":
    # Convert the markdown file
    md_file = "doc/generate_building_fem_analyze_report.md"
    
    # Generate with 2-column layout
    html_file_doc = convert_md_to_html_2col(md_file, "doc", "generate_building_fem_analyze_report.html")
    
    print(f"Conversion complete!")