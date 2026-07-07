import json

from pathlib import Path


def save_json(
    data,
    output_path: str,
):
    path = Path(output_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


def load_json(
    input_path: str,
):
    path = Path(input_path)

    if not path.exists():
        return None

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)