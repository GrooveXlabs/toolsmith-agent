#!/usr/bin/env python3
"""
ToolSmith Agent CLI
Main entry point for the autonomous tool-building agent.
"""

import os
import re
import sys
import json
import subprocess
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from toolsmith.config import load_config
from toolsmith.discoverer import TrendDiscoverer
from toolsmith.analyzer import RepoAnalyzer
from toolsmith.ideator import ConceptIdeator
from toolsmith.generator import ProjectGenerator
from toolsmith.publisher import GitHubPublisher

console = Console()


def _load_skill_checklist(skill_name):
    """Load checklist items from a gstack SKILL.md file."""
    skill_path = Path.home() / ".kimi" / "skills" / skill_name / "SKILL.md"
    if not skill_path.exists():
        return []
    text = skill_path.read_text(encoding="utf-8")
    # Extract checklist lines like "- [ ] item"
    items = re.findall(r"- \[ \]\s*(.+)", text)
    return items


def _scan_for_patterns(project_dir, patterns, file_globs=None):
    """Scan project files for regex patterns. Returns list of matches."""
    if file_globs is None:
        file_globs = ["*.py", "*.js", "*.ts", "*.json", "*.md", "*.toml", "*.yaml", "*.yml"]
    matches = []
    project_path = Path(project_dir)
    skip_dirs = {".venv", "venv", "node_modules", "__pycache__", ".git", "dist", "build", ".pytest_cache", ".mypy_cache"}
    for glob in file_globs:
        for filepath in project_path.rglob(glob):
            if not filepath.is_file():
                continue
            # Skip dependency / cache directories
            if any(part in skip_dirs for part in filepath.parts):
                continue
            try:
                content = filepath.read_text(encoding="utf-8", errors="ignore")
                for pattern in patterns:
                    for m in re.finditer(pattern, content):
                        line_num = content[:m.start()].count("\n") + 1
                        matches.append((str(filepath.relative_to(project_path)), line_num, m.group(0).strip()))
            except Exception:
                continue
    return matches


def _run_shell(cmd, cwd=None):
    """Run a shell command and return (rc, stdout, stderr)."""
    try:
        result = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=True, text=True, timeout=60
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return -1, "", str(e)


def _run_gstack_gate(project_dir, skill_name, title, emoji, checks_fn):
    """Run a single gstack review gate."""
    console.rule(f"[{emoji}] gstack — {title}")
    checklist = _load_skill_checklist(skill_name)
    if checklist:
        console.print(f"[dim]Loaded {len(checklist)} checklist items from {skill_name}[/dim]")

    findings = checks_fn(project_dir, checklist)

    passed = all(f.get("pass", True) for f in findings)
    status = "[green]PASS[/green]" if passed else "[red]FAIL[/red]"
    console.print(f"\n[{emoji}] Gate {status}: {title}")

    if not passed:
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Severity")
        table.add_column("Finding")
        for f in findings:
            if not f.get("pass", True):
                table.add_row(f.get("severity", "HIGH"), f.get("message", ""))
        console.print(table)

    return passed, findings


def _security_checks(project_dir, checklist):
    """Automated security audit checks."""
    findings = []
    # Secret-like patterns
    secret_patterns = [
        r"(?i)(api[_-]?key|password|secret|token)\s*=\s*[\"'][^\"']{8,}[\"']",
        r"(?i)sk-[a-zA-Z0-9]{20,}",
        r"ghp_[a-zA-Z0-9]{36}",
    ]
    secret_matches = _scan_for_patterns(project_dir, secret_patterns)
    for fp, ln, match in secret_matches[:5]:
        findings.append({"pass": False, "severity": "CRITICAL", "message": f"Possible secret in {fp}:{ln} — {match[:40]}..."})

    # Dangerous functions
    danger_matches = _scan_for_patterns(project_dir, [r"(?<!# )\beval\b", r"\bos\.system\b", r"\bsubprocess\.call\b.*shell\s*=\s*True"])
    for fp, ln, match in danger_matches[:5]:
        findings.append({"pass": False, "severity": "HIGH", "message": f"Dangerous call in {fp}:{ln} — {match}"})

    # Check for http (warn) — skip test files
    http_matches = _scan_for_patterns(project_dir, [r"http://(?!localhost|127\.0\.0\.1)"])
    for fp, ln, match in http_matches[:3]:
        if "test_" in fp or "_test.py" in fp:
            continue  # Tests use http:// for validation
        findings.append({"pass": False, "severity": "MEDIUM", "message": f"Insecure HTTP in {fp}:{ln} — {match}"})

    if not findings:
        findings.append({"pass": True, "severity": "INFO", "message": "No obvious security issues detected."})
    return findings


