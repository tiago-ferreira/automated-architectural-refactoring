"""Camada de Middlewares e tratamento centralizado de erros."""
from middlewares.error_handler import register_error_handlers

__all__ = ["register_error_handlers"]
