"""Configurações centralizadas, constantes de domínio e gerenciamento de conexão SQLite."""
import logging
import os
import sqlite3
from flask import g, has_app_context
from werkzeug.security import generate_password_hash

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("ecommerce_api")


class Config:
    """Configurações da aplicação carregadas via variáveis de ambiente."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-configured-via-env")
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1")
    DB_PATH = os.environ.get("DB_PATH", "loja.db")
    ENVIRONMENT = os.environ.get("APP_ENV", "producao")
    VERSION = "1.0.0"
    HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
    PORT = int(os.environ.get("FLASK_PORT", "5000"))

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

    # Constantes de pedidos e relatórios
    DEFAULT_USER_ROLE = "cliente"
    DEFAULT_ORDER_STATUS = "pendente"
    VALID_ORDER_STATUSES = (
        "pendente",
        "aprovado",
        "enviado",
        "entregue",
        "cancelado",
    )

    # Faixas de desconto para relatório de vendas: (limite_faturamento, percentual_desconto)
    DISCOUNT_TIERS = (
        (10000.0, 0.10),
        (5000.0, 0.05),
        (1000.0, 0.02),
    )


_standalone_conn = None
_schema_initialized_for = None


def _create_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_schema_and_seed(conn: sqlite3.Connection) -> None:
    global _schema_initialized_for
    db_abs_path = os.path.abspath(Config.DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            descricao TEXT,
            preco REAL,
            estoque INTEGER,
            categoria TEXT,
            ativo INTEGER DEFAULT 1,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT,
            senha TEXT,
            tipo TEXT DEFAULT 'cliente',
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            status TEXT DEFAULT 'pendente',
            total REAL,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER,
            preco_unitario REAL
        )
        """
    )
    conn.commit()

    if _schema_initialized_for != db_abs_path:
        cursor.execute("SELECT COUNT(*) FROM produtos")
        if cursor.fetchone()[0] == 0:
            produtos = [
                ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
                ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
                ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
                ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
                ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
                ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
                ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
                ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
                ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
                ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
            ]
            cursor.executemany(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                produtos,
            )

            usuarios = [
                ("Admin", "admin@loja.com", generate_password_hash("admin123"), "admin"),
                ("João Silva", "joao@email.com", generate_password_hash("123456"), "cliente"),
                ("Maria Santos", "maria@email.com", generate_password_hash("senha123"), "cliente"),
            ]
            cursor.executemany(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                usuarios,
            )
            conn.commit()
        _schema_initialized_for = db_abs_path


def get_db() -> sqlite3.Connection:
    """Retorna uma conexão SQLite associada ao contexto da requisição atual (`flask.g`)."""
    global _standalone_conn
    if has_app_context():
        if "db" not in g:
            conn = _create_connection()
            _ensure_schema_and_seed(conn)
            g.db = conn
        return g.db

    if _standalone_conn is None:
        _standalone_conn = _create_connection()
        _ensure_schema_and_seed(_standalone_conn)
    return _standalone_conn


def close_db(exception=None) -> None:
    """Fecha a conexão SQLite ao final do ciclo da requisição."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """Inicializa o schema e seed inicial do banco de dados."""
    conn = _create_connection()
    try:
        _ensure_schema_and_seed(conn)
    finally:
        conn.close()
