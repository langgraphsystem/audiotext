# GPT-5 Powered TikTok Content Intelligence Bot

🧠 **Next-Generation AI-Powered Telegram Bot** that processes TikTok video links and provides professional-grade content analysis using GPT-5.

## 🚀 Advanced GPT-5 Features

- **📝 Smart Subtitle Extraction**: Automatically detects and downloads available captions/subtitles
- **🎵 AI-Enhanced Audio Transcription**: Downloads audio and transcribes with Whisper AI when no captions are available
- **🧠 GPT-5 Professional Analysis**: Advanced multi-level content analysis with:
  - Semantic, emotional, and contextual insights
  - Viral potential assessment and engagement scoring
  - Professional marketing recommendations
  - Ready-to-use social media captions
  - SEO-optimized content suggestions
- **⏱️ Intelligent Timestamped Highlights**: AI-curated key moments with precise timing
- **🔄 GPT-5 Exclusive**: Pure GPT-5 processing without fallbacks
- **📊 Professional Report Generation**: Structured analysis files with GPT-5 branding

## 📋 Requirements

### System Requirements
- **Python 3.11+**
- **FFmpeg** (required for audio processing)
- **Git** (for cloning)

### Python Dependencies
All dependencies are listed in `requirements.txt`:
- `aiogram>=3.0.0` - Telegram Bot API
- `yt-dlp>=2025.01.0` - Video/audio downloader
- `openai>=1.40.0` - OpenAI API client (Whisper STT + Responses API)
- `pydantic>=2.6.0` - Configuration management
- `httpx>=0.27.0` - HTTP client
- `uvloop` - Performance optimization (Linux only)

## 🛠️ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp env.example .env
# Edit .env with your API keys
```

#### Speech-to-Text (STT)
- Используется только облачная расшифровка через OpenAI Whisper API (`whisper-1`).
- Настройка: `STT_LANGUAGE=auto|ru|en|...` — автоопределение или фиксированный язык.

### 3. Test Setup
```bash
python test_setup.py
```

### 4. Run Bot
```bash
python -m app.bot
```

## ☁️ Deploy to Railway

### Option 1: Docker (recommended)
- This repo includes a `Dockerfile` that installs Python deps and FFmpeg.
- Steps:
  1. Push the repo to GitHub.
  2. Create a new Railway project → Deploy from GitHub → select this repo.
  3. Railway will build using the Dockerfile.
  4. Set environment variables in Railway → Variables:
     - `BOT_TOKEN` (Telegram token)
     - `OPENAI_API_KEY`
     - `OPENAI_MODEL` (e.g. `gpt-4o-mini`)
     - `STT_LANGUAGE` (e.g. `auto` or `ru`)
     - Optional for webhook: `WEBHOOK_BASE_URL`, `WEBHOOK_PATH`, `PORT`
  5. Deploy. The bot runs in polling mode by default.

### Option 2: Webhook mode (optional)
- Start with: `python -m app.bot --webhook`
- Configure envs:
  - `WEBHOOK_BASE_URL` (e.g. `https://your-railway-domain.up.railway.app`)
  - `WEBHOOK_PATH` (default `/webhook`)
  - `PORT` (Railway provides automatically; we bind to it)
- Railway will route traffic to the container’s `$PORT`.

Notes:
- Polling does not require inbound networking; simplest to run.
- Webhook mode exposes an HTTP server for Telegram callbacks and supports healthz at `/healthz`.

## 📚 Documentation

- **[🎉 CREATED_PROJECT.md](CREATED_PROJECT.md)** - Complete project overview and success summary
- **[🚀 LAUNCH.md](LAUNCH.md)** - Step-by-step launch instructions
- **[⚡ QUICKSTART.md](QUICKSTART.md)** - Quick setup guide
- **[📋 PROJECT_INFO.md](PROJECT_INFO.md)** - Technical details and architecture
- **[🔧 Makefile](Makefile)** - Build and run commands

## 📱 Usage

### Bot Commands
- `/start` - Show welcome message and instructions
- `/help` - Show detailed help and troubleshooting

