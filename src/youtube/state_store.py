"""In-memory OAuth `state` store for CSRF protection.

Each value is single-use: `consume()` pops it so a replayed callback (e.g.
the user hitting back/forward, or an attacker replaying a captured URL)
fails on the second attempt. Entries also expire after
OAUTH_STATE_TTL_SECONDS so an abandoned OAuth flow can't be resurrected
later.
"""

import secrets
import threading
import time
from dataclasses import dataclass
from typing import Optional

from src.youtube.constants import OAUTH_STATE_TTL_SECONDS


@dataclass
class _StateEntry:
    session_id: str
    code_verifier: str
    expires_at: float


class OAuthStateStore:
    def __init__(self) -> None:
        self._states: dict[str, _StateEntry] = {}
        self._lock = threading.Lock()

    def create(self, session_id: str, code_verifier: str) -> str:
        state = secrets.token_urlsafe(32)

        with self._lock:
            self._purge_expired_locked()
            self._states[state] = _StateEntry(
                session_id=session_id,
                code_verifier=code_verifier,
                expires_at=time.time() + OAUTH_STATE_TTL_SECONDS,
            )

        return state

    def consume(self, state: str, session_id: str) -> Optional[str]:
        """Returns the PKCE code_verifier bound to this state on success, else None."""
        with self._lock:
            entry = self._states.pop(state, None)

        if entry is None:
            return None

        if time.time() > entry.expires_at:
            return None

        if not secrets.compare_digest(entry.session_id, session_id):
            return None

        return entry.code_verifier

    def _purge_expired_locked(self) -> None:
        now = time.time()
        expired = [key for key, entry in self._states.items() if entry.expires_at < now]

        for key in expired:
            del self._states[key]


oauth_state_store = OAuthStateStore()
