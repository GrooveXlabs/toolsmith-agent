# 🔨 ToolSmith Agent

Autonomous agent that discovers trending developer tools, analyzes their architecture, identifies gaps, and builds improved alternatives — automatically pushed to GrooveXlabs.

## What It Does

1. **🔍 Discovers** — Scans GitHub trending, Product Hunt, and Hacker News for hot developer tools
2. **🧠 Analyzes** — Deep-dives into architecture, tech stack, features, and user pain points
3. **💡 Ideates** — Generates unique improvements, missing features, and better UX approaches
4. **⚒️ Builds** — Generates complete, production-ready codebases with tests, docs, and CI/CD
5. **🚀 Publishes** — Creates repos under GrooveXlabs with proper branding and documentation

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set your environment variables
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

## Architecture

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

## Categories Supported

- `web-scraping` — Crawlers, scrapers, browser automation
- `ai-ml` — LLM tools, vector DBs, model serving
- `devops` — CI/CD, monitoring, infrastructure
- `security` — Scanners, analyzers, SIEM tools
- `data` — ETL, databases, data pipelines
- `api` — API gateways, testing, documentation
- `frontend` — UI libraries, build tools, frameworks

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Yes | GitHub personal access token |
| `OPENAI_API_KEY` | Yes | OpenAI API key for analysis/ideation |
| `GROOVEXLABS_ORG` | No | Target org (default: GrooveXlabs) |
| `DEFAULT_LANG` | No | Default language: python, typescript, rust, go |

## License

MIT — GrooveXlabs
