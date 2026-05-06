"""Trend discovery module — finds hot developer tools across GitHub."""

import requests
import random
from typing import List, Optional
from datetime import datetime, timedelta

from .models import DiscoveredRepo
from .config import ToolSmithConfig


# Category to GitHub search query mappings
CATEGORY_QUERIES = {
    "web-scraping": [
        "web scraper language:python stars:>100",
        "crawler framework stars:>200",
        "browser automation tools stars:>150",
        "scraping engine language:python stars:>80",
    ],
    "ai-ml": [
        "llm framework language:python stars:>500",
        "vector database stars:>300",
        "machine learning tools stars:>400",
        "ai agent framework stars:>200",
    ],
    "devops": [
        "ci cd tool stars:>300",
        "infrastructure as code stars:>400",
        "monitoring dashboard stars:>200",
        "deployment automation stars:>150",
    ],
    "security": [
        "security scanner stars:>200",
        "penetration testing tool stars:>150",
        "vulnerability scanner stars:>100",
        "siem tool stars:>80",
    ],
    "data": [
        "etl pipeline framework stars:>200",
        "data pipeline tool stars:>300",
        "database proxy stars:>150",
        "data validation library stars:>100",
    ],
    "api": [
        "api gateway stars:>400",
        "api testing tool stars:>300",
        "rest client library stars:>200",
        "graphql framework stars:>250",
    ],
    "frontend": [
        "ui component library stars:>500",
        "build tool vite stars:>400",
        "css framework stars:>600",
        "react state management stars:>300",
    ],
}


class TrendDiscoverer:
    """Discovers trending repositories by category."""
    
    def __init__(self, config: ToolSmithConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(config.headers)
        if config.http_proxy:
            self.session.proxies = {"https": config.http_proxy}
    
    def discover(
        self,
        category: str,
        limit: int = 20,
        min_stars: int = 50,
        language: Optional[str] = None,
        created_after: Optional[str] = None
    ) -> List[DiscoveredRepo]:
        """
        Discover trending repositories in a category.
        
        Args:
            category: One of the predefined categories
            limit: Maximum repos to return
            min_stars: Minimum star count filter
            language: Optional language filter
            created_after: ISO date string for repo creation filter
        """
        queries = CATEGORY_QUERIES.get(category, [f"{category} stars:>100"])
        all_repos = []
        seen = set()
        
        # Use multiple queries to get diverse results
        for query_template in queries:
            query = query_template
            if language and "language:" not in query:
                query += f" language:{language}"
            
            url = "https://api.github.com/search/repositories"
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": min(limit, 100)
            }
            
            try:
                resp = self.session.get(url, params=params, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                
                for item in data.get("items", []):
                    repo_id = item["full_name"]
                    if repo_id in seen:
                        continue
                    seen.add(repo_id)
                    
                    # Skip forks and very old repos unless they're legendary
                    if item.get("fork"):
                        continue
                    
                    created = item.get("created_at", "")
                    if created_after and created < created_after:
                        continue
                    
                    repo = DiscoveredRepo(
                        name=item["name"],
                        full_name=item["full_name"],
                        owner=item["owner"]["login"],
                        description=item.get("description") or "",
                        stars=item["stargazers_count"],
                        forks=item["forks_count"],
                        language=item.get("language"),
                        topics=item.get("topics", []),
                        url=item["html_url"],
                        created_at=created,
                        updated_at=item.get("updated_at"),
                        category=category
                    )
                    
                    if repo.stars >= min_stars:
                        all_repos.append(repo)
                        
            except Exception as e:
                print(f"Warning: query failed for '{query}': {e}")
                continue
        
        # Sort by stars descending, then by recency
        all_repos.sort(key=lambda r: (r.stars, r.updated_at or ""), reverse=True)
        
        # Return top N unique repos
        return all_repos[:limit]
    
    def get_repo_readme(self, owner: str, repo: str) -> str:
        """Fetch the README content of a repository."""
        url = f"https://api.github.com/repos/{owner}/{repo}/readme"
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            import base64
            content = data.get("content", "")
            return base64.b64decode(content).decode("utf-8", errors="ignore")
        except Exception as e:
            return f"# Error fetching README: {e}"
    
    def get_repo_files(self, owner: str, repo: str, path: str = "") -> List[dict]:
        """List files in a repository directory."""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return []
    
    def get_file_content(self, owner: str, repo: str, path: str) -> str:
        """Fetch content of a specific file."""
        url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            import base64
            content = data.get("content", "")
            return base64.b64decode(content).decode("utf-8", errors="ignore")
        except Exception:
            return ""
