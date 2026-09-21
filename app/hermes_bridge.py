"""Authenticated, bounded HTTP bridge for the owner's Hermes runtime.

The Telegram polling bot remains the primary application.  This module only
starts when HERMES_BRIDGE_TOKEN is configured; it does not process anything on
startup or on a status request.  A video is processed only by an authenticated
POST with an explicit request id.
"""

import asyncio
import hmac
import re
import uuid
from urllib.parse import urlsplit

from aiohttp import web

from .config import settings
from .logger import get_logger

logger = get_logger(__name__)
TOKEN_KEY = web.AppKey("bridge_token", str)
JOBS_KEY = web.AppKey("bridge_jobs", dict)
ACTIVE_KEY = web.AppKey("bridge_active", list)

_INSTAGRAM_PATH = re.compile(r"^/(?:reel|p|tv)/[A-Za-z0-9_-]+/?$")
_TIKTOK_PATH = re.compile(r"^/@[A-Za-z0-9_.-]+/video/[0-9]+/?$")


def valid_video_url(value: object) -> bool:
    """Accept only direct public-post URLs, not profiles or arbitrary hosts."""
    if not isinstance(value, str) or not 15 <= len(value) <= 500:
        return False
    try:
        parsed = urlsplit(value)
        invalid_authority = parsed.username or parsed.password or parsed.port
    except ValueError:
        return False
    if parsed.scheme != "https" or invalid_authority:
        return False
    if parsed.query or parsed.fragment:
        return False
    host = (parsed.hostname or "").lower()
    if host in {"instagram.com", "www.instagram.com"}:
        return bool(_INSTAGRAM_PATH.fullmatch(parsed.path))
    if host in {"tiktok.com", "www.tiktok.com"}:
        return bool(_TIKTOK_PATH.fullmatch(parsed.path))
    return False


async def process_video(url: str) -> dict:
    """Reuse the bot's pipeline without sending Telegram messages."""
    from .openai_client import OpenAIClient
    from .stt_engine import STTEngine
    from .utils import (
        check_audio_duration, cleanup_temp_files, collect_metadata,
        detect_platform, get_video_info,
    )
    from .video_processor import VideoProcessor
    from .yt_dlp_client import YtDlpClient

    files = []
    client = None
    try:
        info = await asyncio.to_thread(get_video_info, url)
        if not info:
            raise ValueError("Video metadata unavailable")
        if not check_audio_duration(info):
            raise ValueError("Video exceeds the configured duration limit")

        client = OpenAIClient()
        processor = VideoProcessor(YtDlpClient(), STTEngine(), client)
        text = None
        segments = None
        try:
            text, found = await processor.extract_subtitles(url)
            files.extend(found)
        except Exception as exc:
            logger.warning("Bridge subtitles unavailable: %s", type(exc).__name__)
        if not text:
            try:
                text, segments, found = await processor.extract_audio_transcript(url)
                files.extend(found)
            except Exception as exc:
                logger.warning("Bridge transcription unavailable: %s", type(exc).__name__)

        images, found = await processor.collect_visual_context(url, info)
        files.extend(found)
        if not (text and len(text.strip()) >= 10) and not images:
            raise ValueError("No speech or video frames could be extracted")

        platform = detect_platform(url)
        metadata = collect_metadata(info)
        analysis, report_path = await processor.analyze_content(
            text or "", segments, platform=platform, metadata=metadata, images=images,
        )
        if report_path:
            files.append(report_path)
        if (not analysis or not analysis.strip() or
                analysis.lstrip().startswith(("❌", "Получен пустой ответ"))):
            raise RuntimeError("Analysis unavailable")
        return {
            "url": url,
            "platform": platform,
            "model": settings.openai_model,
            "transcript": (text or "").strip(),
            "analysis": analysis.strip(),
            "metadata": metadata,
            "frames": len(images),
        }
    finally:
        cleanup_temp_files(*files)
        if client:
            await client.close()


def _authorized(request: web.Request) -> bool:
    expected = request.app[TOKEN_KEY]
    header = request.headers.get("Authorization", "")
    prefix = "Bearer "
    supplied = header[len(prefix):] if header.startswith(prefix) else ""
    return bool(supplied) and hmac.compare_digest(supplied, expected)


async def _health(_request: web.Request) -> web.Response:
    return web.json_response({"status": "ok"}, headers={"Cache-Control": "no-store"})


