from __future__ import annotations

from typing import Any

from ..base import client, config


def get_repository(repo: str, owner: str = "") -> dict[str, Any]:
    """Gets repository metadata and permissions."""
    owner = owner or config().default_owner
    data = client().request("GET", f"repos/{owner}/{repo}")
    return {
        "full_name": data.get("full_name"),
        "private": data.get("private"),
        "default_branch": data.get("default_branch"),
        "archived": data.get("archived"),
        "visibility": data.get("visibility"),
        "permissions": data.get("permissions"),
        "html_url": data.get("html_url"),
    }


def list_branches(repo: str, owner: str = "", max_items: int = 100) -> list[dict[str, Any]]:
    """Lists repository branches."""
    owner = owner or config().default_owner
    branches = client().paginate(
        f"repos/{owner}/{repo}/branches", max_items=max(1, min(max_items, 300))
    )
    return [
        {
            "name": item.get("name"),
            "protected": item.get("protected"),
            "sha": (item.get("commit") or {}).get("sha"),
        }
        for item in branches
    ]


def get_collaborator_permission(repo: str, username: str, owner: str = "") -> dict[str, Any]:
    """Checks whether a user/bot is a collaborator and returns repository permission."""
    owner = owner or config().default_owner
    data = client().request("GET", f"repos/{owner}/{repo}/collaborators/{username}/permission")
    return {
        "user": (data.get("user") or {}).get("login", username),
        "permission": data.get("permission"),
        "role_name": data.get("role_name"),
        "available": bool(data.get("permission")),
    }
