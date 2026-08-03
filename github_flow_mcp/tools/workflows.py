from __future__ import annotations

from typing import Any

from ..base import client, config


def list_workflows(repo: str, owner: str = "") -> list[dict[str, Any]]:
    """Lists GitHub Actions workflows in a repository."""
    owner = owner or config().default_owner
    data = client().request("GET", f"repos/{owner}/{repo}/actions/workflows")
    return [
        {
            "id": item.get("id"),
            "name": item.get("name"),
            "path": item.get("path"),
            "state": item.get("state"),
            "html_url": item.get("html_url"),
        }
        for item in data.get("workflows", [])
    ]


def list_workflow_runs(
    repo: str,
    owner: str = "",
    branch: str = "",
    status: str = "",
    event: str = "",
    max_items: int = 100,
) -> list[dict[str, Any]]:
    """Lists recent GitHub Actions workflow runs with optional filters."""
    owner = owner or config().default_owner
    params: dict[str, Any] = {}
    if branch:
        params["branch"] = branch
    if status:
        params["status"] = status
    if event:
        params["event"] = event
    data = client().request(
        "GET",
        f"repos/{owner}/{repo}/actions/runs",
        params={**params, "per_page": max(1, min(max_items, 100))},
    )
    return [
        {
            "id": item.get("id"),
            "name": item.get("name"),
            "display_title": item.get("display_title"),
            "event": item.get("event"),
            "status": item.get("status"),
            "conclusion": item.get("conclusion"),
            "head_branch": item.get("head_branch"),
            "head_sha": item.get("head_sha"),
            "run_number": item.get("run_number"),
            "html_url": item.get("html_url"),
            "created_at": item.get("created_at"),
            "updated_at": item.get("updated_at"),
        }
        for item in data.get("workflow_runs", [])[:max_items]
    ]
