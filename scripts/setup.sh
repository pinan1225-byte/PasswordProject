#!/bin/bash

set -e

echo "🚀 Setting up Password Manager development environment..."

echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

echo "🔧 Installing pre-commit hooks..."
pre-commit install

echo "📝 Creating .env file if not exists..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file. Please update with your MySQL credentials."
fi

echo "🧪 Running tests..."
pytest tests/unit/ -v

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env with your MySQL credentials"
echo "2. Run 'pwdmgr init' to initialize the vault"
echo "3. Start using the password manager!"