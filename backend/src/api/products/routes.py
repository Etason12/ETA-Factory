from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import Product, ProductCategory, Unit, db
from utils.helpers import paginate, generate_unique_code
from utils.error_handlers import NotFoundError, ValidationError, ConflictError
from api.decorators import role_required, permission_required, audit_log
from . import products_bp


@products_bp.route('', methods=['GET'])
@jwt_required()
@permission_required('products.view')
def list_products():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)
    unit_id = request.args.get('unit_id', type=int)
    is_active = request.args.get('is_active', type=int)

    query = Product.query.filter(Product.is_deleted == False)

    if search:
        query = query.filter(
            db.or_(
                Product.name.ilike(f'%{search}%'),
                Product.sku.ilike(f'%{search}%'),
                Product.description.ilike(f'%{search}%'),
            )
        )
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if unit_id:
        query = query.filter(Product.unit_id == unit_id)
    if is_active is not None:
        query = query.filter(Product.is_active == bool(is_active))

    query = query.order_by(Product.name.asc())
    result = paginate(query, page, per_page)

    products = []
    for p in result['items']:
        products.append({
            'id': p.id, 'sku': p.sku, 'name': p.name,
            'description': p.description,
            'unit_price': float(p.unit_price) if p.unit_price else 0,
            'cost_price': float(p.cost_price) if p.cost_price else 0,
            'category_id': p.category_id,
            'category_name': p.category.name if p.category else None,
            'unit_id': p.unit_id,
            'unit_name': p.unit.name if p.unit else None,
            'unit_abbreviation': p.unit.abbreviation if p.unit else None,
            'is_active': p.is_active,
            'min_stock_level': float(p.min_stock_level) if p.min_stock_level else 0,
            'max_stock_level': float(p.max_stock_level) if p.max_stock_level else 0,
            'created_at': p.created_at.isoformat() if p.created_at else None,
        })

    return jsonify({
        'products': products,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@products_bp.route('', methods=['POST'])
@jwt_required()
@audit_log('create', 'Product')
@permission_required('products.create')
def create_product():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    sku = data.get('sku', '').strip()
    name = data.get('name', '').strip()
    category_id = data.get('category_id')
    unit_id = data.get('unit_id')

    if not sku:
        sku = generate_unique_code('SKU')
    if not name or not category_id or not unit_id:
        raise ValidationError('name, category_id, and unit_id are required')

    if Product.query.filter(Product.sku == sku).first():
        raise ConflictError('SKU already exists')

    if not ProductCategory.query.get(category_id):
        raise ValidationError('Invalid category_id')
    if not Unit.query.get(unit_id):
        raise ValidationError('Invalid unit_id')

    product = Product(
        sku=sku,
        name=name,
        description=data.get('description', '').strip(),
        unit_price=data.get('unit_price', 0),
        cost_price=data.get('cost_price', 0),
        category_id=category_id,
        unit_id=unit_id,
        is_active=data.get('is_active', True),
        min_stock_level=data.get('min_stock_level', 0),
        max_stock_level=data.get('max_stock_level', 0),
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(product)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'product': {
        'id': product.id, 'sku': product.sku, 'name': product.name,
        'unit_price': float(product.unit_price),
        'cost_price': float(product.cost_price),
    }, 'message': 'Product created successfully'}), 201


@products_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('products.view')
def get_product(id):
    product = Product.query.filter(Product.id == id, Product.is_deleted == False).first()
    if not product:
        raise NotFoundError('Product not found')

    return jsonify({'product': {
        'id': product.id, 'sku': product.sku, 'name': product.name,
        'description': product.description,
        'unit_price': float(product.unit_price) if product.unit_price else 0,
        'cost_price': float(product.cost_price) if product.cost_price else 0,
        'category_id': product.category_id,
        'category_name': product.category.name if product.category else None,
        'unit_id': product.unit_id,
        'unit_name': product.unit.name if product.unit else None,
        'unit_abbreviation': product.unit.abbreviation if product.unit else None,
        'is_active': product.is_active,
        'min_stock_level': float(product.min_stock_level) if product.min_stock_level else 0,
        'max_stock_level': float(product.max_stock_level) if product.max_stock_level else 0,
        'created_at': product.created_at.isoformat() if product.created_at else None,
        'updated_at': product.updated_at.isoformat() if product.updated_at else None,
    }}), 200


@products_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@audit_log('update', 'Product')
@permission_required('products.edit')
def update_product(id):
    product = Product.query.filter(Product.id == id, Product.is_deleted == False).first()
    if not product:
        raise NotFoundError('Product not found')

    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    sku = data.get('sku', '').strip()
    if sku and sku != product.sku:
        if Product.query.filter(Product.sku == sku, Product.id != id).first():
            raise ConflictError('SKU already exists')
        product.sku = sku

    if data.get('name'):
        product.name = data['name'].strip()
    if data.get('description') is not None:
        product.description = data['description'].strip()
    if data.get('unit_price') is not None:
        product.unit_price = data['unit_price']
    if data.get('cost_price') is not None:
        product.cost_price = data['cost_price']
    if data.get('category_id'):
        if not ProductCategory.query.get(data['category_id']):
            raise ValidationError('Invalid category_id')
        product.category_id = data['category_id']
    if data.get('unit_id'):
        if not Unit.query.get(data['unit_id']):
            raise ValidationError('Invalid unit_id')
        product.unit_id = data['unit_id']
    if data.get('is_active') is not None:
        product.is_active = bool(data['is_active'])
    if data.get('min_stock_level') is not None:
        product.min_stock_level = float(data['min_stock_level'])
    if data.get('max_stock_level') is not None:
        product.max_stock_level = float(data['max_stock_level'])

    product.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Product updated successfully'}), 200


@products_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@audit_log('delete', 'Product')
@permission_required('products.delete')
def delete_product(id):
    product = Product.query.filter(Product.id == id, Product.is_deleted == False).first()
    if not product:
        raise NotFoundError('Product not found')

    product.soft_delete()
    product.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Product deleted successfully'}), 200


@products_bp.route('/categories', methods=['GET'])
@jwt_required()
@permission_required('products.view')
def list_categories():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = ProductCategory.query.filter(ProductCategory.is_deleted == False).order_by(ProductCategory.name.asc())
    result = paginate(query, page, per_page)

    categories = []
    for c in result['items']:
        categories.append({
            'id': c.id, 'name': c.name, 'description': c.description,
        })

    return jsonify({
        'categories': categories,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@products_bp.route('/categories/<int:id>', methods=['PUT'])
@jwt_required()
@audit_log('update', 'Product')
@permission_required('products.edit')
def update_category(id):
    category = ProductCategory.query.filter(ProductCategory.id == id, ProductCategory.is_deleted == False).first()
    if not category:
        raise NotFoundError('Category not found')

    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    name = data.get('name', '').strip()
    if name:
        existing = ProductCategory.query.filter(ProductCategory.name == name, ProductCategory.id != id).first()
        if existing:
            raise ConflictError('Category name already exists')
        category.name = name

    if data.get('description') is not None:
        category.description = data['description'].strip()

    category.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'category': {'id': category.id, 'name': category.name, 'description': category.description},
                    'message': 'Category updated successfully'}), 200


@products_bp.route('/categories/<int:id>', methods=['DELETE'])
@jwt_required()
@audit_log('delete', 'Product')
@permission_required('products.delete')
def delete_category(id):
    category = ProductCategory.query.filter(ProductCategory.id == id, ProductCategory.is_deleted == False).first()
    if not category:
        raise NotFoundError('Category not found')

    from datetime import datetime
    category.name = f"{category.name}__deleted_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    category.soft_delete()
    category.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Category deleted successfully'}), 200


@products_bp.route('/categories', methods=['POST'])
@jwt_required()
@audit_log('create', 'Product')
@permission_required('products.create')
def create_category():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    name = data.get('name', '').strip()
    if not name:
        raise ValidationError('name is required')

    if ProductCategory.query.filter(ProductCategory.name == name, ProductCategory.is_deleted == False).first():
        raise ConflictError('Category name already exists')

    category = ProductCategory(
        name=name,
        description=data.get('description', '').strip(),
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(category)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'category': {'id': category.id, 'name': category.name, 'description': category.description},
                    'message': 'Category created successfully'}), 201


