from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from .errors import GitHubFlowError

load_dotenv()


def env(name: str, required: bool = True, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise GitHubFlowError(f"Missing required env var: {name}")
    return value or ""


def env_bool(name: str, default: bool = False) -> bool:
    raw = env(name, required=False, default=str(default)).strip().lower()
    if raw in {"1", "true", "yes", "on"}:
        return True
    if raw in {"0", "false", "no", "off"}:
        return False
    raise GitHubFlowError(f"Environment variable {name} must be a boolean")


def env_int(name: str, default: int, minimum: int = 0) -> int:
    raw = env(name, required=False, default=str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise GitHubFlowError(f"Environment variable {name} must be an integer") from exc
    if value < minimum:
        raise GitHubFlowError(f"Environment variable {name} must be >= {minimum}")
    return value


def env_csv(name: str, default: str = "") -> tuple[str, ...]:
    raw = env(name, required=False, default=default)
    return tuple(item.strip() for item in raw.split(",") if item.strip())


@dataclass(frozen=True)
class GitHubConfig:
    token: str
    api_base: str
    api_version: str
    user_agent: str
    default_owner: str
    initials: str
    default_base_branch: str
    local_repos_root: Path
    write_enabled: bool
    confirmation_ttl_seconds: int
    basecamp_required: bool
    prod_marker: str
    review_by_ai_repos: tuple[str, ...]
    review_by_ai_label: str
    bot_reviewer: str

    @classmethod
    def from_env(cls) -> GitHubConfig:
        return cls(
            token=env("GITHUB_TOKEN"),
            api_base=env("GITHUB_API_BASE", required=False, default="https://api.github.com"),
            api_version=env("GITHUB_API_VERSION", required=False, default="2022-11-28"),
            user_agent=env("GITHUB_USER_AGENT", required=False, default="GitHub Flow MCP"),
            default_owner=env("GITHUB_DEFAULT_OWNER", required=False, default=""),
            initials=env("GITHUB_INITIALS", required=False, default="tc"),
            default_base_branch=env("GITHUB_DEFAULT_BASE_BRANCH", required=False, default="main"),
            local_repos_root=Path(
                env(
                    "GITHUB_LOCAL_REPOS_ROOT", required=False, default=str(Path.home() / "Projects")
                )
            )
            .expanduser()
            .resolve(),
            write_enabled=env_bool("GITHUB_WRITE_ENABLED", False),
            confirmation_ttl_seconds=env_int("GITHUB_CONFIRMATION_TTL_SECONDS", 300, minimum=30),
            basecamp_required=env_bool("GITHUB_BASECAMP_REQUIRED", False),
            prod_marker=env("GITHUB_PROD_MARKER", required=False, default="production"),
            review_by_ai_repos=env_csv("GITHUB_REVIEW_BY_AI_REPOS"),
            review_by_ai_label=env(
                "GITHUB_REVIEW_BY_AI_LABEL", required=False, default="ReviewByAI"
            ),
            bot_reviewer=env("GITHUB_BOT_REVIEWER", required=False, default=""),
        )
