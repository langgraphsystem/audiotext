#!/usr/bin/env python3
"""
Test script to verify all dependencies are properly installed.
"""
import sys
import subprocess
from pathlib import Path

def test_import(module_name, package_name=None):
    """Test if a module can be imported."""
    try:
        __import__(module_name)
        print(f"✅ {package_name or module_name}")
        return True
    except ImportError as e:
        print(f"❌ {package_name or module_name}: {e}")
        return False

def test_command(command, description):
    """Test if a command is available."""
    try:
        result = subprocess.run([command, '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ {description}")
            return True
        else:
            print(f"❌ {description}: Command failed")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print(f"❌ {description}: {e}")
        return False

def main():
    """Run all tests."""
    print("🔍 Testing TikTok Bot Setup...\n")
    
    # Test Python version
    python_version = sys.version_info
    if python_version >= (3, 11):
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python {python_version.major}.{python_version.minor}.{python_version.micro} (requires 3.11+)")
        return False
    
    print("\n📦 Testing Python Dependencies:")
    
    # Test required packages
    packages = [
        ('aiogram', 'aiogram'),
        ('yt_dlp', 'yt-dlp'),
        ('openai', 'openai'),
        ('pydantic', 'pydantic'),
        ('pydantic_settings', 'pydantic-settings'),
        ('httpx', 'httpx'),
    ]
    
    all_packages_ok = True
    for module, package in packages:
        if not test_import(module, package):
            all_packages_ok = False
    
    print("\n🛠️ Testing System Dependencies:")
    
    # Test system commands
    commands = [
        ('ffmpeg', 'FFmpeg'),
        ('ffprobe', 'FFprobe'),
    ]
    
    all_commands_ok = True
    for command, description in commands:
        if not test_command(command, description):
            all_commands_ok = False
    
    print("\n📁 Testing Project Structure:")
    
    # Test project files
    required_files = [
        '.env',
        'requirements.txt',
        'app/config.py',
        'app/bot.py',
        'data/',
    ]
    
    all_files_ok = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (missing)")
            all_files_ok = False
    
    print("\n" + "="*50)
    
    if all_packages_ok and all_commands_ok and all_files_ok:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Configure your .env file with API keys")
        print("2. Run: python -m app.bot")
        return True
    else:
        print("❌ Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install missing packages: pip install -r requirements.txt")
        print("- Install FFmpeg: https://ffmpeg.org/download.html")
        print("- Copy env.example to .env and configure it")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

