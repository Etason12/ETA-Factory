from flask import jsonify, request
from flask_jwt_extended import jwt_required
from models.models import Role, Permission, RolePermission, User, db
from api.decorators import permission_required
from utils.error_handlers import NotFoundError, ValidationError, ConflictError
from . import roles_bp


@roles_bp.route('', methods=['GET'])
@jwt_required()
@permission_required('users.view')
def list_roles():
    roles = Role.query.order_by(Role.name).all()
    return jsonify([{
        'id': r.id, 'name': r.name, 'description': r.description,
        'is_system': r.is_system,
    } for r in roles]), 200


@roles_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('users.view')
def get_role(id):
    role = Role.query.get(id)
    if not role:
        raise NotFoundError('Role not found')
    return jsonify({
        'id': role.id, 'name': role.name, 'description': role.description,
        'is_system': role.is_system,
    }), 200


@roles_bp.route('', methods=['POST'])
@jwt_required()
@permission_required('users.create')
def create_role():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    if not name:
        raise ValidationError('Role name is required')
    if Role.query.filter_by(name=name).first():
        raise ConflictError('Role name already exists')
    role = Role(name=name, description=description, is_system=False)
    db.session.add(role)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({'message': 'Role created successfully', 'id': role.id}), 201


@roles_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@permission_required('users.edit')
def update_role(id):
    role = Role.query.get(id)
    if not role:
        raise NotFoundError('Role not found')
    if role.is_system:
        raise ValidationError('Cannot modify system roles')
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    if not name:
        raise ValidationError('Role name is required')
    existing = Role.query.filter_by(name=name).first()
    if existing and existing.id != id:
        raise ConflictError('Role name already exists')
    role.name = name
    role.description = description
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({'message': 'Role updated successfully'}), 200


@roles_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@permission_required('users.delete')
def delete_role(id):
    role = Role.query.get(id)
    if not role:
        raise NotFoundError('Role not found')
    if role.is_system:
        raise ValidationError('Cannot delete system roles')
    users_count = User.query.filter_by(role_id=id).count()
    if users_count > 0:
        raise ValidationError(f'Cannot delete role: {users_count} user(s) are assigned to it')
    RolePermission.query.filter_by(role_id=id).delete()
    db.session.delete(role)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({'message': 'Role deleted successfully'}), 200


@roles_bp.route('/permissions', methods=['GET'])
@jwt_required()
@permission_required('users.view')
def list_permissions():
    perms = Permission.query.order_by(Permission.module, Permission.name).all()
    return jsonify([{
        'id': p.id, 'name': p.name, 'description': p.description, 'module': p.module,
    } for p in perms]), 200


@roles_bp.route('/<int:id>/permissions', methods=['GET'])
@jwt_required()
@permission_required('users.view')
def get_role_permissions(id):
    role = Role.query.get(id)
    if not role:
        raise NotFoundError('Role not found')
    permission_ids = [p.id for p in role.permissions]
    return jsonify({'role_id': id, 'permission_ids': permission_ids}), 200


@roles_bp.route('/<int:id>/permissions', methods=['PUT'])
@jwt_required()
@permission_required('users.edit')
def update_role_permissions(id):
    role = Role.query.get(id)
    if not role:
        raise NotFoundError('Role not found')
    if role.is_system:
        raise ValidationError('Cannot modify permissions for system roles')

    data = request.get_json()
    if not data or 'permission_ids' not in data:
        raise ValidationError('permission_ids is required')

    permission_ids = data['permission_ids']
    existing = RolePermission.query.filter_by(role_id=id).all()
    for rp in existing:
        db.session.delete(rp)

    for pid in permission_ids:
        perm = Permission.query.get(pid)
        if perm:
            db.session.add(RolePermission(role_id=id, permission_id=pid))

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Permissions updated successfully'}), 200
