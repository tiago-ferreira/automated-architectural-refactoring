"""Autenticação fail-closed para rotas administrativas (Padrão 11 do playbook)."""
import hmac
from functools import wraps
from flask import abort, request
from config.settings import Config, logger


def require_admin_token(view):
    """Exige o header `X-Admin-Token` igual a `ADMIN_API_TOKEN`; sem token configurado a rota fica desabilitada."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not Config.ADMIN_API_TOKEN:
            abort(404)
        provided = request.headers.get(Config.ADMIN_TOKEN_HEADER, "")
        if not hmac.compare_digest(provided.encode(), Config.ADMIN_API_TOKEN.encode()):
            logger.warning("Acesso administrativo negado em %s", request.path)
            abort(401)
        return view(*args, **kwargs)

    return wrapper
