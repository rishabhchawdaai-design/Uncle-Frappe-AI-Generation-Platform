#!/bin/bash
# Research MCP Stack - Setup Script
set -e
echo "=== Research MCP Stack Setup ==="

# Python venv
echo "[1/5] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

echo "[2/5] Installing Python dependencies..."
pip install beautifulsoup4 httpx aiohttp trafilatura readability-lxml \
    newspaper3k requests-html scrapy playwright selenium httpx \
    trafilatura dateparser

echo "[3/5] Installing Playwright browsers..."
python -m playwright install chromium --with-deps 2>/dev/null || true

echo "[4/5] Environment config..."
cp configs/.env.example .env 2>/dev/null || true

echo "[5/5] Done!"
echo ""
echo "Usage:"
echo "  source venv/bin/activate"
echo "  python main.py health              # Check tool availability"
echo "  python main.py collect <url>       # Collect from a URL"
echo "  python main.py raipur news         # Run Raipur news profile"
echo "  python main.py mcp-list            # List MCP servers"
echo ""
echo "Docker services (optional):"
echo "  docker compose -f docker/docker-compose.yml up -d"
