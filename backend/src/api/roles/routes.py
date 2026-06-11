from flask import jsonify
from flask_jwt_extended import jwt_required
from models.models import Role
from . import roles_bp


@roles_bp.route('', methods=['GET'])
@jwt_required()
def list_roles():
    roles = Role.query.order_by(Role.name).all()
    return jsonify([{
        'id': r.id,
        'name': r.name,
        'description': r.description,
        'is_system': r.is_system,
    } for r in roles]), 200
