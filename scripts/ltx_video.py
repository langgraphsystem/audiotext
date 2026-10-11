#!/usr/bin/env python3
"""
Generate a video with LTX-2.5 on our own Runpod Serverless endpoint.

A sibling of grok_video.py for the self-hosted model: same idea (a tool for Claude,
not part of the bot), same output contract (the last stdout line is JSON with the
saved path). The endpoint runs the vavo/LTX2.5-serverless worker (ComfyUI, distilled
INT8); this script fills its image-to-video workflow (ltx25_i2v_workflow.json, taken
from that repo) and sends it with the picture inline, since the worker reads images
only as base64.

The Runpod key is taken from RUNPOD_API_KEY (environment or .env). In a cloud session
it can instead be a credential of the environment for api.runpod.ai: then the request
goes out without Authorization and the environment adds the header itself.

    python scripts/ltx_video.py "slow push-in, smoke drifts" --image frame.png
    python scripts/ltx_video.py "..." --image frame.png --duration 8 --aspect-ratio 9:16
    python scripts/ltx_video.py "..." --image frame.png --dry-run   # spend nothing

Billing is per second of GPU time, including the first cold start that downloads the
models onto the network volume, so the first clip is slow and the rest are fast.
"""
import argparse
import base64
import copy
import json
import mimetypes
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import httpx

ROOT = Path(__file__).resolve().parent.parent
WORKFLOW_PATH = Path(__file__).resolve().parent / "ltx25_i2v_workflow.json"

DEFAULT_ENDPOINT = "ujaztrmgrdjaxi"
FPS = 24
MIN_DURATION, MAX_DURATION = 1, 20
ASPECT_RATIOS = {
    "16:9": (1280, 720),
    "9:16": (720, 1280),
    "1:1": (1024, 1024),
}

# Node ids of the workflow, as used by the worker's own payload builder
PROMPT_NODE = "398:376"
NEGATIVE_NODE = "398:373"
IMAGE_NODE = "395"
DURATION_NODE = "398:362"
WIDTH_NODE = "398:372"
HEIGHT_NODE = "398:360"
FPS_NODE = "398:361"
ENHANCER_NODE = "398:380"
ENHANCER_TOGGLE_NODE = "398:383"
FIRST_FRAME_NODE = "398:357"
SEED_NODES = ("398:338", "398:339")

INPUT_IMAGE_NAME = "source.png"


class GenerationError(Exception):
    """Generation failed; the message is safe to print."""


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def load_api_key() -> Optional[str]:
    """RUNPOD_API_KEY from the environment, falling back to the repo's .env."""
    key = os.environ.get("RUNPOD_API_KEY")
    if key:
        return key.strip()

    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            match = re.match(r"\s*RUNPOD_API_KEY\s*=\s*(.*?)\s*(?:#.*)?$", line)
            if match and match.group(1):
                return match.group(1).strip().strip("'\"")
    return None


def image_to_data_url(source: str) -> str:
    path = Path(source).expanduser()
    if not path.is_file():
        raise GenerationError(f"картинка не найдена: {source}")

    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    if not mime.startswith("image/"):
        raise GenerationError(f"{path.name} не похож на картинку")

    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def build_payload(args: argparse.Namespace, image_data_url: str) -> dict:
    workflow = json.loads(WORKFLOW_PATH.read_text(encoding="utf-8"))
    width, height = ASPECT_RATIOS[args.aspect_ratio]
    rng = random.Random(args.seed) if args.seed is not None else random.SystemRandom()

    workflow[PROMPT_NODE]["inputs"]["value"] = args.prompt
    workflow[IMAGE_NODE]["inputs"]["image"] = INPUT_IMAGE_NAME
    workflow[DURATION_NODE]["inputs"]["value"] = args.duration
    workflow[WIDTH_NODE]["inputs"]["value"] = width
    workflow[HEIGHT_NODE]["inputs"]["value"] = height
    workflow[FPS_NODE]["inputs"]["value"] = FPS
    workflow[FIRST_FRAME_NODE]["inputs"]["strength"] = args.strength

    # The enhancer rewrites the prompt with a small LLM; our prompts are written
    # shot by shot, so by default they go to the model as is
    workflow[ENHANCER_TOGGLE_NODE]["inputs"]["value"] = args.enhance
    workflow[ENHANCER_NODE]["inputs"]["sampling_mode"] = "on" if args.enhance else "off"
    workflow[ENHANCER_NODE]["inputs"]["sampling_mode.seed"] = rng.randrange(1, 10**9)

    if args.negative:
        workflow[NEGATIVE_NODE]["inputs"]["text"] = args.negative

    for node in SEED_NODES:
        workflow[node]["inputs"]["noise_seed"] = rng.randrange(1, 10**15)

    return {
        "input": {
            "workflow": workflow,
            "images": [{"name": INPUT_IMAGE_NAME, "image": image_data_url}],
        }
    }


