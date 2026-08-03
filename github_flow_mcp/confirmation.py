from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import threading
import time
from dataclasses import dataclass
from typing import Any

from .config import GitHubConfig
from .errors import GitHubFlowError


@dataclass(frozen=True)
class PendingConfirmation:
    action: str
    fingerprint: str
    expires_at: float


_CONFIRMATIONS: dict[str, PendingConfirmation] = {}
_LOCK = threading.Lock()
_MAX_PENDING = 500


def _fingerprint(payload: dict[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _purge_expired(now: float) -> None:
    for token in [k for k, v in _CONFIRMATIONS.items() if v.expires_at <= now]:
        _CONFIRMATIONS.pop(token, None)


def issue_confirmation(action: str, payload: dict[str, Any], cfg: GitHubConfig) -> dict[str, Any]:
    now = time.time()
    token = secrets.token_urlsafe(32)
    pending = PendingConfirmation(
        action=action,
        fingerprint=_fingerprint(payload),
        expires_at=now + cfg.confirmation_ttl_seconds,
    )
    with _LOCK:
        _purge_expired(now)
        if len(_CONFIRMATIONS) >= _MAX_PENDING:
            oldest = min(_CONFIRMATIONS, key=lambda k: _CONFIRMATIONS[k].expires_at)
            _CONFIRMATIONS.pop(oldest, None)
        _CONFIRMATIONS[token] = pending
    return {
        "confirmation_id": token,
        "confirmation_expires_in_seconds": cfg.confirmation_ttl_seconds,
        "confirmation_single_use": True,
    }


def consume_confirmation(action: str, payload: dict[str, Any], confirmation_id: str) -> None:
    if not confirmation_id:
        raise GitHubFlowError(
            "confirmation_id is required. Generate a preview, show it to the user, and pass the token only after explicit approval."
        )
    now = time.time()
    with _LOCK:
        _purge_expired(now)
        pending = _CONFIRMATIONS.pop(confirmation_id, None)
    if pending is None:
        raise GitHubFlowError("confirmation_id is invalid, expired, or has already been used.")
    if pending.action != action:
        raise GitHubFlowError("confirmation_id was issued for a different action.")
    if not hmac.compare_digest(pending.fingerprint, _fingerprint(payload)):
        raise GitHubFlowError(
            "The requested write no longer matches the approved preview. Generate a new preview."
        )
