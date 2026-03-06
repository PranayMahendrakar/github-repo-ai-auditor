#!/usr/bin/env python3
"""
Generate a beautiful HTML report from the JSON analysis output.
This file is part of the GitHub Repo AI Auditor pipeline.
"""

import sys
import json
from pathlib import Path
from datetime import datetime


def score_color(score: float) -> str:
    if score >= 80:
        return '#22c55e'   # green
    if score >= 60:
        return '#f59e0b'   # amber
    return '#ef4444'       # red


def score_label(score: float) -> str:
    if score >= 80:
        return 'Excellent'
    if score >= 60:
        return 'Good'
    if score >= 40:
        return 'Fair'
    return 'Needs Work'


def make_lang_bars(languages: dict) -> str:
    total = sum(languages.values()) or 1
    colors = ['#6366f1', '#06b6d4', '#f59e0b', '#22c55e', '#ec4899', '#8b5cf6']
    bars = []
    for i, (lang, count) in enumerate(sorted(languages.items(), key=lambda x: -x[1])[:6]):
        pct = round(count / total * 100, 1)
        color = colors[i % len(colors)]
        bars.append(f'''
        <div class="lang-bar-row">
          <span class="lang-name">{lang}</span>
          <div class="lang-bar-bg">
            <div class="lang-bar-fill" style="width:{pct}%;background:{color}"></div>
          </div>
          <span class="lang-pct">{pct}%</span>
        </div>''')
    return '\n'.join(bars)


def make_dep_graph(graph: dict) -> str:
    nodes = graph.get('nodes', [])[:20]
    edges = graph.get('edges', [])[:30]
    if not nodes:
        return '<p class="empty-state">No dependency data available.</p>'

    # Build a simple SVG-style visual list
    node_html = ''.join(f'<span class="dep-node">{n.split("/")[-1]}</span>' for n in nodes)
    edge_html = ''.join(
        f'<div class="dep-edge"><code>{u.split("/")[-1]}</code> → <code>{v.split("/")[-1]}</code></div>'
        for u, v in edges[:10]
    )
    return f'''
    <div class="dep-nodes">{node_html}</div>
    {f'<div class="dep-edges">{edge_html}</div>' if edge_html else ''}
    '''


def make_security_table(issues: list) -> str:
    if not issues:
        return '<p class="security-ok">✅ No security issues detected by static analysis.</p>'
    rows = ''
    for issue in issues[:15]:
        rows += f'''<tr>
          <td><code>{issue.get("file","?")}</code></td>
          <td><span class="badge-warn">{issue.get("issue","?")}</span></td>
          <td>{issue.get("count",1)}</td>
        </tr>'''
    return f'''<table class="sec-table">
      <thead><tr><th>File</th><th>Issue</th><th>Count</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>'''


