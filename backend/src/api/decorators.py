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


def audit_log(action, module, entity_getter=None):
    """Decorator for audit logging with optional entity delta tracking.

    Args:
        action: Action name (e.g. 'update', 'create', 'delete')
        module: Module name (e.g. 'Products', 'Sales')
        entity_getter: Optional callable(*args, **kwargs) -> entity object.
            The entity must have 'id' attribute and optionally to_dict().
            If provided, old/new values are recorded.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from models.models import AuditLog, db

            old_entity = None
            if entity_getter:
                try:
                    old_entity = entity_getter(*args, **kwargs)
                except Exception:
                    old_entity = None

            result = fn(*args, **kwargs)

            try:
                user = get_current_user()
                entity_type = None
                entity_id = None
                old_values = None
                new_values = None

                if entity_getter and old_entity:
                    entity_type = old_entity.__class__.__name__
                    entity_id = old_entity.id
                    old_values = _model_to_dict(old_entity)

                    # Re-fetch after the function for new state
                    try:
                        new_entity = entity_getter(*args, **kwargs)
                        if new_entity:
                            new_values = _model_to_dict(new_entity)
                    except Exception:
                        new_values = None

                log = AuditLog(
                    user_id=user.id,
                    username=user.username,
                    action=action,
                    module=module,
                    description=f'{action} on {module}',
                    entity_type=entity_type,
                    entity_id=entity_id,
                    old_values=old_values,
                    new_values=new_values,
                    branch_id=user.branch_id,
                    ip_address=request.remote_addr,
                )
                db.session.add(log)
                db.session.commit()
            except Exception:
                db.session.rollback()
                current_app.logger.error('Audit log failed for %s %s', action, module)
            return result
        return wrapper
    return decorator


def _model_to_dict(model):
    """Extract column values from a SQLAlchemy model as a serializable dict."""
    from sqlalchemy import inspect
    if model is None:
        return None
    mapper = inspect(model)
    result = {}
    for col in mapper.columns:
        key = col.key
        try:
            v = getattr(model, key)
            if isinstance(v, (int, float, str, bool)):
                result[key] = v
            elif v is None:
                result[key] = None
            elif hasattr(v, 'isoformat'):
                result[key] = v.isoformat()
            else:
                result[key] = str(v)
        except Exception:
            pass
    return result if result else None
