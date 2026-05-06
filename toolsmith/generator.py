"""Project generator — builds complete, production-ready codebases."""

import json
import os
from pathlib import Path
from typing import List, Dict
from openai import OpenAI

from .models import Concept, ProjectFile
from .config import ToolSmithConfig


# Language-specific templates and conventions
LANG_CONFIGS = {
    "python": {
        "extension": ".py",
        "package_manager": "pip",
        "manifest": "pyproject.toml",
        "test_framework": "pytest",
        "async_keyword": "async",
        "typing_module": "typing",
    },
    "typescript": {
        "extension": ".ts",
        "package_manager": "npm",
        "manifest": "package.json",
        "test_framework": "jest",
        "async_keyword": "async",
        "typing_module": "",
    },
    "rust": {
        "extension": ".rs",
        "package_manager": "cargo",
        "manifest": "Cargo.toml",
        "test_framework": "cargo test",
        "async_keyword": "async",
        "typing_module": "",
    },
    "go": {
        "extension": ".go",
        "package_manager": "go mod",
        "manifest": "go.mod",
        "test_framework": "go test",
        "async_keyword": "go",
        "typing_module": "",
    },
}


class ProjectGenerator:
    """Generates complete project structures from concepts."""
    
    def __init__(self, config: ToolSmithConfig, language: str = "python"):
        self.config = config
        self.language = language.lower()
        self.client = OpenAI(api_key=config.openai_api_key)
        self.lang_config = LANG_CONFIGS.get(self.language, LANG_CONFIGS["python"])
    
    def generate(self, concept_path: str, output_dir: str) -> str:
        """
        Generate a complete project from a concept file.
        
        Args:
            concept_path: Path to concept JSON
            output_dir: Directory to write project files
            
        Returns:
            Path to generated project directory
        """
        concept = Concept.load(concept_path)
        project_dir = Path(output_dir) / concept.new_name.lower().replace(" ", "-")
        project_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate file manifest first
        manifest = self._generate_file_manifest(concept)
        
        # Generate each file
        for file_spec in manifest:
            file_path = project_dir / file_spec["path"]
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            content = self._generate_file_content(concept, file_spec)
            file_path.write_text(content, encoding="utf-8")
        
        # Generate additional meta files
        self._generate_meta_files(project_dir, concept)
        
        return str(project_dir)
    
    def _generate_file_manifest(self, concept: Concept) -> List[Dict]:
        """Generate a manifest of files to create."""
        prompt = f"""Given this tool concept, generate a minimal but complete file manifest.

Tool: {concept.new_name}
Description: {concept.description}
Language: {self.language}
Core Features: {', '.join(concept.core_features[:5])}
Tech Stack: {', '.join(concept.tech_stack)}

Generate a JSON array of files needed. Include:
- Main source files (core logic)
- CLI entry point
- Test files
- Configuration files
- Documentation

Each entry: {{"path": "relative/path", "description": "what this file does"}}

Keep it lean but production-ready. Maximum 15 files."""
        
        response = self.client.chat.completions.create(
            model=self.config.openai_model,
            messages=[
                {"role": "system", "content": "You are a senior software engineer. Generate pragmatic file structures."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("files", [])
    
    def _generate_file_content(self, concept: Concept, file_spec: Dict) -> str:
        """Generate content for a single file."""
        prompt = f"""Write the complete content for this file:

Project: {concept.new_name}
Tagline: {concept.tagline}
File: {file_spec['path']}
Purpose: {file_spec['description']}
Language: {self.language}

Architecture: {concept.architecture_overview}
Core Features:
{chr(10).join(f"- {f}" for f in concept.core_features)}

Guidelines:
- Write production-quality code
- Include docstrings/comments
- Follow security best practices (input validation, safe defaults)
- Make it async where appropriate
- Include error handling
- NO placeholder code — everything must be functional

Output ONLY the file content, no markdown code fences, no explanations."""
        
        response = self.client.chat.completions.create(
            model=self.config.openai_model,
            messages=[
                {"role": "system", "content": f"You are an expert {self.language} developer. Write complete, working code."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=4000
        )
        
        content = response.choices[0].message.content.strip()
        # Strip code fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            content = "\n".join(lines)
        
        return content
    
    def _generate_meta_files(self, project_dir: Path, concept: Concept):
        """Generate README, LICENSE, and CI/CD files."""
        # README.md
        readme = f"""# {concept.new_name}

> {concept.tagline}

{concept.description}

## Features

{chr(10).join(f"- **{f.split(':')[0]}** — {f.split(':', 1)[1].strip() if ':' in f else ''}" for f in concept.core_features)}

## Installation

```bash
# Clone the repo
git clone https://github.com/{self.config.groovex_org}/{concept.new_name.lower().replace(' ', '-')}.git
cd {concept.new_name.lower().replace(' ', '-')}

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

```python
# Example usage will go here
```

## Architecture

{concept.architecture_overview}

## Why {concept.new_name}?

{chr(10).join(f'- {d}' for d in concept.differentiators)}

## License

{concept.license}

Built with ❤️ by [GrooveXlabs](https://github.com/{self.config.groovex_org})
"""
        (project_dir / "README.md").write_text(readme, encoding="utf-8")
        
        # LICENSE
        license_text = f"""MIT License

Copyright (c) {os.path.basename(str(project_dir))} GrooveXlabs

Permission is hereby granted, free of charge, to any person obtaining a copy...
"""
        (project_dir / "LICENSE").write_text(license_text, encoding="utf-8")
        
        # GitHub Actions CI (Python example)
        workflows_dir = project_dir / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        ci = f"""name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
    
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio
      - name: Run tests
        run: pytest tests/ -v
      - name: Lint
        run: |
          pip install ruff
          ruff check .
"""
        (workflows_dir / "ci.yml").write_text(ci, encoding="utf-8")
        
        # .gitignore
        gitignore = """__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
venv/
.env
.venv
*.log
.coverage
.pytest_cache/
.mypy_cache/
.idea/
.vscode/
*.swp
*.swo
*~
"""
        (project_dir / ".gitignore").write_text(gitignore, encoding="utf-8")
