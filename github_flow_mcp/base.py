from __future__ import annotations

from .client import GitHubClient
from .config import GitHubConfig


def client() -> GitHubClient:
    return GitHubClient()


def config() -> GitHubConfig:
    return GitHubConfig.from_env()
