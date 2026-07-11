"""Firebase ID token verification.

Never trusts a uid/email/display name sent directly by the browser — the
only identity the backend accepts is one cryptographically verified from a
Firebase ID token via the Admin SDK.
"""

from dataclasses import dataclass
from typing import Optional

from src.firebase.admin import get_firebase_app


class InvalidFirebaseToken(RuntimeError):
    """Raised for a missing, malformed, expired, or revoked ID token."""


@dataclass(frozen=True)
class AuthenticatedUser:
    uid: str
    email: Optional[str]
    display_name: Optional[str]
    photo_url: Optional[str]


def verify_id_token(id_token: str) -> AuthenticatedUser:
    from firebase_admin import auth as firebase_auth

    app = get_firebase_app()

    if app is None:
        raise InvalidFirebaseToken("Firebase authentication is not configured.")

    try:
        decoded = firebase_auth.verify_id_token(id_token, app=app)
    except Exception as exc:
        raise InvalidFirebaseToken("Invalid or expired authentication token.") from exc

    uid = decoded.get("uid")

    if not uid:
        raise InvalidFirebaseToken("Token did not contain a user id.")

    return AuthenticatedUser(
        uid=uid,
        email=decoded.get("email"),
        display_name=decoded.get("name"),
        photo_url=decoded.get("picture"),
    )
