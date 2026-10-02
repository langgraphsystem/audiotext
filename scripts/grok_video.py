#!/usr/bin/env python3
"""
Generate a video with Grok Imagine (xAI API) from the command line.

This is a tool for Claude (or for you), not part of the bot: content is produced
in the Claude app, and this script is how a finished idea becomes a clip. It is
standalone on purpose — it needs only the xAI key, not the bot's BOT_TOKEN and
OPENAI_API_KEY — so it runs the same on a laptop and in a cloud session.

The key is taken from XAI_API_KEY (environment or .env). In a cloud session it can
instead be stored as a credential of the environment: then there is no key to read
here, the request goes out without Authorization and the environment adds the header
for api.x.ai itself — which also keeps the key out of the session entirely.

    python scripts/grok_video.py "закат над морем, медленный наезд"
    python scripts/grok_video.py "оживи кадр" --image photo.jpg --duration 8
    python scripts/grok_video.py "..." --dry-run        # show the request, spend nothing

The last line of stdout is a JSON object with the path of the saved file.
Generation is billed per second of output, so the defaults are short and cheap.
"""
import argparse
import base64
import json
import mimetypes
import os
import re
import sys
import time
from pathlib import Path
from typing import Optional

import httpx

ROOT = Path(__file__).resolve().parent.parent

DEFAULT_MODEL = "grok-imagine-video-1.5"
MIN_DURATION, MAX_DURATION = 1, 15
RESOLUTIONS = ("480p", "720p", "1080p")
ASPECT_RATIOS = ("16:9", "9:16", "1:1", "4:3", "3:4", "3:2", "2:3")
# Sanity cap on a download; a 15 s clip is a few megabytes
MAX_DOWNLOAD_BYTES = 200 * 1024 * 1024

# Failure codes of a finished job, as documented by xAI
FAILURE_HINTS = {
    "invalid_argument": "запрос отклонён — описание слишком длинное, картинка не подходит "
                        "или сработала модерация",
    "permission_denied": "у ключа нет доступа к генерации видео",
    "failed_precondition": "модель не поддерживает эти настройки",
    "service_unavailable": "сервис перегружен, повторите позже",
    "internal_error": "внутренняя ошибка сервиса, повторите запрос",
}


class GenerationError(Exception):
    """Generation failed; the message is safe to print."""


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def load_api_key() -> Optional[str]:
    """XAI_API_KEY from the environment, falling back to the repo's .env."""
    key = os.environ.get("XAI_API_KEY")
    if key:
        return key.strip()

    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            match = re.match(r"\s*XAI_API_KEY\s*=\s*(.*?)\s*(?:#.*)?$", line)
            if match and match.group(1):
                return match.group(1).strip().strip("'\"")
    return None


def image_to_input(source: str) -> str:
    """A public URL is passed through; a local file becomes a data URL."""
    if source.startswith(("http://", "https://", "data:")):
        return source

    path = Path(source).expanduser()
    if not path.is_file():
        raise GenerationError(f"картинка не найдена: {source}")

    mime = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    if not mime.startswith("image/"):
        raise GenerationError(f"{path.name} не похож на картинку")

    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def build_body(args: argparse.Namespace, image: Optional[str]) -> dict:
    body: dict = {
        "model": args.model,
        "duration": max(MIN_DURATION, min(MAX_DURATION, args.duration)),
        "resolution": args.resolution,
    }
    if args.prompt:
        body["prompt"] = args.prompt
        if args.negative:
            body["prompt"] += f"\n\nAvoid (negative prompt): {args.negative}"

    if image:
        # The clip starts from this picture and keeps its proportions;
        # aspect_ratio would stretch it
        body["image"] = {"url": image}
    else:
        body["aspect_ratio"] = args.aspect_ratio

    if args.no_audio:
        body["generate_audio"] = False

    return body


def api_error(response: httpx.Response) -> GenerationError:
    status = response.status_code
    if status in (401, 403):
        return GenerationError(
            "xAI не принял ключ: проверьте XAI_API_KEY (или credential окружения для api.x.ai) "
            "и доступ к Imagine API"
        )
    if status == 402:
        return GenerationError("на счёте xAI закончились средства")
    if status == 429:
        return GenerationError("xAI ограничил частоту запросов, повторите позже")

    try:
        payload = response.json()
        detail = str(payload.get("error") or payload.get("message") or "")[:300]
    except Exception:
        detail = response.text[:300]
    return GenerationError(f"xAI ответил ошибкой {status}: {detail}".rstrip(": "))


