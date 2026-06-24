from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.models import Customer, SalesOrder, Invoice, Payment, db
from utils.helpers import paginate, generate_unique_code, escape_like
from utils.error_handlers import NotFoundError, ValidationError, ConflictError
from api.decorators import permission_required, branch_required, audit_log
from . import customers_bp


@customers_bp.route('', methods=['GET'])
@jwt_required()
@permission_required('customers.view')
@branch_required()
def list_customers():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search', '').strip()
    customer_type = request.args.get('customer_type', '').strip()
    branch_id = request.args.get('branch_id', type=int)
    is_active = request.args.get('is_active', type=int)

    query = Customer.query.filter(Customer.is_deleted == False)

    if search:
        safe = escape_like(search)
        query = query.filter(
            db.or_(
                Customer.name.ilike(f'%{safe}%'),
                Customer.customer_code.ilike(f'%{safe}%'),
                Customer.phone.ilike(f'%{safe}%'),
                Customer.email.ilike(f'%{safe}%'),
                Customer.tin_number.ilike(f'%{safe}%'),
            )
        )
    if customer_type:
        query = query.filter(Customer.customer_type == customer_type)
    if branch_id:
        query = query.filter(Customer.branch_id == branch_id)
    if is_active is not None:
        query = query.filter(Customer.is_active == bool(is_active))

    query = query.order_by(Customer.name.asc())
    result = paginate(query, page, per_page)

    customers = []
    for c in result['items']:
        customers.append({
            'id': c.id, 'customer_code': c.customer_code, 'name': c.name,
            'phone': c.phone, 'email': c.email, 'address': c.address,
            'tin_number': c.tin_number, 'customer_type': c.customer_type,
            'credit_limit': float(c.credit_limit) if c.credit_limit else 0,
            'is_active': c.is_active, 'branch_id': c.branch_id,
            'created_at': c.created_at.isoformat() if c.created_at else None,
        })

    return jsonify({
        'customers': customers,
        'total': result['total'],
        'page': result['page'],
        'per_page': result['per_page'],
        'pages': result['pages'],
    }), 200


@customers_bp.route('', methods=['POST'])
@jwt_required()
@audit_log('create', 'Customer')
@permission_required('customers.create')
@branch_required()
def create_customer():
    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    name = data.get('name', '').strip()
    customer_code = data.get('customer_code', '').strip()
    branch_id = data.get('branch_id')

    if not customer_code:
        customer_code = generate_unique_code('CUST')
    if not name or not branch_id:
        raise ValidationError('name and branch_id are required')

    if Customer.query.filter(Customer.customer_code == customer_code).first():
        raise ConflictError('Customer code already exists')

    customer = Customer(
        customer_code=customer_code,
        name=name,
        phone=data.get('phone', '').strip(),
        email=data.get('email', '').strip(),
        address=data.get('address', '').strip(),
        tin_number=data.get('tin_number', '').strip(),
        customer_type=data.get('customer_type', 'Regular'),
        credit_limit=data.get('credit_limit', 0),
        branch_id=branch_id,
        is_active=data.get('is_active', True),
        created_by_id=int(get_jwt_identity()),
    )
    db.session.add(customer)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'customer': {
        'id': customer.id, 'customer_code': customer.customer_code,
        'name': customer.name, 'phone': customer.phone,
        'email': customer.email, 'customer_type': customer.customer_type,
        'branch_id': customer.branch_id,
    }, 'message': 'Customer created successfully'}), 201


@customers_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
@permission_required('customers.view')
def get_customer(id):
    customer = Customer.query.filter(Customer.id == id, Customer.is_deleted == False).first()
    if not customer:
        raise NotFoundError('Customer not found')

    return jsonify({'customer': {
        'id': customer.id, 'customer_code': customer.customer_code, 'name': customer.name,
        'phone': customer.phone, 'email': customer.email, 'address': customer.address,
        'tin_number': customer.tin_number, 'customer_type': customer.customer_type,
        'credit_limit': float(customer.credit_limit) if customer.credit_limit else 0,
        'is_active': customer.is_active, 'branch_id': customer.branch_id,
        'created_at': customer.created_at.isoformat() if customer.created_at else None,
        'updated_at': customer.updated_at.isoformat() if customer.updated_at else None,
    }}), 200


