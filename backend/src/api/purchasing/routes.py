from datetime import date, datetime

from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import (
    PurchaseOrder, PurchaseOrderItem, RawMaterial,
    RawMaterialInventory, RawMaterialLedger,
    Supplier, Warehouse, db
)
from utils.helpers import paginate, generate_unique_code
from utils.error_handlers import NotFoundError, ValidationError, ConflictError
from api.decorators import permission_required, audit_log
from . import purchasing_bp


@purchasing_bp.route('/orders', methods=['GET'])
@jwt_required()
@permission_required('products.view')
def list_orders():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    supplier_id = request.args.get('supplier_id', type=int)
    status = request.args.get('status', '').strip()

    query = PurchaseOrder.query

    if supplier_id:
        query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    if status:
        query = query.filter(PurchaseOrder.status == status)

    query = query.order_by(PurchaseOrder.created_at.desc())
    result = paginate(query, page, per_page)

    orders = []
    for po in result['items']:
        orders.append({
            'id': po.id, 'order_number': po.order_number,
            'supplier_id': po.supplier_id,
            'supplier_name': po.supplier.name if po.supplier else None,
            'order_date': po.order_date.isoformat() if po.order_date else None,
            'expected_date': po.expected_date.isoformat() if po.expected_date else None,
            'status': po.status,
            'notes': po.notes,
            'created_at': po.created_at.isoformat() if po.created_at else None,
            'created_by_name': po.creator.full_name if po.creator else None,
            'approved_by_name': po.approver.full_name if po.approver else None,
        })

    return jsonify({
        'orders': orders,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@purchasing_bp.route('/orders', methods=['POST'])
@jwt_required()
@audit_log('create', 'PurchaseOrder')
@permission_required('products.create')
def create_order():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    order_number = data.get('order_number', '').strip()
    supplier_id = data.get('supplier_id')
    notes = data.get('notes', '').strip()

    if not order_number:
        order_number = generate_unique_code('PO')
    if not supplier_id:
        raise ValidationError('supplier_id is required')

    if PurchaseOrder.query.filter(PurchaseOrder.order_number == order_number).first():
        raise ConflictError('Order number already exists')

    if not Supplier.query.get(supplier_id):
        raise ValidationError('Invalid supplier_id')

    order_date = date.fromisoformat(data['order_date']) if data.get('order_date') else date.today()
    expected_date = date.fromisoformat(data['expected_date']) if data.get('expected_date') else None

    po = PurchaseOrder(
        order_number=order_number,
        supplier_id=supplier_id,
        order_date=order_date,
        expected_date=expected_date,
        notes=notes,
        status='Draft',
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(po)
    db.session.flush()

    items_data = data.get('items', [])
    if not items_data:
        db.session.rollback()
        raise ValidationError('At least one item is required')

    total_cost = 0
    for item in items_data:
        rm_id = item.get('raw_material_id')
        qty = item.get('quantity_ordered')
        cost = item.get('unit_cost')

        if not rm_id or not qty or cost is None:
            db.session.rollback()
            raise ValidationError('Each item needs raw_material_id, quantity_ordered, and unit_cost')

        if not RawMaterial.query.get(rm_id):
            db.session.rollback()
            raise ValidationError(f'Invalid raw_material_id: {rm_id}')

        poi = PurchaseOrderItem(
            purchase_order_id=po.id,
            raw_material_id=rm_id,
            quantity_ordered=qty,
            unit_cost=cost,
        )
        db.session.add(poi)
        total_cost += float(qty) * float(cost)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({
        'purchase_order': {'id': po.id, 'order_number': po.order_number},
        'message': 'Purchase order created successfully'
    }), 201


@purchasing_bp.route('/orders/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('products.view')
def get_order(id):
    po = PurchaseOrder.query.get(id)
    if not po:
        raise NotFoundError('Purchase order not found')

    items = []
    for item in po.items:
        items.append({
            'id': item.id,
            'raw_material_id': item.raw_material_id,
            'raw_material_name': item.raw_material.name if item.raw_material else None,
            'raw_material_sku': item.raw_material.sku if item.raw_material else None,
            'quantity_ordered': float(item.quantity_ordered),
            'unit_cost': float(item.unit_cost),
            'quantity_received': float(item.quantity_received),
        })

    return jsonify({'purchase_order': {
        'id': po.id, 'order_number': po.order_number,
        'supplier_id': po.supplier_id,
        'supplier_name': po.supplier.name if po.supplier else None,
        'order_date': po.order_date.isoformat() if po.order_date else None,
        'expected_date': po.expected_date.isoformat() if po.expected_date else None,
        'status': po.status,
        'notes': po.notes,
        'items': items,
        'created_at': po.created_at.isoformat() if po.created_at else None,
        'created_by_name': po.creator.full_name if po.creator else None,
        'approved_by_name': po.approver.full_name if po.approver else None,
    }}), 200


@purchasing_bp.route('/orders/<int:id>', methods=['PUT'])
@jwt_required()
@audit_log('update', 'PurchaseOrder')
@permission_required('products.edit')
def update_order(id):
    po = PurchaseOrder.query.get(id)
    if not po:
        raise NotFoundError('Purchase order not found')

    if po.status not in ('Draft',):
        raise ValidationError(f'Cannot edit order with status: {po.status}')

    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    if data.get('supplier_id'):
        if not Supplier.query.get(data['supplier_id']):
            raise ValidationError('Invalid supplier_id')
        po.supplier_id = data['supplier_id']
    if data.get('order_date'):
        po.order_date = date.fromisoformat(data['order_date'])
    if data.get('expected_date'):
        po.expected_date = date.fromisoformat(data['expected_date'])
    if data.get('notes') is not None:
        po.notes = data['notes'].strip()

    if 'items' in data:
        # Remove existing items and replace
        for old_item in po.items:
            db.session.delete(old_item)

        for item in data['items']:
            rm_id = item.get('raw_material_id')
            qty = item.get('quantity_ordered')
            cost = item.get('unit_cost')
            if not rm_id or not qty or cost is None:
                raise ValidationError('Each item needs raw_material_id, quantity_ordered, and unit_cost')
            poi = PurchaseOrderItem(
                purchase_order_id=po.id,
                raw_material_id=rm_id,
                quantity_ordered=qty,
                unit_cost=cost,
            )
            db.session.add(poi)

    po.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Purchase order updated successfully'}), 200


@purchasing_bp.route('/orders/<int:id>/submit', methods=['PUT'])
@jwt_required()
@audit_log('submit', 'PurchaseOrder')
@permission_required('products.edit')
def submit_order(id):
    po = PurchaseOrder.query.get(id)
    if not po:
        raise NotFoundError('Purchase order not found')

    if po.status != 'Draft':
        raise ValidationError(f'Order already {po.status}')

    po.status = 'Ordered'
    po.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Purchase order submitted successfully'}), 200


@purchasing_bp.route('/orders/<int:id>/receive', methods=['PUT'])
@jwt_required()
@audit_log('receive', 'PurchaseOrder')
@permission_required('products.edit')
def receive_order(id):
    po = PurchaseOrder.query.get(id)
    if not po:
        raise NotFoundError('Purchase order not found')

    if po.status not in ('Ordered', 'PartiallyReceived'):
        raise ValidationError(f'Cannot receive order with status: {po.status}')

    data = request.get_json()
    if not data or 'items' not in data:
        raise ValidationError('items array is required')

    warehouse_id = data.get('warehouse_id')
    if not warehouse_id:
        raise ValidationError('warehouse_id is required')
    if not Warehouse.query.get(warehouse_id):
        raise ValidationError('Invalid warehouse_id')

    user_id = int(get_jwt_identity())

    try:
        all_fully_received = True

        for recv_item in data['items']:
            item_id = recv_item.get('item_id')
            receive_qty = float(recv_item.get('quantity_received', 0))

            if not item_id or receive_qty <= 0:
                continue

            poi = PurchaseOrderItem.query.get(item_id)
            if not poi or poi.purchase_order_id != po.id:
                raise ValidationError(f'Invalid item_id: {item_id}')

            new_received = float(poi.quantity_received or 0) + receive_qty
            if new_received > float(poi.quantity_ordered):
                raise ValidationError(
                    f'Cannot receive more than ordered for item {poi.raw_material.name}'
                )
            poi.quantity_received = new_received

            # Update RawMaterialInventory
            inv = RawMaterialInventory.query.filter(
                RawMaterialInventory.raw_material_id == poi.raw_material_id,
                RawMaterialInventory.warehouse_id == warehouse_id
            ).first()

            if not inv:
                inv = RawMaterialInventory(
                    raw_material_id=poi.raw_material_id,
                    warehouse_id=warehouse_id,
                    quantity_on_hand=0,
                )
                db.session.add(inv)

            inv.quantity_on_hand = float(inv.quantity_on_hand or 0) + receive_qty

            # Create ledger entry
            ledger = RawMaterialLedger(
                raw_material_id=poi.raw_material_id,
                warehouse_id=warehouse_id,
                movement_type='GRV',
                quantity=receive_qty,
                unit_cost=float(poi.unit_cost),
                reference_type='PurchaseOrder',
                reference_id=po.id,
                created_by_id=user_id,
            )
            db.session.add(ledger)

            if new_received < float(poi.quantity_ordered):
                all_fully_received = False

        po.status = 'FullyReceived' if all_fully_received else 'PartiallyReceived'
        po.updated_by_id = user_id
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Goods received successfully'}), 200


@purchasing_bp.route('/orders/<int:id>/cancel', methods=['PUT'])
@jwt_required()
@audit_log('cancel', 'PurchaseOrder')
@permission_required('products.delete')
def cancel_order(id):
    po = PurchaseOrder.query.get(id)
    if not po:
        raise NotFoundError('Purchase order not found')

    if po.status in ('FullyReceived', 'Cancelled'):
        raise ValidationError(f'Cannot cancel order with status: {po.status}')

    po.status = 'Cancelled'
    po.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Purchase order cancelled successfully'}), 200


@purchasing_bp.route('/orders/<int:id>', methods=['DELETE'])
@jwt_required()
@audit_log('delete', 'PurchaseOrder')
@permission_required('products.delete')
def delete_order(id):
    po = PurchaseOrder.query.get(id)
    if not po:
        raise NotFoundError('Purchase order not found')

    if po.status not in ('Draft', 'Cancelled'):
        raise ValidationError(f'Cannot delete purchase order with status: {po.status}. Only Draft or Cancelled orders can be deleted.')

    if po.status == 'Cancelled':
        pass
    elif PurchaseOrderItem.query.filter_by(purchase_order_id=id).first():
        from models.models import RawMaterialInventory
        for item in po.items:
            if item.raw_material_id and item.received_quantity and float(item.received_quantity) > 0:
                rmi = RawMaterialInventory.query.filter_by(
                    raw_material_id=item.raw_material_id,
                    warehouse_id=po.warehouse_id,
                ).first()
                if rmi:
                    rmi.quantity = float(rmi.quantity) - float(item.received_quantity)
                    if rmi.quantity < 0:
                        rmi.quantity = 0
        db.session.flush()

    db.session.delete(po)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Purchase order deleted successfully'}), 200
