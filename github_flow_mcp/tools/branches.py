from __future__ import annotations

from typing import Any

from ..base import client, config
from ..confirmation import consume_confirmation, issue_confirmation
from ..errors import GitHubFlowError
from ..policy import build_branch_plan, require_write_enabled


def _owner_or_default(owner: str) -> str:
    resolved = owner or config().default_owner
    if not resolved:
        raise GitHubFlowError(
            "owner is required when GITHUB_DEFAULT_OWNER is not configured."
        )
    return resolved


def _branch_payload(
    owner: str,
    repo: str,
    branch_name: str,
    source_branch: str,
    source_sha: str,
    basecamp_url: str,
) -> dict[str, Any]:
    return {
        "owner": owner,
        "repo": repo,
        "branch_name": branch_name,
        "source_branch": source_branch,
        "source_sha": source_sha,
        "basecamp_url": basecamp_url,
    }


def preview_remote_branch(
    repo: str,
    description: str,
    environment: str = "",
    source_branch: str = "",
    basecamp_url: str = "",
    owner: str = "",
) -> dict[str, Any]:
    """Preview a branch and issue a token bound to the exact source commit."""
    cfg = config()
    owner = _owner_or_default(owner)
    plan = build_branch_plan(
        description=description,
        environment=environment,
        source_branch=source_branch or cfg.default_base_branch,
        basecamp_url=basecamp_url,
        cfg=cfg,
    )
    source = client().request(
        "GET",
        f"repos/{owner}/{repo}/git/ref/heads/{plan.source_branch}",
    )
    source_sha = str((source.get("object") or {}).get("sha") or "")
    payload = _branch_payload(
        owner,
        repo,
        plan.branch_name,
        plan.source_branch,
        source_sha,
        plan.basecamp_url,
    )
    return {
        "action": "create_remote_branch",
        **payload,
        "production": plan.production,
        "write_enabled": cfg.write_enabled,
        "will_write": False,
        "requires_explicit_confirmation": True,
        **issue_confirmation("create_remote_branch", payload, cfg),
    }


def create_remote_branch(
    repo: str,
    description: str,
    environment: str = "",
    source_branch: str = "",
    basecamp_url: str = "",
    owner: str = "",
    confirmation_id: str = "",
) -> dict[str, Any]:
    """Create only the remote branch represented by a valid preview token."""
    cfg = config()
    require_write_enabled(cfg)
    owner = _owner_or_default(owner)
    plan = build_branch_plan(
        description=description,
        environment=environment,
        source_branch=source_branch or cfg.default_base_branch,
        basecamp_url=basecamp_url,
        cfg=cfg,
    )
    source = client().request(
        "GET",
        f"repos/{owner}/{repo}/git/ref/heads/{plan.source_branch}",
    )
    source_sha = str((source.get("object") or {}).get("sha") or "")
    payload = _branch_payload(
        owner,
        repo,
        plan.branch_name,
        plan.source_branch,
        source_sha,
        plan.basecamp_url,
    )
    consume_confirmation("create_remote_branch", payload, confirmation_id)
    created = client().request(
        "POST",
        f"repos/{owner}/{repo}/git/refs",
        json={"ref": f"refs/heads/{plan.branch_name}", "sha": source_sha},
    )
    return {
        "ok": True,
        "owner": owner,
        "repo": repo,
        "branch_name": plan.branch_name,
        "source_branch": plan.source_branch,
        "sha": (created.get("object") or {}).get("sha", source_sha),
        "ref": created.get("ref"),
        "basecamp_url": plan.basecamp_url,
        "confirmation_consumed": True,
    }
