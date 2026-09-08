#!/usr/bin/env python3
"""
Setup check: verifies dependencies, system tools and URL recognition.
"""
import os
import subprocess
import sys
from pathlib import Path

BRAND = os.getenv("BRAND_NAME", "ChatGPT Luna")


def test_import(module_name, package_name=None):
    """Test if a module can be imported."""
    try:
        __import__(module_name)
        print(f"✅ {package_name or module_name}")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name}: {e}")
        return False


def test_command(command, description, required=True):
    """Test if a command is available."""
    try:
        result = subprocess.run([command, '-version'],
                                capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ {description}")
            return True
        print(f"{'❌' if required else '⚠️ '} {description}: command failed")
        return not required
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"{'❌' if required else '⚠️ '} {description}: {e}")
        return not required


def test_url_detection():
    """Check that supported links are recognised for both platforms."""
    # Dummy credentials so that importing settings does not fail on a fresh checkout
    os.environ.setdefault("BOT_TOKEN", "test")
    os.environ.setdefault("OPENAI_API_KEY", "test")

    try:
        from app.utils import detect_platform
    except Exception as e:
        print(f"❌ Не удалось импортировать app.utils: {e}")
        return False

    cases = [
        ("https://www.tiktok.com/@user/video/1234567890", "tiktok"),
        ("https://vt.tiktok.com/ZSabcdef/", "tiktok"),
        ("https://vm.tiktok.com/ZSabcdef/", "tiktok"),
        ("https://www.instagram.com/reel/Cxyz12345/", "instagram"),
        ("https://instagram.com/p/Cxyz12345/", "instagram"),
        ("https://www.instagram.com/tv/Cxyz12345/", "instagram"),
        ("https://youtube.com/watch?v=abc", None),
        ("not a url", None),
    ]

    ok = True
    for url, expected in cases:
        actual = detect_platform(url)
        if actual == expected:
            print(f"✅ {url} → {actual}")
        else:
            print(f"❌ {url} → {actual} (ожидалось {expected})")
            ok = False
    return ok


def main():
    """Run all checks."""
    print(f"🔍 Проверка окружения {BRAND}...\n")

    python_version = sys.version_info
    if python_version >= (3, 11):
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor} (нужен 3.11+)")
        return False

    print("\n📦 Python-зависимости:")
    packages = [
        ('aiogram', 'aiogram'),
        ('yt_dlp', 'yt-dlp'),
        ('openai', 'openai'),
        ('pydantic', 'pydantic'),
        ('pydantic_settings', 'pydantic-settings'),
        ('httpx', 'httpx'),
        ('aiohttp', 'aiohttp'),
    ]
    all_packages_ok = all(test_import(module, package) for module, package in packages)

    print("\n🛠️ Системные зависимости:")
    all_commands_ok = all([
        test_command('ffmpeg', 'FFmpeg (обязателен для длинных видео)'),
        test_command('ffprobe', 'FFprobe (обязателен для длинных видео)'),
    ])

    print("\n📁 Структура проекта:")
    required_files = [
        'requirements.txt',
        'app/config.py',
        'app/bot.py',
        'app/audio.py',
        'app/handlers.py',
    ]
    all_files_ok = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (отсутствует)")
            all_files_ok = False

    if Path('.env').exists():
        print("✅ .env")
    else:
        print("⚠️  .env отсутствует — скопируйте env.example в .env")

    print("\n🔗 Распознавание ссылок:")
    urls_ok = test_url_detection()

    print("\n" + "=" * 50)

    if all_packages_ok and all_commands_ok and all_files_ok and urls_ok:
        print(f"🎉 Все проверки пройдены. {BRAND} готов к запуску.")
        print("\nДальше:")
        print("1. Заполните .env (BOT_TOKEN, OPENAI_API_KEY)")
        print("2. Запустите: python -m app.bot")
        return True

    print("❌ Часть проверок не пройдена.")
    print("\nЧастые решения:")
    print("- Установить зависимости: pip install -r requirements.txt")
    print("- Установить FFmpeg: https://ffmpeg.org/download.html")
    print("- Скопировать env.example в .env и заполнить ключи")
    return False


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
