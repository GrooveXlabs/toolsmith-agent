"""Repository analyzer — uses LLM to deeply analyze trending tools."""

import json
import os
from typing import List, Dict
from openai import OpenAI

from .models import RepoAnalysis, Feature, Gap
from .config import ToolSmithConfig
from .discoverer import TrendDiscoverer


class RepoAnalyzer:
    """Analyzes a repository's architecture, features, and gaps using LLM."""
    
    def __init__(self, config: ToolSmithConfig):
        self.config = config
        self.client = OpenAI(api_key=config.openai_api_key)
        self.discoverer = TrendDiscoverer(config)
    
    def analyze(self, repo_full_name: str) -> RepoAnalysis:
        """
        Deep analysis of a repository.
        
        Args:
            repo_full_name: Format 'owner/repo'
        """
        owner, repo = repo_full_name.split("/")
        
        # Gather raw data
        readme = self.discoverer.get_repo_readme(owner, repo)
        files = self.discoverer.get_repo_files(owner, repo)
        file_list = [f["name"] for f in files if isinstance(f, dict)]
        
        # Try to get key source files for deeper analysis
        source_snippets = []
        key_files = [f for f in files if isinstance(f, dict) and 
                     f.get("name", "").endswith((".py", ".js", ".ts", ".rs", ".go", ".md"))]
        for f in key_files[:5]:
            content = self.discoverer.get_file_content(owner, repo, f["path"])
            source_snippets.append(f"=== {f['name']} ===\n{content[:2000]}")
        
        # Build analysis prompt
        prompt = self._build_analysis_prompt(repo, readme, file_list, source_snippets)
        
        # Call LLM
        response = self.client.chat.completions.create(
            model=self.config.openai_model,
            messages=[
                {"role": "system", "content": 
                 "You are a senior software architect and product analyst. "
                 "Analyze developer tools with brutal honesty. Identify real gaps, "
                 "not fluffy marketing speak. Focus on architecture flaws, missing features, "
                 "and opportunities for 10x improvements. Output valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return RepoAnalysis(
            name=repo,
            original_repo=repo_full_name,
            description=result.get("description", ""),
            tech_stack=result.get("tech_stack", []),
            architecture_pattern=result.get("architecture_pattern", "unknown"),
            features=result.get("features", []),
            gaps=result.get("gaps", []),
            target_audience=result.get("target_audience", "developers"),
            monetization_potential=result.get("monetization_potential", "unknown"),
            complexity_score=result.get("complexity_score", 5),
            maintenance_burden=result.get("maintenance_burden", "medium")
        )
    
    def _build_analysis_prompt(
        self,
        repo_name: str,
        readme: str,
        file_list: List[str],
        source_snippets: List[str]
    ) -> str:
        """Build the analysis prompt."""
        readme_truncated = readme[:4000] if readme else "No README available"
        snippets_text = "\n\n".join(source_snippets[:3])
        
        return f"""Analyze the developer tool "{repo_name}" and produce a structured assessment.

README (truncated):
{readme_truncated}

Top-level files:
{', '.join(file_list[:30])}

Source code snippets:
{snippets_text}

Respond with valid JSON matching this structure:
{{
  "description": "One-paragraph summary of what this tool does",
  "tech_stack": ["language", "key framework 1", "key framework 2"],
  "architecture_pattern": "e.g. plugin-based, monolithic, microservices, client-server",
  "features": [
    {{
      "name": "Feature name",
      "description": "What it does",
      "importance": "critical|high|medium|low",
      "implementation_quality": "excellent|good|fair|poor"
    }}
  ],
  "gaps": [
    {{
      "area": "Category like testing, observability, UX, performance",
      "description": "Specific gap or pain point",
      "severity": "critical|high|medium|low",
      "opportunity": "What a competitor could do better"
    }}
  ],
  "target_audience": "Who primarily uses this",
  "monetization_potential": "high|medium|low|unknown",
  "complexity_score": 1-10,
  "maintenance_burden": "high|medium|low"
}}

Be critical and specific. Identify at least 5 real gaps that could be exploited by a better alternative."""
