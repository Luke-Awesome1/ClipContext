"""Opaque, cryptographically random ClipContext session identity.

There is no user-account system in ClipContext (see README "Known
limitations"). For the YouTube OAuth connection we need *some* way to bind
"this browser" to "these YouTube credentials" without one global token
shared by every visitor. A signed-nothing, server-generated random session
id in an HttpOnly cookie is the minimum viable mechanism: the id itself is
unguessable, the cookie can't be read or set by page JavaScript, and every
YouTube credential/upload lookup is keyed strictly by this id.
"""

import secrets

from fastapi import Request, Response

from src.config import get_cookie_samesite, get_cookie_secure
from src.youtube.constants import SESSION_COOKIE_MAX_AGE_SECONDS, SESSION_COOKIE_NAME


def get_session_id(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE_NAME)


def new_session_id() -> str:
    return secrets.token_urlsafe(32)


def set_session_cookie(response: Response, session_id: str) -> None:
    samesite = get_cookie_samesite()

    # SameSite=None cookies are rejected by browsers unless Secure is also
    # set, regardless of COOKIE_SECURE — enforce that pairing here rather
    # than relying on every deployment to configure it correctly.
    secure = get_cookie_secure() or samesite == "none"

    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        max_age=SESSION_COOKIE_MAX_AGE_SECONDS,
        httponly=True,
        secure=secure,
        samesite=samesite,
        path="/",
    )
