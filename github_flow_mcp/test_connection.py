from __future__ import annotations

import json

from .tools.auth import get_authenticated_user, healthcheck


def main() -> None:
    print(json.dumps(healthcheck(), indent=2, ensure_ascii=False))
    print(json.dumps(get_authenticated_user(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