def _code_review_checks(project_dir, checklist):
    """Automated code review checks."""
    findings = []
    # AI slop detection
    slop_patterns = [
        (r"#\s*TODO:\s*implement", "Placeholder comment (TODO: implement)"),
        (r"except\s*:\s*\n?\s*pass", "Fake error handling (except: pass)"),
        (r"(?i)#\s*FIXME\s*", "FIXME comment remains"),
    ]
    for pattern, desc in slop_patterns:
        matches = _scan_for_patterns(project_dir, [pattern])
        for fp, ln, _ in matches[:5]:
            findings.append({"pass": False, "severity": "MEDIUM", "message": f"{desc} in {fp}:{ln}"})

    # Missing type hints in Python files (skip deps, tests, generated)
    skip_dirs = {".venv", "venv", "node_modules", "__pycache__", ".git", "dist", "build", ".pytest_cache", "site-packages"}
    py_files = [f for f in Path(project_dir).rglob("*.py") if not any(part in skip_dirs for part in f.parts)]
    for py_file in py_files[:20]:
        if py_file.name.startswith("test_") or py_file.name.endswith("_test.py"):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
            for i, line in enumerate(lines, 1):
                if line.strip().startswith("def ") and "->" not in line and "__init__" not in line:
                    # Check next 10 lines for multi-line return type annotation
                    window = lines[i-1:i+10]
                    if any("->" in wl for wl in window):
                        continue
                    findings.append({"pass": False, "severity": "LOW", "message": f"Missing return type hint: {py_file.name}:{i}"})
                    if len([f for f in findings if f.get("severity") == "LOW"]) >= 5:
                        break
        except Exception:
            pass

    if not findings:
        findings.append({"pass": True, "severity": "INFO", "message": "Code review clean."})
    return findings


def _qa_checks(project_dir, checklist):
    """Automated QA checks."""
    findings = []
    # Try to run pytest
    rc, out, err = _run_shell("python -m pytest --tb=short -q", cwd=project_dir)
    if rc == 0:
        findings.append({"pass": True, "severity": "INFO", "message": "pytest passed."})
    elif rc == 5:
        findings.append({"pass": False, "severity": "MEDIUM", "message": "No tests found (pytest exit 5)."})
    else:
        findings.append({"pass": False, "severity": "HIGH", "message": f"Tests failed (exit {rc})."})

    # Check for test files
    test_files = list(Path(project_dir).rglob("test_*.py")) + list(Path(project_dir).rglob("*_test.py"))
    if not test_files:
        findings.append({"pass": False, "severity": "MEDIUM", "message": "No test files discovered."})

    return findings


def _design_review_checks(project_dir, checklist):
    """Automated design/UX review checks."""
    findings = []
    readme_path = Path(project_dir) / "README.md"
    if not readme_path.exists():
        findings.append({"pass": False, "severity": "HIGH", "message": "README.md missing."})
    else:
        readme = readme_path.read_text(encoding="utf-8", errors="ignore")
        if "```" not in readme:
            findings.append({"pass": False, "severity": "MEDIUM", "message": "README has no code examples."})
        if len(readme) > 5000 and "quickstart" not in readme.lower() and "example" not in readme.lower():
            findings.append({"pass": False, "severity": "MEDIUM", "message": "README is long but lacks quickstart/example."})

    # Check for .env.example (good practice)
    if not (Path(project_dir) / ".env.example").exists():
        findings.append({"pass": False, "severity": "LOW", "message": "No .env.example file."})

    if not findings or all(f.get("pass", True) for f in findings):
        findings.insert(0, {"pass": True, "severity": "INFO", "message": "Design review checks passed."})
    return findings


