from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from models.models import Inventory, InventoryLedger, Product, Warehouse, db
from utils.helpers import paginate
from utils.error_handlers import NotFoundError, ValidationError
from api.decorators import permission_required
from . import inventory_bp


@inventory_bp.route('', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def list_inventory():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    product_id = request.args.get('product_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    search = request.args.get('search', '').strip()
    low_stock = request.args.get('low_stock', type=bool)
    grouped = request.args.get('grouped', type=bool)

    if grouped:
        query = db.session.query(
            Inventory.product_id,
            Inventory.warehouse_id,
            func.sum(Inventory.quantity_on_hand).label('quantity_on_hand'),
            func.sum(Inventory.reserved_quantity).label('reserved_quantity'),
        ).group_by(Inventory.product_id, Inventory.warehouse_id)

        if product_id:
            query = query.filter(Inventory.product_id == product_id)
        if warehouse_id:
            query = query.filter(Inventory.warehouse_id == warehouse_id)
        if search:
            query = query.join(Product).filter(
                db.or_(
                    Product.name.ilike(f'%{search}%'),
                    Product.sku.ilike(f'%{search}%'),
                )
            )
        query = query.order_by(Inventory.warehouse_id, Inventory.product_id)
        result = paginate(query, page, per_page)

        products = {p.id: p for p in Product.query.all()}
        warehouses = {w.id: w for w in Warehouse.query.all()}

        items = []
        for row in result['items']:
            product = products.get(row.product_id)
            warehouse = warehouses.get(row.warehouse_id)
            qty = float(row.quantity_on_hand or 0)
            reserved = float(row.reserved_quantity or 0)
            items.append({
                'id': None,
                'product_id': row.product_id,
                'product_name': product.name if product else None,
                'product_sku': product.sku if product else None,
                'warehouse_id': row.warehouse_id,
                'warehouse_name': warehouse.name if warehouse else None,
                'quantity_on_hand': qty,
                'reserved_quantity': reserved,
                'available_quantity': qty - reserved,
                'batch_number': None,
                'min_stock_level': None,
                'max_stock_level': None,
                'is_low_stock': False,
            })

        return jsonify({
            'inventory': items,
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages'],
        }), 200

    query = Inventory.query

    if product_id:
        query = query.filter(Inventory.product_id == product_id)
    if warehouse_id:
        query = query.filter(Inventory.warehouse_id == warehouse_id)
    if search:
        query = query.join(Product).filter(
            db.or_(
                Product.name.ilike(f'%{search}%'),
                Product.sku.ilike(f'%{search}%'),
            )
        )
    if low_stock:
        query = query.join(Product).filter(
            Product.min_stock_level > 0,
            Inventory.quantity_on_hand <= Product.min_stock_level,
        )

    query = query.order_by(Inventory.warehouse_id, Inventory.product_id)
    result = paginate(query, page, per_page)

    items = []
    for inv in result['items']:
        items.append({
            'id': inv.id,
            'product_id': inv.product_id,
            'product_name': inv.product.name if inv.product else None,
            'product_sku': inv.product.sku if inv.product else None,
            'warehouse_id': inv.warehouse_id,
            'warehouse_name': inv.warehouse.name if inv.warehouse else None,
            'quantity_on_hand': float(inv.quantity_on_hand) if inv.quantity_on_hand else 0,
            'reserved_quantity': float(inv.reserved_quantity) if inv.reserved_quantity else 0,
            'available_quantity': inv.available_quantity,
            'batch_number': inv.batch_number,
            'min_stock_level': float(inv.product.min_stock_level) if inv.product and inv.product.min_stock_level else 0,
            'max_stock_level': float(inv.product.max_stock_level) if inv.product and inv.product.max_stock_level else 0,
            'is_low_stock': inv.is_low_stock,
        })

    return jsonify({
        'inventory': items,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@inventory_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def get_inventory_item(id):
    inv = Inventory.query.get(id)
    if not inv:
        raise NotFoundError('Inventory item not found')

    return jsonify({'inventory': {
        'id': inv.id,
        'product_id': inv.product_id,
        'product_name': inv.product.name if inv.product else None,
        'product_sku': inv.product.sku if inv.product else None,
        'warehouse_id': inv.warehouse_id,
        'warehouse_name': inv.warehouse.name if inv.warehouse else None,
        'quantity_on_hand': float(inv.quantity_on_hand) if inv.quantity_on_hand else 0,
        'reserved_quantity': float(inv.reserved_quantity) if inv.reserved_quantity else 0,
        'available_quantity': inv.available_quantity,
        'batch_number': inv.batch_number,
        'min_stock_level': float(inv.min_stock_level) if inv.min_stock_level else 0,
        'max_stock_level': float(inv.max_stock_level) if inv.max_stock_level else 0,
        'is_low_stock': inv.is_low_stock,
    }}), 200


@inventory_bp.route('/warehouse/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def get_warehouse_inventory(id):
    warehouse = Warehouse.query.get(id)
    if not warehouse:
        raise NotFoundError('Warehouse not found')

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Inventory.query.filter_by(warehouse_id=id).order_by(Inventory.product_id)
    result = paginate(query, page, per_page)

    items = []
    for inv in result['items']:
        items.append({
            'id': inv.id,
            'product_id': inv.product_id,
            'product_name': inv.product.name if inv.product else None,
            'product_sku': inv.product.sku if inv.product else None,
            'quantity_on_hand': float(inv.quantity_on_hand) if inv.quantity_on_hand else 0,
            'reserved_quantity': float(inv.reserved_quantity) if inv.reserved_quantity else 0,
            'available_quantity': inv.available_quantity,
            'batch_number': inv.batch_number,
        })

    return jsonify({
        'warehouse_id': id,
        'warehouse_name': warehouse.name,
        'inventory': items,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@inventory_bp.route('/ledger', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def list_ledger():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    product_id = request.args.get('product_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    movement_type = request.args.get('movement_type', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = InventoryLedger.query

    if product_id:
        query = query.filter(InventoryLedger.product_id == product_id)
    if warehouse_id:
        query = query.filter(InventoryLedger.warehouse_id == warehouse_id)
    if movement_type:
        group_map = {
            'in': ['Receipt', 'GRV', 'Opening Balance', 'Return'],
            'out': ['Issue', 'GIV'],
            'adjustment': ['Addition', 'Reduction'],
        }
        types = group_map.get(movement_type, [movement_type])
        query = query.filter(InventoryLedger.movement_type.in_(types))
    if date_from:
        query = query.filter(InventoryLedger.transaction_date >= date_from)
    if date_to:
        query = query.filter(InventoryLedger.transaction_date <= date_to)

    query = query.order_by(InventoryLedger.transaction_date.desc())
    result = paginate(query, page, per_page)

    entries = []
    for e in result['items']:
        entries.append({
            'id': e.id,
            'product_id': e.product_id,
            'product_name': e.product.name if e.product else None,
            'product_sku': e.product.sku if e.product else None,
            'warehouse_id': e.warehouse_id,
            'warehouse_name': e.warehouse.name if e.warehouse else None,
            'movement_type': e.movement_type,
            'quantity': float(e.quantity) if e.quantity else 0,
            'unit_cost': float(e.unit_cost) if e.unit_cost else None,
            'reference_type': e.reference_type,
            'reference_id': e.reference_id,
            'batch_number': e.batch_number,
            'transaction_date': e.transaction_date.isoformat() if e.transaction_date else None,
        })

    return jsonify({
        'ledger_entries': entries,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@inventory_bp.route('/ledger/product/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def get_product_ledger(id):
    product = Product.query.get(id)
    if not product:
        raise NotFoundError('Product not found')

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = InventoryLedger.query.filter_by(product_id=id).order_by(InventoryLedger.transaction_date.desc())
    result = paginate(query, page, per_page)

    entries = []
    for e in result['items']:
        entries.append({
            'id': e.id,
            'warehouse_id': e.warehouse_id,
            'warehouse_name': e.warehouse.name if e.warehouse else None,
            'movement_type': e.movement_type,
            'quantity': float(e.quantity) if e.quantity else 0,
            'unit_cost': float(e.unit_cost) if e.unit_cost else None,
            'reference_type': e.reference_type,
            'reference_id': e.reference_id,
            'batch_number': e.batch_number,
            'transaction_date': e.transaction_date.isoformat() if e.transaction_date else None,
        })

    return jsonify({
        'product_id': id,
        'product_name': product.name,
        'product_sku': product.sku,
        'ledger_entries': entries,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@inventory_bp.route('/opening-balances', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def list_opening_balances():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)

    query = InventoryLedger.query.filter_by(movement_type='Opening Balance')
    if warehouse_id:
        query = query.filter(InventoryLedger.warehouse_id == warehouse_id)

    query = query.order_by(InventoryLedger.transaction_date.desc())
    result = paginate(query, page, per_page)

    entries = []
    for e in result['items']:
        entries.append({
            'id': e.id,
            'product_id': e.product_id,
            'product_name': e.product.name if e.product else None,
            'product_sku': e.product.sku if e.product else None,
            'warehouse_id': e.warehouse_id,
            'warehouse_name': e.warehouse.name if e.warehouse else None,
            'quantity': float(e.quantity) if e.quantity else 0,
            'unit_cost': float(e.unit_cost) if e.unit_cost else None,
            'batch_number': e.batch_number,
            'transaction_date': e.transaction_date.isoformat() if e.transaction_date else None,
        })

    return jsonify({
        'opening_balances': entries,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@inventory_bp.route('/opening-balances', methods=['POST'])
@jwt_required()
@permission_required('inventory.adjust')
def set_opening_balances():
    from services.inventory_service import InventoryService

    data = request.get_json()
    if not data or not isinstance(data, list):
        raise ValidationError('Expected a list of opening balance items')

    inv_service = InventoryService()
    user_id = int(get_jwt_identity())
    results = []

    try:
        for item in data:
            product_id = item.get('product_id')
            warehouse_id = item.get('warehouse_id')
            quantity = item.get('quantity')

            if not product_id or not warehouse_id or quantity is None:
                raise ValidationError('Each item must have product_id, warehouse_id, and quantity')

            inv = inv_service.set_opening_balance(
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity=float(quantity),
                batch_number=item.get('batch_number'),
                unit_cost=float(item['unit_cost']) if item.get('unit_cost') else None,
                created_by_id=user_id,
            )
            results.append({
                'product_id': product_id,
                'warehouse_id': warehouse_id,
                'quantity': float(quantity),
                'inventory_id': inv.id,
            })
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Opening balances set successfully', 'items': results}), 201


@inventory_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@permission_required('inventory.adjust')
def update_inventory_item(id):
    inv = Inventory.query.get(id)
    if not inv:
        raise NotFoundError('Inventory item not found')

    data = request.get_json() or {}
    if 'min_stock_level' in data:
        inv.min_stock_level = float(data['min_stock_level'])
    if 'max_stock_level' in data:
        inv.max_stock_level = float(data['max_stock_level'])

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({'message': 'Inventory item updated'}), 200


@inventory_bp.route('/low-stock', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def list_low_stock():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)

    query = Inventory.query.join(Product).filter(
        Product.min_stock_level > 0,
        Inventory.quantity_on_hand <= Product.min_stock_level,
    )
    if warehouse_id:
        query = query.filter(Inventory.warehouse_id == warehouse_id)

    query = query.order_by(
            (Inventory.quantity_on_hand - Product.min_stock_level).asc()
    )
    result = paginate(query, page, per_page)

    items = []
    for inv in result['items']:
        min_level = float(inv.product.min_stock_level) if inv.product and inv.product.min_stock_level else 0
        items.append({
            'id': inv.id,
            'product_id': inv.product_id,
            'product_name': inv.product.name if inv.product else None,
            'product_sku': inv.product.sku if inv.product else None,
            'warehouse_id': inv.warehouse_id,
            'warehouse_name': inv.warehouse.name if inv.warehouse else None,
            'quantity_on_hand': float(inv.quantity_on_hand) if inv.quantity_on_hand else 0,
            'min_stock_level': min_level,
            'shortage': max(0, min_level - float(inv.quantity_on_hand or 0)),
        })

    return jsonify({
        'low_stock_items': items,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@inventory_bp.route('/summary', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def inventory_summary():
    total_products = Product.query.filter_by(is_active=True).count()
    total_warehouses = Warehouse.query.filter_by(is_active=True).count()

    all_inventory = Inventory.query.all()
    total_items = len(all_inventory)
    total_on_hand = sum(float(i.quantity_on_hand or 0) for i in all_inventory)
    total_reserved = sum(float(i.reserved_quantity or 0) for i in all_inventory)

    low_stock_count = sum(1 for i in all_inventory if i.is_low_stock)

    recent = InventoryLedger.query.order_by(InventoryLedger.transaction_date.desc()).limit(10).all()
    recent_movements = []
    for e in recent:
        recent_movements.append({
            'id': e.id,
            'product_name': e.product.name if e.product else None,
            'product_sku': e.product.sku if e.product else None,
            'warehouse_name': e.warehouse.name if e.warehouse else None,
            'movement_type': e.movement_type,
            'quantity': float(e.quantity) if e.quantity else 0,
            'transaction_date': e.transaction_date.isoformat() if e.transaction_date else None,
        })

    return jsonify({
        'total_products': total_products,
        'total_warehouses': total_warehouses,
        'total_inventory_items': total_items,
        'total_quantity_on_hand': total_on_hand,
        'total_reserved_quantity': total_reserved,
        'low_stock_count': low_stock_count,
        'recent_movements': recent_movements,
    }), 200


@inventory_bp.route('/bin-card', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def bin_card():
    product_id = request.args.get('product_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    if not product_id:
        raise ValidationError('product_id is required')
    if not warehouse_id:
        raise ValidationError('warehouse_id is required')
    if not year or not month:
        from datetime import date
        today = date.today()
        year = year or today.year
        month = month or today.month

    product = Product.query.get(product_id)
    if not product:
        raise NotFoundError('Product not found')
    warehouse = Warehouse.query.get(warehouse_id)
    if not warehouse:
        raise NotFoundError('Warehouse not found')

    from datetime import datetime
    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1)
    else:
        month_end = datetime(year, month + 1, 1)

    before_month = InventoryLedger.query.filter(
        InventoryLedger.product_id == product_id,
        InventoryLedger.warehouse_id == warehouse_id,
        InventoryLedger.transaction_date < month_start,
    ).with_entities(db.func.sum(InventoryLedger.quantity)).scalar() or 0

    month_entries = InventoryLedger.query.filter(
        InventoryLedger.product_id == product_id,
        InventoryLedger.warehouse_id == warehouse_id,
        InventoryLedger.transaction_date >= month_start,
        InventoryLedger.transaction_date < month_end,
    ).order_by(InventoryLedger.transaction_date.asc()).all()

    opening_balance = float(before_month)
    running = opening_balance
    entries = []
    for e in month_entries:
        qty = float(e.quantity)
        running += qty
        entries.append({
            'id': e.id,
            'date': e.transaction_date.isoformat() if e.transaction_date else None,
            'movement_type': e.movement_type,
            'reference_type': e.reference_type,
            'reference_id': e.reference_id,
            'quantity': qty,
            'running_balance': running,
            'batch_number': e.batch_number,
        })

    has_opening = InventoryLedger.query.filter_by(
        product_id=product_id, warehouse_id=warehouse_id, movement_type='Opening Balance'
    ).first() is not None

    closing_balance = running if entries else opening_balance

    return jsonify({
        'product_id': product_id,
        'product_name': product.name,
        'product_sku': product.sku,
        'warehouse_id': warehouse_id,
        'warehouse_name': warehouse.name,
        'has_opening_balance': has_opening,
        'year': year,
        'month': month,
        'opening_balance': opening_balance,
        'closing_balance': closing_balance,
        'total_inflow': sum(e['quantity'] for e in entries if e['quantity'] > 0),
        'total_outflow': abs(sum(e['quantity'] for e in entries if e['quantity'] < 0)),
        'entries': entries,
    }), 200
