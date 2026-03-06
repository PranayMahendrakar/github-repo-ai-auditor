#!/usr/bin/env python3
"""
GitHub Repository AI Auditor - Core Analyzer
Uses open-source models (DistilGPT2 via HuggingFace Transformers) for analysis.
No API keys required - runs fully locally on GitHub Actions.
"""

import sys
import os
import json
import ast
import re
import hashlib
from pathlib import Path
from datetime import datetime
import networkx as nx

# ---------------------------------------------------------------------------
# File collection helpers
# ---------------------------------------------------------------------------

SUPPORTED_EXTENSIONS = {
    '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
    '.java': 'Java', '.cpp': 'C++', '.c': 'C', '.go': 'Go',
    '.rb': 'Ruby', '.php': 'PHP', '.rs': 'Rust', '.kt': 'Kotlin',
    '.cs': 'C#', '.html': 'HTML', '.css': 'CSS', '.md': 'Markdown',
    '.sh': 'Shell', '.yml': 'YAML', '.yaml': 'YAML', '.json': 'JSON',
}

IGNORE_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env',
    'dist', 'build', '.next', '.nuxt', 'coverage', '.pytest_cache',
    'target', 'vendor', 'bower_components',
}

SECURITY_PATTERNS = [
    (r'(?i)(password|passwd|pwd)\s*=\s*["\'\'][^\'"\']+["\'\']', 'Hardcoded password'),
    (r'(?i)(api_key|apikey|api-key)\s*=\s*["\'\'][^\'"\']+["\'\']', 'Hardcoded API key'),
    (r'(?i)(secret|token)\s*=\s*["\'\'][^\'"\']+["\'\']', 'Hardcoded secret/token'),
    (r'(?i)\beval\s*\(', 'Dangerous eval() usage'),
    (r'(?i)\bexec\s*\(', 'Dangerous exec() usage'),
    (r'(?i)subprocess\.call\(.*shell=True', 'Shell injection risk'),
    (r'(?i)os\.system\s*\(', 'OS command injection risk'),
    (r'(?i)pickle\.load', 'Unsafe deserialization (pickle)'),
    (r'(?i)yaml\.load\s*\([^,)]+\)', 'Unsafe YAML load (no Loader)'),
    (r'(?i)md5\s*\(|md5\s*=', 'Weak hashing (MD5)'),
    (r'(?i)\.execute\s*\(.*%.*\)', 'Potential SQL injection'),
    (r'(?i)TODO\s*:.*(?:security|vuln|hack|fixme|xxx)', 'Security TODO comment'),
]


def collect_files(repo_path: str) -> list[dict]:
    """Walk the repo and collect source files."""
    files = []
    root = Path(repo_path)
    for path in root.rglob('*'):
        # Skip ignored dirs
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix in SUPPORTED_EXTENSIONS:
            try:
                content = path.read_text(encoding='utf-8', errors='replace')
                rel = str(path.relative_to(root))
                files.append({
                    'path': rel,
                    'language': SUPPORTED_EXTENSIONS[path.suffix],
                    'content': content,
                    'lines': len(content.splitlines()),
                    'size_bytes': path.stat().st_size,
                })
            except Exception:
                pass
    return files


# ---------------------------------------------------------------------------
# Static analysis
# ---------------------------------------------------------------------------

def compute_code_quality(files: list[dict]) -> dict:
    """Compute code quality metrics from static analysis."""
    total_lines = sum(f['lines'] for f in files)
    total_files = len(files)
    lang_counts: dict[str, int] = {}
    issues = []
    complexity_scores = []

    for f in files:
        lang_counts[f['language']] = lang_counts.get(f['language'], 0) + 1

        # Security scan
        for pattern, label in SECURITY_PATTERNS:
            matches = re.findall(pattern, f['content'])
            if matches:
                issues.append({'file': f['path'], 'issue': label, 'count': len(matches)})

        # Python-specific: cyclomatic complexity via AST
        if f['language'] == 'Python':
            try:
                tree = ast.parse(f['content'])
                funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                for func in funcs:
                    branches = sum(1 for n in ast.walk(func) if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With, ast.Assert)))
                    complexity_scores.append(branches + 1)
            except SyntaxError:
                issues.append({'file': f['path'], 'issue': 'Python syntax error', 'count': 1})

    avg_complexity = round(sum(complexity_scores) / len(complexity_scores), 2) if complexity_scores else 1.0

    # Score: start at 100, deduct for issues and complexity
    deductions = min(len(issues) * 5 + max(0, avg_complexity - 5) * 2, 50)
    score = round(max(10, 100 - deductions), 1)

    return {
        'score': score,
        'total_files': total_files,
        'total_lines': total_lines,
        'languages': lang_counts,
        'avg_cyclomatic_complexity': avg_complexity,
        'security_issues': issues[:20],  # cap to 20
        'issue_count': len(issues),
    }


