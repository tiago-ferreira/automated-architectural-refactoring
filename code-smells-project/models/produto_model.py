"""Model de Produtos com queries 100% parametrizadas."""
from typing import Any, Dict, List, Optional
from config.settings import get_db


def _row_to_produto_dict(row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


def get_todos_produtos() -> List[Dict[str, Any]]:
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos"
    )
    return [_row_to_produto_dict(row) for row in cursor.fetchall()]


def get_produto_por_id(produto_id: int) -> Optional[Dict[str, Any]]:
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em FROM produtos WHERE id = ?",
        (produto_id,),
    )
    row = cursor.fetchone()
    return _row_to_produto_dict(row) if row else None


def criar_produto(
    nome: str, descricao: str, preco: float, estoque: int, categoria: str
) -> int:
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cursor.lastrowid


def atualizar_produto(
    produto_id: int,
    nome: str,
    descricao: str,
    preco: float,
    estoque: int,
    categoria: str,
) -> bool:
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        UPDATE produtos
        SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ?
        WHERE id = ?
        """,
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()
    return True


def deletar_produto(produto_id: int) -> bool:
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()
    return True


def buscar_produtos(
    termo: str = "",
    categoria: Optional[str] = None,
    preco_min: Optional[float] = None,
    preco_max: Optional[float] = None,
) -> List[Dict[str, Any]]:
    db = get_db()
    cursor = db.cursor()

    query = (
        "SELECT id, nome, descricao, preco, estoque, categoria, ativo, criado_em "
        "FROM produtos WHERE 1=1"
    )
    params: List[Any] = []

    if termo:
        like_term = f"%{termo}%"
        query += " AND (nome LIKE ? OR descricao LIKE ?)"
        params.extend([like_term, like_term])
    if categoria:
        query += " AND categoria = ?"
        params.append(categoria)
    if preco_min is not None:
        query += " AND preco >= ?"
        params.append(preco_min)
    if preco_max is not None:
        query += " AND preco <= ?"
        params.append(preco_max)

    cursor.execute(query, tuple(params))
    return [_row_to_produto_dict(row) for row in cursor.fetchall()]
