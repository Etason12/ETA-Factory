from datetime import datetime
from typing import Any
import random


def generate_code(prefix: str, sequence: int, length: int = 6) -> str:
    return f'{prefix}-{str(sequence).zfill(length)}'


def generate_unique_code(prefix: str) -> str:
    ts = datetime.now().strftime('%Y%m%d%H%M%S')
    rand = str(random.randint(0, 9999)).zfill(4)
    return f'{prefix}-{ts}-{rand}'


def paginate(query, page: int = 1, per_page: int = 20):
    per_page = max(1, min(per_page, 100))
    page = max(1, page)
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return {
        'items': pagination.items,
        'total': pagination.total,
        'page': pagination.page,
        'per_page': pagination.per_page,
        'pages': pagination.pages,
    }


def escape_like(value: str) -> str:
    """Escape % and _ wildcards for use in SQLAlchemy ilike patterns."""
    return value.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')


def to_dict(model, exclude: set = None) -> dict[str, Any]:
    if exclude is None:
        exclude = set()
    return {
        c.name: getattr(model, c.name)
        for c in model.__table__.columns
        if c.name not in exclude
    }


def format_datetime(dt: datetime) -> str:
    return dt.isoformat() if dt else None
