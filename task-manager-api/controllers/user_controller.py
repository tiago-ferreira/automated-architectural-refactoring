"""Controller de Usuários e Autenticação (UserController)."""
from typing import Any, Dict, Optional, Tuple
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import func
from config.settings import Config, logger
from database import db
from models.task import Task
from models.user import User
from utils.helpers import validate_email


class UserController:
    """Orquestrador das regras de negócio de usuários e autenticação."""

    @staticmethod
    def _generate_auth_token(user: User) -> str:
        serializer = URLSafeTimedSerializer(Config.SECRET_KEY)
        return serializer.dumps({"user_id": user.id, "role": user.role})

    @staticmethod
    def list_users() -> Tuple[Any, int]:
        task_counts = dict(
            db.session.query(Task.user_id, func.count(Task.id))
            .group_by(Task.user_id)
            .all()
        )
        users = User.query.all()
        result = []
        for user in users:
            user_data = user.to_dict()
            user_data["task_count"] = task_counts.get(user.id, 0)
            result.append(user_data)
        return result, 200

    @staticmethod
    def get_user(user_id: int) -> Tuple[Any, int]:
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "Usuário não encontrado"}, 404

        data = user.to_dict()
        tasks = Task.query.filter_by(user_id=user_id).all()
        data["tasks"] = [task.to_dict() for task in tasks]
        return data, 200

    @staticmethod
    def create_user(data: Optional[Dict[str, Any]]) -> Tuple[Any, int]:
        if not data:
            return {"error": "Dados inválidos"}, 400

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        role = data.get("role", Config.DEFAULT_ROLE)

        if not name:
            return {"error": "Nome é obrigatório"}, 400
        if not email:
            return {"error": "Email é obrigatório"}, 400
        if not password:
            return {"error": "Senha é obrigatória"}, 400
        if not validate_email(email):
            return {"error": "Email inválido"}, 400
        if len(password) < Config.MIN_PASSWORD_LENGTH:
            return {"error": "Senha deve ter no mínimo 4 caracteres"}, 400

        if User.query.filter_by(email=email).first():
            return {"error": "Email já cadastrado"}, 409

        if role not in Config.VALID_ROLES:
            return {"error": "Role inválido"}, 400

        user = User(name=name, email=email, role=role)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            logger.info("Usuário criado: %s - %s", user.id, user.name)
            return user.to_dict(), 201
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao criar usuário: %s", exc)
            return {"error": "Erro ao criar usuário"}, 500

    @staticmethod
    def update_user(
        user_id: int, data: Optional[Dict[str, Any]]
    ) -> Tuple[Any, int]:
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "Usuário não encontrado"}, 404
        if not data:
            return {"error": "Dados inválidos"}, 400

        if "name" in data:
            user.name = data["name"]

        if "email" in data:
            if not validate_email(data["email"]):
                return {"error": "Email inválido"}, 400
            existing = User.query.filter_by(email=data["email"]).first()
            if existing and existing.id != user_id:
                return {"error": "Email já cadastrado"}, 409
            user.email = data["email"]

        if "password" in data:
            if len(data["password"]) < Config.MIN_PASSWORD_LENGTH:
                return {"error": "Senha muito curta"}, 400
            user.set_password(data["password"])

        if "role" in data:
            if data["role"] not in Config.VALID_ROLES:
                return {"error": "Role inválido"}, 400
            user.role = data["role"]

        if "active" in data:
            user.active = data["active"]

        try:
            db.session.commit()
            return user.to_dict(), 200
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao atualizar usuário %s: %s", user_id, exc)
            return {"error": "Erro ao atualizar"}, 500

    @staticmethod
    def delete_user(user_id: int) -> Tuple[Any, int]:
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "Usuário não encontrado"}, 404

        try:
            Task.query.filter_by(user_id=user_id).delete()
            db.session.delete(user)
            db.session.commit()
            logger.info("Usuário deletado: %s", user_id)
            return {"message": "Usuário deletado com sucesso"}, 200
        except Exception as exc:
            db.session.rollback()
            logger.error("Erro ao deletar usuário %s: %s", user_id, exc)
            return {"error": "Erro ao deletar"}, 500

    @staticmethod
    def get_user_tasks(user_id: int) -> Tuple[Any, int]:
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "Usuário não encontrado"}, 404

        tasks = Task.query.filter_by(user_id=user_id).all()
        result = [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "created_at": str(task.created_at),
                "due_date": str(task.due_date) if task.due_date else None,
                "overdue": task.is_overdue(),
            }
            for task in tasks
        ]
        return result, 200

    @staticmethod
    def login(data: Optional[Dict[str, Any]]) -> Tuple[Any, int]:
        if not data:
            return {"error": "Dados inválidos"}, 400

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return {"error": "Email e senha são obrigatórios"}, 400

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return {"error": "Credenciais inválidas"}, 401

        if not user.active:
            return {"error": "Usuário inativo"}, 403

        return (
            {
                "message": "Login realizado com sucesso",
                "user": user.to_dict(),
                "token": UserController._generate_auth_token(user),
            },
            200,
        )
