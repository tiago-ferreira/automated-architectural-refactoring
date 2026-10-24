"""Camada de Models (MVC) do projeto de E-commerce."""
from models.produto_model import (
    get_todos_produtos,
    get_produto_por_id,
    criar_produto,
    atualizar_produto,
    deletar_produto,
    buscar_produtos,
)
from models.usuario_model import (
    get_todos_usuarios,
    get_usuario_por_id,
    login_usuario,
    criar_usuario,
)
from models.pedido_model import (
    criar_pedido,
    get_pedidos_usuario,
    get_todos_pedidos,
    relatorio_vendas,
    atualizar_status_pedido,
    get_database_counts,
    reset_all_tables,
    executar_query_segura,
)

__all__ = [
    "get_todos_produtos",
    "get_produto_por_id",
    "criar_produto",
    "atualizar_produto",
    "deletar_produto",
    "buscar_produtos",
    "get_todos_usuarios",
    "get_usuario_por_id",
    "login_usuario",
    "criar_usuario",
    "criar_pedido",
    "get_pedidos_usuario",
    "get_todos_pedidos",
    "relatorio_vendas",
    "atualizar_status_pedido",
    "get_database_counts",
    "reset_all_tables",
    "executar_query_segura",
]
