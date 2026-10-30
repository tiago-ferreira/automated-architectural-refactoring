"""Configurações centralizadas da aplicação, constantes de domínio e logging."""
import logging
import os
import secrets

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ecommerce_api")


def _load_secret_key(environment: str) -> str:
    """Lê SECRET_KEY do ambiente; falha em produção se ausente e usa chave efêmera em dev."""
    secret_key = os.environ.get("SECRET_KEY", "").strip()
    if secret_key:
        return secret_key
    if environment in ("producao", "production"):
        raise RuntimeError("SECRET_KEY deve ser definida no ambiente quando APP_ENV=producao")
    logger.warning("SECRET_KEY não definida; usando chave aleatória efêmera para desenvolvimento")
    return secrets.token_hex(32)


class Config:
    """Configurações da aplicação carregadas via variáveis de ambiente."""

    ENVIRONMENT = os.environ.get("APP_ENV", "development").strip().lower()
    SECRET_KEY = _load_secret_key(ENVIRONMENT)
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1")
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    VERSION = "1.0.0"
    HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
    PORT = int(os.environ.get("FLASK_PORT", "5000"))

    # Rotas administrativas: vazio por padrão => rotas desabilitadas (fail-closed)
    ADMIN_API_TOKEN = os.environ.get("ADMIN_API_TOKEN", "")
    ADMIN_TOKEN_HEADER = "X-Admin-Token"

    # Constantes de validação de produtos
    MIN_PRODUCT_NAME_LENGTH = 2
    MAX_PRODUCT_NAME_LENGTH = 200
    DEFAULT_CATEGORY = "geral"
    VALID_CATEGORIES = (
        "informatica",
        "moveis",
        "vestuario",
        "geral",
        "eletronicos",
        "livros",
    )

    # Constantes de usuários
    DEFAULT_USER_ROLE = "cliente"

    # Constantes de pedidos e relatórios
    ORDER_STATUS_PENDENTE = "pendente"
    ORDER_STATUS_APROVADO = "aprovado"
    ORDER_STATUS_ENVIADO = "enviado"
    ORDER_STATUS_ENTREGUE = "entregue"
    ORDER_STATUS_CANCELADO = "cancelado"
    DEFAULT_ORDER_STATUS = ORDER_STATUS_PENDENTE
    VALID_ORDER_STATUSES = (
        ORDER_STATUS_PENDENTE,
        ORDER_STATUS_APROVADO,
        ORDER_STATUS_ENVIADO,
        ORDER_STATUS_ENTREGUE,
        ORDER_STATUS_CANCELADO,
    )

    # Faixas de desconto para relatório de vendas: (limite_faturamento, percentual_desconto)
    DISCOUNT_TIERS = (
        (10000.0, 0.10),
        (5000.0, 0.05),
        (1000.0, 0.02),
    )
