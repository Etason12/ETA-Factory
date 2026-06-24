from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import Supplier, db
from utils.helpers import paginate, generate_unique_code, escape_like
from utils.error_handlers import NotFoundError, ValidationError, ConflictError
from api.decorators import permission_required, audit_log
from . import suppliers_bp


@suppliers_bp.route('', methods=['GET'])
@jwt_required()
@permission_required('products.view')
def list_suppliers():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '').strip()
    is_active = request.args.get('is_active', type=int)

    query = Supplier.query.filter(Supplier.is_deleted == False)

    if search:
        safe = escape_like(search)
        query = query.filter(
            db.or_(
                Supplier.name.ilike(f'%{safe}%'),
                Supplier.code.ilike(f'%{safe}%'),
                Supplier.contact_person.ilike(f'%{safe}%'),
            )
        )
    if is_active is not None:
        query = query.filter(Supplier.is_active == bool(is_active))

    query = query.order_by(Supplier.name.asc())
    result = paginate(query, page, per_page)

    items = [{
        'id': s.id, 'code': s.code, 'name': s.name,
        'contact_person': s.contact_person,
        'phone': s.phone, 'email': s.email,
        'address': s.address,
        'payment_terms': s.payment_terms,
        'is_active': s.is_active,
        'created_at': s.created_at.isoformat() if s.created_at else None,
    } for s in result['items']]

    return jsonify({
        'suppliers': items,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@suppliers_bp.route('', methods=['POST'])
@jwt_required()
@audit_log('create', 'Supplier')
@permission_required('products.create')
def create_supplier():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    code = data.get('code', '').strip()
    name = data.get('name', '').strip()

    if not code:
        code = generate_unique_code('SUP')
    if not name:
        raise ValidationError('name is required')

    if Supplier.query.filter(Supplier.code == code).first():
        raise ConflictError('Supplier code already exists')

    supplier = Supplier(
        code=code,
        name=name,
        contact_person=data.get('contact_person', '').strip(),
        phone=data.get('phone', '').strip(),
        email=data.get('email', '').strip(),
        address=data.get('address', '').strip(),
        payment_terms=data.get('payment_terms', '').strip(),
        is_active=data.get('is_active', True),
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(supplier)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'supplier': {
        'id': supplier.id, 'code': supplier.code, 'name': supplier.name,
    }, 'message': 'Supplier created successfully'}), 201


@suppliers_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('products.view')
def get_supplier(id):
    supplier = Supplier.query.filter(Supplier.id == id, Supplier.is_deleted == False).first()
    if not supplier:
        raise NotFoundError('Supplier not found')

    return jsonify({'supplier': {
        'id': supplier.id, 'code': supplier.code, 'name': supplier.name,
        'contact_person': supplier.contact_person,
        'phone': supplier.phone, 'email': supplier.email,
        'address': supplier.address,
        'payment_terms': supplier.payment_terms,
        'is_active': supplier.is_active,
        'created_at': supplier.created_at.isoformat() if supplier.created_at else None,
        'updated_at': supplier.updated_at.isoformat() if supplier.updated_at else None,
    }}), 200


@suppliers_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@audit_log('update', 'Supplier')
@permission_required('products.edit')
def update_supplier(id):
    supplier = Supplier.query.filter(Supplier.id == id, Supplier.is_deleted == False).first()
    if not supplier:
        raise NotFoundError('Supplier not found')

    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    code = data.get('code', '').strip()
    if code and code != supplier.code:
        if Supplier.query.filter(Supplier.code == code, Supplier.id != id).first():
            raise ConflictError('Supplier code already exists')
        supplier.code = code

    if data.get('name'):
        supplier.name = data['name'].strip()
    if data.get('contact_person') is not None:
        supplier.contact_person = data['contact_person'].strip()
    if data.get('phone') is not None:
        supplier.phone = data['phone'].strip()
    if data.get('email') is not None:
        supplier.email = data['email'].strip()
    if data.get('address') is not None:
        supplier.address = data['address'].strip()
    if data.get('payment_terms') is not None:
        supplier.payment_terms = data['payment_terms'].strip()
    if data.get('is_active') is not None:
        supplier.is_active = bool(data['is_active'])

    supplier.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Supplier updated successfully'}), 200


@suppliers_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@audit_log('delete', 'Supplier')
@permission_required('products.delete')
def delete_supplier(id):
    supplier = Supplier.query.filter(Supplier.id == id, Supplier.is_deleted == False).first()
    if not supplier:
        raise NotFoundError('Supplier not found')

    from models.models import PurchaseOrder
    if PurchaseOrder.query.filter_by(supplier_id=id).first():
        raise ValidationError('Cannot delete supplier with existing purchase orders')

    from datetime import datetime
    ts = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    supplier.name = f"{supplier.name}__deleted_{ts}"
    supplier.code = f"{supplier.code}__deleted_{ts}"
    supplier.soft_delete()
    supplier.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Supplier deleted successfully'}), 200
