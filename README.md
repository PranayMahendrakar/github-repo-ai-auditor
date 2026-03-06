# 🤖 GitHub Repo AI Auditor

> Analyze **any public GitHub repository** with open-source AI models.
> Get instant reports on code quality, architecture, security risks, and improvement suggestions.
> **No API keys. No signup. 100% open-source.**

[![GitHub Pages](https://img.shields.io/badge/Live-GitHub%20Pages-blue?logo=github)](https://pranayMahendrakar.github.io/github-repo-ai-auditor)
[![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=github-actions)](https://github.com/PranayMahendrakar/github-repo-ai-auditor/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Model: DistilGPT2](https://img.shields.io/badge/Model-DistilGPT2-orange?logo=huggingface)](https://huggingface.co/distilgpt2)

---

## 🌐 Live Demo

**Frontend:** [https://pranayMahendrakar.github.io/github-repo-ai-auditor](https://pranayMahendrakar.github.io/github-repo-ai-auditor)

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **Code Quality Score** | 0–100 score based on cyclomatic complexity, file metrics, and issue count |
| 🏗️ **Architecture Analysis** | AI-generated description of project structure and design patterns |
| 🔐 **Security Risk Scan** | Static analysis for hardcoded secrets, SQL injection, unsafe functions |
| 💡 **Improvement Suggestions** | Actionable AI-generated improvement recommendations |
| 🕸️ **Dependency Graph** | Module-level import graph using NetworkX |
| 🌐 **Language Breakdown** | Visual breakdown of all programming languages used |

---

## ⚙️ Pipeline

```
Input: github.com/user/repo
         │
         ▼
  1. Clone repo (GitHub Actions)
         │
         ▼
  2. Parse code (AST + regex, supports 15+ languages)
         │
         ▼
  3. Build dependency graph (NetworkX)
         │
         ▼
  4. Run AI analysis (DistilGPT2 via HuggingFace Transformers)
         │
         ▼
  5. Generate HTML report (pushed to GitHub Pages)
         │
         ▼
Output: Beautiful report at GitHub Pages URL
```

---

## 🚀 Usage

### Option 1: GitHub Actions UI

1. Go to [Actions → GitHub Repo AI Auditor](https://github.com/PranayMahendrakar/github-repo-ai-auditor/actions/workflows/audit.yml)
2. Click **Run workflow**
3. Enter the repository URL (e.g. `github.com/torvalds/linux`)
4. Click **Run workflow** and wait ~5–10 minutes
5. The report will be published to the GitHub Pages URL

### Option 2: GitHub Pages Frontend

Visit the [live site](https://pranayMahendrakar.github.io/github-repo-ai-auditor), enter a repo URL, and click **Audit** to get step-by-step instructions.

---

## 📁 Project Structure

```
github-repo-ai-auditor/
├── .github/
│   └── workflows/
│       └── audit.yml          # GitHub Actions CI/CD pipeline
├── analyzer/
│   ├── analyze.py             # Core analysis engine (static + AI)
│   └── generate_report.py     # HTML report generator
├── docs/
│   ├── index.html             # GitHub Pages frontend
│   └── report.json            # Latest audit report (auto-generated)
└── README.md
```

---

## 🧠 AI Models Used

| Model | Size | Framework | Usage |
|---|---|---|---|
| **DistilGPT2** | ~82 MB | HuggingFace Transformers | Architecture analysis, improvement suggestions, summary |

> **Why DistilGPT2?** It's small enough to run within GitHub Actions' 7GB RAM / 6-hour timeout limits, requires no API keys, and is available on HuggingFace for free.

### Extending to Larger Models

To use a larger model (e.g. Phi-2, Mistral-7B), you have two options:

1. **Run locally**: Use [Ollama](https://ollama.com) or [llama.cpp](https://github.com/ggerganov/llama.cpp) on your machine and push results to GitHub
2. **Self-hosted runner**: Register a self-hosted GitHub Actions runner with more RAM/GPU

---

## 🔐 Security Analysis

The static security scanner checks for:

- Hardcoded passwords, API keys, tokens, and secrets
- Dangerous `eval()` and `exec()` calls
- Shell injection risks (`subprocess` with `shell=True`)
- OS command injection (`os.system()`)
- Unsafe deserialization (`pickle.load`, `yaml.load` without Loader)
- Weak hashing algorithms (MD5)
- SQL injection patterns
- Security-related TODO comments

---

## 🛠️ Local Development

```bash
# Clone this repo
git clone https://github.com/PranayMahendrakar/github-repo-ai-auditor.git
cd github-repo-ai-auditor

# Install dependencies
pip install transformers torch networkx radon pyflakes gitpython

# Clone a target repo to analyze
git clone https://github.com/some/repo target_repo

# Run the analyzer
python analyzer/analyze.py target_repo github.com/some/repo docs/report.json

# Generate HTML report
python analyzer/generate_report.py docs/report.json docs/report.html

# Open docs/report.html in your browser
```

---

## 📋 Requirements

- Python 3.11+
- `transformers` (HuggingFace)
- `torch` (CPU-only for GitHub Actions)
- `networkx`
- `radon`
- `pyflakes`
- `gitpython`

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Credits

Built by [PranayMahendrakar](https://github.com/PranayMahendrakar)

Powered by:
- [HuggingFace Transformers](https://huggingface.co/transformers/) — DistilGPT2 model
- [NetworkX](https://networkx.org/) — Dependency graph analysis
- [GitHub Actions](https://github.com/features/actions) — CI/CD pipeline
- [GitHub Pages](https://pages.github.com) — Frontend hosting
