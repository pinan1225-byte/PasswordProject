# Fix All Issues Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all 24 identified issues across security, logic, architecture, code quality, and configuration.

**Architecture:** Issues are grouped into 8 tasks by dependency order — critical logic bugs first, then architecture (logging), then code quality, then config/tooling.

**Tech Stack:** Python 3.14, SQLAlchemy 2.x, PyQt6, Pydantic v2, cryptography, pytest

---

### Task 1: Fix CLI VaultManager missing user_id + hash_password salt handling

**Files:**
- Modify: `src/password_manager/cli/main.py`

- [ ] **Step 1: Fix VaultManager calls missing user_id (all vault commands)**

In `src/password_manager/cli/main.py`, every vault command creates `VaultManager(crypto_manager, db_manager)` — missing the required `user_id`. Since the CLI has no login system, use `user_id=1` as a placeholder (single-user CLI mode). Also fix `init` command's `hash_password` salt handling.

Replace the `add` command body (lines 82-107):
```python
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()

        crypto_manager = CryptoManager(master_password)
        vault_manager = VaultManager(crypto_manager, db_manager, user_id=1)

        tag_list = [t.strip() for t in tags.split(",")] if tags else []

        entry = vault_manager.add_entry(
            title=title,
            username=username,
            password=password,
            url=url,
            category=category,
            tags=tag_list,
        )

        click.echo(f"✓ Entry added successfully (ID: {entry.id})")

        crypto_manager.clear_key()
        db_manager.close()

    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        raise click.Abort()
```

Replace the `list_entries` command body (lines 121-150):
```python
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()

        crypto_manager = CryptoManager(master_password)
        vault_manager = VaultManager(crypto_manager, db_manager, user_id=1)

        entries = vault_manager.list_entries(category=category, tag=tag, search=search)

        if not entries:
            click.echo("No entries found.")
            return

        click.echo(f"\nFound {len(entries)} entries:\n")
        for entry in entries:
            click.echo(f"ID: {entry.id}")
            click.echo(f"  Title: {entry.title}")
            click.echo(f"  Username: {entry.username}")
            if entry.url:
                click.echo(f"  URL: {entry.url}")
            if entry.category:
                click.echo(f"  Category: {entry.category}")
            click.echo()

        crypto_manager.clear_key()
        db_manager.close()

    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        raise click.Abort()
```

Replace the `get` command body (lines 162-192):
```python
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()

        crypto_manager = CryptoManager(master_password)
        vault_manager = VaultManager(crypto_manager, db_manager, user_id=1)

        entry = vault_manager.get_entry(entry_id)
        if entry is None:
            click.echo(f"Entry with ID {entry_id} not found.")
            return

        decrypted_password = vault_manager.get_decrypted_password(entry_id)

        click.echo(f"\nEntry ID: {entry.id}")
        click.echo(f"Title: {entry.title}")
        click.echo(f"Username: {entry.username}")
        click.echo(f"Password: {decrypted_password}")
        if entry.url:
            click.echo(f"URL: {entry.url}")
        if entry.notes:
            click.echo(f"Notes: {entry.notes}")
        if entry.category:
            click.echo(f"Category: {entry.category}")
        if entry.tags:
            click.echo(f"Tags: {', '.join(entry.tags)}")

        crypto_manager.clear_key()
        db_manager.close()

    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        raise click.Abort()
```

Replace the `update` command body (lines 215-242):
```python
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()

        crypto_manager = CryptoManager(master_password)
        vault_manager = VaultManager(crypto_manager, db_manager, user_id=1)

        entry = vault_manager.update_entry(
            entry_id=entry_id,
            title=title,
            username=username,
            password=password,
            url=url,
            category=category,
        )

        if entry is None:
            click.echo(f"Entry with ID {entry_id} not found.")
            return

        click.echo(f"✓ Entry {entry_id} updated successfully")

        crypto_manager.clear_key()
        db_manager.close()

    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        raise click.Abort()
```

Replace the `delete` command body (lines 253-272):
```python
    try:
        db_manager = DatabaseManager()
        db_manager.initialize()

        crypto_manager = CryptoManager(master_password)
        vault_manager = VaultManager(crypto_manager, db_manager, user_id=1)

        success = vault_manager.delete_entry(entry_id)

        if success:
            click.echo(f"✓ Entry {entry_id} deleted successfully")
        else:
            click.echo(f"Entry with ID {entry_id} not found.")

        crypto_manager.clear_key()
        db_manager.close()

    except Exception as e:
        click.echo(f"✗ Error: {str(e)}", err=True)
        raise click.Abort()
```

