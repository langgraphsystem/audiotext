"""
Instagram feed through Composio.

Instagram does not serve profile listings anonymously, but the official
Graph API does — for accounts you manage. Composio holds that connection,
so the feed is fetched through its REST API and the resulting permalinks
go through the normal download pipeline.
"""
from typing import Any, Dict, List, Optional, Tuple

import httpx

from .config import settings
from .logger import get_logger

logger = get_logger(__name__)

MEDIA_TOOL = "INSTAGRAM_GET_IG_USER_MEDIA"

# Only what the pipeline can actually process and analyze
MEDIA_FIELDS = (
    "id,caption,media_type,media_product_type,permalink,timestamp,username"
)


def _execute_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/tools/execute/{MEDIA_TOOL}"


def _payload(limit: int) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "arguments": {
            "ig_user_id": settings.composio_ig_user_id,
            "limit": limit,
            "fields": MEDIA_FIELDS,
        }
    }
    if settings.composio_connected_account_id:
        payload["connected_account_id"] = settings.composio_connected_account_id
    if settings.composio_user_id:
        payload["user_id"] = settings.composio_user_id
    return payload


def _extract_items(body: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Media rows sit at data.data; the wrapper shape varies by API version."""
    root = body.get("data") if isinstance(body.get("data"), dict) else body
    items = (root or {}).get("data")
    if isinstance(items, list):
        return [i for i in items if isinstance(i, dict)]

    nested = (body.get("response") or {}).get("data") or {}
    items = nested.get("data") if isinstance(nested, dict) else None
    return [i for i in items if isinstance(i, dict)] if isinstance(items, list) else []


def fetch_instagram_media(limit: int) -> Optional[Tuple[List[Dict[str, Any]], str]]:
    """Fetch recent media of the connected Instagram account.

    Returns (media rows, username) or None when the feed could not be read.
    """
    if not settings.composio_api_key:
        logger.error(
            "Источник composio:instagram требует COMPOSIO_API_KEY — "
            "ключ создаётся в дашборде Composio."
        )
        return None

    headers = {
        "x-api-key": settings.composio_api_key,
        "Content-Type": "application/json",
    }
    payload = _payload(limit)

    # The execute path moved between API revisions; try the configured one first
    bases = [settings.composio_base_url]
    if settings.composio_base_url.rstrip("/").endswith("/v3"):
        bases.append(settings.composio_base_url.rstrip("/")[:-3] + "v3.1")

    last_error = ""
    for base in bases:
        url = _execute_url(base)
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as e:
            last_error = f"{type(e).__name__}: {e}"
            logger.warning(f"Composio недоступен ({base}): {last_error}")
            continue

        if response.status_code == 404:
            last_error = f"404 на {url}"
            logger.info(f"Эндпоинт не найден, пробую другую версию API: {url}")
            continue

        if response.status_code >= 400:
            logger.error(
                f"Composio вернул {response.status_code}: {response.text[:300]}"
            )
            return None

        try:
            body = response.json()
        except ValueError as e:
            logger.error(f"Composio вернул не JSON: {e}")
            return None

        if body.get("successful") is False or body.get("error"):
            logger.error(f"Composio сообщил об ошибке: {str(body.get('error'))[:300]}")
            return None

        items = _extract_items(body)
        if not items:
            logger.warning("Composio вернул пустой список публикаций")
            return [], settings.composio_ig_user_id

        username = str(items[0].get("username") or settings.composio_ig_user_id)
        logger.info(f"Composio: получено {len(items)} публикаций аккаунта @{username}")
        return items, username

    logger.error(f"Не удалось обратиться к Composio: {last_error}")
    return None
