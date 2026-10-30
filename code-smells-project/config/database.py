"""Ciclo de vida da conexão SQLite (por requisição), schema, seed e migração de senhas legadas."""
import sqlite3
from flask import g, has_app_context
from werkzeug.security import generate_password_hash
from config.settings import Config, logger

PASSWORD_HASH_PREFIXES = ("scrypt:", "pbkdf2:")

_SCHEMA_STATEMENTS = (
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
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
)

_SEED_PRODUTOS = (
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
)

_SEED_USUARIOS = (
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
)


def _create_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _seed_if_empty(cursor: sqlite3.Cursor) -> None:
    cursor.execute("SELECT COUNT(*) FROM produtos")
    if cursor.fetchone()[0] > 0:
        return
    cursor.executemany(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        _SEED_PRODUTOS,
    )
    cursor.executemany(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        [(nome, email, generate_password_hash(senha), tipo) for nome, email, senha, tipo in _SEED_USUARIOS],
    )


def _migrate_plaintext_passwords(cursor: sqlite3.Cursor) -> None:
    """Converte senhas em texto puro herdadas do sistema legado para hash seguro."""
    cursor.execute("SELECT id, senha FROM usuarios WHERE senha IS NOT NULL")
    legados = [row for row in cursor.fetchall() if not row["senha"].startswith(PASSWORD_HASH_PREFIXES)]
    for row in legados:
        cursor.execute(
            "UPDATE usuarios SET senha = ? WHERE id = ?",
            (generate_password_hash(row["senha"]), row["id"]),
        )
    if legados:
        logger.warning("%d senha(s) legada(s) em texto puro migrada(s) para hash", len(legados))


def _ensure_unique_email_index(cursor: sqlite3.Cursor) -> None:
    try:
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email)")
    except sqlite3.IntegrityError:
        logger.warning("E-mails duplicados existentes impedem o índice UNIQUE em usuarios.email")


def init_db() -> None:
    """Cria schema, aplica seed inicial e migrações. Executado uma única vez no boot."""
    conn = _create_connection()
    try:
        cursor = conn.cursor()
        for statement in _SCHEMA_STATEMENTS:
            cursor.execute(statement)
        _seed_if_empty(cursor)
        _migrate_plaintext_passwords(cursor)
        _ensure_unique_email_index(cursor)
        conn.commit()
    finally:
        conn.close()


def get_db() -> sqlite3.Connection:
    """Retorna a conexão SQLite do contexto da aplicação atual (`flask.g`)."""
    if not has_app_context():
        raise RuntimeError("get_db() requer um contexto de aplicação Flask ativo")
    if "db" not in g:
        g.db = _create_connection()
    return g.db


def close_db(exception=None) -> None:
    """Fecha a conexão SQLite ao final do ciclo da requisição."""
    db = g.pop("db", None)
    if db is not None:
        db.close()
