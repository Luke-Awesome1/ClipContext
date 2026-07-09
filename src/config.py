import os


REQUIRED_ENVIRONMENT_VARIABLES = (
    "FIREWORKS_API_KEY",
    "YOUTUBE_API_KEY",
    "GEMINI_API_KEY",
)

DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:3001,http://127.0.0.1:3001,"
    "http://localhost:3002,http://127.0.0.1:3002,"
    "http://localhost:3003,http://127.0.0.1:3003"
)
DEFAULT_MAX_UPLOAD_SIZE_MB = 200


def validate_environment() -> None:
    missing = [
        variable
        for variable in REQUIRED_ENVIRONMENT_VARIABLES
        if not os.getenv(variable)
    ]

    if missing:
        missing_text = ", ".join(missing)

        raise RuntimeError(
            "Missing required environment "
            f"variables: {missing_text}. "
            "Copy .env.example to .env and "
            "configure the required API keys."
        )


def get_allowed_origins() -> list[str]:
    raw = os.getenv("ALLOWED_ORIGINS", DEFAULT_ALLOWED_ORIGINS)
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def get_max_upload_size_bytes() -> int:
    raw = os.getenv("MAX_UPLOAD_SIZE_MB", str(DEFAULT_MAX_UPLOAD_SIZE_MB))

    try:
        megabytes = int(raw)
    except ValueError:
        megabytes = DEFAULT_MAX_UPLOAD_SIZE_MB

    return megabytes * 1024 * 1024


def get_port() -> int:
    raw = os.getenv("PORT", "8000")

    try:
        return int(raw)
    except ValueError:
        return 8000


# --- YouTube OAuth ("Connect with YouTube") ---
#
# These are optional at process startup (unlike REQUIRED_ENVIRONMENT_VARIABLES
# above) so the rest of ClipContext keeps working without them configured.
# Endpoints that need them check is_youtube_oauth_configured() and return a
# structured YOUTUBE_OAUTH_NOT_CONFIGURED error instead of crashing.
#
# youtube.upload alone is NOT sufficient to call channels.list(mine=true) —
# verified against the live API, which rejects that combination with a 403
# "insufficientPermissions" — so youtube.readonly is included to identify
# the connected channel. Still well short of the broad "youtube" (manage
# account) scope.
DEFAULT_GOOGLE_OAUTH_SCOPES = (
    "https://www.googleapis.com/auth/youtube.upload "
    "https://www.googleapis.com/auth/youtube.readonly"
)


def get_google_client_id() -> str | None:
    return os.getenv("GOOGLE_CLIENT_ID") or None


def get_google_client_secret() -> str | None:
    return os.getenv("GOOGLE_CLIENT_SECRET") or None


def get_google_oauth_redirect_uri() -> str | None:
    return os.getenv("GOOGLE_OAUTH_REDIRECT_URI") or None


def is_youtube_oauth_configured() -> bool:
    return bool(
        get_google_client_id()
        and get_google_client_secret()
        and get_google_oauth_redirect_uri()
    )


def get_google_oauth_scopes() -> list[str]:
    raw = os.getenv("GOOGLE_OAUTH_SCOPES", DEFAULT_GOOGLE_OAUTH_SCOPES)
    return [scope.strip() for scope in raw.replace(",", " ").split() if scope.strip()]


def get_frontend_url() -> str:
    return os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")


def get_cookie_secure() -> bool:
    return os.getenv("COOKIE_SECURE", "false").strip().lower() == "true"


def get_cookie_samesite() -> str:
    return os.getenv("COOKIE_SAMESITE", "lax").strip().lower()


# --- Firebase (ClipContext account authentication + Firestore artifacts) ---
#
# Deliberately separate from GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET above,
# which authorize YouTube uploads — not the same identity or permission as
# a ClipContext account login. See README for the full distinction.
#
# Optional at process startup, same pattern as YouTube OAuth: anonymous
# ClipContext use (upload/process/results/YouTube) must keep working with
# zero Firebase configuration. Endpoints that need it check
# is_firebase_configured() and return a structured error instead of
# crashing the whole API.


def get_firebase_project_id() -> str | None:
    return os.getenv("FIREBASE_PROJECT_ID") or None


def get_firebase_service_account_json() -> str | None:
    return os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON") or None


def get_google_application_credentials() -> str | None:
    return os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or None
