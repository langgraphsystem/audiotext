# 🚀 Launch Instructions

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] **Python 3.11+** installed
- [ ] **FFmpeg** installed and in PATH
- [ ] **Telegram Bot Token** (from @BotFather)
- [ ] **OpenAI API Key** (from OpenAI Platform)
- [ ] **Git** (for cloning repository)

## 🔧 Step-by-Step Setup

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy example configuration
cp env.example .env

# Edit .env file with your credentials
# Use any text editor: nano, vim, notepad, etc.
```

**Required .env configuration:**
```env
BOT_TOKEN=123456:your-telegram-bot-token-here
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Step 3: Test Setup
```bash
python test_setup.py
```

**Expected output:**
```
🔍 Testing TikTok Bot Setup...

✅ Python 3.11.x
📦 Testing Python Dependencies:
✅ aiogram
✅ yt-dlp
✅ faster-whisper
✅ openai
✅ pydantic
✅ httpx
🛠️ Testing System Dependencies:
✅ FFmpeg
✅ FFprobe
📁 Testing Project Structure:
✅ .env
✅ requirements.txt
✅ app/config.py
✅ app/bot.py
✅ data/

==================================================
🎉 All tests passed! Your setup is ready.
```

### Step 4: Run the Bot
```bash
python -m app.bot
```

**Expected output:**
```
2024-01-XX XX:XX:XX | tiktok_bot | INFO | Starting TikTok Content Analyzer Bot...
2024-01-XX XX:XX:XX | tiktok_bot | INFO | Bot initialized with token: 1234567890...
2024-01-XX XX:XX:XX | tiktok_bot | INFO | OpenAI model: gpt-5 (fallback: gpt-4o)
2024-01-XX XX:XX:XX | tiktok_bot | INFO | STT engine: faster-whisper
2024-01-XX XX:XX:XX | tiktok_bot | INFO | STT model size: small
2024-01-XX XX:XX:XX | tiktok_bot | INFO | Work directory: ./data
2024-01-XX XX:XX:XX | tiktok_bot | INFO | Starting bot in polling mode...
```

## 📱 Using the Bot

### 1. Start the Bot
- Send `/start` to your bot on Telegram
- You'll receive a welcome message with instructions

### 2. Send TikTok URL
- Copy any TikTok video URL
- Paste it in the chat with your bot
- Example: `https://www.tiktok.com/@username/video/1234567890`

### 3. Wait for Processing
The bot will show progress messages:
```
🔄 Processing TikTok video...
📝 Checking for subtitles...
✅ Found subtitles! Converting to text...
📄 Sending text file...
🤖 Analyzing content with AI...
📊 Analysis complete!
```

### 4. Receive Results
You'll get:
- 📄 **Text file** with extracted content
- 📊 **AI analysis** with summary, topics, and highlights

## 🔧 Troubleshooting

### Common Issues & Solutions

**❌ "FFmpeg not found"**
```bash
# Windows: Download from https://ffmpeg.org/download.html
# Add C:\FFmpeg\bin to PATH

# macOS:
brew install ffmpeg

# Linux:
sudo apt install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg  # CentOS/RHEL
```

**❌ "OpenAI API error"**
- Check API key in `.env` file
- Ensure sufficient credits in OpenAI account
- Bot will automatically fallback to GPT-4o

**❌ "yt-dlp extraction failed"**
- Try with a different TikTok video
- Ensure video is public and accessible
- Check internet connection

**❌ "Whisper model not found"**
- Models download automatically on first use
- Check internet connection
- Ensure sufficient disk space

### Using Makefile Commands

```bash
make install    # Install dependencies
make env        # Copy env.example to .env
make test       # Run setup tests
make run        # Start the bot
make clean      # Clean temporary files
```

## 🎯 Quick Commands Reference

### Development
```bash
# Install and setup
pip install -r requirements.txt
cp env.example .env
# Edit .env with your API keys

# Test and run
python test_setup.py
python -m app.bot
```

### Production
```bash
# Webhook mode (for production servers)
python -m app.bot --webhook
```

### Maintenance
```bash
# Clean temporary files
make clean

# Update dependencies
pip install -r requirements.txt --upgrade

# Check logs
# Bot logs are displayed in console
```

## 📞 Getting Help

1. **Check logs** - Bot shows detailed logs in console
2. **Run tests** - `python test_setup.py` for diagnostics
3. **Read docs** - Check README.md for detailed information
4. **Common issues** - See troubleshooting section above

## 🎉 Success Indicators

Your bot is working correctly when:
- ✅ Bot starts without errors
- ✅ `/start` command responds
- ✅ TikTok URLs are processed
- ✅ Text files are sent
- ✅ AI analysis is provided
- ✅ No error messages in logs

---

**Happy botting! 🤖✨**

