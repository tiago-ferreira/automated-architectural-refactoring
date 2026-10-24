"""Definição de rotas HTTP da API delegando exclusivamente aos Controllers."""
from flask import Blueprint, Flask
from controllers import (
    pedido_controller,
    produto_controller,
    usuario_controller,
)

api_bp = Blueprint("api", __name__)

# Rotas de Produtos
api_bp.add_url_rule("/produtos", "listar_produtos", produto_controller.listar_produtos, methods=["GET"])
api_bp.add_url_rule("/produtos/busca", "buscar_produtos", produto_controller.buscar_produtos, methods=["GET"])
api_bp.add_url_rule("/produtos/<int:id>", "buscar_produto", produto_controller.buscar_produto, methods=["GET"])
api_bp.add_url_rule("/produtos", "criar_produto", produto_controller.criar_produto, methods=["POST"])
api_bp.add_url_rule("/produtos/<int:id>", "atualizar_produto", produto_controller.atualizar_produto, methods=["PUT"])
api_bp.add_url_rule("/produtos/<int:id>", "deletar_produto", produto_controller.deletar_produto, methods=["DELETE"])

# Rotas de Usuários e Autenticação
api_bp.add_url_rule("/usuarios", "listar_usuarios", usuario_controller.listar_usuarios, methods=["GET"])
api_bp.add_url_rule("/usuarios/<int:id>", "buscar_usuario", usuario_controller.buscar_usuario, methods=["GET"])
api_bp.add_url_rule("/usuarios", "criar_usuario", usuario_controller.criar_usuario, methods=["POST"])
api_bp.add_url_rule("/login", "login", usuario_controller.login, methods=["POST"])

# Rotas de Pedidos e Relatórios
api_bp.add_url_rule("/pedidos", "criar_pedido", pedido_controller.criar_pedido, methods=["POST"])
api_bp.add_url_rule("/pedidos", "listar_todos_pedidos", pedido_controller.listar_todos_pedidos, methods=["GET"])
api_bp.add_url_rule("/pedidos/usuario/<int:usuario_id>", "listar_pedidos_usuario", pedido_controller.listar_pedidos_usuario, methods=["GET"])
api_bp.add_url_rule("/pedidos/<int:pedido_id>/status", "atualizar_status_pedido", pedido_controller.atualizar_status_pedido, methods=["PUT"])
api_bp.add_url_rule("/relatorios/vendas", "relatorio_vendas", pedido_controller.relatorio_vendas, methods=["GET"])

# Rotas de Sistema e Administração
api_bp.add_url_rule("/health", "health_check", pedido_controller.health_check, methods=["GET"])
api_bp.add_url_rule("/", "index", pedido_controller.index, methods=["GET"])
api_bp.add_url_rule("/admin/reset-db", "reset_database", pedido_controller.reset_database, methods=["POST"])
api_bp.add_url_rule("/admin/query", "executar_query", pedido_controller.executar_query, methods=["POST"])


def register_routes(app: Flask) -> None:
    app.register_blueprint(api_bp)
