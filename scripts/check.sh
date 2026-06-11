#!/bin/bash

set -e

echo "🔍 Running code quality checks..."

echo "1️⃣ Running Ruff linter..."
ruff check src/ tests/ --fix

echo "2️⃣ Running Black formatter..."
black src/ tests/

echo "3️⃣ Running isort..."
isort src/ tests/

echo "4️⃣ Running MyPy type checker..."
mypy src/

echo "5️⃣ Running tests..."
pytest tests/unit/ -v

echo "✅ All checks passed!"