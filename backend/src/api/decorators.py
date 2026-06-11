from functools import wraps
from flask import current_app, request
from flask_jwt_extended import get_jwt_identity
from models.models import User
from utils.error_handlers import ForbiddenError, UnauthorizedError


def get_current_user():
    identity = get_jwt_identity()
    if not identity:
        raise UnauthorizedError('Invalid token identity')
    user = User.query.get(int(identity))
    if not user or not user.is_active or user.is_deleted:
        raise UnauthorizedError('User not found or inactive')
    return user


def role_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user.role or user.role.name not in roles:
                raise ForbiddenError('Insufficient permissions')
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def branch_required():
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            bid = kwargs.get('branch_id')
            if not bid:
                bid = request.args.get('branch_id')
            if not bid and request.is_json:
                bid = request.json.get('branch_id')
            if bid and user.branch_id and int(bid) != user.branch_id:
                raise ForbiddenError('Access restricted to assigned branch')
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def permission_required(permission_name):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = get_current_user()
            if not user.role:
                raise ForbiddenError('No role assigned')
            has_perm = any(p.name == permission_name for p in user.role.permissions)
            if not has_perm:
                raise ForbiddenError(f'Missing permission: {permission_name}')
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def audit_log(action, module):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from models.models import AuditLog, db
            result = fn(*args, **kwargs)
            try:
                user = get_current_user()
                log = AuditLog(
                    user_id=user.id,
                    username=user.username,
                    action=action,
                    module=module,
                    description=f'{action} on {module}',
                    branch_id=user.branch_id,
                    ip_address=request.remote_addr,
                )
                db.session.add(log)
                db.session.commit()
            except Exception:
                db.session.rollback()
                current_app.logger.error('Audit log failed for %s %s', action, module)
                raise
            return result
        return wrapper
    return decorator