Fix the `init` command — `hash_password` returns `(str, bytes)` but `save_master_key` expects `salt` as `str`. Replace lines 290-295:
```python
        crypto_manager = CryptoManager(master_password)
        hashed_key, salt_bytes = CryptoManager.hash_password(master_password)

        db_manager.save_master_key(
            hashed_key, salt_bytes.hex()
        )
```

- [ ] **Step 2: Commit**
```bash
cd /Users/chennanxing/PycharmProjects/PasswordProject
git add src/password_manager/cli/main.py
git commit -m "fix: add missing user_id to VaultManager in CLI, fix salt hex encoding in init"
```

---

### Task 2: Fix llm_model_name priority logic inversion

**Files:**
- Modify: `src/password_manager/config/settings.py`

- [ ] **Step 1: Fix the inverted priority in llm_model_name property**

In `src/password_manager/config/settings.py`, replace lines 131-136:
```python
    @property
    def llm_model_name(self) -> str:
        """Get LLM model name with backward compatibility support."""
        # Prefer new LLM_MODEL over old SENSEAUTO_OPENAI_MODEL
        if self.SENSEAUTO_OPENAI_MODEL:
            return self.SENSEAUTO_OPENAI_MODEL
        return self.LLM_MODEL
```

With:
```python
    @property
    def llm_model_name(self) -> str:
        """Get LLM model name with backward compatibility support."""
        # Prefer new LLM_MODEL over old SENSEAUTO_OPENAI_MODEL
        if self.LLM_MODEL:
            return self.LLM_MODEL
        return self.SENSEAUTO_OPENAI_MODEL or "gpt-3.5-turbo"
```

- [ ] **Step 2: Commit**
```bash
git add src/password_manager/config/settings.py
git commit -m "fix: correct llm_model_name priority to prefer LLM_MODEL over legacy field"
```

---

### Task 3: Fix SQL injection in init_db.py

**Files:**
- Modify: `init_db.py`

- [ ] **Step 1: Sanitize database name before use in raw SQL**

In `init_db.py`, replace lines 26-35:
```python
    try:
        # Validate database name to prevent SQL injection
        import re
        db_name = settings.MYSQL_DATABASE
        if not re.match(r'^[a-zA-Z0-9_]+$', db_name):
            raise ValueError(f"Invalid database name: '{db_name}'. Only alphanumeric and underscore allowed.")

        # Create engine without database
        engine = create_engine(server_url, echo=False)

        # Create database if not exists
        with engine.connect() as conn:
            print(f"📦 Creating database '{db_name}' if not exists...")
            conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{db_name}`"))
            conn.commit()
            print(f"✅ Database '{db_name}' is ready!")
```

- [ ] **Step 2: Commit**
```bash
git add init_db.py
git commit -m "fix: sanitize database name in init_db.py to prevent SQL injection"
```

---

### Task 4: Add logging system, remove all debug prints

**Files:**
- Create: `src/password_manager/utils/logging_config.py`
- Modify: `src/password_manager/gui/main_window.py`
- Modify: `src/password_manager/config/settings.py`

- [ ] **Step 1: Create logging configuration module**

Create `src/password_manager/utils/logging_config.py`:
```python
"""Centralized logging configuration."""

import logging
import sys
from src.password_manager.config import get_settings


def setup_logging() -> logging.Logger:
    """Configure and return the application logger."""
    settings = get_settings()
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    return logging.getLogger("password_manager")


logger = setup_logging()
```

- [ ] **Step 2: Replace all debug prints in gui/main_window.py**

In `src/password_manager/gui/main_window.py`, add import at top (after existing imports):
```python
from src.password_manager.utils.logging_config import logger
```

Replace line 295:
```python
            logger.warning("Crypto manager initialization failed: %s", e)
```

Replace line 303:
```python
            logger.warning("AI generator initialization failed: %s", e)
```

Replace line 770:
```python
                logger.debug("Entry ID: %s, Title: %s, Category: '%s' -> '%s'", entry.id, entry.title, entry.category, category)
```

Replace line 801:
```python
                        logger.error("Decryption error for entry %s: %s", entry.id, e)
```

Replace line 1123-1124:
```python
            logger.debug("Category input: '%s'", category_text)
            logger.debug("Category to save: '%s'", category)
```

Replace line 1139:
```python
            logger.debug("Entry category before save: '%s'", entry.category)
