"""In-memory, thread-safe, per-session YouTube OAuth credential store.

Limitation (documented, acceptable for hackathon scope, same tradeoff as
src/api/jobs.py's JobRegistry): credentials live in process memory only and
are lost on backend restart. Every visitor sees a normal "disconnected"
state after a restart and simply reconnects — no crash, no cross-session
leakage. Tokens are keyed strictly by the opaque ClipContext session id, so
one browser session can never read or use another session's credentials.

Only the fields required to reconstruct a google.oauth2.credentials.
Credentials object are stored — never the raw Credentials object itself,
and never returned to the frontend.
"""

import threading
from dataclasses import dataclass, replace
from typing import Optional


@dataclass(frozen=True)
class StoredCredentials:
    access_token: str
    refresh_token: Optional[str]
    token_uri: str
    scopes: list[str]
    expiry: Optional[str]  # ISO 8601, naive UTC (matches google-auth's Credentials.expiry)
    channel_id: Optional[str] = None
    channel_title: Optional[str] = None
    channel_thumbnail_url: Optional[str] = None


class YouTubeCredentialStore:
    def __init__(self) -> None:
        self._store: dict[str, StoredCredentials] = {}
        self._lock = threading.Lock()

    def get(self, session_id: str) -> Optional[StoredCredentials]:
        with self._lock:
            return self._store.get(session_id)

    def save(self, session_id: str, credentials: StoredCredentials) -> None:
        with self._lock:
            self._store[session_id] = credentials

    def update_tokens(
        self,
        session_id: str,
        access_token: str,
        expiry: Optional[str],
    ) -> None:
        with self._lock:
            existing = self._store.get(session_id)

            if existing is None:
                return

            self._store[session_id] = replace(
                existing, access_token=access_token, expiry=expiry
            )

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._store.pop(session_id, None)


credential_store = YouTubeCredentialStore()
