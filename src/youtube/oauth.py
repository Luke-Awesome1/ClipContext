"""Google OAuth 2.0 (web server flow) + YouTube Data API v3 channel lookup.

Uses google-auth-oauthlib's Flow for the authorization-code exchange and
google-auth's Credentials/Request for refresh — no hand-rolled OAuth
cryptography. Uploads themselves are handled in src/youtube/upload.py.
"""

import logging
import secrets
from datetime import datetime
from typing import Optional

import httpx
from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.config import (
    get_google_client_id,
    get_google_client_secret,
    get_google_oauth_redirect_uri,
    get_google_oauth_scopes,
)
from src.youtube.token_store import StoredCredentials

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_REVOKE_URL = "https://oauth2.googleapis.com/revoke"


class YouTubeReconnectRequired(RuntimeError):
    """Raised when stored credentials can no longer be refreshed."""


class NoChannelError(RuntimeError):
    """Raised when the authorized Google account has no YouTube channel."""


def _client_config() -> dict:
    return {
        "web": {
            "client_id": get_google_client_id(),
            "client_secret": get_google_client_secret(),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [get_google_oauth_redirect_uri()],
        }
    }


def generate_code_verifier() -> str:
    """PKCE code_verifier (RFC 7636): 43-128 chars from the unreserved set.

    token_urlsafe's alphabet (A-Za-z0-9-_) is a valid subset.
    """
    return secrets.token_urlsafe(64)


def _build_flow(code_verifier: str) -> Flow:
    # Explicit code_verifier (not autogenerate_code_verifier=True) because a
    # *separate* Flow instance is constructed for the authorization step
    # (build_authorization_url) than for the token-exchange step
    # (exchange_code) — those happen in different HTTP requests, seconds to
    # minutes apart. Each Flow would otherwise generate its own random PKCE
    # verifier, and Google's token endpoint would reject the mismatch with
    # "Missing code verifier" / invalid_grant. The verifier must be
    # generated once and threaded through both steps (see
    # src.youtube.state_store, which stores it alongside the CSRF state).
    flow = Flow.from_client_config(
        _client_config(),
        scopes=get_google_oauth_scopes(),
        code_verifier=code_verifier,
    )
    flow.redirect_uri = get_google_oauth_redirect_uri()
    return flow


def build_authorization_url(state: str, code_verifier: str) -> str:
    flow = _build_flow(code_verifier)
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return authorization_url


def exchange_code(code: str, code_verifier: str) -> Credentials:
    flow = _build_flow(code_verifier)
    flow.fetch_token(code=code)
    return flow.credentials


def credentials_to_stored(
    credentials: Credentials,
    channel_id: Optional[str] = None,
    channel_title: Optional[str] = None,
    channel_thumbnail_url: Optional[str] = None,
) -> StoredCredentials:
    return StoredCredentials(
        access_token=credentials.token,
        refresh_token=credentials.refresh_token,
        token_uri=credentials.token_uri,
        scopes=list(credentials.scopes or get_google_oauth_scopes()),
        expiry=credentials.expiry.isoformat() if credentials.expiry else None,
        channel_id=channel_id,
        channel_title=channel_title,
        channel_thumbnail_url=channel_thumbnail_url,
    )


def _stored_to_credentials(stored: StoredCredentials) -> Credentials:
    expiry = datetime.fromisoformat(stored.expiry) if stored.expiry else None

    return Credentials(
        token=stored.access_token,
        refresh_token=stored.refresh_token,
        token_uri=stored.token_uri,
        client_id=get_google_client_id(),
        client_secret=get_google_client_secret(),
        scopes=stored.scopes,
        expiry=expiry,
    )


def ensure_valid_credentials(stored: StoredCredentials) -> tuple[Credentials, bool]:
    """Returns (usable credentials, whether a refresh happened).

    Raises YouTubeReconnectRequired if the access token is expired/invalid
    and there is no refresh token, or the refresh token itself has been
    revoked/expired (Google's `invalid_grant`).
    """
    credentials = _stored_to_credentials(stored)

    if credentials.valid:
        return credentials, False

    if not credentials.refresh_token:
        raise YouTubeReconnectRequired("No refresh token available; reconnect required.")

    try:
        credentials.refresh(GoogleAuthRequest())
    except RefreshError as exc:
        raise YouTubeReconnectRequired(
            "YouTube refresh token is invalid or has been revoked."
        ) from exc

    return credentials, True


def build_youtube_client(credentials: Credentials):
    return build("youtube", "v3", credentials=credentials, cache_discovery=False)


def fetch_channel_info(credentials: Credentials) -> dict:
    youtube = build_youtube_client(credentials)
    response = youtube.channels().list(part="snippet", mine=True).execute()

    items = response.get("items", [])

    if not items:
        raise NoChannelError("No YouTube channel is available for this Google account.")

    snippet = items[0].get("snippet", {})
    thumbnails = snippet.get("thumbnails", {})
    thumbnail_url = (
        thumbnails.get("default", {}).get("url")
        or thumbnails.get("medium", {}).get("url")
    )

    return {
        "channel_id": items[0].get("id"),
        "channel_title": snippet.get("title"),
        "channel_thumbnail_url": thumbnail_url,
    }


def revoke_credentials(stored: StoredCredentials) -> None:
    """Best-effort revoke. An already-expired/revoked token is not an error."""
    token = stored.refresh_token or stored.access_token

    if not token:
        return

    try:
        httpx.post(
            GOOGLE_TOKEN_REVOKE_URL,
            params={"token": token},
            headers={"content-type": "application/x-www-form-urlencoded"},
            timeout=10.0,
        )
    except httpx.HTTPError:
        logger.warning("Failed to revoke YouTube token (best-effort); continuing.")


__all__ = [
    "NoChannelError",
    "YouTubeReconnectRequired",
    "build_authorization_url",
    "build_youtube_client",
    "credentials_to_stored",
    "ensure_valid_credentials",
    "exchange_code",
    "fetch_channel_info",
    "generate_code_verifier",
    "revoke_credentials",
    "HttpError",
]
