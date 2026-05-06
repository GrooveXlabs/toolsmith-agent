#!/usr/bin/env python3
"""
ToolSmith Agent CLI
Main entry point for the autonomous tool-building agent.
"""

import os
import sys
import json
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from toolsmith.config import load_config
from toolsmith.discoverer import TrendDiscoverer
from toolsmith.analyzer import RepoAnalyzer
from toolsmith.ideator import ConceptIdeator
from toolsmith.generator import ProjectGenerator
from toolsmith.publisher import GitHubPublisher

console = Console()


@click.group()
@click.pass_context
def cli(ctx):
    """🔨 ToolSmith Agent — Autonomous tool builder for GrooveXlabs"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = load_config()
    console.print(Panel.fit(
        "[bold blue]🔨 ToolSmith Agent[/bold blue]\n"
        "[dim]Autonomous tool discovery & builder for GrooveXlabs[/dim]",
        border_style="blue"
    ))


@cli.command()
@click.option('--category', '-c', default='web-scraping',
              help='Tool category to discover')
@click.option('--limit', '-l', default=20, help='Max repos to fetch')
@click.option('--output', '-o', default='./discovered.json', help='Output file')
@click.pass_context
def discover(ctx, category, limit, output):
    """🔍 Discover trending tools in a category"""
    config = ctx.obj['config']
    discoverer = TrendDiscoverer(config)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Discovering {category} tools...", total=None)
        repos = discoverer.discover(category=category, limit=limit)
        progress.update(task, completed=True)
    
    # Save results
    with open(output, 'w') as f:
        json.dump([r.to_dict() for r in repos], f, indent=2)
    
    console.print(f"[green]✓[/green] Discovered {len(repos)} repositories")
    for repo in repos[:5]:
        console.print(f"  • [bold]{repo.name}[/bold] — ⭐ {repo.stars} — {repo.description[:60]}...")


@cli.command()
@click.option('--repo-owner', '-o', required=True, help='Repository owner')
@click.option('--repo-name', '-n', required=True, help='Repository name')
@click.option('--output', '-o', default=None, help='Output JSON file')
@click.pass_context
def analyze(ctx, repo_owner, repo_name, output):
    """🧠 Analyze a repository's architecture and gaps"""
    config = ctx.obj['config']
    analyzer = RepoAnalyzer(config)
    
    output = output or f"analysis_{repo_name}.json"
    
    with console.status(f"[bold blue]Analyzing {repo_owner}/{repo_name}..."):
        analysis = analyzer.analyze(f"{repo_owner}/{repo_name}")
        analysis.save(output)
    
    console.print(f"[green]✓[/green] Analysis saved to {output}")
    console.print(Panel.fit(
        f"[bold]{analysis.name}[/bold]\n"
        f"Tech Stack: {', '.join(analysis.tech_stack[:5])}\n"
        f"Architecture: {analysis.architecture_pattern}\n"
        f"Key Gaps: {len(analysis.gaps)} identified",
        title="Analysis Summary",
        border_style="green"
    ))


@cli.command()
@click.option('--from-analysis', '-a', required=True, help='Path to analysis JSON')
@click.option('--output', '-o', default=None, help='Output concept JSON')
@click.pass_context
def ideate(ctx, from_analysis, output):
    """💡 Generate improved concept from analysis"""
    config = ctx.obj['config']
    ideator = ConceptIdeator(config)
    
    output = output or from_analysis.replace('analysis_', 'concept_')
    
    with console.status("[bold yellow]Ideating improvements..."):
        concept = ideator.ideate(from_analysis)
        concept.save(output)
    
    console.print(f"[green]✓[/green] Concept saved to {output}")
    console.print(Panel.fit(
        f"[bold]{concept.new_name}[/bold] — {concept.tagline}\n\n"
        f"[bold]Key Differentiators:[/bold]\n" +
        "\n".join(f"  • {d}" for d in concept.differentiators[:3]) +
        f"\n\n[bold]Tech Stack:[/bold] {', '.join(concept.tech_stack)}",
        title="Generated Concept",
        border_style="yellow"
    ))


