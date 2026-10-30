"""Model de Pedidos e Relatórios com queries parametrizadas, transações atômicas e zero N+1."""
from typing import Any, Dict, List, Optional
from config.database import get_db
from config.settings import Config


def criar_pedido(usuario_id: int, itens: List[Dict[str, int]]) -> Dict[str, Any]:
    db = get_db()
    cursor = db.cursor()

    try:
        produtos_cache: Dict[int, Dict[str, Any]] = {}
        total = 0.0

        for item in itens:
            produto_id = item["produto_id"]
            quantidade = item["quantidade"]
            if produto_id not in produtos_cache:
                cursor.execute(
                    "SELECT id, nome, preco FROM produtos WHERE id = ?",
                    (produto_id,),
                )
                produto = cursor.fetchone()
                if produto is None:
                    db.rollback()
                    return {"erro": f"Produto {produto_id} não encontrado"}
                produtos_cache[produto_id] = {
                    "nome": produto["nome"],
                    "preco": float(produto["preco"]),
                }
            total += produtos_cache[produto_id]["preco"] * quantidade

        cursor.execute(
            "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
            (usuario_id, Config.DEFAULT_ORDER_STATUS, total),
        )
        pedido_id = int(cursor.lastrowid)

        for item in itens:
            produto_id = item["produto_id"]
            quantidade = item["quantidade"]
            produto_info = produtos_cache[produto_id]

            cursor.execute(
                "UPDATE produtos SET estoque = estoque - ? WHERE id = ? AND estoque >= ?",
                (quantidade, produto_id, quantidade),
            )
            if cursor.rowcount == 0:
                db.rollback()
                return {"erro": f"Estoque insuficiente para {produto_info['nome']}"}

            cursor.execute(
                """
                INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario)
                VALUES (?, ?, ?, ?)
                """,
                (pedido_id, produto_id, quantidade, produto_info["preco"]),
            )

        db.commit()
        return {"pedido_id": pedido_id, "total": total}
    except Exception:
        db.rollback()
        raise


def _carregar_pedidos_com_itens(
    filtro_usuario_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Carrega pedidos e seus respectivos itens em lote com LEFT JOIN (elimina N+1)."""
    cursor = get_db().cursor()

    if filtro_usuario_id is not None:
        cursor.execute(
            "SELECT id, usuario_id, status, total, criado_em FROM pedidos WHERE usuario_id = ?",
            (filtro_usuario_id,),
        )
    else:
        cursor.execute("SELECT id, usuario_id, status, total, criado_em FROM pedidos")

    pedidos_rows = cursor.fetchall()
    if not pedidos_rows:
        return []

    pedidos_map: Dict[int, Dict[str, Any]] = {}
    pedidos_list: List[Dict[str, Any]] = []

    for row in pedidos_rows:
        pedido_dict = {
            "id": row["id"],
            "usuario_id": row["usuario_id"],
            "status": row["status"],
            "total": row["total"],
            "criado_em": row["criado_em"],
            "itens": [],
        }
        pedidos_map[row["id"]] = pedido_dict
        pedidos_list.append(pedido_dict)

    placeholders = ",".join("?" for _ in pedidos_map)
    cursor.execute(
        f"""
        SELECT
            ip.pedido_id,
            ip.produto_id,
            COALESCE(p.nome, 'Desconhecido') AS produto_nome,
            ip.quantidade,
            ip.preco_unitario
        FROM itens_pedido ip
        LEFT JOIN produtos p ON p.id = ip.produto_id
        WHERE ip.pedido_id IN ({placeholders})
        ORDER BY ip.id
        """,
        tuple(pedidos_map.keys()),
    )

    for item_row in cursor.fetchall():
        pedido_alvo = pedidos_map.get(item_row["pedido_id"])
        if pedido_alvo is not None:
            pedido_alvo["itens"].append(
                {
                    "produto_id": item_row["produto_id"],
                    "produto_nome": item_row["produto_nome"],
                    "quantidade": item_row["quantidade"],
                    "preco_unitario": item_row["preco_unitario"],
                }
            )

    return pedidos_list


def get_pedidos_usuario(usuario_id: int) -> List[Dict[str, Any]]:
    return _carregar_pedidos_com_itens(filtro_usuario_id=usuario_id)


def get_todos_pedidos() -> List[Dict[str, Any]]:
    return _carregar_pedidos_com_itens(filtro_usuario_id=None)


def atualizar_status_pedido(pedido_id: int, novo_status: str) -> bool:
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        (novo_status, pedido_id),
    )
    db.commit()
    return cursor.rowcount > 0


def relatorio_vendas() -> Dict[str, Any]:
    cursor = get_db().cursor()
    cursor.execute(
        """
        SELECT
            COUNT(*) AS total_pedidos,
            COALESCE(SUM(total), 0) AS faturamento,
            SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS pendentes,
            SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS aprovados,
            SUM(CASE WHEN status = ? THEN 1 ELSE 0 END) AS cancelados
        FROM pedidos
        """,
        (
            Config.ORDER_STATUS_PENDENTE,
            Config.ORDER_STATUS_APROVADO,
            Config.ORDER_STATUS_CANCELADO,
        ),
    )
    row = cursor.fetchone()
    total_pedidos = row["total_pedidos"] or 0
    faturamento = float(row["faturamento"] or 0.0)
    pendentes = row["pendentes"] or 0
    aprovados = row["aprovados"] or 0
    cancelados = row["cancelados"] or 0

    desconto = 0.0
    for limite, percentual in Config.DISCOUNT_TIERS:
        if faturamento > limite:
            desconto = faturamento * percentual
            break

    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "desconto_aplicavel": round(desconto, 2),
        "faturamento_liquido": round(faturamento - desconto, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
        "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
    }
