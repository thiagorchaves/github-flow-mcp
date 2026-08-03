from __future__ import annotations

from typing import Any

from ..base import client, config
from ..confirmation import consume_confirmation, issue_confirmation
from ..errors import GitHubFlowError
from ..policy import (
    ensure_basecamp_in_body,
    required_labels,
    require_write_enabled,
    validate_basecamp_url,
)


def _owner_or_default(owner: str) -> str:
    resolved = owner or config().default_owner
    if not resolved:
        raise GitHubFlowError("owner is required when GITHUB_DEFAULT_OWNER is not configured.")
    return resolved


def list_pull_requests(
    repo: str,
    owner: str = "",
    state: str = "open",
    max_items: int = 100,
) -> list[dict[str, Any]]:
    """List pull requests ordered by most recently updated."""
    owner = _owner_or_default(owner)
    pulls = client().paginate(
        f"repos/{owner}/{repo}/pulls",
        params={"state": state, "sort": "updated", "direction": "desc"},
        max_items=max(1, min(max_items, 300)),
    )
    return [compact_pr(item) for item in pulls]


def get_pull_request(repo: str, pull_number: int, owner: str = "") -> dict[str, Any]:
    """Get a pull request by number."""
    owner = _owner_or_default(owner)
    data = client().request("GET", f"repos/{owner}/{repo}/pulls/{pull_number}")
    return compact_pr(data)


def list_pull_request_files(
    repo: str,
    pull_number: int,
    owner: str = "",
    max_items: int = 300,
) -> list[dict[str, Any]]:
    """List changed files in a pull request."""
    owner = _owner_or_default(owner)
    files = client().paginate(
        f"repos/{owner}/{repo}/pulls/{pull_number}/files",
        max_items=max(1, min(max_items, 300)),
    )
    return [
        {
            "filename": item.get("filename"),
            "status": item.get("status"),
            "additions": item.get("additions"),
            "deletions": item.get("deletions"),
            "changes": item.get("changes"),
            "previous_filename": item.get("previous_filename"),
        }
        for item in files
    ]


def list_pull_request_reviews(
    repo: str,
    pull_number: int,
    owner: str = "",
) -> list[dict[str, Any]]:
    """List reviews for a pull request."""
    owner = _owner_or_default(owner)
    reviews = client().paginate(
        f"repos/{owner}/{repo}/pulls/{pull_number}/reviews",
        max_items=300,
    )
    return [
        {
            "id": item.get("id"),
            "user": (item.get("user") or {}).get("login"),
            "state": item.get("state"),
            "body": item.get("body"),
            "submitted_at": item.get("submitted_at"),
            "html_url": item.get("html_url"),
        }
        for item in reviews
    ]


def _reviewer_plan(
    repo: str,
    owner: str,
    requested: list[str],
    bot_reviewer: str,
) -> list[dict[str, Any]]:
    usernames: list[str] = []
    for username in [*requested, bot_reviewer]:
        username = username.strip()
        if username and username not in usernames:
            usernames.append(username)

    output: list[dict[str, Any]] = []
    for username in usernames:
        try:
            data = client().request(
                "GET",
                f"repos/{owner}/{repo}/collaborators/{username}/permission",
            )
            permission = data.get("permission")
            output.append(
                {
                    "username": username,
                    "available": bool(permission),
                    "permission": permission,
                    "role_name": data.get("role_name"),
                }
            )
        except GitHubFlowError:
            output.append(
                {
                    "username": username,
                    "available": False,
                    "permission": None,
                    "role_name": None,
                }
            )
    return output


def _build_pull_request_preview(
    repo: str,
    title: str,
    head: str,
    body: str,
    basecamp_url: str = "",
    base: str = "",
    owner: str = "",
    draft: bool = False,
    labels: list[str] | None = None,
    reviewers: list[str] | None = None,
) -> dict[str, Any]:
    cfg = config()
    owner = _owner_or_default(owner)
    basecamp_url = validate_basecamp_url(basecamp_url, cfg)
    final_labels = required_labels(repo, labels or [], cfg)
    final_body = ensure_basecamp_in_body(body, basecamp_url)
    reviewer_plan = _reviewer_plan(repo, owner, reviewers or [], cfg.bot_reviewer)
    return {
        "action": "create_pull_request",
        "owner": owner,
        "repo": repo,
        "title": title,
        "head": head,
        "base": base or cfg.default_base_branch,
        "draft": draft,
        "body": final_body,
        "basecamp_url": basecamp_url,
        "labels": final_labels,
        "reviewers": reviewer_plan,
        "write_enabled": cfg.write_enabled,
        "will_write": False,
        "requires_explicit_confirmation": True,
    }


def _pr_payload(preview: dict[str, Any]) -> dict[str, Any]:
    return {
        "owner": preview["owner"],
        "repo": preview["repo"],
        "title": preview["title"],
        "head": preview["head"],
        "base": preview["base"],
        "draft": preview["draft"],
        "body": preview["body"],
        "basecamp_url": preview["basecamp_url"],
        "labels": preview["labels"],
        "reviewers": [item["username"] for item in preview["reviewers"] if item.get("available")],
    }


def preview_pull_request(
    repo: str,
    title: str,
    head: str,
    body: str,
    basecamp_url: str = "",
    base: str = "",
    owner: str = "",
    draft: bool = False,
    labels: list[str] | None = None,
    reviewers: list[str] | None = None,
) -> dict[str, Any]:
    """Preview a pull request and issue a token bound to the exact final payload."""
    cfg = config()
    preview = _build_pull_request_preview(
        repo=repo,
        title=title,
        head=head,
        body=body,
        basecamp_url=basecamp_url,
        base=base,
        owner=owner,
        draft=draft,
        labels=labels,
        reviewers=reviewers,
    )
    return {
        **preview,
        **issue_confirmation("create_pull_request", _pr_payload(preview), cfg),
    }