# ---------------------------------------------------------------------------
# Dependency graph
# ---------------------------------------------------------------------------

def build_dependency_graph(files: list[dict]) -> dict:
    """Build a simple import/dependency graph for Python and JS files."""
    G = nx.DiGraph()
    module_map: dict[str, str] = {}

    # Register modules
    for f in files:
        if f['language'] in ('Python', 'JavaScript', 'TypeScript'):
            name = f['path'].replace('/', '.').replace('\\', '.').rsplit('.', 1)[0]
            G.add_node(f['path'])
            module_map[name] = f['path']

    for f in files:
        if f['language'] == 'Python':
            try:
                tree = ast.parse(f['content'])
                for node in ast.walk(tree):
                    if isinstance(node, (ast.Import, ast.ImportFrom)):
                        if isinstance(node, ast.ImportFrom) and node.module:
                            target = node.module.replace('.', '/')
                            # Find matching file
                            for key, path in module_map.items():
                                if target in key:
                                    G.add_edge(f['path'], path)
                                    break
            except Exception:
                pass
        elif f['language'] in ('JavaScript', 'TypeScript'):
            imports = re.findall(r"(?:import|require)\s*\(?['\"](\.[^'\"]+)['\"\)]", f['content'])
            for imp in imports:
                for key, path in module_map.items():
                    if imp.lstrip('./') in key:
                        G.add_edge(f['path'], path)
                        break

    nodes = list(G.nodes())
    edges = [(u, v) for u, v in G.edges()]

    # Stats
    stats = {
        'node_count': G.number_of_nodes(),
        'edge_count': G.number_of_edges(),
        'nodes': nodes[:50],
        'edges': edges[:50],
        'most_imported': sorted([(n, G.in_degree(n)) for n in G.nodes()], key=lambda x: -x[1])[:5],
        'most_dependent': sorted([(n, G.out_degree(n)) for n in G.nodes()], key=lambda x: -x[1])[:5],
    }
    return stats


# ---------------------------------------------------------------------------
# AI Analysis using DistilGPT2 (small, fast, no API key)
# ---------------------------------------------------------------------------

