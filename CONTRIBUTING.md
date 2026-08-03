# Contributing

1. Fork or create a branch from `main`.
2. Keep changes focused and avoid adding organization-specific defaults or private data.
3. Run `uv sync --extra dev` and then the checks below.
4. Open a pull request describing behavior and security impact.

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy github_flow_mcp
uv run pytest
```

Mutation tools should remain disabled by default and new remote writes should use preview-bound confirmation tokens.