def create_pull_request(
    repo: str,
    title: str,
    head: str,
    body: str,
    basecamp_url: str = "",
    base: str = "",
    owner: str = "",
    draft: bool = False,
    labels: list[str] | None = None,
    reviewers: list[str] | None = None,
    confirmation_id: str = "",
) -> dict[str, Any]:
    """Create only the pull request represented by a valid preview token."""
    cfg = config()
    require_write_enabled(cfg)
    preview = _build_pull_request_preview(
        repo=repo,
        title=title,
        head=head,
        body=body,
        basecamp_url=basecamp_url,
        base=base,
        owner=owner,
        draft=draft,
        labels=labels,
        reviewers=reviewers,
    )
    consume_confirmation("create_pull_request", _pr_payload(preview), confirmation_id)

    owner = str(preview["owner"])
    created = client().request(
        "POST",
        f"repos/{owner}/{repo}/pulls",
        json={
            "title": preview["title"],
            "head": preview["head"],
            "base": preview["base"],
            "body": preview["body"],
            "draft": preview["draft"],
        },
    )
    number = int(created["number"])
    warnings: list[str] = []

    if preview["labels"]:
        try:
            client().request(
                "POST",
                f"repos/{owner}/{repo}/issues/{number}/labels",
                json={"labels": preview["labels"]},
            )
        except GitHubFlowError as exc:
            warnings.append(f"PR created, but labels failed: {exc}")

    available_reviewers = [
        item["username"] for item in preview["reviewers"] if item.get("available")
    ]
    if available_reviewers:
        try:
            client().request(
                "POST",
                f"repos/{owner}/{repo}/pulls/{number}/requested_reviewers",
                json={"reviewers": available_reviewers},
            )
        except GitHubFlowError as exc:
            warnings.append(f"PR created, but reviewer request failed: {exc}")

    result = compact_pr(created)
    result.update(
        {
            "ok": True,
            "labels_requested": preview["labels"],
            "reviewers_requested": available_reviewers,
            "basecamp_url": preview["basecamp_url"],
            "warnings": warnings,
            "confirmation_consumed": True,
        }
    )
    return result


def preview_pull_request_comment(
    repo: str,
    pull_number: int,
    body: str,
    owner: str = "",
) -> dict[str, Any]:
    """Preview a PR timeline comment and issue a token for the exact body."""
    cfg = config()
    owner = _owner_or_default(owner)
    payload = {
        "owner": owner,
        "repo": repo,
        "pull_number": pull_number,
        "body": body,
    }
    return {
        "action": "add_pull_request_comment",
        **payload,
        "will_write": False,
        "write_enabled": cfg.write_enabled,
        "requires_explicit_confirmation": True,
        **issue_confirmation("add_pull_request_comment", payload, cfg),
    }


def add_pull_request_comment(
    repo: str,
    pull_number: int,
    body: str,
    owner: str = "",
    confirmation_id: str = "",
) -> dict[str, Any]:
    """Add only the PR comment represented by a valid preview token."""
    cfg = config()
    require_write_enabled(cfg)
    owner = _owner_or_default(owner)
    payload = {
        "owner": owner,
        "repo": repo,
        "pull_number": pull_number,
        "body": body,
    }
    consume_confirmation("add_pull_request_comment", payload, confirmation_id)
    data = client().request(
        "POST",
        f"repos/{owner}/{repo}/issues/{pull_number}/comments",
        json={"body": body},
    )
    return {
        "ok": True,
        "id": data.get("id"),
        "html_url": data.get("html_url"),
        "created_at": data.get("created_at"),
        "confirmation_consumed": True,
    }


def build_basecamp_pr_update(
    repo: str,
    pull_number: int,
    summary: str = "",
    owner: str = "",
) -> dict[str, Any]:
    """Build Markdown for a separate Basecamp MCP without writing to Basecamp."""
    pr = get_pull_request(repo, pull_number, owner)
    lines = [
        "## Pull request opened",
        "",
        f"- **PR:** [#{pr['number']} {pr['title']}]({pr['html_url']})",
        f"- **Branch:** `{pr['head']}` → `{pr['base']}`",
        f"- **State:** {pr['state']}",
        f"- **Draft:** {'yes' if pr['draft'] else 'no'}",
    ]
    if summary.strip():
        lines.extend(["", "## Summary", "", summary.strip()])
    return {
        "project_update_markdown": "\n".join(lines),
        "pull_request": pr,
        "will_write": False,
        "next_step": (
            "Send project_update_markdown to a Basecamp MCP preview tool, then request "
            "explicit approval before publication."
        ),
    }


def compact_pr(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": item.get("number"),
        "title": item.get("title"),
        "state": item.get("state"),
        "draft": item.get("draft"),
        "html_url": item.get("html_url"),
        "body": item.get("body"),
        "head": ((item.get("head") or {}).get("ref")),
        "head_sha": ((item.get("head") or {}).get("sha")),
        "base": ((item.get("base") or {}).get("ref")),
        "user": ((item.get("user") or {}).get("login")),
        "created_at": item.get("created_at"),
        "updated_at": item.get("updated_at"),
        "mergeable": item.get("mergeable"),
        "mergeable_state": item.get("mergeable_state"),
    }
