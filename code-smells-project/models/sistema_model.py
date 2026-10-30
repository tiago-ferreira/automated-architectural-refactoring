"""Model de operações de sistema: verificação de conectividade, contagens e reset administrativo."""
from typing import Dict
from config.database import get_db


def ping_database() -> None:
    """Executa uma consulta mínima para validar conectividade com o SQLite."""
    cursor = get_db().cursor()
    cursor.execute("SELECT 1")
    cursor.fetchone()


def get_database_counts() -> Dict[str, int]:
    cursor = get_db().cursor()
    cursor.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM produtos) AS produtos,
            (SELECT COUNT(*) FROM usuarios) AS usuarios,
            (SELECT COUNT(*) FROM pedidos) AS pedidos
        """
    )
    row = cursor.fetchone()
    return {
        "produtos": row["produtos"],
        "usuarios": row["usuarios"],
        "pedidos": row["pedidos"],
    }


def reset_all_tables() -> None:
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute("DELETE FROM itens_pedido")
        cursor.execute("DELETE FROM pedidos")
        cursor.execute("DELETE FROM produtos")
        cursor.execute("DELETE FROM usuarios")
        db.commit()
    except Exception:
        db.rollback()
        raise
