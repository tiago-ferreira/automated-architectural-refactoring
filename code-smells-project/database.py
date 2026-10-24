"""Módulo de acesso ao banco de dados delegando para config.settings."""
from config.settings import get_db, close_db, init_db

__all__ = ["get_db", "close_db", "init_db"]
