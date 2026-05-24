<div align="center">

<!-- Animated Typing Header -->
<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=24&duration=2500&pause=700&color=FF006E&center=true&vCenter=true&width=550&lines=ToolSmith+Agent;Discover.+Analyze.+Build.+Ship." alt="Typing Animation" />

<br>

<!-- Cyberpunk Banner -->
<img src="https://capsule-render.vercel.app/api?type=venom&color=0:0f0c29,50:302b63,100:24243e&height=150&section=header&text=ToolSmith%20Agent&fontSize=35&fontColor=00d4ff&animation=fadeIn&fontAlignY=55&desc=Autonomous%20agent%20that%20discovers%20trending%20tools%20and%20builds%20better%20alternatives&descSize=14&descAlignY=75&descColor=a8a8b3" width="100%" />

<br><br>

<!-- Badges -->
<a href="https://github.com/GrooveXlabs/toolsmith-agent">
  <img src="https://img.shields.io/badge/🔒%20Security-First-ff006e?style=for-the-badge&labelColor=0f0c29" />
</a>
<a href="https://github.com/GrooveXlabs/toolsmith-agent">
  <img src="https://img.shields.io/badge/🤖%20Agent-Active-00d4ff?style=for-the-badge&labelColor=0f0c29" />
</a>
<a href="https://github.com/GrooveXlabs/toolsmith-agent">
  <img src="https://img.shields.io/badge/🐍%20Python-3.10+-3776AB?style=for-the-badge&labelColor=0f0c29" />
</a>
<a href="https://github.com/GrooveXlabs/toolsmith-agent">
  <img src="https://img.shields.io/badge/📡%20Open%20Source-Always-7b2cbf?style=for-the-badge&labelColor=0f0c29" />
</a>
<a href="LICENSE">
  <img src="https://img.shields.io/badge/📜%20License-MIT-00d4ff?style=for-the-badge&labelColor=0f0c29" />
</a>

<br><br>

<!-- Divider -->
<img src="https://raw.githubusercontent.com/andreasbm/readme/master/assets/lines/colored.png" width="100%" />

</div>

## 🔨 Overview

**ToolSmith Agent** is an autonomous agent that discovers trending developer tools, analyzes their architecture, identifies gaps, and builds improved alternatives — automatically pushed to GrooveXlabs.

It runs a **5-gate gstack review pipeline** to ensure every generated project meets production-grade standards.

---

## ✨ What It Does

| Phase | Icon | Description |
|-------|------|-------------|
| **1. Discover** | 🔍 | Scans GitHub Trending, Product Hunt, and Hacker News for hot dev tools |
| **2. Analyze** | 🧠 | Deep-dives into architecture, tech stack, features, and user pain points |
| **3. Ideate** | 💡 | Generates unique improvements, missing features, and better UX approaches |
| **4. Build** | ⚒️ | Generates complete, production-ready codebases with tests, docs, and CI/CD |
| **5. Publish** | 🚀 | Creates repos under GrooveXlabs with proper branding and documentation |

---

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/GrooveXlabs/toolsmith-agent.git
cd toolsmith-agent

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GitHub token and OpenAI API key

# Run a full cycle
python cli.py full-cycle --category web-scraping

# Or run individual phases
python cli.py discover --category ai-tools --limit 20
python cli.py analyze --repo-owner Scrapling --repo-name Scrapling
python cli.py ideate --from-analysis analysis_Scrapling.json
python cli.py build --concept concept_Scrapling.json --lang python
python cli.py publish --project-dir ./generated/groove-scraper
```

---

## 🏗️ Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Discover   │───→│   Analyze   │───→│   Ideate    │───→│    Build    │───→│   Publish   │
│  🔍 Trend   │    │  🧠 Deep    │    │  💡 Concept │    │  ⚒️ Code    │    │  🚀 GitHub  │
│   Sources   │    │    Dive     │    │   Generate  │    │  Generate   │    │    Push     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

```
toolsmith/
├── discoverer.py      # Trend discovery via GitHub API + web scraping
├── analyzer.py        # Architecture & gap analysis with LLM
├── ideator.py         # Improved concept generation
├── generator.py       # Full project code generation
├── publisher.py       # GitHub repo creation & code push
├── config.py          # Configuration management
└── models.py          # Data models & schemas
```

---

## 📂 Categories Supported

| Category | Description | Example Targets |
|----------|-------------|-----------------|
| `web-scraping` | Crawlers, scrapers, browser automation | Scrapling, Playwright, Selenium |
| `ai-ml` | LLM tools, vector DBs, model serving | LangChain, Ollama, Chroma |
| `devops` | CI/CD, monitoring, infrastructure | ArgoCD, Prometheus, Terraform |
| `security` | Scanners, analyzers, SIEM tools | Nuclei, Wazuh, Zeek |
| `data` | ETL, databases, data pipelines | dbt, Airflow, DuckDB |
| `api` | API gateways, testing, documentation | Kong, Postman, Scalar |
| `frontend` | UI libraries, build tools, frameworks | Vite, Tailwind, Shadcn |

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | ✅ Yes | GitHub personal access token with repo scope |
| `OPENAI_API_KEY` | ✅ Yes | OpenAI API key for analysis & ideation |
| `GROOVEXLABS_ORG` | ❌ No | Target org (default: `GrooveXlabs`) |
| `DEFAULT_LANG` | ❌ No | Default language: `python`, `typescript`, `rust`, `go` |

---

## 🛡️ Security & Quality Gates

Every project built by ToolSmith passes through automated gates:

```
┌─────────────────────────────────────────────────────────────┐
│  Gate 1  │  Security Audit  →  No secrets, safe defaults    │
│  Gate 2  │  Code Review     →  Style, patterns, tests       │
│  Gate 3  │  Design Review   →  UX, architecture, docs       │
│  Gate 4  │  QA Pipeline     →  Tests pass, coverage ≥ 80%   │
│  Gate 5  │  CEO Review      →  Strategic fit, branding      │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗺️ Related GrooveXlabs Projects

| Repository | Description |
|---|---|
| [gstack-kimi](https://github.com/GrooveXlabs/gstack-kimi) | Kimi CLI Skills & Automation |
| [grooveguard](https://github.com/GrooveXlabs/grooveguard) | MCP Server Security Scanner |
| [groovefetch](https://github.com/GrooveXlabs/groovefetch) | AI-Native Adaptive Web Scraper |

---

## 🤝 Contributing

ToolSmith is built to evolve. Ideas for contribution:
- Add new discovery sources (Reddit, Lobsters, etc.)
- Support additional languages (Rust, Go, TypeScript)
- Improve prompt engineering for better code generation
- Add more quality gates and automated checks

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">

<br>

<sub>🔒 Built with security in mind. Open source by conviction.</sub>
<br>
<sub>Maintained by <strong>GrooveXlabs</strong></sub>

</div>
