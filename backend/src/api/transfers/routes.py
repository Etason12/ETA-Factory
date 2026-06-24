from datetime import date

from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import (
    Transfer, TransferItem, GoodsIssueVoucher, GIVItem,
    GoodsReceiveVoucher, GRVItem, Warehouse, Product, db
)
from utils.helpers import paginate, generate_unique_code
from utils.error_handlers import NotFoundError, ValidationError, ConflictError
from api.decorators import role_required, permission_required, audit_log
from . import transfers_bp


@transfers_bp.route('', methods=['GET'])
@jwt_required()
@permission_required('transfers.view')
def list_transfers():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    source_warehouse_id = request.args.get('source_warehouse_id', type=int)
    destination_warehouse_id = request.args.get('destination_warehouse_id', type=int)
    status = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = Transfer.query

    if source_warehouse_id:
        query = query.filter(Transfer.source_warehouse_id == source_warehouse_id)
    if destination_warehouse_id:
        query = query.filter(Transfer.destination_warehouse_id == destination_warehouse_id)
    if status:
        query = query.filter(Transfer.status == status)
    if date_from:
        query = query.filter(Transfer.transfer_date >= date_from)
    if date_to:
        query = query.filter(Transfer.transfer_date <= date_to)

    query = query.order_by(Transfer.created_at.desc())
    result = paginate(query, page, per_page)

    transfers = []
    for t in result['items']:
        transfers.append({
            'id': t.id, 'transfer_number': t.transfer_number,
            'source_warehouse_id': t.source_warehouse_id,
            'source_warehouse_name': t.source_warehouse.name if t.source_warehouse else None,
            'destination_warehouse_id': t.destination_warehouse_id,
            'destination_warehouse_name': t.destination_warehouse.name if t.destination_warehouse else None,
            'transfer_date': t.transfer_date.isoformat() if t.transfer_date else None,
            'status': t.status,
            'notes': t.notes,
            'created_at': t.created_at.isoformat() if t.created_at else None,
        })

    return jsonify({
        'transfers': transfers,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@transfers_bp.route('', methods=['POST'])
@jwt_required()
@audit_log('create', 'Transfer')
@permission_required('transfers.create')
def create_transfer():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    transfer_number = data.get('transfer_number', '').strip()
    source_warehouse_id = data.get('source_warehouse_id')
    destination_warehouse_id = data.get('destination_warehouse_id')
    transfer_date = date.fromisoformat(data['transfer_date']) if data.get('transfer_date') else date.today()
    notes = data.get('notes', '').strip()
    items_data = data.get('items', [])

    if not transfer_number:
        transfer_number = generate_unique_code('TRF')
    if not source_warehouse_id or not destination_warehouse_id:
        raise ValidationError('source_warehouse_id and destination_warehouse_id are required')

    if source_warehouse_id == destination_warehouse_id:
        raise ValidationError('Source and destination warehouses must be different')

    if Transfer.query.filter(Transfer.transfer_number == transfer_number).first():
        raise ConflictError('Transfer number already exists')

    if not items_data:
        raise ValidationError('At least one item is required')

    source = Warehouse.query.get(source_warehouse_id)
    dest = Warehouse.query.get(destination_warehouse_id)
    if not source or not dest:
        raise ValidationError('Invalid warehouse ID')

    user_id = int(get_jwt_identity())
    transfer = Transfer(
        transfer_number=transfer_number,
        source_warehouse_id=source_warehouse_id,
        destination_warehouse_id=destination_warehouse_id,
        transfer_date=transfer_date,
        status='Pending',
        notes=notes,
        requested_by_id=user_id,
        created_by_id=user_id,
    )
    db.session.add(transfer)
    db.session.flush()

    for item in items_data:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        if not product_id or not quantity:
            raise ValidationError('Each item requires product_id and quantity')
        ti = TransferItem(
            transfer_id=transfer.id,
            product_id=product_id,
            quantity=quantity,
            unit_cost=item.get('unit_cost'),
            batch_number=item.get('batch_number', '').strip(),
        )
        db.session.add(ti)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({'message': 'Transfer created successfully', 'transfer_id': transfer.id}), 201


@transfers_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('transfers.view')
def get_transfer(id):
    transfer = Transfer.query.get(id)
    if not transfer:
        raise NotFoundError('Transfer not found')

    items = []
    for item in transfer.items:
        items.append({
            'id': item.id,
            'product_id': item.product_id,
            'product_name': item.product.name if item.product else None,
            'product_sku': item.product.sku if item.product else None,
            'quantity': float(item.quantity) if item.quantity else 0,
            'unit_cost': float(item.unit_cost) if item.unit_cost else None,
            'batch_number': item.batch_number,
        })

    return jsonify({'transfer': {
        'id': transfer.id, 'transfer_number': transfer.transfer_number,
        'source_warehouse_id': transfer.source_warehouse_id,
        'source_warehouse_name': transfer.source_warehouse.name if transfer.source_warehouse else None,
        'destination_warehouse_id': transfer.destination_warehouse_id,
        'destination_warehouse_name': transfer.destination_warehouse.name if transfer.destination_warehouse else None,
        'transfer_date': transfer.transfer_date.isoformat() if transfer.transfer_date else None,
        'status': transfer.status,
        'notes': transfer.notes,
        'giv_id': transfer.giv_id,
        'grv_id': transfer.grv_id,
        'items': items,
        'created_at': transfer.created_at.isoformat() if transfer.created_at else None,
    }}), 200


@transfers_bp.route('/<int:id>/approve', methods=['PUT'])
@jwt_required()
@audit_log('approve', 'Transfer')
@permission_required('transfers.approve')
def approve_transfer(id):
    transfer = Transfer.query.get(id)
    if not transfer:
        raise NotFoundError('Transfer not found')

    if transfer.status not in ('Draft', 'Pending'):
        raise ValidationError(f'Cannot approve transfer with status: {transfer.status}')

    transfer.status = 'Approved'
    transfer.approved_by_id = int(get_jwt_identity())
    transfer.approved_at = db.func.now()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Transfer approved successfully'}), 200


@transfers_bp.route('/<int:id>/issue', methods=['PUT'])
@jwt_required()
@audit_log('issue', 'Transfer')
@permission_required('transfers.approve')
def issue_transfer(id):
    from services.inventory_service import InventoryService

    transfer = Transfer.query.get(id)
    if not transfer:
        raise NotFoundError('Transfer not found')

    if transfer.status != 'Approved':
        raise ValidationError(f'Cannot issue goods for transfer with status: {transfer.status}')

    if transfer.giv_id:
        raise ValidationError('Goods already issued for this transfer')

    user_id = int(get_jwt_identity())
    giv = GoodsIssueVoucher(
        voucher_number=f'GIV-TRF-{transfer.id}-{transfer.transfer_date}',
        warehouse_id=transfer.source_warehouse_id,
        reference_type='Transfer',
        reference_id=transfer.id,
        notes=f'Auto-generated GIV for transfer {transfer.transfer_number}',
        created_by_id=user_id,
        issued_by_id=user_id,
    )
    db.session.add(giv)
    db.session.flush()

    for item in transfer.items:
        giv_item = GIVItem(
            giv_id=giv.id,
            product_id=item.product_id,
            quantity=item.quantity,
            batch_number=item.batch_number,
        )
        db.session.add(giv_item)

    try:
        InventoryService().process_goods_issue(giv.id, user_id, commit=False)
        transfer.giv_id = giv.id
        transfer.status = 'In Transit'
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Goods issued successfully', 'giv_id': giv.id}), 200


@transfers_bp.route('/<int:id>/receive', methods=['PUT'])
@jwt_required()
@audit_log('receive', 'Transfer')
@permission_required('transfers.approve')
def receive_transfer(id):
    from services.inventory_service import InventoryService

    transfer = Transfer.query.get(id)
    if not transfer:
        raise NotFoundError('Transfer not found')

    if transfer.status not in ('In Transit', 'Approved'):
        raise ValidationError(f'Cannot receive goods for transfer with status: {transfer.status}')

    if transfer.grv_id:
        raise ValidationError('Goods already received for this transfer')

    user_id = int(get_jwt_identity())
    grv = GoodsReceiveVoucher(
        voucher_number=f'GRV-TRF-{transfer.id}-{transfer.transfer_date}',
        warehouse_id=transfer.destination_warehouse_id,
        reference_type='Transfer',
        reference_id=transfer.id,
        notes=f'Auto-generated GRV for transfer {transfer.transfer_number}',
        created_by_id=user_id,
        received_by_id=user_id,
    )
    db.session.add(grv)
    db.session.flush()

    for item in transfer.items:
        grv_item = GRVItem(
            grv_id=grv.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_cost=item.unit_cost,
            batch_number=item.batch_number,
        )
        db.session.add(grv_item)

    try:
        InventoryService().process_goods_receipt(grv.id, user_id, commit=False)
        transfer.grv_id = grv.id
        transfer.status = 'Received'
        transfer.received_by_id = user_id
        transfer.received_at = db.func.now()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Goods received successfully', 'grv_id': grv.id}), 200


@transfers_bp.route('/<int:id>/cancel', methods=['PUT'])
@jwt_required()
@audit_log('cancel', 'Transfer')
@permission_required('transfers.approve')
def cancel_transfer(id):
    from services.inventory_service import InventoryService

    transfer = Transfer.query.get(id)
    if not transfer:
        raise NotFoundError('Transfer not found')

    if transfer.status in ('Received', 'Cancelled'):
        raise ValidationError(f'Cannot cancel transfer with status: {transfer.status}')

    user_id = int(get_jwt_identity())

    # Reverse stock if goods were issued
    if transfer.status == 'In Transit' and transfer.giv_id:
        inv_svc = InventoryService()
        giv = GoodsIssueVoucher.query.get(transfer.giv_id)
        if giv and giv.status == 'Issued':
            for item in giv.items:
                inv_svc.add_stock(
                    product_id=item.product_id,
                    warehouse_id=transfer.source_warehouse_id,
                    quantity=float(item.quantity),
                    reference_type='TransferReversal',
                    reference_id=transfer.id,
                    created_by_id=user_id,
                )
            giv.status = 'Cancelled'
            db.session.flush()

    transfer.status = 'Cancelled'
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Transfer cancelled successfully'}), 200


@transfers_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@audit_log('delete', 'Transfer')
@permission_required('transfers.delete')
def delete_transfer(id):
    transfer = Transfer.query.get(id)
    if not transfer:
        raise NotFoundError('Transfer not found')
    db.session.delete(transfer)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({'message': 'Transfer deleted successfully'}), 200
