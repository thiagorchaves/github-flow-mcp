from __future__ import annotations

from typing import Any

import httpx

from .config import GitHubConfig
from .errors import GitHubFlowError


class GitHubClient:
    def __init__(self, config: GitHubConfig | None = None) -> None:
        self.config = config or GitHubConfig.from_env()

    def url(self, path: str) -> str:
        if path.startswith(("https://", "http://")):
            return path
        return f"{self.config.api_base.rstrip('/')}/{path.lstrip('/')}"

    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.config.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": self.config.api_version,
            "User-Agent": self.config.user_agent,
        }

    def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        with httpx.Client(timeout=40, headers=self.headers(), follow_redirects=True) as client:
            response = client.request(method, self.url(path), json=json, params=params)

        if response.status_code >= 400:
            self._raise_api_error(response)

        if response.status_code == 204 or not response.content:
            return {"ok": True}
        return response.json()

    def paginate(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        max_items: int = 300,
    ) -> list[dict[str, Any]]:
        output: list[dict[str, Any]] = []
        page = 1
        per_page = 100
        while len(output) < max_items:
            merged = {"per_page": per_page, "page": page, **(params or {})}
            data = self.request("GET", path, params=merged)
            if not isinstance(data, list):
                raise GitHubFlowError(f"Expected list from GitHub endpoint: {path}")
            output.extend(data)
            if len(data) < per_page:
                break
            page += 1
        return output[:max_items]

    def _raise_api_error(self, response: httpx.Response) -> None:
        status = response.status_code
        body = response.text[:1500]
        if status == 401:
            hint = "Unauthorized. Check GITHUB_TOKEN and whether it is expired or revoked."
        elif status == 403:
            hint = (
                "Forbidden or rate limited. Check token permissions, repository access, "
                "and rate-limit headers."
            )
        elif status == 404:
            hint = "Resource not found or hidden by insufficient token permissions."
        elif status == 409:
            hint = (
                "Conflict. The branch/ref may already exist or the repository state may not "
                "allow this operation."
            )
        elif status == 422:
            hint = (
                "Validation failed. Check branch names, labels, reviewers, and pull-request "
                "parameters."
            )
        else:
            hint = "GitHub API returned an error."
        raise GitHubFlowError(f"GitHub API error {status}: {hint} Response: {body}")
