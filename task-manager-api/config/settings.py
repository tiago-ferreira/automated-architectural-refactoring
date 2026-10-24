"""Configurações centralizadas, constantes de domínio e utilitários de tempo UTC."""
from datetime import datetime, timezone
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("task_manager_api")


def utc_now() -> datetime:
    """Retorna o datetime UTC atual usando a API moderna timezone-aware (Python 3.12+) normalizado para SQLite."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Config:
    """Configurações da aplicação lidas de variáveis de ambiente."""

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///tasks.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get(
        "SECRET_KEY", "dev-task-manager-secret-configured-via-env"
    )
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1")
    HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
    PORT = int(os.environ.get("FLASK_PORT", "5000"))

    # Configurações SMTP via variáveis de ambiente (sem credenciais hardcoded)
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")

    # Constantes de domínio e validação
    VALID_STATUSES = ("pending", "in_progress", "done", "cancelled")
    TERMINAL_STATUSES = ("done", "cancelled")
    VALID_ROLES = ("user", "admin", "manager")
    MIN_TITLE_LENGTH = 3
    MAX_TITLE_LENGTH = 200
    MIN_PASSWORD_LENGTH = 4
    MIN_PRIORITY = 1
    MAX_PRIORITY = 5
    HIGH_PRIORITY_THRESHOLD = 2
    DEFAULT_PRIORITY = 3
    DEFAULT_STATUS = "pending"
    DEFAULT_ROLE = "user"
    DEFAULT_COLOR = "#000000"
    RECENT_ACTIVITY_DAYS = 7
