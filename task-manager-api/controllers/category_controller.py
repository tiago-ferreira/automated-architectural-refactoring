"""Controller de Categorias (CategoryController) — extraído e desacoplado de relatórios."""
from typing import Any, Dict, Optional, Tuple
from sqlalchemy import func
from config.settings import Config, logger
from database import db
from models.category import Category
from models.task import Task


class CategoryController:
    """Orquestrador das regras de negócio de categorias."""

    @staticmethod
    def list_categories() -> Tuple[Any, int]:
        task_counts = dict(
            db.session.query(Task.category_id, func.count(Task.id))
            .group_by(Task.category_id)
            .all()
        )
        categories = Category.query.all()
        result = []
        for cat in categories:
            cat_data = cat.to_dict()
            cat_data["task_count"] = task_counts.get(cat.id, 0)
            result.append(cat_data)
        return result, 200

    @staticmethod
    def create_category(data: Optional[Dict[str, Any]]) -> Tuple[Any, int]:
        if not data:
            return {"error": "Dados inválidos"}, 400

        name = data.get("name")
        if not name:
            return {"error": "Nome é obrigatório"}, 400

        category = Category(
            name=name,
            description=data.get("description", ""),
            color=data.get("color", Config.DEFAULT_COLOR),
        )

        try:
            db.session.add(category)
            db.session.commit()
            return category.to_dict(), 201
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao criar categoria: %s", exc)
            return {"error": "Erro ao criar categoria"}, 500

    @staticmethod
    def update_category(
        cat_id: int, data: Optional[Dict[str, Any]]
    ) -> Tuple[Any, int]:
        cat = db.session.get(Category, cat_id)
        if not cat:
            return {"error": "Categoria não encontrada"}, 404
        if not data:
            return {"error": "Dados inválidos"}, 400

        if "name" in data:
            cat.name = data["name"]
        if "description" in data:
            cat.description = data["description"]
        if "color" in data:
            cat.color = data["color"]

        try:
            db.session.commit()
            return cat.to_dict(), 200
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao atualizar categoria %s: %s", cat_id, exc)
            return {"error": "Erro ao atualizar"}, 500

    @staticmethod
    def delete_category(cat_id: int) -> Tuple[Any, int]:
        cat = db.session.get(Category, cat_id)
        if not cat:
            return {"error": "Categoria não encontrada"}, 404

        try:
            db.session.delete(cat)
            db.session.commit()
            return {"message": "Categoria deletada"}, 200
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao deletar categoria %s: %s", cat_id, exc)
            return {"error": "Erro ao deletar"}, 500
