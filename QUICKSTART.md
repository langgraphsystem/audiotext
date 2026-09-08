# 🚀 Быстрый старт — ChatGPT Luna

## Требования
- Python 3.11+
- FFmpeg в `PATH` (обязательно для длинных видео)
- Токен Telegram-бота (@BotFather)
- Ключ OpenAI API

## ⚡ Установка за 5 минут

### 1. Зависимости
```bash
pip install -r requirements.txt
```

FFmpeg:
- Ubuntu/Debian: `sudo apt install ffmpeg`
- macOS: `brew install ffmpeg`
- Windows: https://ffmpeg.org/download.html

### 2. Конфигурация
```bash
cp env.example .env
```

Минимально нужно заполнить:
```env
BOT_TOKEN=123456:ABC...
OPENAI_API_KEY=sk-...
```

### 3. Проверка
```bash
python test_setup.py
```

### 4. Запуск
```bash
python -m app.bot
```

## 📲 Использование

Отправьте боту ссылку:
- `https://www.tiktok.com/@username/video/1234567890`
- `https://vt.tiktok.com/ZSxxxxxxx/`
- `https://www.instagram.com/reel/Cxxxxxxxxxx/`

Бот пришлёт текст (субтитры или расшифровку) и файл с анализом от ChatGPT Luna.

## 🔧 Полезные настройки

| Нужно | Переменная |
|-------|------------|
| Сменить имя ассистента | `BRAND_NAME` |
| Обрабатывать более длинные ролики | `MAX_AUDIO_DURATION_MINUTES` |
| Уменьшить куски при нестабильной сети | `AUDIO_CHUNK_SECONDS` |
| Открыть закрытый Instagram | `INSTAGRAM_COOKIES_FILE` |
