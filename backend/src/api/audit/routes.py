from flask import jsonify, request
from flask_jwt_extended import jwt_required
from models.models import AuditLog, db
from utils.helpers import paginate
from api.decorators import role_required, permission_required
from . import audit_bp


@audit_bp.route('/logs', methods=['GET'])
@jwt_required()
@permission_required('audit.view')
def list_audit_logs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    user_id = request.args.get('user_id', type=int)
    module = request.args.get('module', '').strip()
    action = request.args.get('action', '').strip()
    branch_id = request.args.get('branch_id', type=int)
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = AuditLog.query

    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if module:
        query = query.filter(AuditLog.module == module)
    if action:
        query = query.filter(AuditLog.action == action)
    if branch_id:
        query = query.filter(AuditLog.branch_id == branch_id)
    if date_from:
        query = query.filter(AuditLog.timestamp >= date_from)
    if date_to:
        query = query.filter(AuditLog.timestamp <= date_to)

    query = query.order_by(AuditLog.timestamp.desc())
    result = paginate(query, page, per_page)

    logs = []
    for log in result['items']:
        logs.append({
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
        })

    return jsonify({
        'logs': logs,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200
