"""Controller de sistema: index, health check público/administrativo e reset do banco."""
from typing import Any, Tuple
from flask import jsonify
from config.settings import Config, logger
from models import sistema_model


def health_check() -> Tuple[Any, int]:
    sistema_model.ping_database()
    return jsonify({"status": "ok", "database": "connected", "versao": Config.VERSION}), 200


def admin_health_check() -> Tuple[Any, int]:
    counts = sistema_model.get_database_counts()
    return (
        jsonify(
            {
                "status": "ok",
                "database": "connected",
                "versao": Config.VERSION,
                "ambiente": Config.ENVIRONMENT,
                "counts": counts,
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
    sistema_model.reset_all_tables()
    logger.warning("Banco de dados resetado via rota administrativa")
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200
