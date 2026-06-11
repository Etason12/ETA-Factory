from typing import Any, Generic, Optional, TypeVar

from sqlalchemy import asc, desc

from models.models import db
from utils.helpers import paginate as paginate_helper

T = TypeVar('T')


class BaseRepository(Generic[T]):
    def __init__(self, model_class: type[T]) -> None:
        self.model_class = model_class

    def get_by_id(self, id: int) -> Optional[T]:
        query = self.model_class.query
        if hasattr(self.model_class, 'is_deleted'):
            query = query.filter(self.model_class.is_deleted == False)
        return query.get(id)

    def get_all(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[dict[str, Any]] = None,
        sort: Optional[str] = None,
        order: str = 'asc',
    ) -> dict[str, Any]:
        query = self.model_class.query
        if hasattr(self.model_class, 'is_deleted'):
            query = query.filter(self.model_class.is_deleted == False)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key) and value is not None:
                    column = getattr(self.model_class, key)
                    if isinstance(value, (list, tuple)):
                        query = query.filter(column.in_(value))
                    else:
                        query = query.filter(column == value)
        if sort and hasattr(self.model_class, sort):
            column = getattr(self.model_class, sort)
            query = query.order_by(desc(column) if order == 'desc' else asc(column))
        return paginate_helper(query, page, per_page)

    def create(self, entity: T) -> T:
        db.session.add(entity)
        db.session.flush()
        return entity

    def update(self, entity: T) -> T:
        db.session.flush()
        return entity

    def delete(self, entity: T) -> None:
        if hasattr(entity, 'soft_delete'):
            entity.soft_delete()
        else:
            db.session.delete(entity)
        db.session.flush()

    def count(self, filters: Optional[dict[str, Any]] = None) -> int:
        query = self.model_class.query
        if hasattr(self.model_class, 'is_deleted'):
            query = query.filter(self.model_class.is_deleted == False)
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key) and value is not None:
                    column = getattr(self.model_class, key)
                    if isinstance(value, (list, tuple)):
                        query = query.filter(column.in_(value))
                    else:
                        query = query.filter(column == value)
        return query.count()
