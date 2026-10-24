"""Pacote de rotas HTTP (Camada View/Routes do MVC)."""
from routes.category_routes import category_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp

__all__ = ["task_bp", "user_bp", "category_bp", "report_bp"]
