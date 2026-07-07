import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


MODEL_ID = (
    "accounts/fireworks/models/kimi-k2p6"
)

BASE_URL = (
    "https://api.fireworks.ai/inference/v1"
)


_client = None


def get_fireworks_client() -> OpenAI:
    global _client

    if _client is None:
        api_key = os.getenv(
            "FIREWORKS_API_KEY"
        )

        if not api_key:
            raise ValueError(
                "FIREWORKS_API_KEY is not set in .env"
            )

        _client = OpenAI(
            api_key=api_key,
            base_url=BASE_URL,
            timeout=120.0,
            max_retries=0,
        )

    return _client