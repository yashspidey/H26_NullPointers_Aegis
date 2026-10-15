"""CLI entry point for RepoRescue-AI."""

import json
import asyncio
from pathlib import Path
from datetime import datetime
import click

from .inspection import inspect_repository
from .analysis import analyze_repository, MaintenanceFinding

# Optional Cognee integration
try:
    from .cognee_memory import store_capsule_in_cognee, query_repo_memory
    COGNEE_AVAILABLE = True
except ImportError:
    COGNEE_AVAILABLE = False


@click.group()
def cli():
    """RepoRescue-AI: AI-powered repository maintenance agent."""
    pass


@cli.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def inspect(path: Path, as_json: bool):
    """Inspect a repository (no AI analysis)."""
    result = inspect_repository(path)
    
    if as_json:
        click.echo(json.dumps(result, indent=2, default=str))
    else:
        _print_inspection(result)


@cli.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path))
@click.option("--output", "-o", type=click.Path(path_type=Path), help="Output capsule to file")
@click.option("--no-ai", is_flag=True, help="Skip AI analysis (static findings only)")
@click.option("--cognee-store", is_flag=True, help="Store analysis in Cognee knowledge graph")
def analyze(path: Path, output: Path | None, no_ai: bool, cognee_store: bool):
    """Analyze a repository and generate Dependency Exit Capsule."""
    # Run full analysis
    result = analyze_repository(str(path), ai_analysis=None if no_ai else {})
    
    if "error" in result:
        click.echo(f"Error: {result['error']}", err=True)
        return
    
    inspection = result["inspection"]
    findings = [MaintenanceFinding(**f) for f in result["findings"]]
    
    # Generate capsule
    capsule = generate_capsule(inspection, findings)
    
    # Output
    if output:
        output.write_text(capsule, encoding="utf-8")
        click.echo(f"Capsule written to: {output}")
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"Dependency_Exit_Capsule_{timestamp}.md"
        Path(default_name).write_text(capsule, encoding="utf-8")
        click.echo(f"Capsule written to: {default_name}")
    
    # Print summary to console
    _print_findings(findings)

    # Optionally store in Cognee
    if cognee_store and COGNEE_AVAILABLE:
        click.echo("\nStoring analysis in Cognee knowledge graph...")
        doc_id = asyncio.run(store_capsule_in_cognee(
            repo_path=str(path),
            capsule_path=output or default_name,
            inspection=inspection,
            findings=[f.to_dict() for f in findings],
        ))
        click.echo(f"Stored in Cognee with doc ID: {doc_id}")
    elif cognee_store and not COGNEE_AVAILABLE:
        click.echo("\nCognee not available. Install with: pip install cognee", err=True)


def _print_inspection(result: dict):
    """Pretty-print inspection results."""
    click.echo(f"\nRepository: {result['path']}")
    click.echo(f"Type: {result['repo_type']}")
    if result.get("commit"):
        click.echo(f"Commit: {result['commit'][:8]}")
    if result.get("branch"):
        click.echo(f"Branch: {result['branch']}")
    
    click.echo(f"\nManifests found: {', '.join(result['manifests'].keys()) or 'none'}")
    click.echo(f"Python source files: {result.get('python_source_files', 0)}")
    click.echo(f"Test files: {len(result.get('test_files', []))}")
    
    if result.get("dependencies"):
        click.echo("\nDependencies:")
        for dep in result["dependencies"]:
            click.echo(f"  - {dep}")


def _print_findings(findings: list[MaintenanceFinding]):
    """Print findings table."""
    if not findings:
        click.echo("\nNo findings.")
        return
    
    click.echo("\nFindings:")
    click.echo("-" * 80)
    for f in findings:
        severity_color = {
            "critical": "red",
            "warning": "yellow",
            "info": "blue",
        }.get(f.severity, "white")
        
        click.echo(f"  [{click.style(f.severity.upper(), fg=severity_color)}] {f.category}: {f.title}")
        click.echo(f"    Evidence: {f.evidence}")
        if f.hypothesis:
            click.echo(f"    Hypothesis: {f.hypothesis}")
        click.echo()


