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
