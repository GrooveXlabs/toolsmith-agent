"""Data models for ToolSmith Agent."""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime
import json


class DiscoveredRepo(BaseModel):
    """A repository discovered during trend scanning."""
    name: str
    full_name: str
    owner: str
    description: str
    stars: int
    forks: int
    language: Optional[str]
    topics: List[str] = []
    url: str
    created_at: Optional[str]
    updated_at: Optional[str]
    category: str
    
    def to_dict(self) -> Dict:
        return self.model_dump()


class Feature(BaseModel):
    """A feature identified in a tool."""
    name: str
    description: str
    importance: str = "medium"  # low, medium, high, critical
    implementation_quality: str = "unknown"  # poor, fair, good, excellent


class Gap(BaseModel):
    """A gap or pain point identified in a tool."""
    area: str
    description: str
    severity: str = "medium"  # low, medium, high, critical
    opportunity: str = ""


class RepoAnalysis(BaseModel):
    """Complete analysis of a repository."""
    name: str
    original_repo: str
    description: str
    tech_stack: List[str]
    architecture_pattern: str
    features: List[Dict]
    gaps: List[Dict]
    target_audience: str
    monetization_potential: str = "unknown"
    complexity_score: int = Field(ge=1, le=10)
    maintenance_burden: str = "medium"
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump(self.model_dump(), f, indent=2)
    
    @classmethod
    def load(cls, path: str):
        with open(path) as f:
            return cls(**json.load(f))


class Concept(BaseModel):
    """Generated concept for an improved tool."""
    original_repo: str
    new_name: str
    tagline: str
    description: str
    differentiators: List[str]
    tech_stack: List[str]
    core_features: List[str]
    architecture_overview: str
    target_users: str
    license: str = "MIT"
    branding_tone: str = "professional"
    generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    def save(self, path: str):
        with open(path, 'w') as f:
            json.dump(self.model_dump(), f, indent=2)
    
    @classmethod
    def load(cls, path: str):
        with open(path) as f:
            return cls(**json.load(f))


class ProjectFile(BaseModel):
    """A file in the generated project."""
    path: str
    content: str
    description: str = ""
