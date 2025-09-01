"""
OpenAI client for content analysis using GPT-5 via the Responses API.
"""
import asyncio
import os
from typing import Optional, List, Dict, Any

from openai import AsyncOpenAI

from .config import settings
from .logger import get_logger


logger = get_logger(__name__)


class OpenAIClient:
    """Async client that calls OpenAI Responses API with GPT-5 models."""

    def __init__(self):
        self.api_key = settings.openai_api_key
        self.primary_model = settings.openai_model or "gpt-5"
        self.client = AsyncOpenAI(api_key=self.api_key, timeout=90.0)
        # Early visibility into chosen model
        logger.info(f"OpenAI client initialized with model: {self.primary_model}")
        if isinstance(self.primary_model, str) and "gpt-5" in self.primary_model.lower():
            logger.warning("Configured model contains 'gpt-5'. Ensure this model is available in your account.")

    async def analyze_text(self, text: str, segments: Optional[List[Dict[str, Any]]] = None) -> str:
        system_prompt = self._build_system_prompt(segments)
        user_prompt = f"Проанализируй этот контент из TikTok видео:\n\n{text}"

        logger.info(f"Sending prompt to OpenAI API. Prompt length: {len(user_prompt)} chars.")
        logger.debug(f"USER PROMPT (first 100 chars): {user_prompt[:100]}...")

        try:
            max_output_tokens = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "4000"))
        except ValueError:
            max_output_tokens = 4000

        for attempt in range(3):
            try:
                # Primary attempt
                resp = await self.client.responses.create(
                    model=self.primary_model,
                    instructions=system_prompt,
                    input=user_prompt,
                    max_output_tokens=max_output_tokens,
                )
                
                logger.info("Received response from OpenAI API.")
                logger.debug(f"OpenAI Response object: {resp.model_dump_json(indent=2)}")

                content = (resp.output_text or "").strip()
                logger.info(f"Model: {self.primary_model} | Output length: {len(content)} chars")
                if content:
                    logger.info(
                        f"Analysis succeeded via Responses API (max_output_tokens={max_output_tokens})"
                    )
                    return content

                # Empty content fallback with simplified prompt
                logger.warning("Primary analysis returned empty content. Trying simplified prompt.")
                simple_user = f"Суммируй в 5 пунктах на русском:\n\n{text[:4000]}"
                resp2 = await self.client.responses.create(
                    model=self.primary_model,
                    instructions=(
                        "Ты помощник по анализу контента. "
                        "Отвечай исключительно на русском языке, даже если входные данные на другом языке. "
                        "Пиши кратко и по делу."
                    ),
                    input=simple_user,
                    max_output_tokens=max_output_tokens,
                )

                logger.info("Received response from simplified prompt attempt.")
                logger.debug(f"OpenAI Simplified Response object: {resp2.model_dump_json(indent=2)}")

                content2 = (resp2.output_text or "").strip()
                logger.info(f"Model: {self.primary_model} | Simplified output length: {len(content2)} chars")
                if content2:
                    logger.info(
                        f"Analysis succeeded via Responses API (simplified prompt)"
                    )
                    return content2

                # Still empty
                logger.error("Both primary and simplified prompts returned empty content.")
                return "Получен пустой ответ анализа от модели. Попробуйте другой ролик или повторите позже."

            except Exception as e:
                # Retry on transient failures
                if attempt < 2:
                    wait = 2 ** attempt
                    logger.warning(f"OpenAI error: {e}. Retrying in {wait}s...")
                    await asyncio.sleep(wait)
                    continue
                logger.error(f"OpenAI API error after retries: {e}")
                return "❌ Ошибка при анализе текста. Попробуйте позже."

        return "❌ Ошибка при анализе текста после всех попыток."

    def _build_system_prompt(self, segments: Optional[List[Dict[str, Any]]]) -> str:
        """Build the full TikTok analysis system prompt."""
        logger.info("Using full TikTok analysis system prompt.")
        seg_text = "есть" if segments else "нет"
        key_moments_line = (
            "Добавь 5 ключевых моментов с временными метками (формат мм:сс)."
            if segments
            else "Добавь 5 ключевых моментов или абзацев из контента (без таймкодов)."
        )

        prompt = (
            "Ты виртуальный ассистент и эксперт по анализу контента.\n"
            "Отвечай исключительно на русском языке, даже если входные данные на другом языке. "
            "Не используй другие языки в ответе. Весь вывод — на русском.\n"
            "Используй модель GPT-5: думай шаг за шагом, соблюдай структуру, форматируй результат для маркетологов и создателей контента.\n\n"
            "Контекст анализа: транскрипт или сценарий TikTok.\n"
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
            "Перед генерацией ответа: продумай решение внутренне (chain-of-thought), но не раскрывай ход рассуждений — выведи только итоговые секции."
        )

        return prompt

    async def close(self):
        try:
            await self.client.close()
        except Exception:
            pass
