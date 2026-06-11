from datetime import datetime
from typing import Any, Optional

from models.models import AuditLog, db
from repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self) -> None:
        super().__init__(AuditLog)

    def log(
        self,
        user_id: Optional[int],
        username: Optional[str],
        action: str,
        module: str,
        description: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        old_values: Optional[dict[str, Any]] = None,
        new_values: Optional[dict[str, Any]] = None,
        branch_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        entry = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            module=module,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_values,
            new_values=new_values,
            branch_id=branch_id,
            ip_address=ip_address,
        )
        db.session.add(entry)
        db.session.commit()
        return entry

    def get_by_user(self, user_id: int, limit: int = 50) -> list[AuditLog]:
        return AuditLog.query.filter_by(user_id=user_id).order_by(
            AuditLog.timestamp.desc(),
        ).limit(limit).all()

    def get_by_module(self, module: str, limit: int = 50) -> list[AuditLog]:
        return AuditLog.query.filter_by(module=module).order_by(
            AuditLog.timestamp.desc(),
        ).limit(limit).all()

    def get_by_action(self, action: str, limit: int = 50) -> list[AuditLog]:
        return AuditLog.query.filter_by(action=action).order_by(
            AuditLog.timestamp.desc(),
        ).limit(limit).all()

    def get_by_entity(
        self, entity_type: str, entity_id: int, limit: int = 50,
    ) -> list[AuditLog]:
        return AuditLog.query.filter_by(
            entity_type=entity_type,
            entity_id=entity_id,
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()

    def get_by_date_range(
        self, start_date: datetime, end_date: datetime, limit: int = 100,
    ) -> list[AuditLog]:
        return AuditLog.query.filter(
            AuditLog.timestamp.between(start_date, end_date),
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()

    def get_recent(self, limit: int = 50) -> list[AuditLog]:
        return AuditLog.query.order_by(
            AuditLog.timestamp.desc(),
        ).limit(limit).all()

    def search(self, term: str, limit: int = 50) -> list[AuditLog]:
        pattern = f'%{term}%'
        return AuditLog.query.filter(
            (
                AuditLog.description.ilike(pattern) |
                AuditLog.username.ilike(pattern) |
                AuditLog.module.ilike(pattern) |
                AuditLog.action.ilike(pattern) |
                AuditLog.entity_type.ilike(pattern)
            ),
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
