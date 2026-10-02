#!/usr/bin/env python3
"""
Generate a still image with Grok Imagine (xAI API).

Companion of grok_video.py: same key handling (XAI_API_KEY from the environment or
.env, or a credential of the cloud environment that adds Authorization for api.x.ai).
The image comes back inside the response (base64), so no second host is involved.

    python scripts/grok_image.py "prompt" --negative "text, letters" --out frame.png
"""
import argparse
import base64
import json
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grok_video import GenerationError, api_error, load_api_key, log  # noqa: E402

import os  # noqa: E402

DEFAULT_MODEL = "grok-imagine-image-2.0"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Генерация картинки в Grok Imagine (xAI). Платно.")
    parser.add_argument("prompt")
    parser.add_argument("--negative", default="",
                        help="что исключить; отдельного поля у xAI нет, уходит абзацем после промпта")
    parser.add_argument("--aspect-ratio", default="9:16")
    parser.add_argument("--resolution", choices=("1k", "2k"), default="1k")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out", required=True, help="куда сохранить файл")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    prompt = args.prompt
    if args.negative:
        prompt += f"\n\nAvoid (negative prompt): {args.negative}"

    body = {
        "model": args.model,
        "prompt": prompt,
        "aspect_ratio": args.aspect_ratio,
        "resolution": args.resolution,
        "response_format": "b64_json",
    }
    base_url = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1").rstrip("/")

    if args.dry_run:
        print(json.dumps({"endpoint": f"{base_url}/images/generations", "body": body},
                         ensure_ascii=False, indent=2))
        return 0

    key = load_api_key()
    headers = {"Content-Type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"

    try:
        with httpx.Client(timeout=httpx.Timeout(180.0)) as client:
            response = client.post(f"{base_url}/images/generations", headers=headers, json=body)
        if response.status_code >= 400:
            raise api_error(response)

        data = (response.json().get("data") or [{}])[0]
        if data.get("respect_moderation") is False:
            raise GenerationError("картинка отфильтрована модерацией xAI")
        if not data.get("b64_json"):
            raise GenerationError("xAI не вернул картинку")

        target = Path(args.out)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(base64.b64decode(data["b64_json"]))
    except httpx.HTTPError as e:
        log(f"Ошибка: не удалось связаться с xAI: {type(e).__name__}")
        return 1
    except GenerationError as e:
        log(f"Ошибка: {e}")
        return 1

    print(json.dumps({"path": str(target), "bytes": target.stat().st_size}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
