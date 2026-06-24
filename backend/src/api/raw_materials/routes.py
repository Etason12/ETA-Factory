from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import BOMItem, Product, RawMaterial, Unit, db
from utils.helpers import paginate, generate_unique_code, escape_like
from utils.error_handlers import NotFoundError, ValidationError, ConflictError
from api.decorators import permission_required, audit_log
from . import raw_materials_bp


@raw_materials_bp.route('', methods=['GET'])
@jwt_required()
@permission_required('products.view')
def list_raw_materials():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '').strip()
    is_active = request.args.get('is_active', type=int)

    query = RawMaterial.query.filter(RawMaterial.is_deleted == False)

    if search:
        safe = escape_like(search)
        query = query.filter(
            db.or_(
                RawMaterial.name.ilike(f'%{safe}%'),
                RawMaterial.sku.ilike(f'%{safe}%'),
                RawMaterial.description.ilike(f'%{safe}%'),
            )
        )
    if is_active is not None:
        query = query.filter(RawMaterial.is_active == bool(is_active))

    query = query.order_by(RawMaterial.name.asc())
    result = paginate(query, page, per_page)

    items = []
    for rm in result['items']:
        items.append({
            'id': rm.id, 'sku': rm.sku, 'name': rm.name,
            'description': rm.description,
            'cost_price': float(rm.cost_price or 0),
            'unit_id': rm.unit_id,
            'unit_name': rm.unit.name if rm.unit else None,
            'unit_abbreviation': rm.unit.abbreviation if rm.unit else None,
            'is_active': rm.is_active,
            'min_stock_level': float(rm.min_stock_level or 0),
            'max_stock_level': float(rm.max_stock_level or 0),
            'stock_quantity': float(rm.stock_quantity or 0),
            'created_at': rm.created_at.isoformat() if rm.created_at else None,
        })

    return jsonify({
        'raw_materials': items,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@raw_materials_bp.route('', methods=['POST'])
@jwt_required()
@audit_log('create', 'RawMaterial')
@permission_required('products.create')
def create_raw_material():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    sku = data.get('sku', '').strip()
    name = data.get('name', '').strip()
    unit_id = data.get('unit_id')

    if not sku:
        sku = generate_unique_code('RM')
    if not name or not unit_id:
        raise ValidationError('name and unit_id are required')

    if RawMaterial.query.filter(RawMaterial.sku == sku).first():
        raise ConflictError('SKU already exists')

    if not Unit.query.get(unit_id):
        raise ValidationError('Invalid unit_id')

    cost_price = float(data.get('cost_price', 0))
    if cost_price < 0:
        raise ValidationError('cost_price cannot be negative')

    rm = RawMaterial(
        sku=sku,
        name=name,
        description=data.get('description', '').strip(),
        cost_price=cost_price,
        unit_id=unit_id,
        is_active=data.get('is_active', True),
        min_stock_level=data.get('min_stock_level', 0),
        max_stock_level=data.get('max_stock_level', 0),
        stock_quantity=data.get('stock_quantity', 0),
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(rm)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'raw_material': {
        'id': rm.id, 'sku': rm.sku, 'name': rm.name,
        'cost_price': float(rm.cost_price or 0),
    }, 'message': 'Raw material created successfully'}), 201


@raw_materials_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('products.view')
def get_raw_material(id):
    rm = RawMaterial.query.filter(RawMaterial.id == id, RawMaterial.is_deleted == False).first()
    if not rm:
        raise NotFoundError('Raw material not found')

    return jsonify({'raw_material': {
        'id': rm.id, 'sku': rm.sku, 'name': rm.name,
        'description': rm.description,
        'cost_price': float(rm.cost_price or 0),
        'unit_id': rm.unit_id,
        'unit_name': rm.unit.name if rm.unit else None,
        'unit_abbreviation': rm.unit.abbreviation if rm.unit else None,
        'is_active': rm.is_active,
        'min_stock_level': float(rm.min_stock_level or 0),
        'max_stock_level': float(rm.max_stock_level or 0),
        'stock_quantity': float(rm.stock_quantity or 0),
        'created_at': rm.created_at.isoformat() if rm.created_at else None,
        'updated_at': rm.updated_at.isoformat() if rm.updated_at else None,
    }}), 200


@raw_materials_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@audit_log('update', 'RawMaterial', entity_getter=lambda id, **kw: RawMaterial.query.get(id))
@permission_required('products.edit')
def update_raw_material(id):
    rm = RawMaterial.query.filter(RawMaterial.id == id, RawMaterial.is_deleted == False).first()
    if not rm:
        raise NotFoundError('Raw material not found')

    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    sku = data.get('sku', '').strip()
    if sku and sku != rm.sku:
        if RawMaterial.query.filter(RawMaterial.sku == sku, RawMaterial.id != id).first():
            raise ConflictError('SKU already exists')
        rm.sku = sku

    if data.get('name'):
        rm.name = data['name'].strip()
    if data.get('description') is not None:
        rm.description = data['description'].strip()
    if data.get('cost_price') is not None:
        new_cost = float(data['cost_price'])
        if new_cost < 0:
            raise ValidationError('cost_price cannot be negative')
        rm.cost_price = new_cost

        # Recalculate cost_price of all products using this raw material in their BOM
        bom_items = BOMItem.query.filter(BOMItem.raw_material_id == rm.id).all()
        product_ids = set(bi.product_id for bi in bom_items)
        for pid in product_ids:
            items = BOMItem.query.filter(BOMItem.product_id == pid).all()
            material_cost = sum(
                float(bi.quantity) * float(bi.raw_material.cost_price or 0)
                for bi in items
            )
            product = Product.query.get(pid)
            if product:
                product.cost_price = material_cost
                db.session.add(product)
    if data.get('unit_id'):
        if not Unit.query.get(data['unit_id']):
            raise ValidationError('Invalid unit_id')
        rm.unit_id = data['unit_id']
    if data.get('is_active') is not None:
        rm.is_active = bool(data['is_active'])
    if data.get('min_stock_level') is not None:
        rm.min_stock_level = float(data['min_stock_level'])
    if data.get('max_stock_level') is not None:
        rm.max_stock_level = float(data['max_stock_level'])
    if data.get('stock_quantity') is not None:
        rm.stock_quantity = float(data['stock_quantity'])

    rm.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Raw material updated successfully'}), 200


@raw_materials_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@audit_log('delete', 'RawMaterial')
@permission_required('products.delete')
def delete_raw_material(id):
    rm = RawMaterial.query.filter(RawMaterial.id == id, RawMaterial.is_deleted == False).first()
    if not rm:
        raise NotFoundError('Raw material not found')

    if BOMItem.query.filter_by(raw_material_id=id).first():
        raise ValidationError('Cannot delete raw material used in a BOM')

    from models.models import PurchaseOrderItem
    if PurchaseOrderItem.query.filter_by(raw_material_id=id).first():
        raise ValidationError('Cannot delete raw material linked to purchase orders')

    from datetime import datetime
    rm.name = f"{rm.name}__deleted_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    rm.sku = f"{rm.sku}__deleted_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    rm.soft_delete()
    rm.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Raw material deleted successfully'}), 200
