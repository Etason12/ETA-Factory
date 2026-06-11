from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import Branch, db
from utils.helpers import paginate, generate_unique_code
from utils.error_handlers import NotFoundError, ValidationError, ConflictError
from api.decorators import role_required, permission_required, audit_log
from . import branches_bp


@branches_bp.route('', methods=['GET'])
@jwt_required()
@permission_required('branches.view')
def list_branches():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '').strip()
    is_active = request.args.get('is_active', type=int)

    query = Branch.query.filter(Branch.is_deleted == False)

    if search:
        query = query.filter(
            db.or_(
                Branch.name.ilike(f'%{search}%'),
                Branch.code.ilike(f'%{search}%'),
                Branch.city.ilike(f'%{search}%'),
            )
        )
    if is_active is not None:
        query = query.filter(Branch.is_active == bool(is_active))

    query = query.order_by(Branch.name.asc())
    result = paginate(query, page, per_page)

    branches = []
    for b in result['items']:
        branches.append({
            'id': b.id, 'name': b.name, 'code': b.code,
            'city': b.city, 'address': b.address,
            'phone': b.phone, 'email': b.email,
            'is_active': b.is_active,
            'created_at': b.created_at.isoformat() if b.created_at else None,
        })

    return jsonify({
        'branches': branches,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@branches_bp.route('', methods=['POST'])
@jwt_required()
@audit_log('create', 'Branch')
@permission_required('branches.create')
def create_branch():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    name = data.get('name', '').strip()
    code = data.get('code', '').strip()

    if not code:
        code = generate_unique_code('BR')
    if not name:
        raise ValidationError('name is required')

    if Branch.query.filter(Branch.code == code).first():
        raise ConflictError('Branch code already exists')

    branch = Branch(
        name=name,
        code=code,
        city=data.get('city', '').strip(),
        address=data.get('address', '').strip(),
        phone=data.get('phone', '').strip(),
        email=data.get('email', '').strip(),
        is_active=data.get('is_active', True),
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(branch)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'branch': {
        'id': branch.id, 'name': branch.name, 'code': branch.code,
        'city': branch.city, 'address': branch.address,
        'phone': branch.phone, 'email': branch.email,
        'is_active': branch.is_active,
    }, 'message': 'Branch created successfully'}), 201


@branches_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('branches.view')
def get_branch(id):
    branch = Branch.query.filter(Branch.id == id, Branch.is_deleted == False).first()
    if not branch:
        raise NotFoundError('Branch not found')

    return jsonify({'branch': {
        'id': branch.id, 'name': branch.name, 'code': branch.code,
        'city': branch.city, 'address': branch.address,
        'phone': branch.phone, 'email': branch.email,
        'is_active': branch.is_active,
        'created_at': branch.created_at.isoformat() if branch.created_at else None,
        'updated_at': branch.updated_at.isoformat() if branch.updated_at else None,
    }}), 200


@branches_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@audit_log('update', 'Branch')
@permission_required('branches.edit')
def update_branch(id):
    branch = Branch.query.filter(Branch.id == id, Branch.is_deleted == False).first()
    if not branch:
        raise NotFoundError('Branch not found')

    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    code = data.get('code', '').strip()
    if code and code != branch.code:
        if Branch.query.filter(Branch.code == code, Branch.id != id).first():
            raise ConflictError('Branch code already exists')
        branch.code = code

    if data.get('name'):
        branch.name = data['name'].strip()
    if data.get('city') is not None:
        branch.city = data['city'].strip()
    if data.get('address') is not None:
        branch.address = data['address'].strip()
    if data.get('phone') is not None:
        branch.phone = data['phone'].strip()
    if data.get('email') is not None:
        branch.email = data['email'].strip()
    if data.get('is_active') is not None:
        branch.is_active = bool(data['is_active'])

    branch.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Branch updated successfully'}), 200


@branches_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@audit_log('delete', 'Branch')
@permission_required('branches.delete')
def delete_branch(id):
    branch = Branch.query.filter(Branch.id == id, Branch.is_deleted == False).first()
    if not branch:
        raise NotFoundError('Branch not found')

    branch.soft_delete()
    branch.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Branch deleted successfully'}), 200
