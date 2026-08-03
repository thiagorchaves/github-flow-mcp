from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

from .config import GitHubConfig
from .errors import GitHubFlowError


def resolve_repo_path(repo_path: str, cfg: GitHubConfig) -> Path:
    path = Path(repo_path).expanduser().resolve()
    try:
        path.relative_to(cfg.local_repos_root)
    except ValueError as exc:
        raise GitHubFlowError(
            f"Local repository must be under GITHUB_LOCAL_REPOS_ROOT: {cfg.local_repos_root}"
        ) from exc
    if not (path / ".git").exists():
        raise GitHubFlowError(f"Not a Git repository: {path}")
    return path


def git(path: Path, *args: str) -> str:
    git_binary = shutil.which("git")
    if not git_binary:
        raise GitHubFlowError("git executable was not found in PATH.")

    result = subprocess.run(  # noqa: S603
        [git_binary, "-C", str(path), *args],
        check=False,
        text=True,
        capture_output=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise GitHubFlowError(
            f"git {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}"
        )
    return result.stdout.strip()


def inspect_repository(repo_path: str, cfg: GitHubConfig) -> dict[str, Any]:
    path = resolve_repo_path(repo_path, cfg)
    status = git(path, "status", "--short")
    branch = git(path, "branch", "--show-current")
    remote = git(path, "remote", "get-url", "origin")
    try:
        ahead_behind = git(path, "rev-list", "--left-right", "--count", "@{upstream}...HEAD")
    except GitHubFlowError:
        ahead_behind = "upstream-not-configured"
    return {
        "path": str(path),
        "branch": branch,
        "origin": remote,
        "clean": not bool(status),
        "status_short": status.splitlines() if status else [],
        "ahead_behind": ahead_behind,
    }
