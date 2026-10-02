"""
Video generation with Grok Imagine (xAI API).

The API is asynchronous: a request returns an id, which is polled until the
clip is ready. The result is a temporary URL, so the file is downloaded right
away and sent to Telegram from disk.
"""
import asyncio
import re
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Deque, Optional

import httpx

from .config import settings
from .logger import get_logger

logger = get_logger(__name__)

# Telegram bots cannot upload files larger than this
MAX_UPLOAD_BYTES = 50 * 1024 * 1024

MIN_DURATION = 1
MAX_DURATION = 15
RESOLUTIONS = ("480p", "720p", "1080p")

# Error codes of a failed job, as documented by xAI
FAILURE_HINTS = {
    "invalid_argument": "Запрос отклонён: проверьте описание — оно могло быть слишком длинным "
                        "или не пройти модерацию.",
    "permission_denied": "У ключа нет доступа к генерации видео.",
    "failed_precondition": "Выбранная модель не поддерживает эти настройки.",
    "service_unavailable": "Сервис генерации перегружен. Повторите позже.",
    "internal_error": "Внутренняя ошибка сервиса генерации. Повторите запрос.",
}

_recent_requests: Deque[float] = deque()


class VideoGenerationError(Exception):
    """Generation failed; the message is safe to show to the user."""


@dataclass
class GeneratedVideo:
    url: str
    duration: Optional[float]
    model: Optional[str]


def is_configured() -> bool:
    return bool(settings.xai_api_key)


def clamp_duration(seconds: Optional[int] = None) -> int:
    value = settings.xai_video_duration if seconds is None else seconds
    return max(MIN_DURATION, min(MAX_DURATION, int(value)))


def check_rate_limit() -> Optional[str]:
    """Return a refusal text when the hourly budget of clips is spent.

    Every clip costs money, so this is separate from (and stricter than) the
    limits on link analysis. Only an accepted request is counted.
    """
    now = time.time()
    while _recent_requests and now - _recent_requests[0] > 3600:
        _recent_requests.popleft()

    if len(_recent_requests) >= settings.xai_video_max_per_hour:
        return (
            f"Лимит генерации — не больше {settings.xai_video_max_per_hour} роликов в час. "
            "Попробуйте позже."
        )

    _recent_requests.append(now)
    return None


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.xai_api_key}",
        "Content-Type": "application/json",
    }


def _build_body(prompt: str, image_data_url: Optional[str], duration: int) -> dict:
    body: dict = {
        "model": settings.xai_video_model,
        "duration": duration,
        "resolution": settings.xai_video_resolution
        if settings.xai_video_resolution in RESOLUTIONS else "480p",
    }
    if prompt:
        body["prompt"] = prompt

    if image_data_url:
        # The clip starts from this picture and keeps its aspect ratio;
        # setting aspect_ratio here would stretch the image
        body["image"] = {"url": image_data_url}
    else:
        body["aspect_ratio"] = settings.xai_video_aspect_ratio

    if not settings.xai_video_audio:
        body["generate_audio"] = False

    return body


def _api_error(response: httpx.Response) -> VideoGenerationError:
    """Turn an HTTP error into a message that does not leak anything sensitive."""
    status = response.status_code
    if status in (401, 403):
        return VideoGenerationError("xAI не принял ключ: проверьте `XAI_API_KEY` и доступ к Imagine API.")
    if status == 402:
        return VideoGenerationError("На счёте xAI закончились средства.")
    if status == 429:
        return VideoGenerationError("xAI ограничил частоту запросов. Повторите позже.")

    detail = ""
    try:
        payload = response.json()
        detail = str(payload.get("error") or payload.get("message") or "")[:200]
    except Exception:
        detail = response.text[:200]

    logger.warning(f"xAI вернул HTTP {status}: {detail}")
    suffix = f": {detail}" if detail else ""
    return VideoGenerationError(f"xAI ответил ошибкой {status}{suffix}")


