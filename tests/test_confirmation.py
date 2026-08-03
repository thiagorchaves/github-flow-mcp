from pathlib import Path

import pytest

from github_flow_mcp.confirmation import consume_confirmation, issue_confirmation
from github_flow_mcp.config import GitHubConfig
from github_flow_mcp.errors import GitHubFlowError


def cfg() -> GitHubConfig:
    return GitHubConfig(
        token="test", api_base="https://api.github.com", api_version="2022-11-28", user_agent="test",
        default_owner="example", initials="tc", default_base_branch="main", local_repos_root=Path("/tmp"),
        write_enabled=True, confirmation_ttl_seconds=300, basecamp_required=False, prod_marker="production",
        review_by_ai_repos=(), review_by_ai_label="ReviewByAI", bot_reviewer="",
    )


def test_confirmation_is_single_use() -> None:
    payload = {"repo": "infra", "branch": "tc-change"}
    issued = issue_confirmation("create_branch", payload, cfg())
    consume_confirmation("create_branch", payload, issued["confirmation_id"])
    with pytest.raises(GitHubFlowError, match="already been used"):
        consume_confirmation("create_branch", payload, issued["confirmation_id"])


def test_confirmation_rejects_payload_change() -> None:
    issued = issue_confirmation("create_branch", {"repo": "infra", "sha": "abc"}, cfg())
    with pytest.raises(GitHubFlowError, match="no longer matches"):
        consume_confirmation("create_branch", {"repo": "infra", "sha": "def"}, issued["confirmation_id"])
