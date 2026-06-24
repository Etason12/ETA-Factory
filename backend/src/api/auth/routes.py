from flask import jsonify, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
)
import bcrypt
from models.models import User, AuditLog, db
from utils.error_handlers import UnauthorizedError, ValidationError, NotFoundError
from api.decorators import audit_log
from . import auth_bp


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        raise ValidationError('Username and password are required')

    user = User.query.filter(
        db.or_(User.username == username, User.email == username),
        User.is_deleted == False
    ).first()

    if not user or not bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise UnauthorizedError('Invalid credentials')

    if not user.is_active:
        raise UnauthorizedError('Account is deactivated')

    user.last_login = db.func.now()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    log = AuditLog(
        user_id=user.id,
        username=user.username,
        action='login',
        module='Auth',
        description='login on Auth',
        branch_id=user.branch_id,
        ip_address=request.remote_addr,
    )
    db.session.add(log)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'username': user.username, 'role': user.role.name if user.role else None}
    )
    refresh_token = create_refresh_token(
        identity=str(user.id),
        additional_claims={'username': user.username}
    )

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict()
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    if not identity:
        raise UnauthorizedError('Invalid token identity')
    user = User.query.get(int(identity))
    if not user or not user.is_active or user.is_deleted:
        raise UnauthorizedError('User not found or inactive')

    access_token = create_access_token(
        identity=str(user.id),
        additional_claims={'username': user.username, 'role': user.role.name if user.role else None}
    )
    return jsonify({'access_token': access_token}), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@audit_log('update', 'Auth')
def change_password():
    data = request.get_json()

    if not data:
        raise ValidationError('Request body is required')

    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not old_password or not new_password or not confirm_password:
        raise ValidationError('All password fields are required')

    if new_password != confirm_password:
        raise ValidationError('New passwords do not match')

    if len(new_password) < 6:
        raise ValidationError('Password must be at least 6 characters')

    user = User.query.get(int(get_jwt_identity()))
    if not user:
        raise NotFoundError('User not found')

    if not bcrypt.checkpw(old_password.encode('utf-8'), user.password_hash.encode('utf-8')):
        raise ValidationError('Current password is incorrect')

    user.password_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Password changed successfully'}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        raise NotFoundError('User not found')
    if not user.is_active or user.is_deleted:
        raise UnauthorizedError('Account is inactive or has been deleted')
    return jsonify({'user': user.to_dict()}), 200
