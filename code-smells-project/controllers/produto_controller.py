"""Controller de Produtos: valida entradas e coordena o ProdutoModel."""
from typing import Any, Dict, Optional, Tuple
from flask import jsonify, request
from config.settings import Config, logger
from models import produto_model


def _is_valid_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float))


def _is_valid_int(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, int)


def _validar_payload_produto(
    dados: Optional[Dict[str, Any]], validar_tamanho_e_categoria: bool = True
) -> Optional[str]:
    if not isinstance(dados, dict) or not dados:
        return "Dados inválidos"
    if "nome" not in dados:
        return "Nome é obrigatório"
    if "preco" not in dados:
        return "Preço é obrigatório"
    if "estoque" not in dados:
        return "Estoque é obrigatório"

    nome = dados["nome"]
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", Config.DEFAULT_CATEGORY)

    if not isinstance(nome, str) or not isinstance(categoria, str):
        return "Nome e categoria devem ser texto"
    if not _is_valid_number(preco):
        return "Preço deve ser numérico"
    if not _is_valid_int(estoque):
        return "Estoque deve ser um número inteiro"
    if preco < 0:
        return "Preço não pode ser negativo"
    if estoque < 0:
        return "Estoque não pode ser negativo"

    if validar_tamanho_e_categoria:
        if len(nome.strip()) < Config.MIN_PRODUCT_NAME_LENGTH:
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


def buscar_produto(produto_id: int) -> Tuple[Any, int]:
    produto = produto_model.get_produto_por_id(produto_id)
    if produto:
        return jsonify({"dados": produto, "sucesso": True}), 200
    return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404


def criar_produto() -> Tuple[Any, int]:
    dados = request.get_json(silent=True)
    erro = _validar_payload_produto(dados, validar_tamanho_e_categoria=True)
    if erro:
        return jsonify({"erro": erro, "sucesso": False}), 400

    produto_id = produto_model.criar_produto(
        nome=dados["nome"].strip(),
        descricao=str(dados.get("descricao", "")),
        preco=float(dados["preco"]),
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


def atualizar_produto(produto_id: int) -> Tuple[Any, int]:
    produto_existente = produto_model.get_produto_por_id(produto_id)
    if not produto_existente:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404

    dados = request.get_json(silent=True)
    erro = _validar_payload_produto(dados, validar_tamanho_e_categoria=False)
    if erro:
        return jsonify({"erro": erro, "sucesso": False}), 400

    produto_model.atualizar_produto(
        produto_id=produto_id,
        nome=dados["nome"].strip(),
        descricao=str(dados.get("descricao", "")),
        preco=float(dados["preco"]),
        estoque=dados["estoque"],
        categoria=dados.get("categoria", Config.DEFAULT_CATEGORY),
    )
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar_produto(produto_id: int) -> Tuple[Any, int]:
    produto = produto_model.get_produto_por_id(produto_id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404

    produto_model.deletar_produto(produto_id)
    logger.info("Produto %d deletado", produto_id)
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
        return jsonify({"erro": "Parâmetros de preço inválidos", "sucesso": False}), 400

    resultados = produto_model.buscar_produtos(termo, categoria, preco_min, preco_max)
    return (
        jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}),
        200,
    )
