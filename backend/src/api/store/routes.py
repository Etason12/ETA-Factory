from datetime import date, datetime

from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import (
    StoreRequisition, StoreRequisitionItem,
    RawMaterial, RawMaterialInventory, RawMaterialLedger,
    Warehouse, ProductionBatch, db
)
from utils.helpers import paginate, generate_unique_code, escape_like
from utils.error_handlers import NotFoundError, ValidationError
from api.decorators import permission_required, audit_log
from . import store_bp


# ----- Store Requisitions (Request raw materials from store) -----

@store_bp.route('/requisitions', methods=['GET'])
@jwt_required()
@permission_required('production.view')
def list_requisitions():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status', '').strip()
    warehouse_id = request.args.get('warehouse_id', type=int)

    query = StoreRequisition.query

    if status:
        query = query.filter(StoreRequisition.status == status)
    if warehouse_id:
        query = query.filter(StoreRequisition.warehouse_id == warehouse_id)

    query = query.order_by(StoreRequisition.created_at.desc())
    result = paginate(query, page, per_page)

    items = []
    for r in result['items']:
        items.append({
            'id': r.id, 'requisition_number': r.requisition_number,
            'warehouse_id': r.warehouse_id,
            'warehouse_name': r.warehouse.name if r.warehouse else None,
            'production_batch_id': r.production_batch_id,
            'production_batch_number': r.production_batch.batch_number if r.production_batch else None,
            'requisition_date': r.requisition_date.isoformat() if r.requisition_date else None,
            'status': r.status,
            'notes': r.notes,
            'created_at': r.created_at.isoformat() if r.created_at else None,
            'created_by_name': r.creator.full_name if r.creator else None,
            'approved_by_name': r.approver.full_name if r.approver else None,
            'issued_by_name': r.issuer.full_name if r.issuer else None,
        })

    return jsonify({
        'requisitions': items,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@store_bp.route('/requisitions', methods=['POST'])
@jwt_required()
@audit_log('create', 'StoreRequisition')
@permission_required('production.create')
def create_requisition():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    warehouse_id = data.get('warehouse_id')
    if not warehouse_id:
        raise ValidationError('warehouse_id is required')

    if not Warehouse.query.get(warehouse_id):
        raise ValidationError('Invalid warehouse_id')

    production_batch_id = data.get('production_batch_id')
    if production_batch_id and not ProductionBatch.query.get(production_batch_id):
        raise ValidationError('Invalid production_batch_id')

    requisition_number = generate_unique_code('SR')
    requisition_date = date.fromisoformat(data['requisition_date']) if data.get('requisition_date') else date.today()

    req = StoreRequisition(
        requisition_number=requisition_number,
        warehouse_id=warehouse_id,
        production_batch_id=production_batch_id,
        requisition_date=requisition_date,
        notes=data.get('notes', '').strip(),
        status='Pending',
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(req)
    db.session.flush()

    items_data = data.get('items', [])
    if not items_data:
        db.session.rollback()
        raise ValidationError('At least one item is required')

    for item in items_data:
        rm_id = item.get('raw_material_id')
        qty = item.get('quantity_requested')

        if not rm_id or not qty:
            db.session.rollback()
            raise ValidationError('Each item needs raw_material_id and quantity_requested')

        if not RawMaterial.query.get(rm_id):
            db.session.rollback()
            raise ValidationError(f'Invalid raw_material_id: {rm_id}')

        sri = StoreRequisitionItem(
            store_requisition_id=req.id,
            raw_material_id=rm_id,
            quantity_requested=qty,
        )
        db.session.add(sri)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({
        'requisition': {'id': req.id, 'requisition_number': req.requisition_number},
        'message': 'Store requisition created successfully'
    }), 201


@store_bp.route('/requisitions/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('production.view')
def get_requisition(id):
    req = StoreRequisition.query.get(id)
    if not req:
        raise NotFoundError('Store requisition not found')

    items = []
    for item in req.items:
        items.append({
            'id': item.id,
            'raw_material_id': item.raw_material_id,
            'raw_material_name': item.raw_material.name if item.raw_material else None,
            'raw_material_sku': item.raw_material.sku if item.raw_material else None,
            'quantity_requested': float(item.quantity_requested),
            'quantity_issued': float(item.quantity_issued),
        })

    return jsonify({'requisition': {
        'id': req.id, 'requisition_number': req.requisition_number,
        'warehouse_id': req.warehouse_id,
        'warehouse_name': req.warehouse.name if req.warehouse else None,
        'production_batch_id': req.production_batch_id,
        'production_batch_number': req.production_batch.batch_number if req.production_batch else None,
        'requisition_date': req.requisition_date.isoformat() if req.requisition_date else None,
        'status': req.status,
        'notes': req.notes,
        'items': items,
        'created_at': req.created_at.isoformat() if req.created_at else None,
        'created_by_name': req.creator.full_name if req.creator else None,
        'approved_by_name': req.approver.full_name if req.approver else None,
        'issued_by_name': req.issuer.full_name if req.issuer else None,
    }}), 200


@store_bp.route('/requisitions/<int:id>/approve', methods=['PUT'])
@jwt_required()
@audit_log('approve', 'StoreRequisition')
@permission_required('production.approve')
def approve_requisition(id):
    req = StoreRequisition.query.get(id)
    if not req:
        raise NotFoundError('Store requisition not found')

    if req.status != 'Pending':
        raise ValidationError(f'Requisition already {req.status}')

    req.status = 'Approved'
    req.approved_by_id = int(get_jwt_identity())
    req.approved_at = datetime.utcnow()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Requisition approved successfully'}), 200


@store_bp.route('/requisitions/<int:id>/issue', methods=['PUT'])
@jwt_required()
@audit_log('issue', 'StoreRequisition')
@permission_required('production.approve')
def issue_requisition(id):
    req = StoreRequisition.query.get(id)
    if not req:
        raise NotFoundError('Store requisition not found')

    if req.status != 'Approved':
        raise ValidationError(f'Requisition must be approved before issuing (current: {req.status})')

    data = request.get_json(silent=True)
    user_id = int(get_jwt_identity())

    try:
        for item in req.items:
            issue_qty = float(item.quantity_requested)
            # Support partial issue via request body
            if data and 'items' in data:
                for di in data['items']:
                    if di.get('item_id') == item.id:
                        issue_qty = float(di.get('quantity_issued', issue_qty))
                        break

            if issue_qty <= 0:
                continue

            # Check and deduct from RawMaterialInventory
            inv = RawMaterialInventory.query.filter(
                RawMaterialInventory.raw_material_id == item.raw_material_id,
                RawMaterialInventory.warehouse_id == req.warehouse_id
            ).first()

            available = float(inv.quantity_on_hand or 0) - float(inv.reserved_quantity or 0) if inv else 0
            if available < issue_qty:
                rm_name = item.raw_material.name if item.raw_material else 'Unknown'
                raise ValidationError(
                    f'Insufficient stock of {rm_name}: need {issue_qty}, available {available}'
                )

            inv.quantity_on_hand = float(inv.quantity_on_hand or 0) - issue_qty
            item.quantity_issued = float(item.quantity_issued or 0) + issue_qty

            # Create ledger entry
            ledger = RawMaterialLedger(
                raw_material_id=item.raw_material_id,
                warehouse_id=req.warehouse_id,
                movement_type='GIV',
                quantity=-issue_qty,
                unit_cost=item.raw_material.cost_price if item.raw_material else None,
                reference_type='StoreRequisition',
                reference_id=req.id,
                created_by_id=user_id,
            )
            db.session.add(ledger)

        req.status = 'Issued'
        req.issued_by_id = user_id
        req.issued_at = datetime.utcnow()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Materials issued successfully'}), 200


@store_bp.route('/requisitions/<int:id>/cancel', methods=['PUT'])
@jwt_required()
@audit_log('cancel', 'StoreRequisition')
@permission_required('production.approve')
def cancel_requisition(id):
    req = StoreRequisition.query.get(id)
    if not req:
        raise NotFoundError('Store requisition not found')

    if req.status in ('Issued',):
        raise ValidationError('Cannot cancel an issued requisition')

    req.status = 'Cancelled'
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Requisition cancelled successfully'}), 200


@store_bp.route('/requisitions/from-batch/<int:batch_id>', methods=['POST'])
@jwt_required()
@audit_log('create', 'StoreRequisition')
@permission_required('production.create')
def create_requisition_from_batch(batch_id):
    from models.models import BOMItem

    batch = ProductionBatch.query.get(batch_id)
    if not batch:
        raise NotFoundError('Production batch not found')

    bom_items = BOMItem.query.filter_by(product_id=batch.product_id).all()
    if not bom_items:
        raise ValidationError('Product has no BOM defined')

    requisition_number = generate_unique_code('SR')
    req = StoreRequisition(
        requisition_number=requisition_number,
        warehouse_id=batch.warehouse_id,
        production_batch_id=batch.id,
        notes=f'Auto-generated from production batch {batch.batch_number}',
        status='Pending',
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(req)
    db.session.flush()

    for item in bom_items:
        needed = float(item.quantity) * float(batch.quantity_produced)
        sri = StoreRequisitionItem(
            store_requisition_id=req.id,
            raw_material_id=item.raw_material_id,
            quantity_requested=needed,
        )
        db.session.add(sri)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({
        'requisition': {'id': req.id, 'requisition_number': req.requisition_number},
        'message': f'Store requisition {requisition_number} created for batch {batch.batch_number}'
    }), 201


# ----- Raw Material Inventory -----

@store_bp.route('/inventory', methods=['GET'])
@jwt_required()
@permission_required('products.view')
def list_rm_inventory():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    search = request.args.get('search', '').strip()

    query = RawMaterialInventory.query

    if warehouse_id:
        query = query.filter(RawMaterialInventory.warehouse_id == warehouse_id)

    if search:
        safe = escape_like(search)
        query = query.join(RawMaterial).filter(
            db.or_(
                RawMaterial.name.ilike(f'%{safe}%'),
                RawMaterial.sku.ilike(f'%{safe}%'),
            )
        )

    query = query.order_by(RawMaterialInventory.updated_at.desc())
    result = paginate(query, page, per_page)

    items = []
    for inv in result['items']:
        rm = inv.raw_material
        items.append({
            'id': inv.id,
            'raw_material_id': inv.raw_material_id,
            'raw_material_name': rm.name if rm else None,
            'raw_material_sku': rm.sku if rm else None,
            'warehouse_id': inv.warehouse_id,
            'warehouse_name': inv.warehouse.name if inv.warehouse else None,
            'quantity_on_hand': float(inv.quantity_on_hand or 0),
            'reserved_quantity': float(inv.reserved_quantity or 0),
            'available_quantity': inv.available_quantity,
            'unit_name': rm.unit.name if rm and rm.unit else None,
        })

    return jsonify({
        'inventory': items,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@store_bp.route('/inventory/<int:rm_id>/<int:warehouse_id>', methods=['GET'])
@jwt_required()
@permission_required('products.view')
def get_rm_inventory(rm_id, warehouse_id):
    inv = RawMaterialInventory.query.filter(
        RawMaterialInventory.raw_material_id == rm_id,
        RawMaterialInventory.warehouse_id == warehouse_id
    ).first()

    if not inv:
        return jsonify({
            'raw_material_id': rm_id,
            'warehouse_id': warehouse_id,
            'quantity_on_hand': 0,
            'reserved_quantity': 0,
            'available_quantity': 0,
        }), 200

    rm = inv.raw_material
    return jsonify({
        'id': inv.id,
        'raw_material_id': inv.raw_material_id,
        'raw_material_name': rm.name if rm else None,
        'raw_material_sku': rm.sku if rm else None,
        'warehouse_id': inv.warehouse_id,
        'warehouse_name': inv.warehouse.name if inv.warehouse else None,
        'quantity_on_hand': float(inv.quantity_on_hand or 0),
        'reserved_quantity': float(inv.reserved_quantity or 0),
        'available_quantity': inv.available_quantity,
        'unit_name': rm.unit.name if rm and rm.unit else None,
    }), 200


# ----- Raw Material Ledger -----

@store_bp.route('/ledger', methods=['GET'])
@jwt_required()
@permission_required('products.view')
def list_rm_ledger():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    raw_material_id = request.args.get('raw_material_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)

    query = RawMaterialLedger.query.order_by(RawMaterialLedger.transaction_date.desc())

    if raw_material_id:
        query = query.filter(RawMaterialLedger.raw_material_id == raw_material_id)
    if warehouse_id:
        query = query.filter(RawMaterialLedger.warehouse_id == warehouse_id)

    result = paginate(query, page, per_page)

    entries = []
    for e in result['items']:
        entries.append({
            'id': e.id,
            'raw_material_id': e.raw_material_id,
            'raw_material_name': e.raw_material.name if e.raw_material else None,
            'warehouse_id': e.warehouse_id,
            'warehouse_name': e.warehouse.name if e.warehouse else None,
            'movement_type': e.movement_type,
            'quantity': float(e.quantity),
            'unit_cost': float(e.unit_cost) if e.unit_cost else None,
            'reference_type': e.reference_type,
            'reference_id': e.reference_id,
            'transaction_date': e.transaction_date.isoformat() if e.transaction_date else None,
        })

    return jsonify({
        'entries': entries,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@store_bp.route('/requisitions/<int:id>', methods=['DELETE'])
@jwt_required()
@audit_log('delete', 'StoreRequisition')
@permission_required('products.delete')
def delete_requisition(id):
    req = StoreRequisition.query.get(id)
    if not req:
        raise NotFoundError('Store requisition not found')
    db.session.delete(req)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({'message': 'Store requisition deleted successfully'}), 200
