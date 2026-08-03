from pathlib import Path

from github_flow_mcp.config import GitHubConfig
from github_flow_mcp.policy import build_branch_plan, required_labels


def cfg() -> GitHubConfig:
    return GitHubConfig(
        token="test",
        api_base="https://api.github.com",
        api_version="2022-11-28",
        user_agent="test",
        default_owner="example-org",
        initials="tc",
        default_base_branch="main",
        local_repos_root=Path("/tmp"),
        write_enabled=False,
        confirmation_ttl_seconds=300,
        basecamp_required=False,
        prod_marker="production",
        review_by_ai_repos=("infra",),
        review_by_ai_label="ReviewByAI",
        bot_reviewer="",
    )


def test_non_prod_branch() -> None:
    plan = build_branch_plan("Adjust CI runners", "staging", "main", "", cfg())
    assert plan.branch_name == "tc-adjust-ci-runners"


def test_prod_branch() -> None:
    plan = build_branch_plan("Adjust CI runners", "prod", "main", "", cfg())
    assert plan.branch_name == "tc-production-adjust-ci-runners"


def test_review_label() -> None:
    assert required_labels("infra", [], cfg()) == ["ReviewByAI"]
    assert required_labels("website", [], cfg()) == []
