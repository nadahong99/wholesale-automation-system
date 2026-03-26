#!/bin/bash
# scripts/deploy.sh
# Deploy the Wholesale Automation System to an Ubuntu server

set -euo pipefail

echo "=== Wholesale Automation System – Deploy ==="

# 1. Pull latest code
git pull origin main

# 2. Activate virtual environment (or create it)
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# 3. Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Copy environment variables (must pre-exist)
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️  Created .env from .env.example – fill in credentials before running!"
fi

# 5. Initialise database
python scripts/init_db.py

# 6. Start services via Docker Compose
docker-compose up -d --build

echo "=== Deploy complete ==="
docker-compose ps
