import os


REQUIRED_ENVIRONMENT_VARIABLES = (
    "FIREWORKS_API_KEY",
    "YOUTUBE_API_KEY",
    "GEMINI_API_KEY",
)


def validate_environment() -> None:
    missing = [
        variable
        for variable
        in REQUIRED_ENVIRONMENT_VARIABLES
        if not os.getenv(variable)
    ]

    if missing:
        missing_text = ", ".join(
            missing
        )

        raise RuntimeError(
            "Missing required environment "
            f"variables: {missing_text}. "
            "Copy .env.example to .env and "
            "configure the required API keys."
        )