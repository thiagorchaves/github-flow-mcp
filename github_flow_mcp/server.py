from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from .base import config
from .tools.auth import get_authenticated_user, healthcheck
from .tools.branches import create_remote_branch, preview_remote_branch
from .tools.local import inspect_local_repository, preview_branch_name, preview_local_commit
from .tools.pull_requests import (
    add_pull_request_comment,
    build_basecamp_pr_update,
    create_pull_request,
    get_pull_request,
    list_pull_request_files,
    list_pull_request_reviews,
    list_pull_requests,
    preview_pull_request,
    preview_pull_request_comment,
)
from .tools.repositories import get_collaborator_permission, get_repository, list_branches
from .tools.workflows import list_workflow_runs, list_workflows

mcp = FastMCP("github-flow-mcp")

for tool in [
    healthcheck,
    get_authenticated_user,
    get_repository,
    list_branches,
    get_collaborator_permission,
    inspect_local_repository,
    preview_branch_name,
    preview_local_commit,
    preview_remote_branch,
    list_pull_requests,
    get_pull_request,
    list_pull_request_files,
    list_pull_request_reviews,
    preview_pull_request,
    preview_pull_request_comment,
    build_basecamp_pr_update,
    list_workflows,
    list_workflow_runs,
]:
    mcp.tool()(tool)

if config().write_enabled:
    for tool in [create_remote_branch, create_pull_request, add_pull_request_comment]:
        mcp.tool()(tool)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
