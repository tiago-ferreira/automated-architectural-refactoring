"""Camada de Controllers (MVC) do projeto de E-commerce."""
from controllers.produto_controller import (
    listar_produtos,
    buscar_produto,
    criar_produto,
    atualizar_produto,
    deletar_produto,
    buscar_produtos,
)
from controllers.usuario_controller import (
    listar_usuarios,
    buscar_usuario,
    criar_usuario,
    login,
)
from controllers.pedido_controller import (
    criar_pedido,
    listar_pedidos_usuario,
    listar_todos_pedidos,
    atualizar_status_pedido,
    relatorio_vendas,
    health_check,
    index,
    reset_database,
    executar_query,
)

__all__ = [
    "listar_produtos",
    "buscar_produto",
    "criar_produto",
    "atualizar_produto",
    "deletar_produto",
    "buscar_produtos",
    "listar_usuarios",
    "buscar_usuario",
    "criar_usuario",
    "login",
    "criar_pedido",
    "listar_pedidos_usuario",
    "listar_todos_pedidos",
    "atualizar_status_pedido",
    "relatorio_vendas",
    "health_check",
    "index",
    "reset_database",
    "executar_query",
]
