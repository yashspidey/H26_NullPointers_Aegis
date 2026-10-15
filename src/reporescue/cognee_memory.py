"""Cognee integration for RepoRescue-AI.

Provides knowledge graph persistence for repository analyses.
Stores Dependency Exit Capsules, findings, and repo metadata
so the agent can 'remember' previous analyses and provide context.
"""

import json
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


class CogneeMemory:
    """Manages Cognee knowledge graph for RepoRescue-AI analysis history."""

    def __init__(self, cognee_config: Optional[Dict[str, Any]] = None):
        self.cognee_config = cognee_config or {}
        self._cognee = None

    async def _get_cognee(self):
        """Lazy initialization of Cognee client."""
        if self._cognee is None:
            try:
                from cognee import Cognee
                self._cognee = Cognee(**self.cognee_config)
                await self._cognee.initialize()
            except ImportError:
                raise RuntimeError(
                    "Cognee not installed. Install with: pip install cognee"
                )
        return self._cognee

    async def store_analysis(
        self,
        repo_url: str,
        branch: str,
        commit: str,
        inspection: Dict[str, Any],
        capsule: str,
        findings: List[Dict[str, Any]],
    ) -> str:
        """Store a full analysis in the knowledge graph.

        Returns the Cognee document ID.
        """
        cognee = await self._get_cognee()

        # Prepare rich metadata for querying
        metadata = {
            "repo_url": repo_url,
            "branch": branch,
            "commit": commit,
            "timestamp": datetime.now().isoformat(),
            "repo_type": inspection.get("repo_type"),
            "python_version": inspection.get("project_info", {}).get("python_requires"),
            "total_findings": len(findings),
            "severity_counts": {
                "critical": sum(1 for f in findings if f.get("severity") == "critical"),
                "warning": sum(1 for f in findings if f.get("severity") == "warning"),
                "info": sum(1 for f in findings if f.get("severity") == "info"),
            },
            "categories": list(set(f.get("category") for f in findings)),
            "dependency_manifests": list(inspection.get("manifests", {}).keys()),
            "source_file_count": len(inspection.get("python_source_files", [])),
            "test_file_count": len(inspection.get("test_files", [])),
        }

        # Store capsule as main content with metadata
        doc_id = await cognee.add(
            content=capsule,
            metadata=metadata,
        )

        # Also store individual findings as separate nodes for granular queries
        for finding in findings:
            await cognee.add(
                content=f"{finding.get('title')}: {finding.get('description')}",
                metadata={
                    "parent_doc_id": doc_id,
                    "finding_category": finding.get("category"),
                    "finding_severity": finding.get("severity"),
                    "repo_url": repo_url,
                    "commit": commit,
                },
            )

        return doc_id

    async def query_repo_history(
        self,
        repo_url: str,
        query: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Query historical analyses for a repository.

        Example queries:
        - "What dependency issues were found before?"
        - "Show me all critical findings for this repo"
        - "Has pydantic version been a problem before?"
        """
        cognee = await self._get_cognee()

        results = await cognee.search(
            query=query,
            filters={"repo_url": repo_url},
            limit=limit,
        )

        return results

    async def get_repo_timeline(self, repo_url: str) -> List[Dict[str, Any]]:
        """Get chronological history of analyses for a repo."""
        cognee = await self._get_cognee()

        results = await cognee.search(
            query=f"analysis history for {repo_url}",
            filters={"repo_url": repo_url},
            limit=50,
        )

        # Sort by timestamp
        return sorted(
            results,
            key=lambda x: x.get("metadata", {}).get("timestamp", ""),
            reverse=True,
        )

    async def find_similar_issues(
        self,
        finding_category: str,
        finding_description: str,
        exclude_repo: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find similar issues across all analyzed repositories."""
        cognee = await self._get_cognee()

        query = f"{finding_category}: {finding_description}"
        filters = {"finding_category": finding_category}
        if exclude_repo:
            filters["repo_url!="] = exclude_repo

        return await cognee.search(query=query, filters=filters, limit=limit)

    async def get_cross_repo_insights(self) -> Dict[str, Any]:
        """Get aggregate insights across all analyzed repositories."""
        cognee = await self._get_cognee()

        results = await cognee.search(
            query="common dependency issues patterns",
            limit=100,
        )

        # Aggregate
        categories = {}
        severities = {"critical": 0, "warning": 0, "info": 0}
        repos = set()

        for r in results:
            meta = r.get("metadata", {})
            cat = meta.get("finding_category") or meta.get("categories", [])
            if isinstance(cat, list):
                for c in cat:
                    categories[c] = categories.get(c, 0) + 1
            else:
                categories[cat] = categories.get(cat, 0) + 1

            sev = meta.get("finding_severity")
            if sev in severities:
                severities[sev] += 1

            repos.add(meta.get("repo_url"))

        return {
            "total_analyses": len(results),
            "unique_repos": len(repos),
            "top_categories": sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10],
            "severity_distribution": severities,
        }

    async def close(self):
        """Close Cognee connection."""
        if self._cognee:
            await self._cognee.close()
            self._cognee = None


# Convenience functions for CLI usage
async def store_capsule_in_cognee(
    repo_path: str,
    capsule_path: str,
    inspection: Dict[str, Any],
    findings: List[Dict[str, Any]],
    cognee_config: Optional[Dict[str, Any]] = None,
) -> str:
    """Store a generated capsule in Cognee."""
    memory = CogneeMemory(cognee_config)
    try:
        capsule_text = Path(capsule_path).read_text(encoding="utf-8")
        repo_url = inspection.get("remote_url") or f"local://{repo_path}"
        commit = inspection.get("commit", "unknown")
        branch = inspection.get("branch", "unknown")

        doc_id = await memory.store_analysis(
            repo_url=repo_url,
            branch=branch,
            commit=commit,
            inspection=inspection,
            capsule=capsule_text,
            findings=findings,
        )
        return doc_id
    finally:
        await memory.close()


async def query_repo_memory(
    repo_url: str,
    question: str,
    cognee_config: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Query Cognee for historical context about a repo."""
    memory = CogneeMemory(cognee_config)
    try:
        return await memory.query_repo_history(repo_url, question)
    finally:
        await memory.close()