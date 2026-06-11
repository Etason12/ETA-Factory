from typing import Any, Optional

from models.models import AuditLog
from repositories.base import BaseRepository
from utils.helpers import paginate


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self) -> None:
        super().__init__(AuditLog)


class AuditService:
    def __init__(self, audit_repository: Optional[AuditLogRepository] = None):
        self.repo = audit_repository or AuditLogRepository()

    def log_action(
        self,
        user_id: Optional[int],
        action: str,
        module: str,
        description: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        old_values: Optional[dict[str, Any]] = None,
        new_values: Optional[dict[str, Any]] = None,
        branch_id: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        from models.models import User

        username = None
        if user_id:
            user = User.query.get(user_id)
            username = user.username if user else None

        log = AuditLog(
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
        return self.repo.create(log)

    def get_logs(
        self,
        page: int = 1,
        per_page: int = 20,
        filters: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        query = AuditLog.query.order_by(AuditLog.timestamp.desc())

        if filters:
            if filters.get('user_id'):
                query = query.filter(AuditLog.user_id == filters['user_id'])
            if filters.get('action'):
                query = query.filter(AuditLog.action == filters['action'])
            if filters.get('module'):
                query = query.filter(AuditLog.module == filters['module'])
            if filters.get('entity_type'):
                query = query.filter(
                    AuditLog.entity_type == filters['entity_type']
                )
            if filters.get('entity_id'):
                query = query.filter(AuditLog.entity_id == filters['entity_id'])
            if filters.get('branch_id'):
                query = query.filter(AuditLog.branch_id == filters['branch_id'])
            if filters.get('start_date') and filters.get('end_date'):
                query = query.filter(
                    AuditLog.timestamp >= filters['start_date'],
                    AuditLog.timestamp <= filters['end_date'],
                )

        result = paginate(query, page, per_page)

        return {
            'items': [
                {
                    'id': log.id,
                    'user_id': log.user_id,
                    'username': log.username,
                    'action': log.action,
                    'module': log.module,
                    'description': log.description,
                    'entity_type': log.entity_type,
                    'entity_id': log.entity_id,
                    'old_values': log.old_values,
                    'new_values': log.new_values,
                    'branch_id': log.branch_id,
                    'ip_address': log.ip_address,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                }
                for log in result['items']
            ],
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages'],
        }
