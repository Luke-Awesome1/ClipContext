"""Centralized Firebase Admin SDK initialization.

Lazy and idempotent: firebase_admin.initialize_app() is called at most
once, on first use, not at import time. This keeps anonymous ClipContext
functionality (upload, processing, results, YouTube) working with zero
Firebase configuration — only the code paths that actually need
Firebase-backed auth/persistence call get_firebase_app() and see a
structured "not configured" state instead of crashing the whole API.

Credential resolution order (first match wins):
1. FIREBASE_SERVICE_ACCOUNT_JSON — inline service-account JSON, useful on
   hosts that don't support mounting a credentials file (e.g. many PaaS
   environment-variable-only deployments).
2. GOOGLE_APPLICATION_CREDENTIALS — path to a service-account JSON file.
   Never commit this file; it must be gitignored.
3. Application Default Credentials — works out of the box when the
   backend itself runs on Google Cloud (Cloud Run, GCE, GKE) with an
   attached service account, no explicit credential file needed.
"""

from __future__ import annotations

import json
import logging
import threading
from typing import TYPE_CHECKING, Optional

from src.config import (
    get_firebase_project_id,
    get_firebase_service_account_json,
    get_google_application_credentials,
)

if TYPE_CHECKING:
    import firebase_admin

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_app: Optional[firebase_admin.App] = None
_init_attempted = False
_init_error: Optional[str] = None


def _build_credentials():
    # Deferred: firebase_admin (and its grpc/google-cloud-firestore
    # dependencies) are only needed once an account/artifact endpoint is
    # actually hit — importing at module load would add them to every
    # process's boot-time memory footprint even for anonymous use. See
    # docs/Deployment.md "the real memory constraint".
    from firebase_admin import credentials

    service_account_json = get_firebase_service_account_json()
    if service_account_json:
        return credentials.Certificate(json.loads(service_account_json))

    credentials_path = get_google_application_credentials()
    if credentials_path:
        return credentials.Certificate(credentials_path)

    return credentials.ApplicationDefault()


def get_firebase_app() -> Optional[firebase_admin.App]:
    import firebase_admin

    global _app, _init_attempted, _init_error

    if _app is not None:
        return _app

    with _lock:
        if _app is not None:
            return _app

        if _init_attempted:
            return None

        _init_attempted = True
        project_id = get_firebase_project_id()

        if not project_id:
            _init_error = "FIREBASE_PROJECT_ID is not set."
            logger.info("Firebase Admin not configured: %s", _init_error)
            return None

        try:
            cred = _build_credentials()
            _app = firebase_admin.initialize_app(cred, {"projectId": project_id})
            logger.info("Firebase Admin initialized for project %s", project_id)
        except Exception as exc:
            _init_error = str(exc)
            logger.exception("Failed to initialize Firebase Admin SDK")
            _app = None

    return _app


def is_firebase_configured() -> bool:
    return get_firebase_app() is not None


def get_firebase_init_error() -> Optional[str]:
    return _init_error


def get_firestore_client():
    from firebase_admin import firestore

    app = get_firebase_app()

    if app is None:
        raise RuntimeError("Firebase Admin is not configured.")

    return firestore.client(app)


def reset_for_tests() -> None:
    """Test-only hook: clears cached init state between test cases."""
    import firebase_admin

    global _app, _init_attempted, _init_error

    with _lock:
        if _app is not None:
            try:
                firebase_admin.delete_app(_app)
            except Exception:
                pass

        _app = None
        _init_attempted = False
        _init_error = None
