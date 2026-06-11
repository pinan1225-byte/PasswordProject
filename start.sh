#!/bin/bash

set -e

echo "🚀 Initializing Password Manager..."
echo ""

cd "$(dirname "$0")"

export PYTHONPATH="$(pwd)/src"

echo "📦 Step 1: Initializing database..."
.venv/bin/python init_db.py

if [ $? -ne 0 ]; then
    echo "❌ Database initialization failed!"
    exit 1
fi

echo ""
echo "🎉 Step 2: Starting application..."
.venv/bin/python run_gui.py