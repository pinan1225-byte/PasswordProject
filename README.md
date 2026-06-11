# Password Manager

🔐 A secure, enterprise-grade password management tool built with Python.

## Features

- ✅ **AES-256-GCM Encryption**: Military-grade encryption for all stored passwords
- ✅ **Secure Key Derivation**: PBKDF2 with configurable iterations
- ✅ **Password Generation**: Configurable password policies and passphrase generation
- ✅ **AI-Powered Password Generation**: Intelligent password creation using LLM
- ✅ **AI-Powered Multimodal Import**: Extract and import passwords from texts, images (macOS Vision OCR), and audios (macOS Speech ASR) using LLM (SenseAuto)
- ✅ **macOS Standalone Application (.app)**: Standalone packaged macOS bundle with custom Dock icon and built-in configurations for easy drag-and-drop
- ✅ **Password Strength Analysis**: Real-time strength evaluation
- ✅ **MySQL Database**: Enterprise-ready database backend
- ✅ **GUI Interface**: Modern PyQt6-based graphical interface
- ✅ **CLI Interface**: Powerful command-line interface
- ✅ **Category & Tags**: Organize passwords with categories and tags
- ✅ **Search**: Quick search across all entries
- ✅ **Soft Delete**: Recover accidentally deleted entries

## Quick Start

### Prerequisites

- Python 3.14+
- MySQL 8.0+

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/password-manager.git
cd password-manager
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your MySQL credentials and AI API settings
```

5. Initialize the vault:
```bash
pwdmgr init
```

### Launch GUI

```bash
python run_gui.py
```

### macOS Application Bundling

You can build a standalone macOS application bundle (`PasswordManager.app`) for seamless drag-and-drop usage:

1. **Build the bundle**:
   ```bash
   ./scripts/build_mac_app.sh
   ```
   This script will compile high-resolution icon resources from `app_icon.png` using native `sips` and `iconutil` utilities, and bundle the app with your default `.env` configuration.

2. **Run the bundle**:
   - Go to `dist/` directory.
   - Simply drag `PasswordManager.app` to your desktop or **Applications** folder.
   - Double-click to run! It connects to your database with the built-in configuration automatically.

## Usage

### GUI Application

Launch the graphical interface:

```bash
python run_gui.py
```

**Features:**
1. **随机生成**: Generate completely random high-strength passwords
2. **关键词生成**: Generate memorable passwords based on keywords
3. **AI智能生成**: Use AI/LLM to generate intelligent passwords

### CLI Usage

#### Generate Password
```bash
pwdmgr generate --length 20
pwdmgr generate --passphrase
```

#### Check Password Strength
```bash
pwdmgr strength "YourPassword123!"
```

#### Manage Vault
```bash
# Add entry
pwdmgr vault add --title "GitHub" --username "user@example.com" --url "https://github.com"

# List entries
pwdmgr vault list

# Search entries
pwdmgr vault list --search "github"

# Get entry
pwdmgr vault get 1

# Update entry
pwdmgr vault update 1 --title "New Title"

# Delete entry
pwdmgr vault delete 1
```

## Configuration

Edit `.env` file:

```env
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=password_manager

MASTER_KEY_SALT=random_salt_here
ENVIRONMENT=development
LOG_LEVEL=INFO

# AI Password Generation (Optional)
SENSEAUTO_OPENAI_API_KEY=your_api_key
SENSEAUTO_OPENAI_API_BASE=http://your-api-base/v1
```

## Security Features

### Encryption
- **Algorithm**: AES-256-GCM
- **Key Derivation**: PBKDF2-SHA256 with 100,000 iterations
- **Salt**: 16-byte random salt per encryption
- **Nonce**: 12-byte random nonce per encryption

### Password Storage
- Master password is never stored in plaintext
- Password hash stored using PBKDF2
- Each password encrypted with unique nonce
- Encryption keys cleared from memory after use

### Best Practices
- Use `secrets` module for cryptographically secure random numbers
- No sensitive data in logs
- Soft delete with recovery option
- Session timeout configuration

## Development

### Setup Development Environment

```bash
# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run tests with coverage
pytest --cov=src/password_manager

# Run linters
ruff check src/ tests/
black src/ tests/
isort src/ tests/
mypy src/
```

### Code Quality

This project uses:
- **Ruff**: Fast Python linter
- **Black**: Code formatter
- **isort**: Import sorter
- **MyPy**: Static type checker
- **pytest**: Testing framework
- **pre-commit**: Git hooks for code quality

### Testing

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests
pytest tests/integration/

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_crypto.py
```

## Project Structure

```
password-manager/
├── src/password_manager/
│   ├── core/           # Core functionality (crypto, password gen, vault, AI)
│   ├── storage/        # Database models and operations
│   ├── cli/            # Command-line interface
│   ├── gui/            # Graphical user interface
│   ├── config/         # Configuration management
│   └── utils/          # Utility functions
├── tests/
│   ├── unit/           # Unit tests
│   ├── integration/    # Integration tests
│   └── conftest.py     # Pytest fixtures
├── .github/workflows/  # CI/CD pipelines
├── docs/               # Documentation
├── run_gui.py          # GUI launcher
└── requirements.txt    # Dependencies
```

## API Reference

### CryptoManager

```python
from password_manager.core import CryptoManager

crypto = CryptoManager(master_password="your_master_password")

encrypted = crypto.encrypt("secret_data")
decrypted = crypto.decrypt(encrypted)

crypto.clear_key()  # Clear key from memory
```

### PasswordGenerator

```python
from password_manager.core import PasswordGenerator

generator = PasswordGenerator(
    length=20,
    use_special=True,
    exclude_ambiguous=True
)

password = generator.generate()
strength = PasswordGenerator.calculate_strength(password)
```

### AIPasswordGenerator

```python
from password_manager.core import AIPasswordGenerator

ai_gen = AIPasswordGenerator()

# Generate from keyword
password = ai_gen.generate_from_keyword("github", length=16)

# Generate memorable password
password = ai_gen.generate_memorable_password(context="work email")

# Generate variations
variations = ai_gen.suggest_password_variations("BasePass123!", count=3)
```

### VaultManager

```python
from password_manager.core import VaultManager, CryptoManager
from password_manager.storage import DatabaseManager

db = DatabaseManager()
db.initialize()

crypto = CryptoManager(master_password)
vault = VaultManager(crypto, db)

entry = vault.add_entry(
    title="Website",
    username="user@example.com",
    password="secret123",
    url="https://example.com",
    category="Work"
)

password = vault.get_decrypted_password(entry.id)
```

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Security

For security concerns, please read [SECURITY.md](SECURITY.md) and report vulnerabilities responsibly.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [cryptography](https://cryptography.io/) library
- Database ORM by [SQLAlchemy](https://www.sqlalchemy.org/)
- CLI framework by [Click](https://click.palletsprojects.com/)
- GUI framework by [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- AI integration with [OpenAI API](https://openai.com/)
- Inspired by industry best practices for password management

## Roadmap

- [x] GUI application (PyQt6)
- [x] AI-powered password generation
- [ ] Browser extension
- [ ] Mobile app
- [ ] Cloud sync
- [ ] Two-factor authentication
- [ ] Password sharing
- [ ] Audit logs
- [ ] Import/Export from other password managers

---

**⚠️ Security Notice**: This is a development project. For production use, ensure proper security audits and use strong master passwords.