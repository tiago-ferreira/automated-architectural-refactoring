"""Controller de Pedidos, Relatórios de Vendas e Operações Administrativas."""
from typing import Any, Tuple
from flask import jsonify, request
from config.settings import Config, logger
from models import pedido_model


def criar_pedido() -> Tuple[Any, int]:
    dados = request.get_json(silent=True)
    if not dados:
        return jsonify({"erro": "Dados inválidos"}), 400

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        return jsonify({"erro": "Usuario ID é obrigatório"}), 400
    if not itens or len(itens) == 0:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400

    resultado = pedido_model.criar_pedido(usuario_id, itens)
    if "erro" in resultado:
        return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

    logger.info(
        "Pedido %s criado para usuario %s", resultado["pedido_id"], usuario_id
    )
    return (
        jsonify(
            {
                "dados": resultado,
                "sucesso": True,
                "mensagem": "Pedido criado com sucesso",
            }
        ),
        201,
    )


def listar_pedidos_usuario(usuario_id: int) -> Tuple[Any, int]:
    pedidos = pedido_model.get_pedidos_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_todos_pedidos() -> Tuple[Any, int]:
    pedidos = pedido_model.get_todos_pedidos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status_pedido(pedido_id: int) -> Tuple[Any, int]:
    dados = request.get_json(silent=True) or {}
    novo_status = dados.get("status", "")

    if novo_status not in Config.VALID_ORDER_STATUSES:
        return jsonify({"erro": "Status inválido"}), 400

    pedido_model.atualizar_status_pedido(pedido_id, novo_status)
    logger.info("Pedido %d atualizado para status '%s'", pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


def relatorio_vendas() -> Tuple[Any, int]:
    relatorio = pedido_model.relatorio_vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200


def health_check() -> Tuple[Any, int]:
    counts = pedido_model.get_database_counts()
    return (
        jsonify(
            {
                "status": "ok",
                "database": "connected",
                "counts": counts,
                "versao": Config.VERSION,
                "ambiente": Config.ENVIRONMENT,
                "db_path": Config.DB_PATH,
                "debug": Config.DEBUG,
            }
        ),
        200,
    )


def index() -> Tuple[Any, int]:
    return (
        jsonify(
            {
                "mensagem": "Bem-vindo à API da Loja",
                "versao": Config.VERSION,
                "endpoints": {
                    "produtos": "/produtos",
                    "usuarios": "/usuarios",
                    "pedidos": "/pedidos",
                    "login": "/login",
                    "relatorios": "/relatorios/vendas",
                    "health": "/health",
                },
            }
        ),
        200,
    )


def reset_database() -> Tuple[Any, int]:
    pedido_model.reset_all_tables()
    logger.warning("Banco de dados resetado via rota administrativa")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


def executar_query() -> Tuple[Any, int]:
    dados = request.get_json(silent=True) or {}
    query = dados.get("sql", "")
    if not query:
        return jsonify({"erro": "Query não informada"}), 400

    try:
        result = pedido_model.executar_query_segura(query)
        return jsonify({"dados": result, "sucesso": True}), 200
    except PermissionError as exc:
        return jsonify({"erro": str(exc), "sucesso": False}), 403
    except ValueError as exc:
        return jsonify({"erro": str(exc), "sucesso": False}), 400
