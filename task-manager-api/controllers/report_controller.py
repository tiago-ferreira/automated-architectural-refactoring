"""Controller de Relatórios Analíticos (ReportController) — consultas agregadas sem N+1."""
from datetime import timedelta
from typing import Any, Tuple
from sqlalchemy import case, func
from config.settings import Config, utc_now
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import calculate_percentage


class ReportController:
    """Orquestrador dos relatórios gerenciais e de produtividade por usuário."""

    @staticmethod
    def get_summary_report() -> Tuple[Any, int]:
        now = utc_now()
        total_users = User.query.count()
        total_categories = Category.query.count()

        status_counts = dict(
            db.session.query(Task.status, func.count(Task.id))
            .group_by(Task.status)
            .all()
        )
        priority_counts = dict(
            db.session.query(Task.priority, func.count(Task.id))
            .group_by(Task.priority)
            .all()
        )
        total_tasks = sum(status_counts.values())

        overdue_tasks = Task.query.filter(
            Task.due_date.isnot(None),
            Task.due_date < now,
            Task.status.notin_(Config.TERMINAL_STATUSES),
        ).all()
        overdue_list = [
            {
                "id": task.id,
                "title": task.title,
                "due_date": str(task.due_date),
                "days_overdue": (now - task.due_date).days,
            }
            for task in overdue_tasks
        ]

        recent_cutoff = now - timedelta(days=Config.RECENT_ACTIVITY_DAYS)
        recent_tasks = Task.query.filter(
            Task.created_at >= recent_cutoff
        ).count()
        recent_done = Task.query.filter(
            Task.status == "done",
            Task.updated_at >= recent_cutoff,
        ).count()

        # Agregação em query única com LEFT JOIN para produtividade por usuário (elimina N+1)
        user_rows = (
            db.session.query(
                User.id,
                User.name,
                func.count(Task.id).label("total_tasks"),
                func.coalesce(
                    func.sum(case((Task.status == "done", 1), else_=0)), 0
                ).label("completed_tasks"),
            )
            .outerjoin(Task, Task.user_id == User.id)
            .group_by(User.id, User.name)
            .order_by(User.id)
            .all()
        )

        user_stats = []
        for row in user_rows:
            total = int(row.total_tasks or 0)
            completed = int(row.completed_tasks or 0)
            user_stats.append(
                {
                    "user_id": row.id,
                    "user_name": row.name,
                    "total_tasks": total,
                    "completed_tasks": completed,
                    "completion_rate": calculate_percentage(completed, total),
                }
            )

        report = {
            "generated_at": str(now),
            "overview": {
                "total_tasks": total_tasks,
                "total_users": total_users,
                "total_categories": total_categories,
            },
            "tasks_by_status": {
                "pending": status_counts.get("pending", 0),
                "in_progress": status_counts.get("in_progress", 0),
                "done": status_counts.get("done", 0),
                "cancelled": status_counts.get("cancelled", 0),
            },
            "tasks_by_priority": {
                "critical": priority_counts.get(1, 0),
                "high": priority_counts.get(2, 0),
                "medium": priority_counts.get(3, 0),
                "low": priority_counts.get(4, 0),
                "minimal": priority_counts.get(5, 0),
            },
            "overdue": {
                "count": len(overdue_list),
                "tasks": overdue_list,
            },
            "recent_activity": {
                "tasks_created_last_7_days": recent_tasks,
                "tasks_completed_last_7_days": recent_done,
            },
            "user_productivity": user_stats,
        }
        return report, 200

    @staticmethod
    def get_user_report(user_id: int) -> Tuple[Any, int]:
        user = db.session.get(User, user_id)
        if not user:
            return {"error": "Usuário não encontrado"}, 404

        tasks = Task.query.filter_by(user_id=user_id).all()
        total = len(tasks)
        done = sum(1 for t in tasks if t.status == "done")
        pending = sum(1 for t in tasks if t.status == "pending")
        in_progress = sum(1 for t in tasks if t.status == "in_progress")
        cancelled = sum(1 for t in tasks if t.status == "cancelled")
        overdue = sum(1 for t in tasks if t.is_overdue())
        high_priority = sum(
            1 for t in tasks if t.priority <= Config.HIGH_PRIORITY_THRESHOLD
        )

        report = {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
            },
            "statistics": {
                "total_tasks": total,
                "done": done,
                "pending": pending,
                "in_progress": in_progress,
                "cancelled": cancelled,
                "overdue": overdue,
                "high_priority": high_priority,
                "completion_rate": calculate_percentage(done, total),
            },
        }
        return report, 200
