from datetime import datetime, date
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
import random
import os
from models.models import (
    SalesQuotation, SalesQuotationItem, SalesOrder, SalesOrderItem,
    Invoice, Payment, LoadingAuthorization, Customer, db
)
from utils.helpers import paginate, generate_unique_code
from utils.error_handlers import NotFoundError, ValidationError, ConflictError
from api.decorators import role_required, permission_required, branch_required, audit_log
from . import sales_bp


# ─── Quotations ───────────────────────────────────────────

@sales_bp.route('/quotations', methods=['GET'])
@jwt_required()
@permission_required('sales.view')
@branch_required()
def list_quotations():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    customer_id = request.args.get('customer_id', type=int)
    branch_id = request.args.get('branch_id', type=int)
    status = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = SalesQuotation.query

    if customer_id:
        query = query.filter(SalesQuotation.customer_id == customer_id)
    if branch_id:
        query = query.filter(SalesQuotation.branch_id == branch_id)
    if status:
        query = query.filter(SalesQuotation.status == status)
    if date_from:
        query = query.filter(SalesQuotation.created_at >= date_from)
    if date_to:
        query = query.filter(SalesQuotation.created_at <= date_to + ' 23:59:59')

    query = query.order_by(SalesQuotation.created_at.desc())
    result = paginate(query, page, per_page)

    quotations = []
    for q in result['items']:
        quotations.append({
            'id': q.id, 'quotation_number': q.quotation_number,
            'customer_id': q.customer_id,
            'customer_name': q.customer.name if q.customer else None,
            'branch_id': q.branch_id,
            'status': q.status,
            'valid_until': q.valid_until.isoformat() if q.valid_until else None,
            'subtotal': float(q.subtotal) if q.subtotal else 0,
            'tax_amount': float(q.tax_amount) if q.tax_amount else 0,
            'total_amount': float(q.total_amount) if q.total_amount else 0,
            'notes': q.notes,
            'created_at': q.created_at.isoformat() if q.created_at else None,
        })

    return jsonify({
        'quotations': quotations,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@sales_bp.route('/quotations', methods=['POST'])
@jwt_required()
@audit_log('create', 'Sales')
@permission_required('sales.create')
@branch_required()
def create_quotation():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    quotation_number = data.get('quotation_number', '').strip()
    customer_id = data.get('customer_id')
    branch_id = data.get('branch_id')
    valid_until_str = data.get('valid_until')
    valid_until = None
    if valid_until_str:
        try:
            valid_until = date.fromisoformat(valid_until_str)
        except (ValueError, TypeError):
            raise ValidationError('Invalid valid_until format, expected YYYY-MM-DD')
    notes = data.get('notes', '').strip()
    items_data = data.get('items', [])

    if not quotation_number:
        quotation_number = generate_unique_code('QTN')
    if not customer_id or not branch_id:
        raise ValidationError('customer_id and branch_id are required')

    if SalesQuotation.query.filter(SalesQuotation.quotation_number == quotation_number).first():
        raise ConflictError('Quotation number already exists')

    if not items_data:
        raise ValidationError('At least one item is required')

    quotation = SalesQuotation(
        quotation_number=quotation_number,
        customer_id=customer_id,
        branch_id=branch_id,
        valid_until=valid_until,
        notes=notes,
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(quotation)
    db.session.flush()

    subtotal = 0
    for item in items_data:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        unit_price = item.get('unit_price', 0)
        if not product_id or not quantity:
            raise ValidationError('Each item requires product_id and quantity')
        total_price = float(quantity) * float(unit_price)
        subtotal += total_price
        qi = SalesQuotationItem(
            quotation_id=quotation.id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
        )
        db.session.add(qi)

    quotation.subtotal = subtotal
    quotation.tax_amount = data.get('tax_amount', 0)
    quotation.total_amount = float(quotation.subtotal) + float(quotation.tax_amount)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Quotation created successfully', 'quotation_id': quotation.id}), 201


@sales_bp.route('/quotations/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('sales.view')
def get_quotation(id):
    quotation = SalesQuotation.query.get(id)
    if not quotation:
        raise NotFoundError('Quotation not found')

    items = []
    for item in quotation.items:
        items.append({
            'id': item.id, 'product_id': item.product_id,
            'product_name': item.product.name if item.product else None,
            'product_sku': item.product.sku if item.product else None,
            'quantity': float(item.quantity) if item.quantity else 0,
            'unit_price': float(item.unit_price) if item.unit_price else 0,
            'total_price': float(item.total_price) if item.total_price else 0,
        })

    return jsonify({'quotation': {
        'id': quotation.id, 'quotation_number': quotation.quotation_number,
        'customer_id': quotation.customer_id,
        'customer_name': quotation.customer.name if quotation.customer else None,
        'branch_id': quotation.branch_id,
        'status': quotation.status,
        'valid_until': quotation.valid_until.isoformat() if quotation.valid_until else None,
        'subtotal': float(quotation.subtotal) if quotation.subtotal else 0,
        'tax_amount': float(quotation.tax_amount) if quotation.tax_amount else 0,
        'total_amount': float(quotation.total_amount) if quotation.total_amount else 0,
        'notes': quotation.notes,
        'items': items,
        'created_at': quotation.created_at.isoformat() if quotation.created_at else None,
    }}), 200


@sales_bp.route('/quotations/<int:id>', methods=['PUT'])
@jwt_required()
@audit_log('update', 'Sales')
@permission_required('sales.create')
def update_quotation(id):
    quotation = SalesQuotation.query.get(id)
    if not quotation:
        raise NotFoundError('Quotation not found')

    if quotation.status not in ('Draft',):
        raise ValidationError(f'Cannot update quotation with status: {quotation.status}')

    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    if data.get('valid_until'):
        try:
            quotation.valid_until = date.fromisoformat(data['valid_until'])
        except (ValueError, TypeError):
            raise ValidationError('Invalid valid_until format, expected YYYY-MM-DD')
    if data.get('notes') is not None:
        quotation.notes = data['notes'].strip()

    items_data = data.get('items')
    if items_data is not None:
        subtotal = 0
        new_items = []
        for item in items_data:
            product_id = item.get('product_id')
            quantity = item.get('quantity')
            unit_price = item.get('unit_price', 0)
            if not product_id or not quantity:
                raise ValidationError('Each item requires product_id and quantity')
            total_price = float(quantity) * float(unit_price)
            subtotal += total_price
            new_items.append(SalesQuotationItem(
                quotation_id=id, product_id=product_id,
                quantity=quantity, unit_price=unit_price, total_price=total_price,
            ))
        SalesQuotationItem.query.filter_by(quotation_id=id).delete()
        for qi in new_items:
            db.session.add(qi)
        quotation.subtotal = subtotal
        if data.get('tax_amount') is not None:
            quotation.tax_amount = data['tax_amount']
        quotation.total_amount = float(quotation.subtotal) + float(quotation.tax_amount)

    quotation.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Quotation updated successfully'}), 200


@sales_bp.route('/quotations/<int:id>', methods=['DELETE'])
@jwt_required()
@audit_log('delete', 'Sales')
@permission_required('sales.delete')
def delete_quotation(id):
    quotation = SalesQuotation.query.get(id)
    if not quotation:
        raise NotFoundError('Quotation not found')

    db.session.delete(quotation)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Quotation deleted successfully'}), 200


@sales_bp.route('/quotations/<int:id>/convert', methods=['POST'])
@jwt_required()
@audit_log('convert', 'Sales')
@permission_required('sales.create')
def convert_quotation_to_order(id):
    quotation = SalesQuotation.query.get(id)
    if not quotation:
        raise NotFoundError('Quotation not found')

    if quotation.status != 'Draft':
        raise ValidationError(f'Cannot convert quotation with status: {quotation.status}')

    data = request.get_json() or {}

    order = SalesOrder(
        order_number=data.get('order_number', f'ORD-{quotation.id}-{datetime.now().strftime("%Y%m%d%H%M%S")}'),
        customer_id=quotation.customer_id,
        branch_id=quotation.branch_id,
        warehouse_id=data.get('warehouse_id'),
        quotation_id=quotation.id,
        subtotal=quotation.subtotal,
        tax_amount=quotation.tax_amount,
        total_amount=quotation.total_amount,
        notes=quotation.notes,
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(order)
    db.session.flush()

    for qi in quotation.items:
        oi = SalesOrderItem(
            sales_order_id=order.id,
            product_id=qi.product_id,
            quantity=qi.quantity,
            unit_price=qi.unit_price,
            total_price=qi.total_price,
        )
        db.session.add(oi)

    quotation.status = 'Converted'
    quotation.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Quotation converted to order successfully', 'order_id': order.id}), 200


# ─── Orders ───────────────────────────────────────────────

@sales_bp.route('/orders', methods=['GET'])
@jwt_required()
@permission_required('sales.view')
@branch_required()
def list_orders():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    customer_id = request.args.get('customer_id', type=int)
    branch_id = request.args.get('branch_id', type=int)
    status = request.args.get('status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = SalesOrder.query

    if customer_id:
        query = query.filter(SalesOrder.customer_id == customer_id)
    if branch_id:
        query = query.filter(SalesOrder.branch_id == branch_id)
    if status:
        query = query.filter(SalesOrder.status == status)
    if date_from:
        query = query.filter(SalesOrder.order_date >= date_from)
    if date_to:
        query = query.filter(SalesOrder.order_date <= date_to)

    query = query.order_by(SalesOrder.created_at.desc())
    result = paginate(query, page, per_page)

    orders = []
    for o in result['items']:
        orders.append({
            'id': o.id, 'order_number': o.order_number,
            'customer_id': o.customer_id,
            'customer_name': o.customer.name if o.customer else None,
            'branch_id': o.branch_id,
            'warehouse_id': o.warehouse_id,
            'warehouse_name': o.warehouse.name if o.warehouse else None,
            'order_date': o.order_date.isoformat() if o.order_date else None,
            'status': o.status,
            'subtotal': float(o.subtotal) if o.subtotal else 0,
            'tax_amount': float(o.tax_amount) if o.tax_amount else 0,
            'total_amount': float(o.total_amount) if o.total_amount else 0,
            'notes': o.notes,
            'created_at': o.created_at.isoformat() if o.created_at else None,
        })

    return jsonify({
        'orders': orders,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@sales_bp.route('/orders', methods=['POST'])
@jwt_required()
@audit_log('create', 'Sales')
@permission_required('sales.create')
@branch_required()
def create_order():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    order_number = data.get('order_number', '').strip()
    customer_id = data.get('customer_id')
    branch_id = data.get('branch_id')
    warehouse_id = data.get('warehouse_id')
    order_date_str = data.get('order_date')
    order_date = None
    if order_date_str:
        try:
            order_date = date.fromisoformat(order_date_str)
        except (ValueError, TypeError):
            raise ValidationError('Invalid order_date format, expected YYYY-MM-DD')
    notes = data.get('notes', '').strip()
    items_data = data.get('items', [])

    if not order_number:
        order_number = generate_unique_code('ORD')
    if not customer_id or not branch_id or not warehouse_id or not order_date:
        raise ValidationError('customer_id, branch_id, warehouse_id, and order_date are required')

    if SalesOrder.query.filter(SalesOrder.order_number == order_number).first():
        raise ConflictError('Order number already exists')

    if not items_data:
        raise ValidationError('At least one item is required')

    order = SalesOrder(
        order_number=order_number,
        customer_id=customer_id,
        branch_id=branch_id,
        warehouse_id=warehouse_id,
        order_date=order_date,
        notes=notes,
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(order)
    db.session.flush()

    subtotal = 0
    for item in items_data:
        product_id = item.get('product_id')
        quantity = item.get('quantity')
        unit_price = item.get('unit_price', 0)
        if not product_id or not quantity:
            raise ValidationError('Each item requires product_id and quantity')
        total_price = float(quantity) * float(unit_price)
        subtotal += total_price
        oi = SalesOrderItem(
            sales_order_id=order.id,
            product_id=product_id,
            quantity=quantity,
            unit_price=unit_price,
            total_price=total_price,
        )
        db.session.add(oi)

    order.subtotal = subtotal
    order.tax_amount = data.get('tax_amount', 0)
    order.total_amount = float(order.subtotal) + float(order.tax_amount)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Order created successfully', 'order_id': order.id}), 201


@sales_bp.route('/orders/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('sales.view')
def get_order(id):
    order = SalesOrder.query.get(id)
    if not order:
        raise NotFoundError('Order not found')

    items = []
    for item in order.items:
        items.append({
            'id': item.id, 'product_id': item.product_id,
            'product_name': item.product.name if item.product else None,
            'product_sku': item.product.sku if item.product else None,
            'quantity': float(item.quantity) if item.quantity else 0,
            'unit_price': float(item.unit_price) if item.unit_price else 0,
            'total_price': float(item.total_price) if item.total_price else 0,
            'delivered_quantity': float(item.delivered_quantity) if item.delivered_quantity else 0,
        })

    return jsonify({'order': {
        'id': order.id, 'order_number': order.order_number,
        'customer_id': order.customer_id,
        'customer_name': order.customer.name if order.customer else None,
        'branch_id': order.branch_id,
        'warehouse_id': order.warehouse_id,
        'warehouse_name': order.warehouse.name if order.warehouse else None,
        'quotation_id': order.quotation_id,
        'order_date': order.order_date.isoformat() if order.order_date else None,
        'status': order.status,
        'subtotal': float(order.subtotal) if order.subtotal else 0,
        'tax_amount': float(order.tax_amount) if order.tax_amount else 0,
        'total_amount': float(order.total_amount) if order.total_amount else 0,
        'notes': order.notes,
        'items': items,
        'created_at': order.created_at.isoformat() if order.created_at else None,
    }}), 200


@sales_bp.route('/orders/<int:id>/approve', methods=['PUT'])
@jwt_required()
@audit_log('approve', 'Sales')
@role_required('Owner', 'General Manager', 'Sales Manager', 'Branch Manager')
def approve_order(id):
    from services.inventory_service import InventoryService

    order = SalesOrder.query.get(id)
    if not order:
        raise NotFoundError('Order not found')

    if order.status != 'Draft':
        raise ValidationError(f'Cannot approve order with status: {order.status}')

    inv_service = InventoryService()
    user_id = int(get_jwt_identity())

    giv = inv_service.create_goods_issue_voucher(
        warehouse_id=order.warehouse_id,
        items=[
            {
                'product_id': item.product_id,
                'quantity': float(item.quantity),
            }
            for item in order.items
        ],
        sales_order_id=order.id,
        reference_type='SalesOrder',
        reference_id=order.id,
        notes=f'Auto-generated GIV for order {order.order_number}',
        created_by_id=user_id,
        issued_by_id=user_id,
    )

    inv_service.process_goods_issue(giv.id, user_id)

    order.status = 'Approved'
    order.approved_by_id = user_id
    order.approved_at = db.func.now()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({
        'message': 'Order approved successfully',
        'giv_id': giv.id,
        'giv_number': giv.voucher_number,
    }), 200


@sales_bp.route('/orders/<int:id>/cancel', methods=['PUT'])
@jwt_required()
@audit_log('cancel', 'Sales')
@role_required('Owner', 'General Manager', 'Sales Manager', 'Branch Manager')
def cancel_order(id):
    from services.inventory_service import InventoryService

    order = SalesOrder.query.get(id)
    if not order:
        raise NotFoundError('Order not found')

    if order.status in ('Cancelled', 'Completed'):
        raise ValidationError(f'Cannot cancel order with status: {order.status}')

    user_id = int(get_jwt_identity())

    if order.status == 'Approved':
        inv_service = InventoryService()
        inv_service.reverse_goods_issue(order.id, user_id)

    order.status = 'Cancelled'
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Order cancelled successfully'}), 200


# ─── Invoices ─────────────────────────────────────────────

@sales_bp.route('/invoices', methods=['GET'])
@jwt_required()
@permission_required('sales.view')
def list_invoices():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    customer_id = request.args.get('customer_id', type=int)
    sales_order_id = request.args.get('sales_order_id', type=int)
    payment_status = request.args.get('payment_status', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = Invoice.query

    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    if sales_order_id:
        query = query.filter(Invoice.sales_order_id == sales_order_id)
    if payment_status:
        query = query.filter(Invoice.payment_status == payment_status)
    if date_from:
        query = query.filter(Invoice.invoice_date >= date_from)
    if date_to:
        query = query.filter(Invoice.invoice_date <= date_to)

    query = query.order_by(Invoice.created_at.desc())
    result = paginate(query, page, per_page)

    invoices = []
    for inv in result['items']:
        invoices.append({
            'id': inv.id, 'invoice_number': inv.invoice_number,
            'sales_order_id': inv.sales_order_id,
            'customer_id': inv.customer_id,
            'customer_name': inv.customer.name if inv.customer else None,
            'invoice_date': inv.invoice_date.isoformat() if inv.invoice_date else None,
            'due_date': inv.due_date.isoformat() if inv.due_date else None,
            'subtotal': float(inv.subtotal) if inv.subtotal else 0,
            'tax_amount': float(inv.tax_amount) if inv.tax_amount else 0,
            'total_amount': float(inv.total_amount) if inv.total_amount else 0,
            'paid_amount': float(inv.paid_amount) if inv.paid_amount else 0,
            'balance_due': float(inv.balance_due) if inv.balance_due else 0,
            'payment_status': inv.payment_status,
            'status': inv.status,
            'notes': inv.notes,
        })

    return jsonify({
        'invoices': invoices,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@sales_bp.route('/invoices', methods=['POST'])
@jwt_required()
@audit_log('create', 'Sales')
@permission_required('sales.create')
def create_invoice():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    invoice_number = data.get('invoice_number', '').strip()
    sales_order_id = data.get('sales_order_id')
    customer_id = data.get('customer_id')
    invoice_date_str = data.get('invoice_date')
    due_date_str = data.get('due_date')
    try:
        invoice_date = date.fromisoformat(invoice_date_str) if invoice_date_str else date.today()
    except (ValueError, TypeError):
        raise ValidationError('Invalid invoice_date format, expected YYYY-MM-DD')
    try:
        due_date = date.fromisoformat(due_date_str) if due_date_str else None
    except (ValueError, TypeError):
        raise ValidationError('Invalid due_date format, expected YYYY-MM-DD')
    subtotal = data.get('subtotal', 0)
    tax_amount = data.get('tax_amount', 0)
    total_amount = data.get('total_amount', 0)
    notes = data.get('notes', '').strip()

    if not invoice_number:
        invoice_number = generate_unique_code('INV')
    if not sales_order_id or not customer_id:
        raise ValidationError('sales_order_id and customer_id are required')

    if Invoice.query.filter(Invoice.invoice_number == invoice_number).first():
        raise ConflictError('Invoice number already exists')

    invoice = Invoice(
        invoice_number=invoice_number,
        sales_order_id=sales_order_id,
        customer_id=customer_id,
        invoice_date=invoice_date,
        due_date=due_date,
        subtotal=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        balance_due=float(total_amount),
        notes=notes,
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(invoice)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Invoice created successfully', 'invoice_id': invoice.id}), 201


@sales_bp.route('/invoices/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('sales.view')
def get_invoice(id):
    invoice = Invoice.query.get(id)
    if not invoice:
        raise NotFoundError('Invoice not found')

    return jsonify({'invoice': {
        'id': invoice.id, 'invoice_number': invoice.invoice_number,
        'sales_order_id': invoice.sales_order_id,
        'customer_id': invoice.customer_id,
        'customer_name': invoice.customer.name if invoice.customer else None,
        'invoice_date': invoice.invoice_date.isoformat() if invoice.invoice_date else None,
        'due_date': invoice.due_date.isoformat() if invoice.due_date else None,
        'subtotal': float(invoice.subtotal) if invoice.subtotal else 0,
        'tax_amount': float(invoice.tax_amount) if invoice.tax_amount else 0,
        'total_amount': float(invoice.total_amount) if invoice.total_amount else 0,
        'paid_amount': float(invoice.paid_amount) if invoice.paid_amount else 0,
        'balance_due': float(invoice.balance_due) if invoice.balance_due else 0,
        'payment_status': invoice.payment_status,
        'status': invoice.status,
        'notes': invoice.notes,
    }}), 200


@sales_bp.route('/invoices/<int:id>/pay', methods=['PUT'])
@jwt_required()
@audit_log('pay', 'Sales')
@permission_required('payments.create')
def pay_invoice(id):
    invoice = Invoice.query.get(id)
    if not invoice:
        raise NotFoundError('Invoice not found')

    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    amount = data.get('amount')
    payment_method = data.get('payment_method', '').strip()
    payment_date_str = data.get('payment_date')
    payment_date = date.fromisoformat(payment_date_str) if payment_date_str else date.today()
    reference_number = data.get('reference_number', '').strip()
    bank_name = data.get('bank_name', '').strip()
    receipt_image = data.get('receipt_image', '').strip()
    notes = data.get('notes', '').strip()

    if not amount or not payment_method:
        raise ValidationError('amount and payment_method are required')

    if float(amount) <= 0:
        raise ValidationError('Amount must be positive')

    if float(amount) > float(invoice.balance_due):
        raise ValidationError('Payment amount exceeds balance due')

    payment_number = f'PAY-{invoice.id}-{random.randint(1000, 9999)}'

    payment = Payment(
        payment_number=payment_number,
        invoice_id=invoice.id,
        customer_id=invoice.customer_id,
        amount=amount,
        payment_date=payment_date,
        payment_method=payment_method,
        reference_number=reference_number,
        bank_name=bank_name,
        receipt_image=receipt_image,
        notes=notes,
        received_by_id=int(get_jwt_identity()),
    )
    db.session.add(payment)

    invoice.paid_amount = float(invoice.paid_amount or 0) + float(amount)
    invoice.balance_due = float(invoice.total_amount) - float(invoice.paid_amount)
    invoice.payment_status = 'Paid' if invoice.balance_due <= 0 else 'Partial'
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Payment recorded successfully', 'payment_id': payment.id}), 200


@sales_bp.route('/payments', methods=['GET'])
@jwt_required()
@permission_required('payments.view')
def list_payments():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    customer_id = request.args.get('customer_id', type=int)
    invoice_id = request.args.get('invoice_id', type=int)
    payment_method = request.args.get('payment_method', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()

    query = Payment.query

    if customer_id:
        query = query.filter(Payment.customer_id == customer_id)
    if invoice_id:
        query = query.filter(Payment.invoice_id == invoice_id)
    if payment_method:
        query = query.filter(Payment.payment_method == payment_method)
    if date_from:
        query = query.filter(Payment.payment_date >= date_from)
    if date_to:
        query = query.filter(Payment.payment_date <= date_to)

    query = query.order_by(Payment.created_at.desc())
    result = paginate(query, page, per_page)

    payments = []
    for p in result['items']:
        invoice = Invoice.query.get(p.invoice_id)
        payments.append({
            'id': p.id, 'payment_number': p.payment_number,
            'invoice_id': p.invoice_id,
            'invoice_number': invoice.invoice_number if invoice else None,
            'customer_id': p.customer_id,
            'customer_name': p.customer.name if p.customer else None,
            'amount': float(p.amount) if p.amount else 0,
            'payment_date': p.payment_date.isoformat() if p.payment_date else None,
            'payment_method': p.payment_method,
            'reference_number': p.reference_number,
            'bank_name': p.bank_name,
            'receipt_image': p.receipt_image,
            'notes': p.notes,
        })

    return jsonify({
        'items': payments,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


# ─── Loading Authorizations ──────────────────────────────

@sales_bp.route('/loading-authorizations', methods=['POST'])
@jwt_required()
@audit_log('create', 'Sales')
@role_required('Owner', 'General Manager', 'Sales Manager', 'Warehouse Manager')
def create_loading_authorization():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    authorization_number = data.get('authorization_number', '').strip()
    sales_order_id = data.get('sales_order_id')
    warehouse_id = data.get('warehouse_id')
    notes = data.get('notes', '').strip()

    if not authorization_number:
        authorization_number = generate_unique_code('LA')
    if not sales_order_id or not warehouse_id:
        raise ValidationError('sales_order_id and warehouse_id are required')

    if LoadingAuthorization.query.filter(LoadingAuthorization.authorization_number == authorization_number).first():
        raise ConflictError('Authorization number already exists')

    la = LoadingAuthorization(
        authorization_number=authorization_number,
        sales_order_id=sales_order_id,
        warehouse_id=warehouse_id,
        notes=notes,
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(la)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Loading authorization created successfully', 'la_id': la.id}), 201


@sales_bp.route('/loading-authorizations', methods=['GET'])
@jwt_required()
@permission_required('sales.view')
def list_loading_authorizations():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sales_order_id = request.args.get('sales_order_id', type=int)
    status = request.args.get('status', '').strip()

    query = LoadingAuthorization.query

    if sales_order_id:
        query = query.filter(LoadingAuthorization.sales_order_id == sales_order_id)
    if status:
        query = query.filter(LoadingAuthorization.status == status)

    query = query.order_by(LoadingAuthorization.created_at.desc())
    result = paginate(query, page, per_page)

    auths = []
    for la in result['items']:
        auths.append({
            'id': la.id, 'authorization_number': la.authorization_number,
            'sales_order_id': la.sales_order_id,
            'warehouse_id': la.warehouse_id,
            'warehouse_name': la.warehouse.name if la.warehouse else None,
            'authorized_date': la.authorized_date.isoformat() if la.authorized_date else None,
            'status': la.status,
            'notes': la.notes,
        })

    return jsonify({
        'loading_authorizations': auths,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@sales_bp.route('/loading-authorizations/<int:id>/approve', methods=['PUT'])
@jwt_required()
@audit_log('approve', 'Sales')
@role_required('Owner', 'General Manager', 'Sales Manager', 'Warehouse Manager')
def approve_loading(id):
    la = LoadingAuthorization.query.get(id)
    if not la:
        raise NotFoundError('Loading authorization not found')

    if la.status != 'Pending':
        raise ValidationError(f'Cannot approve authorization with status: {la.status}')

    la.status = 'Approved'
    la.authorized_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Loading authorization approved successfully'}), 200


@sales_bp.route('/upload-receipt', methods=['POST'])
@jwt_required()
def upload_receipt():
    if 'file' not in request.files:
        raise ValidationError('No file uploaded')
    f = request.files['file']
    if f.filename == '':
        raise ValidationError('No file selected')
    upload_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'uploads', 'receipts')
    os.makedirs(upload_dir, exist_ok=True)
    ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else 'jpg'
    filename = f'receipt_{datetime.now().strftime("%Y%m%d%H%M%S")}_{random.randint(1000,9999)}.{ext}'
    filepath = os.path.join(upload_dir, filename)
    f.save(filepath)
    return jsonify({'url': f'/uploads/receipts/{filename}'}), 200
