"""Minimal user profile persistence: users/{uid} in Firestore.

Called as a side effect of successful authentication (see
src/api/auth_dependencies.py). Best-effort: a Firestore hiccup here must
never fail the authenticated request itself, since the profile write is
incidental to whatever the user actually asked to do.
"""

import logging
from datetime import datetime, timezone

from src.firebase.admin import get_firestore_client, is_firebase_configured
from src.firebase.auth import AuthenticatedUser

logger = logging.getLogger(__name__)


def upsert_user_profile(user: AuthenticatedUser) -> None:
    if not is_firebase_configured():
        return

    try:
        client = get_firestore_client()
        doc_ref = client.collection("users").document(user.uid)
        now = datetime.now(timezone.utc)
        existing = doc_ref.get()

        payload = {
            "display_name": user.display_name,
            "email": user.email,
            "photo_url": user.photo_url,
            "last_login_at": now,
        }

        if not existing.exists:
            payload["created_at"] = now

        doc_ref.set(payload, merge=True)
    except Exception:
        logger.exception("Failed to upsert user profile for uid=%s", user.uid)