```

Replace lines 1147-1148 (the `traceback.print_exc()` block):
```python
        except Exception as e:
            logger.exception("Failed to save password entry")
            QMessageBox.critical(self, "错误", f"保存失败:\n{str(e)}")
```

Also remove the `import traceback` on line 1147.

- [ ] **Step 3: Export logger from utils __init__**

In `src/password_manager/utils/__init__.py`, add:
```python
from src.password_manager.utils.logging_config import logger

__all__ = ["logger"]
```

- [ ] **Step 4: Commit**
```bash
git add src/password_manager/utils/logging_config.py src/password_manager/utils/__init__.py src/password_manager/gui/main_window.py
git commit -m "feat: add centralized logging, replace all debug print() calls with logger"
```

---

### Task 5: Fix DatabaseManager uninitialized guard + tag search bug

**Files:**
- Modify: `src/password_manager/storage/database.py`

- [ ] **Step 1: Add initialization guard to get_session**

In `src/password_manager/storage/database.py`, replace the `get_session` method (lines 49-65):
```python
    @contextmanager
    def get_session(self) -> Session:
        """
        Get database session context manager.

        Yields:
            SQLAlchemy Session

        Raises:
            RuntimeError: If database has not been initialized via initialize()
        """
        if self._session_factory is None:
            raise RuntimeError(
                "DatabaseManager not initialized. Call initialize() before use."
            )
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
```

- [ ] **Step 2: Fix tag search to avoid partial-match false positives**

In `src/password_manager/storage/database.py`, replace lines 161-162:
```python
            if tag:
                query = query.filter(PasswordEntryModel.tags.contains(f'"{tag}"'))
