#!/bin/bash

# Setup script for Class Seat Monitor
# This script automates the setup process for local development

set -e

echo "🚀 Class Seat Monitor - Setup Script"
echo "===================================="
echo

# Check Python version
echo "📌 Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | awk '{print $2}')
echo "✅ Found Python $PYTHON_VERSION"

# Check if Python version is 3.9 or higher
REQUIRED_VERSION="3.9"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "❌ Python 3.9 or higher is required. Current version: $PYTHON_VERSION"
    exit 1
fi

echo

# Create virtual environment
echo "📦 Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping..."
else
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

echo

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"

echo

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1
echo "✅ pip upgraded"

echo

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"

echo

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data logs
echo "✅ Directories created: data/, logs/"

echo

# Copy .env.example to .env if it doesn't exist
if [ -f ".env" ]; then
    echo "⚠️  .env file already exists. Skipping..."
else
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please edit .env and add your Telegram bot token and chat IDs"
fi

echo

# Make main.py executable
chmod +x main.py
echo "✅ Made main.py executable"

echo
echo "=========================================="
echo "✅ Setup completed successfully!"
echo "=========================================="
echo
echo "📋 Next steps:"
echo "1. Edit .env file and add your Telegram bot configuration:"
echo "   - Get bot token from @BotFather on Telegram"
echo "   - Get your chat ID from @userinfobot"
echo
echo "2. Edit config.yaml to configure courses to monitor"
echo
echo "3. Activate virtual environment (if not already active):"
echo "   source venv/bin/activate"
echo
echo "4. Test the setup:"
echo "   python main.py test-telegram"
echo "   python main.py test-scraper"
echo
echo "5. Start monitoring:"
echo "   python main.py start"
echo
echo "📚 For more information, see README.md"
echo
