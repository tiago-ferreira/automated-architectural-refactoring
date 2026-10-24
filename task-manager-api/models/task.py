"""Model de Tarefas (Task)."""
from config.settings import Config, utc_now
from database import db


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(Config.MAX_TITLE_LENGTH), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default=Config.DEFAULT_STATUS)
    priority = db.Column(db.Integer, default=Config.DEFAULT_PRIORITY)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    category_id = db.Column(
        db.Integer, db.ForeignKey("categories.id"), nullable=True
    )
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship("User", backref="tasks")
    category = db.relationship("Category", backref="tasks")

    def to_dict(
        self, include_overdue: bool = False, include_relations: bool = False
    ) -> dict:
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "user_id": self.user_id,
            "category_id": self.category_id,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
            "due_date": str(self.due_date) if self.due_date else None,
            "tags": self.tags.split(",") if self.tags else [],
        }
        if include_overdue:
            data["overdue"] = self.is_overdue()
        if include_relations:
            data["user_name"] = self.user.name if self.user else None
            data["category_name"] = (
                self.category.name if self.category else None
            )
        return data

    def validate_status(self, new_status: str) -> bool:
        return new_status in Config.VALID_STATUSES

    def validate_priority(self, priority_value: int) -> bool:
        return Config.MIN_PRIORITY <= priority_value <= Config.MAX_PRIORITY

    def is_overdue(self) -> bool:
        return bool(
            self.due_date
            and self.due_date < utc_now()
            and self.status not in Config.TERMINAL_STATUSES
        )