def api_error(response: httpx.Response) -> GenerationError:
    status = response.status_code
    if status in (401, 403):
        return GenerationError(
            "Runpod не принял ключ: проверьте RUNPOD_API_KEY (или credential окружения "
            "для api.runpod.ai)"
        )
    if status == 404:
        return GenerationError("эндпоинт не найден: проверьте --endpoint")
    if status == 429:
        return GenerationError("Runpod ограничил частоту запросов, повторите позже")
    return GenerationError(f"Runpod ответил ошибкой {status}: {response.text[:300]}")


def generate(client: httpx.Client, base_url: str, headers: dict, payload: dict,
             timeout: int, poll: float) -> tuple[str, dict]:
    """Submit the job and wait for it; returns the job id and the worker's output."""
    try:
        response = client.post(f"{base_url}/run", headers=headers, json=payload)
    except httpx.HTTPError as e:
        raise GenerationError(f"не удалось связаться с Runpod: {type(e).__name__}") from e

    if response.status_code >= 400:
        raise api_error(response)

    job_id = response.json().get("id")
    if not job_id:
        raise GenerationError("Runpod не вернул идентификатор задачи")

    log(f"задача {job_id} принята, жду готовности (первый запуск качает модели)...")
    started = time.monotonic()

    while True:
        time.sleep(poll)
        waited = int(time.monotonic() - started)
        if waited > timeout:
            # The job keeps running and billing on Runpod; leaving it would waste money
            try:
                client.post(f"{base_url}/cancel/{job_id}", headers=headers)
            except httpx.HTTPError:
                pass
            raise GenerationError(
                f"ролик не успел сгенерироваться за {timeout // 60} мин, задача {job_id} отменена"
            )

        try:
            poll_response = client.get(f"{base_url}/status/{job_id}", headers=headers)
        except httpx.HTTPError as e:
            # A blip while waiting must not lose a paid job
            log(f"опрос не удался ({type(e).__name__}), повторяю")
            continue

        if poll_response.status_code >= 400:
            raise api_error(poll_response)

        data = poll_response.json()
        status = data.get("status")

        if status == "COMPLETED":
            output = data.get("output") or {}
            # The worker reports its own failures inside a COMPLETED job
            if output.get("status") == "error":
                raise GenerationError(f"воркер не смог сгенерировать ролик: {output.get('error')}")
            return job_id, output

        if status in ("FAILED", "CANCELLED", "TIMED_OUT"):
            raise GenerationError(f"задача {job_id}: {status} {str(data.get('error', ''))[:300]}")

        log(f"  {status.lower() if status else 'жду'}... {waited} с")


def save_video(output: dict, target: Path, keep_audio: bool) -> None:
    videos = (output.get("output") or {}).get("videos") or []
    if not videos:
        raise GenerationError("воркер не вернул видео")

    video = videos[0]
    if video.get("type") != "base64":
        raise GenerationError(f"неожиданный формат ответа: {video.get('type')}")

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        target.write_bytes(base64.b64decode(video["data"]))
        if not keep_audio:
            strip_audio(target)
    except BaseException:
        # A half-written clip must not pass for a finished one
        target.unlink(missing_ok=True)
        raise


