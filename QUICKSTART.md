# 🚀 Быстрый старт на своём компьютере — ChatGPT Luna

## Требования
- Python 3.11+
- FFmpeg в `PATH` (обязателен: длинные видео, кадры, проверка аудиодорожки)
- Токен Telegram-бота (@BotFather)
- Ключ OpenAI API

FFmpeg:
- macOS: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt install ffmpeg`
- Windows: https://ffmpeg.org/download.html и добавить `bin` в `PATH`

## Вариант 1. Напрямую (три команды)

```bash
git clone https://github.com/langgraphsystem/audiotext.git
cd audiotext
make setup          # создаст .venv, поставит зависимости, сделает .env
```

Откройте `.env` и заполните два поля:

```env
BOT_TOKEN=123456:ABC...
OPENAI_API_KEY=sk-...
```

Дальше:

```bash
make test           # проверит зависимости, FFmpeg и распознавание ссылок
make run            # запуск бота
```

## Вариант 2. Docker (FFmpeg ставить не нужно)

```bash
make env            # создаст .env из шаблона
# заполните BOT_TOKEN и OPENAI_API_KEY
make docker-up      # сборка и запуск
```

База и временные файлы останутся в `./data` на вашем диске, поэтому собранный
материал переживает перезапуск контейнера. Остановить: `make docker-down`.

## ⚠️ Только одна копия бота одновременно

Telegram не допускает двух потребителей `getUpdates` с одним токеном. Если бот
уже работает на сервере, локальный запуск будет выбивать его ошибкой
`TelegramConflictError` — и наоборот.

Варианты: остановить сервис на сервере на время отладки **или** завести у
@BotFather второго бота для локальной работы и указать его токен в `.env`.

## 🍪 Instagram локально работает лучше

При запуске на своём компьютере yt-dlp умеет брать cookies **прямо из браузера** —
экспортировать ничего не нужно:

```env
COOKIES_FROM_BROWSER=chrome    # или firefox, edge, brave, safari, chromium
```

Это решает главную проблему сервера: лента профиля Instagram требует авторизации,
а домашний IP не режется так, как датацентровый. Если Chrome запущен, файл cookies
может быть заблокирован — тогда закройте браузер перед запуском.

## 📲 Проверка

Отправьте боту ссылку:
- `https://www.tiktok.com/@username/video/1234567890`
- `https://www.instagram.com/reel/Cxxxxxxxxxx/`

Команды сбора: `/sources`, `/scan`, `/digest`.

## 🔧 Полезные команды

```bash
make test        # проверка окружения
make run         # запуск (polling)
make webhook     # запуск в режиме webhook
make lint        # компиляция всех модулей
make clean       # удалить временные медиафайлы
make docker-up   # запуск в Docker
```

## 🔧 Частые настройки

| Нужно | Переменная |
|-------|------------|
| Сменить имя ассистента | `BRAND_NAME` |
| Обрабатывать более длинные ролики | `MAX_AUDIO_DURATION_MINUTES` |
| Уменьшить куски при нестабильной сети | `AUDIO_CHUNK_SECONDS` |
| Взять cookies из браузера | `COOKIES_FROM_BROWSER` |
| Собирать ленту своего Instagram | `COMPOSIO_API_KEY` + `SOURCE_ACCOUNTS=composio:instagram` |
