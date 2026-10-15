"""Example: Using RepoRescue-AI with Kestra and Cognee programmatically."""

import asyncio
import json
from pathlib import Path

from reporescue.inspection import inspect_repository
from reporescue.analysis import analyze_repository
from reporescue.cli import generate_capsule
from reporescue.cognee_memory import CogneeMemory, store_capsule_in_cognee


async def main():
    repo_path = "https://github.com/rishrek/LinkWatch"  # or local path
    local_path = "./LinkWatch"  # assume cloned

    print("=" * 60)
    print("RepoRescue-AI + Kestra + Cognee Demo")
    print("=" * 60)

    # 1. Inspect repository (can run in Kestra task)
    print("\n[1/4] Inspecting repository...")
    inspection = inspect_repository(local_path)
    print(f"  Repo type: {inspection['repo_type']}")
    print(f"  Commit: {inspection.get('commit', 'unknown')[:8]}")
    print(f"  Manifests: {list(inspection['manifests'].keys())}")
    print(f"  Source files: {len(inspection.get('python_source_files', []))}")
    print(f"  Test files: {len(inspection.get('test_files', []))}")

    # 2. Run analysis (can run in Kestra task)
    print("\n[2/4] Running analysis...")
    result = analyze_repository(local_path, ai_analysis=None)  # no AI for demo
    findings = result["findings"]
    print(f"  Total findings: {result['summary']['total_findings']}")
    print(f"  By severity: {result['summary']['by_severity']}")
    print(f"  Categories: {result['summary']['categories']}")

    # 3. Generate capsule
    print("\n[3/4] Generating Dependency Exit Capsule...")
    from reporescue.analysis import MaintenanceFinding
    finding_objs = [MaintenanceFinding(**f) for f in findings]
    capsule = generate_capsule(inspection, finding_objs)
    capsule_path = f"Dependency_Exit_Capsule_demo.md"
    Path(capsule_path).write_text(capsule, encoding="utf-8")
    print(f"  Saved to: {capsule_path}")

    # 4. Store in Cognee knowledge graph
    print("\n[4/4] Storing in Cognee knowledge graph...")
    try:
        doc_id = await store_capsule_in_cognee(
            repo_path=local_path,
            capsule_path=capsule_path,
            inspection=inspection,
            findings=findings,
        )
        print(f"  ✓ Stored with doc ID: {doc_id}")

        # Query the memory
        print("\n[Bonus] Querying Cognee for historical context...")
        memory = CogneeMemory()
        try:
            # Query for this repo's history
            history = await memory.query_repo_history(
                repo_url=inspection.get("remote_url") or f"local://{local_path}",
                query="What dependency issues were found?",
            )
            print(f"  Found {len(history)} relevant memories")

            # Get cross-repo insights
            insights = await memory.get_cross_repo_insights()
            print(f"  Cross-repo insights: {insights['unique_repos']} repos analyzed")
            print(f"  Top categories: {insights['top_categories'][:3]}")
        finally:
            await memory.close()

    except ImportError:
        print("  ⚠ Cognee not installed. Run: pip install -e .[cognee]")
    except Exception as e:
        print(f"  ⚠ Cognee error: {e}")

    print("\n" + "=" * 60)
    print("Demo complete! Check the capsule file and Kestra flow.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())