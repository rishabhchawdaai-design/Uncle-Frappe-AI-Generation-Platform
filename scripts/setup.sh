#!/bin/bash
# Uncle Frappe AI Generation Platform — Setup Script
set -e

echo "=== Uncle Frappe AI Generation Platform Setup ==="

# Python venv
echo "[1/4] Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

echo "[2/4] Installing runtime and test dependencies..."
pip install -r requirements.txt pytest pytest-asyncio

echo "[3/4] Environment config..."
if [ ! -f .env ]; then
    cp configs/.env.example .env
    echo "    Created .env from configs/.env.example (fill in your API keys)"
fi

echo "[4/4] Verifying the platform..."
PYTHONPATH=. python -c "
import importlib, pkgutil, ai_generation
count = sum(1 for _ in pkgutil.iter_modules(ai_generation.__path__))
print(f'    All {count} modules import cleanly')
"
PYTHONPATH=. pytest ai_generation/tests/ -q

echo ""
echo "Optional local backends (keyless, CPU — embeddings, TTS, STT, translation,"
echo "upscaling, background removal, OCR, documents):"
echo "  bash scripts/install-optional.sh              # all groups"
echo "  bash scripts/install-optional.sh --group embeddings   # one group"
echo "  Verify:      python -m ai_generation.cli local-backends"
echo ""
echo "Optional Kimi K3 (Moonshot AI):"
echo "  - Cloud API:   add MOONSHOT_API_KEY to .env (platform.kimi.ai)"
echo "  - Self-hosted: set KIMI_K3_VLLM_URL / KIMI_K3_SGLANG_URL in .env"
echo "  - Verify:      python -m ai_generation.cli kimi-info"
echo ""
echo "=== Setup complete ==="
echo ""
echo "Usage:"
echo "  source venv/bin/activate"
echo "  python -m ai_generation.cli --help    # CLI"
echo "  python -m ai_generation.cli stats     # Platform stats"
echo "  python -m ai_generation.cli quality-report [file]  # Quality dashboard"