async def _status(request: web.Request) -> web.Response:
    if not _authorized(request):
        raise web.HTTPUnauthorized(headers={"Cache-Control": "no-store"})
    return web.json_response({
        "service": "audiotext",
        "bridge": "hermes-v1",
        "model": settings.openai_model,
        "platforms": ["instagram", "tiktok"],
        "processing": "explicit-post-only",
    }, headers={"Cache-Control": "no-store"})


def _job_response(request_id: str, job: dict) -> web.Response:
    body = {"request_id": request_id, "state": job["state"]}
    if job["state"] == "completed":
        body["result"] = job["result"]
    elif job["state"] == "failed":
        body["error"] = job["error"]
    return web.json_response(body, status=202 if job["state"] == "running" else 200,
                             headers={"Cache-Control": "no-store"})


async def _run_job(app: web.Application, request_id: str, url: str) -> None:
    job = app[JOBS_KEY][request_id]
    try:
        job["result"] = await process_video(url)
        job["state"] = "completed"
    except ValueError as exc:
        job["error"] = str(exc)
        job["state"] = "failed"
    except Exception:
        logger.exception("Hermes bridge processing failed")
        job["error"] = "Processing failed; do not retry blindly"
        job["state"] = "failed"
    finally:
        app[ACTIVE_KEY][0] = None


async def _process(request: web.Request) -> web.Response:
    if not _authorized(request):
        raise web.HTTPUnauthorized(headers={"Cache-Control": "no-store"})
    try:
        payload = await request.json()
    except (ValueError, TypeError):
        raise web.HTTPBadRequest(text="Invalid JSON")
    if not isinstance(payload, dict) or not valid_video_url(payload.get("url")):
        raise web.HTTPBadRequest(text="Direct Instagram/TikTok video URL required")
    try:
        request_id = str(uuid.UUID(str(payload.get("request_id", ""))))
    except (ValueError, TypeError, AttributeError):
        raise web.HTTPBadRequest(text="UUID request_id required")
    url = payload["url"]
    jobs = request.app[JOBS_KEY]
    if request_id in jobs:
        if jobs[request_id]["url"] != url:
            raise web.HTTPConflict(text="request_id already used for another URL")
        return _job_response(request_id, jobs[request_id])

    if request.app[ACTIVE_KEY][0] is not None:
        raise web.HTTPTooManyRequests(text="Processing already in progress")
    if len(jobs) >= 128:
        finished = next((key for key, job in jobs.items() if job["state"] != "running"), None)
        if finished is None:
            raise web.HTTPTooManyRequests(text="Bridge job capacity reached")
        jobs.pop(finished)
    jobs[request_id] = {"url": url, "state": "running"}
    request.app[ACTIVE_KEY][0] = asyncio.create_task(_run_job(request.app, request_id, url))
    return _job_response(request_id, jobs[request_id])


async def _get_job(request: web.Request) -> web.Response:
    if not _authorized(request):
        raise web.HTTPUnauthorized(headers={"Cache-Control": "no-store"})
    try:
        request_id = str(uuid.UUID(request.match_info["request_id"]))
    except ValueError:
        raise web.HTTPBadRequest(text="UUID request_id required")
    job = request.app[JOBS_KEY].get(request_id)
    if job is None:
        raise web.HTTPNotFound(text="Job not found; do not resubmit blindly")
    return _job_response(request_id, job)


def register_bridge_routes(app: web.Application) -> bool:
    """Add routes only when a strong bridge token is configured."""
    import os

    token = os.environ.get("HERMES_BRIDGE_TOKEN", "")
    if len(token) < 32:
        return False
    app[TOKEN_KEY] = token
    app[JOBS_KEY] = {}
    app[ACTIVE_KEY] = [None]
    app.router.add_get("/v1/hermes/status", _status)
    app.router.add_post("/v1/hermes/process", _process)
    app.router.add_get("/v1/hermes/jobs/{request_id}", _get_job)
    logger.info("Hermes bridge routes enabled")
    return True


async def start_polling_bridge():
    """Serve the bridge alongside Telegram polling, on Railway's PORT."""
    app = web.Application(client_max_size=4096)
    if not register_bridge_routes(app):
        logger.info("Hermes bridge disabled (token not configured)")
        return None
    app.router.add_get("/healthz", _health)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.webhook_host, port=settings.webhook_port)
    await site.start()
    logger.info("Hermes bridge listening on configured port")
    return runner
