"""Repository inspection module for RepoRescue-AI.

Inspects Git repositories, detects project metadata, and extracts
dependency and source code information.
"""

import os
import json
import subprocess
from typing import Any, Dict, List, Optional


GIT_DIR = ".git"


def detect_repo_type(path: str) -> Optional[str]:
    """Detect the type of repository at the given path.

    Returns 'git', 'svn', 'hg', or None if not recognized.
    """
    if not os.path.isdir(os.path.join(path, GIT_DIR)):
        return None
    return "git"


def get_git_commit(path: str) -> Optional[str]:
    """Get the current HEAD commit hash for the repository."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def get_git_branch(path: str) -> Optional[str]:
    """Get the current branch name."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def find_dependency_manifests(path: str) -> Dict[str, str]:
    """Find dependency manifest files and their paths.

    Returns a dict of {manifest_type: filepath}.
    """
    manifests = {}
    for root, dirs, files in os.walk(path):
        # Skip .git directory
        if GIT_DIR in root.split(os.sep):
            continue
        for f in files:
            fname = f.lower()
            if fname in {"pyproject.toml", "setup.py", "setup.cfg",
                         "requirements.txt", "requirements-dev.txt",
                         "environment.yml", "glide.yaml",
                         "go.mod", "package.json", "Cargo.toml"}:
                relpath = os.path.relpath(os.path.join(root, f), path)
                if fname == "pyproject.toml" or fname == "setup.py":
                    manifests["python"] = relpath
                elif fname == "requirements.txt":
                    manifests["python_reqs"] = relpath
                elif fname == "requirements-dev.txt":
                    manifests["python_reqs_dev"] = relpath
                elif fname == "glide.yaml":
                    manifests["go"] = relpath
                elif fname == "go.mod":
                    manifests["go_mod"] = relpath
                elif fname == "package.json":
                    manifests["node"] = relpath
                elif fname == "Cargo.toml":
                    manifests["rust"] = relpath
    return manifests


def read_manifest(path: str) -> Optional[Dict[str, Any]]:
    """Read and parse a dependency manifest file.

    Supported: pyproject.toml, setup.py, requirements.txt,
    package.json, Cargo.toml, go.mod
    """
    if not os.path.isfile(path):
        return None

    try:
        if path.lower().endswith("pyproject.toml"):
            import toml
            data = toml.load(path)
            return {"type": "pyproject_toml", "data": data}
        elif path.lower().endswith("requirements.txt"):
            deps = []
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        deps.append(line)
            return {"type": "requirements_txt", "data": {"dependencies": deps}}
        elif path.lower().endswith("package.json"):
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
            return {"type": "package_json", "data": data}
        elif path.lower().endswith("go.mod"):
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return {"type": "go_mod", "data": {"content": content}}
        else:
            return {"type": "unknown", "path": path}
    except Exception as e:
        return {"type": "error", "error": str(e)}


def find_python_source_files(path: str) -> List[str]:
    """Find Python source files in the repository.

    Returns a list of file paths ending in .py.
    """
    source_files = []
    for root, dirs, files in os.walk(path):
        if GIT_DIR in root.split(os.sep):
            continue
        # Skip __pycache__ and .egg-info
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".egg-info", "build", "dist")]
        for f in files:
            if f.endswith(".py"):
                relpath = os.path.relpath(os.path.join(root, f), path)
                source_files.append(relpath)
    return source_files


def find_test_files(path: str) -> List[str]:
    """Find test files in the repository."""
    test_files = []
    for root, dirs, files in os.walk(path):
        if GIT_DIR in root.split(os.sep):
            continue
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".egg-info", "build", "dist")]
        for f in files:
            if f.startswith("test_") or f.endswith("_test.py"):
                relpath = os.path.relpath(os.path.join(root, f), path)
                test_files.append(relpath)
    return test_files


def inspect_repository(path: str) -> Dict[str, Any]:
    """Perform a comprehensive inspection of a repository.

    Returns a dict with all available metadata about the repository.
    """
    repo_type = detect_repo_type(path)
    if repo_type is None:
        return {"repo_type": None, "error": "Not a recognized repository"}

    commit = get_git_commit(path)
    branch = get_git_branch(path)

    # Find dependency manifests
    manifests = find_dependency_manifests(path)

    # Read key manifests
    manifest_data = {}
    for manifest_type, manifest_path in manifests.items():
        # Don't overwrite if already read
        if manifest_type not in manifest_data:
            read = read_manifest(os.path.join(path, manifest_path))
            if read and "error" not in read:
                manifest_data[manifest_type] = read

    # Find Python source files
    py_files = find_python_source_files(path)
    test_files = find_test_files(path)

    # Try to get basic project info from pyproject.toml
    project_info = {"python_requires": ">=3.12"}
    if "python" in manifest_data:
        py_data = manifest_data["python"]["data"]
        if isinstance(py_data, dict):
            project_info["python_requires"] = py_data.get("requires-python", ">=3.12")
            project_info["project_name"] = py_data.get("project", {}).get("name", "")

    return {
        "repo_type": repo_type,
        "path": os.path.abspath(path),
        "commit": commit,
        "branch": branch,
        "manifests": manifest_data,
        "python_source_files": py_files,
        "test_files": test_files,
        "project_info": project_info,
    }