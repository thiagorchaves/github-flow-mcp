from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from .config import GitHubConfig
from .errors import GitHubFlowError


@dataclass(frozen=True)
class BranchPlan:
    branch_name: str
    source_branch: str
    environment: str
    production: bool
    basecamp_url: str


def slugify(value: str) -> str:
    slug = value.strip().lower().replace("_", " ")
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


def validate_basecamp_url(url: str, cfg: GitHubConfig) -> str:
    candidate = (url or "").strip()
    if cfg.basecamp_required and not candidate:
        raise GitHubFlowError("Basecamp link is required by policy before creating a branch or pull request.")
    if candidate:
        parsed = urlparse(candidate)
        if parsed.scheme not in {"http", "https"} or "basecamp" not in parsed.netloc.lower():
            raise GitHubFlowError("basecamp_url must be a valid Basecamp HTTP(S) URL.")
    return candidate


def require_write_enabled(cfg: GitHubConfig) -> None:
    if not cfg.write_enabled:
        raise GitHubFlowError(
            "GitHub writes are disabled. Set GITHUB_WRITE_ENABLED=true only for sessions that need remote mutations."
        )


def build_branch_plan(
    description: str,
    environment: str,
    source_branch: str,
    basecamp_url: str,
    cfg: GitHubConfig,
) -> BranchPlan:
    change_slug = slugify(description)
    if not change_slug:
        raise GitHubFlowError("description must produce a non-empty branch suffix.")

    env_normalized = slugify(environment or "")
    prod_marker = slugify(cfg.prod_marker)
    production = env_normalized in {"prod", "production", prod_marker}
    prefix = slugify(cfg.initials)
    if not prefix:
        raise GitHubFlowError("GITHUB_INITIALS must contain letters or numbers.")

    branch_name = f"{prefix}-{prod_marker}-{change_slug}" if production else f"{prefix}-{change_slug}"
    return BranchPlan(
        branch_name=branch_name,
        source_branch=source_branch,
        environment=environment or "unspecified",
        production=production,
        basecamp_url=validate_basecamp_url(basecamp_url, cfg),
    )


def required_labels(repo: str, requested: list[str], cfg: GitHubConfig) -> list[str]:
    labels: list[str] = []
    for label in requested:
        if label and label not in labels:
            labels.append(label)
    if repo in cfg.review_by_ai_repos and cfg.review_by_ai_label not in labels:
        labels.append(cfg.review_by_ai_label)
    return labels


def ensure_basecamp_in_body(body: str, basecamp_url: str) -> str:
    body = (body or "").strip()
    if basecamp_url and basecamp_url not in body:
        return f"{body}\n\n## Basecamp\n\n{basecamp_url}".strip()
    return body