```

This searches for the JSON-encoded form of the tag string (e.g. `"work"` with quotes), which correctly matches `["work", "personal"]` but not `["network"]`.

- [ ] **Step 3: Commit**
```bash
git add src/password_manager/storage/database.py
git commit -m "fix: guard get_session against uninitialized state, fix tag search false positives"
```

---

### Task 6: Fix models.py unused imports + Boolean columns

**Files:**
- Modify: `src/password_manager/storage/models.py`

- [ ] **Step 1: Remove unused imports and fix Boolean columns**

Replace the imports section (lines 1-11) with:
```python
"""Database models for password storage."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()
```

Replace `is_active` column in `UserModel` (line 26):
```python
    is_active = Column(Boolean, default=True, index=True)
```

Replace `is_deleted` column in `PasswordEntryModel` (line 47):
```python
    is_deleted = Column(Boolean, default=False, index=True)
```

- [ ] **Step 2: Update all integer comparisons in database.py to use boolean values**

In `src/password_manager/storage/database.py`, replace all occurrences of `== 0` and `== 1` for these columns:

Line 107: `PasswordEntryModel.is_deleted == False`
Line 151: `PasswordEntryModel.is_deleted == False`
Line 213: `PasswordEntryModel.is_deleted == False`
Line 245: `PasswordEntryModel.is_deleted == False`
Line 255: `model.is_deleted = True`
Line 271: `PasswordEntryModel.is_deleted == False`
Line 296: `PasswordEntryModel.is_deleted == False`

- [ ] **Step 3: Update all integer comparisons in user_manager.py to use boolean values**

In `src/password_manager/core/user_manager.py`:

Line 80: `UserModel.is_active == True`
Line 113: `UserModel.is_active == True`
Line 142: `UserModel.is_active == True`
Line 169: `UserModel.is_active == True`
Line 205: `UserModel.is_active == True`
Line 245: `UserModel.is_active == True`
Line 252: `user.is_active = False`

Also in `user_manager.py`, the `create_user` call sets `is_active=1` — change to `is_active=True`.

- [ ] **Step 4: Commit**
```bash
git add src/password_manager/storage/models.py src/password_manager/storage/database.py src/password_manager/core/user_manager.py
git commit -m "fix: remove unused imports in models.py, use Boolean columns instead of Integer 0/1"
```

---

### Task 7: Fix passphrase entropy + replace random with secrets in GUI

**Files:**
- Modify: `src/password_manager/core/password_gen.py`
- Modify: `src/password_manager/gui/main_window.py`

- [ ] **Step 1: Expand passphrase word list in password_gen.py**

In `src/password_manager/core/password_gen.py`, replace the `word_list` in `generate_passphrase` (lines 195-216) with a larger list:
```python
        word_list = [
            "correct", "horse", "battery", "staple", "apple", "banana",
            "orange", "purple", "green", "blue", "happy", "sunny", "cloud",
            "river", "mountain", "forest", "ocean", "desert", "valley",
            "meadow", "silver", "golden", "crystal", "thunder", "winter",
            "summer", "autumn", "spring", "dragon", "falcon", "tiger",
            "eagle", "shadow", "bright", "swift", "brave", "calm", "bold",
            "sharp", "frost", "flame", "stone", "iron", "copper", "amber",
            "coral", "cedar", "maple", "birch", "willow", "jasper", "onyx",
            "ruby", "sapphire", "emerald", "topaz", "quartz", "granite",
            "marble", "cobalt", "indigo", "violet", "crimson", "scarlet",
            "tawny", "azure", "ivory", "ebony", "walnut", "hazel", "clover",
            "thistle", "nettle", "fern", "moss", "lichen", "pebble", "gravel",
            "canyon", "plateau", "glacier", "tundra", "savanna", "jungle",
            "lagoon", "harbor", "beacon", "lantern", "compass", "anchor",
            "vessel", "current", "ripple", "torrent", "cascade", "delta",
            "summit", "ridge", "crater", "cavern", "tunnel", "bridge",
        ]
```

This gives 100 words → `100^4 = 100,000,000` combinations (~26.5 bits entropy for 4 words).

- [ ] **Step 2: Replace random with secrets in GUI keyword password generation**

In `src/password_manager/gui/main_window.py`, replace the `generate_keyword_password` method (lines 640-677):
```python
    def generate_keyword_password(self):
        """Generate password based on keyword using cryptographically secure random."""
        keyword = self.keyword_input.text().strip()

        if not keyword:
            QMessageBox.warning(self, "警告", "请输入关键词!")
            return

        import secrets
        import string

        keyword_lower = keyword.lower()
        keyword_upper = keyword.upper()
        keyword_cap = keyword.capitalize()

        length = self.length_spinbox.value()
        special_chars = "!@#$%^&*" if self.special_checkbox.isChecked() else ""

        patterns = [
            f"{keyword_cap}{secrets.randbelow(900) + 100}{secrets.choice(special_chars) if special_chars else ''}",
            f"{keyword_lower[0].upper()}{keyword_lower[1:]}{secrets.randbelow(10)}{secrets.randbelow(10)}{secrets.choice(special_chars) if special_chars else ''}",
            f"{keyword_upper[:3]}{secrets.randbelow(90) + 10}{keyword_lower[-3:]}{secrets.choice(special_chars) if special_chars else ''}",
        ]

        password = secrets.choice(patterns)

        all_chars = string.ascii_lowercase
        if self.uppercase_checkbox.isChecked():
            all_chars += string.ascii_uppercase
        if self.digits_checkbox.isChecked():
            all_chars += string.digits
        if self.special_checkbox.isChecked():
            all_chars += special_chars

        while len(password) < length:
            password += secrets.choice(all_chars)

        password = password[:length]
        self.display_password(password)
```

- [ ] **Step 3: Commit**
```bash
git add src/password_manager/core/password_gen.py src/password_manager/gui/main_window.py
git commit -m "fix: expand passphrase word list to 100 words, replace random with secrets in keyword generator"
```

---

### Task 8: Deduplicate load_passwords/search_passwords in GUI + fix .gitignore comments

**Files:**
- Modify: `src/password_manager/gui/main_window.py`
- Modify: `.gitignore`

- [ ] **Step 1: Extract shared tree-rendering logic into private method**

In `src/password_manager/gui/main_window.py`, add this private method before `load_passwords` (insert after line 756):
```python
    def _render_password_tree(self, entries):
        """Render password entries into the tree widget."""
        from collections import defaultdict

        self.password_tree.clear()
        grouped_data = defaultdict(lambda: defaultdict(list))

        for entry in entries:
            category = entry.category or "未分类"
            grouped_data[category][entry.username].append(entry)

        for category in sorted(grouped_data.keys()):
            category_item = QTreeWidgetItem(self.password_tree)
            category_item.setText(0, f"📁 {category}")
            category_item.setExpanded(True)
            font = category_item.font(0)
            font.setBold(True)
            category_item.setFont(0, font)
            category_item.setData(0, Qt.ItemDataRole.UserRole, "category")

            for username in sorted(grouped_data[category].keys()):
                username_item = QTreeWidgetItem(category_item)
                username_item.setText(0, f"👤 {username}")
                username_item.setExpanded(True)
                username_font = username_item.font(0)
                username_font.setBold(True)
                username_item.setFont(0, username_font)
                username_item.setData(0, Qt.ItemDataRole.UserRole, "username")

                for entry in grouped_data[category][username]:
                    entry_item = QTreeWidgetItem(username_item)

                    try:
                        decrypted_password = self.crypto_manager.decrypt(entry.encrypted_password)
                    except Exception as e:
                        logger.error("Decryption error for entry %s: %s", entry.id, e)
                        decrypted_password = "解密失败"

                    entry_item.setText(0, entry.title)
                    entry_item.setText(1, entry.username)
                    entry_item.setText(2, decrypted_password)
                    entry_item.setText(3, entry.url or "")

                    delete_button = QPushButton("删除")
                    delete_button.setFixedSize(80, 35)
                    delete_button.setStyleSheet("""
                        QPushButton {
                            background-color: #e74c3c;
                            color: white;
                            border: none;
                            padding: 8px 15px;
                            border-radius: 5px;
                            font-size: 14px;
                            font-weight: bold;
                        }
                        QPushButton:hover { background-color: #c0392b; }
                        QPushButton:pressed { background-color: #a93226; }
                    """)
                    delete_button.clicked.connect(
                        lambda checked, id=entry.id: self.delete_password(id)
                    )
                    self.password_tree.setItemWidget(entry_item, 4, delete_button)
                    entry_item.setData(0, Qt.ItemDataRole.UserRole, "entry")
                    entry_item.setData(0, Qt.ItemDataRole.UserRole + 1, entry.id)
```

Replace `load_passwords` method body (lines 758-836) with:
```python
    def load_passwords(self):
        """Load passwords for current user."""
        try:
            entries = self.db_manager.list_entries(user_id=self.current_user.id)
            self._render_password_tree(entries)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载密码失败:\n{str(e)}")
```

Replace `search_passwords` method body (lines 838-924) with:
```python
    def search_passwords(self):
        """Search passwords."""
        search_text = self.search_input.text().strip()
        try:
            entries = self.db_manager.list_entries(
                user_id=self.current_user.id,
                search=search_text if search_text else None,
            )
            self._render_password_tree(entries)
        except Exception as e:
            QMessageBox.critical(self, "错误", f"搜索失败:\n{str(e)}")
```

- [ ] **Step 2: Fix .gitignore missing comment markers**

In `.gitignore`, add `# ` prefix to all section header lines that are missing it:

Line 1: `# Python 3.14`
Line 23: `# Virtual Environment`
Line 29: `# IDE`
Line 36: `# Testing`
Line 42: `# Type checking`
Line 47: `# Distribution`
Line 51: `# Logs`
Line 55: `# Database`
Line 60: `# Environment variables`
Line 65: `# OS`
Line 74: `# Security`
Line 79: `# Backup`
Line 83: `# Documentation`
Line 87: `# Jupyter`
Line 90: `# Project specific`

- [ ] **Step 3: Commit**
```bash
git add src/password_manager/gui/main_window.py .gitignore
git commit -m "refactor: extract _render_password_tree to eliminate duplication, fix .gitignore comment markers"
```

---

### Task 9: Fix pyproject.toml metadata + MASTER_KEY_SALT enforcement

**Files:**
- Modify: `pyproject.toml`
- Modify: `src/password_manager/config/settings.py`

- [ ] **Step 1: Fix pyproject.toml author placeholder**

In `pyproject.toml`, replace line 5:
```toml
authors = [{name = "Password Manager", email = "admin@passwordmanager.local"}]
```

- [ ] **Step 2: Add MASTER_KEY_SALT validation to settings**

In `src/password_manager/config/settings.py`, add a validator after the `validate_llm_provider` validator (after line 93):
```python
    @field_validator("MASTER_KEY_SALT")
    @classmethod
    def validate_master_key_salt(cls, v: str) -> str:
        """Ensure MASTER_KEY_SALT has been changed from the insecure default."""
        insecure_default = "change_this_to_random_salt_in_production"
        if v == insecure_default and __import__("os").environ.get("ENVIRONMENT", "development") == "production":
            raise ValueError(
                "MASTER_KEY_SALT must be changed from the default value in production. "
                "Generate a random salt with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        return v
```

- [ ] **Step 3: Commit**
```bash
git add pyproject.toml src/password_manager/config/settings.py
git commit -m "fix: replace placeholder author in pyproject.toml, add MASTER_KEY_SALT production validation"
```