def generate(client: httpx.Client, base_url: str, headers: dict, body: dict,
             timeout: int, poll: float) -> dict:
    """Submit the job and wait for it; returns the finished job's JSON."""
    try:
        response = client.post(f"{base_url}/videos/generations", headers=headers, json=body)
    except httpx.HTTPError as e:
        raise GenerationError(f"не удалось связаться с xAI: {type(e).__name__}") from e

    if response.status_code >= 400:
        raise api_error(response)

    request_id = response.json().get("request_id")
    if not request_id:
        raise GenerationError("xAI не вернул идентификатор задачи")

    log(f"задача {request_id} принята, жду готовности...")
    started = time.monotonic()

    while True:
        time.sleep(poll)
        waited = int(time.monotonic() - started)
        if waited > timeout:
            raise GenerationError(
                f"ролик не успел сгенерироваться за {timeout // 60} мин (задача {request_id})"
            )

        try:
            poll_response = client.get(f"{base_url}/videos/{request_id}", headers=headers)
        except httpx.HTTPError as e:
            # A blip while waiting must not lose a paid job
            log(f"опрос не удался ({type(e).__name__}), повторяю")
            continue

        if poll_response.status_code >= 400:
            raise api_error(poll_response)

        data = poll_response.json()
        status = data.get("status")

        if status == "done":
            video = data.get("video") or {}
            if video.get("respect_moderation") is False:
                raise GenerationError("ролик отфильтрован модерацией xAI")
            if not video.get("url"):
                raise GenerationError("xAI не вернул ссылку на ролик")
            data["request_id"] = request_id
            return data

        if status == "expired":
            raise GenerationError("задача просрочена, повторите запрос")

        if status == "failed":
            code = (data.get("error") or {}).get("code", "")
            raise GenerationError(FAILURE_HINTS.get(code, "сервис не смог сгенерировать ролик"))

        log(f"  генерируется... {waited} с")


def download(url: str, target: Path) -> None:
    """Save the clip. The API key is deliberately not sent: another host serves it."""
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with httpx.Client(timeout=httpx.Timeout(120.0), follow_redirects=True) as client:
            with client.stream("GET", url) as response:
                if response.status_code >= 400:
                    raise GenerationError(f"не удалось скачать ролик (HTTP {response.status_code})")

                size = 0
                with open(target, "wb") as f:
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > MAX_DOWNLOAD_BYTES:
                            raise GenerationError("ролик подозрительно большой, скачивание прервано")
                        f.write(chunk)
    except httpx.HTTPError as e:
        target.unlink(missing_ok=True)
        raise GenerationError(f"не удалось скачать ролик: {type(e).__name__}") from e
    except BaseException:
        # A half-written clip must not pass for a finished one
        target.unlink(missing_ok=True)
        raise


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Генерация видео в Grok Imagine (xAI). Платно: оплата за секунду ролика.",
    )
    parser.add_argument("prompt", nargs="?", default="",
                        help="что должно происходить в ролике (можно пустым, если есть --image)")
    parser.add_argument("--negative", default="",
                        help="чего не должно быть в кадре; у xAI для видео нет отдельного поля "
                             "negative prompt, поэтому уходит отдельным абзацем после промпта")
    parser.add_argument("--image", help="картинка, с которой начинается ролик: файл или https-ссылка")
    parser.add_argument("--duration", type=int, default=5, help="секунд, 1-15 (по умолчанию 5)")
    parser.add_argument("--resolution", choices=RESOLUTIONS, default="480p",
                        help="чем выше, тем дороже и дольше (по умолчанию 480p)")
    parser.add_argument("--aspect-ratio", choices=ASPECT_RATIOS, default="9:16",
                        help="формат при генерации по тексту (по умолчанию 9:16)")
    parser.add_argument("--no-audio", action="store_true", help="ролик без звука")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out", default=str(ROOT / "videos"), help="папка для готовых роликов")
    parser.add_argument("--name", help="имя файла без расширения")
    parser.add_argument("--timeout", type=int, default=600, help="сколько ждать, секунд")
    parser.add_argument("--poll", type=float, default=5.0, help="как часто спрашивать о готовности")
    parser.add_argument("--dry-run", action="store_true",
                        help="показать запрос и ничего не отправлять (денег не тратит)")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)

    if not args.prompt and not args.image:
        log("Нужно описание ролика или --image.")
        return 2

    base_url = os.environ.get("XAI_BASE_URL", "https://api.x.ai/v1").rstrip("/")

    try:
        image = image_to_input(args.image) if args.image else None
        body = build_body(args, image)

        if args.dry_run:
            shown = json.loads(json.dumps(body))
            if "image" in shown and shown["image"]["url"].startswith("data:"):
                shown["image"]["url"] = shown["image"]["url"][:40] + "...(данные картинки)"
            print(json.dumps({"endpoint": f"{base_url}/videos/generations", "body": shown},
                             ensure_ascii=False, indent=2))
            return 0

        key = load_api_key()
        log(f"Grok Imagine: {body['duration']} с, {body['resolution']}"
            f"{', по картинке' if image else ', по тексту'}")

        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        else:
            # Not an error: the environment may inject the header for api.x.ai
            log("XAI_API_KEY не задан — рассчитываю на credential окружения")
        with httpx.Client(timeout=httpx.Timeout(60.0)) as client:
            job = generate(client, base_url, headers, body, args.timeout, args.poll)

        stamp = time.strftime("%Y%m%d-%H%M%S")
        name = re.sub(r"[^\w.-]+", "_", args.name) if args.name else f"grok_{stamp}"
        target = Path(args.out) / f"{name}.mp4"
        download(job["video"]["url"], target)

    except GenerationError as e:
        log(f"Ошибка: {e}")
        return 1

    result = {
        "path": str(target),
        "bytes": target.stat().st_size,
        "duration": job["video"].get("duration"),
        "url": job["video"]["url"],
        "model": job.get("model"),
        "request_id": job["request_id"],
    }
    log(f"Готово: {target}")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
