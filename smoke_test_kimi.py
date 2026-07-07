import base64
import os

from dotenv import load_dotenv
from openai import OpenAI, APIStatusError


load_dotenv()


MODEL_ID = "accounts/fireworks/models/kimi-k2p5"

IMAGE_PATH = (
    "data/frames/test/"
    "candidate_001_1.0s.jpg"
)


def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(
            image_file.read()
        ).decode("utf-8")

    return (
        "data:image/jpeg;base64,"
        + encoded
    )


client = OpenAI(
    api_key=os.getenv("FIREWORKS_API_KEY"),
    base_url=(
        "https://api.fireworks.ai/"
        "inference/v1"
    ),
)


try:
    response = client.chat.completions.create(
        model=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Describe only what is "
                            "visibly shown in this image. "
                            "Be concise."
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": encode_image(
                                IMAGE_PATH
                            ),
                        },
                    },
                ],
            }
        ],
        max_tokens=200,
        temperature=0.1,
    )

    print("\nSUCCESS\n")

    print(
        response.choices[0].message.content
    )

    print("\nUSAGE\n")

    print(response.usage)


except APIStatusError as error:
    print("\nFIREWORKS ERROR\n")

    print(
        f"Status: {error.status_code}"
    )

    print(
        f"Request ID: "
        f"{getattr(error, 'request_id', None)}"
    )

    raise