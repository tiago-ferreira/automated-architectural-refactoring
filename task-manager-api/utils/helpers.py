"""Funções utilitárias de formatação, cálculo percentual e validação."""
from datetime import datetime
import re
from typing import Any, Optional

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$")


def format_date(date_obj: Any) -> Optional[str]:
    return str(date_obj) if date_obj else None


def calculate_percentage(part: int, total: int) -> float:
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email: str) -> bool:
    return bool(email and EMAIL_REGEX.match(email))


def normalize_tags(tags: Any) -> Optional[str]:
    if tags is None:
        return None
    if isinstance(tags, list):
        return ",".join(str(tag) for tag in tags)
    return str(tags)


def parse_date(date_string: str) -> Optional[datetime]:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_string, fmt)
        except (ValueError, TypeError):
            continue
    return None
