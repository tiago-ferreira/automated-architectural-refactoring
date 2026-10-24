"""Controller de Tarefas (TaskController) — concentra a lógica de negócio e persistência de Tasks."""
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from config.settings import Config, logger, utc_now
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage, normalize_tags


class TaskController:
    """Orquestrador das regras de negócio de tarefas."""

    @staticmethod
    def list_tasks() -> Tuple[Any, int]:
        tasks = (
            Task.query.options(
                joinedload(Task.user), joinedload(Task.category)
            )
            .all()
        )
        result = [
            task.to_dict(include_overdue=True, include_relations=True)
            for task in tasks
        ]
        return result, 200

    @staticmethod
    def get_task(task_id: int) -> Tuple[Any, int]:
        task = db.session.get(Task, task_id)
        if not task:
            return {"error": "Task não encontrada"}, 404
        return task.to_dict(include_overdue=True), 200

    @staticmethod
    def create_task(data: Optional[Dict[str, Any]]) -> Tuple[Any, int]:
        if not data:
            return {"error": "Dados inválidos"}, 400

        title = data.get("title")
        if not title:
            return {"error": "Título é obrigatório"}, 400
        if len(title) < Config.MIN_TITLE_LENGTH:
            return {"error": "Título muito curto"}, 400
        if len(title) > Config.MAX_TITLE_LENGTH:
            return {"error": "Título muito longo"}, 400

        description = data.get("description", "")
        status = data.get("status", Config.DEFAULT_STATUS)
        priority = data.get("priority", Config.DEFAULT_PRIORITY)
        user_id = data.get("user_id")
        category_id = data.get("category_id")
        due_date_raw = data.get("due_date")
        tags_raw = data.get("tags")

        task = Task()
        if not task.validate_status(status):
            return {"error": "Status inválido"}, 400
        if not isinstance(priority, int) or not task.validate_priority(priority):
            return {"error": "Prioridade deve ser entre 1 e 5"}, 400

        if user_id and not db.session.get(User, user_id):
            return {"error": "Usuário não encontrado"}, 404
        if category_id and not db.session.get(Category, category_id):
            return {"error": "Categoria não encontrada"}, 404

        task.title = title
        task.description = description
        task.status = status
        task.priority = priority
        task.user_id = user_id
        task.category_id = category_id

        if due_date_raw:
            try:
                task.due_date = datetime.strptime(due_date_raw, "%Y-%m-%d")
            except (ValueError, TypeError):
                return {"error": "Formato de data inválido. Use YYYY-MM-DD"}, 400

        if tags_raw is not None:
            task.tags = normalize_tags(tags_raw)

        try:
            db.session.add(task)
            db.session.commit()
            logger.info("Task criada: %s - %s", task.id, task.title)
            return task.to_dict(), 201
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao criar task: %s", exc)
            return {"error": "Erro ao criar task"}, 500

    @staticmethod
    def update_task(
        task_id: int, data: Optional[Dict[str, Any]]
    ) -> Tuple[Any, int]:
        task = db.session.get(Task, task_id)
        if not task:
            return {"error": "Task não encontrada"}, 404
        if not data:
            return {"error": "Dados inválidos"}, 400

        if "title" in data:
            title = data["title"] or ""
            if len(title) < Config.MIN_TITLE_LENGTH:
                return {"error": "Título muito curto"}, 400
            if len(title) > Config.MAX_TITLE_LENGTH:
                return {"error": "Título muito longo"}, 400
            task.title = title

        if "description" in data:
            task.description = data["description"]

        if "status" in data:
            if not task.validate_status(data["status"]):
                return {"error": "Status inválido"}, 400
            task.status = data["status"]

        if "priority" in data:
            priority_val = data["priority"]
            if not isinstance(priority_val, int) or not task.validate_priority(
                priority_val
            ):
                return {"error": "Prioridade deve ser entre 1 e 5"}, 400
            task.priority = priority_val

        if "user_id" in data:
            if data["user_id"] and not db.session.get(User, data["user_id"]):
                return {"error": "Usuário não encontrado"}, 404
            task.user_id = data["user_id"]

        if "category_id" in data:
            if data["category_id"] and not db.session.get(
                Category, data["category_id"]
            ):
                return {"error": "Categoria não encontrada"}, 404
            task.category_id = data["category_id"]

        if "due_date" in data:
            if data["due_date"]:
                try:
                    task.due_date = datetime.strptime(
                        data["due_date"], "%Y-%m-%d"
                    )
                except (ValueError, TypeError):
                    return {"error": "Formato de data inválido"}, 400
            else:
                task.due_date = None

        if "tags" in data:
            task.tags = normalize_tags(data["tags"])

        task.updated_at = utc_now()

        try:
            db.session.commit()
            logger.info("Task atualizada: %s", task.id)
            return task.to_dict(), 200
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao atualizar task %s: %s", task_id, exc)
            return {"error": "Erro ao atualizar"}, 500

    @staticmethod
    def delete_task(task_id: int) -> Tuple[Any, int]:
        task = db.session.get(Task, task_id)
        if not task:
            return {"error": "Task não encontrada"}, 404

        try:
            db.session.delete(task)
            db.session.commit()
            logger.info("Task deletada: %s", task_id)
            return {"message": "Task deletada com sucesso"}, 200
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao deletar task %s: %s", task_id, exc)
            return {"error": "Erro ao deletar"}, 500

    @staticmethod
    def search_tasks(
        query_term: str = "",
        status: str = "",
        priority_raw: str = "",
        user_id_raw: str = "",
    ) -> Tuple[Any, int]:
        tasks_query = Task.query

        if query_term:
            like_pattern = f"%{query_term}%"
            tasks_query = tasks_query.filter(
                db.or_(
                    Task.title.like(like_pattern),
                    Task.description.like(like_pattern),
                )
            )

        if status:
            tasks_query = tasks_query.filter(Task.status == status)

        if priority_raw:
            try:
                tasks_query = tasks_query.filter(
                    Task.priority == int(priority_raw)
                )
            except ValueError:
                return {"error": "Parâmetro priority inválido"}, 400

        if user_id_raw:
            try:
                tasks_query = tasks_query.filter(
                    Task.user_id == int(user_id_raw)
                )
            except ValueError:
                return {"error": "Parâmetro user_id inválido"}, 400

        results = tasks_query.all()
        return [task.to_dict() for task in results], 200

    @staticmethod
    def get_task_stats() -> Tuple[Any, int]:
        status_rows = (
            db.session.query(Task.status, func.count(Task.id))
            .group_by(Task.status)
            .all()
        )
        counts_by_status = {status: count for status, count in status_rows}

        total = sum(counts_by_status.values())
        pending = counts_by_status.get("pending", 0)
        in_progress = counts_by_status.get("in_progress", 0)
        done = counts_by_status.get("done", 0)
        cancelled = counts_by_status.get("cancelled", 0)

        now = utc_now()
        overdue_count = (
            Task.query.filter(
                Task.due_date.isnot(None),
                Task.due_date < now,
                Task.status.notin_(Config.TERMINAL_STATUSES),
            ).count()
        )

        stats = {
            "total": total,
            "pending": pending,
            "in_progress": in_progress,
            "done": done,
            "cancelled": cancelled,
            "overdue": overdue_count,
            "completion_rate": calculate_percentage(done, total),
        }
        return stats, 200