def run_ai_analysis(files: list[dict], quality: dict) -> dict:
    """Run lightweight AI analysis using DistilGPT2 from HuggingFace Transformers."""
    try:
        from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
        import torch

        print("Loading DistilGPT2 model (this is a small ~82MB model)...")
        model_name = "distilgpt2"

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForCausalLM.from_pretrained(model_name)
        model.eval()

        generator = pipeline('text-generation', model=model, tokenizer=tokenizer,
                              device=-1, max_new_tokens=80, do_sample=False,
                              pad_token_id=tokenizer.eos_token_id)

        # Build a concise summary of the repo for the prompt
        top_langs = sorted(quality['languages'].items(), key=lambda x: -x[1])
        lang_summary = ', '.join(f"{k}({v})" for k, v in top_langs[:3])
        issue_summary = '; '.join(set(i['issue'] for i in quality['security_issues'][:3])) or 'none found'
        sample_files = [f['path'] for f in files[:5]]

        prompts = {
            'architecture': (
                f"Code repository analysis: {quality['total_files']} files, {quality['total_lines']} lines, "
                f"languages: {lang_summary}. Architecture pattern: "
            ),
            'improvements': (
                f"Software with complexity score {quality['avg_cyclomatic_complexity']} and {quality['issue_count']} issues. "
                f"Top 3 improvement suggestions: 1."
            ),
            'summary': (
                f"Repository has {quality['total_files']} files in {lang_summary}. Code quality score {quality['score']}/100. "
                f"Security issues: {issue_summary}. One sentence summary: "
            ),
        }

        results = {}
        for key, prompt in prompts.items():
            try:
                out = generator(prompt, truncation=True)[0]['generated_text']
                # Remove the prompt from output
                generated = out[len(prompt):].strip()
                # Clean up: take first 150 chars
                generated = generated.split('\n')[0][:150].strip()
                results[key] = generated if generated else "Analysis complete."
            except Exception as e:
                results[key] = f"Analysis unavailable: {str(e)[:50]}"

        return {
            'model_used': model_name,
            'architecture_analysis': results.get('architecture', ''),
            'improvement_suggestions': results.get('improvements', ''),
            'summary': results.get('summary', ''),
            'ai_available': True,
        }

    except ImportError as e:
        return {
            'model_used': 'none (transformers not available)',
            'architecture_analysis': _fallback_architecture(files, quality),
            'improvement_suggestions': _fallback_improvements(quality),
            'summary': _fallback_summary(quality),
            'ai_available': False,
        }
    except Exception as e:
        return {
            'model_used': 'distilgpt2 (error)',
            'architecture_analysis': _fallback_architecture(files, quality),
            'improvement_suggestions': _fallback_improvements(quality),
            'summary': _fallback_summary(quality),
            'ai_available': False,
            'error': str(e)[:100],
        }


def _fallback_architecture(files, quality):
    langs = list(quality['languages'].keys())
    if 'Python' in langs and 'JavaScript' in langs:
        return "Full-stack application with Python backend and JavaScript frontend."
    if 'Python' in langs:
        return "Python-based project, likely a backend service, CLI tool, or data pipeline."
    if 'JavaScript' in langs or 'TypeScript' in langs:
        return "JavaScript/TypeScript project, likely a web app or Node.js service."
    return f"Multi-language project using: {', '.join(langs[:3])}."


def _fallback_improvements(quality):
    tips = []
    if quality['issue_count'] > 0:
        tips.append(f"Address {quality['issue_count']} security issues found in static scan.")
    if quality['avg_cyclomatic_complexity'] > 10:
        tips.append("Reduce cyclomatic complexity by breaking large functions into smaller ones.")
    if quality['total_files'] > 50 and quality['languages'].get('Python', 0) > 0:
        tips.append("Consider adding type hints and docstrings for better maintainability.")
    if not tips:
        tips.append("Add comprehensive test coverage and CI/CD linting pipelines.")
    return ' '.join(tips[:3])


def _fallback_summary(quality):
    return (f"Repository with {quality['total_files']} files and {quality['total_lines']} lines of code. "
            f"Quality score: {quality['score']}/100.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 4:
        print("Usage: analyze.py <repo_path> <repo_url> <output_json>")
        sys.exit(1)

    repo_path, repo_url, output_path = sys.argv[1], sys.argv[2], sys.argv[3]

    print(f"Analyzing repository: {repo_url}")
    print(f"Local path: {repo_path}")

    files = collect_files(repo_path)
    print(f"Found {len(files)} source files")

    if not files:
        result = {
            'repo_url': repo_url,
            'timestamp': datetime.utcnow().isoformat(),
            'error': 'No source files found in repository',
        }
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(result, indent=2))
        sys.exit(0)

    quality = compute_code_quality(files)
    print(f"Code quality score: {quality['score']}")

    deps = build_dependency_graph(files)
    print(f"Dependency graph: {deps['node_count']} nodes, {deps['edge_count']} edges")

    ai = run_ai_analysis(files, quality)
    print(f"AI analysis complete (model: {ai['model_used']})")

    result = {
        'repo_url': repo_url,
        'timestamp': datetime.utcnow().isoformat(),
        'code_quality': quality,
        'dependency_graph': deps,
        'ai_analysis': ai,
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(result, indent=2))
    print(f"Report saved to {output_path}")


if __name__ == '__main__':
    main()
