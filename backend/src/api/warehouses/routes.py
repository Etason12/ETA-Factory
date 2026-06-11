from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import date
from models.models import (
    Warehouse, Inventory, InventoryLedger, GoodsReceiveVoucher, GRVItem,
    GoodsIssueVoucher, GIVItem, StockAdjustment, StockAdjustmentItem,
    ReturnVoucher, ReturnVoucherItem, DisposalVoucher, DisposalVoucherItem, Product, db
)
from utils.helpers import paginate, generate_unique_code
from utils.error_handlers import NotFoundError, ValidationError, ConflictError
from api.decorators import role_required, permission_required, branch_required, audit_log
from . import warehouses_bp


@warehouses_bp.route('', methods=['GET'])
@jwt_required()
@permission_required('warehouses.view')
@branch_required()
def list_warehouses():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    branch_id = request.args.get('branch_id', type=int)
    is_active = request.args.get('is_active', type=int)

    query = Warehouse.query.filter(Warehouse.is_deleted == False)

    if branch_id:
        query = query.filter(Warehouse.branch_id == branch_id)
    if is_active is not None:
        query = query.filter(Warehouse.is_active == bool(is_active))

    query = query.order_by(Warehouse.name.asc())
    result = paginate(query, page, per_page)

    warehouses = []
    for w in result['items']:
        warehouses.append({
            'id': w.id, 'name': w.name, 'code': w.code,
            'type': w.type, 'address': w.address,
            'is_active': w.is_active, 'branch_id': w.branch_id,
            'branch_name': w.branch.name if w.branch else None,
        })

    return jsonify({
        'warehouses': warehouses,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@warehouses_bp.route('', methods=['POST'])
@jwt_required()
@audit_log('create', 'Warehouse')
@permission_required('warehouses.create')
def create_warehouse():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    name = data.get('name', '').strip()
    code = data.get('code', '').strip()
    type_ = data.get('type', '').strip()
    branch_id = data.get('branch_id')

    if not code:
        code = generate_unique_code('WH')
    if not name or not type_ or not branch_id:
        raise ValidationError('name, type, and branch_id are required')

    if Warehouse.query.filter(Warehouse.code == code).first():
        raise ConflictError('Warehouse code already exists')

    warehouse = Warehouse(
        name=name,
        code=code,
        type=type_,
        address=data.get('address', '').strip(),
        is_active=data.get('is_active', True),
        branch_id=branch_id,
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(warehouse)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'warehouse': {
        'id': warehouse.id, 'name': warehouse.name, 'code': warehouse.code,
        'type': warehouse.type, 'branch_id': warehouse.branch_id,
    }, 'message': 'Warehouse created successfully'}), 201


@warehouses_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('warehouses.view')
def get_warehouse(id):
    warehouse = Warehouse.query.filter(Warehouse.id == id, Warehouse.is_deleted == False).first()
    if not warehouse:
        raise NotFoundError('Warehouse not found')

    return jsonify({'warehouse': {
        'id': warehouse.id, 'name': warehouse.name, 'code': warehouse.code,
        'type': warehouse.type, 'address': warehouse.address,
        'is_active': warehouse.is_active, 'branch_id': warehouse.branch_id,
        'branch_name': warehouse.branch.name if warehouse.branch else None,
    }}), 200


@warehouses_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@audit_log('update', 'Warehouse')
@permission_required('warehouses.edit')
def update_warehouse(id):
    warehouse = Warehouse.query.filter(Warehouse.id == id, Warehouse.is_deleted == False).first()
    if not warehouse:
        raise NotFoundError('Warehouse not found')

    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    code = data.get('code', '').strip()
    if code and code != warehouse.code:
        if Warehouse.query.filter(Warehouse.code == code, Warehouse.id != id).first():
            raise ConflictError('Warehouse code already exists')
        warehouse.code = code

    if data.get('name'):
        warehouse.name = data['name'].strip()
    if data.get('type'):
        warehouse.type = data['type'].strip()
    if data.get('address') is not None:
        warehouse.address = data['address'].strip()
    if data.get('is_active') is not None:
        warehouse.is_active = bool(data['is_active'])
    if data.get('branch_id'):
        warehouse.branch_id = data['branch_id']

    warehouse.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Warehouse updated successfully'}), 200


@warehouses_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@audit_log('delete', 'Warehouse')
@permission_required('warehouses.delete')
def delete_warehouse(id):
    warehouse = Warehouse.query.filter(Warehouse.id == id, Warehouse.is_deleted == False).first()
    if not warehouse:
        raise NotFoundError('Warehouse not found')

    warehouse.soft_delete()
    warehouse.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Warehouse deleted successfully'}), 200


@warehouses_bp.route('/<int:id>/inventory', methods=['GET'])
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


@warehouses_bp.route('/grv', methods=['POST'])
@jwt_required()
@audit_log('create', 'Warehouse')
@role_required('Owner', 'General Manager', 'Warehouse Manager', 'Store Keeper')
def create_grv():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    voucher_number = data.get('voucher_number', '').strip()
    warehouse_id = data.get('warehouse_id')
    reference_type = data.get('reference_type', '').strip()
    reference_id = data.get('reference_id')
    notes = data.get('notes', '').strip()
    items_data = data.get('items', [])

    if not voucher_number:
        voucher_number = generate_unique_code('GRV')
    if not warehouse_id:
        raise ValidationError('warehouse_id is required')

    if GoodsReceiveVoucher.query.filter(GoodsReceiveVoucher.voucher_number == voucher_number).first():
        raise ConflictError('Voucher number already exists')

    if not items_data:
        raise ValidationError('At least one item is required')

    voucher = GoodsReceiveVoucher(
        voucher_number=voucher_number,
        warehouse_id=warehouse_id,
        reference_type=reference_type,
        reference_id=reference_id,
        notes=notes,
        received_by_id=int(get_jwt_identity()),
    )
    db.session.add(voucher)
    db.session.flush()

    for item in items_data:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        if not product_id or not quantity:
            raise ValidationError('Each item requires product_id and quantity')
        grv_item = GRVItem(
            grv_id=voucher.id,
            product_id=product_id,
            quantity=quantity,
            unit_cost=item.get('unit_cost'),
            batch_number=item.get('batch_number', '').strip(),
        )
        db.session.add(grv_item)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({'message': 'GRV created successfully', 'grv_id': voucher.id}), 201


@warehouses_bp.route('/grv', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def list_grvs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    status = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = GoodsReceiveVoucher.query

    if warehouse_id:
        query = query.filter(GoodsReceiveVoucher.warehouse_id == warehouse_id)
    if status:
        query = query.filter(GoodsReceiveVoucher.status == status)
    if date_from:
        query = query.filter(GoodsReceiveVoucher.voucher_date >= date_from)
    if date_to:
        query = query.filter(GoodsReceiveVoucher.voucher_date <= date_to)

    query = query.order_by(GoodsReceiveVoucher.created_at.desc())
    result = paginate(query, page, per_page)

    vouchers = []
    for v in result['items']:
        vouchers.append({
            'id': v.id, 'voucher_number': v.voucher_number,
            'warehouse_id': v.warehouse_id,
            'warehouse_name': v.warehouse.name if v.warehouse else None,
            'voucher_date': v.voucher_date.isoformat() if v.voucher_date else None,
            'reference_type': v.reference_type,
            'reference_id': v.reference_id,
            'status': v.status,
            'notes': v.notes,
            'created_by_name': v.creator.full_name if v.creator else None,
            'received_by_name': v.receiver.full_name if v.receiver else None,
        })

    return jsonify({
        'grvs': vouchers,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@warehouses_bp.route('/grv/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def get_grv(id):
    voucher = GoodsReceiveVoucher.query.get(id)
    if not voucher:
        raise NotFoundError('GRV not found')

    items = []
    for item in voucher.items:
        items.append({
            'id': item.id,
            'product_id': item.product_id,
            'product_name': item.product.name if item.product else None,
            'product_sku': item.product.sku if item.product else None,
            'quantity': float(item.quantity) if item.quantity else 0,
            'unit_cost': float(item.unit_cost) if item.unit_cost else None,
            'batch_number': item.batch_number,
        })

    return jsonify({'grv': {
        'id': voucher.id, 'voucher_number': voucher.voucher_number,
        'warehouse_id': voucher.warehouse_id,
        'warehouse_name': voucher.warehouse.name if voucher.warehouse else None,
        'voucher_date': voucher.voucher_date.isoformat() if voucher.voucher_date else None,
        'reference_type': voucher.reference_type,
        'reference_id': voucher.reference_id,
        'status': voucher.status,
        'notes': voucher.notes,
        'created_by_name': voucher.creator.full_name if voucher.creator else None,
        'received_by_name': voucher.receiver.full_name if voucher.receiver else None,
        'items': items,
    }    }), 200


@warehouses_bp.route('/grv/<int:id>/approve', methods=['PUT'])
@jwt_required()
@audit_log('approve', 'Warehouse')
@permission_required('inventory.edit')
def approve_grv(id):
    voucher = GoodsReceiveVoucher.query.get(id)
    if not voucher:
        raise NotFoundError('GRV not found')
    if voucher.status != 'Draft':
        raise ValidationError(f'Cannot approve GRV with status: {voucher.status}')

    voucher.status = 'Completed'
    db.session.flush()

    for item in voucher.items:
        inv = Inventory.query.filter_by(
            product_id=item.product_id,
            warehouse_id=voucher.warehouse_id,
            batch_number=item.batch_number or '',
        ).first()
        if inv:
            inv.quantity_on_hand = float(inv.quantity_on_hand or 0) + float(item.quantity)
        else:
            inv = Inventory(
                product_id=item.product_id,
                warehouse_id=voucher.warehouse_id,
                quantity_on_hand=item.quantity,
                batch_number=item.batch_number or '',
            )
            db.session.add(inv)
        db.session.flush()

        ledger = InventoryLedger(
            product_id=item.product_id,
            warehouse_id=voucher.warehouse_id,
            movement_type='GRV',
            quantity=item.quantity,
            unit_cost=item.unit_cost,
            reference_type=voucher.reference_type or 'GRV',
            reference_id=voucher.id,
            batch_number=item.batch_number or '',
        )
        db.session.add(ledger)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({'message': 'GRV approved successfully'}), 200


@warehouses_bp.route('/giv', methods=['POST'])
@jwt_required()
@audit_log('create', 'Warehouse')
@role_required('Owner', 'General Manager', 'Warehouse Manager', 'Store Keeper')
def create_giv():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    voucher_number = data.get('voucher_number', '').strip()
    warehouse_id = data.get('warehouse_id')
    sales_order_id = data.get('sales_order_id')
    reference_type = data.get('reference_type', '').strip()
    reference_id = data.get('reference_id')
    notes = data.get('notes', '').strip()
    items_data = data.get('items', [])

    if not voucher_number:
        voucher_number = generate_unique_code('GIV')
    if not warehouse_id:
        raise ValidationError('warehouse_id is required')

    if GoodsIssueVoucher.query.filter(GoodsIssueVoucher.voucher_number == voucher_number).first():
        raise ConflictError('Voucher number already exists')

    if not items_data:
        raise ValidationError('At least one item is required')

    voucher = GoodsIssueVoucher(
        voucher_number=voucher_number,
        warehouse_id=warehouse_id,
        sales_order_id=sales_order_id,
        reference_type=reference_type,
        reference_id=reference_id,
        notes=notes,
        issued_by_id=int(get_jwt_identity()),
    )
    db.session.add(voucher)
    db.session.flush()

    for item in items_data:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        if not product_id or not quantity:
            raise ValidationError('Each item requires product_id and quantity')
        giv_item = GIVItem(
            giv_id=voucher.id,
            product_id=product_id,
            quantity=quantity,
            batch_number=item.get('batch_number', '').strip(),
        )
        db.session.add(giv_item)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({'message': 'GIV created successfully', 'giv_id': voucher.id}), 201


@warehouses_bp.route('/giv', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def list_givs():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    status = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = GoodsIssueVoucher.query

    if warehouse_id:
        query = query.filter(GoodsIssueVoucher.warehouse_id == warehouse_id)
    if status:
        query = query.filter(GoodsIssueVoucher.status == status)
    if date_from:
        query = query.filter(GoodsIssueVoucher.voucher_date >= date_from)
    if date_to:
        query = query.filter(GoodsIssueVoucher.voucher_date <= date_to)

    query = query.order_by(GoodsIssueVoucher.created_at.desc())
    result = paginate(query, page, per_page)

    vouchers = []
    for v in result['items']:
        vouchers.append({
            'id': v.id, 'voucher_number': v.voucher_number,
            'warehouse_id': v.warehouse_id,
            'warehouse_name': v.warehouse.name if v.warehouse else None,
            'sales_order_id': v.sales_order_id,
            'voucher_date': v.voucher_date.isoformat() if v.voucher_date else None,
            'reference_type': v.reference_type,
            'reference_id': v.reference_id,
            'status': v.status,
            'notes': v.notes,
            'created_by_name': v.creator.full_name if v.creator else None,
            'issued_by_name': v.issuer.full_name if v.issuer else None,
        })

    return jsonify({
        'givs': vouchers,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@warehouses_bp.route('/giv/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def get_giv(id):
    voucher = GoodsIssueVoucher.query.get(id)
    if not voucher:
        raise NotFoundError('GIV not found')

    items = []
    for item in voucher.items:
        items.append({
            'id': item.id,
            'product_id': item.product_id,
            'product_name': item.product.name if item.product else None,
            'product_sku': item.product.sku if item.product else None,
            'quantity': float(item.quantity) if item.quantity else 0,
            'batch_number': item.batch_number,
        })

    return jsonify({'giv': {
        'id': voucher.id, 'voucher_number': voucher.voucher_number,
        'warehouse_id': voucher.warehouse_id,
        'warehouse_name': voucher.warehouse.name if voucher.warehouse else None,
        'sales_order_id': voucher.sales_order_id,
        'voucher_date': voucher.voucher_date.isoformat() if voucher.voucher_date else None,
        'reference_type': voucher.reference_type,
        'reference_id': voucher.reference_id,
        'status': voucher.status,
        'notes': voucher.notes,
        'created_by_name': voucher.creator.full_name if voucher.creator else None,
        'issued_by_name': voucher.issuer.full_name if voucher.issuer else None,
        'items': items,
    }}), 200


@warehouses_bp.route('/giv/<int:id>/approve', methods=['PUT'])
@jwt_required()
@audit_log('approve', 'Warehouse')
@permission_required('inventory.edit')
def approve_giv(id):
    voucher = GoodsIssueVoucher.query.get(id)
    if not voucher:
        raise NotFoundError('GIV not found')
    if voucher.status != 'Draft':
        raise ValidationError(f'Cannot approve GIV with status: {voucher.status}')

    voucher.status = 'Completed'
    db.session.flush()

    for item in voucher.items:
        inv = Inventory.query.filter_by(
            product_id=item.product_id,
            warehouse_id=voucher.warehouse_id,
            batch_number=item.batch_number or '',
        ).first()
        if not inv and not item.batch_number:
            inv = Inventory.query.filter_by(
                product_id=item.product_id,
                warehouse_id=voucher.warehouse_id,
            ).filter(Inventory.batch_number != '').first()
        if not inv:
            raise ValidationError(f'Insufficient stock for product {item.product_id}')
        current_qty = float(inv.quantity_on_hand or 0)
        issue_qty = float(item.quantity)
        if current_qty < issue_qty:
            raise ValidationError(f'Insufficient stock: have {current_qty}, need {issue_qty}')
        inv.quantity_on_hand = current_qty - issue_qty
        db.session.flush()

        ledger = InventoryLedger(
            product_id=item.product_id,
            warehouse_id=voucher.warehouse_id,
            movement_type='GIV',
            quantity=-item.quantity,
            reference_type=voucher.reference_type or 'GIV',
            reference_id=voucher.id,
            batch_number=inv.batch_number,
        )
        db.session.add(ledger)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({'message': 'GIV approved successfully'}), 200


@warehouses_bp.route('/adjustments', methods=['POST'])
@jwt_required()
@audit_log('create', 'Warehouse')
@permission_required('inventory.adjust')
def create_adjustment():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    adjustment_number = data.get('adjustment_number', '').strip()
    warehouse_id = data.get('warehouse_id')
    adjustment_type = data.get('adjustment_type', '').strip()
    notes = data.get('notes', '').strip()
    items_data = data.get('items', [])

    if not adjustment_number:
        adjustment_number = generate_unique_code('ADJ')
    if not warehouse_id or not adjustment_type:
        raise ValidationError('warehouse_id and adjustment_type are required')

    if StockAdjustment.query.filter(StockAdjustment.adjustment_number == adjustment_number).first():
        raise ConflictError('Adjustment number already exists')

    if not items_data:
        raise ValidationError('At least one item is required')

    adjustment = StockAdjustment(
        adjustment_number=adjustment_number,
        warehouse_id=warehouse_id,
        adjustment_type=adjustment_type,
        notes=notes,
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(adjustment)
    db.session.flush()

    for item in items_data:
        product_id = item.get('product_id')
        current_qty = item.get('current_quantity')
        adjusted_qty = item.get('adjusted_quantity')
        if not product_id or current_qty is None or adjusted_qty is None:
            raise ValidationError('Each item requires product_id, current_quantity, and adjusted_quantity')
        adj_item = StockAdjustmentItem(
            adjustment_id=adjustment.id,
            product_id=product_id,
            current_quantity=current_qty,
            adjusted_quantity=adjusted_qty,
            difference=float(adjusted_qty) - float(current_qty),
            batch_number=item.get('batch_number', '').strip(),
        )
        db.session.add(adj_item)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({'message': 'Adjustment created successfully', 'adjustment_id': adjustment.id}), 201


@warehouses_bp.route('/adjustments', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def list_adjustments():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    adjustment_type = request.args.get('adjustment_type', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = StockAdjustment.query

    if warehouse_id:
        query = query.filter(StockAdjustment.warehouse_id == warehouse_id)
    if adjustment_type:
        query = query.filter(StockAdjustment.adjustment_type == adjustment_type)
    if date_from:
        query = query.filter(StockAdjustment.adjustment_date >= date_from)
    if date_to:
        query = query.filter(StockAdjustment.adjustment_date <= date_to)

    query = query.order_by(StockAdjustment.created_at.desc())
    result = paginate(query, page, per_page)

    adjustments = []
    for a in result['items']:
        adjustments.append({
            'id': a.id, 'adjustment_number': a.adjustment_number,
            'warehouse_id': a.warehouse_id,
            'warehouse_name': a.warehouse.name if a.warehouse else None,
            'adjustment_date': a.adjustment_date.isoformat() if a.adjustment_date else None,
            'adjustment_type': a.adjustment_type,
            'status': a.status,
            'notes': a.notes,
        })

    return jsonify({
        'adjustments': adjustments,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@warehouses_bp.route('/returns', methods=['POST'])
@jwt_required()
@audit_log('create', 'Warehouse')
@role_required('Owner', 'General Manager', 'Warehouse Manager', 'Store Keeper')
def create_return():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    return_number = data.get('return_number', '').strip()
    warehouse_id = data.get('warehouse_id')
    customer_id = data.get('customer_id')
    return_type = data.get('return_type', '').strip()
    notes = data.get('notes', '').strip()
    items_data = data.get('items', [])

    if not return_number:
        return_number = generate_unique_code('RET')
    if not warehouse_id or not return_type:
        raise ValidationError('warehouse_id and return_type are required')

    if ReturnVoucher.query.filter(ReturnVoucher.return_number == return_number).first():
        raise ConflictError('Return number already exists')

    if not items_data:
        raise ValidationError('At least one item is required')

    voucher = ReturnVoucher(
        return_number=return_number,
        warehouse_id=warehouse_id,
        customer_id=customer_id,
        return_type=return_type,
        notes=notes,
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(voucher)
    db.session.flush()

    for item in items_data:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        if not product_id or not quantity:
            raise ValidationError('Each item requires product_id and quantity')
        ret_item = ReturnVoucherItem(
            return_voucher_id=voucher.id,
            product_id=product_id,
            quantity=quantity,
            unit_cost=item.get('unit_cost'),
            batch_number=item.get('batch_number', '').strip(),
            reason=item.get('reason', '').strip(),
        )
        db.session.add(ret_item)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({'message': 'Return voucher created successfully', 'return_id': voucher.id}), 201


@warehouses_bp.route('/returns', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def list_returns():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    return_type = request.args.get('return_type', '').strip()

    query = ReturnVoucher.query

    if warehouse_id:
        query = query.filter(ReturnVoucher.warehouse_id == warehouse_id)
    if return_type:
        query = query.filter(ReturnVoucher.return_type == return_type)

    query = query.order_by(ReturnVoucher.created_at.desc())
    result = paginate(query, page, per_page)

    returns = []
    for r in result['items']:
        returns.append({
            'id': r.id, 'return_number': r.return_number,
            'warehouse_id': r.warehouse_id,
            'warehouse_name': r.warehouse.name if r.warehouse else None,
            'customer_id': r.customer_id,
            'return_date': r.return_date.isoformat() if r.return_date else None,
            'return_type': r.return_type,
            'status': r.status,
            'notes': r.notes,
        })

    return jsonify({
        'returns': returns,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@warehouses_bp.route('/disposal', methods=['POST'])
@jwt_required()
@audit_log('create', 'Warehouse')
@permission_required('inventory.edit')
def create_disposal():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    voucher_number = data.get('voucher_number', '').strip()
    warehouse_id = data.get('warehouse_id')
    reason = data.get('reason')
    notes = data.get('notes', '')
    items_data = data.get('items', [])
    voucher_date_str = data.get('voucher_date')
    voucher_date = None
    if voucher_date_str:
        try:
            voucher_date = date.fromisoformat(voucher_date_str)
        except (ValueError, TypeError):
            raise ValidationError('Invalid voucher_date format, expected YYYY-MM-DD')

    if not voucher_number:
        voucher_number = generate_unique_code('DSP')
    if not warehouse_id or not reason:
        raise ValidationError('warehouse_id and reason are required')
    if not items_data:
        raise ValidationError('At least one item is required')

    if DisposalVoucher.query.filter(DisposalVoucher.voucher_number == voucher_number).first():
        raise ConflictError('Voucher number already exists')

    voucher = DisposalVoucher(
        voucher_number=voucher_number,
        warehouse_id=warehouse_id,
        voucher_date=voucher_date or date.today(),
        reason=reason,
        notes=notes,
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(voucher)
    db.session.flush()

    for item in items_data:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        if not product_id or not quantity:
            raise ValidationError('Each item requires product_id and quantity')
        di = DisposalVoucherItem(
            disposal_id=voucher.id,
            product_id=product_id,
            quantity=quantity,
            batch_number=item.get('batch_number', ''),
            reason=item.get('reason', ''),
        )
        db.session.add(di)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Disposal voucher created', 'id': voucher.id}), 201


@warehouses_bp.route('/disposal', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def list_disposal():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    status = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = DisposalVoucher.query.order_by(DisposalVoucher.created_at.desc())

    if warehouse_id:
        query = query.filter(DisposalVoucher.warehouse_id == warehouse_id)
    if status:
        query = query.filter(DisposalVoucher.status == status)
    if date_from:
        query = query.filter(DisposalVoucher.voucher_date >= date_from)
    if date_to:
        query = query.filter(DisposalVoucher.voucher_date <= date_to)

    result = paginate(query, page, per_page)

    items = []
    for dv in result['items']:
        items.append({
            'id': dv.id,
            'voucher_number': dv.voucher_number,
            'warehouse_id': dv.warehouse_id,
            'warehouse_name': dv.warehouse.name if dv.warehouse else None,
            'voucher_date': dv.voucher_date.isoformat() if dv.voucher_date else None,
            'reason': dv.reason,
            'notes': dv.notes,
            'status': dv.status,
            'created_by_name': dv.creator.name if dv.creator else None,
            'disposed_by_name': dv.disposer.name if dv.disposer else None,
            'created_at': dv.created_at.isoformat() if dv.created_at else None,
        })

    return jsonify({
        'items': items,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@warehouses_bp.route('/disposal/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('inventory.view')
def get_disposal(id):
    dv = DisposalVoucher.query.get(id)
    if not dv:
        raise NotFoundError('Disposal voucher not found')

    items_list = []
    for item in dv.items:
        items_list.append({
            'id': item.id,
            'disposal_id': item.disposal_id,
            'product_id': item.product_id,
            'product_name': item.product.name if item.product else None,
            'quantity': float(item.quantity),
            'batch_number': item.batch_number or '',
            'reason': item.reason or '',
        })

    return jsonify({
        'disposal': {
            'id': dv.id,
            'voucher_number': dv.voucher_number,
            'warehouse_id': dv.warehouse_id,
            'warehouse_name': dv.warehouse.name if dv.warehouse else None,
            'voucher_date': dv.voucher_date.isoformat() if dv.voucher_date else None,
            'reason': dv.reason,
            'notes': dv.notes,
            'status': dv.status,
            'created_by_name': dv.creator.name if dv.creator else None,
            'disposed_by_name': dv.disposer.name if dv.disposer else None,
            'items': items_list,
        }
    }), 200


@warehouses_bp.route('/disposal/<int:id>/approve', methods=['PUT'])
@jwt_required()
@audit_log('approve', 'Warehouse')
@permission_required('inventory.edit')
def approve_disposal(id):
    voucher = DisposalVoucher.query.get(id)
    if not voucher:
        raise NotFoundError('Disposal voucher not found')
    if voucher.status != 'Draft':
        raise ValidationError(f'Cannot approve disposal voucher with status: {voucher.status}')

    voucher.status = 'Completed'
    voucher.disposed_by_id = int(get_jwt_identity())
    db.session.flush()

    for item in voucher.items:
        inv = Inventory.query.filter_by(
            product_id=item.product_id,
            warehouse_id=voucher.warehouse_id,
            batch_number=item.batch_number or '',
        ).first()
        if not inv and not item.batch_number:
            inv = Inventory.query.filter_by(
                product_id=item.product_id,
                warehouse_id=voucher.warehouse_id,
            ).filter(Inventory.batch_number != '').first()
        if not inv:
            raise ValidationError(f'Insufficient stock for product {item.product_id}')
        current_qty = float(inv.quantity_on_hand or 0)
        issue_qty = float(item.quantity)
        if current_qty < issue_qty:
            raise ValidationError(f'Insufficient stock: have {current_qty}, need {issue_qty}')
        inv.quantity_on_hand = current_qty - issue_qty
        db.session.flush()

        ledger = InventoryLedger(
            product_id=item.product_id,
            warehouse_id=voucher.warehouse_id,
            movement_type='Disposal',
            quantity=-item.quantity,
            reference_type='Disposal',
            reference_id=voucher.id,
            batch_number=inv.batch_number,
        )
        db.session.add(ledger)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({'message': 'Disposal voucher approved successfully'}), 200
