# 🚀 Инструкция по запуску — ChatGPT Luna

## 📋 Чеклист перед стартом

- [ ] **Python 3.11+**
- [ ] **FFmpeg** установлен и доступен в `PATH`
- [ ] **Токен Telegram-бота** (от @BotFather)
- [ ] **Ключ OpenAI API**
- [ ] **Git** (для клонирования репозитория)

## 🔧 Пошаговая настройка

### Шаг 1. Зависимости Python
```bash
pip install -r requirements.txt
```

### Шаг 2. Конфигурация
```bash
cp env.example .env
```

Минимально необходимые поля:
```env
BOT_TOKEN=123456:your-telegram-bot-token-here
OPENAI_API_KEY=sk-your-openai-api-key-here
```

Дополнительно можно задать имя ассистента (`BRAND_NAME`), модель (`OPENAI_MODEL`),
лимиты и cookies для Instagram — см. `env.example`.

### Шаг 3. Проверка окружения
```bash
python test_setup.py
```

Ожидаемый вывод:
```
🔍 Проверка окружения ChatGPT Luna...

✅ Python 3.11.x

📦 Python-зависимости:
✅ aiogram
✅ yt-dlp
✅ openai
✅ pydantic
✅ pydantic-settings
✅ httpx
✅ aiohttp

🛠️ Системные зависимости:
✅ FFmpeg (обязателен для длинных видео)
✅ FFprobe (обязателен для длинных видео)

📁 Структура проекта:
✅ requirements.txt
✅ app/config.py
✅ app/bot.py
✅ app/audio.py
✅ app/handlers.py
✅ .env

🔗 Распознавание ссылок:
✅ https://www.tiktok.com/@user/video/1234567890 → tiktok
✅ https://www.instagram.com/reel/Cxyz12345/ → instagram
...

==================================================
🎉 Все проверки пройдены. ChatGPT Luna готов к запуску.
```

### Шаг 4. Запуск
```bash
python -m app.bot
```

Ожидаемый вывод:
```
| INFO | 🌙 ChatGPT Luna · анализатор видеоконтента запущен
| INFO | 🧠 Модель ИИ: Luna (backend: gpt-5.6-luna)
| INFO | 🎤 Распознавание речи: OpenAI Audio API (whisper-1)
| INFO | 🌐 Платформы: TikTok, Instagram
| INFO | 🎬 FFmpeg найден: длинные видео будут разбиваться на части
| INFO | Starting bot in polling mode...
```

## 📱 Работа с ботом

1. Отправьте `/start` — придёт приветствие и список возможностей.
2. Вставьте ссылку на TikTok или Instagram видео.
3. Бот покажет прогресс одним обновляющимся сообщением:
   ```
   🔄 Обрабатываю видео из Instagram...
   📝 Проверяю субтитры...
   🎵 Субтитров нет. Скачиваю аудиодорожку...
   🎤 Расшифровываю аудио: часть 2 из 5...
   🧠 ChatGPT Luna анализирует контент...
   🎉 Анализ завершён!
   ```
4. В ответ придут: 📄 файл с текстом и 📊 файл с анализом.

## 🔧 Устранение неполадок

**❌ «FFmpeg не найден»**
```bash
# Ubuntu/Debian
sudo apt install ffmpeg
# macOS
brew install ffmpeg
# Windows: https://ffmpeg.org/download.html и добавить bin в PATH
```

**❌ Instagram: «Не удалось получить данные видео»**
- Запись приватная или требует входа — экспортируйте cookies в формате Netscape
  и укажите путь в `INSTAGRAM_COOKIES_FILE`.
- Проверьте, что ссылка ведёт на конкретный пост/reel, а не на профиль.

**❌ Ошибка загрузки в OpenAI Audio API**
- Лимит одной загрузки — 25 МБ. Уменьшите `MAX_UPLOAD_SIZE_MB` (по умолчанию 24)
  или `AUDIO_CHUNK_SECONDS`, чтобы куски были меньше.

**❌ Пустая расшифровка**
- В ролике может не быть разговорной речи (только музыка или шум).

**❌ Ошибка OpenAI API**
- Проверьте ключ в `.env` и наличие средств на аккаунте.
- Проверьте, что модель из `OPENAI_MODEL` доступна вашему аккаунту.

### Команды Makefile

```bash
make install    # установка зависимостей
make env        # копирование env.example в .env
make test       # проверка окружения
make run        # запуск бота
make clean      # удаление временных файлов
```

## 🏭 Продакшн

```bash
# Режим webhook
WEBHOOK_BASE_URL=https://your-domain.com python -m app.bot --webhook

# Docker (FFmpeg уже внутри образа)
docker build -t chatgpt-luna .
docker run --env-file .env chatgpt-luna
```

### Railway

Сборка идёт по `Dockerfile` (см. `railway.toml`) — FFmpeg уже внутри образа.
В Variables достаточно `BOT_TOKEN` и `OPENAI_API_KEY`; `PORT` и
`RAILWAY_PUBLIC_DOMAIN` платформа подставляет сама.

- По умолчанию — polling, одна реплика (`numReplicas = 1`): Telegram не
  допускает двух потребителей `getUpdates`.
- Webhook включается переменной `USE_WEBHOOK=true`; адрес соберётся из
  домена сервиса. Дополнительно стоит задать `WEBHOOK_SECRET` и добавить
  `healthcheckPath = "/healthz"` в `railway.toml`.
- При редеплое приходит `SIGTERM` — бот корректно завершает работу, а при
  старте чистит рабочую директорию.

Подробнее — раздел «Деплой на Railway» в `README.md`.

## 🎉 Признаки корректной работы

- ✅ Бот стартует без ошибок и пишет `FFmpeg найден`
- ✅ `/start` отвечает приветствием ChatGPT Luna
- ✅ Ссылки TikTok и Instagram обрабатываются
- ✅ Длинное видео режется на части (видно в прогрессе и логах)
- ✅ Приходят файл с текстом и файл с анализом
