"""Controller de Pedidos e Relatórios de Vendas."""
from typing import Any, Dict, List, Optional, Tuple
from flask import jsonify, request
from config.settings import Config, logger
from models import pedido_model, usuario_model


def _is_positive_int(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value > 0


def _validar_itens_pedido(itens: Any) -> Tuple[Optional[List[Dict[str, int]]], Optional[str]]:
    if not isinstance(itens, list) or len(itens) == 0:
        return None, "Pedido deve ter pelo menos 1 item"

    itens_limpos: List[Dict[str, int]] = []
    for item in itens:
        if not isinstance(item, dict):
            return None, "Formato de item inválido"
        produto_id = item.get("produto_id")
        quantidade = item.get("quantidade")
        if not _is_positive_int(produto_id):
            return None, "produto_id deve ser um inteiro positivo"
        if not _is_positive_int(quantidade):
            return None, "quantidade deve ser um inteiro positivo"
        itens_limpos.append({"produto_id": produto_id, "quantidade": quantidade})

    return itens_limpos, None


def criar_pedido() -> Tuple[Any, int]:
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or not dados:
        return jsonify({"erro": "Dados inválidos", "sucesso": False}), 400

    usuario_id = dados.get("usuario_id")
    if not _is_positive_int(usuario_id):
        return jsonify({"erro": "Usuario ID inválido", "sucesso": False}), 400

    itens_validados, erro_itens = _validar_itens_pedido(dados.get("itens"))
    if erro_itens or itens_validados is None:
        return jsonify({"erro": erro_itens, "sucesso": False}), 400

    if not usuario_model.get_usuario_por_id(usuario_id):
        return jsonify({"erro": "Usuário não encontrado", "sucesso": False}), 404

    resultado = pedido_model.criar_pedido(usuario_id, itens_validados)
    if "erro" in resultado:
        return jsonify({"erro": resultado["erro"], "sucesso": False}), 400

    logger.info("Pedido %s criado para usuario %s", resultado["pedido_id"], usuario_id)
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
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return jsonify({"erro": "Dados inválidos", "sucesso": False}), 400

    novo_status = dados.get("status", "")
    if novo_status not in Config.VALID_ORDER_STATUSES:
        return jsonify({"erro": "Status inválido", "sucesso": False}), 400

    atualizado = pedido_model.atualizar_status_pedido(pedido_id, novo_status)
    if not atualizado:
        return jsonify({"erro": "Pedido não encontrado", "sucesso": False}), 404

    logger.info("Pedido %d atualizado para status '%s'", pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


def relatorio_vendas() -> Tuple[Any, int]:
    relatorio = pedido_model.relatorio_vendas()
    return jsonify({"dados": relatorio, "sucesso": True}), 200
