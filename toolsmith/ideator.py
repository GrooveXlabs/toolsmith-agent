"""Concept ideator — generates improved tool concepts from analysis."""

import json
from typing import List
from openai import OpenAI

from .models import Concept
from .config import ToolSmithConfig


class ConceptIdeator:
    """Generates improved tool concepts based on gap analysis."""
    
    def __init__(self, config: ToolSmithConfig):
        self.config = config
        self.client = OpenAI(api_key=config.openai_api_key)
    
    def ideate(self, analysis_path: str) -> Concept:
        """
        Generate an improved concept from an analysis file.
        
        Args:
            analysis_path: Path to the analysis JSON file
        """
        # Load analysis
        import os
        with open(analysis_path) as f:
            analysis_data = json.load(f)
        
        original_repo = analysis_data.get("original_repo", "unknown/unknown")
        gaps = analysis_data.get("gaps", [])
        features = analysis_data.get("features", [])
        tech_stack = analysis_data.get("tech_stack", [])
        
        # Build ideation prompt
        prompt = self._build_ideation_prompt(analysis_data)
        
        # Call LLM
        response = self.client.chat.completions.create(
            model=self.config.openai_model,
            messages=[
                {"role": "system", "content": 
                 "You are a visionary product manager and technical architect. "
                 "You excel at taking existing tools and reimagining them with "
                 "bold improvements, better developer experience, and modern tech. "
                 "Generate compelling, differentiated concepts. Output valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.85,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        
        return Concept(
            original_repo=original_repo,
            new_name=result.get("new_name", f"Groove{original_repo.split('/')[-1]}"),
            tagline=result.get("tagline", "A better developer tool"),
            description=result.get("description", ""),
            differentiators=result.get("differentiators", []),
            tech_stack=result.get("tech_stack", tech_stack),
            core_features=result.get("core_features", []),
            architecture_overview=result.get("architecture_overview", ""),
            target_users=result.get("target_users", "developers"),
            license=result.get("license", "MIT"),
            branding_tone=result.get("branding_tone", "professional")
        )
    
    def _build_ideation_prompt(self, analysis: dict) -> str:
        """Build the ideation prompt from analysis data."""
        gaps_text = "\n".join([
            f"- [{g.get('severity','medium').upper()}] {g.get('area')}: {g.get('description')}"
            for g in analysis.get("gaps", [])
        ])
        
        features_text = "\n".join([
            f"- {f.get('name')}: {f.get('description')} (quality: {f.get('implementation_quality')})"
            for f in analysis.get("features", [])[:10]
        ])
        
        return f"""Based on this analysis of "{analysis.get('name')}", create a concept for a superior alternative.

Original Tool Summary:
{analysis.get('description', '')}

Tech Stack: {', '.join(analysis.get('tech_stack', []))}
Architecture: {analysis.get('architecture_pattern', 'unknown')}

Existing Features:
{features_text}

Identified Gaps (our opportunities):
{gaps_text}

Generate a concept for "GrooveXlabs-style" improvement. We build:
- Developer-first tools with exceptional UX
- Secure-by-default implementations
- Modern async architecture where applicable
- Clean APIs with great documentation
- Batteries included but swappable

Respond with valid JSON:
{{
  "new_name": "A catchy, brandable name (prefixed with Groove if fitting)",
  "tagline": "One sentence that hooks developers",
  "description": "2-3 paragraphs describing the tool, its philosophy, and why it exists",
  "differentiators": [
    "Specific improvement 1 (not generic)",
    "Specific improvement 2"
  ],
  "tech_stack": ["primary language", "key libraries/frameworks"],
  "core_features": [
    "Feature 1: what it does and why it matters",
    "Feature 2: what it does and why it matters"
  ],
  "architecture_overview": "High-level architecture description",
  "target_users": "Primary and secondary users",
  "license": "MIT",
  "branding_tone": "professional|playful|technical|minimal"
}}

Make the differentiators genuinely compelling — things that would make a developer switch."""
