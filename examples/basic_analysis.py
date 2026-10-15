#!/usr/bin/env python3
"""Basic example of using RepoRescue-AI."""
import sys

from reporescure.inspection import inspect_repository


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python basic_analysis.py <repository-path>")
        sys.exit(1)

    repo_path = sys.argv[1]
    print(f"Inspecting: {repo_path}")
    inspection = inspect_repository(repo_path)

    if inspection.get("repo_type"):
        print(f"Repository type: {inspection['repo_type']}")
        print(f"Commit: {inspection.get('commit', 'unknown')[:8] if inspection.get('commit') else 'unknown'}")
        print(f"Python requires: {inspection.get('project_info', {}).get('python_requires', 'unknown')}")
    else:
        print("Not a recognized repository")