@customers_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@audit_log('update', 'Customer', entity_getter=lambda id, **kw: Customer.query.get(id))
@permission_required('customers.edit')
def update_customer(id):
    customer = Customer.query.filter(Customer.id == id, Customer.is_deleted == False).first()
    if not customer:
        raise NotFoundError('Customer not found')

    data = request.get_json()
    if not data:
        raise ValidationError('Request body is required')

    customer_code = data.get('customer_code', '').strip()
    if customer_code and customer_code != customer.customer_code:
        if Customer.query.filter(Customer.customer_code == customer_code, Customer.id != id).first():
            raise ConflictError('Customer code already exists')
        customer.customer_code = customer_code

    if data.get('name'):
        customer.name = data['name'].strip()
    if data.get('phone') is not None:
        customer.phone = data['phone'].strip()
    if data.get('email') is not None:
        customer.email = data['email'].strip()
    if data.get('address') is not None:
        customer.address = data['address'].strip()
    if data.get('tin_number') is not None:
        customer.tin_number = data['tin_number'].strip()
    if data.get('customer_type'):
        customer.customer_type = data['customer_type']
    if data.get('credit_limit') is not None:
        customer.credit_limit = data['credit_limit']
    if data.get('is_active') is not None:
        customer.is_active = bool(data['is_active'])
    if data.get('branch_id'):
        customer.branch_id = data['branch_id']

    customer.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Customer updated successfully'}), 200


@customers_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@audit_log('delete', 'Customer')
@permission_required('customers.delete')
def delete_customer(id):
    customer = Customer.query.filter(Customer.id == id, Customer.is_deleted == False).first()
    if not customer:
        raise NotFoundError('Customer not found')

    if SalesOrder.query.filter_by(customer_id=id).first():
        raise ValidationError('Cannot delete customer with existing sales orders')
    if Invoice.query.filter_by(customer_id=id).first():
        raise ValidationError('Cannot delete customer with existing invoices')
    if Payment.query.filter_by(customer_id=id).first():
        raise ValidationError('Cannot delete customer with existing payments')

    customer.soft_delete()
    customer.updated_by_id = int(get_jwt_identity())
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return jsonify({'message': 'Customer deleted successfully'}), 200


@customers_bp.route('/<int:id>/history', methods=['GET'])
@jwt_required()
@permission_required('customers.view')
def get_customer_history(id):
    customer = Customer.query.filter(Customer.id == id, Customer.is_deleted == False).first()
    if not customer:
        raise NotFoundError('Customer not found')

    orders = SalesOrder.query.filter_by(customer_id=id).order_by(SalesOrder.created_at.desc()).limit(50).all()
    invoices = Invoice.query.filter_by(customer_id=id).order_by(Invoice.created_at.desc()).limit(50).all()
    payments = Payment.query.filter_by(customer_id=id).order_by(Payment.created_at.desc()).limit(50).all()

    return jsonify({
        'customer': {'id': customer.id, 'name': customer.name, 'customer_code': customer.customer_code},
        'orders': [{
            'id': o.id, 'order_number': o.order_number, 'order_date': o.order_date.isoformat() if o.order_date else None,
            'status': o.status, 'total_amount': float(o.total_amount) if o.total_amount else 0,
        } for o in orders],
        'invoices': [{
            'id': i.id, 'invoice_number': i.invoice_number, 'invoice_date': i.invoice_date.isoformat() if i.invoice_date else None,
            'total_amount': float(i.total_amount) if i.total_amount else 0,
            'paid_amount': float(i.paid_amount) if i.paid_amount else 0,
            'balance_due': float(i.balance_due) if i.balance_due else 0,
            'payment_status': i.payment_status,
        } for i in invoices],
        'payments': [{
            'id': p.id, 'payment_number': p.payment_number, 'amount': float(p.amount) if p.amount else 0,
            'payment_date': p.payment_date.isoformat() if p.payment_date else None,
            'payment_method': p.payment_method,
        } for p in payments],
    }), 200
