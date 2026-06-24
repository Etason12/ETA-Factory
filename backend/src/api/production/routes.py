from datetime import date

from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import (
    ProductionBatch, Product, Warehouse, BOMItem, db
)
from utils.helpers import paginate, generate_unique_code
from utils.error_handlers import NotFoundError, ValidationError, ConflictError
from api.decorators import role_required, permission_required, audit_log
from . import production_bp


@production_bp.route('/batches', methods=['GET'])
@jwt_required()
@permission_required('production.view')
def list_batches():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    product_id = request.args.get('product_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    status = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = ProductionBatch.query

    if product_id:
        query = query.filter(ProductionBatch.product_id == product_id)
    if warehouse_id:
        query = query.filter(ProductionBatch.warehouse_id == warehouse_id)
    if status:
        query = query.filter(ProductionBatch.status == status)
    if date_from:
        query = query.filter(ProductionBatch.production_date >= date_from)
    if date_to:
        query = query.filter(ProductionBatch.production_date <= date_to)

    query = query.order_by(ProductionBatch.created_at.desc())
    result = paginate(query, page, per_page)

    batches = []
    for b in result['items']:
        batches.append({
            'id': b.id, 'batch_number': b.batch_number,
            'product_id': b.product_id,
            'product_name': b.product.name if b.product else None,
            'product_sku': b.product.sku if b.product else None,
            'quantity_produced': float(b.quantity_produced) if b.quantity_produced else 0,
            'production_cost': float(b.production_cost) if b.production_cost else 0,
            'production_date': b.production_date.isoformat() if b.production_date else None,
            'warehouse_id': b.warehouse_id,
            'warehouse_name': b.warehouse.name if b.warehouse else None,
            'status': b.status,
            'notes': b.notes,
            'created_at': b.created_at.isoformat() if b.created_at else None,
            'created_by_name': b.creator.full_name if b.creator else None,
            'approved_by_name': b.approver.full_name if b.approver else None,
            'approved_at': b.approved_at.isoformat() if b.approved_at else None,
        })

    return jsonify({
        'batches': batches,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@production_bp.route('/batches', methods=['POST'])
@jwt_required()
@audit_log('create', 'Production')
@permission_required('production.create')
def create_batch():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    batch_number = data.get('batch_number', '').strip()
    product_id = data.get('product_id')
    quantity_produced = data.get('quantity_produced')
    production_cost = data.get('production_cost', 0)
    production_date = date.fromisoformat(data['production_date']) if data.get('production_date') else date.today()
    warehouse_id = data.get('warehouse_id')
    notes = data.get('notes', '').strip()

    if not batch_number:
        batch_number = generate_unique_code('PRD')
    if not product_id or not quantity_produced or not production_date or not warehouse_id:
        raise ValidationError('product_id, quantity_produced, production_date, and warehouse_id are required')
    if float(quantity_produced) <= 0:
        raise ValidationError('quantity_produced must be positive')
    if float(production_cost) < 0:
        raise ValidationError('production_cost cannot be negative')

    if ProductionBatch.query.filter(ProductionBatch.batch_number == batch_number).first():
        raise ConflictError('Batch number already exists')

    product = Product.query.get(product_id)
    if not product:
        raise ValidationError('Product not found')
    bom_count = BOMItem.query.filter_by(product_id=product_id).count()
    if bom_count == 0:
        raise ValidationError(f'Product {product.name} has no Bill of Materials (BOM). Please create a BOM first.')

    batch = ProductionBatch(
        batch_number=batch_number,
        product_id=product_id,
        quantity_produced=quantity_produced,
        production_cost=production_cost,
        production_date=production_date,
        warehouse_id=warehouse_id,
        notes=notes,
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(batch)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Production batch created successfully', 'batch_id': batch.id}), 201


@production_bp.route('/batches/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('production.view')
def get_batch(id):
    batch = ProductionBatch.query.get(id)
    if not batch:
        raise NotFoundError('Production batch not found')

    return jsonify({'batch': {
        'id': batch.id, 'batch_number': batch.batch_number,
        'product_id': batch.product_id,
        'product_name': batch.product.name if batch.product else None,
        'product_sku': batch.product.sku if batch.product else None,
        'quantity_produced': float(batch.quantity_produced) if batch.quantity_produced else 0,
        'production_cost': float(batch.production_cost) if batch.production_cost else 0,
        'production_date': batch.production_date.isoformat() if batch.production_date else None,
        'warehouse_id': batch.warehouse_id,
        'warehouse_name': batch.warehouse.name if batch.warehouse else None,
        'status': batch.status,
        'notes': batch.notes,
        'created_at': batch.created_at.isoformat() if batch.created_at else None,
        'created_by_name': batch.creator.full_name if batch.creator else None,
        'approved_by_name': batch.approver.full_name if batch.approver else None,
        'approved_at': batch.approved_at.isoformat() if batch.approved_at else None,
    }}), 200


@production_bp.route('/batches/<int:id>/approve', methods=['PUT'])
@jwt_required()
@audit_log('approve', 'Production')
@permission_required('production.approve')
def approve_batch(id):
    from services.production_service import ProductionService

    service = ProductionService()
    service.approve_batch(batch_id=id, approved_by_id=int(get_jwt_identity()))

    return jsonify({'message': 'Batch approved successfully. Inventory updated and GRV created.'}), 200


@production_bp.route('/check-requirements', methods=['GET'])
@jwt_required()
@permission_required('production.view')
def check_requirements():
    from services.production_service import ProductionService
    
    product_id = request.args.get('product_id', type=int)
    quantity = request.args.get('quantity', type=float)
    warehouse_id = request.args.get('warehouse_id', type=int)
    
    if not product_id or quantity is None or not warehouse_id:
        raise ValidationError('product_id, quantity, and warehouse_id are required')
        
    service = ProductionService()
    requirements = service.get_required_materials(product_id, quantity, warehouse_id)
    
    return jsonify({'requirements': requirements}), 200


@production_bp.route('/batches/<int:id>/cancel', methods=['PUT'])
@jwt_required()
@audit_log('cancel', 'Production')
@permission_required('production.approve')
def cancel_batch(id):
    batch = ProductionBatch.query.get(id)
    if not batch:
        raise NotFoundError('Production batch not found')

    if batch.status in ('Approved', 'Cancelled'):
        raise ValidationError(f'Cannot cancel batch with status: {batch.status}')

    batch.status = 'Cancelled'
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Batch cancelled successfully'}), 200


@production_bp.route('/batches/<int:id>', methods=['DELETE'])
@jwt_required()
@audit_log('delete', 'Production')
@permission_required('production.approve')
def delete_batch(id):
    batch = ProductionBatch.query.get(id)
    if not batch:
        raise NotFoundError('Production batch not found')

    if batch.status not in ('Draft', 'Cancelled'):
        raise ValidationError(f'Cannot delete batch with status: {batch.status}. Only Draft or Cancelled batches can be deleted.')

    db.session.delete(batch)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return jsonify({'message': 'Production batch deleted successfully'}), 200
