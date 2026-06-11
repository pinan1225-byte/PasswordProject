"""Main GUI window for Password Manager with user management."""

import os
import secrets as _secrets
import sys
from collections import defaultdict
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
    QCheckBox,
    QSpinBox,
    QMessageBox,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QFormLayout,
    QComboBox,
    QTabWidget,
    QInputDialog,
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
)
from PyQt6.QtCore import Qt, QThread, QSize, pyqtSignal
from PyQt6.QtGui import QFont, QClipboard, QIcon

from src.password_manager.core import PasswordGenerator, AIPasswordGenerator, UserManager, VaultManager, CryptoManager
from src.password_manager.core.password_gen import PasswordStrength
from src.password_manager.storage import DatabaseManager
from src.password_manager.storage.models import PasswordEntry
from src.password_manager.utils.logging_config import logger


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if getattr(sys, "frozen", False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        # In development, check if it needs 'src/' prefix
        dev_path = os.path.join(base_path, relative_path)
        if not os.path.exists(dev_path):
            alt_path = os.path.join(base_path, "src", relative_path)
            if os.path.exists(alt_path):
                return alt_path
    return os.path.join(base_path, relative_path)


class LoginWindow(QMainWindow):
    """Login/Register window."""

    def __init__(self):
        """Initialize login window."""
        super().__init__()
        self.db_manager: Optional[DatabaseManager] = None
        self.user_manager: Optional[UserManager] = None
        self.current_user = None
        
        self.init_db()
        self.init_ui()

    def init_db(self):
        """Initialize database."""
        try:
            self.db_manager = DatabaseManager()
            self.db_manager.initialize()
            self.user_manager = UserManager(self.db_manager)
            
            # 如果 MySQL 连接失败自动降级到 SQLite，给予用户友好提示
            if getattr(self.db_manager, "is_sqlite_fallback", False):
                QMessageBox.information(
                    self,
                    "数据库自动降级提示",
                    "系统检测到您的本地 MySQL 数据库服务未启动或未安装。\n\n"
                    "为了保证软件正常运行，密码管家已为您【自动启用本地免安装 SQLite 数据库】。\n"
                    "您的密码数据目前正安全加密保存在本地：\n"
                    f"{self.db_manager._database_url.replace('sqlite:///', '')}\n\n"
                    "如果您需要使用云端 MySQL 数据库，请确保本地 MySQL 服务已启动并在项目根目录的 .env 文件中配置好连接变量。"
                )
        except Exception as e:
            QMessageBox.critical(self, "错误", f"数据库初始化失败:\n{str(e)}")
            sys.exit(1)

    def init_ui(self):
        """Initialize the user interface."""
        from src.password_manager.config import get_settings
        settings = get_settings()
        self.setWindowTitle(f"密码管家 - 登录 (v{settings.CURRENT_VERSION})")
        icon_path = get_resource_path("password_manager/gui/app_icon.png")
        self.setWindowIcon(QIcon(icon_path))
        self.setFixedSize(460, 380)
        self.setStyleSheet("""
            QMainWindow { background-color: #f0faf4; }
            QWidget { background-color: #f0faf4;
                      font-family: "PingFang SC", "Microsoft YaHei", Arial, sans-serif; }
            QGroupBox {
                font-weight: bold; font-size: 13px;
                border: 1.5px solid #b2dfdb; border-radius: 10px;
                margin-top: 12px; padding-top: 12px;
                background-color: white; color: #2e7d5e;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
            QPushButton {
                background-color: #2ecc71; color: white; border: none;
                padding: 10px 22px; border-radius: 8px;
                font-weight: bold; font-size: 14px;
            }
            QPushButton:hover { background-color: #27ae60; }
            QPushButton:pressed { background-color: #1e8449; }
            QLineEdit {
                padding: 9px 12px; border: 1.5px solid #b2dfdb;
                border-radius: 8px; background-color: white;
                font-size: 14px; color: #2c3e50;
            }
            QLineEdit:focus { border: 2px solid #2ecc71; }
            QLabel { color: #2c3e50; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(40, 40, 40, 40)

        title_label = QLabel("🌿 密码管家")
        title_label.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("color: #27ae60; margin-bottom: 10px;")
        main_layout.addWidget(title_label)

        form_group = QGroupBox("用户登录 / 注册")
        form_layout = QVBoxLayout(form_group)
        form_layout.setSpacing(15)

        username_layout = QHBoxLayout()
        username_label = QLabel("用户名:")
        username_label.setMinimumWidth(80)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        form_layout.addLayout(username_layout)

        password_layout = QHBoxLayout()
        password_label = QLabel("密码:")
        password_label.setMinimumWidth(80)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("请输入密码")
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        form_layout.addLayout(password_layout)

        button_layout = QHBoxLayout()
        
        self.login_button = QPushButton("登录")
        self.login_button.setMinimumHeight(45)
        self.login_button.clicked.connect(self.login)
        button_layout.addWidget(self.login_button)
        
        self.register_button = QPushButton("注册")
        self.register_button.setMinimumHeight(45)
        self.register_button.setStyleSheet("""
            QPushButton { background-color: #a8e6cf; color: #1e8449; }
            QPushButton:hover { background-color: #81d4a8; }
        """)
        self.register_button.clicked.connect(self.register)
        button_layout.addWidget(self.register_button)
        
        form_layout.addLayout(button_layout)
        main_layout.addWidget(form_group)

        info_label = QLabel(f"首次使用请先注册账号  •  v{settings.CURRENT_VERSION}")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #7f8c8d; font-size: 12px;")
        main_layout.addWidget(info_label)

    def login(self):
        """Handle login."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "警告", "请输入用户名和密码!")
            return

        self.login_button.setEnabled(False)
        self.register_button.setEnabled(False)
        self.login_button.setText("正在登录...")

        self.login_thread = LoginThread(self.user_manager, username, password)
        self.login_thread.finished.connect(lambda user: self.on_login_finished(user, password))
        self.login_thread.error.connect(self.on_login_error)
        self.login_thread.start()

    def on_login_finished(self, user, password):
        """Handle successful login lookup."""
        self.login_button.setEnabled(True)
        self.register_button.setEnabled(True)
        self.login_button.setText("登录")

        if user:
            self.current_user = user
            QMessageBox.information(self, "成功", f"欢迎回来, {user.username}!")
            self.open_main_window(password)
            # Clear password after handing off
            password = "\x00" * len(password)
        else:
            QMessageBox.warning(self, "失败", "用户名或密码错误!")

    def on_login_error(self, error_msg):
        """Handle login error."""
        self.login_button.setEnabled(True)
        self.register_button.setEnabled(True)
        self.login_button.setText("登录")
        QMessageBox.critical(self, "错误", f"登录失败:\n{error_msg}")

    def register(self):
        """Handle registration."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(self, "警告", "请输入用户名和密码!")
            return

        self.login_button.setEnabled(False)
        self.register_button.setEnabled(False)
        self.register_button.setText("正在注册...")

        self.register_thread = RegisterThread(self.user_manager, username, password)
        self.register_thread.finished.connect(self.on_register_finished)
        self.register_thread.error.connect(self.on_register_error)
        self.register_thread.start()

    def on_register_finished(self, user):
        """Handle successful registration."""
        self.login_button.setEnabled(True)
        self.register_button.setEnabled(True)
        self.register_button.setText("注册")
        QMessageBox.information(self, "注册成功", f"账号 {user.username} 创建成功，请登录使用。")
        self.password_input.clear()

    def on_register_error(self, error_msg):
        """Handle registration error."""
        self.login_button.setEnabled(True)
        self.register_button.setEnabled(True)
        self.register_button.setText("注册")
        if "Duplicate entry" in error_msg or "UNIQUE constraint" in error_msg:
            QMessageBox.warning(self, "失败", "用户名已存在，请选择其他用户名!")
        else:
            QMessageBox.critical(self, "错误", f"注册失败:\n{error_msg}")

    def open_main_window(self, password: str):
        """Open main password manager window."""
        self.main_window = PasswordManagerGUI(
            db_manager=self.db_manager,
            user_manager=self.user_manager,
            current_user=self.current_user,
            master_password=password,
        )
        self.main_window.show()
        self.close()

class LoginThread(QThread):
    """Thread for user authentication."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, user_manager: UserManager, username: str, password: str):
        super().__init__()
        self.user_manager = user_manager
        self.username = username
        self.password = password

    def run(self):
        try:
            user = self.user_manager.authenticate_user(self.username, self.password)
            self.finished.emit(user)
        except Exception as e:
            self.error.emit(str(e))


class RegisterThread(QThread):
    """Thread for user registration."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, user_manager: UserManager, username: str, password: str):
        super().__init__()
        self.user_manager = user_manager
        self.username = username
        self.password = password

    def run(self):
        try:
            user = self.user_manager.create_user(self.username, self.password)
            self.finished.emit(user)
        except Exception as e:
            self.error.emit(str(e))


class InitCryptoThread(QThread):
    """Thread for crypto and vault initialization."""
    finished = pyqtSignal(object, object)
    error = pyqtSignal(str)

    def __init__(self, db_manager: DatabaseManager, user, master_password: str):
        super().__init__()
        self.db_manager = db_manager
        self.user = user
        self.master_password = master_password

    def run(self):
        try:
            master_key_data = self.db_manager.get_master_key(user_id=self.user.id)
            if master_key_data:
                _, salt_hex = master_key_data
                salt = bytes.fromhex(salt_hex)
            else:
                salt = _secrets.token_bytes(16)
                dummy_hash, _ = CryptoManager.hash_password(self.master_password)
                self.db_manager.save_master_key(dummy_hash, salt.hex(), user_id=self.user.id)

            crypto_manager = CryptoManager(self.master_password, salt=salt)
            vault_manager = VaultManager(
                crypto_manager, self.db_manager, user_id=self.user.id
            )
            self.finished.emit(crypto_manager, vault_manager)
        except Exception as e:
            self.error.emit(str(e))


class LoadPasswordsThread(QThread):
    """Thread for listing and decrypting password entries."""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, vault_manager: VaultManager, crypto_manager: CryptoManager, search: Optional[str] = None):
        super().__init__()
        self.vault_manager = vault_manager
        self.crypto_manager = crypto_manager
        self.search = search

    def run(self):
        try:
            entries = self.vault_manager.list_entries(search=self.search)
            results = []
            for entry in entries:
                try:
                    decrypted_password = self.crypto_manager.decrypt(entry.encrypted_password)
                except Exception as e:
                    logger.error("Decryption error for entry %s: %s", entry.id, e)
                    decrypted_password = "解密失败"
                results.append((entry, decrypted_password))
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class AddEntryThread(QThread):
    """Thread for adding new password entry."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, vault_manager: VaultManager, title: str, username: str, password: str, url: Optional[str], notes: Optional[str], category: Optional[str], tags: list):
        super().__init__()
        self.vault_manager = vault_manager
        self.title = title
        self.username = username
        self.password = password
        self.url = url
        self.notes = notes
        self.category = category
        self.tags = tags

    def run(self):
        try:
            entry = self.vault_manager.add_entry(
                title=self.title,
                username=self.username,
                password=self.password,
                url=self.url,
                notes=self.notes,
                category=self.category,
                tags=self.tags
            )
            self.finished.emit(entry)
        except Exception as e:
            self.error.emit(str(e))


class UpdateEntryThread(QThread):
    """Thread for updating password entry."""
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, vault_manager: VaultManager, entry_id: int, **kwargs):
        super().__init__()
        self.vault_manager = vault_manager
        self.entry_id = entry_id
        self.kwargs = kwargs

    def run(self):
        try:
            entry = self.vault_manager.update_entry(
                entry_id=self.entry_id,
                **self.kwargs
            )
            self.finished.emit(entry)
        except Exception as e:
            self.error.emit(str(e))


class DeleteEntryThread(QThread):
    """Thread for deleting password entry."""
    finished = pyqtSignal(bool)
    error = pyqtSignal(str)

    def __init__(self, vault_manager: VaultManager, entry_id: int):
        super().__init__()
        self.vault_manager = vault_manager
        self.entry_id = entry_id

    def run(self):
        try:
            success = self.vault_manager.delete_entry(self.entry_id)
            self.finished.emit(success)
        except Exception as e:
            self.error.emit(str(e))


class AIGeneratorThread(QThread):
    """Thread for AI password generation to prevent UI freezing."""

    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, generator: AIPasswordGenerator, keyword: str, length: int, include_special: bool):
        super().__init__()
        self.generator = generator
        self.keyword = keyword
        self.length = length
        self.include_special = include_special

    def run(self):
        """Run AI password generation."""
        try:
            password = self.generator.generate_from_keyword(
                keyword=self.keyword,
                length=self.length,
                include_special=self.include_special,
            )
            self.finished.emit(password)
        except Exception as e:
            self.error.emit(str(e))


class PasswordManagerGUI(QMainWindow):
    """Main GUI window for password management."""

    def __init__(self, db_manager: DatabaseManager, user_manager: UserManager, current_user, master_password: str):
        """Initialize the GUI."""
        super().__init__()
        self.db_manager = db_manager
        self.user_manager = user_manager
        self.current_user = current_user

        self.password_generator = PasswordGenerator()
        self.ai_generator: Optional[AIPasswordGenerator] = None
        self.vault_manager: Optional[VaultManager] = None
        self.crypto_manager: Optional[CryptoManager] = None

        self.current_password_gen: Optional[str] = None
        self.ai_thread: Optional[AIGeneratorThread] = None
        self.init_crypto_thread: Optional[InitCryptoThread] = None
        self.load_passwords_thread: Optional[LoadPasswordsThread] = None
        self.search_passwords_thread: Optional[LoadPasswordsThread] = None
        self.delete_thread: Optional[DeleteEntryThread] = None

        self.init_ai_generator()
        self.init_ui()
        self.init_crypto_and_vault(master_password)

    def init_crypto_and_vault(self, master_password: str):
        """Initialize crypto manager and vault manager using QThread."""
        self.password_tree.setEnabled(False)
        self.search_input.setEnabled(False)
        self.search_input.setPlaceholderText("正在初始化解密密钥...")

        self.init_crypto_thread = InitCryptoThread(self.db_manager, self.current_user, master_password)
        self.init_crypto_thread.finished.connect(self.on_init_crypto_finished)
        self.init_crypto_thread.error.connect(self.on_init_crypto_error)
        self.init_crypto_thread.start()

    def on_init_crypto_finished(self, crypto_manager, vault_manager):
        """Handle successful initialization of crypto and vault."""
        self.crypto_manager = crypto_manager
        self.vault_manager = vault_manager
        self.password_tree.setEnabled(True)
        self.search_input.setEnabled(True)
        self.search_input.setPlaceholderText("搜索密码...")
        self.load_passwords()

    def on_init_crypto_error(self, error_msg):
        """Handle crypto initialization error."""
        logger.error("Crypto initialization failed: %s", error_msg)
        QMessageBox.critical(self, "错误", f"密钥初始化失败:\n{error_msg}")

    def init_ai_generator(self):
        """Initialize AI password generator."""
        try:
            self.ai_generator = AIPasswordGenerator()
        except Exception as e:
            logger.warning("AI generator initialization failed: %s", e)

    def init_ui(self):
        """Initialize the user interface."""
        from src.password_manager.config import get_settings
        settings = get_settings()
        self.setWindowTitle(f"密码管家 — {self.current_user.username} (v{settings.CURRENT_VERSION})")
        icon_path = get_resource_path("password_manager/gui/app_icon.png")
        self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("""
            QMainWindow { background-color: #f0faf4; }
            QWidget { background-color: #f0faf4;
                      font-family: "PingFang SC", "Microsoft YaHei", Arial, sans-serif; }
            QGroupBox {
                font-weight: bold; font-size: 13px;
                border: 1.5px solid #b2dfdb; border-radius: 10px;
                margin-top: 12px; padding-top: 12px;
                background-color: white; color: #2e7d5e;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 14px; padding: 0 6px; }
            QPushButton {
                background-color: #2ecc71; color: white; border: none;
                padding: 7px 16px; border-radius: 8px; font-weight: bold;
            }
            QPushButton:hover { background-color: #27ae60; }
            QPushButton:pressed { background-color: #1e8449; }
            QPushButton:disabled { background-color: #c8e6c9; color: #a5d6a7; }
            QLineEdit {
                padding: 7px 10px; border: 1.5px solid #b2dfdb;
                border-radius: 8px; background-color: white; color: #2c3e50;
            }
            QLineEdit:focus { border: 2px solid #2ecc71; }
            QTextEdit {
                border: 1.5px solid #b2dfdb; border-radius: 8px;
                background-color: white; padding: 5px; color: #2c3e50;
            }
            QLabel { color: #2c3e50; }
            QSpinBox {
                padding: 5px 8px; border: 1.5px solid #b2dfdb;
                border-radius: 8px; background-color: white;
            }
            QCheckBox { color: #2c3e50; spacing: 6px; }
            QCheckBox::indicator {
                width: 16px; height: 16px; border-radius: 4px;
                border: 1.5px solid #b2dfdb; background: white;
            }
            QCheckBox::indicator:checked {
                background-color: #2ecc71; border-color: #27ae60;
            }
            QRadioButton { color: #2c3e50; spacing: 6px; }
            QTabWidget::pane {
                border: 1.5px solid #b2dfdb; border-radius: 10px;
                background-color: white; margin-top: -1px;
            }
            QTabBar::tab {
                background-color: #e8f5e9; color: #555;
                padding: 8px 22px; border-radius: 8px 8px 0 0;
                margin-right: 3px; font-size: 13px;
            }
            QTabBar::tab:selected { background-color: #2ecc71; color: white; font-weight: bold; }
            QTabBar::tab:hover:!selected { background-color: #c8e6c9; }
            QProgressBar {
                border: 1.5px solid #b2dfdb; border-radius: 6px;
                background-color: #e8f5e9; text-align: center;
            }
            QProgressBar::chunk { border-radius: 5px; }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        header_layout = QHBoxLayout()
        
        title_label = QLabel(f"🌿  {self.current_user.username} 的密码库 (v{settings.CURRENT_VERSION})")
        title_label.setFont(QFont("Arial", 17, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #27ae60;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # 检查更新按钮
        self.update_btn = QPushButton("检查更新")
        self.update_btn.setStyleSheet("""
            QPushButton { background-color: #3498db; color: white; }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.update_btn.clicked.connect(self.check_for_updates_manual)
        header_layout.addWidget(self.update_btn)

        logout_button = QPushButton("退出登录")
        logout_button.setStyleSheet("""
            QPushButton { background-color: #ff8a80; color: white; }
            QPushButton:hover { background-color: #ff5252; }
        """)
        logout_button.clicked.connect(self.logout)
        header_layout.addWidget(logout_button)
        
        main_layout.addLayout(header_layout)

        # 创建密码列表的主面板容器，替代原来的 tab 结构，保持界面的卡片包裹感
        passwords_panel = QFrame()
        passwords_panel.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1.5px solid #b2dfdb;
                border-radius: 12px;
            }
        """)
        passwords_layout = QVBoxLayout(passwords_panel)
        passwords_layout.setContentsMargins(15, 15, 15, 15)
        passwords_layout.setSpacing(10)

        toolbar_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索密码...")
        self.search_input.textChanged.connect(self.search_passwords)
        toolbar_layout.addWidget(self.search_input)
        
        refresh_button = QPushButton("🔄 刷新")
        refresh_button.clicked.connect(self.load_passwords)
        toolbar_layout.addWidget(refresh_button)

        ai_import_button = QPushButton("🤖 AI 智能导入")
        ai_import_button.setStyleSheet("""
            QPushButton { background-color: #9c27b0; }
            QPushButton:hover { background-color: #7b1fa2; }
        """)
        ai_import_button.clicked.connect(self.show_ai_import_dialog)
        toolbar_layout.addWidget(ai_import_button)
        
        add_button = QPushButton("＋ 添加密码")
        add_button.setStyleSheet("""
            QPushButton { background-color: #2ecc71; }
            QPushButton:hover { background-color: #27ae60; }
        """)
        add_button.clicked.connect(self.show_add_password_dialog)
        toolbar_layout.addWidget(add_button)
        
        passwords_layout.addLayout(toolbar_layout)

        self.password_tree = QTreeWidget()
        self.password_tree.setHeaderLabels(["标题", "用户名", "密码", "URL", "备注", "操作"])
        self.password_tree.setColumnCount(6)
        self.password_tree.setColumnWidth(0, 200)
        self.password_tree.setColumnWidth(1, 120)
        self.password_tree.setColumnWidth(2, 150)
        self.password_tree.setColumnWidth(3, 220)
        self.password_tree.setColumnWidth(4, 200)
        self.password_tree.setColumnWidth(5, 110)

        # 允许用户调整列宽，并将所有数据列设置为可调整大小 (Interactive) 模式
        header = self.password_tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)

        self.password_tree.setIconSize(QSize(14, 14))
        self.password_tree.setIndentation(16)
        self.password_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.password_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.password_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.password_tree.setStyleSheet("""
            QTreeWidget {
                background-color: white;
                border: 1.5px solid #b2dfdb;
                border-radius: 10px;
                font-size: 13px;
                outline: none;
            }
            QTreeWidget::item {
                padding: 3px 4px;
                border-bottom: 1px solid #f1f8f4;
                min-height: 26px;
            }
            QTreeWidget::item:selected {
                background-color: #e8f5e9;
                color: #1b5e20;
            }
            QTreeWidget::item:hover {
                background-color: #f1faf4;
            }
            QHeaderView::section {
                background-color: #e8f5e9;
                color: #2e7d5e;
                padding: 7px 8px;
                border: none;
                border-bottom: 2px solid #b2dfdb;
                font-weight: bold;
                font-size: 12px;
            }
        """)
        passwords_layout.addWidget(self.password_tree)
        main_layout.addWidget(passwords_panel)

        # 初始化状态栏提示双击复制
        self.statusBar().showMessage("提示: 双击列表单元格可直接复制文本内容", 5000)

        # 启动后延时 3 秒在后台静默检查一次更新，并启动定时器每 2 小时在后台自动检查一次（结合 24 小时频控）
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(3000, self.check_for_updates_silent)
        
        self._auto_update_check_timer = QTimer(self)
        self._auto_update_check_timer.timeout.connect(self.check_for_updates_silent)
        self._auto_update_check_timer.start(2 * 60 * 60 * 1000)  # 每 2 小时自动在后台检测一次更新

    def load_passwords(self):
        """Load passwords for current user asynchronously."""
        if not self.vault_manager:
            return
        self.search_input.setEnabled(False)
        self.load_passwords_thread = LoadPasswordsThread(self.vault_manager, self.crypto_manager)
        self.load_passwords_thread.finished.connect(self.on_load_passwords_finished)
        self.load_passwords_thread.error.connect(self.on_load_passwords_error)
        self.load_passwords_thread.start()

    def search_passwords(self):
        """Search passwords asynchronously."""
        if not self.vault_manager:
            return
        search_text = self.search_input.text().strip()
        self.search_passwords_thread = LoadPasswordsThread(
            self.vault_manager, self.crypto_manager, search=search_text if search_text else None
        )
        self.search_passwords_thread.finished.connect(self.on_load_passwords_finished)
        self.search_passwords_thread.error.connect(self.on_load_passwords_error)
        self.search_passwords_thread.start()

    def on_load_passwords_finished(self, results):
        """Handle rendering of decrypted password list."""
        self.search_input.setEnabled(True)
        self._render_entries(results)

    def on_load_passwords_error(self, error_msg):
        """Handle loading error."""
        self.search_input.setEnabled(True)
        QMessageBox.critical(self, "错误", f"加载密码失败:\n{error_msg}")

    def _render_entries(self, results):
        """Render password entries into the tree widget with pre-decrypted passwords."""
        self.password_tree.clear()

        grouped_data = defaultdict(lambda: defaultdict(list))
        for entry, decrypted_password in results:
            category = entry.category or "未分类"
            grouped_data[category][entry.username].append((entry, decrypted_password))

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

                for entry, decrypted_password in grouped_data[category][username]:
                    entry_item = QTreeWidgetItem(username_item)

                    entry_item.setText(0, entry.title)
                    entry_item.setText(1, entry.username)
                    entry_item.setText(2, decrypted_password)
                    entry_item.setText(3, entry.url or "")
                    entry_item.setText(4, entry.notes or "")

                    entry_item.setToolTip(0, entry.title)
                    entry_item.setToolTip(1, entry.username)
                    entry_item.setToolTip(2, decrypted_password)
                    entry_item.setToolTip(3, entry.url or "")
                    entry_item.setToolTip(4, entry.notes or "")

                    delete_button = QPushButton("🗑")
                    delete_button.setFixedSize(26, 26)
                    delete_button.setToolTip("删除")
                    delete_button.setStyleSheet("""
                        QPushButton {
                            background-color: transparent;
                            color: #e57373;
                            border: 1px solid #ef9a9a;
                            border-radius: 5px;
                            font-size: 13px;
                            padding: 0;
                        }
                        QPushButton:hover { background-color: #ffebee; border-color: #e53935; }
                        QPushButton:pressed { background-color: #ffcdd2; }
                    """)
                    # Action buttons container
                    action_widget = QWidget()
                    action_widget.setStyleSheet("background: transparent;")
                    action_layout = QHBoxLayout(action_widget)
                    action_layout.setContentsMargins(2, 1, 2, 1)
                    action_layout.setSpacing(4)

                    edit_button = QPushButton("✏️")
                    edit_button.setFixedSize(26, 26)
                    edit_button.setToolTip("修改")
                    edit_button.setStyleSheet("""
                        QPushButton {
                            background-color: transparent;
                            color: #1976d2;
                            border: 1px solid #90caf9;
                            border-radius: 5px;
                            font-size: 13px;
                            padding: 0;
                        }
                        QPushButton:hover { background-color: #e3f2fd; border-color: #115293; }
                        QPushButton:pressed { background-color: #bbdefb; }
                    """)
                    copy_button = QPushButton("📋")
                    copy_button.setFixedSize(26, 26)
                    copy_button.setToolTip("复制密码")
                    copy_button.setStyleSheet("""
                        QPushButton {
                            background-color: transparent;
                            color: #66bb6a;
                            border: 1px solid #a5d6a7;
                            border-radius: 5px;
                            font-size: 13px;
                            padding: 0;
                        }
                        QPushButton:hover { background-color: #e8f5e9; border-color: #43a047; }
                        QPushButton:pressed { background-color: #c8e6c9; }
                    """)
                    copy_button.clicked.connect(lambda checked, pw=decrypted_password: self._copy_to_clipboard(pw))

                    edit_button.clicked.connect(lambda checked, id=entry.id: self.edit_password(id))

                    delete_button.clicked.connect(lambda checked, id=entry.id: self.delete_password(id))

                    action_layout.addWidget(copy_button)
                    action_layout.addWidget(edit_button)
                    action_layout.addWidget(delete_button)
                    self.password_tree.setItemWidget(entry_item, 5, action_widget)

                    entry_item.setData(0, Qt.ItemDataRole.UserRole, "entry")
                    entry_item.setData(0, Qt.ItemDataRole.UserRole + 1, entry.id)

        # 根据内容自适应调整首列（标题列）宽度，并设置安全区间限制，防止标题过长挤压其他列，或过短影响美观
        self.password_tree.resizeColumnToContents(0)
        col_width = self.password_tree.columnWidth(0)
        if col_width < 200:
            self.password_tree.setColumnWidth(0, 200)
        elif col_width > 450:
            self.password_tree.setColumnWidth(0, 450)


    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard and show brief confirmation."""
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "成功", "密码已复制到剪贴板!")

    def on_item_double_clicked(self, item, column):
        """Double click to copy unit cell value to clipboard."""
        item_type = item.data(0, Qt.ItemDataRole.UserRole)
        if item_type == "entry":
            text = item.text(column)
            if text:
                QApplication.clipboard().setText(text)
                self.statusBar().showMessage("提示: 已成功将单元格内容复制到剪贴板", 2000)

    def show_add_password_dialog(self):
        """Show dialog to add new password."""
        dialog = AddPasswordDialog(self, self.vault_manager, self.crypto_manager)
        dialog.exec()
        self.load_passwords()

    def show_ai_import_dialog(self):
        """Show AI import dialog."""
        if not self.vault_manager:
            return
        dialog = AIImportDialog(self, self.vault_manager, self.ai_generator)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_passwords()

    def delete_password(self, entry_id: int):
        """Delete password asynchronously."""
        reply = QMessageBox.question(
            self,
            "确认删除",
            "确定要删除这个密码吗?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.delete_thread = DeleteEntryThread(self.vault_manager, entry_id)
            self.delete_thread.finished.connect(self.on_delete_finished)
            self.delete_thread.error.connect(self.on_delete_error)
            self.delete_thread.start()

    def on_delete_finished(self, success):
        """Handle successful deletion."""
        if success:
            QMessageBox.information(self, "成功", "密码已删除!")
            self.load_passwords()
        else:
            QMessageBox.warning(self, "警告", "密码不存在!")

    def on_delete_error(self, error_msg):
        """Handle deletion error."""
        QMessageBox.critical(self, "错误", f"删除失败:\n{error_msg}")

    def edit_password(self, entry_id: int):
        """Open edit dialog for a password entry."""
        try:
            dialog = EditPasswordDialog(self, self.vault_manager, self.crypto_manager, entry_id)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                self.load_passwords()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"打开修改对话框失败:\n{str(e)}")

    def show_context_menu(self, position):
        """Show context menu for password tree."""
        item = self.password_tree.itemAt(position)
        
        if not item:
            return
        
        item_type = item.data(0, Qt.ItemDataRole.UserRole)
        
        if item_type != "entry":
            return
        
        entry_id = item.data(0, Qt.ItemDataRole.UserRole + 1)
        
        menu = QMenu(self)

        edit_action = menu.addAction("✏️ 修改")
        copy_password_action = menu.addAction("📋 复制密码")
        copy_username_action = menu.addAction("📋 复制用户名")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ 删除")

        action = menu.exec(self.password_tree.viewport().mapToGlobal(position))

        if action == edit_action:
            self.edit_password(entry_id)
        elif action == copy_password_action:
            password = item.text(2)
            if password:
                clipboard = QApplication.clipboard()
                clipboard.setText(password)
                QMessageBox.information(self, "成功", "密码已复制到剪贴板!")
        elif action == copy_username_action:
            username = item.text(1)
            if username:
                clipboard = QApplication.clipboard()
                clipboard.setText(username)
                QMessageBox.information(self, "成功", "用户名已复制到剪贴板!")
        elif action == delete_action:
            self.delete_password(entry_id)

    def logout(self):
        """Logout and return to login window."""
        reply = QMessageBox.question(
            self,
            "确认退出",
            "确定要退出登录吗?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.login_window = LoginWindow()
            self.login_window.show()
            self.close()

    def check_for_updates_manual(self):
        """手动检查更新"""
        self.start_update_check(silent=False)

    def check_for_updates_silent(self):
        """启动时静默检查更新"""
        self.start_update_check(silent=True)

    def start_update_check(self, silent=False):
        """触发更新探测"""
        from src.password_manager.config import get_settings
        settings = get_settings()
        
        # 保存是否为静默检测的标志
        self._silent_update_check = silent
        self._update_check_cancelled = False
        
        # 如果是静默检测，限制 24 小时内只请求一次 GitHub API
        if silent:
            from PyQt6.QtCore import QSettings, QDateTime
            q_settings = QSettings("PasswordManager", "Updater")
            last_check_str = q_settings.value("last_check_time", "")
            if last_check_str:
                last_check_dt = QDateTime.fromString(last_check_str, Qt.DateFormat.ISODate)
                if last_check_dt.isValid():
                    current_dt = QDateTime.currentDateTime()
                    # 如果距离上次成功检测的时间小于 24 小时，则直接跳过请求
                    if last_check_dt.secsTo(current_dt) < 24 * 3600:
                        logger.info("Skipping silent update check. Last checked at: %s", last_check_str)
                        return
        
        if not silent:
            # 弹窗提示
            self._update_checking_dialog = QMessageBox(self)
            self._update_checking_dialog.setWindowTitle("检查更新")
            self._update_checking_dialog.setText("正在连接服务器检测新版本，请稍候...")
            self._update_checking_dialog.setStandardButtons(QMessageBox.StandardButton.Cancel)
            self._update_checking_dialog.buttonClicked.connect(self.on_update_checking_cancelled)
            self._update_checking_dialog.show()

        self._update_thread = UpdateThread(settings.CURRENT_VERSION, settings.UPDATE_URL)
        self._update_thread.check_finished.connect(self.on_update_check_finished)
        self._update_thread.check_error.connect(self.on_update_check_error)
        self._update_thread.start()

    def on_update_checking_cancelled(self, button):
        """用户在检测更新弹窗中点击取消"""
        logger.info("User cancelled the update check.")
        self._update_check_cancelled = True
        
        if hasattr(self, "_update_thread") and self._update_thread:
            try:
                self._update_thread.terminate()
                self._update_thread.wait()
            except Exception as e:
                logger.warning("Failed to terminate update check thread: %s", str(e))
                
        if hasattr(self, "_update_checking_dialog") and self._update_checking_dialog:
            self._update_checking_dialog.close()
            self._update_checking_dialog = None

    def on_update_check_finished(self, has_update, new_version, download_url, changelog):
        if getattr(self, "_update_check_cancelled", False):
            return

        # 关闭“正在检测”弹窗
        if hasattr(self, "_update_checking_dialog") and self._update_checking_dialog:
            self._update_checking_dialog.close()
            self._update_checking_dialog = None

        if has_update:
            if self._silent_update_check:
                # 静默检测到更新：高亮右上角的“检查更新”按钮为醒目的橙色，提示新版本
                self.update_btn.setText(f"🔴 发现新版 v{new_version}")
                self.update_btn.setStyleSheet("""
                    QPushButton { background-color: #e67e22; color: white; font-weight: bold; }
                    QPushButton:hover { background-color: #d35400; }
                """)
                # 在状态栏温和提醒
                self.statusBar().showMessage(f"✨ 发现新版本 v{new_version}！点击右上角按钮即可一键更新重载。", 15000)
            else:
                # 手动检测到更新：弹窗提问是否升级
                msg = f"发现新版本 v{new_version}！\n\n更新日志:\n{changelog}\n\n是否立即下载升级？"
                reply = QMessageBox.question(
                    self,
                    "发现新版本",
                    msg,
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    if download_url:
                        self.start_download_update(download_url, new_version)
                    else:
                        QMessageBox.warning(self, "更新警告", "云端 Release 中未找到打包发布好的 zip 升级文件！请稍后再试。")
        else:
            if not self._silent_update_check:
                QMessageBox.information(self, "检查更新", "当前已是最新版本！")

        # 记录最后成功检测更新的时间戳，用于静默检查频控
        from PyQt6.QtCore import QSettings, QDateTime
        q_settings = QSettings("PasswordManager", "Updater")
        q_settings.setValue("last_check_time", QDateTime.currentDateTime().toString(Qt.DateFormat.ISODate))

    def on_update_check_error(self, err_msg):
        if getattr(self, "_update_check_cancelled", False):
            return

        if hasattr(self, "_update_checking_dialog") and self._update_checking_dialog:
            self._update_checking_dialog.close()
            self._update_checking_dialog = None

        logger.warning("Update check failed: %s", err_msg)
        if not self._silent_update_check:
            if "404" in err_msg or "Not Found" in err_msg:
                QMessageBox.warning(
                    self,
                    "检测更新失败",
                    "未能在您的 GitHub 仓库中找到任何已发布的 Release 版本（404 错误）。\n\n"
                    "如果您是开发发布人员，请先在终端运行以下脚本以打包并发布您的首个版本：\n"
                    "python scripts/release.py 1.0.0"
                )
            elif "403" in err_msg or "rate limit" in err_msg.lower():
                from src.password_manager.config import get_settings
                settings = get_settings()
                repo_owner = "pinan1225-byte"
                if "repos/" in settings.UPDATE_URL:
                    try:
                        repo_owner = settings.UPDATE_URL.split("repos/")[1].split("/")[0]
                    except Exception:
                        pass
                
                QMessageBox.warning(
                    self,
                    "检测更新太频繁",
                    "您当前的 IP 访问 GitHub 接口太频繁，已触发 GitHub 限流保护（403 错误）。\n\n"
                    "请您稍候再试（通常 30-60 分钟后会自动解除限制），"
                    "或者直接访问下方链接在浏览器中查看最新版本：\n"
                    f"https://github.com/{repo_owner}/PasswordProject/releases"
                )
            else:
                QMessageBox.warning(self, "更新失败", f"无法连接到更新服务器，请检查网络！\n错误详情: {err_msg}")

    def start_download_update(self, download_url, new_version):
        """开启升级包下载进度展示"""
        from PyQt6.QtWidgets import QProgressDialog
        
        self._progress_dialog = QProgressDialog("正在下载升级包，请稍候...", "取消", 0, 100, self)
        self._progress_dialog.setWindowTitle(f"正在更新至 v{new_version}")
        self._progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._progress_dialog.setAutoClose(True)
        self._progress_dialog.setValue(0)
        
        # 绑定取消操作
        self._progress_dialog.canceled.connect(self.cancel_download)
        
        # 重构线程为下载模式
        from src.password_manager.config import get_settings
        settings = get_settings()
        
        self._download_thread = UpdateThread(settings.CURRENT_VERSION, settings.UPDATE_URL)
        self._download_thread.mode = "download"
        self._download_thread.download_target_url = download_url
        
        self._download_thread.download_progress.connect(self.on_download_progress)
        self._download_thread.download_finished.connect(self.on_download_finished)
        self._download_thread.download_error.connect(self.on_download_error)
        self._download_thread.start()

    def cancel_download(self):
        if hasattr(self, "_download_thread") and self._download_thread:
            self._download_thread.is_cancelled = True

    def on_download_progress(self, percent):
        if hasattr(self, "_progress_dialog") and self._progress_dialog:
            self._progress_dialog.setValue(percent)

    def on_download_finished(self, zip_path):
        if hasattr(self, "_progress_dialog") and self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None
            
        reply = QMessageBox.question(
            self,
            "下载成功",
            "升级包已下载完毕！是否立刻重启软件以完成自动更新覆盖？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            import sys
            if sys.platform == "darwin":
                self.perform_hot_reload_mac(zip_path)
            elif sys.platform == "win32":
                self.perform_hot_reload_win(zip_path)
            else:
                QMessageBox.warning(
                    self, 
                    "更新提示", 
                    f"当前系统 {sys.platform} 暂不支持自动热更新覆盖，请手动解压替换。"
                )
                try:
                    os.remove(zip_path)
                except:
                    pass
        else:
            # 删除临时文件
            try:
                os.remove(zip_path)
            except:
                pass

    def on_download_error(self, err_msg):
        if hasattr(self, "_progress_dialog") and self._progress_dialog:
            self._progress_dialog.close()
            self._progress_dialog = None
        QMessageBox.critical(self, "下载失败", f"升级包下载中途出错:\n{err_msg}")

    def perform_hot_reload_mac(self, zip_path: str):
        """执行 macOS 本地 App 文件的热重载覆盖"""
        import os
        import sys
        import tempfile
        import zipfile
        import shutil
        import subprocess
        
        try:
            # 1. 解压包并修复 macOS/Windows 解压缩时中文文件名 cp437 乱码问题，保留 Unix 权限属性
            extract_dir = tempfile.mkdtemp(prefix="pwd_update_")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    try:
                        filename = member.filename.encode('cp437').decode('utf-8')
                    except Exception:
                        try:
                            filename = member.filename.encode('utf-8').decode('utf-8')
                        except Exception:
                            filename = member.filename
                    
                    # 规避潜在的目录穿越漏洞
                    filename = os.path.normpath(filename)
                    if filename.startswith(("/", "..")):
                        continue
                        
                    target_path = os.path.join(extract_dir, filename)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    
                    if not member.is_dir():
                        with zip_ref.open(member) as source, open(target_path, "wb") as target:
                            shutil.copyfileobj(source, target)
                        # 保留并恢复 Unix 文件执行权限属性
                        unix_perms = member.external_attr >> 16
                        if unix_perms:
                            os.chmod(target_path, unix_perms)
                    else:
                        os.makedirs(target_path, exist_ok=True)

            # 2. 寻找到打包出的 .app 结构
            new_app_path = None
            for root, dirs, files in os.walk(extract_dir):
                for d in dirs:
                    if d.endswith(".app"):
                        new_app_path = os.path.join(root, d)
                        break
                if new_app_path:
                    break

            # 3. 删除下载的 zip 临时包
            try:
                os.remove(zip_path)
            except:
                pass

            if not new_app_path:
                QMessageBox.critical(self, "更新错误", "未能从升级包中解压出合法的 macOS 应用程序结构！")
                shutil.rmtree(extract_dir, ignore_errors=True)
                return

            # 4. 判断当前执行环境
            if getattr(sys, "frozen", False):
                exe_dir = sys.executable
                current_app_path = os.path.dirname(os.path.dirname(os.path.dirname(exe_dir)))
                
                if not current_app_path.endswith(".app"):
                    QMessageBox.warning(
                        self, 
                        "更新提示", 
                        f"未能自动识别您的安装路径。\n新版 App 已解压至此，请手动拖拽替换：\n{extract_dir}"
                    )
                    subprocess.run(["open", extract_dir])
                    return

                # 5. 用延时 1.2 秒的后台 bash 脚本，接管并热替换当前 app 并 open 重新拉起
                shell_script = f"""
                (
                sleep 1.2
                rm -rf "{current_app_path}"
                mv "{new_app_path}" "{current_app_path}"
                open "{current_app_path}"
                rm -rf "{extract_dir}"
                ) &
                """
                subprocess.Popen(shell_script, shell=True)
                QApplication.quit()
                sys.exit(0)
            else:
                # 开发模式
                QMessageBox.information(
                    self,
                    "开发更新提示",
                    f"检测到您目前正处于 Python 源码开发调试模式。\n最新版本 App 已在临时文件夹中编译解压就绪，无需执行热覆盖：\n{new_app_path}"
                )
                shutil.rmtree(extract_dir, ignore_errors=True)
        except Exception as e:
            logger.exception("Failed to apply mac app update")
            QMessageBox.critical(self, "热替换失败", f"执行覆盖升级包中途出错:\n{str(e)}")

    def perform_hot_reload_win(self, zip_path: str):
        """执行 Windows 本地 exe 文件的热重载覆盖"""
        import os
        import sys
        import tempfile
        import zipfile
        import shutil
        import subprocess
        from PyQt6.QtWidgets import QApplication
        
        try:
            # 1. 解压包并修复中文路径乱码问题
            extract_dir = tempfile.mkdtemp(prefix="pwd_update_win_")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                for member in zip_ref.infolist():
                    try:
                        filename = member.filename.encode('cp437').decode('utf-8')
                    except Exception:
                        try:
                            filename = member.filename.encode('utf-8').decode('utf-8')
                        except Exception:
                            filename = member.filename
                    
                    filename = os.path.normpath(filename)
                    if filename.startswith(("/", "..")):
                        continue
                        
                    target_path = os.path.join(extract_dir, filename)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    
                    if not member.is_dir():
                        with zip_ref.open(member) as source, open(target_path, "wb") as target:
                            shutil.copyfileobj(source, target)
                    else:
                        os.makedirs(target_path, exist_ok=True)

            # 2. 寻找到打包出的新 exe 文件
            new_exe_path = None
            for root, dirs, files in os.walk(extract_dir):
                for f in files:
                    if f.lower().endswith(".exe"):
                        new_exe_path = os.path.join(root, f)
                        break
                if new_exe_path:
                    break

            # 3. 删除下载的 zip 临时包
            try:
                os.remove(zip_path)
            except:
                pass

            if not new_exe_path:
                QMessageBox.critical(self, "更新错误", "未能从升级包中解压出合法的 Windows 可执行程序（.exe）！")
                shutil.rmtree(extract_dir, ignore_errors=True)
                return

            # 4. 判断当前执行环境
            if getattr(sys, "frozen", False):
                current_exe_path = sys.executable
                
                # 5. 用延时 2 秒的后台 bat 脚本，接管并替换当前 exe，并重新拉起
                bat_content = f"""@echo off
chcp 65001 > nul
timeout /t 2 /nobreak > nul
del /f /q "{current_exe_path}"
copy /y "{new_exe_path}" "{current_exe_path}"
start "" "{current_exe_path}"
rd /s /q "{extract_dir}"
(goto) 2>nul & del "%~f0"
"""
                bat_path = os.path.join(tempfile.gettempdir(), "pwd_update.bat")
                with open(bat_path, "w", encoding="utf-8") as f:
                    f.write(bat_content)

                # 隐藏窗口启动 bat 脚本
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
                
                subprocess.Popen(
                    [bat_path], 
                    startupinfo=startupinfo, 
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                
                QApplication.quit()
                sys.exit(0)
            else:
                # 开发模式
                QMessageBox.information(
                    self,
                    "开发更新提示",
                    f"检测到您目前正处于 Python 源码开发调试模式。\n最新版本 App 已在临时文件夹中编译解压就绪，无需执行热覆盖：\n{new_exe_path}"
                )
                shutil.rmtree(extract_dir, ignore_errors=True)
        except Exception as e:
            logger.exception("Failed to apply windows exe update")
            QMessageBox.critical(self, "热替换失败", f"执行覆盖升级包中途出错:\n{str(e)}")

class PasswordGeneratorDialog(QDialog):
    """高级密码生成对话框"""

    def __init__(self, parent, ai_generator: Optional[AIPasswordGenerator] = None):
        super().__init__(parent)
        self.ai_generator = ai_generator
        self.current_password_gen = ""
        self.generated_password = ""
        self.ai_thread = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("生成高强度密码")
        self.setFixedSize(550, 540)
        self.setStyleSheet("""
            QDialog { background-color: #f0faf4; }
            QWidget { background-color: #f0faf4;
                      font-family: "PingFang SC", "Microsoft YaHei", Arial, sans-serif; }
            QGroupBox {
                border: 1.5px solid #b2dfdb;
                border-radius: 8px;
                margin-top: 12px;
                font-weight: bold;
                color: #2e7d5e;
                font-size: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QLabel { color: #2e7d5e; font-size: 13px; font-weight: 500; }
            QLineEdit {
                padding: 8px 12px; border: 1.5px solid #b2dfdb;
                border-radius: 8px; background-color: white;
                font-size: 13px; color: #2c3e50;
            }
            QLineEdit:focus { border: 2px solid #2ecc71; }
            QCheckBox { color: #2e7d5e; font-size: 13px; }
            QRadioButton { color: #2e7d5e; font-size: 13px; }
            QSpinBox {
                padding: 5px; border: 1.5px solid #b2dfdb;
                border-radius: 6px; background-color: white; font-size: 13px;
            }
            QPushButton {
                background-color: #2ecc71; color: white; border: none;
                padding: 8px 16px; border-radius: 8px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #27ae60; }
            QPushButton:pressed { background-color: #1e8449; }
            QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                border-radius: 3px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 15, 20, 15)

        # Title
        title_label = QLabel("高级密码生成")
        title_label.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #27ae60;")
        layout.addWidget(title_label)

        # 模式选择
        mode_group = QGroupBox("选择生成模式")
        mode_layout = QVBoxLayout(mode_group)
        self.mode_button_group = QButtonGroup()
        
        self.random_radio = QRadioButton("🎲 随机生成高强度密码")
        self.random_radio.setChecked(True)
        self.mode_button_group.addButton(self.random_radio, 0)
        mode_layout.addWidget(self.random_radio)
        
        self.keyword_radio = QRadioButton("🔑 基于关键词生成密码")
        self.mode_button_group.addButton(self.keyword_radio, 1)
        mode_layout.addWidget(self.keyword_radio)
        
        self.ai_radio = QRadioButton("🤖 AI智能生成密码")
        self.mode_button_group.addButton(self.ai_radio, 2)
        mode_layout.addWidget(self.ai_radio)
        
        self.mode_button_group.buttonClicked.connect(self.on_mode_changed)
        layout.addWidget(mode_group)

        # 关键词设置
        self.keyword_group = QGroupBox("关键词设置")
        keyword_layout = QVBoxLayout(self.keyword_group)
        keyword_input_layout = QHBoxLayout()
        keyword_label = QLabel("输入关键词:")
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("例如: github, email, work...")
        keyword_input_layout.addWidget(keyword_label)
        keyword_input_layout.addWidget(self.keyword_input)
        keyword_layout.addLayout(keyword_input_layout)
        self.keyword_group.setVisible(False)
        layout.addWidget(self.keyword_group)

        # 密码设置
        settings_group = QGroupBox("密码设置")
        settings_layout = QVBoxLayout(settings_group)
        
        length_layout = QHBoxLayout()
        length_label = QLabel("密码长度:")
        self.length_spinbox = QSpinBox()
        self.length_spinbox.setMinimum(8)
        self.length_spinbox.setMaximum(64)
        self.length_spinbox.setValue(16)
        length_layout.addWidget(length_label)
        length_layout.addWidget(self.length_spinbox)
        length_layout.addStretch()
        settings_layout.addLayout(length_layout)
        
        options_layout = QHBoxLayout()
        self.uppercase_checkbox = QCheckBox("大写字母 (A-Z)")
        self.uppercase_checkbox.setChecked(True)
        self.lowercase_checkbox = QCheckBox("小写字母 (a-z)")
        self.lowercase_checkbox.setChecked(True)
        self.digits_checkbox = QCheckBox("数字 (0-9)")
        self.digits_checkbox.setChecked(True)
        self.special_checkbox = QCheckBox("特殊字符 (!@#$...)")
        self.special_checkbox.setChecked(True)
        
        options_layout.addWidget(self.uppercase_checkbox)
        options_layout.addWidget(self.lowercase_checkbox)
        options_layout.addWidget(self.digits_checkbox)
        options_layout.addWidget(self.special_checkbox)
        settings_layout.addLayout(options_layout)
        layout.addWidget(settings_group)

        # 生成与复制按钮
        actions_layout = QHBoxLayout()
        self.generate_button = QPushButton("🎲 生成密码")
        self.generate_button.setMinimumHeight(36)
        self.generate_button.clicked.connect(self.generate_password)
        actions_layout.addWidget(self.generate_button)
        
        self.copy_button = QPushButton("📋 复制密码")
        self.copy_button.setMinimumHeight(36)
        self.copy_button.clicked.connect(self.copy_password)
        self.copy_button.setEnabled(False)
        actions_layout.addWidget(self.copy_button)
        layout.addLayout(actions_layout)

        # 生成结果及强度
        result_group = QGroupBox("生成结果")
        result_layout = QVBoxLayout(result_group)
        
        password_display_layout = QHBoxLayout()
        self.password_display = QLineEdit()
        self.password_display.setReadOnly(True)
        self.password_display.setFont(QFont("Courier New", 14))
        self.password_display.setMinimumHeight(36)
        password_display_layout.addWidget(self.password_display)
        result_layout.addLayout(password_display_layout)
        
        strength_layout = QHBoxLayout()
        strength_label = QLabel("密码强度:")
        self.strength_bar = QProgressBar()
        self.strength_bar.setMinimum(0)
        self.strength_bar.setMaximum(5)
        self.strength_bar.setValue(0)
        self.strength_bar.setTextVisible(True)
        self.strength_bar.setFormat("%v/5")
        self.strength_label = QLabel("")
        strength_layout.addWidget(strength_label)
        strength_layout.addWidget(self.strength_bar)
        strength_layout.addWidget(self.strength_label)
        result_layout.addLayout(strength_layout)
        layout.addWidget(result_group)

        # 底部返回与关闭按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: white; color: #7f8c8d;
                border: 1.5px solid #b2dfdb; border-radius: 8px;
            }
            QPushButton:hover { background-color: #f5f5f5; }
        """)
        cancel_btn.clicked.connect(self.reject)

        self.use_button = QPushButton("✔️ 使用该密码并返回")
        self.use_button.setStyleSheet("""
            QPushButton { background-color: #2ecc71; color: white; }
            QPushButton:hover { background-color: #27ae60; }
        """)
        self.use_button.clicked.connect(self.accept_password)
        self.use_button.setEnabled(False)

        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.use_button)
        layout.addLayout(button_layout)

    def on_mode_changed(self):
        """Handle mode change."""
        is_keyword_mode = self.keyword_radio.isChecked()
        is_ai_mode = self.ai_radio.isChecked()
        
        self.keyword_group.setVisible(is_keyword_mode or is_ai_mode)
        
        if is_ai_mode:
            self.keyword_input.setPlaceholderText("输入关键词或上下文信息...")
        else:
            self.keyword_input.setPlaceholderText("例如: github, email, work...")

        # 动态改变对话框高度，防挤压其他密码设置项
        if is_keyword_mode or is_ai_mode:
            self.setFixedHeight(620)
        else:
            self.setFixedHeight(540)

    def generate_password(self):
        """Generate password based on selected mode."""
        mode_id = self.mode_button_group.checkedId()
        
        try:
            if mode_id == 0:
                self.generate_random_password()
            elif mode_id == 1:
                self.generate_keyword_password()
            elif mode_id == 2:
                self.generate_ai_password()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"生成密码失败:\n{str(e)}")

    def generate_random_password(self):
        """Generate random password."""
        generator = PasswordGenerator(
            length=self.length_spinbox.value(),
            use_uppercase=self.uppercase_checkbox.isChecked(),
            use_lowercase=self.lowercase_checkbox.isChecked(),
            use_digits=self.digits_checkbox.isChecked(),
            use_special=self.special_checkbox.isChecked(),
        )
        
        password = generator.generate()
        self.display_password(password)

    def generate_keyword_password(self):
        """Generate password based on keyword using cryptographically secure randomness."""
        keyword = self.keyword_input.text().strip()

        if not keyword:
            QMessageBox.warning(self, "警告", "请输入关键词!")
            return

        import string as _string

        length = self.length_spinbox.value()
        special_chars = "!@#$%^&*" if self.special_checkbox.isChecked() else ""

        keyword_cap = keyword.capitalize()
        suffix_digits = str(_secrets.randbelow(900) + 100)  # 100-999
        suffix_special = _secrets.choice(special_chars) if special_chars else ""

        password = keyword_cap + suffix_digits + suffix_special

        char_pool = _string.ascii_lowercase
        if self.uppercase_checkbox.isChecked():
            char_pool += _string.ascii_uppercase
        if self.digits_checkbox.isChecked():
            char_pool += _string.digits
        if self.special_checkbox.isChecked():
            char_pool += special_chars

        while len(password) < length:
            password += _secrets.choice(char_pool)

        password = password[:length]
        self.display_password(password)

    def generate_ai_password(self):
        """Generate password using AI."""
        keyword = self.keyword_input.text().strip()
        
        if not keyword:
            QMessageBox.warning(self, "警告", "请输入关键词或上下文信息!")
            return
        
        if not self.ai_generator:
            QMessageBox.critical(self, "错误", "AI生成器未初始化，请检查配置!")
            return
        
        self.generate_button.setEnabled(False)
        self.generate_button.setText("🤖 AI生成中...")
        
        self.ai_thread = AIGeneratorThread(
            generator=self.ai_generator,
            keyword=keyword,
            length=self.length_spinbox.value(),
            include_special=self.special_checkbox.isChecked(),
        )
        self.ai_thread.finished.connect(self.on_ai_finished)
        self.ai_thread.error.connect(self.on_ai_error)
        self.ai_thread.start()

    def on_ai_finished(self, password: str):
        """Handle AI generation finished."""
        self.display_password(password)
        self.generate_button.setEnabled(True)
        self.generate_button.setText("🎲 生成密码")

    def on_ai_error(self, error_msg: str):
        """Handle AI generation error."""
        QMessageBox.critical(self, "AI生成错误", f"AI生成失败:\n{error_msg}")
        self.generate_button.setEnabled(True)
        self.generate_button.setText("🎲 生成密码")

    def display_password(self, password: str):
        """Display generated password."""
        self.current_password_gen = password
        self.password_display.setText(password)
        self.copy_button.setEnabled(True)
        self.use_button.setEnabled(True)
        
        strength = PasswordGenerator.calculate_strength(password)
        strength_value = strength.value
        
        self.strength_bar.setValue(strength_value)
        
        strength_colors = {
            PasswordStrength.VERY_WEAK: ("#e74c3c", "非常弱"),
            PasswordStrength.WEAK: ("#e67e22", "弱"),
            PasswordStrength.FAIR: ("#f39c12", "一般"),
            PasswordStrength.STRONG: ("#27ae60", "强"),
            PasswordStrength.VERY_STRONG: ("#16a085", "非常强"),
        }
        
        color, text = strength_colors.get(strength, ("#95a5a6", "未知"))
        self.strength_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                background-color: #ecf0f1;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)
        self.strength_label.setText(f"<b style='color: {color}'>{text}</b>")

    def copy_password(self):
        """Copy password to clipboard."""
        if self.current_password_gen:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.current_password_gen)
            QMessageBox.information(self, "成功", "密码已复制到剪贴板!")

    def accept_password(self):
        self.generated_password = self.password_display.text()
        if not self.generated_password:
            QMessageBox.warning(self, "警告", "请先生成一个密码!")
            return
        self.accept()

    def get_generated_password(self):
        return self.generated_password


class AddPasswordDialog(QDialog):
    """Dialog for adding new password."""

    def __init__(self, parent, vault_manager: VaultManager, crypto_manager: CryptoManager):
        """Initialize dialog."""
        super().__init__(parent)
        self.vault_manager = vault_manager
        self.crypto_manager = crypto_manager
        self.init_ui()

    def init_ui(self):
        """Initialize UI."""
        self.setWindowTitle("添加新密码")
        self.setFixedSize(520, 430)
        self.setStyleSheet("""
            QDialog { background-color: #f0faf4; }
            QWidget { background-color: #f0faf4;
                      font-family: "PingFang SC", "Microsoft YaHei", Arial, sans-serif; }
            QLabel { color: #2e7d5e; font-size: 13px; font-weight: 500; }
            QLineEdit {
                padding: 8px 12px; border: 1.5px solid #b2dfdb;
                border-radius: 8px; background-color: white;
                font-size: 13px; color: #2c3e50;
            }
            QLineEdit:focus { border: 2px solid #2ecc71; }
            QTextEdit {
                border: 1.5px solid #b2dfdb; border-radius: 8px;
                background-color: white; padding: 6px; font-size: 13px;
            }
            QComboBox {
                padding: 7px 10px; border: 1.5px solid #b2dfdb;
                border-radius: 8px; background-color: white; font-size: 13px;
            }
            QPushButton {
                background-color: #2ecc71; color: white; border: none;
                padding: 8px 20px; border-radius: 8px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #27ae60; }
            QPushButton:pressed { background-color: #1e8449; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        # Title
        title_label = QLabel("添加新密码")
        title_label.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #27ae60; margin-bottom: 4px;")
        layout.addWidget(title_label)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("例如: GitHub 账号")
        form_layout.addRow("标题 *", self.title_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("用户名或邮箱")
        form_layout.addRow("用户名 *", self.username_input)

        # Password row: input + show/hide toggle + generate
        password_row = QHBoxLayout()
        password_row.setSpacing(6)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("输入或点击生成")

        self.toggle_password_btn = QPushButton("显示")
        self.toggle_password_btn.setFixedWidth(52)
        self.toggle_password_btn.setStyleSheet("""
            QPushButton {
                background-color: white; color: #27ae60;
                border: 1.5px solid #b2dfdb; border-radius: 8px;
                font-size: 12px; font-weight: bold; padding: 0;
            }
            QPushButton:hover { background-color: #e8f5e9; border-color: #2ecc71; }
            QPushButton:checked { background-color: #e8f5e9; }
        """)
        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)

        generate_btn = QPushButton("生成")
        generate_btn.setFixedWidth(52)
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #a8e6cf; color: #1b5e20;
                border: none; border-radius: 8px;
                font-size: 12px; font-weight: bold; padding: 0;
            }
            QPushButton:hover { background-color: #81d4a8; }
        """)
        generate_btn.clicked.connect(self.generate_password)

        password_row.addWidget(self.password_input)
        password_row.addWidget(self.toggle_password_btn)
        password_row.addWidget(generate_btn)
        form_layout.addRow("密码 *", password_row)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com")
        form_layout.addRow("URL", self.url_input)

        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.addItems(["工作", "个人", "社交", "金融", "购物", "其他"])
        form_layout.addRow("分类", self.category_input)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(70)
        self.notes_input.setPlaceholderText("备注信息（可选）")
        form_layout.addRow("备注", self.notes_input)

        layout.addLayout(form_layout)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        cancel_button = QPushButton("取消")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: white; color: #7f8c8d;
                border: 1.5px solid #b2dfdb; border-radius: 8px;
            }
            QPushButton:hover { background-color: #f5f5f5; }
        """)
        cancel_button.clicked.connect(self.reject)

        self.save_button = QPushButton("保存密码")
        self.save_button.clicked.connect(self.save_password)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

    def toggle_password_visibility(self):
        """Toggle password visibility."""
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_btn.setText("隐藏")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_btn.setText("显示")

    def generate_password(self):
        """Open advanced password generator dialog."""
        ai_gen = self.parent().ai_generator if hasattr(self.parent(), 'ai_generator') else None
        dialog = PasswordGeneratorDialog(self, ai_gen)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            password = dialog.get_generated_password()
            self.password_input.setText(password)

    def save_password(self):
        """Save password asynchronously."""
        title = self.title_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not all([title, username, password]):
            QMessageBox.warning(self, "警告", "请填写所有必填项!")
            return

        category_text = self.category_input.currentText().strip()
        category = category_text if category_text else None

        self.save_button.setEnabled(False)

        self.save_thread = AddEntryThread(
            vault_manager=self.vault_manager,
            title=title,
            username=username,
            password=password,
            url=self.url_input.text().strip() or None,
            notes=self.notes_input.toPlainText().strip() or None,
            category=category,
            tags=[]
        )
        self.save_thread.finished.connect(self.on_save_finished)
        self.save_thread.error.connect(self.on_save_error)
        self.save_thread.start()

    def on_save_finished(self, entry):
        """Handle successful saving."""
        QMessageBox.information(self, "成功", "密码保存成功!")
        self.accept()

    def on_save_error(self, error_msg):
        """Handle saving error."""
        self.save_button.setEnabled(True)
        logger.exception("Failed to save password entry")
        QMessageBox.critical(self, "错误", f"保存失败:\n{error_msg}")


class EditPasswordDialog(QDialog):
    """Dialog for editing an existing password entry."""

    def __init__(self, parent, vault_manager: VaultManager, crypto_manager: CryptoManager, entry_id: int):
        """Initialize dialog with pre-filled entry data."""
        super().__init__(parent)
        self.vault_manager = vault_manager
        self.crypto_manager = crypto_manager
        self.entry_id = entry_id
        self._entry = vault_manager.get_entry(entry_id)
        if self._entry is None:
            raise ValueError(f"Entry {entry_id} not found")
        self._decrypted_password = crypto_manager.decrypt(self._entry.encrypted_password)
        self.init_ui()

    def init_ui(self):
        """Initialize UI with pre-filled values."""
        self.setWindowTitle("修改密码")
        self.setFixedSize(520, 430)
        self.setStyleSheet("""
            QDialog { background-color: #f0faf4; }
            QWidget { background-color: #f0faf4;
                      font-family: "PingFang SC", "Microsoft YaHei", Arial, sans-serif; }
            QLabel { color: #2e7d5e; font-size: 13px; font-weight: 500; }
            QLineEdit {
                padding: 8px 12px; border: 1.5px solid #b2dfdb;
                border-radius: 8px; background-color: white;
                font-size: 13px; color: #2c3e50;
            }
            QLineEdit:focus { border: 2px solid #2ecc71; }
            QTextEdit {
                border: 1.5px solid #b2dfdb; border-radius: 8px;
                background-color: white; padding: 6px; font-size: 13px;
            }
            QComboBox {
                padding: 7px 10px; border: 1.5px solid #b2dfdb;
                border-radius: 8px; background-color: white; font-size: 13px;
            }
            QPushButton {
                background-color: #2ecc71; color: white; border: none;
                padding: 8px 20px; border-radius: 8px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #27ae60; }
            QPushButton:pressed { background-color: #1e8449; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        title_label = QLabel("修改密码")
        title_label.setFont(QFont("Arial", 15, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #27ae60; margin-bottom: 4px;")
        layout.addWidget(title_label)

        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.title_input = QLineEdit(self._entry.title)
        form_layout.addRow("标题 *", self.title_input)

        self.username_input = QLineEdit(self._entry.username)
        form_layout.addRow("用户名 *", self.username_input)

        # Password row
        password_row = QHBoxLayout()
        password_row.setSpacing(6)
        self.password_input = QLineEdit(self._decrypted_password)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.toggle_password_btn = QPushButton("显示")
        self.toggle_password_btn.setFixedWidth(52)
        self.toggle_password_btn.setStyleSheet("""
            QPushButton {
                background-color: white; color: #27ae60;
                border: 1.5px solid #b2dfdb; border-radius: 8px;
                font-size: 12px; font-weight: bold; padding: 0;
            }
            QPushButton:hover { background-color: #e8f5e9; border-color: #2ecc71; }
        """)
        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)

        generate_btn = QPushButton("生成")
        generate_btn.setFixedWidth(52)
        generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #a8e6cf; color: #1b5e20;
                border: none; border-radius: 8px;
                font-size: 12px; font-weight: bold; padding: 0;
            }
            QPushButton:hover { background-color: #81d4a8; }
        """)
        generate_btn.clicked.connect(self.generate_password)

        password_row.addWidget(self.password_input)
        password_row.addWidget(self.toggle_password_btn)
        password_row.addWidget(generate_btn)
        form_layout.addRow("密码 *", password_row)

        self.url_input = QLineEdit(self._entry.url or "")
        self.url_input.setPlaceholderText("https://example.com")
        form_layout.addRow("URL", self.url_input)

        self.category_input = QComboBox()
        self.category_input.setEditable(True)
        self.category_input.addItems(["工作", "个人", "社交", "金融", "购物", "其他"])
        if self._entry.category:
            self.category_input.setCurrentText(self._entry.category)
        form_layout.addRow("分类", self.category_input)

        self.notes_input = QTextEdit()
        self.notes_input.setMaximumHeight(70)
        self.notes_input.setPlaceholderText("备注信息（可选）")
        if self._entry.notes:
            self.notes_input.setPlainText(self._entry.notes)
        form_layout.addRow("备注", self.notes_input)

        layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)

        cancel_button = QPushButton("取消")
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: white; color: #7f8c8d;
                border: 1.5px solid #b2dfdb; border-radius: 8px;
            }
            QPushButton:hover { background-color: #f5f5f5; }
        """)
        cancel_button.clicked.connect(self.reject)

        self.save_button = QPushButton("保存修改")
        self.save_button.clicked.connect(self.save_changes)

        button_layout.addWidget(cancel_button)
        button_layout.addWidget(self.save_button)
        layout.addLayout(button_layout)

    def toggle_password_visibility(self):
        """Toggle password visibility."""
        if self.password_input.echoMode() == QLineEdit.EchoMode.Password:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_btn.setText("隐藏")
        else:
            self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_btn.setText("显示")

    def generate_password(self):
        """Open advanced password generator dialog."""
        ai_gen = self.parent().ai_generator if hasattr(self.parent(), 'ai_generator') else None
        dialog = PasswordGeneratorDialog(self, ai_gen)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            password = dialog.get_generated_password()
            self.password_input.setText(password)

    def save_changes(self):
        """Save updated entry asynchronously."""
        title = self.title_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not all([title, username, password]):
            QMessageBox.warning(self, "警告", "标题、用户名和密码不能为空!")
            return

        category_text = self.category_input.currentText().strip()
        self.save_button.setEnabled(False)

        self.update_thread = UpdateEntryThread(
            vault_manager=self.vault_manager,
            entry_id=self.entry_id,
            title=title,
            username=username,
            password=password,
            url=self.url_input.text().strip() or None,
            category=category_text if category_text else None,
            notes=self.notes_input.toPlainText().strip() or None,
        )
        self.update_thread.finished.connect(self.on_update_finished)
        self.update_thread.error.connect(self.on_update_error)
        self.update_thread.start()

    def on_update_finished(self, entry):
        """Handle successful update."""
        QMessageBox.information(self, "成功", "密码修改成功!")
        self.accept()

    def on_update_error(self, error_msg):
        """Handle update error."""
        self.save_button.setEnabled(True)
        logger.exception("Failed to update password entry")
        QMessageBox.critical(self, "错误", f"修改失败:\n{error_msg}")


class OCRThread(QThread):
    """后台执行图像文字提取(OCR)的线程"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            from src.password_manager.core import MultimodalExtractor
            text = MultimodalExtractor.extract_text_from_image(self.file_path)
            self.finished.emit(text)
        except Exception as e:
            self.error.emit(str(e))


class ASRThread(QThread):
    """后台执行音频语音识别(ASR)的线程"""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, file_path: str):
        super().__init__()
        self.file_path = file_path

    def run(self):
        try:
            from src.password_manager.core import MultimodalExtractor
            text = MultimodalExtractor.extract_text_from_audio(self.file_path)
            self.finished.emit(text)
        except Exception as e:
            self.error.emit(str(e))


class AIExtractionThread(QThread):
    """后台使用大模型智能分析文本提取资产的线程"""
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, generator: AIPasswordGenerator, text: str):
        super().__init__()
        self.generator = generator
        self.text = text

    def run(self):
        try:
            results = self.generator.extract_entries_from_text(self.text)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class BatchImportThread(QThread):
    """后台单线程顺序将条目加密并保存到数据库的批量导入线程，防锁竞争"""
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(int)
    error = pyqtSignal(str)

    def __init__(self, vault_manager: VaultManager, entries: list[dict]):
        super().__init__()
        self.vault_manager = vault_manager
        self.entries = entries

    def run(self):
        success_count = 0
        try:
            for item in self.entries:
                self.vault_manager.add_entry(
                    title=item.get("title", "未命名"),
                    username=item.get("username", "未知"),
                    password=item.get("password", "未提供"),
                    url=item.get("url") or None,
                    notes=item.get("notes") or None,
                    category=item.get("category") or None,
                    tags=[]
                )
                success_count += 1
                self.progress.emit(success_count, len(self.entries))
            self.finished.emit(success_count)
        except Exception as e:
            self.error.emit(str(e))


class AIImportDialog(QDialog):
    """🤖 AI 智能多模态导入密码对话框"""

    def __init__(self, parent, vault_manager: VaultManager, ai_generator: Optional[AIPasswordGenerator]):
        super().__init__(parent)
        self.vault_manager = vault_manager
        self.ai_generator = ai_generator
        self.extracted_entries: list[dict] = []
        
        # 线程变量
        self.ocr_thread = None
        self.asr_thread = None
        self.ai_thread = None
        self.import_thread = None
        
        # 实时录音相关变量
        self.audio_source = None
        self.temp_pcmfile = None
        self.record_timer = None
        self.record_seconds = 0
        self.temp_pcm_path = ""
        self.temp_wav_path = ""
        
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("AI 智能密码资产导入")
        self.setFixedSize(1000, 600)
        self.setStyleSheet("""
            QDialog { background-color: #f0faf4; }
            QWidget { background-color: #f0faf4;
                      font-family: "PingFang SC", "Microsoft YaHei", Arial, sans-serif; }
            QLabel { color: #2e7d5e; font-size: 13px; font-weight: 500; }
            QTextEdit {
                border: 1.5px solid #b2dfdb; border-radius: 8px;
                background-color: white; padding: 6px; font-size: 13px; color: #2c3e50;
            }
            QTableWidget {
                background-color: white; border: 1.5px solid #b2dfdb;
                border-radius: 8px; font-size: 12px; gridline-color: #f1f8f4;
            }
            QTableWidget::item { padding: 4px; }
            QHeaderView::section {
                background-color: #e8f5e9; color: #2e7d5e;
                font-weight: bold; border: none; border-bottom: 1.5px solid #b2dfdb;
            }
            QPushButton {
                background-color: #2ecc71; color: white; border: none;
                padding: 8px 16px; border-radius: 8px; font-weight: bold; font-size: 13px;
            }
            QPushButton:hover { background-color: #27ae60; }
            QPushButton:pressed { background-color: #1e8449; }
            QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
            QProgressBar {
                border: 1.5px solid #b2dfdb; border-radius: 6px;
                text-align: center; background-color: #ecf0f1; height: 18px;
            }
            QProgressBar::chunk {
                background-color: #2ecc71; border-radius: 4px;
            }
            QTabWidget::pane {
                border: 1px solid #b2dfdb; border-radius: 8px; background-color: white;
            }
            QTabBar::tab {
                background-color: #e8f5e9; color: #2e7d5e; border: 1px solid #b2dfdb;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
                padding: 6px 12px; font-size: 12px;
            }
            QTabBar::tab:selected { background-color: #2ecc71; color: white; font-weight: bold; }
        """)

        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ---------------- 左半面板：源文字录入与 OCR/ASR 提取 ----------------
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        # 标题提示
        source_label = QLabel("🤖 步骤 1：录入或提取待解析文本")
        source_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        source_label.setStyleSheet("color: #27ae60;")
        left_layout.addWidget(source_label)

        # 多模态提取选项卡
        self.source_tabs = QTabWidget()
        
        # Tab 1: 文本贴入
        text_tab = QWidget()
        text_tab_layout = QVBoxLayout(text_tab)
        text_tab_layout.setContentsMargins(10, 10, 10, 10)
        self.text_tip_label = QLabel("可在下方汇总框直接输入或粘贴账号密码说明，例如：\\n'我的 GitHub 账号是 cnx@example.com，密码为 p@ss123'")
        self.text_tip_label.setWordWrap(True)
        self.text_tip_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        text_tab_layout.addWidget(self.text_tip_label)
        self.source_tabs.addTab(text_tab, "✏️ 贴入文本")

        # Tab 2: 图片识别
        image_tab = QWidget()
        image_tab_layout = QVBoxLayout(image_tab)
        image_tab_layout.setContentsMargins(10, 10, 10, 10)
        self.select_img_btn = QPushButton("📂 选择图片并提取文字 (OCR)")
        self.select_img_btn.clicked.connect(self.select_image_file)
        self.image_path_label = QLabel("未选择任何图片。支持 .png, .jpg, .jpeg")
        self.image_path_label.setWordWrap(True)
        self.image_path_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        image_tab_layout.addWidget(self.select_img_btn)
        image_tab_layout.addWidget(self.image_path_label)
        image_tab_layout.addStretch()
        self.source_tabs.addTab(image_tab, "🖼️ 图片提取")

        # Tab 3: 音频识别
        audio_tab = QWidget()
        audio_tab_layout = QVBoxLayout(audio_tab)
        audio_tab_layout.setContentsMargins(10, 10, 10, 10)
        audio_tab_layout.setSpacing(10)
        
        # 选项一：选择已录制音频文件
        self.select_audio_btn = QPushButton("📂 选择已录制音频 (ASR)")
        self.select_audio_btn.clicked.connect(self.select_audio_file)
        
        # 选项二：实时耳机/麦克风录音
        record_layout = QHBoxLayout()
        record_layout.setSpacing(8)
        self.start_record_btn = QPushButton("🎙️ 开始耳机/麦克风录音")
        self.start_record_btn.setStyleSheet("""
            QPushButton { background-color: #2980b9; color: white; }
            QPushButton:hover { background-color: #3498db; }
        """)
        self.start_record_btn.clicked.connect(self.start_recording)
        
        self.stop_record_btn = QPushButton("⏹️ 结束录音并转写")
        self.stop_record_btn.setStyleSheet("""
            QPushButton { background-color: #c0392b; color: white; }
            QPushButton:hover { background-color: #e74c3c; }
            QPushButton:disabled { background-color: #bdc3c7; color: #7f8c8d; }
        """)
        self.stop_record_btn.setEnabled(False)
        self.stop_record_btn.clicked.connect(self.stop_recording)
        
        record_layout.addWidget(self.start_record_btn)
        record_layout.addWidget(self.stop_record_btn)
        
        # 提示和路径展示标签
        self.audio_path_label = QLabel("未录制或选择任何音频。支持 .wav 格式或麦克风录音")
        self.audio_path_label.setWordWrap(True)
        self.audio_path_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        
        audio_tab_layout.addWidget(self.select_audio_btn)
        audio_tab_layout.addLayout(record_layout)
        audio_tab_layout.addWidget(self.audio_path_label)
        audio_tab_layout.addStretch()
        self.source_tabs.addTab(audio_tab, "🎵 音频提取")

        left_layout.addWidget(self.source_tabs)

        # 汇总展示与人工微调框
        summary_title = QLabel("📝 汇总待分析文本（支持人工修改）：")
        left_layout.addWidget(summary_title)
        
        self.summary_textedit = QTextEdit()
        self.summary_textedit.setPlaceholderText("在此处补充、贴入或微调您录入的密码数据...")
        left_layout.addWidget(self.summary_textedit)

        # AI 智能分析按钮
        self.analyze_btn = QPushButton("🤖 提交 AI 智能分析提取")
        self.analyze_btn.setMinimumHeight(40)
        self.analyze_btn.setStyleSheet("""
            QPushButton { background-color: #27ae60; font-size: 14px; }
            QPushButton:hover { background-color: #219a52; }
        """)
        self.analyze_btn.clicked.connect(self.start_ai_extraction)
        left_layout.addWidget(self.analyze_btn)

        main_layout.addWidget(left_panel, 45)

        # ---------------- 右半面板：AI 提取预览与确认导入 ----------------
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        # 标题提示
        preview_label = QLabel("📋 步骤 2：AI 提取结果确认与核对")
        preview_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        preview_label.setStyleSheet("color: #27ae60;")
        right_layout.addWidget(preview_label)

        # 表格预览
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(6)
        self.preview_table.setHorizontalHeaderLabels(["标题", "用户名", "密码", "网址", "分类", "备注"])
        header = self.preview_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        right_layout.addWidget(self.preview_table)

        # 状态展示与进度条
        self.status_label = QLabel("就绪。请贴入文本并点击“提交 AI 智能分析提取”")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        right_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        # 底部操作按钮
        right_buttons = QHBoxLayout()
        right_buttons.setSpacing(10)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton { background-color: white; color: #7f8c8d; border: 1.5px solid #b2dfdb; }
            QPushButton:hover { background-color: #f5f5f5; }
        """)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.import_btn = QPushButton("📥 一键导入确认的密码")
        self.import_btn.setStyleSheet("""
            QPushButton { background-color: #2ecc71; }
            QPushButton:hover { background-color: #27ae60; }
        """)
        self.import_btn.clicked.connect(self.start_batch_import)
        self.import_btn.setEnabled(False)

        right_buttons.addWidget(self.cancel_btn)
        right_buttons.addWidget(self.import_btn)
        right_layout.addLayout(right_buttons)

        main_layout.addWidget(right_panel, 55)

    def select_image_file(self):
        """选择图片并触发后台 OCR 处理"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择密码截图/图片", "", "图片文件 (*.png *.jpg *.jpeg *.bmp)"
        )
        if not file_path:
            return

        self.image_path_label.setText(f"已选择: {os.path.basename(file_path)}")
        self.status_label.setText("正在执行原生图像 OCR 识别文字...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.select_img_btn.setEnabled(False)

        self.ocr_thread = OCRThread(file_path)
        self.ocr_thread.finished.connect(self.on_ocr_finished)
        self.ocr_thread.error.connect(self.on_ocr_error)
        self.ocr_thread.start()

    def on_ocr_finished(self, text: str):
        self.select_img_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("图像 OCR 文字识别完成！")
        if text.strip():
            curr_text = self.summary_textedit.toPlainText().strip()
            new_text = f"{curr_text}\n{text}" if curr_text else text
            self.summary_textedit.setPlainText(new_text)
        else:
            QMessageBox.warning(self, "OCR 识别提示", "未能在该图片中提取到有效文本字样，请确保图片文字清晰。")

    def on_ocr_error(self, err_msg: str):
        self.select_img_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("图像 OCR 识别失败。")
        QMessageBox.critical(self, "识别失败", f"OCR 提取出错:\n{err_msg}")

    def select_audio_file(self):
        """选择音频并触发后台 ASR 处理"""
        from PyQt6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择语音口述音频", "", "音频文件 (*.wav)"
        )
        if not file_path:
            return

        self.audio_path_label.setText(f"已选择: {os.path.basename(file_path)}")
        self.run_asr_process(file_path)

    def run_asr_process(self, file_path: str):
        """统一触发后台 ASR 进程，锁定所有音频源"""
        self.status_label.setText("正在转录语音音频 (ASR)...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        # 禁用所有相关的音频输入按钮，防止识别中二次操作
        self.select_audio_btn.setEnabled(False)
        self.start_record_btn.setEnabled(False)
        self.stop_record_btn.setEnabled(False)

        self.asr_thread = ASRThread(file_path)
        self.asr_thread.finished.connect(self.on_asr_finished)
        self.asr_thread.error.connect(self.on_asr_error)
        self.asr_thread.start()

    def on_asr_finished(self, text: str):
        self.select_audio_btn.setEnabled(True)
        self.start_record_btn.setEnabled(True)
        self.stop_record_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("语音音频转录完成！")
        if text.strip():
            curr_text = self.summary_textedit.toPlainText().strip()
            new_text = f"{curr_text}\n{text}" if curr_text else text
            self.summary_textedit.setPlainText(new_text)
        else:
            QMessageBox.warning(self, "语音转文字提示", "未能识别转写出音频中的口述词，请确保录音清晰。")

    def on_asr_error(self, err_msg: str):
        self.select_audio_btn.setEnabled(True)
        self.start_record_btn.setEnabled(True)
        self.stop_record_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_label.setText("语音转文字失败。")
        QMessageBox.critical(self, "识别失败", f"ASR 提取出错:\n{err_msg}")

    def start_recording(self):
        """开始从耳机/麦克风录制语音音频 PCM 流"""
        from PyQt6.QtMultimedia import QAudioSource, QAudioFormat, QMediaDevices
        from PyQt6.QtCore import QFile, QIODevice, QTimer
        import tempfile

        devices = QMediaDevices.audioInputs()
        if not devices:
            QMessageBox.warning(self, "设备警告", "未检测到可用的麦克风/耳机录音输入设备，请检查连接！")
            return

        # 固定标准的 ASR 识别音频格式参数：16000Hz, 单声道, Int16 
        format = QAudioFormat()
        format.setSampleRate(16000)
        format.setChannelCount(1)
        format.setSampleFormat(QAudioFormat.SampleFormat.Int16)

        default_device = QMediaDevices.defaultAudioInput()
        if not default_device.isFormatSupported(format):
            format = default_device.preferredFormat()

        try:
            self.audio_source = QAudioSource(default_device, format)
            
            # 创建 PCM 缓存文件
            self.temp_pcm_path = tempfile.mktemp(suffix=".pcm")
            self.temp_pcmfile = QFile(self.temp_pcm_path)
            if not self.temp_pcmfile.open(QIODevice.OpenModeFlag.WriteOnly | QIODevice.OpenModeFlag.Truncate):
                QMessageBox.critical(self, "错误", "无法创建录音临时缓存文件，请检查系统读写权限！")
                return

            # 控制交互按钮状态
            self.select_audio_btn.setEnabled(False)
            self.start_record_btn.setEnabled(False)
            self.stop_record_btn.setEnabled(True)

            # 启动录音
            self.audio_source.start(self.temp_pcmfile)

            # 启动计时器
            self.record_seconds = 0
            self.audio_path_label.setText("<html><span style='color: #e74c3c; font-weight: bold;'>🔴 录音中...</span> 00:00</html>")
            if not self.record_timer:
                self.record_timer = QTimer(self)
                self.record_timer.timeout.connect(self.update_record_time)
            self.record_timer.start(1000)

        except Exception as e:
            logger.exception("Failed to start audio recording")
            QMessageBox.critical(self, "错误", f"启动录音失败:\n{str(e)}")
            self.select_audio_btn.setEnabled(True)
            self.start_record_btn.setEnabled(True)
            self.stop_record_btn.setEnabled(False)

    def update_record_time(self):
        """刷新录音计时时间显示，每秒红灰双色闪烁且支持 60s 超时保护"""
        self.record_seconds += 1
        
        # 60秒录音最大时长强行切断保护
        if self.record_seconds >= 60:
            self.stop_recording()
            QMessageBox.information(self, "录音提示", "已达到最大录音时长（60秒），系统已自动停止并开始转写分析。")
            return

        mins = self.record_seconds // 60
        secs = self.record_seconds % 60
        
        # 奇数秒显示红点，偶数秒显示灰点，呈现闪烁 REC 效果
        if self.record_seconds % 2 == 1:
            self.audio_path_label.setText(
                f"<html><span style='color: #e74c3c; font-weight: bold;'>🔴 录音中...</span> {mins:02d}:{secs:02d}</html>"
            )
        else:
            self.audio_path_label.setText(
                f"<html><span style='color: #7f8c8d; font-weight: bold;'>⚪ 录音中...</span> {mins:02d}:{secs:02d}</html>"
            )

    def stop_recording(self):
        """停止录音，将 PCM 数据加上 WAV 头转换格式，并自动触发转写"""
        import wave

        if self.audio_source:
            self.audio_source.stop()
            self.audio_source = None
        if self.temp_pcmfile:
            self.temp_pcmfile.close()
            self.temp_pcmfile = None
        if self.record_timer:
            self.record_timer.stop()

        # 还原交互状态
        self.select_audio_btn.setEnabled(True)
        self.start_record_btn.setEnabled(True)
        self.stop_record_btn.setEnabled(False)

        if not self.temp_pcm_path or not os.path.exists(self.temp_pcm_path):
            QMessageBox.critical(self, "错误", "未找到录音缓存数据！")
            return

        # 组装为标准的 WAV 文件以便 ASR 识别
        import tempfile
        self.temp_wav_path = tempfile.mktemp(suffix=".wav")
        try:
            with open(self.temp_pcm_path, 'rb') as pcm_f:
                pcm_data = pcm_f.read()
            
            if len(pcm_data) == 0:
                QMessageBox.warning(self, "录音警告", "未录制到任何有效的音频信号，请确保耳机/麦克风正常工作！")
                return

            with wave.open(self.temp_wav_path, 'wb') as wav_f:
                wav_f.setnchannels(1)       # 单声道
                wav_f.setsampwidth(2)       # Int16 -> 2 字节
                wav_f.setframerate(16000)   # 采样率 16000Hz
                wav_f.writeframes(pcm_data)

            self.audio_path_label.setText(f"录音分析成功！时长: {self.record_seconds}秒，已加载临时音频。")
            self.run_asr_process(self.temp_wav_path)
            
        except Exception as e:
            logger.exception("Failed to save and convert WAV audio")
            QMessageBox.critical(self, "错误", f"转换音频格式失败:\n{str(e)}")
        finally:
            # 清除 PCM 临时残留
            if self.temp_pcm_path and os.path.exists(self.temp_pcm_path):
                try:
                    os.remove(self.temp_pcm_path)
                except:
                    pass

    def clean_up_temp_files(self):
        """析构或窗口关闭时，确保删除全部临时生成的多媒体文件"""
        if self.audio_source:
            try:
                self.audio_source.stop()
            except:
                pass
            self.audio_source = None
        if self.temp_pcmfile:
            try:
                self.temp_pcmfile.close()
            except:
                pass
            self.temp_pcmfile = None
        if self.record_timer:
            self.record_timer.stop()

        for path in [self.temp_pcm_path, self.temp_wav_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass

    def reject(self):
        self.clean_up_temp_files()
        super().reject()

    def accept(self):
        self.clean_up_temp_files()
        super().accept()

    def start_ai_extraction(self):
        """提交给大模型进行自然语言提取"""
        text = self.summary_textedit.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "警告", "待分析的汇总文本不能为空!")
            return

        if not self.ai_generator:
            QMessageBox.critical(self, "错误", "AI 大模型提取器未初始化，请检查配置!")
            return

        self.status_label.setText("正在连接大模型分析并提取资产...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.analyze_btn.setEnabled(False)
        self.import_btn.setEnabled(False)

        self.ai_thread = AIExtractionThread(self.ai_generator, text)
        self.ai_thread.finished.connect(self.on_ai_extraction_finished)
        self.ai_thread.error.connect(self.on_ai_extraction_error)
        self.ai_thread.start()

    def on_ai_extraction_finished(self, results: list):
        self.analyze_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if not results:
            self.status_label.setText("分析完毕，大模型未发现有效的账号密码资产。")
            QMessageBox.information(self, "提示", "大模型未从该段文本中匹配出密码资产。")
            return

        self.status_label.setText(f"AI 成功提取了 {len(results)} 个密码资产！请在右侧双击表格单元格校对后再导入。")
        self.extracted_entries = results
        self.import_btn.setEnabled(True)

        # 填入预览表格
        self.preview_table.setRowCount(len(results))
        for row, item in enumerate(results):
            self.preview_table.setItem(row, 0, QTableWidgetItem(item.get("title", "未命名")))
            self.preview_table.setItem(row, 1, QTableWidgetItem(item.get("username", "未知")))
            self.preview_table.setItem(row, 2, QTableWidgetItem(item.get("password", "未提供")))
            self.preview_table.setItem(row, 3, QTableWidgetItem(item.get("url", "")))
            self.preview_table.setItem(row, 4, QTableWidgetItem(item.get("category", "其他")))
            self.preview_table.setItem(row, 5, QTableWidgetItem(item.get("notes", "")))

    def on_ai_extraction_error(self, err_msg: str):
        self.analyze_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("AI 智能分析提取失败。")
        QMessageBox.critical(self, "分析失败", f"AI 推理出错:\n{err_msg}")

    def start_batch_import(self):
        """开始顺序把校对好的行导入加密数据库中"""
        final_entries = []
        for row in range(self.preview_table.rowCount()):
            final_entries.append({
                "title": self.preview_table.item(row, 0).text().strip(),
                "username": self.preview_table.item(row, 1).text().strip(),
                "password": self.preview_table.item(row, 2).text(),
                "url": self.preview_table.item(row, 3).text().strip(),
                "category": self.preview_table.item(row, 4).text().strip(),
                "notes": self.preview_table.item(row, 5).text().strip(),
            })

        if not final_entries:
            return

        self.import_btn.setEnabled(False)
        self.analyze_btn.setEnabled(False)
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(final_entries))
        self.progress_bar.setValue(0)
        self.status_label.setText(f"开始导入密码... (0/{len(final_entries)})")

        self.import_thread = BatchImportThread(self.vault_manager, final_entries)
        self.import_thread.progress.connect(self.on_import_progress)
        self.import_thread.finished.connect(self.on_import_finished)
        self.import_thread.error.connect(self.on_import_error)
        self.import_thread.start()

    def on_import_progress(self, current: int, total: int):
        self.progress_bar.setValue(current)
        self.status_label.setText(f"正在导入密码并进行高强度 AES 加密... ({current}/{total})")

    def on_import_finished(self, count: int):
        self.progress_bar.setVisible(False)
        QMessageBox.information(self, "成功", f"恭喜！成功加密并导入了 {count} 个密码资产！")
        self.accept()

    def on_import_error(self, err_msg: str):
        self.import_btn.setEnabled(True)
        self.analyze_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("批量导入出错。")
        QMessageBox.critical(self, "导入失败", f"批量写入数据库失败:\n{err_msg}")


class UpdateThread(QThread):
    """后台执行在线检测更新与文件下载的线程"""
    check_finished = pyqtSignal(bool, str, str, str) # (has_update, new_version, download_url, changelog)
    check_error = pyqtSignal(str)
    
    download_progress = pyqtSignal(int)
    download_finished = pyqtSignal(str) # temp_zip_path
    download_error = pyqtSignal(str)

    def __init__(self, current_version: str, update_url: str):
        super().__init__()
        self.current_version = current_version
        self.update_url = update_url
        self.mode = "check" # "check" or "download"
        self.download_target_url = ""
        self.temp_zip_path = ""
        self.is_cancelled = False

    def run(self):
        if self.mode == "check":
            self.run_check()
        elif self.mode == "download":
            self.run_download()

    def run_check(self):
        import urllib.request
        import json
        import ssl
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            req = urllib.request.Request(
                self.update_url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
            )
            with urllib.request.urlopen(req, context=ctx, timeout=8) as response:
                data = json.loads(response.read().decode())
                
            tag_name = data.get("tag_name", "").strip()
            new_version = tag_name.lstrip("v")
            changelog = data.get("body", "无更新日志。")
            
            # 寻找适合当前平台(macOS/Windows)的更新压缩包
            import sys
            download_url = ""
            is_mac = sys.platform == "darwin"
            is_win = sys.platform == "win32"
            
            # 优先匹配特定平台的 zip 包 (如 密码管家_mac_dist.zip 或 _mac_dist.zip)
            for asset in data.get("assets", []):
                name = asset.get("name", "").lower()
                if is_mac and "mac" in name and name.endswith(".zip"):
                    download_url = asset.get("browser_download_url", "")
                    break
                elif is_win and "win" in name and name.endswith(".zip"):
                    download_url = asset.get("browser_download_url", "")
                    break
            
            # 如果没有找到精确的平台标识，则寻找任何 dist.zip 或 .zip 文件作为兜底
            if not download_url:
                for asset in data.get("assets", []):
                    name = asset.get("name", "").lower()
                    if "dist.zip" in name or name.endswith(".zip"):
                        download_url = asset.get("browser_download_url", "")
                        break
            
            if not download_url and data.get("assets"):
                download_url = data["assets"][0].get("browser_download_url", "")
                
            if not new_version:
                self.check_error.emit("未能解析到合法的版本号。")
                return
                
            def parse_ver(v_str):
                return tuple(map(int, (v_str.split("."))))
                
            try:
                curr_t = parse_ver(self.current_version)
                new_t = parse_ver(new_version)
                has_update = new_t > curr_t
            except Exception:
                has_update = new_version != self.current_version
                
            self.check_finished.emit(has_update, new_version, download_url, changelog)
            
        except Exception as e:
            self.check_error.emit(str(e))

    def run_download(self):
        import urllib.request
        import tempfile
        import ssl
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            self.temp_zip_path = tempfile.mktemp(suffix=".zip")
            req = urllib.request.Request(
                self.download_target_url,
                headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
            )
            
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                total_size = int(response.headers.get('content-length', 0))
                bytes_so_far = 0
                block_size = 8192
                
                with open(self.temp_zip_path, 'wb') as f:
                    while True:
                        if self.is_cancelled:
                            self.download_error.emit("下载已被用户取消。")
                            return
                        buffer = response.read(block_size)
                        if not buffer:
                            break
                        f.write(buffer)
                        bytes_so_far += len(buffer)
                        if total_size > 0:
                            percent = int(bytes_so_far * 100 / total_size)
                            self.download_progress.emit(percent)
                            
            self.download_finished.emit(self.temp_zip_path)
        except Exception as e:
            self.download_error.emit(str(e))


def main():
    """Main entry point for GUI application."""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # 全局设置应用程序图标，这是 macOS 更新 Dock 图标的关键
    icon_path = get_resource_path("password_manager/gui/app_icon.png")
    app.setWindowIcon(QIcon(icon_path))
    
    # macOS 专属：如果由于虚拟环境或 python 运行导致 Dock 图标无法刷新，通过 Cocoa 框架强制更新
    if sys.platform == 'darwin':
        try:
            import ctypes
            app_kit = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/AppKit.framework/AppKit')
            app_kit.NSApplicationLoad()
        except Exception:
            pass
    
    window = LoginWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()