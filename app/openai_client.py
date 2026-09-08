"""
OpenAI client for content analysis, exposed to users as ChatGPT Luna.
"""
import asyncio
from typing import Optional, List, Dict, Any

from openai import AsyncOpenAI

from .config import settings
from .logger import get_logger
from .utils import platform_title


logger = get_logger(__name__)

# Markers of "this key cannot use this model" in provider error messages
_MODEL_UNAVAILABLE_MARKERS = (
    "model_not_found",
    "does not exist",
    "do not have access",
    "not have access",
    "unknown model",
    "invalid model",
    "unsupported model",
    "model is not supported",
)


def _is_model_unavailable(error: Exception) -> bool:
    """Whether the error means the model itself is unusable for this key."""
    text = str(error).lower()
    return any(marker in text for marker in _MODEL_UNAVAILABLE_MARKERS)


class OpenAIClient:
    """Async client that calls the OpenAI Responses API."""

    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url
        self.brand = settings.brand_name
        self.model_name = settings.model_display_name

        # Configured model first, then the fallbacks, without duplicates
        self._candidates: List[str] = []
        for candidate in [settings.openai_model, *settings.fallback_models]:
            if candidate and candidate not in self._candidates:
                self._candidates.append(candidate)
        self.model = self._candidates[0]

        client_kwargs: Dict[str, Any] = {"api_key": self.api_key, "timeout": 180.0}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        self.client = AsyncOpenAI(**client_kwargs)

        logger.info(
            f"{self.brand} client initialized | модель ИИ: {self.model_name} "
            f"| backend: {self.model} | endpoint: {self.base_url or 'api.openai.com'}"
        )
        if len(self._candidates) > 1:
            logger.info(f"Fallback models: {', '.join(self._candidates[1:])}")

    def _request_kwargs(self, instructions: str, user_input: str) -> Dict[str, Any]:
        """Build Responses API kwargs, including reasoning/verbosity controls."""
        max_output_tokens = settings.openai_max_output_tokens or settings.openai_max_tokens

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "instructions": instructions,
            "input": user_input,
            "max_output_tokens": max_output_tokens,
        }

        effort = (settings.openai_reasoning_effort or "").strip().lower()
        if effort and effort != "none":
            kwargs["reasoning"] = {"effort": effort}

        verbosity = (settings.openai_verbosity or "").strip().lower()
        if verbosity:
            kwargs["text"] = {"verbosity": verbosity}

        return kwargs

    async def _call_model(self, model: str, instructions: str, user_input: str) -> str:
        """One Responses API call, retrying without optional controls if needed."""
        kwargs = self._request_kwargs(instructions, user_input)
        kwargs["model"] = model

        try:
            resp = await self.client.responses.create(**kwargs)
        except Exception as e:
            # Older models reject reasoning/verbosity: retry with a plain call.
            if not _is_model_unavailable(e) and ("reasoning" in kwargs or "text" in kwargs):
                logger.warning(f"Retrying without reasoning/verbosity controls: {e}")
                kwargs.pop("reasoning", None)
                kwargs.pop("text", None)
                resp = await self.client.responses.create(**kwargs)
            else:
                raise

        return (resp.output_text or "").strip()

    async def _create_response(self, instructions: str, user_input: str) -> str:
        """Call the model, switching to a fallback if it is unavailable."""
        start = self._candidates.index(self.model) if self.model in self._candidates else 0

        last_error: Optional[Exception] = None
        for model in self._candidates[start:]:
            try:
                content = await self._call_model(model, instructions, user_input)
            except Exception as e:
                if _is_model_unavailable(e):
                    logger.warning(f"Модель {model} недоступна для этого ключа: {e}")
                    last_error = e
                    continue
                raise

            if model != self.model:
                logger.warning(f"Переключился на резервную модель: {model}")
                self.model = model
            return content

        raise RuntimeError(
            "Ни одна из моделей не доступна для этого ключа: "
            f"{', '.join(self._candidates)}"
        ) from last_error

    async def analyze_text(
        self,
        text: str,
        segments: Optional[List[Dict[str, Any]]] = None,
        platform: Optional[str] = None,
    ) -> str:
        """Analyze a transcript and return a structured report."""
        source = platform_title(platform)
        system_prompt = self._build_system_prompt(segments, source)
        user_prompt = f"Проанализируй этот контент из видео ({source}):\n\n{text}"

        logger.info(f"Sending prompt to {self.brand}. Prompt length: {len(user_prompt)} chars.")

        for attempt in range(3):
            try:
                content = await self._create_response(system_prompt, user_prompt)
                logger.info(f"Model: {self.model} | Output length: {len(content)} chars")
                if content:
                    return content

                # Empty content fallback with a simplified prompt
                logger.warning("Analysis returned empty content. Trying simplified prompt.")
                content = await self._create_response(
                    (
                        f"Ты — модель ИИ {self.model_name} в составе {self.brand}, "
                        "ассистент по анализу контента. "
                        "Отвечай исключительно на русском языке, даже если входные данные "
                        "на другом языке. Пиши кратко и по делу."
                    ),
                    f"Суммируй в 5 пунктах на русском:\n\n{text[:4000]}",
                )
                if content:
                    logger.info("Analysis succeeded via simplified prompt")
                    return content

                logger.error("Both primary and simplified prompts returned empty content.")
                return (
                    "Получен пустой ответ анализа. Попробуйте другой ролик или повторите позже."
                )

            except Exception as e:
                if attempt < 2:
                    wait = 2 ** attempt
                    logger.warning(f"{self.brand} error: {e}. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                logger.error(f"{self.brand} API error after retries: {e}")
                return "❌ Ошибка при анализе текста. Попробуйте позже."

        return "❌ Ошибка при анализе текста после всех попыток."

    def _build_system_prompt(self, segments: Optional[List[Dict[str, Any]]], source: str) -> str:
        """Build the full analysis system prompt."""
        logger.info(f"Using full {source} analysis system prompt.")
        seg_text = "есть" if segments else "нет"
        key_moments_line = (
            "Добавь 5 ключевых моментов с временными метками (формат мм:сс)."
            if segments
            else "Добавь 5 ключевых моментов или абзацев из контента (без таймкодов)."
        )

        prompt = (
            f"Ты — модель ИИ {self.model_name}, ассистент {self.brand} "
            "и эксперт по анализу видеоконтента.\n"
            f"Если спрашивают, какая модель отвечает, называй себя: {self.model_name}.\n"
            "Отвечай исключительно на русском языке, даже если входные данные на другом языке. "
            "Не используй другие языки в ответе. Весь вывод — на русском.\n"
            "Думай шаг за шагом, соблюдай структуру, форматируй результат для маркетологов "
            "и создателей контента.\n\n"
            f"Контекст анализа: транскрипт или сценарий видео из {source}.\n"
            f"Дополнительные сегменты: {seg_text}.\n\n"
            "Сгенерируй ответ строго по разделам:\n"
            "1. РЕЗЮМЕ (5–6 предложений)\n"
            "   • В конце резюме отдельным подпунктом выведи блок ‘Имена и организации’:\n"
            "     - Люди, организации, места (если упоминаются), в виде маркеров.\n"
            "   • Добавь мини-блок ‘Краткое содержание’: 5 пунктов, суммирующих основной контент.\n\n"
            "2. ЧЕКЛИСТ (до 6 шагов, каждый с эмодзи в начале)\n"
            f"   • {key_moments_line}\n\n"
            "3. ПРОБЛЕМА · РЕШЕНИЕ · ВЫГОДА\n"
            "   • По 1–2 предложения на каждый элемент.\n\n"
            "4. СОЦИАЛЬНЫЙ КЭПШН\n"
            "   • До 3 предложений для TikTok/Instagram, с эмодзи и CTA.\n\n"
            "5. ИНСАЙТЫ + ХЭШТЕГИ\n"
            "   • 3 инсайта.\n"
            "   • 8–10 хэштегов (добавь также до 10 релевантных тем/тегов из контента).\n\n"
            "6. МИНИ-СТАТЬЯ (~150–200 слов) с подзаголовками\n"
            "   • Сделай 2–3 подзаголовка и логичную структуру.\n\n"
            "7. JSON-вывод (пример):\n"
            "   {\n"
            "     \"title\": \"...\",\n"
            "     \"problem\": \"...\",\n"
            "     \"solution\": \"...\",\n"
            "     \"benefits\": [\"...\", \"...\"],\n"
            "     \"cta\": \"\"\n"
            "   }\n\n"
            "Дополнительные требования:\n"
            " • Не копируй дословно — перефразируй своими словами, будь ёмким и полезным.\n"
            " • Будь краток, точен и сосредоточься на самых важных аспектах контента.\n"
            " • Пиши весь ответ на русском языке (включая возможные заголовки/ярлыки).\n"
            " • В конце напиши: ‘Структура соблюдена, формат понятен, все разделы выведены’.\n\n"
            "Перед генерацией ответа: продумай решение внутренне, но не раскрывай ход "
            "рассуждений — выведи только итоговые секции."
        )

        return prompt

    async def close(self):
        try:
            await self.client.close()
        except Exception:
            pass
