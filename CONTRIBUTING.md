# Contributing to Password Manager

Thank you for your interest in contributing to this project! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please be considerate of others and follow standard open-source community guidelines.

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Use the bug report template
3. Include:
   - Clear description of the bug
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Environment details (OS, Python version)
   - Logs or screenshots if applicable

### Suggesting Features

1. Check existing issues for similar suggestions
2. Use the feature request template
3. Describe:
   - The feature you'd like
   - Why it would be useful
   - Possible implementation approach

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters
5. Commit your changes
6. Push to your branch
7. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.14+
- MySQL 8.0+
- Git

### Setup Steps

```bash
# Clone your fork
git clone https://github.com/yourusername/password-manager.git
cd password-manager

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Run tests to verify setup
pytest
```

## Coding Standards

### Code Style

- Follow PEP 8 guidelines
- Use Black for formatting (line length: 100)
- Use isort for import sorting
- Use type hints for all functions
- Write docstrings for all public functions

### Example

```python
def calculate_password_strength(password: str) -> PasswordStrength:
    """
    Calculate the strength of a password.
    
    Args:
        password: The password to evaluate.
    
    Returns:
        PasswordStrength enum value indicating strength level.
    
    Example:
        >>> strength = calculate_password_strength("MyP@ssw0rd")
        >>> print(strength.name)
        STRONG
    """
    score = 0
    
    if len(password) >= 8:
        score += 1
    
    return PasswordStrength(score)
```

### Commit Messages

Follow conventional commits:

```
feat: add password strength indicator
fix: resolve encryption key leak
docs: update API documentation
style: format code with black
refactor: simplify password generation logic
test: add unit tests for crypto module
chore: update dependencies
```

### Testing

- Write tests for all new features
- Maintain test coverage above 80%
- Use pytest fixtures for common setup
- Include both unit and integration tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/password_manager

# Run specific test file
pytest tests/unit/test_crypto.py

# Run specific test
pytest tests/unit/test_crypto.py::TestCryptoManager::test_encrypt_decrypt
```

### Code Quality

Before submitting PR:

```bash
# Format code
black src/ tests/
isort src/ tests/

# Run linters
ruff check src/ tests/
mypy src/

# Run all checks
pre-commit run --all-files
```

## Project Structure

```
src/password_manager/
├── core/           # Core business logic
│   ├── crypto.py       # Encryption/decryption
│   ├── password_gen.py # Password generation
│   └── vault.py        # Vault management
├── storage/        # Data persistence
│   ├── database.py     # Database operations
│   └── models.py       # Data models
├── cli/            # Command-line interface
│   └── main.py         # CLI commands
├── config/         # Configuration
│   └── settings.py     # Settings management
└── utils/          # Utilities
    ├── helpers.py      # Helper functions
    └── validators.py   # Validation logic
```

## Security Considerations

When contributing:

- **Never commit secrets** (passwords, API keys, etc.)
- **Review encryption code carefully**
- **Add security tests** for security features
- **Document security implications** of changes
- **Follow secure coding practices**

## Documentation

- Update README.md for user-facing changes
- Update docstrings for API changes
- Add inline comments for complex logic
- Update CHANGELOG.md for notable changes

## Review Process

1. All PRs require at least one approval
2. CI checks must pass
3. Code coverage must not decrease
4. Security-sensitive changes need additional review

## Getting Help

- Open a GitHub Discussion for questions
- Check existing issues and documentation
- Email: support@example.com

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