def generate_capsule(inspection: dict, findings: list[MaintenanceFinding]) -> str:
    """Generate Dependency Exit Capsule as Markdown."""
    lines = []
    lines.append("# Dependency Exit Capsule")
    lines.append(f"\nGenerated: {datetime.now().isoformat()}")
    lines.append(f"Tool: RepoRescue-AI v0.1.0")
    lines.append(f"Target: {inspection['path']}")
    
    # Repository Metadata
    lines.append("\n## Repository Metadata")
    lines.append(f"- **Path**: {inspection['path']}")
    lines.append(f"- **Type**: {inspection['repo_type']}")
    if inspection.get("commit"):
        lines.append(f"- **Commit**: {inspection['commit']}")
    if inspection.get("branch"):
        lines.append(f"- **Branch**: {inspection['branch']}")
    if inspection.get("remote_url"):
        lines.append(f"- **Remote**: {inspection['remote_url']}")
    
    # Dependency Manifests
    lines.append("\n## Dependency Manifests")
    for name, manifest in inspection["manifests"].items():
        lines.append(f"\n### {name}")
        lines.append("```")
        if isinstance(manifest.get("data"), str):
            lines.append(manifest["data"][:2000])
        else:
            lines.append(json.dumps(manifest.get("data", {}), indent=2)[:2000])
        lines.append("```")
    
    # Source & Test Files
    py_files = inspection.get("python_source_files", [])
    test_files = inspection.get("test_files", [])
    lines.append(f"\n## Source Files ({len(py_files)} found)")
    for f in py_files[:20]:
        lines.append(f"- {f}")
    if len(py_files) > 20:
        lines.append(f"- ... and {len(py_files) - 20} more")
    
    lines.append(f"\n## Test Files ({len(test_files)} found)")
    for f in test_files[:20]:
        lines.append(f"- {f}")
    
    # Findings
    lines.append("\n## Findings")
    if not findings:
        lines.append("\nNo maintenance issues detected.")
    else:
        for i, f in enumerate(findings, 1):
            lines.append(f"\n### Finding {i}: {f.title}")
            lines.append(f"- **Category**: {f.category}")
            lines.append(f"- **Severity**: {f.severity}")
            lines.append(f"- **Evidence**: {f.evidence}")
            if f.hypothesis:
                lines.append(f"- **Hypothesis (AI)**: {f.hypothesis}")
            if f.proposed_action:
                lines.append(f"- **Proposed Action**: {f.proposed_action}")
            if f.risk:
                lines.append(f"- **Risk Rating**: {f.risk}")
    
    # AI Disclosure
    lines.append("\n## AI Disclosure")
    lines.append("This capsule contains AI-generated hypotheses (marked as **Hypothesis (AI)**).")
    lines.append("All hypotheses require human verification before action.")
    lines.append("Verified findings are based on static analysis of repository artifacts.")
    
    # Commands Executed
    lines.append("\n## Commands Executed")
    lines.append("```bash")
    lines.append(f"re-rescue inspect {inspection['path']}")
    lines.append(f"re-rescue analyze {inspection['path']}")
    lines.append("```")
    
    # Compatibility & Limitations
    lines.append("\n## Compatibility Gaps & Limitations")
    lines.append("- Read-only analysis; no modifications made to target repository")
    lines.append("- AI hypotheses based on bounded context (manifests + key source files)")
    lines.append("- Python version compatibility checked against hackathon requirements (3.12–3.13)")
    lines.append("- Dependency analysis limited to declared manifests; transitive deps not resolved")
    lines.append("- Test execution not performed in static mode; use --no-ai for pure static analysis")
    
    return "\n".join(lines)


@cli.command()
@click.argument("repo_url", type=str)
@click.argument("question", type=str)
@click.option("--limit", "-l", type=int, default=5, help="Max results to return")
def cognee_query(repo_url: str, question: str, limit: int):
    """Query Cognee knowledge graph for historical repo context.

    Examples:
      re-rescue cognee-query https://github.com/user/repo "What dependency issues were found?"
      re-rescue cognee-query https://github.com/user/repo "Show me critical findings"
    """
    if not COGNEE_AVAILABLE:
        click.echo("Cognee not available. Install with: pip install cognee", err=True)
        return

    click.echo(f"Querying Cognee for: {repo_url}")
    click.echo(f"Question: {question}")

    results = asyncio.run(query_repo_memory(repo_url, question))

    if not results:
        click.echo("No relevant history found.")
        return

    click.echo(f"\nFound {len(results)} relevant memories:")
    for i, r in enumerate(results[:limit], 1):
        meta = r.get("metadata", {})
        content = r.get("content", "")[:300]
        click.echo(f"\n{i}. {meta.get('timestamp', 'unknown')} - {meta.get('repo_url', 'unknown')}")
        click.echo(f"   {content}...")


@cli.command()
@click.option("--repo-url", type=str, help="Filter by repository URL")
def cognee_insights(repo_url: str | None):
    """Show cross-repository insights from Cognee knowledge graph."""
    if not COGNEE_AVAILABLE:
        click.echo("Cognee not available. Install with: pip install cognee", err=True)
        return

    from .cognee_memory import CogneeMemory

    async def run():
        memory = CogneeMemory()
        try:
            insights = await memory.get_cross_repo_insights()
            click.echo("\n=== Cross-Repository Insights ===")
            click.echo(f"Total analyses: {insights['total_analyses']}")
            click.echo(f"Unique repositories: {insights['unique_repos']}")
            click.echo(f"\nTop finding categories:")
            for cat, count in insights['top_categories']:
                click.echo(f"  {cat}: {count}")
            click.echo(f"\nSeverity distribution:")
            for sev, count in insights['severity_distribution'].items():
                click.echo(f"  {sev}: {count}")
        finally:
            await memory.close()

    asyncio.run(run())


if __name__ == "__main__":
    cli()