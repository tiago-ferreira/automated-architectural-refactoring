"""Controller de Produtos: valida entradas e coordena o ProdutoModel."""
from typing import Any, Dict, Optional, Tuple
from flask import jsonify, request
from config.settings import Config, logger
from models import produto_model


def _validar_payload_produto(
    dados: Optional[Dict[str, Any]], validar_tamanho_e_categoria: bool = True
) -> Optional[str]:
    if not dados:
        return "Dados inválidos"
    if "nome" not in dados:
        return "Nome é obrigatório"
    if "preco" not in dados:
        return "Preço é obrigatório"
    if "estoque" not in dados:
        return "Estoque é obrigatório"

    preco = dados["preco"]
    estoque = dados["estoque"]
    nome = str(dados["nome"])
    categoria = dados.get("categoria", Config.DEFAULT_CATEGORY)

    if preco < 0:
        return "Preço não pode ser negativo"
    if estoque < 0:
        return "Estoque não pode ser negativo"

    if validar_tamanho_e_categoria:
        if len(nome) < Config.MIN_PRODUCT_NAME_LENGTH:
            return "Nome muito curto"
        if len(nome) > Config.MAX_PRODUCT_NAME_LENGTH:
            return "Nome muito longo"
        if categoria not in Config.VALID_CATEGORIES:
            return f"Categoria inválida. Válidas: {list(Config.VALID_CATEGORIES)}"

    return None


def listar_produtos() -> Tuple[Any, int]:
    produtos = produto_model.get_todos_produtos()
    logger.info("Listando %d produtos", len(produtos))
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_produto(id: int) -> Tuple[Any, int]:
    produto = produto_model.get_produto_por_id(id)
    if produto:
        return jsonify({"dados": produto, "sucesso": True}), 200
    return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404


def criar_produto() -> Tuple[Any, int]:
    dados = request.get_json(silent=True)
    erro = _validar_payload_produto(dados, validar_tamanho_e_categoria=True)
    if erro:
        return jsonify({"erro": erro}), 400

    produto_id = produto_model.criar_produto(
        nome=dados["nome"],
        descricao=dados.get("descricao", ""),
        preco=dados["preco"],
        estoque=dados["estoque"],
        categoria=dados.get("categoria", Config.DEFAULT_CATEGORY),
    )
    logger.info("Produto criado com ID: %d", produto_id)
    return (
        jsonify(
            {"dados": {"id": produto_id}, "sucesso": True, "mensagem": "Produto criado"}
        ),
        201,
    )


def atualizar_produto(id: int) -> Tuple[Any, int]:
    produto_existente = produto_model.get_produto_por_id(id)
    if not produto_existente:
        return jsonify({"erro": "Produto não encontrado"}), 404

    dados = request.get_json(silent=True)
    erro = _validar_payload_produto(dados, validar_tamanho_e_categoria=False)
    if erro:
        return jsonify({"erro": erro}), 400

    produto_model.atualizar_produto(
        produto_id=id,
        nome=dados["nome"],
        descricao=dados.get("descricao", ""),
        preco=dados["preco"],
        estoque=dados["estoque"],
        categoria=dados.get("categoria", Config.DEFAULT_CATEGORY),
    )
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(id: int) -> Tuple[Any, int]:
    produto = produto_model.get_produto_por_id(id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado"}), 404

    produto_model.deletar_produto(id)
    logger.info("Produto %d deletado", id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar_produtos() -> Tuple[Any, int]:
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria", None)
    preco_min_raw = request.args.get("preco_min", None)
    preco_max_raw = request.args.get("preco_max", None)

    try:
        preco_min = float(preco_min_raw) if preco_min_raw else None
        preco_max = float(preco_max_raw) if preco_max_raw else None
    except ValueError:
        return jsonify({"erro": "Parâmetros de preço inválidos"}), 400

    resultados = produto_model.buscar_produtos(termo, categoria, preco_min, preco_max)
    return (
        jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}),
        200,
    )
