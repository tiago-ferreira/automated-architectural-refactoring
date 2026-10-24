"""Tratamento centralizado de exceções HTTP e de aplicação."""
from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException
from config.settings import logger


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        return jsonify({"error": exc.description}), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected_exception(exc: Exception):
        logger.exception("Erro interno não tratado: %s", exc)
        return jsonify({"error": "Erro interno"}), 500
