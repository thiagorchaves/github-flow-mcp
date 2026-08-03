from __future__ import annotations

from typing import Any

from ..base import client, config


def healthcheck() -> dict[str, Any]:
    cfg = config()
    return {
        "ok": True,
        "token_present": bool(cfg.token),
        "api_base": cfg.api_base,
        "api_version": cfg.api_version,
        "default_owner": cfg.default_owner or None,
        "initials": cfg.initials,
        "write_enabled": cfg.write_enabled,
        "preview_bound_confirmations": True,
        "confirmation_ttl_seconds": cfg.confirmation_ttl_seconds,
        "basecamp_required": cfg.basecamp_required,
        "review_by_ai_repos": list(cfg.review_by_ai_repos),
        "bot_reviewer": cfg.bot_reviewer or None,
    }


def get_authenticated_user() -> dict[str, Any]:
    user = client().request("GET", "user")
    return {
        "login": user.get("login"),
        "id": user.get("id"),
        "name": user.get("name"),
        "html_url": user.get("html_url"),
        "type": user.get("type"),
    }
