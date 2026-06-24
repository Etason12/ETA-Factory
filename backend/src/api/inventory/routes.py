from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from models.models import Inventory, InventoryLedger, Product, RawMaterial, RawMaterialInventory, RawMaterialLedger, Warehouse, db
from utils.helpers import paginate, escape_like
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
            safe = escape_like(search)
            query = query.join(Product).filter(
                db.or_(
                    Product.name.ilike(f'%{safe}%'),
                    Product.sku.ilike(f'%{safe}%'),
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
        safe = escape_like(search)
        query = query.join(Product).filter(
            db.or_(
                Product.name.ilike(f'%{safe}%'),
                Product.sku.ilike(f'%{safe}%'),
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
            unit_cost = item.get('unit_cost')

            if not product_id or not warehouse_id or quantity is None:
                raise ValidationError('Each item must have product_id, warehouse_id, and quantity')
            
            if float(quantity) < 0:
                raise ValidationError(f'Quantity for product {product_id} cannot be negative')
            
            if unit_cost is not None and float(unit_cost) < 0:
                raise ValidationError(f'Unit cost for product {product_id} cannot be negative')

            inv = inv_service.set_opening_balance(
                product_id=product_id,
                warehouse_id=warehouse_id,
                quantity=float(quantity),
                batch_number=item.get('batch_number'),
                unit_cost=float(unit_cost) if unit_cost else None,
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


@inventory_bp.route('/opening-balances/raw-materials', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def list_raw_material_opening_balances():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)

    query = RawMaterialLedger.query.filter_by(movement_type='Opening Balance')
    if warehouse_id:
        query = query.filter(RawMaterialLedger.warehouse_id == warehouse_id)

    query = query.order_by(RawMaterialLedger.transaction_date.desc())
    result = paginate(query, page, per_page)

    entries = []
    for e in result['items']:
        entries.append({
            'id': e.id,
            'raw_material_id': e.raw_material_id,
            'raw_material_name': e.raw_material.name if e.raw_material else None,
            'raw_material_sku': e.raw_material.sku if e.raw_material else None,
            'warehouse_id': e.warehouse_id,
            'warehouse_name': e.warehouse.name if e.warehouse else None,
            'quantity': float(e.quantity) if e.quantity else 0,
            'unit_cost': float(e.unit_cost) if e.unit_cost else None,
            'transaction_date': e.transaction_date.isoformat() if e.transaction_date else None,
        })

    return jsonify({
        'opening_balances': entries,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@inventory_bp.route('/opening-balances/raw-materials', methods=['POST'])
@jwt_required()
@permission_required('inventory.adjust')
def set_raw_material_opening_balances():
    from services.inventory_service import InventoryService

    data = request.get_json()
    if not data or not isinstance(data, list):
        raise ValidationError('Expected a list of opening balance items')

    inv_service = InventoryService()
    user_id = int(get_jwt_identity())
    results = []

    try:
        for item in data:
            raw_material_id = item.get('raw_material_id')
            warehouse_id = item.get('warehouse_id')
            quantity = item.get('quantity')
            unit_cost = item.get('unit_cost')

            if not raw_material_id or not warehouse_id or quantity is None:
                raise ValidationError('Each item must have raw_material_id, warehouse_id, and quantity')

            if float(quantity) < 0:
                raise ValidationError(f'Quantity for raw material {raw_material_id} cannot be negative')

            if unit_cost is not None and float(unit_cost) < 0:
                raise ValidationError(f'Unit cost for raw material {raw_material_id} cannot be negative')

            inv = inv_service.set_raw_material_opening_balance(
                raw_material_id=raw_material_id,
                warehouse_id=warehouse_id,
                quantity=float(quantity),
                unit_cost=float(unit_cost) if unit_cost else None,
                created_by_id=user_id,
            )
            results.append({
                'raw_material_id': raw_material_id,
                'warehouse_id': warehouse_id,
                'quantity': float(quantity),
                'inventory_id': inv.id,
            })
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Raw material opening balances set successfully', 'items': results}), 201


@inventory_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@permission_required('inventory.adjust')
def update_inventory_item(id):
    inv = Inventory.query.get(id)
    if not inv:
        raise NotFoundError('Inventory item not found')

    data = request.get_json() or {}
    
    min_stock = data.get('min_stock_level')
    if min_stock is not None:
        if float(min_stock) < 0:
            raise ValidationError('Minimum stock level cannot be negative')
        inv.min_stock_level = float(min_stock)
        
    max_stock = data.get('max_stock_level')
    if max_stock is not None:
        if float(max_stock) < 0:
            raise ValidationError('Maximum stock level cannot be negative')
        inv.max_stock_level = float(max_stock)

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
    total_warehouses = Warehouse.query.filter(Warehouse.is_deleted == False, Warehouse.is_active == True).count()

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

    # Data for stock by warehouse chart
    warehouse_stock = db.session.query(
        Warehouse.name,
        func.sum(Inventory.quantity_on_hand).label("total")
    ).join(Inventory, Warehouse.id == Inventory.warehouse_id)\
     .group_by(Warehouse.name).all()
    
    warehouse_data = [{"name": name, "value": float(total or 0)} for name, total in warehouse_stock]

    return jsonify({
        "total_products": total_products,
        "total_warehouses": total_warehouses,
        "total_inventory_items": total_items,
        "total_quantity_on_hand": total_on_hand,
        "total_reserved_quantity": total_reserved,
        "low_stock_count": low_stock_count,
        "recent_movements": recent_movements,
        "warehouse_data": warehouse_data,
        "stock_status": [
            {"name": "In Stock", "value": total_items - low_stock_count},
            {"name": "Low Stock", "value": low_stock_count},
        ]
    }), 200


@inventory_bp.route('/warehouse-monthly-report', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def warehouse_monthly_report():
    warehouse_id = request.args.get('warehouse_id', type=int)
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)

    if not warehouse_id:
        raise ValidationError('warehouse_id is required')
    if not year or not month:
        from datetime import date
        today = date.today()
        year = year or today.year
        month = month or today.month

    warehouse = Warehouse.query.get(warehouse_id)
    if not warehouse:
        raise NotFoundError('Warehouse not found')

    from datetime import datetime
    month_start = datetime(year, month, 1)
    if month == 12:
        month_end = datetime(year + 1, 1, 1)
    else:
        month_end = datetime(year, month + 1, 1)

    product_ids = [
        row[0] for row in InventoryLedger.query
        .with_entities(InventoryLedger.product_id)
        .filter(InventoryLedger.warehouse_id == warehouse_id)
        .distinct().all()
    ]

    products = Product.query.filter(Product.id.in_(product_ids)).all() if product_ids else []
    product_map = {p.id: p for p in products}

    before_by_product = dict(
        InventoryLedger.query.with_entities(
            InventoryLedger.product_id,
            db.func.sum(InventoryLedger.quantity).label('total')
        ).filter(
            InventoryLedger.warehouse_id == warehouse_id,
            InventoryLedger.transaction_date < month_start,
        ).group_by(InventoryLedger.product_id).all()
    )

    opening_in_month_by_product = dict(
        InventoryLedger.query.with_entities(
            InventoryLedger.product_id,
            db.func.sum(InventoryLedger.quantity).label('total')
        ).filter(
            InventoryLedger.warehouse_id == warehouse_id,
            InventoryLedger.transaction_date >= month_start,
            InventoryLedger.transaction_date < month_end,
            InventoryLedger.movement_type == 'Opening Balance',
        ).group_by(InventoryLedger.product_id).all()
    )

    inflow_by_product = dict(
        InventoryLedger.query.with_entities(
            InventoryLedger.product_id,
            db.func.sum(InventoryLedger.quantity).label('total')
        ).filter(
            InventoryLedger.warehouse_id == warehouse_id,
            InventoryLedger.product_id.in_(product_ids) if product_ids else True,
            InventoryLedger.transaction_date >= month_start,
            InventoryLedger.transaction_date < month_end,
            InventoryLedger.movement_type != 'Opening Balance',
            InventoryLedger.quantity > 0,
        ).group_by(InventoryLedger.product_id).all()
    )

    outflow_by_product = dict(
        InventoryLedger.query.with_entities(
            InventoryLedger.product_id,
            db.func.abs(db.func.sum(InventoryLedger.quantity)).label('total')
        ).filter(
            InventoryLedger.warehouse_id == warehouse_id,
            InventoryLedger.product_id.in_(product_ids) if product_ids else True,
            InventoryLedger.transaction_date >= month_start,
            InventoryLedger.transaction_date < month_end,
            InventoryLedger.movement_type != 'Opening Balance',
            InventoryLedger.quantity < 0,
        ).group_by(InventoryLedger.product_id).all()
    )

    products_data = []
    totals = {'opening_balance': 0, 'total_inflow': 0, 'total_outflow': 0, 'closing_balance': 0}

    for pid in product_ids:
        product = product_map.get(pid)
        if not product:
            continue
        opening = float(before_by_product.get(pid, 0) or 0) + float(opening_in_month_by_product.get(pid, 0) or 0)
        inflow = float(inflow_by_product.get(pid, 0) or 0)
        outflow = float(outflow_by_product.get(pid, 0) or 0)
        closing = opening + inflow - outflow

        totals['opening_balance'] += opening
        totals['total_inflow'] += inflow
        totals['total_outflow'] += outflow
        totals['closing_balance'] += closing

        products_data.append({
            'product_id': pid,
            'product_name': product.name,
            'product_sku': product.sku,
            'opening_balance': opening,
            'total_inflow': inflow,
            'total_outflow': outflow,
            'closing_balance': closing,
        })

    products_data.sort(key=lambda x: x['product_name'].lower() if x['product_name'] else '')

    return jsonify({
        'warehouse_id': warehouse_id,
        'warehouse_name': warehouse.name,
        'year': year,
        'month': month,
        'products': products_data,
        'totals': totals,
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

    opening_in_month = InventoryLedger.query.filter(
        InventoryLedger.product_id == product_id,
        InventoryLedger.warehouse_id == warehouse_id,
        InventoryLedger.transaction_date >= month_start,
        InventoryLedger.transaction_date < month_end,
        InventoryLedger.movement_type == 'Opening Balance',
    ).with_entities(db.func.sum(InventoryLedger.quantity)).scalar() or 0

    opening_balance = float(before_month) + float(opening_in_month)

    month_entries = InventoryLedger.query.filter(
        InventoryLedger.product_id == product_id,
        InventoryLedger.warehouse_id == warehouse_id,
        InventoryLedger.transaction_date >= month_start,
        InventoryLedger.transaction_date < month_end,
        InventoryLedger.movement_type != 'Opening Balance',
    ).order_by(InventoryLedger.transaction_date.asc()).all()

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

    closing_balance = running

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
