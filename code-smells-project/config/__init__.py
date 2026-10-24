"""Pacote de configuração do projeto."""
from config.settings import Config, get_db, close_db, init_db

__all__ = ["Config", "get_db", "close_db", "init_db"]