### Processing TikTok Videos
1. **Send a TikTok URL** to the bot:
   ```
   https://www.tiktok.com/@username/video/1234567890
   ```

2. **Bot will automatically:**
   - Check for available subtitles/captions
   - Download audio if no captions found
   - Transcribe audio using Whisper AI
   - Analyze content with OpenAI GPT
   - Send back text file and analysis

3. **Output includes:**
   - 📄 Text file (captions or transcript)
   - 📊 AI analysis with:
     - 5-bullet summary
     - Key topics and hashtags
     - Named entities
     - Timestamped highlights

## 🔧 Troubleshooting

### Common Issues

**"FFmpeg not found"**
- Ensure FFmpeg is installed and in your system PATH
- Windows: Add `C:\FFmpeg\bin` to PATH environment variable

**"OpenAI API error"**
- Check your API key is correct
- Ensure you have sufficient credits
- Bot uses exclusive GPT-5 processing for maximum quality

**"Пустой анализ (только шапка в файле)"**
- Убедитесь, что `OPENAI_MODEL` реально доступна вашему аккаунту (рекомендуем `gpt-4o-mini`).
- Увеличьте `OPENAI_MAX_OUTPUT_TOKENS` (например, до 3000).
- В логах проверьте `Output length: ... chars` после ответа API.

**"yt-dlp extraction failed"**
- Video might be private or region-restricted
- TikTok might have updated their API
- Try with a different video

**"OpenAI STT error"**
- Проверьте `OPENAI_API_KEY` и подключение к интернету
- Убедитесь, что формат аудио поддерживается (mp3/mp4/m4a/webm/ogg)

### Performance Notes
- Для быстрой работы используйте короткие ролики и качественный звук.
- Старайтесь избегать фонового шума — это повышает точность STT.

## 📁 Project Structure

```
tiktok_bot/
├── app/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── logger.py          # Logging setup
│   ├── utils.py           # Utility functions
│   ├── yt_dlp_client.py   # Video/audio downloader
│   ├── stt_engine.py      # Speech-to-text engine
│   ├── openai_client.py   # OpenAI API client
│   ├── handlers.py        # Telegram message handlers
│   └── bot.py             # Main bot application
├── data/                  # Temporary files (created automatically)
├── .env                   # Environment configuration
├── env.example           # Example configuration
├── requirements.txt      # Python dependencies
├── Makefile             # Build commands
├── test_setup.py        # Setup verification script
├── README.md            # This file
├── LAUNCH.md            # Launch instructions
├── QUICKSTART.md        # Quick start guide
├── PROJECT_INFO.md      # Project information
├── SUMMARY.md           # Project summary
├── FINAL_README.md      # Complete project overview
└── CREATED_PROJECT.md   # Success summary
```

## 🔒 Legal & Ethical Considerations

### TikTok Terms of Service
⚠️ **IMPORTANT**: This bot interacts with TikTok content. Please ensure compliance with:

- [TikTok Terms of Service](https://www.tiktok.com/legal/terms-of-service)
- [TikTok Community Guidelines](https://www.tiktok.com/community-guidelines)
- Local laws and regulations

**Usage Guidelines:**
- Use only for **personal/research purposes**
- Respect content creators' rights
- Do not use for commercial purposes without permission
- Do not store or redistribute content without consent
- Respect rate limits and be mindful of server load

### Data Privacy
- Bot does not store personal data by default
- Temporary files are automatically cleaned up
- No user data is logged or retained
- Consider implementing data retention policies for production use

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is for educational and personal use. Please ensure compliance with all applicable laws and terms of service.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs for error messages
3. Ensure all dependencies are properly installed
4. Verify your API keys are correct

## 🔗 Useful Links

- [yt-dlp Documentation](https://github.com/yt-dlp/yt-dlp)
- [FFmpeg Installation Guide](https://ffmpeg.org/download.html)
- [Whisper AI Documentation](https://github.com/openai/whisper)
- [faster-whisper Documentation](https://github.com/guillaumekln/faster-whisper)
- [Aiogram Documentation](https://docs.aiogram.dev/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [TikTok Terms of Service](https://www.tiktok.com/legal/terms-of-service)