@products_bp.route('/units', methods=['GET'])
@jwt_required()
@permission_required('products.view')
def list_units():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Unit.query.order_by(Unit.name.asc())
    result = paginate(query, page, per_page)

    units = []
    for u in result['items']:
        units.append({'id': u.id, 'name': u.name, 'abbreviation': u.abbreviation})

    return jsonify({
        'units': units,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@products_bp.route('/units/<int:id>', methods=['PUT'])
@jwt_required()
@audit_log('update', 'Product')
@permission_required('products.edit')
def update_unit(id):
    unit = Unit.query.get(id)
    if not unit:
        raise NotFoundError('Unit not found')

    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    name = data.get('name', '').strip()
    if name:
        existing = Unit.query.filter(Unit.name == name, Unit.id != id).first()
        if existing:
            raise ConflictError('Unit name already exists')
        unit.name = name

    abbreviation = data.get('abbreviation', '').strip()
    if abbreviation:
        unit.abbreviation = abbreviation

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'unit': {'id': unit.id, 'name': unit.name, 'abbreviation': unit.abbreviation},
                    'message': 'Unit updated successfully'}), 200


@products_bp.route('/units/<int:id>', methods=['DELETE'])
@jwt_required()
@audit_log('delete', 'Product')
@permission_required('products.delete')
def delete_unit(id):
    unit = Unit.query.get(id)
    if not unit:
        raise NotFoundError('Unit not found')

    if Product.query.filter(Product.unit_id == id, Product.is_deleted == False).first():
        raise ValidationError('Cannot delete unit that is assigned to products')

    db.session.delete(unit)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Unit deleted successfully'}), 200


@products_bp.route('/units', methods=['POST'])
@jwt_required()
@audit_log('create', 'Product')
@permission_required('products.create')
def create_unit():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    name = data.get('name', '').strip()
    abbreviation = data.get('abbreviation', '').strip()

    if not name or not abbreviation:
        raise ValidationError('name and abbreviation are required')

    if Unit.query.filter(Unit.name == name).first():
        raise ConflictError('Unit name already exists')

    unit = Unit(name=name, abbreviation=abbreviation)
    db.session.add(unit)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'unit': {'id': unit.id, 'name': unit.name, 'abbreviation': unit.abbreviation},
                    'message': 'Unit created successfully'}), 201