async def generate_video(
    prompt: str,
    image_data_url: Optional[str] = None,
    duration: Optional[int] = None,
    progress=None,
) -> GeneratedVideo:
    """Generate a clip from text, optionally starting from a picture.

    Args:
        prompt: What should happen in the clip. May be empty with an image.
        image_data_url: Starting frame as a data URL (image-to-video).
        duration: Seconds, clamped to the API range.
        progress: Optional async callback receiving the elapsed seconds.
    """
    if not is_configured():
        raise VideoGenerationError("Не задан `XAI_API_KEY`.")
    if not prompt and not image_data_url:
        raise VideoGenerationError("Нужно описание ролика или картинка.")

    seconds = clamp_duration(duration)
    base = settings.xai_base_url.rstrip("/")
    deadline = time.monotonic() + settings.xai_video_timeout_seconds
    started = time.monotonic()

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
        try:
            response = await client.post(
                f"{base}/videos/generations",
                headers=_headers(),
                json=_build_body(prompt, image_data_url, seconds),
            )
        except httpx.HTTPError as e:
            raise VideoGenerationError(f"Не удалось связаться с xAI: {type(e).__name__}") from e

        if response.status_code >= 400:
            raise _api_error(response)

        request_id = response.json().get("request_id")
        if not request_id:
            raise VideoGenerationError("xAI не вернул идентификатор задачи.")

        logger.info(f"Grok Imagine: задача {request_id} принята ({seconds} с)")

        while True:
            await asyncio.sleep(settings.xai_video_poll_seconds)

            if time.monotonic() > deadline:
                raise VideoGenerationError(
                    f"Ролик не успел сгенерироваться за {settings.xai_video_timeout_seconds // 60} мин."
                )

            try:
                poll = await client.get(f"{base}/videos/{request_id}", headers=_headers())
            except httpx.HTTPError as e:
                # A network blip while waiting is not a reason to lose a paid job
                logger.warning(f"Опрос задачи {request_id} не удался: {type(e).__name__}")
                continue

            if poll.status_code >= 400:
                raise _api_error(poll)

            data = poll.json()
            status = data.get("status")

            if status == "done":
                video = data.get("video") or {}
                if video.get("respect_moderation") is False:
                    raise VideoGenerationError("Ролик отфильтрован модерацией xAI.")
                if not video.get("url"):
                    raise VideoGenerationError("xAI не вернул ссылку на ролик.")
                logger.info(
                    f"Grok Imagine: задача {request_id} готова за {time.monotonic() - started:.0f} с"
                )
                return GeneratedVideo(
                    url=video["url"], duration=video.get("duration"), model=data.get("model"),
                )

            if status == "expired":
                raise VideoGenerationError("Задача на генерацию просрочена. Повторите запрос.")

            if status == "failed":
                error = data.get("error") or {}
                code = error.get("code", "")
                logger.warning(f"Grok Imagine: задача {request_id} не удалась: {code}")
                raise VideoGenerationError(
                    FAILURE_HINTS.get(code, "Сервис не смог сгенерировать ролик.")
                )

            if progress:
                await progress(int(time.monotonic() - started))


async def download_video(video: GeneratedVideo) -> Path:
    """Download the generated clip into WORKDIR and return its path.

    The API key is deliberately not sent: the file lives on a different host.
    """
    settings.workdir.mkdir(parents=True, exist_ok=True)
    stem = re.sub(r"[^A-Za-z0-9]+", "", video.url.split("?")[0].rsplit("/", 2)[-2])[:24] or "clip"
    target = settings.workdir / f"grok_{stem}_{int(time.time())}.mp4"

    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0), follow_redirects=True) as client:
            async with client.stream("GET", video.url) as response:
                if response.status_code >= 400:
                    raise VideoGenerationError(f"Не удалось скачать ролик (HTTP {response.status_code}).")

                size = 0
                with open(target, "wb") as f:
                    async for chunk in response.aiter_bytes():
                        size += len(chunk)
                        if size > MAX_UPLOAD_BYTES:
                            raise VideoGenerationError(
                                "Ролик больше 50 МБ — Telegram не принимает такие файлы от ботов. "
                                "Уменьшите длительность или разрешение."
                            )
                        f.write(chunk)
    except httpx.HTTPError as e:
        target.unlink(missing_ok=True)
        raise VideoGenerationError(f"Не удалось скачать ролик: {type(e).__name__}") from e
    except BaseException:
        # Includes cancellation: a half-written clip must not stay on the disk
        target.unlink(missing_ok=True)
        raise

    return target