def generate_html(data: dict) -> str:
    repo_url = data.get('repo_url', 'Unknown')
    timestamp = data.get('timestamp', datetime.utcnow().isoformat())
    error = data.get('error')

    if error:
        return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><title>Audit Error</title></head>
        <body><h1>Audit Failed</h1><p>{error}</p><p>Repository: {repo_url}</p></body></html>'''

    quality = data.get('code_quality', {})
    deps = data.get('dependency_graph', {})
    ai = data.get('ai_analysis', {})

    score = quality.get('score', 0)
    color = score_color(score)
    label = score_label(score)
    total_files = quality.get('total_files', 0)
    total_lines = quality.get('total_lines', 0)
    avg_cc = quality.get('avg_cyclomatic_complexity', 0)
    issue_count = quality.get('issue_count', 0)
    languages = quality.get('languages', {})
    security_issues = quality.get('security_issues', [])

    lang_bars = make_lang_bars(languages)
    dep_graph_html = make_dep_graph(deps)
    sec_table = make_security_table(security_issues)

    arch = ai.get('architecture_analysis', 'N/A')
    improvements = ai.get('improvement_suggestions', 'N/A')
    summary = ai.get('summary', 'N/A')
    model = ai.get('model_used', 'N/A')

    # Format timestamp nicely
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        ts_str = dt.strftime('%Y-%m-%d %H:%M UTC')
    except Exception:
        ts_str = timestamp

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AI Audit Report – {repo_url}</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background: #0f172a;
      color: #e2e8f0;
      min-height: 100vh;
    }}
    .hero {{
      background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 50%, #0c1a2e 100%);
      padding: 48px 24px 36px;
      text-align: center;
      border-bottom: 1px solid #1e293b;
    }}
    .hero h1 {{
      font-size: 2rem;
      font-weight: 700;
      background: linear-gradient(90deg, #818cf8, #38bdf8);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 8px;
    }}
    .hero .subtitle {{ color: #94a3b8; font-size: 0.9rem; }}
    .hero .repo-link {{
      display: inline-block;
      margin-top: 12px;
      padding: 6px 16px;
      background: #1e293b;
      border-radius: 20px;
      color: #38bdf8;
      font-size: 0.85rem;
      text-decoration: none;
      border: 1px solid #334155;
    }}
    .container {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 24px;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 20px;
      margin-bottom: 24px;
    }}
    .card {{
      background: #1e293b;
      border: 1px solid #334155;
      border-radius: 12px;
      padding: 24px;
    }}
    .card h2 {{
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: #94a3b8;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .score-circle {{
      width: 120px; height: 120px;
      border-radius: 50%;
      display: flex; flex-direction: column;
      align-items: center; justify-content: center;
      margin: 0 auto 16px;
      border: 4px solid {color};
      box-shadow: 0 0 30px {color}44;
    }}
    .score-num {{ font-size: 2.5rem; font-weight: 700; color: {color}; }}
    .score-lbl {{ font-size: 0.75rem; color: {color}; font-weight: 600; text-transform: uppercase; }}
    .stat-row {{ display: flex; justify-content: space-between; margin-bottom: 8px; color: #cbd5e1; font-size: 0.9rem; }}
    .stat-val {{ font-weight: 600; color: #f1f5f9; }}
    .lang-bar-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 8px; }}
    .lang-name {{ font-size: 0.8rem; width: 90px; color: #94a3b8; }}
    .lang-bar-bg {{ flex: 1; height: 8px; background: #334155; border-radius: 4px; overflow: hidden; }}
    .lang-bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.3s; }}
    .lang-pct {{ font-size: 0.75rem; color: #94a3b8; width: 40px; text-align: right; }}
    .ai-section {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px; margin-bottom: 24px; }}
    .ai-section h2 {{ font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: #94a3b8; margin-bottom: 16px; }}
    .ai-card {{ background: #0f172a; border-radius: 8px; padding: 16px; margin-bottom: 12px; border-left: 3px solid #6366f1; }}
    .ai-card h3 {{ font-size: 0.85rem; font-weight: 600; color: #818cf8; margin-bottom: 8px; }}
    .ai-card p {{ font-size: 0.9rem; color: #cbd5e1; line-height: 1.6; }}
    .model-badge {{ display: inline-flex; align-items: center; gap: 6px; background: #0f172a; border: 1px solid #334155; border-radius: 20px; padding: 4px 12px; font-size: 0.75rem; color: #94a3b8; margin-top: 8px; }}
    .sec-table {{ width: 100%; border-collapse: collapse; font-size: 0.85rem; }}
    .sec-table th {{ text-align: left; color: #94a3b8; font-weight: 600; padding: 8px 12px; border-bottom: 1px solid #334155; }}
    .sec-table td {{ padding: 8px 12px; border-bottom: 1px solid #1e293b; color: #cbd5e1; }}
    .sec-table td code {{ background: #0f172a; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; color: #38bdf8; word-break: break-all; }}
    .badge-warn {{ background: #7c2d12; color: #fbbf24; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }}
    .security-ok {{ color: #22c55e; font-size: 0.9rem; }}
    .dep-nodes {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }}
    .dep-node {{ background: #0f172a; border: 1px solid #334155; border-radius: 6px; padding: 4px 10px; font-size: 0.75rem; color: #38bdf8; }}
    .dep-edge {{ font-size: 0.8rem; color: #94a3b8; margin-bottom: 4px; }}
    .dep-edge code {{ background: #0f172a; padding: 1px 5px; border-radius: 3px; color: #818cf8; }}
    .empty-state {{ color: #64748b; font-size: 0.85rem; }}
    .footer {{ text-align: center; padding: 24px; color: #475569; font-size: 0.8rem; border-top: 1px solid #1e293b; }}
    .footer a {{ color: #38bdf8; text-decoration: none; }}
    @media (max-width: 600px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}
  </style>
</head>
<body>
  <div class="hero">
    <h1>🤖 AI Repository Auditor</h1>
    <p class="subtitle">Powered by open-source LLMs · No API keys required · {ts_str}</p>
    <a class="repo-link" href="https://{repo_url.replace('github.com/', 'github.com/')}" target="_blank">
      📦 {repo_url}
    </a>
  </div>

  <div class="container">

    <!-- Row 1: Score + Stats -->
    <div class="grid-2">
      <div class="card">
        <h2>📊 Code Quality Score</h2>
        <div class="score-circle">
          <span class="score-num">{score}</span>
          <span class="score-lbl">{label}</span>
        </div>
        <div class="stat-row"><span>Total Files</span><span class="stat-val">{total_files:,}</span></div>
        <div class="stat-row"><span>Total Lines</span><span class="stat-val">{total_lines:,}</span></div>
        <div class="stat-row"><span>Avg Complexity</span><span class="stat-val">{avg_cc}</span></div>
        <div class="stat-row"><span>Issues Found</span><span class="stat-val">{issue_count}</span></div>
      </div>

      <div class="card">
        <h2>🌐 Language Breakdown</h2>
        {lang_bars if lang_bars else '<p class="empty-state">No language data.</p>'}
      </div>
    </div>

    <!-- Row 2: AI Analysis -->
    <div class="ai-section">
      <h2>🧠 AI Analysis <span class="model-badge">⚡ {model}</span></h2>
      <div class="ai-card">
        <h3>🏗️ Architecture Analysis</h3>
        <p>{arch}</p>
      </div>
      <div class="ai-card">
        <h3>💡 Improvement Suggestions</h3>
        <p>{improvements}</p>
      </div>
      <div class="ai-card" style="border-left-color: #06b6d4">
        <h3>📝 Summary</h3>
        <p>{summary}</p>
      </div>
    </div>

    <!-- Row 3: Security + Dependencies -->
    <div class="grid-2">
      <div class="card">
        <h2>🔐 Security Risks</h2>
        {sec_table}
      </div>

      <div class="card">
        <h2>🔗 Dependency Graph</h2>
        <div class="stat-row">
          <span>Modules</span><span class="stat-val">{deps.get("node_count",0)}</span>
        </div>
        <div class="stat-row">
          <span>Dependencies</span><span class="stat-val">{deps.get("edge_count",0)}</span>
        </div>
        {dep_graph_html}
      </div>
    </div>

  </div>

  <div class="footer">
    Generated by
    <a href="https://github.com/PranayMahendrakar/github-repo-ai-auditor">GitHub Repo AI Auditor</a>
    · Open-source · No API keys required ·
    Model: {model}
  </div>
</body>
</html>'''


def main():
    if len(sys.argv) < 3:
        print("Usage: generate_report.py <report.json> <output.html>")
        sys.exit(1)

    report_path = sys.argv[1]
    output_path = sys.argv[2]

    data = json.loads(Path(report_path).read_text())
    html = generate_html(data)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(html, encoding='utf-8')
    print(f"HTML report written to {output_path}")


if __name__ == '__main__':
    main()
