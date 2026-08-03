from __future__ import annotations

from typing import Any

from ..base import config
from ..local_git import inspect_repository
from ..policy import build_branch_plan, validate_basecamp_url


def inspect_local_repository(repo_path: str) -> dict[str, Any]:
    """Inspects a local Git repository without changing files, branches, commits, or remotes."""
    return inspect_repository(repo_path, config())


def preview_local_commit(
    repo_path: str,
    commit_message: str,
    basecamp_url: str,
) -> dict[str, Any]:
    """Previews a local commit plan. This tool never creates commits."""
    cfg = config()
    validate_basecamp_url(basecamp_url, cfg)
    state = inspect_repository(repo_path, cfg)
    return {
        "action": "local_commit_preview",
        "commit_message": commit_message.strip(),
        "basecamp_url": basecamp_url,
        "repository": state,
        "will_write": False,
        "note": "Use Kiro/local git for the signed commit after explicit user confirmation.",
    }


def preview_branch_name(
    description: str,
    environment: str = "",
    source_branch: str = "",
    basecamp_url: str = "",
) -> dict[str, Any]:
    """Builds and validates the branch name without creating the branch."""
    cfg = config()
    plan = build_branch_plan(
        description=description,
        environment=environment,
        source_branch=source_branch or cfg.default_base_branch,
        basecamp_url=basecamp_url,
        cfg=cfg,
    )
    return {
        "action": "branch_preview",
        "branch_name": plan.branch_name,
        "source_branch": plan.source_branch,
        "environment": plan.environment,
        "production": plan.production,
        "basecamp_url": plan.basecamp_url,
        "will_write": False,
    }
