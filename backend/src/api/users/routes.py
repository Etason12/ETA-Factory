from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import bcrypt
from models.models import User, Role, Permission, db
from utils.helpers import paginate, escape_like
from utils.error_handlers import NotFoundError, ValidationError, ConflictError
from api.decorators import permission_required, audit_log
from . import users_bp


@users_bp.route('', methods=['GET'])
@jwt_required()
@permission_required('users.view')
def list_users():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '').strip()
    role_id = request.args.get('role_id', type=int)
    branch_id = request.args.get('branch_id', type=int)
    is_active = request.args.get('is_active', type=int)

    query = User.query.filter(User.is_deleted == False)

    if search:
        safe = escape_like(search)
        query = query.filter(
            db.or_(
                User.username.ilike(f'%{safe}%'),
                User.email.ilike(f'%{safe}%'),
                User.full_name.ilike(f'%{safe}%'),
                User.phone.ilike(f'%{safe}%'),
            )
        )
    if role_id:
        query = query.filter(User.role_id == role_id)
    if branch_id:
        query = query.filter(User.branch_id == branch_id)
    if is_active is not None:
        query = query.filter(User.is_active == bool(is_active))

    query = query.order_by(User.created_at.desc())
    result = paginate(query, page, per_page)

    return jsonify({
        'users': [u.to_dict() for u in result['items']],
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@users_bp.route('', methods=['POST'])
@jwt_required()
@audit_log('create', 'User')
@permission_required('users.create')
def create_user():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    full_name = data.get('full_name', '').strip()
    role_id = data.get('role_id')
    branch_id = data.get('branch_id')
    phone = data.get('phone', '').strip()

    if not all([username, email, password, full_name, role_id]):
        raise ValidationError('username, email, password, full_name, and role_id are required')

    if len(password) < 6:
        raise ValidationError('Password must be at least 6 characters')

    if User.query.filter((User.username == username) | (User.email == email)).first():
        raise ConflictError('Username or email already exists')

    role = Role.query.get(role_id)
    if not role:
        raise ValidationError('Invalid role_id')

    user = User(
        username=username,
        email=email,
        password_hash=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
        full_name=full_name,
        phone=phone,
        role_id=role_id,
        branch_id=branch_id,
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(user)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'user': user.to_dict(), 'message': 'User created successfully'}), 201


@users_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('users.view')
def get_user(id):
    user = User.query.filter(User.id == id, User.is_deleted == False).first()
    if not user:
        raise NotFoundError('User not found')
    return jsonify({'user': user.to_dict()}), 200


@users_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@audit_log('update', 'User')
@permission_required('users.edit')
def update_user(id):
    user = User.query.filter(User.id == id, User.is_deleted == False).first()
    if not user:
        raise NotFoundError('User not found')

    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    role_id = data.get('role_id')
    branch_id = data.get('branch_id')
    is_active = data.get('is_active')

    if username and username != user.username:
        if User.query.filter(User.username == username, User.id != id).first():
            raise ConflictError('Username already taken')
        user.username = username

    if email and email != user.email:
        if User.query.filter(User.email == email, User.id != id).first():
            raise ConflictError('Email already taken')
        user.email = email

    if full_name:
        user.full_name = full_name
    if phone is not None:
        user.phone = phone
    if role_id:
        role = Role.query.get(role_id)
        if not role:
            raise ValidationError('Invalid role_id')
        user.role_id = role_id
    if branch_id is not None:
        user.branch_id = branch_id
    if is_active is not None:
        user.is_active = bool(is_active)

    user.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'user': user.to_dict(), 'message': 'User updated successfully'}), 200


@users_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@audit_log('delete', 'User')
@permission_required('users.delete')
def delete_user(id):
    user = User.query.filter(User.id == id, User.is_deleted == False).first()
    if not user:
        raise NotFoundError('User not found')

    current_user_id = int(get_jwt_identity())
    if user.id == current_user_id:
        raise ValidationError('Cannot delete your own account')

    if user.role and user.role.name == 'Owner':
        from models.models import Role
        owner_role = Role.query.filter_by(name='Owner').first()
        if owner_role:
            active_owners = User.query.filter(
                User.role_id == owner_role.id,
                User.is_active == True,
                User.is_deleted == False,
                User.id != user.id,
            ).count()
            if active_owners == 0:
                raise ValidationError('Cannot delete the last Owner account')

    user.soft_delete()
    user.updated_by_id = current_user_id
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'User deleted successfully'}), 200


@users_bp.route('/<int:id>/permissions', methods=['GET'])
@jwt_required()
@permission_required('users.view')
def get_user_permissions(id):
    user = User.query.filter(User.id == id, User.is_deleted == False).first()
    if not user:
        raise NotFoundError('User not found')

    if not user.role:
        return jsonify({'role': None, 'permissions': []}), 200

    permissions = [{'id': p.id, 'name': p.name, 'description': p.description, 'module': p.module}
                   for p in user.role.permissions]

    return jsonify({
        'role': {'id': user.role.id, 'name': user.role.name},
        'permissions': permissions,
    }), 200