def _ship_checks(project_dir, checklist, gate_results):
    """Ship gate — validates all prior gates and release readiness."""
    findings = []
    failed_gates = [name for name, (passed, _) in gate_results.items() if not passed]
    if failed_gates:
        findings.append({"pass": False, "severity": "CRITICAL", "message": f"Prior gates failed: {', '.join(failed_gates)}"})

    # Version file check
    version_files = ["pyproject.toml", "package.json", "Cargo.toml", "setup.py"]
    has_version = any((Path(project_dir) / vf).exists() for vf in version_files)
    if not has_version:
        findings.append({"pass": False, "severity": "MEDIUM", "message": "No version file (pyproject.toml/package.json) found."})

    if not findings or all(f.get("pass", True) for f in findings):
        findings.insert(0, {"pass": True, "severity": "INFO", "message": "Ship gate ready."})
    return findings


def run_gstack_review(project_dir, force=False):
    """Run the full gstack review pipeline on a generated project."""
    console.rule("[bold white on magenta] GSTACK REVIEW PIPELINE ")
    console.print("[dim]Reading skill definitions from ~/.kimi/skills/gstack-*[/dim]\n")

    gates = [
        ("gstack-security-audit", "Security Audit", "🔒", _security_checks),
        ("gstack-code-review", "Code Review", "🔍", _code_review_checks),
        ("gstack-qa", "QA Pipeline", "🧪", _qa_checks),
        ("gstack-design-review", "Design Review", "🎨", _design_review_checks),
    ]

    gate_results = {}
    for skill_name, title, emoji, checks_fn in gates:
        passed, findings = _run_gstack_gate(project_dir, skill_name, title, emoji, checks_fn)
        gate_results[skill_name] = (passed, findings)
        console.print("")

    # Ship gate depends on all prior gates
    ship_passed, ship_findings = _run_gstack_gate(
        project_dir, "gstack-ship", "Release / Ship", "🚀",
        lambda d, c: _ship_checks(d, c, gate_results)
    )
    gate_results["gstack-ship"] = (ship_passed, ship_findings)

    # Summary
    console.rule("[bold]GSTACK REVIEW SUMMARY")
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Gate")
    table.add_column("Status")
    for skill_name, title, _, _ in gates:
        passed, _ = gate_results[skill_name]
        table.add_row(title, "[green]PASS[/green]" if passed else "[red]FAIL[/red]")
    table.add_row("Release / Ship", "[green]PASS[/green]" if ship_passed else "[red]FAIL[/red]")
    console.print(table)

    all_passed = all(passed for passed, _ in gate_results.values())
    if all_passed:
        console.print(Panel.fit(
            "[bold green]🚀 All gstack gates passed! Ready to ship.[/bold green]",
            border_style="green"
        ))
        return True
    elif force:
        console.print(Panel.fit(
            "[bold yellow]⚠️ Some gates failed, but --force is set. Proceeding.[/bold yellow]",
            border_style="yellow"
        ))
        return True
    else:
        console.print(Panel.fit(
            "[bold red]⛔ gstack review blocked shipping.[/bold red]\n"
            "Fix the issues above or use --force to override.",
            border_style="red"
        ))
        return False


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
@click.option('--gstack-review', is_flag=True, help='Run gstack review gates after build')
@click.option('--force', is_flag=True, help='Force ship even if gstack gates fail')
@click.pass_context
def build(ctx, concept, lang, output_dir, gstack_review, force):
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

    if gstack_review:
        ok = run_gstack_review(project_dir, force=force)
        if not ok:
            sys.exit(1)


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
@click.option('--gstack-review', is_flag=True, help='Run gstack review gates after build')
@click.option('--force', is_flag=True, help='Force ship even if gstack gates fail')
@click.pass_context
def full_cycle(ctx, category, limit, lang, auto_publish, gstack_review, force):
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
    
    # Step 4.5: gstack Review
    if gstack_review:
        ok = run_gstack_review(project_dir, force=force)
        if not ok:
            console.print("[red]✗[/red] gstack review blocked publish. Exiting.")
            return
    
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