@cli.command()
@click.option('--concept', '-c', required=True, help='Path to concept JSON')
@click.option('--lang', '-l', default=None, help='Target language (python/typescript/rust/go)')
@click.option('--output-dir', '-o', default='./generated', help='Output directory')
@click.pass_context
def build(ctx, concept, lang, output_dir):
    """⚒️ Build a complete project from concept"""
    config = ctx.obj['config']
    lang = lang or config.default_lang
    generator = ProjectGenerator(config, language=lang)
    
    with console.status(f"[bold magenta]Building {lang} project..."):
        project_dir = generator.generate(concept, output_dir)
    
    console.print(f"[green]✓[/green] Project built at {project_dir}")
    
    # Show structure
    files = list(Path(project_dir).rglob('*'))
    files = [f for f in files if f.is_file()]
    console.print(f"[dim]Generated {len(files)} files[/dim]")


@cli.command()
@click.option('--project-dir', '-d', required=True, help='Project directory to publish')
@click.option('--repo-name', '-n', default=None, help='Target repo name (auto from concept if not set)')
@click.pass_context
def publish(ctx, project_dir, repo_name):
    """🚀 Publish project to GrooveXlabs GitHub"""
    config = ctx.obj['config']
    publisher = GitHubPublisher(config)
    
    with console.status("[bold cyan]Publishing to GitHub..."):
        repo_url = publisher.publish(project_dir, repo_name)
    
    console.print(f"[green]✓[/green] Published to {repo_url}")


@cli.command()
@click.option('--category', '-c', default='web-scraping', help='Category to explore')
@click.option('--limit', '-l', default=10, help='Repos to analyze')
@click.option('--lang', '-l2', default=None, help='Build language')
@click.option('--auto-publish', is_flag=True, help='Auto-publish to GitHub')
@click.pass_context
def full_cycle(ctx, category, limit, lang, auto_publish):
    """🔄 Run full discovery → analyze → ideate → build → publish cycle"""
    config = ctx.obj['config']
    lang = lang or config.default_lang
    
    discoverer = TrendDiscoverer(config)
    analyzer = RepoAnalyzer(config)
    ideator = ConceptIdeator(config)
    generator = ProjectGenerator(config, language=lang)
    publisher = GitHubPublisher(config)
    
    # Step 1: Discover
    console.rule("[bold blue]Step 1: Discovery")
    repos = discoverer.discover(category=category, limit=limit)
    if not repos:
        console.print("[red]✗[/red] No repos discovered. Exiting.")
        return
    
    top_repo = repos[0]
    console.print(f"[green]✓[/green] Top candidate: [bold]{top_repo.full_name}[/bold] (⭐ {top_repo.stars})")
    
    # Step 2: Analyze
    console.rule("[bold green]Step 2: Analysis")
    analysis = analyzer.analyze(top_repo.full_name)
    analysis_path = f"analysis_{top_repo.name}.json"
    analysis.save(analysis_path)
    console.print(f"[green]✓[/green] Identified {len(analysis.gaps)} gaps and {len(analysis.features)} features")
    
    # Step 3: Ideate
    console.rule("[bold yellow]Step 3: Ideation")
    concept = ideator.ideate(analysis_path)
    concept_path = f"concept_{top_repo.name}.json"
    concept.save(concept_path)
    console.print(f"[green]✓[/green] Generated concept: [bold]{concept.new_name}[/bold]")
    console.print(f"  [dim]{concept.tagline}[/dim]")
    
    # Step 4: Build
    console.rule("[bold magenta]Step 4: Build")
    project_dir = generator.generate(concept_path, f"./generated/{concept.new_name.lower()}")
    console.print(f"[green]✓[/green] Built at {project_dir}")
    
    # Step 5: Publish
    if auto_publish:
        console.rule("[bold cyan]Step 5: Publish")
        repo_url = publisher.publish(project_dir, concept.new_name.lower())
        console.print(f"[green]✓[/green] Published to {repo_url}")
    else:
        console.print(f"\n[dim]To publish, run:[/dim]")
        console.print(f"  [bold]python cli.py publish --project-dir {project_dir}[/bold]")
    
    console.rule("[bold]Complete[/bold]")
    console.print(Panel.fit(
        f"[bold green]🎉 ToolSmith cycle complete![/bold green]\n\n"
        f"Inspired by: {top_repo.full_name}\n"
        f"Generated: {concept.new_name}\n"
        f"Language: {lang}\n"
        f"Location: {project_dir}",
        border_style="green"
    ))


if __name__ == '__main__':
    cli()
