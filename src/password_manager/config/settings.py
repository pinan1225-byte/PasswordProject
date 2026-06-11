"""Application settings and configuration management."""

import os
import sys
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def get_env_file_path() -> str:
    """Get the absolute path to the .env file, supporting PyInstaller freeze environment."""
    default_env = ".env"
    
    # Check if we are running in a PyInstaller bundle
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        
        # 1. Try inside Contents/MacOS/
        candidate1 = os.path.join(exe_dir, ".env")
        if os.path.exists(candidate1):
            return candidate1
            
        # 2. Try alongside the .app bundle (three directories up from Contents/MacOS)
        # exe_dir = /Path/To/PasswordManager.app/Contents/MacOS
        # Contents/MacOS -> Contents -> PasswordManager.app -> Parent Directory
        app_dir = os.path.dirname(os.path.dirname(os.path.dirname(exe_dir)))
        candidate2 = os.path.join(app_dir, ".env")
        if os.path.exists(candidate2):
            return candidate2
            
        # 3. Try user's home directory ~/.password_manager/.env
        home_dir = os.path.expanduser("~")
        candidate3 = os.path.join(home_dir, ".password_manager", ".env")
        if os.path.exists(candidate3):
            return candidate3
            
        # 4. Try inside PyInstaller temporary folder (packaged inside .app)
        if hasattr(sys, "_MEIPASS"):
            candidate4 = os.path.join(sys._MEIPASS, ".env")
            if os.path.exists(candidate4):
                return candidate4
            
        return candidate2
    else:
        # Developer mode path fallback: if no .env in current cwd, look up to the project root
        if not os.path.exists(default_env):
            project_root = os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            )
            candidate_dev = os.path.join(project_root, ".env")
            if os.path.exists(candidate_dev):
                return candidate_dev
        return default_env


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=get_env_file_path(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )



    DATABASE_URL: Optional[str] = Field(default=None, description="Database URL (SQLite or MySQL)")
    MYSQL_HOST: str = Field(default="localhost", description="MySQL host")
    MYSQL_PORT: int = Field(default=3306, description="MySQL port")
    MYSQL_USER: str = Field(default="root", description="MySQL user")
    MYSQL_PASSWORD: str = Field(default="", description="MySQL password")
    MYSQL_DATABASE: str = Field(default="password_manager", description="MySQL database name")

    ENVIRONMENT: str = Field(default="development", description="Environment name")
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")

    ENCRYPTION_ITERATIONS: int = Field(
        default=100000, description="PBKDF2 iterations for key derivation"
    )
    AES_KEY_SIZE: int = Field(default=32, description="AES key size in bytes (32 for AES-256)")
    SALT_SIZE: int = Field(default=16, description="Salt size in bytes")

    SESSION_TIMEOUT: int = Field(default=300, description="Session timeout in seconds")
    MAX_LOGIN_ATTEMPTS: int = Field(default=5, description="Maximum login attempts before lockout")

    # Auto-Update Configuration
    CURRENT_VERSION: str = Field(default="1.0.7", description="Current client version")
    UPDATE_URL: str = Field(
        default="https://api.github.com/repos/pinan1225-byte/PasswordProject/releases/latest",
        description="Update check endpoint"
    )

    # LLM Configuration
    LLM_PROVIDER: str = Field(
        default="openai", description="LLM provider (e.g., 'openai', 'doubao')"
    )
    LLM_MODEL: str = Field(
        default="gpt-3.5-turbo", description="Model name (e.g., 'gpt-3.5-turbo', 'deepseek-v3-250324')"
    )
    LLM_API_KEY: Optional[str] = Field(
        default=None, description="API key for LLM provider"
    )
    LLM_BASE_URL: Optional[str] = Field(
        default=None, description="Base URL for LLM API (optional, defaults to provider's official URL)"
    )
    LLM_SSL_VERIFY: bool = Field(
        default=True, description="Whether to verify SSL certificates for LLM client"
    )

    @field_validator("LOG_LEVEL")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"LOG_LEVEL must be one of {allowed_levels}")
        return v.upper()

    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment name."""
        allowed_envs = ["development", "staging", "production", "testing"]
        if v.lower() not in allowed_envs:
            raise ValueError(f"ENVIRONMENT must be one of {allowed_envs}")
        return v.lower()

    @field_validator("LLM_PROVIDER")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider."""
        allowed_providers = ["openai", "doubao", "custom", "senseauto"]
        if v.lower() not in allowed_providers:
            raise ValueError(f"LLM_PROVIDER must be one of {allowed_providers}")
        return v.lower()

    @property
    def database_url(self) -> str:
        """Construct database URL, prioritizing DATABASE_URL from env if set."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
            f"?charset=utf8mb4"
        )

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    @property
    def llm_api_key(self) -> Optional[str]:
        """Get LLM API key."""
        return self.LLM_API_KEY

    @property
    def llm_base_url(self) -> Optional[str]:
        """Get LLM base URL."""
        return self.LLM_BASE_URL

    @property
    def llm_model_name(self) -> str:
        """Get LLM model name."""
        return self.LLM_MODEL


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
