"""Controller de Usuários e Autenticação."""
import sqlite3
from typing import Any, Dict, Tuple
from flask import jsonify, request
from itsdangerous import URLSafeTimedSerializer
from config.settings import Config, logger
from models import usuario_model


def _gerar_token_sessao(usuario: Dict[str, Any]) -> str:
    serializer = URLSafeTimedSerializer(Config.SECRET_KEY, salt="ecommerce-auth")
    return serializer.dumps({"user_id": usuario["id"], "tipo": usuario["tipo"]})


def listar_usuarios() -> Tuple[Any, int]:
    usuarios = usuario_model.get_todos_usuarios()
    return jsonify({"dados": usuarios, "sucesso": True}), 200


def buscar_usuario(usuario_id: int) -> Tuple[Any, int]:
    usuario = usuario_model.get_usuario_por_id(usuario_id)
    if usuario:
        return jsonify({"dados": usuario, "sucesso": True}), 200
    return jsonify({"erro": "Usuário não encontrado", "sucesso": False}), 404


def criar_usuario() -> Tuple[Any, int]:
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or not dados:
        return jsonify({"erro": "Dados inválidos", "sucesso": False}), 400

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not isinstance(nome, str) or not isinstance(email, str) or not isinstance(senha, str):
        return jsonify({"erro": "Nome, email e senha devem ser texto", "sucesso": False}), 400

    nome = nome.strip()
    email = email.strip().lower()
    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha são obrigatórios", "sucesso": False}), 400

    if usuario_model.email_ja_cadastrado(email):
        return jsonify({"erro": "Email já cadastrado", "sucesso": False}), 409

    try:
        usuario_id = usuario_model.criar_usuario(nome, email, senha)
    except sqlite3.IntegrityError:
        return jsonify({"erro": "Email já cadastrado", "sucesso": False}), 409

    logger.info("Usuário criado: %s", email)
    return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201


def login() -> Tuple[Any, int]:
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict) or not dados:
        return jsonify({"erro": "Dados inválidos", "sucesso": False}), 400

    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not isinstance(email, str) or not isinstance(senha, str):
        return jsonify({"erro": "Email e senha inválidos", "sucesso": False}), 400

    email = email.strip()
    if not email or not senha:
        return jsonify({"erro": "Email e senha são obrigatórios", "sucesso": False}), 400

    usuario = usuario_model.login_usuario(email, senha)
    if usuario:
        token = _gerar_token_sessao(usuario)
        logger.info("Login bem-sucedido: %s", email)
        return (
            jsonify(
                {
                    "dados": usuario,
                    "token": token,
                    "sucesso": True,
                    "mensagem": "Login OK",
                }
            ),
            200,
        )

    logger.warning("Login falhou: %s", email)
    return jsonify({"erro": "Email ou senha inválidos", "sucesso": False}), 401
