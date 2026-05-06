"""Configuration management for ToolSmith Agent."""

import os
from dataclasses import dataclass
from typing import Dict, Optional
from dotenv import load_dotenv

# Load .env file if present
load_dotenv()


@dataclass
class ToolSmithConfig:
    """Agent configuration."""
    github_token: str
    openai_api_key: str
    groovex_org: str = "GrooveXlabs"
    default_lang: str = "python"
    max_repos: int = 20
    analysis_depth: str = "deep"
    output_dir: str = "./generated"
    openai_model: str = "gpt-4o"
    http_proxy: Optional[str] = None
    
    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }


def load_config() -> ToolSmithConfig:
    """Load configuration from environment."""
    github_token = os.getenv("GITHUB_TOKEN")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable required")
    if not openai_key:
        raise ValueError("OPENAI_API_KEY environment variable required")
    
    return ToolSmithConfig(
        github_token=github_token,
        openai_api_key=openai_key,
        groovex_org=os.getenv("GROOVEXLABS_ORG", "GrooveXlabs"),
        default_lang=os.getenv("DEFAULT_LANG", "python"),
        max_repos=int(os.getenv("MAX_REPOS_PER_DISCOVERY", "20")),
        analysis_depth=os.getenv("ANALYSIS_DEPTH", "deep"),
        output_dir=os.getenv("OUTPUT_DIR", "./generated"),
        openai_model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        http_proxy=os.getenv("HTTP_PROXY")
    )
