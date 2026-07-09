"""Reusable FastAPI dependencies for ClipContext account authentication.

Distinct from YouTube OAuth (src/youtube/session.py etc.): this verifies a
Firebase ID token identifying a ClipContext account, not a YouTube
authorization session. A request can carry either, both, or neither.
"""

from typing import Optional

from fastapi import Header, HTTPException

from src.firebase.auth import AuthenticatedUser, InvalidFirebaseToken, verify_id_token
from src.firebase.users import upsert_user_profile


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None

    parts = authorization.split(" ", 1)

    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None

    token = parts[1].strip()
    return token or None


async def get_optional_current_user(
    authorization: Optional[str] = Header(None),
) -> Optional[AuthenticatedUser]:
    token = _extract_bearer_token(authorization)

    if not token:
        return None

    try:
        return verify_id_token(token)
    except InvalidFirebaseToken:
        return None


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> AuthenticatedUser:
    token = _extract_bearer_token(authorization)

    if not token:
        raise HTTPException(status_code=401, detail="Authentication required.")

    try:
        user = verify_id_token(token)
    except InvalidFirebaseToken as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    upsert_user_profile(user)
    return user
