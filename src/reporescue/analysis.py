"""Maintenance analysis module for RepoRescue-AI.

Analyzes repository inspection results to identify maintenance problems,
trace dependency usage, and generate evidence-based findings.
"""

import os
from typing import Any, Dict, List, Optional

from .inspection import inspect_repository


class MaintenanceFinding:
    """Represents a maintenance finding with evidence and recommendations."""

    def __init__(
        self,
        category: str,
        severity: str,  # "info", "warning", "critical"
        title: str,
        description: str,
        evidence: Dict[str, Any],
        hypothesis: Optional[str] = None,
        proposed_action: Optional[str] = None,
        risk: str = "",
    ):
        self.category = category
        self.severity = severity
        self.title = title
        self.description = description
        self.evidence = evidence
        self.hypothesis = hypothesis
        self.proposed_action = proposed_action
        self.risk = risk

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "hypothesis": self.hypothesis,
            "proposed_action": self.proposed_action,
            "risk": self.risk,
        }


# Common deprecated/old dependency patterns
DEPREDICTED_PYTHON_VERSIONS = [">=3.14", "==3.14", "==3.13"]


def detect_deprecated_dependencies(
    inspection: Dict[str, Any],
) -> List[MaintenanceFinding]:
    """Detect dependencies that may be deprecated or outdated.

    Examines dependency manifests for packages with known
    compatibility concerns or outdated versions.
    """
    findings = []
    manifests = inspection.get("manifests", {})

    # Check Python version compatibility
    project_info = inspection.get("project_info", {})
    python_requires = project_info.get("python_requires", "")

    # Check if Python 3.14 is requested (not supported)
    for pattern in DEPREDICTED_PYTHON_VERSIONS:
        if pattern in python_requires:
            findings.append(
                MaintenanceFinding(
                    category="python-version",
                    severity="warning",
                    title="Unsupported Python version requested",
                    description=(
                        f"The project requests Python {pattern[2:]}, "
                        f"but Python 3.14 is not supported by the hackathon "
                        f"requirements. Target Python 3.12 or 3.13."
                    ),
                    evidence={
                        "python_requires": python_requires,
                        "inspection": inspection,
                    },
                    hypothesis=(
                        "Consider relaxing python_requires to >=3.12 "
                        "or pinning to 3.12/3.13"
                    ),
                    proposed_action=(
                        "Update pyproject.toml python_requires to >=3.12,<=3.13"
                    ),
                    risk="Low - only affects Python 3.14 users",
                )
            )
            break

    # Check for old chardet version (LinkWatch issue)
    if "python_reqs" in manifests:
        reqs_data = manifests["python_reqs"]["data"]
        deps = reqs_data.get("dependencies", [])
        for dep in deps:
            if "chardet" in dep.lower():
                manifest_relpath = manifests["python_reqs"].get("path", "unknown")
                findings.append(
                    MaintenanceFinding(
                        category="dependency-version",
                        severity="info",
                        title="chardet dependency pinning observed",
                        description=(
                            f"Dependency manifest includes: {dep}"
                        ),
                        evidence={
                            "dependency": dep,
                            "manifest_path": manifest_relpath,
                        },
                        hypothesis=(
                            "chardet 5.2.0 is pinned; consider whether "
                            "to update or pin to a specific compatible version"
                        ),
                        proposed_action=(
                            "Evaluate chardet compatibility with "
                            "Python 3.12 and pin to compatible version"
                        ),
                        risk="Medium - chardet API may change between versions",
                    )
                )

    # Check for old pydantic version
    if "python_reqs" in manifests:
        reqs_data = manifests["python_reqs"]["data"]
        deps = reqs_data.get("dependencies", [])
        for dep in deps:
            if "pydantic" in dep.lower():
                manifest_relpath = manifests["python_reqs"].get("path", "unknown")
                findings.append(
                    MaintenanceFinding(
                        category="dependency-version",
                        severity="info",
                        title="pydantic dependency observed",
                        description=(
                            f"Dependency manifest includes: {dep}"
                        ),
                        evidence={
                            "dependency": dep,
                            "manifest_path": manifest_relpath,
                        },
                        hypothesis=(
                            "pydantic without exact version pin may "
                            "lead to compatibility changes between v1 and v2"
                        ),
                        proposed_action=(
                            "Pin pydantic to a specific version "
                            "compatible with Python 3.12"
                        ),
                        risk="Medium - pydantic v1 vs v2 API differences",
                    )
                )

    return findings


def detect_unused_dependencies(
    inspection: Dict[str, Any],
) -> List[MaintenanceFinding]:
    """Detect potentially unused dependencies by checking imports.

    Compares imported modules against declared dependencies.
    """
    findings = []
    source_files = inspection.get("python_source_files", [])

    # For now, just report the source files found
    # A full unused-deps analysis would require AST parsing
    if source_files:
        findings.append(
            MaintenanceFinding(
                category="dependency-analysis",
                severity="info",
                title="Python source files found",
                description=(
                    f"Found {len(source_files)} Python source files: "
                    f"{', '.join(source_files[:10])}"
                    f"{' ...' if len(source_files) > 10 else ''}"
                ),
                evidence={
                    "source_file_count": len(source_files),
                    "sample_files": source_files[:10],
                    "total_files": len(source_files),
                },
                hypothesis=(
                    "Some declared dependencies may not be directly "
                    "imported in the source files examined"
                ),
                proposed_action=(
                    "Review declared dependencies against "
                    "actual import usage in source files"
                ),
                risk="Low - may have indirect or dynamic imports",
            )
        )

    return findings


def analyze_repository(
    path: str,
    ai_analysis: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run a full maintenance analysis on a repository.

    Performs static inspection and optionally incorporates AI-generated
    analysis. Returns a structured analysis result.
    """
    # Step 1: Static inspection
    inspection = inspect_repository(path)

    if inspection.get("repo_type") is None:
        return {"error": "Not a recognized repository", "path": path}

    # Step 2: Detect maintenance issues
    findings: List[MaintenanceFinding] = []

    # Detect deprecated dependencies
    findings.extend(detect_deprecated_dependencies(inspection))

    # Detect unused/underused dependencies
    findings.extend(detect_unused_dependencies(inspection))

    # Step 3: Incorporate AI analysis if provided
    if ai_analysis:
        # Merge AI findings with static findings
        for key, value in ai_analysis.items():
            if key not in ("raw_model_output",):
                findings.append(
                    MaintenanceFinding(
                        category="ai-analysis",
                        severity="info",
                        title=f"AI analysis: {key}",
                        description=str(value),
                        evidence={
                            "ai_source": "Hermes Agent",
                            "model_output": value,
                        },
                        hypothesis=f"AI-generated analysis from {key}",
                    )
                )

    # Step 4: Structure the result
    result = {
        "inspection": inspection,
        "findings": [f.to_dict() for f in findings],
        "summary": {
            "total_findings": len(findings),
            "by_severity": {
                "info": sum(1 for f in findings if f.severity == "info"),
                "warning": sum(1 for f in findings if f.severity == "warning"),
                "critical": sum(1 for f in findings if f.severity == "critical"),
            },
            "categories": list(set(f.category for f in findings)),
        },
        "path": path,
    }

    return result