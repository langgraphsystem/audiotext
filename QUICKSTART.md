# 🚀 Quick Start Guide

## Prerequisites
- Python 3.11+
- FFmpeg installed and in PATH
- Telegram Bot Token (from @BotFather)
- OpenAI API Key

## ⚡ Quick Setup (5 minutes)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
# Copy example config
cp env.example .env

# Edit .env with your API keys and options
# BOT_TOKEN=your_telegram_bot_token
# OPENAI_API_KEY=your_openai_api_key

# Speech-to-Text via OpenAI Whisper API
# STT_LANGUAGE=auto   # or ru/en/... to force language
```

### 3. Test Setup
```bash
python test_setup.py
```

### 4. Run Bot
```bash
python -m app.bot
```

## 🎯 Usage

1. **Start bot**: Send `/start` to your bot
2. **Send TikTok URL**: Paste any TikTok video link
3. **Get results**: Bot will return text file + AI analysis

## 🔧 Troubleshooting

**"FFmpeg not found"**
- Windows: Download from https://ffmpeg.org/download.html
- Add `C:\FFmpeg\bin` to PATH

**"OpenAI API error"**
- Check API key in `.env`
- Ensure sufficient credits

**"yt-dlp extraction failed"**
- Try with a different video
- Check if video is public

## 📞 Support

- Check `README.md` for detailed documentation
- Run `python test_setup.py` to diagnose issues
- Ensure all dependencies are installed correctly