def strip_audio(target: Path) -> None:
    """LTX always generates a soundtrack; drop it without re-encoding the picture."""
    if not shutil.which("ffmpeg"):
        log("ffmpeg не найден — звук оставлен в ролике")
        return

    silent = target.with_suffix(".noaudio.mp4")
    result = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(target), "-an", "-c:v", "copy", str(silent)],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        silent.unlink(missing_ok=True)
        log(f"не удалось убрать звук: {result.stderr.strip()[:200]}")
        return
    silent.replace(target)


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Генерация видео в LTX-2.5 на своём эндпоинте Runpod. "
                    "Платно: оплата за секунды работы GPU.",
    )
    parser.add_argument("prompt", help="что должно происходить в ролике")
    parser.add_argument("--image", required=True, help="картинка, с которой начинается ролик (файл)")
    parser.add_argument("--negative", default="",
                        help="чего не должно быть в кадре; быстрая версия модели работает с CFG=1 "
                             "и негатив почти не учитывает — важное пишите в сам промпт")
    parser.add_argument("--duration", type=int, default=6, help="секунд, 1-20 (по умолчанию 6)")
    parser.add_argument("--aspect-ratio", choices=tuple(ASPECT_RATIOS), default="16:9",
                        help="формат кадра (по умолчанию 16:9, 1280x720)")
    parser.add_argument("--strength", type=float, default=0.7,
                        help="насколько жёстко держать исходный кадр, 0-1 (по умолчанию 0.7, "
                             "как в воркфлоу; выше — меньше уходит от картинки)")
    parser.add_argument("--enhance", action="store_true",
                        help="дать модели переписать промпт (по умолчанию выключено)")
    parser.add_argument("--keep-audio", action="store_true",
                        help="оставить сгенерированный звук (по умолчанию вырезается)")
    parser.add_argument("--seed", type=int, help="зерно для воспроизводимости")
    parser.add_argument("--endpoint", default=os.environ.get("LTX_ENDPOINT_ID", DEFAULT_ENDPOINT),
                        help="id эндпоинта Runpod")
    parser.add_argument("--out", default=str(ROOT / "videos"), help="папка для готовых роликов")
    parser.add_argument("--name", help="имя файла без расширения")
    parser.add_argument("--timeout", type=int, default=1800,
                        help="сколько ждать, секунд (первый запуск качает около 50 ГБ моделей)")
    parser.add_argument("--poll", type=float, default=10.0, help="как часто спрашивать о готовности")
    parser.add_argument("--dry-run", action="store_true",
                        help="показать запрос и ничего не отправлять (денег не тратит)")
    args = parser.parse_args(argv)

    if not MIN_DURATION <= args.duration <= MAX_DURATION:
        parser.error(f"--duration должен быть от {MIN_DURATION} до {MAX_DURATION}")
    if not 0.0 <= args.strength <= 1.0:
        parser.error("--strength должен быть от 0 до 1")
    return args


def main(argv=None) -> int:
    args = parse_args(argv)
    base_url = f"https://api.runpod.ai/v2/{args.endpoint}"

    try:
        payload = build_payload(args, image_to_data_url(args.image))

        if args.dry_run:
            shown = copy.deepcopy(payload)
            shown["input"]["images"][0]["image"] = "...(данные картинки)"
            changed = (PROMPT_NODE, NEGATIVE_NODE, DURATION_NODE, WIDTH_NODE, HEIGHT_NODE,
                       FIRST_FRAME_NODE, ENHANCER_TOGGLE_NODE)
            shown["input"]["workflow"] = {k: shown["input"]["workflow"][k]["inputs"] for k in changed}
            print(json.dumps({"endpoint": f"{base_url}/run", "body": shown},
                             ensure_ascii=False, indent=2))
            return 0

        if args.negative:
            log("внимание: при CFG=1 негатив почти не влияет на результат")

        key = load_api_key()
        log(f"LTX-2.5: {args.duration} с, {args.aspect_ratio}, кадр {args.strength}")

        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        else:
            # Not an error: the environment may inject the header for api.runpod.ai
            log("RUNPOD_API_KEY не задан — рассчитываю на credential окружения")

        with httpx.Client(timeout=httpx.Timeout(120.0)) as client:
            job_id, output = generate(client, base_url, headers, payload, args.timeout, args.poll)

        stamp = time.strftime("%Y%m%d-%H%M%S")
        name = re.sub(r"[^\w.-]+", "_", args.name) if args.name else f"ltx_{stamp}"
        target = Path(args.out) / f"{name}.mp4"
        save_video(output, target, args.keep_audio)

    except GenerationError as e:
        log(f"Ошибка: {e}")
        return 1

    result = {
        "path": str(target),
        "bytes": target.stat().st_size,
        "duration": args.duration,
        "model": "ltx-2.5-distilled-int8",
        "job_id": job_id,
        "render_time_sec": (output.get("metadata") or {}).get("render_time_sec"),
    }
    log(f"Готово: {target}")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
