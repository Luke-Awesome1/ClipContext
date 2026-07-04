import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


api_key = os.getenv("FIREWORKS_API_KEY")

if not api_key:
    raise ValueError(
        "FIREWORKS_API_KEY is not set."
    )


client = OpenAI(
    api_key=api_key,
    base_url=(
        "https://api.fireworks.ai/"
        "inference/v1"
    ),
)


models = client.models.list()


print("\nAVAILABLE MODELS:\n")


for model in models.data:
    print(model.id)